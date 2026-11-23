"""One predeclared, full-public-input collision probe; no inference calls."""

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from playwright.sync_api import sync_playwright

from afterclick.agent.browser_observation import observe, public_history, public_task
from afterclick.agent.gateway import Action, Gateway
from afterclick.agent.modal_policy import atomic_json, digest
from afterclick.contracts.schema import load_contract
from afterclick.evaluation.mechanism_pilot import World
from afterclick.evaluation.pilot import prepare
from afterclick.infrastructure.db import Database
from afterclick.replay.server import serve
from afterclick.research.witnesses import query


def run(directory):
    if (directory / "raw/started.json").exists():
        raise ValueError("Fresh preregistered probe required")
    atomic_json(directory / "raw/started.json", dict(started=True))
    contract = load_contract("fixtures/tasks/review-readiness-v2.json")
    notice = Database("ac_collision_" + uuid4().hex)
    fee = None
    inputs = {}
    try:
        notice.migrate()
        prepare(notice, contract)
        fee = World(7)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                for name, db in [("notification", notice), ("mock_payment_fee", fee.source)]:
                    with serve(db) as origin:
                        context = browser.new_context()
                        page = context.new_page()
                        instant = datetime(2026, 1, 1, tzinfo=timezone.utc)
                        page.clock.install(time=instant)
                        page.clock.pause_at(instant)
                        gateway = Gateway(page, origin)
                        gateway.act(Action("navigate", "/"))
                        inputs[name] = dict(
                            task=public_task(contract),
                            observation=observe(gateway),
                            history=public_history(gateway.history),
                            prospective_horizon_ms=150,
                            candidate_action=dict(kind="click", target="Mark reviewed", value=""),
                        )
                        atomic_json(directory / f"raw/input-{name}.json", inputs[name])
                        context.close()
            finally:
                browser.close()
    finally:
        if fee:
            fee.close()
        notice.drop_experiment()
    equal = digest(inputs["notification"]) == digest(inputs["mock_payment_fee"])
    outcomes = {}
    for mechanism in ["notification", "mock_payment_fee"]:
        result = query(mechanism, 150)
        outcomes[mechanism] = result["certificate"]["classification"]
        atomic_json(directory / f"raw/outcome-{mechanism}.json", result)
        with (directory / "oracle_certificates.jsonl").open("a") as stream:
            stream.write(
                json.dumps(dict(mechanism=mechanism, certificate=result["certificate"])) + "\n"
            )
        with (directory / "trials.jsonl").open("a") as stream:
            stream.write(
                json.dumps(
                    dict(
                        mechanism=mechanism,
                        input_sha256=digest(inputs[mechanism]),
                        classification=outcomes[mechanism],
                        planted=True,
                        organic=False,
                    )
                )
                + "\n"
            )
    metrics = dict(
        schema_version=1,
        executed=True,
        public_input_equal=equal,
        outcomes=outcomes,
        opposite_known_outcomes=set(outcomes.values())
        == {"VERIFIED_RECOVERABLE", "VERIFIED_UNRECOVERABLE"},
        model_calls=0,
        cost_usd=0,
    )
    atomic_json(directory / "metrics.json", metrics)
    print(json.dumps(metrics))


if __name__ == "__main__":
    run(Path("artifacts/research_runs/p7-visible-collision-v1"))
