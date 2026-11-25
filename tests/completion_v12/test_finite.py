import copy
import itertools
import random

import pytest

from afterclick.completion_v12.finite import existential, robust, verify_robust


def model(states):
    return {"move_order": "CONTROLLER_ENVIRONMENT_OBSERVATION", "states": states}


def node(observation, actions, goal=False, safe=True):
    return dict(observation=observation, actions=actions, goal=goal, safe=safe)


def test_identical_observations_cannot_use_hidden_authority():
    m = model(
        {
            "authorized": node("same screen", {"send": ["good"], "cancel": ["bad"]}),
            "forbidden": node("same screen", {"send": ["bad"], "cancel": ["good"]}),
            "good": node("completed", {}, goal=True),
            "bad": node("violated", {}, safe=False),
        }
    )
    assert existential(m, "authorized", 1)["witness"]
    assert existential(m, "forbidden", 1)["witness"]
    cert = robust(m, ["authorized", "forbidden"], 1)
    assert cert["status"] == "NO_ROBUST_POLICY_WITHIN_HORIZON"
    assert not verify_robust(m, cert)["robust"]
    # With a real public query, the controller can distinguish the required action.
    m["states"]["authorized"]["actions"]["verify"] = ["public_yes"]
    m["states"]["forbidden"]["actions"]["verify"] = ["public_no"]
    m["states"]["public_yes"] = node("authorized policy", {"send": ["good"]})
    m["states"]["public_no"] = node("forbidden policy", {"cancel": ["good"]})
    cert = robust(m, ["authorized", "forbidden"], 2)
    assert verify_robust(m, cert)["robust"]


def test_verification_can_consume_the_last_prevention_opportunity():
    m = model(
        {
            "pending": node("pending", {"cancel": ["safe"], "verify": ["pending", "committed"]}),
            "safe": node("canceled", {}, goal=True),
            "committed": node("pending", {"cancel": ["history"]}),
            "history": node("canceled", {}, safe=False),
        }
    )
    assert verify_robust(m, robust(m, ["pending"], 2))["robust"]
    assert existential(m, "committed", 2)["status"] == "NO_PATH_UNDER_DECLARED_MODEL"
    # Current UI repair cannot remove forbidden history.
    assert not verify_robust(m, robust(m, ["committed"], 2))["robust"]
    certificate = robust(m, ["pending"], 2)
    root = next(r for r in certificate["expansions"] if r["key"] == certificate["root"])
    assert root["selected_action"] == "cancel"


@pytest.mark.parametrize("mutation", ["omit_action", "omit_successor", "conclusion", "model"])
def test_proof_checker_rejects_incomplete_and_forged_certificates(mutation):
    m = model(
        {
            "pending": node("pending", {"cancel": ["safe"], "wait": ["safe", "bad"]}),
            "safe": node("done", {}, goal=True),
            "bad": node("bad", {}, safe=False),
        }
    )
    cert = robust(m, ["pending"], 2)
    altered = copy.deepcopy(cert)
    root = next(r for r in altered["expansions"] if r["key"] == cert["root"])
    if mutation == "omit_action":
        del root["actions"]["wait"]
    elif mutation == "omit_successor":
        root["actions"]["wait"].pop("bad")
    elif mutation == "conclusion":
        altered["status"] = "NO_ROBUST_POLICY_WITHIN_HORIZON"
    else:
        m["states"]["pending"]["actions"]["cancel"] = ["bad"]
    with pytest.raises(ValueError):
        verify_robust(m, altered)


def test_timeout_is_unknown_and_short_horizon_is_not_universal_impossibility():
    m = model(
        {
            "a": node("a", {"next": ["b"]}),
            "b": node("b", {"next": ["c"]}),
            "c": node("c", {}, goal=True),
        }
    )
    assert existential(m, "a", 1)["status"] == "NO_PATH_WITHIN_HORIZON"
    assert existential(m, "a", 2)["status"] == "WITNESSED_BOUNDED_EXISTENTIAL"
    assert robust(m, ["a"], 2, max_expansions=1)["status"] == "UNKNOWN"
    assert existential(m, "a", 2, max_expansions=1)["status"] == "UNKNOWN"


@pytest.mark.parametrize("seed", range(20))
def test_full_observation_deterministic_games_match_exhaustive_action_words(seed):
    rng = random.Random(seed)
    m = model(
        {
            str(i): node(
                str(i), {a: [str(rng.randrange(5))] for a in ["x", "y"]}, goal=i == 4, safe=i != 3
            )
            for i in range(5)
        }
    )
    possible = False
    for length in range(5):
        for word in itertools.product(["x", "y"], repeat=length):
            current, safe = "0", True
            for action in word:
                safe &= m["states"][current]["safe"]
                current = m["states"][current]["actions"][action][0]
            possible |= safe and m["states"][current]["safe"] and m["states"][current]["goal"]
    assert (existential(m, "0", 4)["witness"] is not None) == possible
    assert verify_robust(m, robust(m, ["0"], 4))["robust"] == possible
