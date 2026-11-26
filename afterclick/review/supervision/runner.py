"""Certified actor/supervisor branches, real tools, advancing workers and private scoring."""

import copy
import json
import time
import traceback
from pathlib import Path

from playwright.sync_api import sync_playwright

from afterclick.agent.browser_observation import observe
from afterclick.agent.modal_policy import atomic_json
from afterclick.extensions.native_tools import parse_call
from afterclick.oecr.client import attach
from afterclick.review.continuation import public_conversation
from afterclick.review.paired import discover
from afterclick.review.progressing import admit, resume
from afterclick.review.study_runner import TimingFactory, task
from afterclick.review.supervision.gateway import Enforcer
from afterclick.review.supervision.policy import Reviewer
from afterclick.review.supervision.world import SupervisionWorld
from afterclick.tcope.driver import append
from afterclick.tcope.provenance import provenance


class SupervisionFactory(TimingFactory):
    def admit(self):
        if self.transport is None:
            ledger = json.loads(Path("research_ops/TIMING_SPEND_STATE.json").read_text())
            active = ledger.get("active")
            if (
                not active
                or active["run_id"] != self.run.name
                or not active["category"].startswith("supervision_")
            ):
                raise ValueError("Active conserved supervision reservation required")
        super().admit()

    def rows(self):
        rows = super().rows()
        path = self.run / "supervisor-model-calls.jsonl"
        if path.exists():
            rows += [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
        return rows

    def reviewer(self):
        return Reviewer(self)


def continuation(
    world, gateway, envelope, policy, spec, directory, arm, factory, *, deadline, max_calls, horizon
):
    directory.mkdir(exist_ok=False)
    saved = envelope["payload"]["conversation"]
    policy.messages = copy.deepcopy(saved["messages"])
    policy.pending_ids = set(saved["pending_ids"])
    policy.seen_ids = set(saved["seen_ids"])
    history = copy.deepcopy(saved["history"])
    queued = copy.deepcopy(saved["queued"])
    certificate = admit(world, gateway, envelope, public_conversation(policy, history, queued))
    atomic_json(directory / "certificate.json", certificate)
    reviewer = factory.reviewer() if arm in {"C2", "C3"} else None
    enforcer = Enforcer(arm, world, gateway, policy, spec, directory, reviewer)
    fresh_calls = 0
    finished = False
    error = None
    inference_seconds = 0
    started = time.time()
    resume(world, gateway)
    try:
        while not finished:
            if time.time() >= deadline:
                raise TimeoutError("Finite source UTC deadline")
            if queued:
                calls = queued
                queued = []
                origin = "recorded_source_proposal"
            else:
                if fresh_calls >= max_calls:
                    break
                begin = time.time()
                calls = policy.decide(spec.public(), observe(gateway), history[-12:])
                fresh_calls += 1
                inference_seconds += time.time() - begin
                append(
                    directory / "actor-inference.jsonl",
                    dict(start_wall=begin, end_wall=time.time(), seconds=time.time() - begin),
                )
                origin = "fresh_model_continuation" if policy.mode == "live" else "mock_policy"
            if not calls:
                break
            for item in calls:
                decision = parse_call(item)
                if finished:
                    policy.tool_result(
                        item["id"],
                        status="task_finished",
                        observation=observe(gateway),
                        task=spec.public(),
                        history=history[-12:],
                    )
                elif decision.kind == "done":
                    finished = True
                    policy.tool_result(
                        item["id"],
                        status="completed",
                        observation=observe(gateway),
                        task=spec.public(),
                        history=history[-12:],
                    )
                    append(
                        directory / "completion-claims.jsonl",
                        dict(tool_call_id=item["id"], wall=time.time()),
                    )
                else:
                    enforcer.execute(item, decision, history, origin)
        # Real elapsed observation, not a logical future jump; leave time after last action too.
        tail_end = time.time() + 3
        while time.time() < deadline and (world.elapsed() < horizon + 70 or time.time() < tail_end):
            gateway.page.wait_for_timeout(100)
    except BaseException:
        error = traceback.format_exc()
        (directory / "error.txt").write_text(error)
        raise
    finally:
        world.finish()
        final = world.snapshot()
        atomic_json(directory / "final.json", final)
        atomic_json(directory / "conversation.json", public_conversation(policy, history, queued))
        atomic_json(directory / "worker-intervals.json", world.worker_intervals)
        atomic_json(
            directory / "gateway-journal.json",
            dict(actions=gateway.history, requests=gateway.requests),
        )
        report = dict(
            schema_version=1,
            initial_certificate=certificate,
            new_actor_generations=fresh_calls if policy.mode == "live" else 0,
            actor_policy_calls=fresh_calls,
            supervisor_reviews=enforcer.review_count,
            finished_claim=finished,
            actor_inference_seconds=inference_seconds,
            controller_seconds=enforcer.controller_seconds,
            elapsed_seconds=time.time() - started,
            error=bool(error),
            observed_clock_ms=final["tc_runtime"][0]["clock_ms"],
        )
        report["oracle"] = world.evaluate(
            envelope["payload"]["initial_state"], final, provenance(policy)["actor"]
        )
        if final["tc_runtime"][0]["clock_ms"] < horizon:
            report["oracle"]["right_censored"] = True
        atomic_json(directory / "report.json", report)
    return report


def source_trial(browser, row, factory, directory, deadline, protocol):
    spec = task(row)
    directory.mkdir(exist_ok=False)
    source = SupervisionWorld(spec)
    source.initialize()
    source.frozen_initial = source.snapshot()
    try:
        with source.serve() as origin:
            page = browser.new_page()
            page.set_default_timeout(5000)
            g = attach(page, origin, source)
            policy = factory.make("corrected")
            envelope = discover(
                source,
                g,
                policy,
                spec,
                directory,
                max_calls=protocol["source_call_cap"],
                deadline=deadline,
                cut_rule="service_proposal"
                if row["condition"] == "pre_dispatch"
                else "first_mutating_batch",
            )
            if envelope is None:
                return dict(
                    eligible=False,
                    reason="No organically proposed eligible action within fixed prefix cap",
                    source_attempted=True,
                )
            cp = envelope["payload"]
            atomic_json(
                directory / "source-certificate.json",
                admit(source, g, envelope, cp["conversation"]),
            )
            atomic_json(directory / "source-worker-intervals.json", source.worker_intervals)
            results = []
            for arm in row["arm_order"]:
                clone = SupervisionWorld(spec)
                clone.initialize(cp)
                try:
                    with clone.serve() as other:
                        q = browser.new_page()
                        q.set_default_timeout(5000)
                        cg = attach(q, other, clone, cp)
                        actor = factory.make("corrected")
                        report = continuation(
                            clone,
                            cg,
                            envelope,
                            actor,
                            spec,
                            directory / arm,
                            arm,
                            factory,
                            deadline=deadline,
                            max_calls=protocol["suffix_call_cap"],
                            horizon=protocol["min_observation_clock_ms"],
                        )
                        results.append(dict(arm=arm, **report))
                        q.close()
                finally:
                    clone.finish()
                    clone.db.drop_experiment()
            page.close()
            return dict(eligible=True, results=results)
    finally:
        source.finish()
        source.db.drop_experiment()


def run_experiment(name, factory, run, deadline):
    if name != "independent_supervision_v1":
        raise ValueError("Wrong registered experiment")
    p = factory.protocol
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            for row in p["cases"]:
                if time.monotonic() + p["minimum_source_seconds"] >= deadline:
                    append(
                        run / "trials.jsonl",
                        dict(
                            source_id=row["id"], status="unattempted", reason="finite wall budget"
                        ),
                    )
                    continue
                try:
                    result = source_trial(
                        browser,
                        row,
                        factory,
                        run / "raw" / row["id"],
                        time.time() + min(p["source_seconds"], deadline - time.monotonic() - 8),
                        p,
                    )
                    append(
                        run / "trials.jsonl",
                        dict(
                            source_id=row["id"],
                            status="completed" if result["eligible"] else "ineligible",
                            result=result,
                        ),
                    )
                    for r in result.get("results", []):
                        append(
                            run / "oracle_certificates.jsonl",
                            dict(
                                source_id=row["id"],
                                arm=r["arm"],
                                certificate=r["initial_certificate"],
                                oracle=r["oracle"],
                            ),
                        )
                except BaseException:
                    append(
                        run / "trials.jsonl",
                        dict(
                            source_id=row["id"],
                            status="interrupted_or_invalid",
                            error=traceback.format_exc(),
                        ),
                    )
                    raise
        finally:
            browser.close()
    atomic_json(
        run / "metrics.json",
        dict(schema_version=1, status="execution_complete_analysis_pending", usage=factory.usage()),
    )
