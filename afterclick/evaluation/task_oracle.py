from afterclick.contracts.predicates import evaluate
from afterclick.contracts.schema import TaskContract


def evaluate_task(contract: TaskContract, state: dict) -> dict:
    results = [
        {"predicate": p.model_dump(), "satisfied": evaluate(p, state)} for p in contract.goals
    ]
    return {
        "contract_id": contract.contract_id,
        "success": all(r["satisfied"] for r in results),
        "predicates": results,
    }
