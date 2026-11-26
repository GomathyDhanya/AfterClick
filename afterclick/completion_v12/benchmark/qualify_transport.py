"""Execute P0-P5 native tool plumbing using an explicitly scripted public actor.

No generated output is represented as an LLM call. This validates orchestration,
not agent competence or experimental efficacy.
"""

import argparse
import json
import threading
import time
from pathlib import Path

from afterclick.completion_v12.benchmark.qualification import choose
from afterclick.completion_v12.benchmark.runner import execute
from afterclick.completion_v12.benchmark.transport import save
from afterclick.completion_v12.evidence import digest, sha


class ScriptedTransport:
    def __init__(self, directory):
        self.directory = directory
        self.directory.mkdir()
        self.deadline = time.monotonic() + 900
        self.counter = 0
        self.lock = threading.Lock()

    def actor(self, episode, public, recent, feedback=None):
        time.sleep(0.15)
        with self.lock:
            self.counter += 1
            identifier = f"SCRIPTED-NO-MODEL-{self.counter:05d}"
        service = public["service"]
        name, args = "browser_act", None
        if service["authority"] == "verify-required":
            args = dict(actions=[dict(id="verify")])
        elif service["authority"] == "approved" and service["suspended"]:
            args = dict(actions=[dict(id="verify"), dict(id="resume")])
        elif (
            service["authority"] == "prohibited"
            and not service["request_resolved"]
            and not service["suspended"]
        ):
            args = dict(actions=[dict(id="suspend")])
        else:
            incomplete = [r for r in public["records"] if r["stage"] != "complete"]
            complete = {r["id"] for r in public["records"] if r["stage"] == "complete"}
            ready = [
                r
                for r in incomplete
                if set(r["dependencies"]) <= complete
                and choose(public, r) is not None
                and r["stage"] not in {"approval_requested", "outcome_uncertain", "In progress"}
            ]
            if ready:
                args = dict(actions=[dict(id=r["id"], value=choose(public, r)) for r in ready[:8]])
            elif any(r["kind"] == "external" for r in incomplete):
                args = dict(actions=[dict(id="verify")])
            elif incomplete or not service["request_resolved"]:
                name, args = "browser_state", {}
            elif not service["verified"]:
                args = dict(actions=[dict(id="verify")])
            elif service["suspended"]:
                args = dict(actions=[dict(id="restore")])
            else:
                name, args = "finish_task", {}
        message = dict(
            tool_calls=[
                dict(
                    id=identifier,
                    type="function",
                    function=dict(name=name, arguments=json.dumps(args)),
                )
            ]
        )
        save(
            self.directory / (identifier + ".json"),
            dict(episode=episode, public=public, native_output=message, genuine_model_call=False),
        )
        return message, identifier

    def review(self, episode, public):
        return dict(
            request_id="SCRIPTED-NO-MODEL-REVIEW",
            schema_valid=True,
            decision="allow" if public["service"]["authority"] == "approved" else "suspend",
            reason="Deterministic public authorization witness, not an LLM recommendation",
        )


def qualify(contracts, output, workers=1):
    output.mkdir(parents=True, exist_ok=False)
    specs, tasks = [], {}
    for app in ["FLOWBOARD", "OPSCONSOLE"]:
        path = contracts / f"DEV-RETENTION_EXPORT-L3-{app}-01.json"
        contract = json.loads(path.read_text())
        tasks[contract["task_id"]] = dict(path=str(path.resolve()), digest=digest(contract))
        for policy in ["P0", "P1", "P2", "P3", "P4", "P5"]:
            specs.append(
                dict(
                    episode_id=f"{app}-{policy}-SCRIPTED",
                    task_id=contract["task_id"],
                    policy=policy,
                    world_seed=1212,
                    admission_ms=3000,
                    clean=False,
                )
            )
    registration = dict(
        mode="LOCAL_SCRIPTED_NATIVE_TOOL_QUALIFICATION",
        genuine_model_calls=0,
        source_hashes={
            str(p): sha(p) for p in Path(__file__).parent.glob("*") if p.suffix in {".py", ".html"}
        },
        contracts=tasks,
        episodes=specs,
        environment_concurrency=workers,
        limits=dict(
            max_actor_calls=60, max_browser_actions=160, episode_seconds=180, settlement_seconds=1.5
        ),
    )
    save(output / "registration.json", registration)
    transport = ScriptedTransport(output / "scripted-traces")
    execute(registration, output / "episodes", transport)
    results = [json.loads(p.read_text()) for p in (output / "episodes").glob("*/result.json")]
    save(
        output / "summary.json",
        dict(
            registered=12,
            attempted=len(results),
            joint_safe=sum(
                r["score"] and r["score"].get("joint_safe_completion") is True for r in results
            ),
            genuine_model_calls=0,
            scripted_actor_outputs=transport.counter,
        ),
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contracts", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--workers", type=int, default=1)
    a = p.parse_args()
    qualify(a.contracts, a.output, a.workers)
