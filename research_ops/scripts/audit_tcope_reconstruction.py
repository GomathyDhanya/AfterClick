"""Local counterexample: independently check copied server state and stale browser state."""

import argparse
import copy
import json
import traceback
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

from afterclick.agent.browser_observation import observe
from afterclick.agent.modal_policy import atomic_json
from afterclick.model_sprint.driver import append
from afterclick.model_sprint.records import register, seal, sha
from afterclick.tcope.gateway import ServiceGateway
from afterclick.tcope.workload_specs import workload_suite
from afterclick.tcope.workloads import WorkloadWorld


def audit(run_id):
    source = Path("artifacts/research_runs/t9-confirm07-controller-v1/checkpoints/source.json")
    protocol = dict(
        phase="E5_RECONSTRUCTION_VALIDITY_AUDIT",
        max_usd=0,
        question="Does a correct copied database fail replay because the actual browser was stale?",
        rivals=["Database copy is corrupted", "Fresh navigation loses stale client state"],
        unit="One archived source checkpoint; three dependent diagnostic certificates",
        primary_metric="Exact public observation and independent world equality, separately",
        controls=[
            "Exact archived checkpoint",
            "Explicit coherent-observation diagnostic",
            "Corrupted-world negative control",
        ],
        interpretation=(
            "Only exact original replay can validate a causal twin. Diagnostic "
            "controls cannot replace it."
        ),
        randomization=None,
        sample_size_rationale=(
            "One deterministic counterexample suffices to refute universal reconstruction"
        ),
        hyperparameter_search_budget=0,
        data_partition="Opened failed confirmation source only; no unopened source inspected",
        invalid_handling=(
            "Preserve reconstruction failures and exceptions; no model calls or efficacy labels"
        ),
        source_checkpoint=str(source),
        source_checkpoint_sha256=sha(source),
        source_hashes={str(Path(__file__).relative_to(Path.cwd())): sha(__file__)},
        exact_command=" ".join(
            [
                ".venv/bin/python",
                "-m",
                "research_ops.scripts.audit_tcope_reconstruction",
                "--run-id",
                run_id,
            ]
        ),
    )
    run = register(run_id, protocol)
    cp = json.loads(source.read_text())
    world = WorkloadWorld(
        next(t for t in workload_suite("confirmation") if t.case_id == "confirm-07")
    )
    try:
        world.initialize(cp)
        with world.serve() as origin, sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            gateway = ServiceGateway(page, origin)
            page.goto(origin)
            expect(page.get_by_label("Description", exact=True)).to_be_visible()
            expect(page.get_by_text("Live updates", exact=True)).to_be_visible()
            world.browser_ready(page)
            current = observe(gateway)
            atomic_json(run / "raw/actual-reconstructed-observation.json", current)
            atomic_json(run / "raw/original-observation.json", cp["observation"])
            atomic_json(run / "raw/copied-world.json", world.snapshot())
            exact = world.certify(cp, current)
            coherent = copy.deepcopy(cp)
            coherent["observation"] = current
            coherent_cert = world.certify(coherent, current)
            corrupt = copy.deepcopy(coherent)
            corrupt["world"]["tasks"][0]["priority"] = "Critical"
            corrupt_cert = world.certify(corrupt, current)
            rows = [
                ("exact_source", exact),
                ("diagnostic_coherent_view", coherent_cert),
                ("negative_corrupted_world", corrupt_cert),
            ]
            for name, cert in rows:
                append(
                    run / "trials.jsonl",
                    dict(
                        schema_version=1,
                        condition=name,
                        diagnostic_only=True,
                        causal_reconstruction_valid=cert["valid"],
                        model_calls=0,
                        efficacy_label=None,
                    ),
                )
                append(run / "oracle_certificates.jsonl", dict(condition=name, certificate=cert))
            result = dict(
                schema_version=1,
                attempted=3,
                diagnostic_checks_passed=3,
                exact_causal_replays_attempted=1,
                exact_causal_replays_valid=0,
                exact_causal_replays_invalid=1,
                censored=0,
                unknown=0,
                model_calls=0,
                original_inputs=cp["observation"]["inputs"],
                current_inputs=current["inputs"],
                copied_database_priority=cp["world"]["tasks"][0]["priority"],
                original_service_age_ms=cp["browser_payload"]["public_state"]["age_ms"],
                hidden_clock_ms=cp["world"]["tc_runtime"][0]["clock_ms"],
                certificates={name: cert for name, cert in rows},
            )
            assert not exact["valid"] and exact["initial_world_copied"]
            assert not exact["browser_inputs_equal"] and coherent_cert["valid"]
            assert not corrupt_cert["valid"] and not corrupt_cert["initial_world_copied"]
            atomic_json(run / "metrics.json", result)
            browser.close()
        (run / "analysis.md").write_text(
            "The original source showed Normal while its copied database already contained High. "(
                "Exact full-observation reconstruction rejects the fresh browser, "
                "despite correct world copying. "
            )(
                "An explicitly changed diagnostic observation passes; it is NOT the"
                " original causal twin. "
            )(
                "Corrupting world state still fails. No check is relaxed and no "
                "hidden state is supplied to a model. "
            )(
                "The frozen confirmation must remain inconclusive. A future replay "
                "version needs actual client-cache "
            )(
                "and update-queue reconstruction, qualified before a separately "
                "frozen evaluation. Zero paid calls.\n"
            )
        )
        (run / "next_experiment.md").write_text(
            (
                "No further paid experiment in this frozen cohort. Complete the "
                "bounded negative/validity synthesis. "
            )(
                "Future work: local client-cache/SSE reconstruction and independent"
                " evaluation preregistration.\n"
            )
        )
        atomic_json(
            run / "availability.json",
            dict(
                model_calls="none; local Chromium/PG only",
                figures=(
                    "Original and reconstructed observations saved as JSON; aggregate "
                    "figures elsewhere"
                ),
            ),
        )
        seal(run)
        print(json.dumps(result, indent=2))
    except BaseException:
        (run / "raw/error.txt").write_text(traceback.format_exc())
        append(run / "trials.jsonl", dict(event="crashed_or_interrupted", model_calls=0))
        seal(run, status="failed")
        raise
    finally:
        world.db.drop_experiment()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-id", required=True)
    audit(p.parse_args().run_id)
