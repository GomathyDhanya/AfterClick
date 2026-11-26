"Explicitly bounded live timing study; original frozen experiments are untouched."

import json
import time
import traceback
from dataclasses import replace

from playwright.sync_api import sync_playwright

from afterclick.agent.modal_policy import atomic_json
from afterclick.review.paired import paired_source
from afterclick.tcope.budget import Factory
from afterclick.tcope.driver import append
from afterclick.tcope.workload_specs import workload_suite


class TimingFactory(Factory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, _, path in self.settings.values():
            approval = json.loads(path.read_text())
            approval["authorization_source"] = "research_ops/TIMING_STUDY_AUTHORIZATION.json"
            atomic_json(path, approval)


def task(row):
    base = workload_suite()[row["template"]]
    return replace(
        base,
        case_id=row["id"],
        source_group=row["id"],
        seed=row["seed"],
        instruction=row["instruction"],
        expected=row["expected"],
        comment=row["comment"],
        schedule=row["schedule"],
        partition=row["partition"],
    )


def run_experiment(name, factory, run, deadline):
    if name != "progressing_timing_v1":
        raise ValueError("Unregistered experiment")
    protocol = factory.protocol
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            for row in protocol["cases"]:
                if time.monotonic() + protocol["minimum_source_seconds"] > deadline:
                    append(
                        run / "trials.jsonl",
                        dict(
                            source_id=row["id"], status="unattempted", reason="finite_wall_budget"
                        ),
                    )
                    continue
                started = time.monotonic()
                try:
                    result = paired_source(
                        browser,
                        task(row),
                        factory,
                        run / "raw" / row["id"],
                        deadline=time.time()
                        + min(protocol["source_seconds"], deadline - time.monotonic() - 8),
                        max_source_calls=protocol["source_call_cap"],
                        max_suffix_calls=protocol["suffix_call_cap"],
                        arms=row["arm_order"],
                        cut_rule=protocol["cut_rule"],
                        final_observation_seconds=protocol["final_observation_seconds"],
                        min_observation_clock_ms=protocol.get("min_observation_clock_ms", 0),
                    )
                    append(
                        run / "trials.jsonl",
                        dict(
                            source_id=row["id"],
                            status="completed" if result["eligible"] else "no_eligible_checkpoint",
                            elapsed_seconds=time.monotonic() - started,
                            result=result,
                        ),
                    )
                    for report in result.get("results", []):
                        append(
                            run / "oracle_certificates.jsonl",
                            dict(
                                source_id=row["id"],
                                arm=report["arm"],
                                certificate=report["initial_certificate"],
                                oracle=report["oracle"],
                            ),
                        )
                except BaseException:
                    append(
                        run / "trials.jsonl",
                        dict(
                            source_id=row["id"],
                            status="invalid",
                            elapsed_seconds=time.monotonic() - started,
                            error=traceback.format_exc(),
                        ),
                    )
                    raise  # A technical failure stops this bounded block, never replace a source.
        finally:
            browser.close()
    atomic_json(
        run / "metrics.json",
        dict(schema_version=1, status="executed_analysis_pending", usage=factory.usage()),
    )
