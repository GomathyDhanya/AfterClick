"""Finite, explicitly closed, partially observed safety/reachability games.

Move order: controller chooses a public-history action, then environment chooses
one listed successor, then its observation is revealed. There is no access to
the actual hidden state. Certificates cover all expansions, including losing
actions; resource exhaustion returns UNKNOWN. This module makes no claims about
an unmodeled live application's reachability.
"""

from collections import deque

from afterclick.completion_v12.evidence import digest


def validate(model):
    states = model["states"]
    if not states or model["move_order"] != "CONTROLLER_ENVIRONMENT_OBSERVATION":
        raise ValueError("Explicit finite state set and move order required")
    for key, state in states.items():
        if not isinstance(state["observation"], str):
            raise ValueError("Observation equivalence label required")
        for targets in state["actions"].values():
            if (
                not targets
                or len(set(targets)) != len(targets)
                or not set(targets) <= states.keys()
            ):
                raise ValueError("Incomplete or duplicate transition")
        if state["goal"] and not state["safe"]:
            raise ValueError("Unsafe goal is not joint completion")
        if not isinstance(key, str):
            raise ValueError("Stable state identifiers required")
    return model


def existential(model, initial, horizon, max_expansions=100000):
    """Some actions and some environment choices, at most horizon transitions."""
    validate(model)
    if initial not in model["states"] or horizon < 0 or max_expansions < 1:
        raise ValueError("Invalid finite query")
    queue = deque([(initial, 0, [])])
    seen = {initial}
    expanded, witness, cutoff = [], None, False
    while queue:
        if len(expanded) >= max_expansions:
            return dict(
                status="UNKNOWN",
                reason="RESOURCE_BOUND",
                model_sha256=digest(model),
                initial=initial,
                horizon=horizon,
                expansions=expanded,
            )
        key, depth, path = queue.popleft()
        state = model["states"][key]
        if state["safe"] and state["goal"] and witness is None:
            witness = path
        outgoing = []
        if state["safe"]:
            for action, targets in sorted(state["actions"].items()):
                for target in targets:
                    outgoing.append([action, target])
                    if depth < horizon and target not in seen:
                        seen.add(target)
                        queue.append((target, depth + 1, path + [[key, action, target]]))
                    elif depth == horizon and target not in seen:
                        cutoff = True
        expanded.append(dict(state=key, depth=depth, outgoing=outgoing))
    return dict(
        status="WITNESSED_BOUNDED_EXISTENTIAL"
        if witness is not None
        else "NO_PATH_WITHIN_HORIZON"
        if cutoff
        else "NO_PATH_UNDER_DECLARED_MODEL",
        model_sha256=digest(model),
        initial=initial,
        horizon=horizon,
        expansions=expanded,
        witness=witness,
        closure_exhausted=not cutoff,
    )


def _key(belief, horizon):
    return digest([sorted(belief), horizon])


def robust(model, initial_belief, horizon, max_expansions=100000):
    """Exists an observation-based policy, for every listed environment choice."""
    validate(model)
    initial = frozenset(initial_belief)
    states = model["states"]
    if not initial or not initial <= states.keys() or horizon < 0 or max_expansions < 1:
        raise ValueError("Invalid robust query")
    if len({states[s]["observation"] for s in initial}) != 1:
        raise ValueError("Initial belief must be a single public observation class")
    memo = {}

    def solve(belief, remaining):
        key = _key(belief, remaining)
        if key in memo:
            return memo[key]["winning"]
        if len(memo) >= max_expansions:
            raise OverflowError("Finite belief budget exhausted")
        row = dict(
            key=key,
            belief=sorted(belief),
            remaining=remaining,
            actions={},
            winning=False,
            selected_action=None,
            terminal=None,
        )
        memo[key] = row
        if not all(states[s]["safe"] for s in belief):
            row["terminal"] = "UNSAFE"
        elif all(states[s]["goal"] for s in belief):
            row.update(terminal="GOAL", winning=True)
        elif remaining == 0:
            row["terminal"] = "HORIZON"
        else:
            common = set.intersection(*(set(states[s]["actions"]) for s in belief))
            for action in sorted(common):
                groups = {}
                for s in belief:
                    for target in states[s]["actions"][action]:
                        groups.setdefault(states[target]["observation"], set()).add(target)
                children = {obs: _key(b, remaining - 1) for obs, b in groups.items()}
                row["actions"][action] = children
                # Do not short-circuit: the certificate retains every successor.
                wins = [solve(frozenset(b), remaining - 1) for b in groups.values()]
                if all(wins) and row["selected_action"] is None:
                    row.update(winning=True, selected_action=action)
        return row["winning"]

    try:
        win = solve(initial, horizon)
        status = "CERTIFIED_OBSERVATION_ROBUST" if win else "NO_ROBUST_POLICY_WITHIN_HORIZON"
    except OverflowError:
        status = "UNKNOWN"
    return dict(
        status=status,
        model_sha256=digest(model),
        initial=sorted(initial),
        horizon=horizon,
        move_order=model["move_order"],
        root=_key(initial, horizon),
        expansions=sorted(memo.values(), key=lambda r: (r["remaining"], r["key"])),
    )


def verify_robust(model, certificate):
    """Check the supplied dynamic-programming proof, without trusting solver labels."""
    validate(model)
    if certificate["model_sha256"] != digest(model) or certificate["status"] == "UNKNOWN":
        raise ValueError("Missing complete certificate for this exact model")
    states, known = model["states"], {}
    for row in certificate["expansions"]:
        b, h = row["belief"], row["remaining"]
        if not b or not set(b) <= states.keys() or row["key"] != _key(b, h):
            raise ValueError("Invalid belief expansion")
        if row["key"] in known or len({states[s]["observation"] for s in b}) != 1:
            raise ValueError("Duplicate expansion or hidden-state observation leak")
        unsafe = not all(states[s]["safe"] for s in b)
        goal = all(states[s]["goal"] for s in b)
        expected_terminal = (
            "UNSAFE" if unsafe else "GOAL" if goal else "HORIZON" if h == 0 else None
        )
        if row["terminal"] != expected_terminal:
            raise ValueError("False terminal label")
        if expected_terminal is not None:
            expected = expected_terminal == "GOAL"
            if row["actions"] or row["selected_action"] is not None:
                raise ValueError("Terminal proof has actions")
        else:
            common = set.intersection(*(set(states[s]["actions"]) for s in b))
            if set(row["actions"]) != common:
                raise ValueError("Omitted controller action")
            winners = []
            for action in common:
                groups = {}
                for s in b:
                    for t in states[s]["actions"][action]:
                        groups.setdefault(states[t]["observation"], set()).add(t)
                children = {o: _key(g, h - 1) for o, g in groups.items()}
                if row["actions"][action] != children or not set(children.values()) <= known.keys():
                    raise ValueError("Omitted environment transition or child proof")
                if all(known[c] for c in children.values()):
                    winners.append(action)
            expected = bool(winners)
            if row["selected_action"] not in winners + ([None] if not winners else []):
                raise ValueError("Selected action is not a public-information winning policy")
        if row["winning"] != expected:
            raise ValueError("False reachability label")
        known[row["key"]] = expected
    root = _key(certificate["initial"], certificate["horizon"])
    if root != certificate["root"] or root not in known:
        raise ValueError("Missing root proof")
    expected_status = (
        "CERTIFIED_OBSERVATION_ROBUST" if known[root] else "NO_ROBUST_POLICY_WITHIN_HORIZON"
    )
    if certificate["status"] != expected_status:
        raise ValueError("Certificate conclusion contradicts proof")
    return dict(
        passed=True, expanded_beliefs=len(known), robust=known[root], model_sha256=digest(model)
    )
