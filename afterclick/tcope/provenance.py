"""Model identity is metadata, never a hardcoded actor name."""

from afterclick.agent.modal_policy import digest


def provenance(policy, tool_call_id=None, kind=None, intervention="none"):
    kind = kind or ("organic_llm" if policy.mode == "live" else "mock_policy")
    identity = dict(
        model=policy.config.underlying_model,
        revision=policy.config.model_revision,
        interaction_mode=policy.config.interaction_mode,
    )
    return dict(
        kind=kind,
        actor=kind + ":" + digest(identity)[:16],
        **identity,
        tool_call_id=tool_call_id,
        parent_request_id=policy.records[-1]["request_id"] if policy.records else None,
        intervention=intervention,
    )
