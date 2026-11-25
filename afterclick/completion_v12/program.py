"""Derive a truthful completion manifest. Never substitutes design slots for tasks or runs."""

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from afterclick.completion_v12.contracts import KIT, enrollment, verify_kit
from afterclick.completion_v12.evidence import sha
from afterclick.completion_v12.verify_graphs import verify


def write(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def audit(output):
    output.mkdir(parents=True, exist_ok=False)
    inventory = enrollment()
    write(output / "task-registry.json", inventory)
    (output / "task-registry.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in inventory["rows"])
    )
    base = Path("artifacts/research_runs")
    graph = base / "v12-01-historical-graphs-attempt-1/graphs"
    graph_check = verify(Path.cwd(), graph)
    write(output / "graph-verification.json", graph_check)
    enforcement = base / "v12-04-enforcement-delay-v1"
    protocol = json.loads((enforcement / "protocol.json").read_text())
    manifest = json.loads((enforcement / "execution-manifest.json").read_text())
    if {r["trial_id"] for r in protocol["rows"]} != {r["trial_id"] for r in manifest}:
        raise ValueError("Missing registered local experiment cell")
    (output / "execution-manifest.jsonl").write_text(
        "".join(
            json.dumps(dict(study="LOCAL_LEGACY_ENFORCEMENT_MECHANISM", **row), sort_keys=True)
            + "\n"
            for row in manifest
        )
    )
    planned = json.loads((KIT / "manifests/prospective_counts.json").read_text())
    claims = [
        dict(
            claim="Historical graph cohort",
            metric="branches",
            value=42,
            file=str(graph / "summary.json"),
            population="36 frozen confirmation + 6 supervisor DEV",
        ),
        dict(
            claim="Legacy exact finite closure comparison",
            metric="repair_exists",
            value=10,
            file=str(base / "v12-02-finite-qualification/summary.json"),
            population="256 authored Boolean states; fixed-time API only",
        ),
        dict(
            claim="Temporal game qualification",
            metric="states",
            value=141,
            file=str(base / "v12-02-temporal-formal-qualification/summary.json"),
            population="Declared six-tick example; no empirical rate",
        ),
        dict(
            claim="Local enforcement experiment",
            metric="valid",
            value=60,
            file=str(base / "v12-04-enforcement-analysis-v2/summary.json"),
            population="3 legacy fixtures, 2 seed worlds, 10 continuations per cut",
        ),
    ]
    for claim in claims:
        data = json.loads(Path(claim["file"]).read_text())
        measured = (
            len(data[claim["metric"]]) if claim["metric"] == "branches" else data[claim["metric"]]
        )
        if measured != claim["value"]:
            raise ValueError("Claim-to-evidence mismatch")
        claim["file_sha256"] = sha(claim["file"])
    (output / "evidence-ledger.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in claims)
    )
    result = dict(
        schema_version=1,
        utc=datetime.now(timezone.utc).isoformat(),
        research_complete=False,
        kit_integrity=verify_kit(),
        task_authoring_status=inventory["counts"],
        planned_test_contracts=216,
        planned_dev_contracts=72,
        authored_dev_contracts=sum(
            r["split"] == "dev" and r["status"] != "NOT_AUTHORED" for r in inventory["rows"]
        ),
        authored_test_contracts=sum(
            r["split"] == "test" and r["status"] != "NOT_AUTHORED" for r in inventory["rows"]
        ),
        test_protocol_frozen=False,
        new_model_test_executions=0,
        new_model_calls=0,
        planned_primary_model_executions=planned["total_primary_model_proposed_executions"],
        planned_second_model_core=planned["second_model_full_core_proposed_executions"],
        registered_local_mechanism_trials=protocol["count"],
        local_trial_statuses=dict(Counter(r["status"] for r in manifest)),
        new_v12_paid_compute_usd=0,
        endpoint_credit_ceiling_usd=18,
        graph_verification=graph_check,
        remaining_requirements=[
            "Author and qualify remaining 71 DEV and all 216 structurally diverse TEST contracts",
            "Extend both application backends to all six workflow families and complexity levels",
            "Complete P0-P5 native-model harness, replay and effective-commit instrumentation",
            "Run complete genuine DEV competence/calibration and source-clustered power analysis",
            "Freeze source/model/protocol/randomization/retry manifests before TEST",
            "Execute 9,720 primary-model and 8,424 second-model episodes, "
            "or preregister a justified revision before TEST",
            "Execute official unchanged external TEST benchmark; verify prior-work code and claims",
            "Complete independent scoring, statistics, attribution, manuscript and artifact",
        ],
        next_work="Earliest incomplete milestone: complete task environments and contracts",
    )
    write(output / "execution-summary.json", result)
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in ["remaining_requirements"]}, indent=2
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    audit(parser.parse_args().output)
