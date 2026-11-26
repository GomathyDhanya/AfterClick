"""Executed bad-history/local-repair counterexamples in both independent apps.

These are deterministic oracle challenges, not model efficacy results. Each
branch starts from a separately initialized cut and changes a consequential
choice through the same visible browser interface.
"""

import argparse
import json
import traceback
from pathlib import Path

from playwright.sync_api import sync_playwright

from afterclick.completion_v12.benchmark.browser import Browser
from afterclick.completion_v12.benchmark.flow import FlowWorld
from afterclick.completion_v12.benchmark.ops import OpsWorld
from afterclick.completion_v12.benchmark.oracle import evaluate
from afterclick.completion_v12.benchmark.qualification import reference
from afterclick.completion_v12.benchmark.transport import save
from afterclick.completion_v12.evidence import digest, sha


class WrongExternal:
    def __init__(self, gateway):
        self.gateway, self.changed = gateway, None
        self.page = gateway.page

    def observe(self):
        return self.gateway.observe()

    def act(self, identifier, value=""):
        record = next((r for r in self.observe()["records"] if r["id"] == identifier), None)
        if record and record["kind"] == "external" and self.changed is None:
            self.changed = identifier
            value = record["choices"][2]
        return self.gateway.act(identifier, value)


def execute(contracts, qualification, output):
    output.mkdir(parents=True, exist_ok=False)
    selected = [p for p in sorted(contracts.glob("DEV-*-L3-*-01.json"))]
    assert len(selected) == 12
    save(
        output / "registration.json",
        dict(
            mode="EXECUTED_ORACLE_COUNTEREXAMPLES_NOT_LLM",
            contracts={p.name: sha(p) for p in selected},
            count=12,
            intervention="First actual external business action uses forbidden public choice; "
            "then its local scope is corrected after physical delivery",
            source_qualification=str(qualification),
            model_calls=0,
        ),
    )
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for path in selected:
            contract = json.loads(path.read_text())
            folder = output / contract["task_id"]
            folder.mkdir()
            world = (FlowWorld if contract["application"] == "flowboard" else OpsWorld)(
                contract, admission_ms=3000
            )
            row = dict(task_id=contract["task_id"], status="NOT_RUN", model_calls=0)
            try:
                world.initialize()
                with world.serve() as origin:
                    page = browser.new_page()
                    gateway = Browser(page, origin, contract["application"])
                    cut = dict(
                        database=world.snapshot(),
                        public=gateway.observe(),
                        client=gateway.client_cut(),
                        contract_sha256=digest(contract),
                        schedule=dict(
                            seed=world.seed,
                            admission_ms=world.admission_ms,
                            effect_lag_ms=world.effect_lag_ms,
                            evidence_ms=world.evidence_ms,
                            collaborator_ms=world.collaborator_ms,
                        ),
                    )
                    save(folder / "source-cut.json", cut)
                    world.start()
                    gateway.start_polling()
                    intervention = WrongExternal(gateway)
                    reference(intervention)
                    before = world.snapshot()
                    save(folder / "bad-history-before-repair.json", before)
                    save(folder / "oracle-before.json", evaluate(contract, before, world.errors))
                    changed = next(
                        r for r in gateway.observe()["records"] if r["id"] == intervention.changed
                    )
                    gateway.act(changed["id"], changed["choices"][0])
                    reference(gateway)
                    page.wait_for_timeout(350)
                    world.finish()
                    final = world.snapshot()
                    score = evaluate(contract, final, world.errors)
                    save(folder / "final.json", final)
                    save(folder / "oracle.json", score)
                    save(folder / "browser-actions.json", gateway.history)
                    if not (
                        score["status"] == "VALID"
                        and score["current_local_goals_complete"]
                        and score["forbidden_history"]
                        and not score["joint_safe_completion"]
                    ):
                        raise ValueError(
                            "Independent oracle failed executed history challenge: "
                            + json.dumps(score)
                        )
                    row.update(
                        status="COUNTEREXAMPLE_REJECTED",
                        changed_operation=intervention.changed,
                        forbidden_count=len(score["forbidden_history"]),
                        current_local_goals_complete=True,
                    )
                    page.close()
            except Exception:
                row.update(status="FAILED_CHALLENGE", error=traceback.format_exc())
            finally:
                world.finish()
                save(folder / "worker-errors.json", world.errors)
                world.db.drop_experiment()
            save(folder / "result.json", row)
            results.append(row)
            print(json.dumps({k: v for k, v in row.items() if k != "error"}), flush=True)
    save(
        output / "summary.json",
        dict(
            registered=12,
            attempted=len(results),
            rejected=sum(r["status"] == "COUNTEREXAMPLE_REJECTED" for r in results),
            model_calls=0,
        ),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contracts", type=Path, required=True)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    execute(args.contracts, args.qualification, args.output)
