"""Regenerate descriptive P0 metrics from saved reports; never invoke a policy/provider.

Outputs go into a NEW directory. The finalized experiment is never rewritten.
"""

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def analyze(run, output):
    output.mkdir(parents=True, exist_ok=False)
    tests = list(ET.parse(run / "raw/tests.xml").iter("testcase"))
    old_tests = list(ET.parse(ROOT / "evidence/sprint1/local-tests.xml").iter("testcase"))

    def identify(test):
        return (test.get("classname"), test.get("name"))

    added = set(map(identify, tests)) - set(map(identify, old_tests))
    removed = set(map(identify, old_tests)) - set(map(identify, tests))
    historical = []
    for folder in ("adaptive-live", "adaptive-live-second"):
        path = ROOT / "artifacts" / folder / "report.json"
        report = read(path)
        journal_path = path.parent / report["run_id"] / "model-calls.jsonl"
        journal = [json.loads(line) for line in journal_path.read_text().splitlines()]
        branches = [b for case in report["cases"] for b in case["branches"].values()]
        failures = Counter()
        traces = []
        for case in report["cases"]:
            for name, branch in case["branches"].items():
                error = branch.get("error", "")
                if not error:
                    continue
                category = (
                    "provider_generate_http_503"
                    if "HTTP 503" in error
                    else "budget_frozen_uncertain"
                    if "prior usage unknown" in error
                    else "invalid_source_trace"
                    if error == "Source trace invalid"
                    else "browser_clock_past"
                    if "Cannot fast-forward to the past" in error
                    else "other"
                )
                failures[category] += 1
                if category not in {"budget_frozen_uncertain", "invalid_source_trace"}:
                    traces.append(
                        {
                            "family": case["contract"]["workflow_family"],
                            "seed": case["contract"]["seed"],
                            "branch": name,
                            "category": category,
                            "trace": error,
                        }
                    )
        historical.append(
            {
                "run_id": report["run_id"],
                "source_path": str(path.relative_to(ROOT)),
                "report_sha256": sha(path),
                "journal_sha256": sha(journal_path),
                "source_hash": report["manifest"]["source_hash"],
                "case_attempts": len(report["cases"]),
                "valid_cases": sum(c["certificate"]["valid"] for c in report["cases"]),
                "invalid_cases": sum(not c["certificate"]["valid"] for c in report["cases"]),
                "branch_slots": len(branches),
                "valid_branches": sum(b.get("valid", False) for b in branches),
                "branch_error_categories": dict(failures),
                "primary_traces": traces,
                "generation_reservations": sum(r["status"] == "pending" for r in journal),
                "completed_generations": sum(r["status"] == "completed" for r in journal),
                "journal_rows": len(journal),
                "budget": report["budget"],
                "invoice_usd": None,
                "data_origin": "archived live continuation after planted action",
            }
        )
    dump(output / "historical_live_audit.json", historical)
    integrity = {}
    archive = ROOT / "evidence/sprint1"
    for name, expected in read(archive / "manifest.json")["files"].items():
        integrity[name] = {
            "expected": expected,
            "actual": sha(archive / name),
            "matches": expected == sha(archive / name),
        }
    dump(output / "archive_integrity.json", integrity)
    demo = read(run / "raw/demo/report.json")
    pilot = read(run / "raw/oracle-pilot/report.json")
    from afterclick.contracts.schema import TaskContract
    from afterclick.evaluation.recovery_reference import verify_recovery
    from afterclick.replay.demo import validity_certificate

    recertified_demo = validity_certificate(demo["branches"])
    certificates = [
        {
            "schema_version": 1,
            "case_id": "demo",
            "report_run_id": demo["run_id"],
            "certificate": recertified_demo,
            "matches_saved": recertified_demo == demo["replay_certificate"],
        }
    ]
    strata = defaultdict(list)
    for case in pilot["cases"]:
        saved = case["certificate"]
        recomputed = verify_recovery(
            TaskContract.model_validate(case["contract"]),
            case["before"],
            case["after"],
            case["reference"],
            "selected",
            reference_validated=case["reference_certificate"]["valid"],
            requests_quiescent=saved["requests_quiescent"],
            horizon_complete=saved["horizon_complete"],
        )
        certificates.append(
            {
                "schema_version": 1,
                "case_id": case["contract"]["workflow_family"] + "/" + case["mode"],
                "report_run_id": pilot["run_id"],
                "certificate": recomputed,
                "matches_saved": recomputed == saved,
            }
        )
        strata[(case["contract"]["workflow_family"], case["contract"]["seed"])].append(case)
    fields = (
        "scenario_family effect_mechanism template_id seed observation_hash action_hash "
        "schedule_genome_hash branch replay_valid invalid_reasons selected_action_planted "
        "organic_action goal_succeeded authorized forbidden_effect_occurred "
        "first_irreversible_elapsed_ms event_time_right_censored horizon_ms "
        "recovery_attempt_elapsed_ms recovery_class verified_residual_effects "
        "collaborator_edits_preserved oracle_reference_hash execution_wall_ms errors"
    ).split()
    trials = []
    for name, branch in demo["branches"].items():
        row = dict.fromkeys(fields)
        row.update(
            schema_version=1,
            run_id=run.name,
            report_run_id=demo["run_id"],
            case_id="demo/" + name,
            scenario_family="legacy-review",
            seed=branch["seed"],
            effect_mechanism="scripted_notification_receipt",
            template_id=demo["contract"]["task_id"],
            branch=name,
            replay_valid=branch["valid"],
            invalid_reasons=[],
            selected_action_planted=True,
            organic_action=False,
            goal_succeeded=branch["goal_success"],
            horizon_ms=branch["horizon"],
            recovery_attempt_elapsed_ms=branch["recovery_start"],
            recovery_class=branch.get("recovery_certificate", {}).get("classification"),
            model_calls=0,
            input_tokens=0,
            output_tokens=0,
            billed_or_estimated_usd=0,
            raw_reference="raw/demo/" + demo["run_id"] + "/report.json",
            raw_report_sha256=sha(run / "raw/demo/report.json"),
            missing_label_reason="legacy schema: absent standardized labels remain null",
        )
        trials.append(row)
    for case in pilot["cases"]:
        row = dict.fromkeys(fields)
        certificate = case["certificate"]
        row.update(
            schema_version=1,
            run_id=run.name,
            report_run_id=pilot["run_id"],
            case_id=case["contract"]["workflow_family"] + "/" + case["mode"],
            scenario_family=case["contract"]["workflow_family"],
            seed=case["contract"]["seed"],
            effect_mechanism="scripted_notification_receipt",
            template_id=case["contract"]["contract_id"],
            branch=case["mode"],
            replay_valid=case["reference_certificate"]["valid"],
            invalid_reasons=[],
            selected_action_planted=True,
            organic_action=False,
            goal_succeeded=certificate["goal_preserved"],
            first_irreversible_elapsed_ms=certificate["first_verified_irreversible_time"],
            horizon_ms=certificate["observation_horizon"],
            recovery_class=certificate["classification"],
            verified_residual_effects=certificate["residuals"],
            collaborator_edits_preserved=certificate["independent_edits_preserved"],
            oracle_reference_hash=hashlib.sha256(
                json.dumps(case["reference_certificate"], sort_keys=True).encode()
            ).hexdigest(),
            model_calls=0,
            input_tokens=0,
            output_tokens=0,
            billed_or_estimated_usd=0,
            raw_reference="raw/oracle-pilot/" + pilot["run_id"] + "/report.json",
            raw_report_sha256=sha(run / "raw/oracle-pilot/report.json"),
            missing_label_reason=(
                "No P6 survival-label pipeline; censoring flag and unmeasured fields remain null. "
                "See raw horizon_complete/requests_quiescent/receipt witnesses."
            ),
        )
        trials.append(row)
    (output / "normalized_trials.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in trials)
    )
    (output / "oracle_certificates.jsonl").write_text(
        "".join(json.dumps(c) + "\n" for c in certificates)
    )
    stages = [read(p) for p in sorted((run / "raw").glob("*.result.json"))]
    metrics = {
        "schema_version": 1,
        "run_id": run.name,
        "analysis_kind": "descriptive regression audit",
        "commands": {
            "attempted": len(stages),
            "passed": sum(s["exit_code"] == 0 for s in stages),
            "failed": sum(s["exit_code"] != 0 for s in stages),
        },
        "tests": {
            "attempted": len(tests),
            "passed": sum(
                not any(t.find(x) is not None for x in ("failure", "error", "skipped"))
                for t in tests
            ),
            "failed": sum(
                t.find("failure") is not None or t.find("error") is not None for t in tests
            ),
            "skipped": sum(t.find("skipped") is not None for t in tests),
            "historical_sprint_count": len(old_tests),
            "added_count": len(added),
            "removed_count": len(removed),
            "added_by_module": dict(Counter(k[0] for k in added)),
        },
        "demo": {
            "run_id": demo["run_id"],
            "attempted": len(demo["branches"]),
            "valid": sum(b["valid"] for b in demo["branches"].values()),
            "invalid": sum(not b["valid"] for b in demo["branches"].values()),
            "certificate_valid": recertified_demo["valid"],
            "acceptance": demo["milestone_acceptance"],
            "recovery_classes": {
                n: b["recovery_certificate"]["classification"]
                for n, b in demo["branches"].items()
                if "recovery_certificate" in b
            },
        },
        "oracle_pilot": {
            "run_id": pilot["run_id"],
            "attempted": len(pilot["cases"]) + len(pilot["errors"]),
            "valid_references": sum(c["reference_certificate"]["valid"] for c in pilot["cases"]),
            "invalid": sum(not c["reference_certificate"]["valid"] for c in pilot["cases"])
            + len(pilot["errors"]),
            "expected_class_matches": sum(c["passed"] for c in pilot["cases"]),
            "classes": dict(Counter(c["certificate"]["classification"] for c in pilot["cases"])),
            "by_family_seed": [
                {
                    "family": family,
                    "seed": seed,
                    "attempted": len(cases),
                    "class_matches": sum(c["passed"] for c in cases),
                    "classes": dict(Counter(c["certificate"]["classification"] for c in cases)),
                }
                for (family, seed), cases in strata.items()
            ],
        },
        "oracle_certificates_recomputed": len(certificates),
        "all_certificates_match": all(c["matches_saved"] for c in certificates),
        "historical_live": {
            "attempted_cases": sum(r["case_attempts"] for r in historical),
            "valid_cases": sum(r["valid_cases"] for r in historical),
            "invalid_cases": sum(r["invalid_cases"] for r in historical),
            "generations_attempted": sum(r["generation_reservations"] for r in historical),
            "generations_completed": sum(r["completed_generations"] for r in historical),
        },
        "archive_files_verified": len(integrity),
        "all_archive_hashes_match": all(v["matches"] for v in integrity.values()),
        "fresh_model_calls": 0,
        "modal_cost_usd": 0,
        "actual_remaining_credit_usd": None,
        "confidence_intervals": None,
        "confidence_interval_reason": (
            "fixed development fixtures share mechanism/seed; no independent population sampling"
        ),
        "calibration_discrimination_search_shield_metrics": None,
        "unmeasured_reason": "no learned model, equal-budget search, or runtime shield in P0",
    }
    dump(output / "metrics.json", metrics)
    dump(
        output / "source_comparison.json",
        [
            {
                "run_id": r["run_id"],
                "matches_current_manifest": r["source_hash"] == demo["manifest"]["source_hash"],
            }
            for r in historical
        ],
    )
    dump(output / "tests_delta.json", {"added": sorted(added), "removed": sorted(removed)})
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    analyze(args.run.resolve(), args.output.resolve())
