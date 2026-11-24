"""Validate exact live approval contract with a network-forbidden mock transport."""

import argparse
import json
import time
from pathlib import Path

import httpx

from afterclick.agent.modal_policy import atomic_json
from afterclick.tcope.budget import Factory
from afterclick.tcope.lifecycle import validate_phase_budget
from afterclick.tcope.policy import ExecutionPolicy


def preflight(run, info):
    p = json.loads((run / "protocol.json").read_text())
    validate_phase_budget(p)
    destination = run / "raw/approval-preflight-v2"
    destination.mkdir()
    (destination / "raw").mkdir()
    startup = 200

    def no_network(request):
        raise AssertionError("Preflight must not send HTTP")

    f = Factory(
        destination,
        p,
        info,
        time.monotonic() + p["total_seconds"] - p["cleanup_seconds"] - startup,
        20,
        transport=httpx.MockTransport(no_network),
        startup_elapsed_seconds=startup,
    )
    try:
        config, limits, approval_path = f.settings["corrected"]
        policy = ExecutionPolicy(
            config,
            limits,
            journal=destination / "corrected-model-calls.jsonl",
            transport=httpx.MockTransport(no_network),
            public_synthetic_task_hashes=p["public_task_hashes"],
        )
        f.instances.append(policy)
        approval = policy._approval(f.settings["corrected"][2])
        assert approval["public_synthetic_task_hashes"] == list(policy.public_task_hashes)
        atomic_json(
            destination / "result.json",
            dict(
                passed=True,
                model_calls=0,
                network_requests=0,
                canonical_task_hashes=approval["public_synthetic_task_hashes"],
            ),
        )
    finally:
        f.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--info", type=Path, required=True)
    a = p.parse_args()
    preflight(a.run, json.loads(a.info.read_text()))
