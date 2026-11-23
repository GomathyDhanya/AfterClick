"""Selected experimental browser driver; old frozen replay interface is preserved.

Default is the evidence-selected native format. Instantiation still requires
mock transport or an exact live approval record produced under project guards.
"""

import json
from pathlib import Path

from afterclick.agent.modal_policy import ModalConfig, ModalPolicy
from afterclick.extensions.interaction_trial import run_task
from afterclick.extensions.native_tools import NativeConfig, NativeToolPolicy

ROOT = Path(__file__).resolve().parents[2]


def make_policy(config_values, limits, *, format_name=None, **kwargs):
    if format_name is None:
        format_name = json.loads((ROOT / "research_ops/INTERACTION_FORMAT.json").read_text())[
            "preferred"
        ]
    if format_name in {"native_tools", "native_tools_v1"}:
        return NativeToolPolicy(NativeConfig(**config_values), limits, **kwargs)
    if format_name in {"json_schema", "json_schema_conditional_v2"}:
        return ModalPolicy(
            ModalConfig(**config_values), limits, argument_contract="conditional-v2", **kwargs
        )
    raise ValueError("Explicit known format; no automatic fallback")


def run_selected_task(
    browser, contract, config_values, limits, directory, deadline, **policy_kwargs
):
    policy = make_policy(config_values, limits, **policy_kwargs)
    try:
        return run_task(browser, contract, policy, directory, deadline, max_turns=6)
    finally:
        policy.close()
