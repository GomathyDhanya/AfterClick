"""Gateway-native continuation from an admitted progressing cut, with public history.

No provider transport is created here. Supplied policy must be mock or externally
budgeted. Treatments are labeled controller-imposed, pending source calls remain
recorded proposals, and only subsequent decide calls are fresh generations.
"""

import copy
import time

from afterclick.agent.action_parser import Decision
from afterclick.agent.browser_observation import observe
from afterclick.agent.modal_policy import atomic_json
from afterclick.extensions.interaction_trial import execute_visible
from afterclick.extensions.native_tools import parse_call
from afterclick.review.progressing import admit, resume
from afterclick.tcope.controllers import PublicDecision, protect_action
from afterclick.tcope.driver import append, settle_visible
from afterclick.tcope.policy import public_effect
from afterclick.tcope.provenance import provenance


def public_conversation(policy, history, queued):
    return dict(
        messages=copy.deepcopy(policy.messages),
        pending_ids=sorted(policy.pending_ids),
        seen_ids=sorted(policy.seen_ids),
        history=copy.deepcopy(history),
        queued=copy.deepcopy(queued),
    )


def continue_from_cut(
    world,
    gateway,
    envelope,
    policy,
    spec,
    directory,
    *,
    treatments=(),
    max_calls=6,
    deadline,
    late_protect=False,
    final_observation_seconds=0,
    min_observation_clock_ms=0,
):
    directory.mkdir(exist_ok=False)
    cp = envelope["payload"]
    saved = cp["conversation"]
    policy.messages = copy.deepcopy(saved["messages"])
    policy.pending_ids = set(saved["pending_ids"])
    policy.seen_ids = set(saved["seen_ids"])
    history = copy.deepcopy(saved.get("history", []))
    queued = copy.deepcopy(saved.get("queued", []))
    cert = admit(world, gateway, envelope, public_conversation(policy, history, queued))
    atomic_json(directory / "certificate.json", cert)
    calls_used = 0
    finished = False
    inference = tool_seconds = 0.0
    seen_actions = set()
    resume(world, gateway)
    try:
        for treatment in treatments:
            before = time.monotonic()
            gateway.source = dict(
                actor="controller",
                kind="controller_imposed",
                model=None,
                revision=None,
                tool_call_id=None,
            )
            world.allowed_actors.add("controller")
            status = execute_visible(
                gateway, treatment, observe(gateway), lambda: settle_visible(gateway)
            )
            append(
                directory / "treatments.jsonl",
                dict(
                    action=treatment.model_dump(),
                    status=status,
                    actor_kind="controller_imposed",
                    wall=time.time(),
                    start_wall=time.time() - (time.monotonic() - before),
                    seconds=time.monotonic() - before,
                ),
            )
            if status not in {"completed", "already_satisfied"}:
                raise RuntimeError("Treatment failed")
        while not finished:
            if time.time() >= deadline:
                raise TimeoutError("UTC continuation deadline")
            if queued:
                calls = queued
                queued = []
                origin = "recorded_source_proposal"
            else:
                if calls_used >= max_calls:
                    break
                observation = observe(gateway)
                began = time.monotonic()
                wall = time.time()
                calls = policy.decide(spec.public(), observation, history[-12:])
                calls_used += 1
                elapsed = time.monotonic() - began
                inference += elapsed
                append(
                    directory / "inference.jsonl",
                    dict(start_wall=wall, end_wall=time.time(), seconds=elapsed),
                )
                origin = "fresh_model_continuation" if policy.mode == "live" else "mock_policy"
                if late_protect:
                    late_protect = False
                    proposal = (
                        parse_call(calls[0])
                        if calls
                        else Decision(kind="read", target="Description", value="")
                    )
                    protective = protect_action(
                        PublicDecision.from_visible(
                            spec.public(), observe(gateway), proposal, [], 1
                        )
                    )
                    if protective:
                        gateway.source = dict(
                            actor="controller",
                            kind="controller_imposed",
                            model=None,
                            revision=None,
                            tool_call_id=None,
                        )
                        world.allowed_actors.add("controller")
                        start_protection = time.time()
                        status = execute_visible(
                            gateway, protective, observe(gateway), lambda: settle_visible(gateway)
                        )
                        append(
                            directory / "treatments.jsonl",
                            dict(
                                action=protective.model_dump(),
                                status=status,
                                actor_kind="controller_imposed",
                                wall=time.time(),
                                start_wall=start_protection,
                                seconds=time.time() - start_protection,
                            ),
                        )
                        if status not in {"completed", "already_satisfied"}:
                            raise RuntimeError("Late treatment failed")
            if not calls:
                break
            for item in calls:
                before = observe(gateway)
                decision = parse_call(item)
                began = time.monotonic()
                key = str(decision.model_dump())
                repeated = key in seen_actions
                seen_actions.add(key)
                if decision.kind == "done":
                    finished = True
                    status = "completed"
                else:
                    gateway.source = provenance(policy, item["id"], kind=origin)
                    world.allowed_actors.add(gateway.source["actor"])
                    status = execute_visible(
                        gateway, decision, before, lambda: settle_visible(gateway)
                    )
                duration = time.monotonic() - began
                tool_seconds += duration
                after = observe(gateway)
                if decision.kind != "done":
                    history.append(
                        dict(
                            action=decision.model_dump(),
                            feedback="completed"
                            if status in {"completed", "already_satisfied"}
                            else "failed",
                        )
                    )
                policy.tool_result(
                    item["id"],
                    status=status,
                    observation=after,
                    task=spec.public(),
                    history=history[-12:],
                    effect=public_effect(decision, before, after, status),
                )
                append(
                    directory / "actions.jsonl",
                    dict(
                        action=decision.model_dump(),
                        status=status,
                        actor_kind=origin,
                        tool_call_id=item["id"],
                        repeated=repeated,
                        tool_seconds=duration,
                    ),
                )
        # Finite real observation tail; never fabricate future logical-time jumps.
        tail_end = min(time.time() + final_observation_seconds, deadline)
        while time.time() < deadline and (
            time.time() < tail_end or world.elapsed() < min_observation_clock_ms + 50
        ):
            gateway.page.wait_for_timeout(min(100, max(1, int((deadline - time.time()) * 1000))))
        return dict(
            initial_certificate=cert,
            new_generation_requests=calls_used if policy.mode == "live" else 0,
            policy_decision_calls=calls_used,
            finished_claim=finished,
            inference_seconds=inference,
            tool_seconds=tool_seconds,
            observation_clock_ms=world.elapsed(),
            required_observation_clock_ms=min_observation_clock_ms,
        )
    finally:
        world.finish()
        atomic_json(directory / "final.json", world.snapshot())
        atomic_json(
            directory / "final-conversation.json", public_conversation(policy, history, queued)
        )
