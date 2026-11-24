"""Paired real-policy controller suffixes; private engine separated from selector."""

import copy
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from afterclick.agent.browser_observation import observe
from afterclick.agent.modal_policy import InferenceError, atomic_json
from afterclick.extensions.interaction_trial import execute_visible
from afterclick.tcope.controllers import Controller, PublicDecision, service_state
from afterclick.tcope.driver import append, run_task, settle_visible
from afterclick.tcope.forecasts import ForecastEngine
from afterclick.tcope.provenance import provenance
from afterclick.tcope.workload_specs import workload_suite
from afterclick.tcope.workloads import WorkloadWorld


class Bridge:
    """Trusted engine adapter. The selector receives only a typed public projection."""

    def __init__(self, arm, spec, policy, factory, directory):
        self.arm, self.spec, self.policy, self.factory = arm, spec, policy, factory
        self.directory = Path(directory)
        self.directory.mkdir(parents=True)
        self.engines = []
        self.active = None
        self.interventions = 0
        self.intervention_cap = factory.protocol.get("intervention_cap", 4)
        self.controller = Controller(
            arm,
            rollout=self.forecast,
            stage=self.stage,
            log=lambda row: append(self.directory / "selector.jsonl", row),
            latency_prior_ms=factory.protocol.get("latency_prior_ms", 1000),
            latency_placebo_ms=factory.protocol.get("latency_placebo_ms", 0),
        )

    def stage(self, decision):
        self.reserve_intervention()
        cp, world, gateway = self.active
        gateway.source = provenance(
            self.policy,
            cp["proposed_call"]["id"],
            kind="imposed_intervention",
            intervention=self.arm,
        )
        world.allowed_actors.add(gateway.source["actor"])
        before = time.monotonic()
        status = execute_visible(
            gateway, decision, observe(gateway), lambda: settle_visible(gateway)
        )
        append(
            self.directory / "protective-actions.jsonl",
            dict(
                action=decision.model_dump(),
                status=status,
                elapsed_ms=(time.monotonic() - before) * 1000,
                actual_source=copy.deepcopy(gateway.source),
            ),
        )
        if status not in {"completed", "already_satisfied"}:
            raise RuntimeError("Supported protective action failed: " + status)

    def reserve_intervention(self):
        if self.interventions >= self.intervention_cap:
            raise InferenceError("intervention_budget_exhausted")
        self.interventions += 1

    def forecast(self, public, candidate):
        cp, world, gateway = self.active
        # Refresh only actual PUBLIC observations after staging. No actual world
        # snapshot, realized schedule, oracle or task-private fields enter forecast.
        refreshed = PublicDecision.from_visible(
            public.task.model_dump(),
            observe(gateway),
            public.proposal,
            public.latency_ms,
            self.factory.remaining_trial_calls(),
        )
        conversation = {
            key: copy.deepcopy(cp[key])
            for key in [
                "messages",
                "history",
                "pending_ids",
                "seen_ids",
                "batch_remaining",
                "source",
            ]
        }
        engine = ForecastEngine(
            self.factory,
            self.directory / ("decision-" + str(len(self.engines))),
            conversation,
            seed=711 + len(self.engines) * 13,
        )
        self.engines.append(engine)
        return engine(refreshed, candidate)

    def __call__(self, cp, decision, world, browser, gateway):
        self.active = (cp, world, gateway)
        rows = self.factory.rows()
        latencies = [float(r["latency_ms"]) for r in rows if r.get("latency_ms") is not None]
        public = PublicDecision.from_visible(
            self.spec.public(),
            cp["observation"],
            decision,
            latencies[-80:],
            self.factory.remaining_trial_calls(),
        )
        began = time.monotonic()
        chosen = self.controller.choose(public)
        if chosen and chosen["kind"] not in {"execute", "noop", "preexecuted"}:
            self.reserve_intervention()
        append(
            self.directory / "timing.jsonl",
            dict(
                elapsed_ms=(time.monotonic() - began) * 1000,
                public_age_ms=service_state(public.observation).get("age_ms"),
                original_worker_not_paused=True,
                chosen=chosen,
            ),
        )
        return chosen

    def finish(self):
        for engine in self.engines:
            engine.join()
        return [row for engine in self.engines for row in engine.results]


def comparison(factory, run, deadline):
    from afterclick.tcope.experiments import record

    protocol = factory.protocol
    spec = next(
        t for t in workload_suite(protocol["partition"]) if t.case_id == protocol["case_id"]
    )
    rows = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            if protocol.get("checkpoint_path"):
                checkpoint = json.loads(Path(protocol["checkpoint_path"]).read_text())
            else:
                factory.begin_trial(protocol["parent_call_cap"])
                policy = factory.make()
                parent = run_task(
                    browser,
                    spec,
                    policy,
                    run / "raw/source-parent",
                    deadline,
                    max_turns=protocol["max_turns"],
                    world=WorkloadWorld(spec),
                )
                record(run, spec, "source-parent", parent, role="source_parent", family=spec.family)
                policy.close()
                factory.end_trial()
                paths = sorted((run / "raw/source-parent").glob("checkpoint-*.json"))
                if not parent["valid"] or not paths:
                    raise RuntimeError("Source prefix invalid; no fabricated checkpoint")
                checkpoint = json.loads(paths[0].read_text())
            atomic_json(run / "checkpoints/source.json", checkpoint)
            for arm in protocol["execution_order"]:
                if time.monotonic() + 40 >= deadline or factory.usage()["uncertain"]:
                    break
                factory.begin_trial(protocol["trial_call_cap"])
                calls_before = factory.usage()["calls"]
                policy = factory.make()
                bridge = Bridge(arm, spec, policy, factory, run / "raw" / arm / "controller")
                result = run_task(
                    browser,
                    spec,
                    policy,
                    run / "raw" / arm / "world",
                    deadline,
                    max_turns=protocol["max_turns"],
                    checkpoint=checkpoint,
                    world=WorkloadWorld(spec),
                    interceptor=bridge,
                )
                forecasts = bridge.finish()
                rows.append(
                    record(
                        run,
                        spec,
                        arm,
                        result,
                        role="primary_controller",
                        family=spec.family,
                        total_model_calls_including_forecasts=factory.usage()["calls"]
                        - calls_before,
                        forecast_count=len(forecasts),
                    )
                )
                for index, row in enumerate(forecasts):
                    record(
                        run,
                        row["spec"],
                        arm + "-forecast-" + str(index),
                        row["result"],
                        role="public_belief_forecast",
                        exact_actual_world=False,
                    )
                policy.close()
                factory.end_trial()
        finally:
            browser.close()
    atomic_json(
        run / "metrics.json",
        dict(
            schema_version=1,
            planned=len(protocol["execution_order"]),
            attempted=len(rows),
            valid=sum(r["valid"] for r in rows),
            invalid=sum(r["invalid"] for r in rows),
            unknown=sum(r["unknown"] for r in rows),
            censored=sum(r["censored"] for r in rows),
            primary_rows=rows,
            paired_source_groups=1,
            dependent_branches=True,
            actual_world_private_used_by_online_selector=False,
        ),
    )
