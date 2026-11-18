from copy import deepcopy

from afterclick.replay.demo import canonical, validity_certificate


def certificate_inputs():
    # Deliberately synthetic certificate unit inputs, never emitted as experiment results.
    return {
        name: {
            "valid": True,
            "checkpoint": {"database_hash": "same"},
            "outcome_hash": "execute" if name.startswith("execute") else "suppress",
        }
        for name in ("execute", "execute_placebo", "suppress", "suppress_placebo", "early", "late")
    }


def test_invalid_checkpoint_cannot_support_causal_claim():
    inputs = certificate_inputs()
    assert validity_certificate(inputs)["valid"]
    inputs["early"]["checkpoint"]["database_hash"] = "different"
    assert not validity_certificate(inputs)["valid"]


def test_placebo_divergence_and_failed_trials_are_retained_as_invalid():
    inputs = certificate_inputs()
    inputs["execute_placebo"]["outcome_hash"] = "diverged"
    assert not validity_certificate(inputs)["valid"]
    inputs["suppress"]["valid"] = False
    certificate = validity_certificate(inputs)
    assert not certificate["valid"]
    assert certificate["missing_or_failed_branches"] == ["suppress"]


def test_canonical_state_retains_pending_jobs_and_excludes_only_transport_receipts():
    original = {"tasks": [{"id": "t", "version": 1}], "scheduled_jobs": [], "sse_receipts": []}
    changed = deepcopy(original)
    changed["sse_receipts"] = [{"session_id": "random-session"}]
    assert canonical(original) == canonical(changed)
    changed["scheduled_jobs"] = [{"status": "pending"}]
    assert canonical(original) != canonical(changed)
