"""Prepare, or explicitly run an approved, bounded non-side-effecting decision smoke.

Default invocation only validates/locks input files. It creates no endpoint or model call.
"""

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from afterclick.agent.inference import public_input
from afterclick.agent.modal_policy import Limits, ModalConfig, ModalPolicy, atomic_json, digest
from afterclick.replay.demo import source_manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--max-calls", type=int, default=1)
    args = parser.parse_args()
    if not 1 <= args.max_calls <= 20 or args.output.exists():
        parser.error("One to twenty decisions and a fresh output directory required")
    if args.live and args.approval is None:
        parser.error("Live mode requires separate specific paid authorization")
    config_data = json.loads(args.config.read_text())
    config = ModalConfig(**config_data["config"])
    limits = Limits(**config_data["limits"])
    if args.max_calls > limits.max_calls:
        parser.error("Requested count exceeds frozen call cap")
    inputs = json.loads(args.inputs.read_text())
    if len(inputs) < args.max_calls:
        parser.error("Insufficient frozen smoke inputs")
    for value in inputs:
        public_input(value["task"], value["observation"], value["history"])
    args.output.mkdir(parents=True)
    for folder in ("raw", "figures"):
        (args.output / folder).mkdir()
    for file in (
        "model_calls.jsonl",
        "trials.jsonl",
        "browser_events.jsonl",
        "oracle_certificates.jsonl",
    ):
        (args.output / file).touch()
    run_id = uuid4().hex
    atomic_json(
        args.output / "protocol.json",
        {
            "schema_version": 1,
            "run_id": run_id,
            "phase": "P1C structured smoke",
            "max_decisions": args.max_calls,
            "config": asdict(config),
            "limits": asdict(limits),
            "inputs_sha256": digest(inputs),
            "data_mode": "live_modal" if args.live else "prepare_only",
            "primary_metric": "strict Decision validity; read-only compliance reported separately",
            "stop_rule": "first error/uncertainty; zero automatic retries; no browser actions",
            "planned_decisions_denominator": args.max_calls,
            "claim_scope": "engineering smoke; repeated inputs are not independent tasks",
        },
    )
    atomic_json(
        args.output / "manifest.json",
        {
            "schema_version": 1,
            "run_id": run_id,
            "source": source_manifest(),
            "config_sha256": config.fingerprint,
            "model_revision": config.model_revision,
            "billed_actual_usd": None,
        },
    )
    atomic_json(args.output / "raw/inputs.json", inputs)
    metrics = {
        "schema_version": 1,
        "run_id": run_id,
        "planned": args.max_calls,
        "attempted": 0,
        "valid_decisions": 0,
        "invalid_decisions": 0,
        "read_only_compliant": 0,
        "status": "prepared_only",
        "actual_cost_usd": None,
        "live_model_calls": 0,
    }
    try:
        if args.live:
            policy = ModalPolicy(
                config,
                limits,
                journal=args.output / "model_calls.jsonl",
                mode="live",
                approval_path=args.approval,
            )
            try:
                for index, value in enumerate(inputs[: args.max_calls]):
                    metrics["attempted"] += 1
                    try:
                        decision = policy.decide(
                            value["task"], value["observation"], value["history"]
                        )
                        metrics["valid_decisions"] += 1
                        metrics["read_only_compliant"] += decision.kind in {"read", "wait", "done"}
                        trial = {
                            "index": index,
                            "status": "valid",
                            "decision": decision.model_dump(),
                        }
                    except Exception as exc:
                        metrics["invalid_decisions"] += 1
                        trial = {
                            "index": index,
                            "status": "invalid",
                            "error_type": type(exc).__name__,
                        }
                    with (args.output / "trials.jsonl").open("a") as stream:
                        stream.write(json.dumps(trial) + "\n")
                        stream.flush()
                    if trial["status"] == "invalid":
                        break
                metrics.update(
                    status="executed",
                    usage=policy.usage_summary(),
                    live_model_calls=policy.usage_summary()["calls"],
                )
            finally:
                policy.close()
    except BaseException as exc:
        metrics.update(status="blocked_or_failed", error_type=type(exc).__name__)
        raise
    finally:
        atomic_json(args.output / "metrics.json", metrics)
        (args.output / "analysis.md").write_text(
            "No browser action executed. Preparation is not live validation. "
            "See metrics and immutable request journal; "
            "actual billing must be reconciled separately.\n"
        )
        (args.output / "next_experiment.md").write_text(
            "Review validity/errors and billing before separately approving browser tasks/replay.\n"
        )
        (args.output / "figures/README.md").write_text(
            "Not applicable to this engineering smoke.\n"
        )
    print(json.dumps(metrics))
    if metrics["status"] in {"blocked_or_failed"} or metrics["invalid_decisions"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
