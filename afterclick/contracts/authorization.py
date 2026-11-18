from afterclick.contracts.schema import EffectScope, TaskContract


def matches(scope: EffectScope, event: dict) -> bool:
    changed = set(event.get("after") or {}) | set(event.get("before") or {})
    return (
        scope.kind == event["kind"]
        and scope.resource in {"*", event["resource"]}
        and scope.actor in {"*", event["actor"]}
        and (not scope.fields or bool(changed) and changed <= set(scope.fields))
    )


def authorized(contract: TaskContract, event: dict) -> bool:
    return any(matches(scope, event) for scope in contract.authorized_effects)
