"""Run real browser execute/suppress trials and verified recovery schedules.

All scenarios are synthetic planted fixtures. Outputs are measured system executions,
not population estimates, learned-model results, or general irreversibility proofs.
"""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from playwright.sync_api import expect, sync_playwright

from afterclick import domain
from afterclick.agent.gateway import Action, Gateway
from afterclick.infrastructure.db import Database, digest
from afterclick.recovery.oracle import goal, verify
from afterclick.recovery.planner import compensate_review
from afterclick.replay.server import serve


def canonical(state):
    # Receipt timing/count is asynchronous transport telemetry, not a business effect.
    # Everything else (including queued work, publication, ownership, versions) is compared.
    return {key: value for key, value in state.items() if key != "sse_receipts"}


def source_manifest():
    paths = [
        p
        for root in ("afterclick", "migrations", "fixtures", "apps/flowboard-web/src")
        for p in Path(root).rglob("*")
        if p.is_file()
        and "__pycache__" not in str(p)
        and not any(part.startswith(".") for part in p.parts)
    ]
    paths += [
        Path(p) for p in ("pyproject.toml", "uv.lock", "apps/flowboard-web/package-lock.json")
    ]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    image = subprocess.run(
        ["docker", "image", "inspect", "postgres:17.7", "--format", "{{json .RepoDigests}}"],
        capture_output=True,
        text=True,
    )
    return {
        "source_hash": digest(hashes),
        "source_files": hashes,
        "git_commit": commit.stdout.strip() if commit.returncode == 0 else None,
        "git_dirty": bool(status.stdout),
        "python": platform.python_version(),
        "dependencies": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
        "postgres_image_digests": json.loads(image.stdout) if image.returncode == 0 else [],
        "application_image_digest": None,
        "application_runtime": "local source; source_hash substitutes for container digest",
        "frontend_build_hashes": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path("apps/flowboard-web/dist").rglob("*")
            if p.is_file()
        },
    }


def branch(
    browser, name, *, suppress=False, recovery_time=None, reference=None, collaborator=False, seed=7
):
    db = Database("ac_run_" + uuid4().hex)
    db.migrate()
    domain.seed(db, seed=seed)
    result = {
        "name": name,
        "schema": db.schema,
        "seed": seed,
        "intervention": "suppress mark_reviewed" if suppress else "execute mark_reviewed",
        "recovery_start": recovery_time,
        "horizon": 300,
        "valid": False,
    }
    context = None
    try:
        with serve(db) as origin:
            context = browser.new_context(viewport={"width": 1440, "height": 1000})
            page = context.new_page()
            instant = datetime(2026, 1, 1, tzinfo=timezone.utc)
            page.clock.install(time=instant)
            page.clock.pause_at(instant)
            gateway = Gateway(page, origin)
            gateway.act(Action("navigate", "/"))
            gateway.act(Action("fill", "Description", "Document the API v2 integration."))
            page.clock.fast_forward(600)
            expect(page.get_by_role("status")).to_have_text("✓ Committed")
            domain.advance(db, 0)
            expect(page.get_by_text("Task updated", exact=True)).to_be_visible()
            expect(page.get_by_text("Version 2", exact=True)).to_be_visible()
            initial = domain.snapshot(db)
            checkpoint = {
                "database_hash": digest(canonical(initial)),
                "browser_storage_hash": digest(context.storage_state()),
                "observation_hash": digest(gateway.observe()),
                "action_prefix_hash": digest(gateway.history),
                "pending_write_requests": len(gateway.pending),
                "pending_jobs": [
                    j["id"] for j in initial["scheduled_jobs"] if j["status"] == "pending"
                ],
                "logical_time": initial["runtime"][0]["logical_time"],
                "client_clock_ms": 600,
                "client_debounce_settled": True,
                "reconstruction": "fresh fixture + deterministic browser prefix",
            }
            result["checkpoint"] = checkpoint
            result["checkpoint_state"] = initial
            gateway.act(Action("click", "Mark reviewed"), suppress=suppress)
            page.clock.fast_forward(600)
            expect(page.get_by_role("status")).to_have_text("✓ Committed")
            if not suppress:
                expect(page.get_by_role("button", name="✓ Reviewed", exact=True)).to_be_visible()
            result["actions"] = gateway.history
            result["requests"] = gateway.requests
            # All mutation responses are acknowledged before closing the client. Closing
            # does not claim to snapshot JS; checkpoint reconstruction replays the prefix.
            result["requests_quiescent"] = not gateway.pending
            context.close()
            context = None
            if not result["requests_quiescent"] or checkpoint["pending_write_requests"]:
                raise RuntimeError("Checkpoint or continuation has an unsettled write request")
            if recovery_time is not None:
                domain.advance(db, recovery_time)
                if collaborator:
                    current = domain.snapshot(db)["tasks"][0]
                    domain.patch_task(
                        db,
                        "TASK-42",
                        {"reviewed": True},
                        current["version"],
                        "collaborator",
                        "collaborator",
                        "scripted-human",
                    )
                result["pre_recovery_state"] = domain.snapshot(db)
                result["recovery_attempt"] = compensate_review(db, "a0003")
                if reference is not None:
                    result["attempt_certificate"] = verify(
                        result["pre_recovery_state"],
                        domain.snapshot(db),
                        reference,
                        "a0003",
                        requests_quiescent=result["requests_quiescent"],
                        horizon_complete=False,
                    )
                    result["attempt_certificate"]["verification_time"] = recovery_time
            domain.advance(db, 300)
            final = domain.snapshot(db)
            result["state"] = final
            result["outcome_hash"] = digest(canonical(final))
            result["goal_success"] = goal(final)
            if recovery_time is not None:
                if reference is None:
                    raise ValueError("Recovery verification requires a suppressed reference")
                result["recovery_certificate"] = verify(
                    result["pre_recovery_state"],
                    final,
                    reference,
                    "a0003",
                    requests_quiescent=result["requests_quiescent"],
                    horizon_complete=True,
                )
            result["valid"] = True
    except Exception:
        result["error"] = traceback.format_exc()
        result["state"] = domain.snapshot(db)
    finally:
        if context:
            context.close()
        db.drop_experiment()
    return result


def validity_certificate(branches):
    required = ["execute", "execute_placebo", "suppress", "suppress_placebo", "early", "late"]
    missing = [name for name in required if name not in branches or not branches[name]["valid"]]
    if missing:
        return {"valid": False, "missing_or_failed_branches": missing}
    checkpoints = [branches[name]["checkpoint"] for name in required]
    same = all(c == checkpoints[0] for c in checkpoints)
    placebo = all(
        branches[name]["outcome_hash"] == branches[name + "_placebo"]["outcome_hash"]
        for name in ("execute", "suppress")
    )
    return {
        "valid": same and placebo,
        "initial_equivalence": same,
        "identical_continuation_placebos_match": placebo,
        "checkpoint_hashes": {n: digest(branches[n]["checkpoint"]) for n in required},
        "excluded_from_equivalence": ["SSE consumer receipt identity/count"],
        "fixed": [
            "fixture",
            "browser action prefix",
            "seed=7",
            "worker_delay=100",
            "delivery_delay=100",
            "horizon=300",
        ],
        "interventions": [
            "selected review tool call executed/suppressed",
            "recovery starts at logical time 99 or 200",
        ],
        "scope": "quiescent prefix, fixed continuation, one planted workflow, no adaptive LLM",
    }


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "run_id": uuid4().hex,
        "data_mode": "measured executions of synthetic planted fixture",
        "manifest": source_manifest(),
        "contract": json.loads(Path("fixtures/tasks/description-review.json").read_text()),
        "branches": {},
    }
    branches = report["branches"]
    run_dir = output / report["run_id"]
    run_dir.mkdir()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        report["manifest"]["browser_version"] = browser.version
        try:
            for name in (
                "execute",
                "execute_placebo",
                "suppress",
                "suppress_placebo",
                "early",
                "late",
                "conflict",
            ):
                print(f"Running {name}…", flush=True)
                reference = branches.get("suppress", {}).get("state")
                branches[name] = branch(
                    browser,
                    name,
                    suppress=name.startswith("suppress"),
                    recovery_time={"early": 99, "late": 200, "conflict": 150}.get(name),
                    reference=reference,
                    collaborator=name == "conflict",
                )
                (run_dir / f"{name}.json").write_text(json.dumps(branches[name], indent=2))
        finally:
            browser.close()
    report["replay_certificate"] = validity_certificate(branches)
    if report["replay_certificate"]["valid"]:
        executed, suppressed = branches["execute"], branches["suppress"]
        report["fixture_findings"] = {
            "goal_success_execute": executed["goal_success"],
            "goal_success_suppress": suppressed["goal_success"],
            "fixture_goal_difference": int(executed["goal_success"])
            - int(suppressed["goal_success"]),
            "selected_action_semantic_effects": [
                e
                for e in executed["state"]["effect_events"]
                if e["action_id"] == "a0003" and e["kind"] != "outbox.published"
            ],
            "recovery_early": branches["early"]["recovery_certificate"]["classification"],
            "recovery_late": branches["late"]["recovery_certificate"]["classification"],
            "conflict_at_attempt": branches["conflict"]
            .get("attempt_certificate", {})
            .get("classification"),
            "conflict_branch_final": branches["conflict"]
            .get("recovery_certificate", {})
            .get("classification"),
            "population_necessity_label": "NOT_ESTIMATED",
            "boundary_claim": (
                "Verified witness at two sampled recovery-start times; "
                "not a globally minimal boundary"
            ),
        }
    report["milestone_acceptance"] = {
        "replay_valid": report["replay_certificate"]["valid"],
        "all_branches_completed": all(b["valid"] for b in branches.values()),
        "all_goals_succeeded": all(b.get("goal_success", False) for b in branches.values()),
        "expected_recovery_classes": all(
            branches[name].get("recovery_certificate", {}).get("classification") == expected
            for name, expected in {
                "early": "VERIFIED_RECOVERABLE",
                "late": "VERIFIED_UNRECOVERABLE",
            }.items()
        ),
        "overlapping_edit_conflict_verified": (
            branches["conflict"].get("attempt_certificate", {}).get("classification") == "CONFLICT"
            and branches["conflict"]
            .get("attempt_certificate", {})
            .get("independent_edits_preserved")
            and branches["conflict"].get("recovery_attempt", {}).get("status") == "CONFLICT"
        ),
    }
    (output / "report.json").write_text(json.dumps(report, indent=2))
    (run_dir / "report.json").write_text(json.dumps(report, indent=2))
    from afterclick.replay.viewer import render

    render(report, output / "explorer.html")
    render(report, run_dir / "explorer.html")
    print(json.dumps(report.get("fixture_findings", report["replay_certificate"]), indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/demo"))
    args = parser.parse_args()
    report = run(args.output)
    if not all(report["milestone_acceptance"].values()):
        raise SystemExit("Milestone check failed; all trial evidence is retained in report.json")
