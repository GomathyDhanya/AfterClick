"""Real browser / PostgreSQL live trajectory driver with no oracle feedback."""

import copy
import json
import socket
import threading
import time
import traceback
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

import uvicorn
from playwright.sync_api import expect

from afterclick import domain
from afterclick.agent.browser_observation import observe
from afterclick.agent.gateway import Action
from afterclick.agent.modal_policy import atomic_json, digest
from afterclick.api import create_app
from afterclick.extensions.interaction_trial import execute_visible
from afterclick.extensions.native_tools import parse_call
from afterclick.infrastructure.db import Database
from afterclick.model_sprint.gateway import AgentGateway
from afterclick.model_sprint.oracle import evaluate


def append(path, value):
    with Path(path).open("a") as f:
        f.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")
        f.flush()


@contextmanager
def serve_realtime(db):
    """Existing worker ticks logical +100 ms every >=100 ms of wall time.

    This is a controlled clock, not a physical real-time deadline guarantee.
    Browser timers run normally; consequences may arrive during model inference.
    """
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    app = create_app(db, auto_tick=True, static_dir="apps/flowboard-web/dist")
    server = uvicorn.Server(uvicorn.Config(app, log_level="error", timeout_graceful_shutdown=2))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    end = time.monotonic() + 15
    try:
        while not server.started:
            if not thread.is_alive() or time.monotonic() >= end:
                raise RuntimeError("Local server startup failed")
            threading.Event().wait(0.01)
        yield f"http://127.0.0.1:{sock.getsockname()[1]}"
    finally:
        app.state.stop_streams.set()
        server.should_exit = True
        thread.join(5)
        sock.close()
        if thread.is_alive():
            raise RuntimeError("Local worker did not stop")


def settle_visible(gateway):
    # Comment drafts are local, other changes autosave after 500 ms. Pump actual
    # browser events; no backend counts or scheduler state determine this barrier.
    gateway.page.wait_for_timeout(650)
    expect(gateway.page.get_by_role("status")).to_have_text("✓ Committed", timeout=5000)
    if gateway.pending:
        raise RuntimeError("Write requests remain unresolved")


def run_task(browser, spec, policy, directory, deadline, max_turns=6):
    directory = Path(directory)
    directory.mkdir()
    db = Database("ac_sprint_" + uuid4().hex)
    report = dict(
        schema_version=1,
        case_id=spec.case_id,
        source_group=spec.source_group,
        evidence_kind=policy.evidence_kind,
        selected_action_planted=False,
        organic_action=policy.mode == "live",
        model=policy.config.underlying_model,
        revision=policy.config.model_revision,
        steps=[],
        repeated_proposals=0,
        argument_errors=0,
        model_calls=0,
        valid=False,
        completed_claim=False,
    )
    context, gateway = None, None
    history = []
    task = spec.public()
    began = time.monotonic()
    try:
        db.migrate()
        domain.seed(db, seed=spec.seed, worker_delay=100, delivery_delay=100)
        report["initial_state"] = domain.snapshot(db)
        with serve_realtime(db) as origin:
            context = browser.new_context()
            context.set_default_timeout(5000)
            page = context.new_page()
            gateway = AgentGateway(page, origin)
            gateway.act(Action("navigate", "/"))
            for turn in range(max_turns):
                if time.monotonic() + policy.config.timeout_seconds + 8 >= deadline:
                    report["termination"] = "wall_budget"
                    break
                current = observe(gateway)
                calls = policy.decide(task, current, history)
                report["model_calls"] += 1
                if not calls:
                    report["completed_claim"] = current["save_status"] == "✓ Committed"
                    report["termination"] = "model_terminal_text"
                    break
                for item in calls:
                    current = observe(gateway)
                    decision = None
                    before_actions = len(gateway.history)
                    try:
                        decision = parse_call(item)
                    except (ValueError, TypeError, KeyError):
                        status = "invalid_arguments"
                        report["argument_errors"] += 1
                    else:
                        if report["completed_claim"]:
                            status = "task_finished"
                        elif decision.kind == "done":
                            # Purely public transport state, never hidden task grading.
                            report["completed_claim"] = current["save_status"] == "✓ Committed"
                            status = (
                                "completed" if report["completed_claim"] else "premature_finish"
                            )
                        else:
                            gateway.source = dict(
                                kind="llm" if policy.mode == "live" else "mock",
                                actor="llm-qwen35-4b" if policy.mode == "live" else "mock-model",
                                model=policy.config.underlying_model,
                                revision=policy.config.model_revision,
                                tool_call_id=item["id"],
                            )
                            # Research-only checkpoint, never passed to action selection.
                            atomic_json(
                                directory / f"checkpoint-{len(report['steps']):02}.json",
                                dict(
                                    schema_version=1,
                                    world=domain.snapshot(db),
                                    observation=current,
                                    history=history,
                                    messages=copy.deepcopy(policy.messages),
                                    pending_ids=sorted(policy.pending_ids),
                                    seen_ids=sorted(policy.seen_ids),
                                    proposed_call=item,
                                    prefix_actions=gateway.history,
                                    selector_access=False,
                                ),
                            )
                            status = execute_visible(
                                gateway, decision, current, lambda: settle_visible(gateway)
                            )
                            history.append(
                                dict(
                                    action=decision.model_dump(),
                                    feedback="completed"
                                    if status in {"completed", "already_satisfied"}
                                    else "failed",
                                )
                            )
                            report["repeated_proposals"] += status == "already_satisfied"
                    after_observation = observe(gateway)
                    policy.tool_result(
                        item["id"],
                        status=status,
                        task=task,
                        observation=after_observation,
                        history=history,
                    )
                    step = dict(
                        turn=turn,
                        tool_call_id=item["id"],
                        raw_call=item,
                        decision=decision.model_dump() if decision else None,
                        observation=current,
                        observation_sha256=digest(current),
                        result=after_observation,
                        status=status,
                        executed=len(gateway.history) > before_actions,
                        source=dict(
                            model=policy.config.underlying_model,
                            revision=policy.config.model_revision,
                            evidence_kind=policy.evidence_kind,
                        ),
                        intervention="none",
                    )
                    report["steps"].append(step)
                    append(directory / "steps.jsonl", step)
                    atomic_json(directory / "trace.json", report)
                if report["completed_claim"]:
                    report["termination"] = "model_finish"
                    break
            report.setdefault("termination", "turn_budget")
            report["requests_quiescent"] = not gateway.pending
            report["valid"] = not gateway.pending
            report["agent_stop_state"] = domain.snapshot(db)
            report["final_messages"] = policy.messages
    except BaseException:
        report["error"] = traceback.format_exc()
        report["termination"] = "error"
    finally:
        if context:
            context.close()
        if gateway:
            report["actions"], report["requests"] = gateway.history, gateway.requests
        try:
            now = domain.snapshot(db)["runtime"][0]["logical_time"]
            # Explicit finite post-stop observation window, not policy exposure.
            domain.advance(db, now + 1000)
            report["state"] = domain.snapshot(db)
            report["oracle"] = evaluate(
                spec,
                report["initial_state"],
                report["state"],
                expected_actor="llm-qwen35-4b" if policy.mode == "live" else "mock-model",
            )
            report["valid"] = report["valid"] and report["oracle"]["receiver_consistent"]
        except BaseException:
            report["oracle_error"] = traceback.format_exc()
            report["valid"] = False
        report["policy_usage"] = policy.usage_summary()
        report["elapsed_seconds"] = time.monotonic() - began
        atomic_json(directory / "report.json", report)
        try:
            db.drop_experiment()
        except Exception:
            (directory / "cleanup-error.txt").write_text(traceback.format_exc())
    return report
