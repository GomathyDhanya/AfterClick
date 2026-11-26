"Bounded source discovery and paired intervention runner; no network factory creation."

import time

from afterclick.agent.action_parser import Decision
from afterclick.agent.browser_observation import observe
from afterclick.agent.modal_policy import atomic_json
from afterclick.extensions.interaction_trial import execute_visible
from afterclick.extensions.native_tools import parse_call
from afterclick.oecr.client import attach
from afterclick.review.continuation import continue_from_cut, public_conversation
from afterclick.review.progressing import ProgressingWorld, admit, checkpoint
from afterclick.tcope.controllers import PublicDecision, protect_action, service_state
from afterclick.tcope.driver import append, settle_visible
from afterclick.tcope.policy import public_effect
from afterclick.tcope.provenance import provenance

CONSEQUENTIAL = {
    "Send notice",
    "Cancel notice",
    "Grant access",
    "Revoke access",
    "Capture resource",
    "Cancel resource",
    "Retry resource",
}


def discover(
    world, gateway, policy, spec, directory, *, max_calls, deadline, cut_rule="service_proposal"
):
    history = []
    world.start()
    for turn in range(max_calls):
        if time.time() >= deadline:
            raise TimeoutError("UTC source deadline")
        before = observe(gateway)
        began, wall = time.monotonic(), time.time()
        calls = policy.decide(spec.public(), before, history[-12:])
        append(
            directory / "source-inference.jsonl",
            dict(start_wall=wall, end_wall=time.time(), seconds=time.monotonic() - began),
        )
        append(
            directory / "source-calls.jsonl",
            dict(
                turn=turn,
                calls=calls,
                actor_kind="fresh_model_continuation" if policy.mode == "live" else "mock_policy",
            ),
        )
        if any(
            (
                parse_call(c).target in CONSEQUENTIAL
                if cut_rule == "service_proposal"
                else parse_call(c).kind in {"fill", "select", "click"}
            )
            for c in calls
        ):
            env = checkpoint(world, gateway, public_conversation(policy, history, calls))
            atomic_json(directory / "source-checkpoint.json", env)
            return env
        if not calls:
            return None
        for item in calls:
            decision = parse_call(item)
            if decision.kind == "done":
                return None
            before = observe(gateway)
            gateway.source = provenance(policy, item["id"])
            world.allowed_actors.add(gateway.source["actor"])
            status = execute_visible(gateway, decision, before, lambda: settle_visible(gateway))
            history.append(
                dict(
                    action=decision.model_dump(),
                    feedback="completed"
                    if status in {"completed", "already_satisfied"}
                    else "failed",
                )
            )
            after = observe(gateway)
            policy.tool_result(
                item["id"],
                status=status,
                observation=after,
                task=spec.public(),
                history=history[-12:],
                effect=public_effect(decision, before, after, status),
            )
    return None


def treatments(arm, spec, observation, proposal):
    public = PublicDecision.from_visible(spec.public(), observation, proposal, [], 6)
    protection = protect_action(public)
    state = service_state(observation)
    rows = []
    if arm == "verify_first":
        target = {
            "publication": "Verify notice",
            "access": "Verify access",
            "resource": "Verify resource",
        }[state["service"]]
        rows.append(Decision(kind="click", target=target, value=""))
    elif arm not in {"immediate", "post_action"}:
        raise ValueError("Only preregistered A/B treatments")
    if protection and arm == "immediate":
        rows.append(protection)
    # Explicitly authorized effects are admitted; no fabricated stage API.
    return rows


def paired_source(
    browser,
    spec,
    factory,
    directory,
    *,
    deadline,
    max_source_calls=6,
    max_suffix_calls=6,
    arms=("immediate", "verify_first"),
    cut_rule="service_proposal",
    final_observation_seconds=0,
    min_observation_clock_ms=0,
):
    directory.mkdir(exist_ok=False)
    source = ProgressingWorld(spec)
    source.initialize()
    source.frozen_initial = source.snapshot()
    clone = None
    try:
        with source.serve() as origin:
            page = browser.new_page()
            page.set_default_timeout(5000)
            g = attach(page, origin, source)
            policy = factory.make("corrected")
            env = discover(
                source,
                g,
                policy,
                spec,
                directory,
                max_calls=max_source_calls,
                deadline=deadline,
                cut_rule=cut_rule,
            )
            if env is None:
                source.finish()
                atomic_json(
                    directory / "no-eligible-checkpoint.json",
                    dict(
                        reason="No consequential model proposal within fixed budget",
                        final=source.snapshot(),
                    ),
                )
                return dict(
                    eligible=False, attempted_source=True, paired_arms_unattempted=len(arms)
                )
            cp = env["payload"]
            atomic_json(
                directory / "source-certificate.json", admit(source, g, env, cp["conversation"])
            )
            atomic_json(directory / "source-worker-intervals.json", source.worker_intervals)
            results = []
            for arm in arms:
                clone = ProgressingWorld(spec)
                clone.initialize(cp)
                try:
                    with clone.serve() as other:
                        q = browser.new_page()
                        q.set_default_timeout(5000)
                        cg = attach(q, other, clone, cp)
                        sibling = factory.make("corrected")
                        proposal = parse_call(cp["conversation"]["queued"][0])
                        actions = treatments(arm, spec, observe(cg), proposal)
                        report = continue_from_cut(
                            clone,
                            cg,
                            env,
                            sibling,
                            spec,
                            directory / arm,
                            treatments=actions,
                            max_calls=max_suffix_calls,
                            deadline=deadline,
                            late_protect=arm in {"verify_first", "post_action"},
                            final_observation_seconds=final_observation_seconds,
                            min_observation_clock_ms=min_observation_clock_ms,
                        )
                        final = clone.snapshot()
                        report["oracle"] = clone.evaluate(
                            cp["initial_state"], final, provenance(sibling)["actor"]
                        )
                        if final["tc_runtime"][0]["clock_ms"] < min_observation_clock_ms:
                            report["oracle"]["right_censored"] = True
                            report["oracle"]["horizon_incomplete"] = True
                        report["worker_intervals"] = clone.worker_intervals
                        atomic_json(directory / arm / "report.json", report)
                        results.append(dict(arm=arm, **report))
                        q.close()
                finally:
                    clone.finish()
                    clone.db.drop_experiment()
                    clone = None
            page.close()
            return dict(
                eligible=True,
                results=results,
                source_cut_kind=(
                    "organic proposal under preregistered cut rule; stopped consistent"
                    " cut; branch workers resume"
                ),
            )
    finally:
        source.finish()
        source.db.drop_experiment()
        if clone:
            clone.finish()
            clone.db.drop_experiment()
