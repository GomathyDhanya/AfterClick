"""Seal one finished live run after retaining factual summaries and full evidence."""

import argparse
import json
from pathlib import Path
from afterclick.agent.modal_policy import atomic_json
from afterclick.model_sprint.records import seal, utc


def finalize(run, note):
    run = Path(run)
    if (run / "checksums.json").exists():
        raise ValueError("Already sealed; do not rewrite")
    lifecycle = json.loads((run / "lifecycle-metrics.json").read_text())
    assert (run / "finalization.json").exists(), "Live lifecycle must be closed first"
    protocol = json.loads((run / "protocol.json").read_text())
    trials = [
        json.loads(line) for line in (run / "trials.jsonl").read_text().splitlines() if line.strip()
    ]
    calls = [
        json.loads(line)
        for line in (run / "model_calls.jsonl").read_text().splitlines()
        if line.strip()
    ]
    starts = {row["request_id"]: row for row in calls if row["event"] == "started"}
    ends = {row["request_id"]: row for row in calls if row["event"] == "finished"}
    with (run / "requests.jsonl").open("w") as f:
        for key in starts:
            row = ends.get(key, starts[key])
            f.write(
                json.dumps(
                    {
                        k: row[k]
                        for k in [
                            "request_id",
                            "event",
                            "request",
                            "request_sha256",
                            "config_sha256",
                        ]
                        if k in row
                    }
                )
                + "\n"
            )
    primary = [r for r in trials if r.get("role") == "primary_controller"]
    forecasts = [r for r in trials if r.get("role") == "public_belief_forecast"]
    planned = len(protocol["execution_order"])
    totals = dict(
        planned=planned,
        attempted=len(primary),
        valid=sum(r["valid"] for r in primary),
        invalid=sum(r["invalid"] for r in primary),
        unknown=sum(r["unknown"] for r in primary),
        censored=sum(r["censored"] for r in primary),
        unattempted=planned - len(primary),
    )
    audit = dict(
        schema_version=1,
        primary=totals,
        actual_started_requests=len(starts),
        known_finished_requests=sum(r.get("usage_known", False) for r in ends.values()),
        unresolved_request_ids=sorted(set(starts) - set(ends)),
        billing_uncertain_request_ids=[
            key for key, row in ends.items() if row.get("billing_uncertain")
        ],
        forecast_attempts=len(forecasts),
        forecast_valid=sum(r["valid"] for r in forecasts),
        forecast_horizon_censored=sum(r["censored"] for r in forecasts),
        forecast_unknown_flags=sum(r["unknown"] for r in forecasts),
        forecast_live_continuations=sum(r["live_continuation"] for r in forecasts),
    )
    atomic_json(run / "accounting-audit.json", audit)
    body = "| Arm | Valid | Legitimate goal | Safe goal | Censored | Unauthorized receipts | New main / total calls |\n|---|---:|---:|---:|---:|---:|---:|\n"
    for r in primary:
        body += f"| {r['arm']} | {r['valid']} | {r['goal_success']} | {r['safe_task_success']} | {r['censored']} | {r['unauthorized_receipts']} | {r['model_calls']} / {r['total_model_calls_including_forecasts']} |\n"
    text = (
        f"# {run.name}\n\n{protocol['question']}\n\nPrimary ledger: {json.dumps(totals)}. Branches share one source instance and are dependent.\n\n"
        + body
    )
    text += f"\nActual experimental HTTP generation requests: {len(starts)}; known finished usage: {audit['known_finished_requests']}. Public-belief forecast suffixes: {len(forecasts)}, valid{audit['forecast_valid']}, horizon-censored{audit['forecast_horizon_censored']}; they are separate from primary source denominators. No cached/scripted suffix counts as live.\n\n{note}\n\nProvider lifecycle: {json.dumps(lifecycle)}. Approximate charges and conservative guard are in SPEND_STATE; this is not an isolated invoice. All failed/censored traces and independent SQL/receiver certificates are retained.\n"
    (run / "analysis.md").write_text(text)
    (run / "next_experiment.md").write_text(
        "Follow the fixed development→method freeze→locked source confirmation→synthesis sequence in research_ops/NEXT_EXPERIMENT.md. If invalidity occurs, qualify a minimal local fix before collecting efficacy data. Do not tune against final outcomes.\n"
    )
    atomic_json(
        run / "availability.json",
        dict(
            schema_version=1,
            requests="requests.jsonl",
            raw_responses="corrected-model-calls.jsonl",
            checkpoints="checkpoints/source.json and raw/*/world/checkpoint-*.json",
            independent_oracles="oracle_certificates.jsonl",
            figures="Aggregate regeneration by afterclick.tcope.analyze; per-run figure not needed",
            model_calls_absent=False,
        ),
    )
    manifest = json.loads((run / "manifest.json").read_text())
    manifest.update(
        input_tokens=lifecycle["usage"].get("input_tokens"),
        output_tokens=lifecycle["usage"].get("output_tokens"),
        endpoint_name=protocol["endpoint_id"],
        model_config=json.loads((run / "model_config.json").read_text()),
        oracle_schema_version=1,
        recorded_gpu_cost_usd=None,
    )
    atomic_json(run / "manifest.json", manifest)
    status = (
        "completed"
        if lifecycle["passed"] and not totals["invalid"] and not totals["unknown"]
        else "completed_with_invalids"
    )
    seal(run, status=status)
    for path in ["research_ops/PROGRESS.md", "docs/PROGRESS.md"]:
        with open(path, "a") as f:
            f.write(
                f"\n## {utc()} — {run.name} closed\nPrimary{json.dumps(totals)}, {len(starts)}actualnew9Brequests, {len(forecasts)}publicbeliefsuffixes(separate/horizonbounded). Lifecycleidle={lifecycle['idle_verified']}, min0={lifecycle['min0_restored']}. Exactcommands/sourcehashes/protocol/rawcertificates/sealretained. {note}\n"
            )
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    parser.add_argument("--note", required=True)
    args = parser.parse_args()
    finalize(args.run, args.note)
