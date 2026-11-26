"""Finite full-cohort reference qualification using real PostgreSQL/Chromium/HTTP.

Workers may qualify independent contracts concurrently. Every started attempt,
failed attempt and incomplete slot remains in the append-only execution journal.
"""

import argparse
import copy
import json
import multiprocessing
import shutil
import time
import traceback
from pathlib import Path

from playwright.sync_api import sync_playwright

from afterclick.completion_v12.benchmark.browser import Browser
from afterclick.completion_v12.benchmark.flow import FlowWorld
from afterclick.completion_v12.benchmark.ops import OpsWorld
from afterclick.completion_v12.benchmark.oracle import evaluate
from afterclick.completion_v12.evidence import digest, sha


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def choose(public, record):
    if record.get("scope_rule", "primary") == "primary":
        return record["choices"][0]
    evidence = public["service"]["evidence"]
    classifications = evidence.get("classifications")
    if classifications is None:
        return None
    return record["choices"][classifications[record["scope_rule"]] == "alternate"]


def reference(gateway, *, reverse=False, deadline=None):
    deadline = deadline or time.monotonic() + 120
    public = gateway.observe()
    if public["service"]["authority"] != "approved":
        gateway.act("suspend")
        gateway.act("verify")
        if gateway.observe()["service"]["authority"] == "approved":
            gateway.act("resume")
    turns = 0
    while time.monotonic() < deadline:
        public = gateway.observe()
        remaining = [r for r in public["records"] if r["stage"] != "complete"]
        if not remaining:
            break
        completed = {r["id"] for r in public["records"] if r["stage"] == "complete"}
        ready = [
            r
            for r in remaining
            if set(r["dependencies"]) <= completed
            and choose(public, r) is not None
            and not (
                r["kind"] == "approval" and r["stage"] in {"approval_requested", "In progress"}
            )
            and not (r["kind"] == "external" and r["stage"] in {"outcome_uncertain", "In progress"})
        ]
        ready = sorted(ready, key=lambda r: r["id"], reverse=reverse)
        if ready:
            for record in ready:
                result = gateway.act(record["id"], choose(public, record))
                if result["status"] not in [200, 409]:
                    raise ValueError("Reference unexpected business response: " + str(result))
                turns += 1
        elif any(
            r["kind"] == "external" and r["stage"] in {"outcome_uncertain", "In progress"}
            for r in remaining
        ):
            gateway.act("verify")
        gateway.page.wait_for_timeout(30)
    else:
        raise TimeoutError("Full reference horizon exhausted")
    while not gateway.observe()["service"]["request_resolved"]:
        if time.monotonic() >= deadline:
            raise TimeoutError("Pending service unresolved at observation deadline")
        gateway.page.wait_for_timeout(30)
    gateway.act("verify")
    if gateway.observe()["service"]["suspended"]:
        gateway.act("restore")
    return turns


def mutate(contract, snapshot):
    results = []
    for op in contract["private"]["initial_private_state"]["operations"]:
        bad = copy.deepcopy(snapshot)
        if contract["application"] == "flowboard":
            row = next(t for t in bad["tasks"] if t["id"] == op["id"])
            row["status"] = "Backlog"
        else:
            row = next(t for t in bad["ops_work_orders"] if t["id"] == op["id"])
            row["stage"] = "open"
        score = evaluate(contract, bad)
        if score.get("joint_safe_completion") is True:
            raise ValueError("Oracle accepts omitted obligation: " + op["id"])
        results.append(dict(mutation="omit_obligation", id=op["id"], rejected=True))
    for kind in ["missing_receiver", "unrestored_service", "lost_collaborator"]:
        bad = copy.deepcopy(snapshot)
        if kind == "missing_receiver":
            bad["v12_receipts"] = []
        elif kind == "unrestored_service":
            bad["v12_controls"][0]["state"]["suspended"] = True
        else:
            bad["v12_controls"][0]["state"]["collaborator_note"] = []
        if evaluate(contract, bad).get("joint_safe_completion") is True:
            raise ValueError("Oracle accepts mutation: " + kind)
        results.append(dict(mutation=kind, rejected=True))
    return results


def qualify_one(args):
    contract_path, output_path = args
    contract_path, output = Path(contract_path), Path(output_path)
    contract = json.loads(contract_path.read_text())
    directory = output / contract["task_id"]
    directory.mkdir(exist_ok=False)
    world = gateway = None
    try:
        cls = FlowWorld if contract["application"] == "flowboard" else OpsWorld
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            cut = None
            # Equivalent initialized source cuts in independent schemas, never a live reset.
            for index in range(2):
                world = cls(contract, admission_ms=3000)
                world.initialize()
                with world.serve() as origin:
                    page = browser.new_page()
                    gateway = Browser(page, origin, contract["application"])
                    current = dict(
                        database=world.snapshot(),
                        public=gateway.observe(),
                        client=gateway.client_cut(),
                        contract_sha256=digest(contract),
                        schedule=dict(
                            seed=world.seed,
                            admission_ms=world.admission_ms,
                            effect_lag_ms=world.effect_lag_ms,
                            evidence_ms=world.evidence_ms,
                            collaborator_ms=world.collaborator_ms,
                        ),
                    )
                    if index == 0:
                        cut = current
                        write(directory / "source-cut.json", cut)
                    certificate = dict(
                        valid=current == cut,
                        source_sha256=digest(cut),
                        actual_sha256=digest(current),
                        scope="Initial quiescent cut; no in-flight writes",
                    )
                    write(directory / f"cut-certificate-{index}.json", certificate)
                    if not certificate["valid"]:
                        raise ValueError("Source reconstruction mismatch")
                    world.start()
                    gateway.start_polling()
                    count = reference(gateway, reverse=bool(index))
                    gateway.page.wait_for_timeout(350)
                    world.finish()
                    final = world.snapshot()
                    score = evaluate(contract, final, world.errors)
                    write(directory / f"final-{index}.json", final)
                    write(directory / f"actions-{index}.json", gateway.history)
                    write(directory / f"oracle-{index}.json", score)
                    if score.get("joint_safe_completion") is not True:
                        raise ValueError(
                            "Independent oracle rejects reference: " + json.dumps(score)
                        )
                    tests = mutate(contract, final)
                    write(directory / f"mutations-{index}.json", tests)
                    page.close()
                world.db.drop_experiment()
                world = None
            browser.close()
        result = dict(
            task_id=contract["task_id"],
            status="REFERENCE_QUALIFIED",
            contract_sha256=sha(contract_path),
            plans=2,
            oracle_mutations=len(tests) * 2,
            reference_commands=count,
            model_calls=0,
        )
    except BaseException:
        result = dict(
            task_id=contract["task_id"], status="FAILED_QUALIFICATION", error=traceback.format_exc()
        )
        write(directory / "qualification.json", result)
    finally:
        if gateway:
            write(directory / "last-browser-actions.json", gateway.history)
            write(directory / "last-browser-network.json", gateway.network)
        if world is not None:
            world.finish()
            write(directory / "worker-errors.json", world.errors)
            try:
                write(directory / "failed-snapshot.json", world.snapshot())
            except Exception:
                write(directory / "snapshot-error.json", dict(error=traceback.format_exc()))
            finally:
                world.db.drop_experiment()
    write(directory / "qualification.json", result)
    return result


def execute(contracts, output, workers=2, limit=None, dev_first=False):
    output.mkdir(parents=True, exist_ok=False)
    paths = sorted(p for p in contracts.glob("*.json") if p.name != "manifest.json")
    if dev_first:
        dev = [json.loads(p.read_text()) for p in paths if p.name.startswith("DEV-")]
        families = sorted({c["family"] for c in dev})
        priority = {
            c["task_id"]
            for c in dev
            if c["task_id"].endswith("-01")
            and c["complexity"] == f"L{families.index(c['family']) % 3 + 1}"
        }
        paths.sort(key=lambda p: (p.stem not in priority, p.name))
    if limit is not None:
        paths = paths[:limit]
    write(
        output / "registration.json",
        dict(
            contract_hashes={p.name: sha(p) for p in paths},
            count=len(paths),
            model_calls=0,
            workers=workers,
            mode="LOCAL_REFERENCE_QUALIFICATION_NOT_MODEL_TEST",
        ),
    )
    for source in [*Path(__file__).parent.glob("*.py"), *Path(__file__).parent.glob("*.html")]:
        target = output / "source-archive" / source.name
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(source, target)
    results = []
    with multiprocessing.get_context("spawn").Pool(workers) as pool:
        for row in pool.imap_unordered(qualify_one, [(str(p), str(output)) for p in paths]):
            results.append(row)
            with (output / "execution.jsonl").open("a") as stream:
                stream.write(json.dumps(row) + "\n")
            print(json.dumps({k: v for k, v in row.items() if k != "error"}), flush=True)
    summary = dict(
        expected=len(paths),
        attempted=len(results),
        reference_qualified=sum(r["status"] == "REFERENCE_QUALIFIED" for r in results),
        failed=sum(r["status"] != "REFERENCE_QUALIFIED" for r in results),
        model_calls=0,
    )
    write(output / "summary.json", summary)
    print(json.dumps(summary), flush=True)
    if summary["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contracts", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--limit", type=int)
    p.add_argument("--dev-first", action="store_true")
    a = p.parse_args()
    execute(a.contracts, a.output, a.workers, a.limit, a.dev_first)
