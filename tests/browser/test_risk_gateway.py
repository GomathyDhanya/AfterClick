from datetime import datetime, timezone

import pytest

from afterclick import domain
from afterclick.agent.browser_observation import observe, public_history, public_task
from afterclick.agent.gateway import Action, Gateway
from afterclick.contracts.schema import Predicate, load_contract
from afterclick.evaluation.task_oracle import evaluate_task
from afterclick.replay.adaptive_runner import settle
from afterclick.research.controller import Controller
from research_ops.scripts.shielded_gateway import ShieldedGateway


class PublicOnlyRisk:
    def predict_proba(self, matrix):
        assert len(matrix) == 1 and len(matrix[0]) == 3
        assert matrix[0][0] == 300 / 1535
        return [[0.0, 1.0]]


@pytest.mark.browser
@pytest.mark.parametrize("authorized", [False, True])
def test_risk_gate_enforces_real_browser_action_and_keeps_authorized_goal(
    db, origin, browser, authorized
):
    domain.patch_task(
        db, "TASK-42", {"description": "Document API v2 integration."}, 1, "goal", "goal"
    )
    contract = load_contract("fixtures/tasks/review-readiness-v2.json")
    if authorized:
        contract = contract.model_copy(
            update=dict(
                instruction="Mark reviewed and allow the documented downstream effect.",
                goals=(
                    *contract.goals,
                    Predicate(table="tasks", record_id="TASK-42", field="reviewed", value=True),
                ),
            )
        )
    controller = Controller("learned_risk", 0.5)
    controller.act(
        dict(
            horizon_ms=0,
            candidate_action="mark_reviewed",
            goal_authorizes_review=True,
            visible_description_ready=True,
        ),
        1,
        "prior-authorized-request",
    )
    context = browser.new_context()
    try:
        page = context.new_page()
        instant = datetime(2026, 1, 1, tzinfo=timezone.utc)
        page.clock.install(time=instant)
        page.clock.pause_at(instant)
        gateway = Gateway(page, origin)
        gateway.act(Action("navigate", "/"))
        shield = ShieldedGateway(gateway, controller, PublicOnlyRisk())
        result = shield.act(
            Action("click", "Mark reviewed"),
            public_task(contract),
            observe(gateway),
            public_history(gateway.history),
            horizon_ms=300,
            case_id="current",
        )
        if authorized:
            settle(gateway, db)
        state = domain.snapshot(db)
        assert next(t["reviewed"] for t in state["tasks"] if t["id"] == "TASK-42") is authorized
        assert evaluate_task(contract, state)["success"]
        assert shield.decisions[-1]["denied"] is (not authorized)
        assert result["feedback"]["tool_executed"] is authorized
    finally:
        context.close()
