"""One no-cost causal probe, never represented as a new LLM continuation."""

import argparse
import json
import time
import traceback
from pathlib import Path
from uuid import uuid4

from playwright.sync_api import sync_playwright

from afterclick import domain
from afterclick.agent.browser_observation import observe
from afterclick.agent.gateway import Action
from afterclick.agent.modal_policy import atomic_json, digest
from afterclick.infrastructure.db import Database
from afterclick.model_sprint.driver import append, serve_realtime, settle_visible
from afterclick.model_sprint.gateway import AgentGateway
from afterclick.model_sprint.oracle import evaluate
from afterclick.model_sprint.tasks import suite


def probe(run):
    protocol = json.loads((run / "protocol.json").read_text())
    if (run / "raw/started.json").exists() or protocol["max_usd"] != 0:
        raise ValueError("Fresh local-only diagnostic required")
    source = Path("artifacts/research_runs") / protocol["source_run"]
    source = source / "raw" / protocol["source_case"] / "report.json"
    parent = json.loads(source.read_text())
    spec = next(t for t in suite() if t.case_id == protocol["source_case"])
    prefix = [s for s in parent["steps"] if s["decision"]["kind"] != "done"]
    atomic_json(run / "raw/started.json", dict(paid=False, source=str(source)))
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            for arm in protocol["branches"]:
                db = Database("ac_diagnostic_" + uuid4().hex)
                report = dict(
                    schema_version=1,
                    branch=arm,
                    valid=False,
                    live_model_calls=0,
                    prefix_source="recorded_qwen_proposals",
                    continuation_source="deterministic_controller",
                    errors=[],
                )
                context = None
                began = time.monotonic()
                try:
                    db.migrate()
                    domain.seed(db, seed=spec.seed)
                    initial = domain.snapshot(db)
                    with serve_realtime(db) as origin:
                        context = browser.new_context()
                        context.set_default_timeout(5000)
                        gateway = AgentGateway(context.new_page(), origin)
                        gateway.act(Action("navigate", "/"))
                        for step in prefix:
                            gateway.source = dict(
                                kind="recorded_model_replay",
                                actor="local-replay",
                                model=parent["model"],
                                revision=parent["revision"],
                                tool_call_id=step["tool_call_id"],
                            )
                            d = step["decision"]
                            gateway.act(Action(d["kind"], d["target"], d["value"]))
                            settle_visible(gateway)
                        report["before_continuation"] = observe(gateway)
                        report["prefix_inputs_match"] = (
                            report["before_continuation"]["inputs"]
                            == prefix[-1]["result"]["inputs"]
                        )
                        # Only visible instruction and currently enabled Post control
                        # motivate this diagnostic action. No oracle guides execution.
                        gateway.source = dict(
                            kind="scripted_controller",
                            actor="local-replay",
                            model=None,
                            revision=None,
                            tool_call_id=None,
                        )
                        if arm == "read_placebo":
                            gateway.act(Action("read", "Comment"))
                        elif arm == "post_commit":
                            gateway.act(Action("click", "Post"))
                            settle_visible(gateway)
                        elif arm != "original_finish":
                            raise ValueError("Unregistered diagnostic arm")
                        report["after_continuation"] = observe(gateway)
                        report["actions"] = gateway.history
                        report["valid"] = report["prefix_inputs_match"] and not gateway.pending
                    now = domain.snapshot(db)["runtime"][0]["logical_time"]
                    domain.advance(db, now + 1000)
                    report["state"] = domain.snapshot(db)
                    report["oracle"] = evaluate(
                        spec, initial, report["state"], expected_actor="local-replay"
                    )
                    report["valid"] = report["valid"] and report["oracle"]["receiver_consistent"]
                except BaseException:
                    report["errors"].append(traceback.format_exc())
                finally:
                    if context:
                        context.close()
                    report["elapsed_seconds"] = time.monotonic() - began
                    atomic_json(run / "raw" / (arm + ".json"), report)
                    append(
                        run / "trials.jsonl",
                        dict(
                            schema_version=1,
                            case_id=spec.case_id,
                            branch=arm,
                            valid=report["valid"],
                            errors=report["errors"],
                            goal_success=report.get("oracle", {}).get("goal_success"),
                            live_model_calls=0,
                            selected_action_planted=False,
                            continuation_source="deterministic_controller",
                        ),
                    )
                    oracle = report.get("oracle", {})
                    append(
                        run / "oracle_certificates.jsonl",
                        dict(branch=arm, certificate=oracle, certificate_sha256=digest(oracle)),
                    )
                    db.drop_experiment()
                    results.append(report)
        finally:
            browser.close()
    metrics = dict(
        schema_version=1,
        attempted=3,
        valid=sum(r["valid"] for r in results),
        invalid=sum(not r["valid"] for r in results),
        unknown=0,
        censored=sum(r.get("oracle", {}).get("right_censored", True) for r in results),
        live_model_calls=0,
        modal_cost_usd=0,
        success_by_branch={r["branch"]: r.get("oracle", {}).get("goal_success") for r in results},
    )
    atomic_json(run / "metrics.json", metrics)
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, required=True)
    probe(p.parse_args().run)
