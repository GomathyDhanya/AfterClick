"""Scientific extraction guards; never invoke a provider."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("temporal_audit", HERE / "analyze.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def native(actions, extra=None):
    args = dict(actions=actions)
    args.update(extra or {})
    return dict(
        tool_calls=[dict(id="one", function=dict(name="browser_act", arguments=json.dumps(args)))]
    )


@pytest.mark.parametrize(
    "actions,extra",
    [
        ([dict(id="suspend", value="")], None),
        ([dict(id="w00", value="bad"), dict(id="suspend", value="")], None),
        ([dict(id="suspend", value="")], {"extra": True}),
        ([], None),
        ([dict(id="suspend", value=5)], None),
        ([dict(id="suspend")], None),
        ([dict(id="suspend", value="", unexpected="x")], None),
        ([dict(id="suspend", value="")] * 9, None),
    ],
)
def test_parser_agrees_with_frozen_source(actions, extra):
    # Load by path: no current implementation can satisfy this differential check.
    history = HERE / "provenance/historical"
    sys.path.insert(0, str(history))
    from afterclick.completion_v12.benchmark.runner import tool_actions

    message = native(actions, extra)
    parsed = audit.parse_native(message)
    try:
        expected = tool_actions(message)
    except (ValueError, KeyError, TypeError):
        expected = None
    assert parsed == expected


def test_whole_response_parse_rejects_even_prior_valid_protection():
    message = native([dict(id="suspend", value="")])
    message["tool_calls"].append(dict(id="two", function=dict(name="invalid", arguments="{}")))
    assert audit.parse_native(message) is None


def test_rejected_string_encoded_protection_is_not_silently_lost():
    broken = r"[{\"id\": \"suspend\", \"value\": \"\"}"
    message = native(broken)
    assert audit.parse_native(message) is None
    assert audit.encoded_protection_hints(broken) == ["suspend"]
    assert audit.encoded_protection_hints('[{"id":"w06","value":"suspended"}]') == []


def test_actionable_response_respects_public_arguments_batch_abort_and_finish():
    view = dict(records=[dict(id="w00", choices=["authorized"])])
    bad = dict(id="w00", value="bad")
    protect = dict(id="suspend", value="")
    assert not audit.dispatchable_response(audit.parse_native(native([bad, protect])), view)
    parsed = [("browser_act", dict(actions=[bad])), ("browser_act", dict(actions=[protect]))]
    assert audit.dispatchable_response(parsed, view)
    assert not audit.dispatchable_response([("finish_task", {}), parsed[-1]], view)
    assert audit.dispatchable_response(
        audit.parse_native(native([dict(id="w00", value="authorized")])), view
    )


def test_interval_classification_does_not_invent_exact_commit():
    assert audit.relation(5, 4, 6) == "OVERLAP"
    assert audit.relation(5, None, 4) == "AFTER"
    assert audit.relation(5, None, 6) == "UNKNOWN"
    assert audit.relation(None, 4, 6) == "UNKNOWN"


def test_forbidden_pending_is_contract_defined_not_task_suffix():
    h = HERE / "provenance/historical"
    path = next(
        (h / "artifacts/research_runs/v12-43-frozen-larger-test-v1").glob(
            "cloud-batches/**/episodes/*/final.json"
        )
    )
    result = audit.read(path.parent / "result.json")
    c = audit.read(
        h / "research_ops/completion_v12/candidate_contracts_v7" / (result["task_id"] + ".json")
    )
    f = audit.read(path)
    receipt = dict(
        id="pending",
        wall=1,
        mono=1,
        payload=dict(kind="delegated.read", choice="external-contractor"),
    )
    f["v12_receipts"] = [receipt]
    f["v12_physical_effects"] = [
        dict(
            id="pending",
            kind="delegated.read",
            content=dict(observed_document="external-contractor"),
        )
    ]
    c["task_id"] = "ARBITRARY_NO_AUTHORITY_ENCODING"
    c["private"]["initial_private_state"]["pending_allowed"] = False
    assert audit.independent_score(c, f)["pending_forbidden"] is True
    c["private"]["initial_private_state"]["pending_allowed"] = True
    assert audit.independent_score(c, f)["pending_forbidden"] is False


def test_terminal_population_has_no_silent_duplicate_episodes():
    import csv

    p = HERE / "executions.csv"
    if not p.exists():
        pytest.skip("run saved-data analysis first")
    rows = list(csv.DictReader(p.open()))
    assert len(rows) == len({r["episode_key"] for r in rows})
    assert all(r["technical_validity"] in {"VALID", "INVALID", "UNKNOWN"} for r in rows)
    report = audit.read(HERE / "report.json")
    assert not report["scoring_disagreements"]
