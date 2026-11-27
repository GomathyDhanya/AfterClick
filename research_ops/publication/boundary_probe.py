"""Explicitly scheduled PostgreSQL/HTTP boundary probes, not agent or deadline trials.

Reuses unmodified frozen worker/control/receiver methods. The added database wrapper
records return boundaries and gates one read while holding the original schema lock.
"""

import argparse
import concurrent.futures
import contextlib
import hashlib
import json
import os
import threading
import time
import traceback
from pathlib import Path

from afterclick.completion_v12.benchmark.flow import FlowWorld
from afterclick.completion_v12.benchmark.ops import OpsWorld
from afterclick.completion_v12.opsconsole import serve_app
from afterclick.infrastructure.db import Database

ROOT = Path(__file__).resolve().parents[2]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p, x):
    p.write_text(json.dumps(x, indent=2) + "\n")


class Trace:
    def __init__(self):
        self.rows = []
        self.lock = threading.Lock()
        self.gate = False
        self.read_locked = threading.Event()
        self.release = threading.Event()

    def emit(self, kind, **payload):
        with self.lock:
            self.rows.append(
                dict(
                    seq=len(self.rows),
                    kind=kind,
                    pid=os.getpid(),
                    thread=threading.current_thread().name,
                    mono_ns=time.monotonic_ns(),
                    wall_ns=time.time_ns(),
                    clock="process_monotonic_ns",
                    **payload,
                )
            )


class Result:
    def __init__(self, result, trace):
        self.result = result
        self.trace = trace

    def mappings(self):
        return Result(self.result.mappings(), self.trace)

    def one(self):
        r = self.result.one()
        self.trace.emit("authority_read_return", version=r.get("version"), state=r.get("state"))
        return r

    def scalar_one(self):
        r = self.result.scalar_one()
        self.trace.emit("authority_read_return", state=r)
        return r

    def __getattr__(self, n):
        return getattr(self.result, n)

    def __iter__(self):
        return iter(self.result)


class Connection:
    def __init__(self, c, trace):
        self.c = c
        self.trace = trace

    def __getattr__(self, n):
        return getattr(self.c, n)

    def execute(self, statement, *a, **kw):
        s = str(statement)
        authority = s.lstrip().startswith("SELECT") and "v12_controls" in s
        if authority and self.trace.gate and threading.current_thread().name.startswith("worker"):
            self.trace.gate = False
            self.trace.emit("barrier_holding_schema_lock")
            self.trace.read_locked.set()
            if not self.trace.release.wait(5):
                raise TimeoutError("read barrier")
        r = self.c.execute(statement, *a, **kw)
        return Result(r, self.trace) if authority else r


class TracedDatabase(Database):
    def __init__(self, old, trace):
        self.__dict__.update(old.__dict__)
        self.trace = trace

    @contextlib.contextmanager
    def transaction(self):
        self.trace.emit("transaction_attempt")
        try:
            with super().transaction() as c:
                self.trace.emit(
                    "schema_lock_acquired",
                    postgres_backend_pid=c.connection.driver_connection.info.backend_pid,
                )
                yield Connection(c, self.trace)
                self.trace.emit("commit_begin_lower_bound")
            self.trace.emit("commit_return_upper_bound")
        except Exception:
            self.trace.emit("transaction_rollback_or_failure")
            raise


def one(spec, out):
    dest = out / spec["id"]
    dest.mkdir()
    c = json.loads((ROOT / spec["contract"]).read_text())
    t = Trace()
    w = None
    r = dict(**spec, status="INVALID", model_calls=0)
    try:
        w = (FlowWorld if c["application"] == "flowboard" else OpsWorld)(
            c, seed=773, admission_ms=0, effect_lag_ms=80
        )
        w.initialize()
        w.db = TracedDatabase(w.db, t)
        with serve_app(w.receiver()) as url:
            w.receiver_url = url

            def tick():
                w.tick_audit()

            def protect():
                t.emit("protect_invocation", command=spec["command"])
                result = w.control(spec["command"])
                t.emit("protect_return", result=result)
                return result

            with (
                concurrent.futures.ThreadPoolExecutor(1, thread_name_prefix="worker") as worker,
                concurrent.futures.ThreadPoolExecutor(1, thread_name_prefix="controller") as ctl,
            ):
                if spec["order"] == "protection_before_admission":
                    ctl.submit(protect).result(10)
                    worker.submit(tick).result(10)
                elif spec["order"] == "admission_before_protection":
                    t.gate = True
                    f = worker.submit(tick)
                    assert t.read_locked.wait(5)
                    g = ctl.submit(protect)
                    # Wait for the controller's transaction attempt, while admission owns lock.
                    end = time.monotonic() + 3
                    while time.monotonic() < end:
                        if any(
                            x["kind"] == "transaction_attempt"
                            and x["thread"].startswith("controller")
                            for x in t.rows
                        ):
                            break
                        time.sleep(0.001)
                    else:
                        raise TimeoutError("controller did not attempt lock")
                    t.release.set()
                    f.result(10)
                    g.result(10)
                else:
                    worker.submit(tick).result(10)
                    w.anchor = time.monotonic() - 0.5
                    worker.submit(tick).result(10)
                    ctl.submit(protect).result(10)
                w.anchor = time.monotonic() - 0.5
                worker.submit(tick).result(10)
            final = w.snapshot()
            save(dest / "final.json", final)
            delivered = any(x["id"] == "pending" for x in final["v12_receipts"])
            physical = any(x["id"] == "pending" for x in final["v12_physical_effects"])
            assert delivered == physical
            expected = spec["order"] != "protection_before_admission"
            assert delivered == expected
            if spec["order"] == "admission_before_protection":
                lock = next(
                    x["seq"]
                    for x in t.rows
                    if x["kind"] == "schema_lock_acquired" and x["thread"].startswith("controller")
                )
                worker_commit = next(
                    x["seq"]
                    for x in t.rows
                    if x["kind"] == "commit_begin_lower_bound" and x["thread"].startswith("worker")
                )
                assert lock > worker_commit
                upper = next(x["mono_ns"] for x in t.rows if x["kind"] == "protect_return")
                receipt = next(x for x in final["v12_receipts"] if x["id"] == "pending")
                assert receipt["mono"] * 1e9 > upper
            r.update(
                status="VALID",
                pending_received=delivered,
                physical_effect=physical,
                forbidden_pending=delivered
                and not c["private"]["initial_private_state"]["pending_allowed"],
                serialized_source=True,
                exact_sql_commit_instant_observed=False,
            )
    except Exception:
        r["error"] = traceback.format_exc()
    finally:
        t.release.set()
        save(dest / "boundaries.json", t.rows)
        if w:
            w.finish()
            w.db.drop_experiment()
    save(dest / "result.json", r)
    return r


def main(output, dev=False):
    output.mkdir(parents=True, exist_ok=False)
    tasks = sorted(
        (ROOT / "research_ops/completion_v12/candidate_contracts_v7").glob("DEV-*-L3-*-02.json")
    )
    if dev:
        tasks = [
            next(p for p in tasks if "FLOWBOARD" in p.name),
            next(p for p in tasks if "OPSCONSOLE" in p.name),
        ]
    specs = [
        dict(
            id=f"{p.stem}-{o}-{cmd.split()[0]}",
            contract=str(p.relative_to(ROOT)),
            contract_sha256=sha(p),
            order=o,
            command=cmd,
        )
        for p in tasks
        for o in [
            "protection_before_admission",
            "admission_before_protection",
            "receipt_before_protection",
        ]
        for cmd in ["Suspend pending service", "Cancel pending service"]
    ]
    reg = dict(
        scope="ENGINEERED_BARRIER_MECHANISM_PROBE_NOT_NEW_BENCHMARK_OR_DEADLINE_ESTIMATE",
        tasks_reused_from_open_DEV=True,
        source_clusters=len(tasks),
        registered=len(specs),
        episodes=specs,
        source_sha256=sha(Path(__file__)),
        frozen_worker_sha256=sha(ROOT / "afterclick/completion_v12/benchmark/infrastructure.py"),
        model_calls=0,
        expected="Only pre-admission protection prevents original non-revocable pending ticket",
        gate="Stop new confirmation if either-app DEV probe fails; preserve every failed result",
        dev=dev,
    )
    save(output / "registration.json", reg)
    (output / "probe-source.py").write_bytes(Path(__file__).read_bytes())
    results = []
    for spec in specs:
        r = one(spec, output)
        results.append(r)
        print(json.dumps({k: r[k] for k in ["id", "status"]}), flush=True)
    report = dict(
        registered=len(specs),
        terminal=len(results),
        valid=sum(r["status"] == "VALID" for r in results),
        pending_received=sum(r.get("pending_received", False) for r in results),
        complete=len(results) == len(specs),
        model_calls=0,
        provider_calls=0,
        source_clusters=len(tasks),
        not_independent_new_tasks=True,
    )
    save(output / "report.json", report)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--dev", action="store_true")
    a = p.parse_args()
    main(a.output, a.dev)
