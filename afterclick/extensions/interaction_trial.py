"""Same development browser task and shared visible driver for both interaction formats."""

import time
import traceback
from datetime import datetime, timezone
from uuid import uuid4

from afterclick import domain
from afterclick.agent.browser_observation import observe, public_task
from afterclick.agent.gateway import Action, Gateway
from afterclick.agent.modal_policy import atomic_json
from afterclick.evaluation.effect_oracle import evaluate_effects
from afterclick.evaluation.task_oracle import evaluate_task
from afterclick.extensions.native_tools import NativeToolPolicy, parse_call
from afterclick.infrastructure.db import Database
from afterclick.replay.adaptive_runner import settle
from afterclick.replay.server import serve


def visibly_complete(task, observation):
    labels = dict(
        description="Description", priority="Priority", status="Status", assignee="Assignee"
    )
    if observation["save_status"] != "✓ Committed" or not task["goals"]:
        return False
    for goal in task["goals"]:
        if (
            goal["table"] != "tasks"
            or goal["record_id"] != "TASK-42"
            or goal["field"] not in labels
        ):
            return False
        value = observation["inputs"][labels[goal["field"]]]
        if goal["operator"] == "contains":
            if str(goal["value"]) not in value:
                return False
        elif value != goal["value"]:
            return False
    return True


def execute_visible(gateway, decision, observation, settle_action):
    if decision.kind == "done":
        raise ValueError("Finish is not a Gateway operation")
    if (
        decision.kind in {"fill", "select"}
        and observation["save_status"] == "✓ Committed"
        and observation["inputs"].get(decision.target) == decision.value
    ):
        return "already_satisfied"
    if decision.kind == "click" and not any(
        c["role"] == "button" and c["name"] == decision.target and c["enabled"]
        for c in observation["controls"]
    ):
        return "invalid_arguments"
    try:
        gateway.act(decision.action())
        settle_action()
    except Exception:
        return "gateway_error"
    return "completed"


def run_task(browser, contract, policy, directory, deadline, max_turns=6):
    directory.mkdir()
    db = Database("ac_format_" + uuid4().hex)
    result = dict(
        schema_version=1,
        format="native_tools" if isinstance(policy, NativeToolPolicy) else "json_schema",
        selected_action_planted=False,
        valid=False,
        accepted=False,
        steps=[],
        repeated_proposals=0,
        executed_repetitions=0,
        argument_errors=0,
        model_calls=0,
    )
    context = None
    history = []
    task = public_task(contract)
    try:
        db.migrate()
        domain.seed(db, seed=contract.seed)
        with serve(db) as origin:
            context = browser.new_context()
            context.set_default_timeout(5000)
            page = context.new_page()
            instant = datetime(2026, 1, 1, tzinfo=timezone.utc)
            page.clock.install(time=instant)
            page.clock.pause_at(instant)
            gateway = Gateway(page, origin)
            gateway.act(Action("navigate", "/"))
            result["initial_state"] = domain.snapshot(db)
            completed = False
            consecutive_repeats = 0
            for turn in range(max_turns):
                if time.monotonic() + policy.config.timeout_seconds + 7 > deadline:
                    result["termination"] = "wall_budget"
                    break
                current = observe(gateway)
                response = policy.decide(task, current, history)
                result["model_calls"] += 1
                native = isinstance(policy, NativeToolPolicy)
                items = response if native else [response]
                if native and not items:
                    completed = visibly_complete(task, current)
                    result["termination"] = (
                        "terminal_text_verified" if completed else "premature_terminal_text"
                    )
                    break
                for item in items:
                    current = observe(gateway)
                    decision = None
                    try:
                        decision = parse_call(item) if native else item
                    except (ValueError, TypeError, KeyError):
                        status = "invalid_arguments"
                        result["argument_errors"] += 1
                    else:
                        if completed:
                            status = "task_finished"
                        elif decision.kind == "done":
                            completed = visibly_complete(task, current)
                            status = "completed" if completed else "premature_finish"
                        else:
                            status = execute_visible(
                                gateway, decision, current, lambda: settle(gateway, db)
                            )
                            history.append(
                                dict(
                                    action=decision.model_dump(),
                                    feedback="completed" if status == "completed" else "failed",
                                )
                            )
                            if status == "already_satisfied":
                                result["repeated_proposals"] += 1
                    if native:
                        policy.tool_result(
                            item["id"],
                            status=status,
                            task=task,
                            observation=observe(gateway),
                            history=history,
                        )
                    consecutive_repeats = (
                        consecutive_repeats + 1 if status == "already_satisfied" else 0
                    )
                    result["steps"].append(
                        dict(
                            turn=turn,
                            observation=current,
                            decision=decision.model_dump() if decision else None,
                            status=status,
                            tool_call_id=item.get("id") if native else None,
                        )
                    )
                    atomic_json(directory / "trace.json", result)
                if completed:
                    result["termination"] = "finish_verified"
                    break
                if consecutive_repeats >= 2:
                    result["termination"] = "repeated_satisfied_action"
                    break
            result.setdefault("termination", "turn_budget")
            result["executed_repetitions"] = sum(
                a["action"]["kind"] in {"fill", "select"}
                and a["pre_observation"]["inputs"].get(a["action"]["target"])
                == a["action"]["value"]
                and a["feedback"]["status"] == "completed"
                for a in gateway.history
            )
            result["actions"] = gateway.history
            result["requests"] = gateway.requests
            result["requests_quiescent"] = not gateway.pending
            result["valid"] = completed and not gateway.pending
    except BaseException:
        result["error"] = traceback.format_exc()
        result["termination"] = "error"
    finally:
        if context:
            context.close()
        try:
            domain.advance(db, contract.horizon)
            result["state"] = domain.snapshot(db)
            result["task"] = evaluate_task(contract, result["state"])
            result["effects"] = evaluate_effects(contract, result["state"])
            result["accepted"] = (
                result["valid"]
                and result["task"]["success"]
                and not result["effects"]["unauthorized_event_ids"]
            )
        except Exception:
            result["oracle_error"] = traceback.format_exc()
        result["policy_usage"] = policy.usage_summary()
        result["policy_records"] = policy.records
        atomic_json(directory / "report.json", result)
        db.drop_experiment()
    return result
