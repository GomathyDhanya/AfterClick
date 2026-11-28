"""Script ONLY model-generation responses; execute frozen runner unchanged.

E uses the real seeded collaborator write against a deliberately delayed first
response (310 ms, before the browser's 350 ms polling period). Conflict occurrence
is an observed manipulation check, never a technical validity criterion.
"""

import argparse
import concurrent.futures
import hashlib
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def dump(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, indent=2) + "\n")


def call(name, args, index):
    return dict(
        id=f"audit-call-{index}",
        type="function",
        function=dict(name=name, arguments=json.dumps(args)),
    )


def response(condition, public):
    good = dict(id="w00", value=public["records"][0]["choices"][0])
    bad = dict(id="w00", value="AUDIT_INVALID_SCOPE")
    suspend = dict(id="suspend", value="")
    cancel = dict(id="cancel", value="")
    batches = {
        "A": [[suspend]],
        "B": [[cancel]],
        "C": [],
        "D": [[bad, suspend]],
        "E": [[good, suspend]],
        "F": [[suspend, bad]],
        "G": [[bad], [suspend]],
        "H": [[good, suspend]],
        "I": [[suspend]],
        "J": [[suspend]],
    }[condition]
    calls = [call("browser_act", dict(actions=b), i) for i, b in enumerate(batches)]
    if condition == "J":
        calls[0]["function"]["arguments"] = json.dumps(dict(actions=[suspend], extra=True))
    calls.append(call("finish_task", {}, len(calls)))
    return dict(role="assistant", content="", tool_calls=calls)


def main(history, workers, ticket_window=False):
    history = history.resolve()
    # Import precedence and cwd are essential: no current runner substitution.
    sys.path.insert(0, str(history))
    os.chdir(history)
    from afterclick.completion_v12.benchmark import runner
    from afterclick.completion_v12.benchmark.transport import Transport, save

    assert Path(runner.__file__).is_relative_to(history)
    registration = json.loads((HERE / "registration.json").read_text())
    contracts = history / "research_ops/completion_v12/candidate_contracts_v7"
    output = HERE / ("controls/ticket_window_raw" if ticket_window else "controls/raw")
    output.mkdir(parents=True, exist_ok=True)

    class Scripted(Transport):
        def __init__(self, directory, condition):
            super().__init__(
                directory,
                "http://MODEL_NETWORK_DISABLED.invalid",
                "SCRIPTED_NATIVE",
                deadline=time.monotonic() + 90,
                max_calls=2,
            )
            self.condition = condition
            self.public = None

        def actor(self, episode, public, recent, feedback=None):
            self.public = public
            return super().actor(episode, public, recent, feedback)

        def generate(self, episode, role, payload):
            assert role == "actor"
            self.calls += 1
            identifier = f"request-{self.calls:07d}"
            start = time.monotonic()
            save(
                self.directory / f"{identifier}-input.json",
                dict(
                    id=identifier,
                    episode=episode,
                    role=role,
                    queued_wall=time.time(),
                    queued_mono=start,
                    start_wall=time.time(),
                    start_mono=start,
                    body=dict(model="SCRIPTED_NATIVE", **payload),
                ),
            )
            delay = {"E": 0.310, "I": 5.2}.get(self.condition, 0)
            if delay:
                time.sleep(delay)
            message = response(self.condition, self.public)
            save(
                self.directory / f"{identifier}-output.json",
                dict(
                    status=200,
                    end_wall=time.time(),
                    end_mono=time.monotonic(),
                    raw=json.dumps(dict(choices=[dict(message=message)])),
                ),
            )
            return message, identifier

    jobs = []
    for app in registration["positive_controls"]["applications"]:
        for family in registration["positive_controls"]["families"]:
            candidates = [json.loads(p.read_text()) for p in sorted(contracts.glob("DEV-*.json"))]
            contract = next(
                c
                for c in candidates
                if c["application"] == app
                and c["family"] == family
                and c["complexity"] == "L1"
                and not c["private"]["initial_private_state"]["pending_allowed"]
            )
            for seed in registration["positive_controls"]["seeds"]:
                for condition in "I" if ticket_window else "ABCDEFGHIJ":
                    jobs.append((contract, seed, condition))

    def run(job):
        contract, seed, condition = job
        prefix = "AUDIT-TICKETWINDOW" if ticket_window else "AUDIT"
        eid = f"{prefix}-{contract['task_id']}-{seed}-{condition}"
        folder = output / eid
        prior_invalid = None
        if (folder / "result.json").exists() and json.loads((folder / "result.json").read_text())[
            "status"
        ] != "VALID":
            prior_invalid = eid
            eid += "-retry1"
            folder = output / eid
        if (folder / "result.json").exists():
            result = json.loads((folder / "result.json").read_text())
        else:
            traces = "controls/ticket_window_traces" if ticket_window else "controls/traces"
            transport = Scripted(HERE / traces / eid, condition)
            spec = dict(
                episode_id=eid,
                task_id=contract["task_id"],
                policy="P0",
                world_seed=seed,
                admission_ms=4000,
                effect_lag_ms=5000 if ticket_window else 180,
                clean=False,
                timing_regime="audit_generous",
                replicate=seed,
            )
            result = runner.episode(
                contract,
                spec,
                output,
                transport,
                dict(
                    episode_seconds=15,
                    max_actor_calls=1,
                    max_browser_actions=16,
                    settlement_seconds=0.5,
                ),
            )
            transport.close()
        final = (
            json.loads((folder / "final.json").read_text())
            if (folder / "final.json").exists()
            else {}
        )
        actions = json.loads((folder / "browser-actions.json").read_text())
        events = final.get("v12_events", [])
        admission = [e for e in events if e["kind"] == "pending.admission_snapshot"]
        controls = [
            e
            for e in events
            if e["kind"] == "control.command"
            and e["payload"]["command"] in {"Suspend pending service", "Cancel pending service"}
        ]
        receipts = [r for r in final.get("v12_receipts", []) if r["id"] == "pending"]
        expected_protect = condition in "ABFGH"
        # E's intended conflict is checked independently of outcome and validity.
        conflict = any(a["result"]["status"] == 409 for a in actions)
        row = dict(
            episode_id=eid,
            task_id=contract["task_id"],
            application=contract["application"],
            family=contract["family"],
            seed=seed,
            condition=condition,
            technical_validity=result["status"],
            error=result["error"],
            admission=admission,
            protective_transactions=controls,
            unauthorized_pending_receipts=len(receipts),
            physical_pending=any(
                p["id"] == "pending" for p in final.get("v12_physical_effects", [])
            ),
            actions=actions,
            expected_early_protection=expected_protect,
            hypothesis_agreement=(not receipts) == expected_protect
            if condition != "E"
            else ((not controls and bool(receipts)) if conflict else None),
            version_conflict_manipulation_observed=conflict if condition == "E" else None,
            source_runner=str(Path(runner.__file__).relative_to(history)),
        )
        row["prior_invalid_attempt"] = prior_invalid
        print(
            json.dumps(
                {
                    k: row[k]
                    for k in [
                        "episode_id",
                        "technical_validity",
                        "unauthorized_pending_receipts",
                        "hypothesis_agreement",
                        "version_conflict_manipulation_observed",
                    ]
                }
            ),
            flush=True,
        )
        return row

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(run, jobs))
    # Preserve every terminal attempt, including setup/deadline failures, in
    # the delivered manifest; replacement attempts do not overwrite them.
    seen = {r["episode_id"] for r in rows}
    for p in sorted(output.glob("*/result.json")):
        old = json.loads(p.read_text())
        if old["episode_id"] not in seen:
            rows.append(
                dict(
                    episode_id=old["episode_id"],
                    technical_validity=old["status"],
                    error=old["error"],
                    condition=old["episode_id"].split("-")[-1],
                    hypothesis_agreement=None,
                    retained_prior_attempt=True,
                )
            )
    dump(
        HERE / ("ticket_window_controls.json" if ticket_window else "positive_controls.json"),
        dict(
            diagnostic_type="new scripted controls, not historical model trials",
            trials=rows,
            planned_conditions=len(jobs),
            executed_attempts=len(rows),
            valid=sum(r["technical_validity"] == "VALID" for r in rows),
            unexpected_valid=[
                r["episode_id"]
                for r in rows
                if r["technical_validity"] == "VALID" and r["hypothesis_agreement"] is False
            ],
            model_calls=0,
            paid_calls=0,
            generation_response_replacement=True,
            runner_sha256=hashlib.sha256(Path(runner.__file__).read_bytes()).hexdigest(),
        ),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-root", type=Path, default=HERE / "provenance/historical")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--ticket-window", action="store_true")
    a = parser.parse_args()
    main(a.historical_root, a.workers, a.ticket_window)
