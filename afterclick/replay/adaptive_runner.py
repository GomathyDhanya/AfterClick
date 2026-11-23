"""Real browser pilot with live-model continuation and recorded-action placebos.

The selected workflow action is planted, not attributed to the LLM. Every policy
sees only UI/task data. Backend jobs are held during the decision window and then
released to the same horizon, regardless of API latency or continuation length.
"""

import argparse
import json
import traceback
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from playwright.sync_api import expect, sync_playwright

from afterclick import domain
from afterclick.agent.action_parser import Decision
from afterclick.agent.browser_observation import observe, public_history, public_task
from afterclick.agent.gateway import Action, Gateway
from afterclick.agent.inference import public_input
from afterclick.agent.llm_policy import Budget, GeminiPolicy, RecordedPolicy, credential
from afterclick.contracts.schema import load_contract
from afterclick.evaluation.effect_oracle import evaluate_effects
from afterclick.evaluation.pilot import CONTRACT_PATHS
from afterclick.evaluation.task_oracle import evaluate_task
from afterclick.infrastructure.db import Database, digest
from afterclick.replay.branch_compare import CONDITIONS, certify, compare
from afterclick.replay.demo import canonical, source_manifest
from afterclick.replay.semantic_alignment import evidence_edges, fixed_precondition
from afterclick.replay.server import serve


def selected_action(contract):
    return {
        "reviewed": Action("click", "Mark reviewed"),
        "priority": Action("select", "Priority", "Critical"),
        "status": Action("select", "Status", "Done"),
    }[contract.selected_action.field]


def settle(gateway, db, status="✓ Committed"):
    page = gateway.page
    page.clock.fast_forward(600)
    expect(page.get_by_role("status")).to_have_text(status)
    # A UI refresh barrier, not a model input. API activity includes committed events
    # even before outbox publication. Wait for the selected record's visible activity.
    record_id = page.locator(".task-key").inner_text().split()[0]
    events = [e for e in domain.snapshot(db)["effect_events"] if e["resource"] == record_id]
    expect(page.locator(".activity-item")).to_have_count(min(5, len(events)))
    if gateway.pending:
        raise RuntimeError("Unsettled browser mutation request")


def run_branch(
    browser,
    contract,
    name,
    *,
    policy=None,
    fixed_steps=None,
    max_steps=5,
    blind_interventions=True,
):
    condition = name.removesuffix("_placebo")
    db = Database("ac_adaptive_" + uuid4().hex)
    result = {
        "name": name,
        "valid": False,
        "steps": [],
        "policy_records": [],
        "seed": contract.seed,
        "selected_action_origin": "planted fixture intervention",
        "continuation": "adaptive" if fixed_steps is None else "fixed",
        "policy_evidence": getattr(policy, "evidence_kind", "recorded_actions"),
    }
    context = None
    policy_start = len(policy.records) if policy else 0
    try:
        db.migrate()
        domain.seed(db, seed=contract.seed)
        with serve(db) as origin:
            context = browser.new_context(viewport={"width": 1440, "height": 1000})
            page = context.new_page()
            instant = datetime(2026, 1, 1, tzinfo=timezone.utc)
            page.clock.install(time=instant)
            page.clock.pause_at(instant)
            gateway = Gateway(page, origin)
            gateway.act(Action("navigate", "/"))
            initial = domain.snapshot(db)
            result["checkpoint_state"] = initial
            result["checkpoint"] = {
                "database_hash": digest(canonical(initial)),
                # The empty storage payload has no random origin-specific data.
                "storage_hash": digest(context.storage_state()),
                "observation_hash": digest(observe(gateway)),
                "prefix_hash": digest(gateway.history),
                "pending_requests": len(gateway.pending),
                "client_clock_ms": 0,
                "logical_time": initial["runtime"][0]["logical_time"],
                "pending_jobs": initial["scheduled_jobs"],
            }
            null = condition.startswith("null_")
            action = Action("read", "Description") if null else selected_action(contract)
            if condition == "lost_ack":
                gateway.drop_ack_action = "a0002"
            suppressed = condition in {"suppress_fixed", "suppress_adaptive", "null_suppress"}
            gateway.act(action, suppress=suppressed)
            settle(gateway, db, "Failed" if condition == "lost_ack" else "✓ Committed")
            result["selected_action"] = asdict(action)
            result["post_selected_state"] = domain.snapshot(db)
            if condition == "lost_ack":
                interventions = gateway.feedback_interventions
                operations = result["post_selected_state"]["operations"]
                result["ack_evidence"] = {
                    "verified": len(interventions) == 1
                    and interventions[0]["http_status"] == 200
                    and any(o["id"] == interventions[0]["operation_id"] for o in operations)
                    and page.get_by_role("status").inner_text() == "Failed",
                    "interventions": interventions,
                }
            for step_index in range(max_steps):
                current = observe(gateway)
                if fixed_steps is None:
                    task = public_task(contract)
                    history = public_history(
                        gateway.history, blind_interventions=blind_interventions
                    )
                    public_input(task, current, history)
                    decision = policy.decide(task, current, history)
                    applicable = True
                else:
                    if step_index >= len(fixed_steps):
                        result["termination"] = "fixed_trace_exhausted"
                        break
                    original = fixed_steps[step_index]
                    decision = Decision.model_validate(original["decision"])
                    applicable = fixed_precondition(decision, original["observation"], current)
                    # A placebo retains original skips; a skipped action cannot become a write.
                    if name.endswith("_placebo") and not original["executed"]:
                        applicable = False
                step = {
                    "decision": decision.model_dump(),
                    "observation": current,
                    "executed": applicable,
                    "skip_reason": None if applicable else "semantic_precondition_changed",
                }
                result["steps"].append(step)
                if decision.kind == "done":
                    result["termination"] = "policy_done"
                    break
                if applicable:
                    gateway.act(decision.action())
                    settle(gateway, db)
            else:
                result["termination"] = "step_limit"
            result["actions"] = gateway.history
            result["requests"] = gateway.requests
            result["requests_quiescent"] = not gateway.pending
            result["final_observation"] = observe(gateway)
            result["continuation_hash"] = digest(result["steps"])
            context.close()
            context = None
        domain.advance(db, contract.horizon)
        final = domain.snapshot(db)
        result.update(
            state=final,
            outcome_hash=digest(canonical(final)),
            task=evaluate_task(contract, final),
            effects=evaluate_effects(contract, final),
            edges=evidence_edges(final),
            valid=result["requests_quiescent"],
        )
    except Exception:
        result["error"] = traceback.format_exc()
        try:
            result["state"] = domain.snapshot(db)
        except Exception:
            result["snapshot_error"] = "Could not read failed experiment state"
    finally:
        if policy:
            result["policy_records"] = policy.records[policy_start:]
        if context:
            context.close()
        db.drop_experiment()
    return result


def run_case(
    browser,
    contract,
    policy,
    directory,
    *,
    max_steps=5,
    fail_fast=False,
    blind_interventions=True,
    check_budget=None,
):
    branches = {}
    halted = False
    for condition in CONDITIONS:
        source = {"suppress_fixed": "execute", "null_suppress": "null_execute"}.get(condition)
        for suffix in ("", "_placebo"):
            name = condition + suffix
            fixed_source = condition if suffix else source
            if check_budget is not None and not halted:
                try:
                    check_budget()
                except TimeoutError:
                    halted = True
            if halted:
                branches[name] = {
                    "name": name,
                    "valid": False,
                    "attempted": False,
                    "error": "Unattempted after prior acceptance failure",
                }
            elif fixed_source and not branches.get(fixed_source, {}).get("valid"):
                branches[name] = {"name": name, "valid": False, "error": "Source trace invalid"}
            else:
                branches[name] = run_branch(
                    browser,
                    contract,
                    name,
                    policy=None if fixed_source else policy,
                    fixed_steps=branches[fixed_source]["steps"] if fixed_source else None,
                    max_steps=max_steps,
                    blind_interventions=blind_interventions,
                )
            if fail_fast and (
                not branches[name].get("valid") or not branches[name].get("task", {}).get("success")
            ):
                halted = True
            (directory / f"{name}.json").write_text(json.dumps(branches[name], indent=2))
            print(
                f"{contract.workflow_family}/seed={contract.seed}/{name}: "
                f"valid={branches[name]['valid']}",
                flush=True,
            )
    certificate = certify(branches)
    report = {
        "contract": contract.model_dump(),
        "branches": branches,
        "certificate": certificate,
        "comparison": compare(branches, certificate),
    }
    (directory / "report.json").write_text(json.dumps(report, indent=2))
    return report


def run(output, policy, *, seeds=(7, 19), paths=CONTRACT_PATHS, max_steps=5):
    run_id = uuid4().hex
    directory = output / run_id
    directory.mkdir(parents=True)
    policy.journal = directory / "model-calls.jsonl"
    report = {
        "run_id": run_id,
        "manifest": source_manifest(),
        "cases": [],
        "data_mode": getattr(policy, "evidence_kind", "test_policy"),
        "schedule": "worker=100, delivery=100; backend frozen at 0 during bounded "
        "decision window, then common horizon=300; no independent collaborators",
        "limitations": [
            "selected actions planted, not organically chosen by the model",
            "three workflows share the scripted-notification mechanism",
            "fixed-action placebos do not assert model determinism",
            "no population necessity or safety improvement estimate",
        ],
    }
    with sync_playwright() as p:
        browser = p.chromium.launch()
        report["manifest"]["browser_version"] = browser.version
        try:
            for path in paths:
                for seed in seeds:
                    contract = load_contract(path).model_copy(update={"seed": seed})
                    case_dir = directory / f"{contract.workflow_family}-{seed}"
                    case_dir.mkdir()
                    report["cases"].append(
                        run_case(browser, contract, policy, case_dir, max_steps=max_steps)
                    )
                    (directory / "report.json").write_text(json.dumps(report, indent=2))
        finally:
            browser.close()
    report["budget"] = (
        policy.usage_summary()
        if hasattr(policy, "usage_summary")
        else asdict(policy.budget)
        if hasattr(policy, "budget")
        else None
    )
    report["replay_valid"] = bool(report["cases"]) and all(
        c["certificate"]["valid"] for c in report["cases"]
    )
    report["policy_calls"] = sum(
        len(b["policy_records"])
        for c in report["cases"]
        for b in c["branches"].values()
        if "policy_records" in b
    )
    report["live_model_calls"] = sum(
        r.get("evidence_kind") in {"live_gemini", "live_modal"} and "response" in r
        for c in report["cases"]
        for b in c["branches"].values()
        for r in b.get("policy_records", [])
    )
    report["all_goals_succeeded"] = all(
        b.get("task", {}).get("success", False)
        for c in report["cases"]
        for b in c["branches"].values()
    )
    (directory / "report.json").write_text(json.dumps(report, indent=2))
    (output / "report.json").write_text(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/adaptive"))
    parser.add_argument("--seeds", type=int, nargs="+", default=[7, 19])
    parser.add_argument("--contracts", nargs="+", default=CONTRACT_PATHS)
    parser.add_argument("--max-steps", type=int, default=5)
    parser.add_argument("--max-calls", type=int, default=80)
    parser.add_argument("--budget-usd", type=float, default=0.10)
    parser.add_argument("--replay-report", type=Path)
    args = parser.parse_args()
    if not 1 <= args.max_steps <= 10:
        parser.error("max-steps must be between 1 and 10")
    if args.replay_report:
        source = json.loads(args.replay_report.read_text())
        records = [
            r
            for c in source["cases"]
            for b in c["branches"].values()
            for r in b.get("policy_records", [])
        ]
        policy = RecordedPolicy(records)
    else:
        policy = GeminiPolicy(
            credential(), Budget(ceiling_usd=args.budget_usd, max_calls=args.max_calls)
        )
    report = run(
        args.output, policy, seeds=args.seeds, paths=args.contracts, max_steps=args.max_steps
    )
    print(
        json.dumps(
            {k: report[k] for k in ("run_id", "replay_valid", "all_goals_succeeded", "budget")}
        )
    )
    if not report["replay_valid"]:
        raise SystemExit("Replay invalid; raw failures retained")
