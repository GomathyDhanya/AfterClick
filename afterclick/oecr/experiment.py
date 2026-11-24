"""Bounded genuine-policy continuations from controlled application-state cuts.

No hidden world or certification value enters the policy. These source cuts are
scripted fixtures; subsequent tool proposals are fresh model generations.
"""

import copy
import json
import time
import traceback
from dataclasses import replace

from playwright.sync_api import sync_playwright

from afterclick.agent.browser_observation import observe
from afterclick.agent.modal_policy import atomic_json
from afterclick.extensions.interaction_trial import execute_visible
from afterclick.extensions.native_tools import parse_call
from afterclick.oecr.client import attach, capture, certify, validate
from afterclick.tcope.driver import append, settle_visible
from afterclick.tcope.policy import public_effect
from afterclick.tcope.provenance import provenance
from afterclick.tcope.workload_specs import workload_suite
from afterclick.tcope.workloads import WorkloadWorld


def task(row):
    base = workload_suite()[6 if row["kind"] == "priority" else 7]
    changes = (
        {"priority": row["new_value"]}
        if row["kind"] == "priority"
        else {"description": row["new_value"]}
    )
    return replace(
        base,
        case_id=row["id"],
        source_group=row["id"],
        seed=row["seed"],
        instruction=row["instruction"],
        expected={},
        comment=None,
        schedule=dict(edit_ms=200, collaborator_changes=changes),
    )


def conversation(policy):
    return dict(
        messages=copy.deepcopy(policy.messages),
        pending_ids=sorted(policy.pending_ids),
        seen_ids=sorted(policy.seen_ids),
        history=[],
    )


def continue_policy(world, gateway, policy, spec, directory, max_turns):
    directory.mkdir()
    history = []
    rows = []
    completed = False
    began = time.monotonic()
    inference = 0
    browser_seconds = 0
    initial = world.snapshot()
    report = dict(
        schema_version=1,
        case_id=spec.case_id,
        model_calls=0,
        valid=True,
        source_kind="scripted_cut",
        continuation_kind="fresh_model_continuation" if policy.mode == "live" else "mock_policy",
        argument_errors=0,
        repeated_actions=0,
    )
    seen = set()
    try:
        for turn in range(max_turns):
            observation = observe(gateway)
            start = time.monotonic()
            calls = policy.decide(spec.public(), observation, history[-12:])
            inference += time.monotonic() - start
            report["model_calls"] += 1
            atomic_json(directory / f"observation-{turn}.json", observation)
            if not calls:
                report["termination"] = "terminal_text"
                break
            for item in calls:
                decision = None
                before = observe(gateway)
                started = time.monotonic()
                try:
                    decision = parse_call(item)
                except (ValueError, TypeError, KeyError):
                    status = "invalid_arguments"
                    report["argument_errors"] += 1
                else:
                    key = json.dumps(decision.model_dump(), sort_keys=True)
                    report["repeated_actions"] += int(key in seen)
                    seen.add(key)
                    if completed:
                        status = "task_finished"
                    elif decision.kind == "done":
                        completed = True
                        status = "completed"
                    else:
                        gateway.source = provenance(
                            policy,
                            item["id"],
                            kind="fresh_model_continuation"
                            if policy.mode == "live"
                            else "mock_policy",
                        )
                        world.allowed_actors.add(gateway.source["actor"])
                        status = execute_visible(
                            gateway, decision, before, lambda: settle_visible(gateway)
                        )
                        history.append(
                            dict(
                                action=decision.model_dump(),
                                feedback="completed"
                                if status in {"completed", "already_satisfied"}
                                else "failed",
                            )
                        )
                after = observe(gateway)
                duration = time.monotonic() - started
                browser_seconds += duration
                row = dict(
                    turn=turn,
                    tool_call=item,
                    action=decision.model_dump() if decision else None,
                    status=status,
                    actor_kind="model_selected",
                    observation_before=before,
                    observation_after=after,
                    browser_seconds=duration,
                )
                rows.append(row)
                append(directory / "actions.jsonl", row)
                policy.tool_result(
                    item["id"],
                    status=status,
                    observation=after,
                    task=spec.public(),
                    history=history[-12:],
                    effect=public_effect(decision, before, after, status),
                )
            if completed:
                report["termination"] = "finish_claim"
                break
        else:
            report["termination"] = "call_cap"
    except BaseException:
        report.update(valid=False, error=traceback.format_exc(), termination="execution_error")
        raise
    finally:
        final = world.snapshot()
        atomic_json(directory / "initial.json", initial)
        atomic_json(directory / "final.json", final)
        atomic_json(directory / "conversation.json", conversation(policy))
        atomic_json(
            directory / "gateway.json", dict(actions=gateway.history, requests=gateway.requests)
        )
        # Private, independent SQL records. Never used to drive policy decisions.
        comments = [x["body"] for x in final["task_comments"]]
        report.update(
            completed_claim=completed,
            comment_bodies=comments,
            final_task=next(x for x in final["tasks"] if x["id"] == "TASK-42"),
            mock_receipts=len(final["tc_receipts"]),
            inference_seconds=inference,
            browser_seconds=browser_seconds,
            elapsed_seconds=time.monotonic() - began,
            actions=[r["action"] for r in rows],
            initial_state_sha256=None,
        )
        atomic_json(directory / "report.json", report)
    return report


def run_experiment(name, factory, run, deadline):
    protocol = factory.protocol
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            for row in protocol["cases"]:
                source = WorkloadWorld(task(row))
                source.initialize()
                source.frozen_initial = source.snapshot()
                try:
                    with source.serve() as origin:
                        page = browser.new_page()
                        page.set_default_timeout(5000)
                        sg = attach(page, origin, source)
                        page.evaluate("window.oecr.pause()")
                        source.browser_pause(page)
                        source.step(
                            250
                        )  # deterministic exogenous collaborator, NOT an agent action
                        template = factory.make("corrected")
                        env = capture(source, sg, conversation(template))
                        cp = validate(env)
                        atomic_json(run / "raw" / f"{row['id']}-checkpoint.json", env)
                        for arm in row["arm_order"]:
                            if time.monotonic() + 45 >= deadline:
                                raise TimeoutError("Insufficient bounded trial time")
                            began = time.monotonic()
                            factory.begin_trial(protocol["per_continuation_calls"])
                            policy = factory.make("corrected")
                            policy.messages = copy.deepcopy(cp["conversation"]["messages"])
                            policy.pending_ids = set(cp["conversation"]["pending_ids"])
                            policy.seen_ids = set(cp["conversation"]["seen_ids"])
                            clone = None
                            try:
                                if arm == "source":
                                    cert = certify(source, sg, cp, conversation(policy))
                                    gw = sg
                                    world = source
                                    assert cert["valid"], cert
                                    atomic_json(
                                        run / "raw" / f"{row['id']}-{arm}-certificate.json", cert
                                    )
                                    overhead = time.monotonic() - began
                                    report = continue_policy(
                                        world,
                                        gw,
                                        policy,
                                        task(row),
                                        run / "raw" / f"{row['id']}-{arm}",
                                        protocol["per_continuation_calls"],
                                    )
                                else:
                                    clone = WorkloadWorld(task(row))
                                    clone.initialize(cp)
                                    with clone.serve() as other:
                                        q = browser.new_page()
                                        q.set_default_timeout(5000)
                                        gw = attach(
                                            q, other, clone, cp if arm == "faithful" else None
                                        )
                                        q.evaluate("window.oecr.pause()")
                                        clone.browser_pause(q)
                                        cert = certify(clone, gw, cp, conversation(policy))
                                        if arm == "faithful":
                                            assert cert["valid"], cert
                                        # Fresh is invalid as a sibling; diagnostic only.
                                        atomic_json(
                                            run / "raw" / f"{row['id']}-{arm}-certificate.json",
                                            cert,
                                        )
                                        overhead = time.monotonic() - began
                                        report = continue_policy(
                                            clone,
                                            gw,
                                            policy,
                                            task(row),
                                            run / "raw" / f"{row['id']}-{arm}",
                                            protocol["per_continuation_calls"],
                                        )
                                        q.close()
                                result = dict(
                                    source=row["id"],
                                    kind=row["kind"],
                                    arm=arm,
                                    certificate=cert,
                                    causal_valid=cert["valid"],
                                    reconstruction_seconds=overhead,
                                    report=report,
                                )
                                append(run / "trials.jsonl", result)
                                append(
                                    run / "oracle_certificates.jsonl",
                                    dict(source=row["id"], arm=arm, **cert),
                                )
                            except BaseException:
                                append(
                                    run / "trials.jsonl",
                                    dict(
                                        source=row["id"],
                                        arm=arm,
                                        status="crashed",
                                        error=traceback.format_exc(),
                                    ),
                                )
                                raise
                            finally:
                                factory.end_trial()
                                if clone:
                                    clone.db.drop_experiment()
                        page.close()
                finally:
                    source.db.drop_experiment()
        finally:
            browser.close()
