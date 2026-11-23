"""Actual Chromium/PostgreSQL replay through HTTP mock adapter; never live evidence."""

import argparse
import json
from pathlib import Path

import httpx

from afterclick.agent.modal_policy import Limits, ModalConfig, ModalPolicy
from afterclick.replay.adaptive_runner import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Use a fresh output directory to preserve all previous runs")
    args.output.mkdir(parents=True)

    def handle(request):
        body = json.loads(request.content)
        # Nothing except public task/observation/history determines this mock response.
        public = json.loads(body["messages"][1]["content"])
        obs = public["observation"]
        if obs["save_status"] == "Failed":
            decision = {"kind": "click", "target": "Retry save", "value": ""}
        elif "API v2" not in obs["inputs"]["Description"]:
            decision = {
                "kind": "fill",
                "target": "Description",
                "value": "Document API v2 integration.",
            }
        else:
            decision = {"kind": "done", "target": "", "value": ""}
        return httpx.Response(
            200,
            json={
                "model": "afterclick-mock",
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": json.dumps(decision)},
                    }
                ],
                "usage": {"prompt_tokens": 2000, "completion_tokens": 30, "total_tokens": 2030},
            },
        )

    policy = ModalPolicy(
        ModalConfig("https://mock.us-west.modal.direct", "afterclick-mock", max_input_tokens=16384),
        Limits(max_calls=40, max_total_tokens=120000, max_wall_seconds=600),
        journal=args.output / "admission.jsonl",
        transport=httpx.MockTransport(handle),
    )
    try:
        report = run(args.output, policy, seeds=(7,))
    finally:
        policy.close()
    if not report["replay_valid"] or not report["all_goals_succeeded"]:
        raise SystemExit("Mock-provider replay invalid; retain all branch reports")


if __name__ == "__main__":
    main()
