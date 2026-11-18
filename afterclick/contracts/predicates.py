from afterclick.contracts.schema import Predicate


def evaluate(predicate: Predicate, state: dict) -> bool:
    matches = [row for row in state.get(predicate.table, []) if row["id"] == predicate.record_id]
    if len(matches) != 1 or predicate.field not in matches[0]:
        return False
    actual = matches[0][predicate.field]
    if predicate.operator == "contains":
        return isinstance(actual, str) and predicate.value in actual
    return type(actual) is type(predicate.value) and actual == predicate.value
