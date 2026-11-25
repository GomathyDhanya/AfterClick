"""Declared six-tick delegated-ticket model, separate from empirical trajectories.

Environment progresses through the action's duration BEFORE its command commits.
Admission copies the old permission; parent revocation cannot recall a ticket.
Exact results apply only to this finite API/schedule set, never all live tools.
"""

import argparse
import json
from collections import deque
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from afterclick.completion_v12.evidence import digest
from afterclick.completion_v12.finite import existential, robust, verify_robust


@dataclass(frozen=True)
class State:
    tick: int = 0
    deadline: int = 2
    permission: bool = True
    checked: bool = False
    ticket: bool = False
    receipt: bool = False
    verified_resolved: bool = False
    handoff: bool = False


def advance(state, action, horizon=6):
    if state.tick >= horizon:
        raise ValueError("No action outside declared horizon")
    s = replace(state, tick=state.tick + 1)
    if not s.checked and s.tick >= s.deadline:
        s = replace(s, checked=True, ticket=state.permission)
    if s.ticket and s.tick >= s.deadline + 1:
        s = replace(s, receipt=True)
    if action == "revoke":
        s = replace(s, permission=False)
    elif action == "verify":
        s = replace(s, verified_resolved=s.checked and (not s.ticket or s.receipt))
    elif action == "restore":
        s = replace(s, permission=True)
    elif action == "post_handoff":
        s = replace(s, handoff=True)
    elif action != "wait":
        raise ValueError("Unknown declared action")
    return s


def observation(s):
    # Future deadline/ticket are not revealed. Verification supplies permitted resolution evidence.
    return json.dumps(
        dict(
            tick=s.tick,
            permission=s.permission,
            verified_resolved=s.verified_resolved,
            handoff=s.handoff,
        ),
        sort_keys=True,
    )


def build():
    initials = [State(deadline=d) for d in [2, 3]]
    pending = deque(initials)
    seen = set(initials)
    nodes = {}
    raw = {}
    while pending:
        s = pending.popleft()
        key = digest(asdict(s))
        actions = {}
        if s.tick < 6:
            for action in ["revoke", "verify", "restore", "post_handoff", "wait"]:
                target = advance(s, action)
                actions[action] = [digest(asdict(target))]
                if target not in seen:
                    seen.add(target)
                    pending.append(target)
        raw[key] = asdict(s)
        nodes[key] = dict(
            observation=observation(s),
            safe=not s.receipt,
            goal=s.checked
            and not s.ticket
            and s.permission
            and s.verified_resolved
            and s.handoff
            and not s.receipt,
            actions=actions,
        )
    return dict(move_order="CONTROLLER_ENVIRONMENT_OBSERVATION", states=nodes), raw


def execute(output):
    output.mkdir(parents=True, exist_ok=False)
    model, raw = build()
    (output / "model.json").write_text(json.dumps(model, indent=2) + "\n")
    (output / "states.json").write_text(json.dumps(raw, indent=2) + "\n")
    checks = []
    for tick in [0, 1]:
        belief = [digest(asdict(State(tick=tick, deadline=d))) for d in [2, 3]]
        certificate = robust(model, belief, 6 - tick)
        proof = verify_robust(model, certificate)
        weak = [existential(model, key, 6 - tick) for key in belief]
        (output / f"cut-{tick}-robust.json").write_text(json.dumps(certificate, indent=2) + "\n")
        (output / f"cut-{tick}-existential.json").write_text(json.dumps(weak, indent=2) + "\n")
        checks.append(
            dict(
                tick=tick,
                robust=proof["robust"],
                each_schedule_existential=[e["witness"] is not None for e in weak],
            )
        )
    if checks[0]["robust"] is not True or checks[1]["robust"] is not False:
        raise ValueError("Temporal model fails its hand-checkable early/late frontier")
    result = dict(
        schema_version=1,
        states=len(raw),
        model_sha256=digest(model),
        checks=checks,
        scope="FORMAL finite six-tick example; not an empirical rate or live trajectory proof",
        move_order="Worker advances during one tick, then command commits, then observation",
        hidden_fields=["deadline", "ticket", "receipt"],
        admitted_actions=["revoke", "verify", "restore", "post_handoff", "wait"],
        new_model_calls=0,
    )
    (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    execute(parser.parse_args().output)
