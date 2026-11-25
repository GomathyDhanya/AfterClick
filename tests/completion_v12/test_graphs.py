import json
from pathlib import Path

import pytest

from afterclick.completion_v12.evidence import EvidenceStore
from afterclick.completion_v12.graphs import build
from afterclick.completion_v12.historical import RUNS
from afterclick.completion_v12.verify_graphs import verify

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    output = tmp_path_factory.mktemp("graphs") / "generated"
    summary = build(ROOT, ["artifacts/research_runs/" + r for r in RUNS], output)
    return output, summary


def test_complete_historical_population_and_all_siblings_are_evidence_grounded(built):
    output, summary = built
    result = verify(ROOT, output)
    assert result["passed"] and result["nodes"] > 1000
    assert len(summary["branches"]) == 42
    assert sum(b["safe"] for b in summary["branches"]) == 36
    by_source = {}
    for branch in summary["branches"]:
        by_source.setdefault((branch["run_id"], branch["source_id"]), []).append(branch)
    assert len(by_source) == 14
    assert all(len({b["cut_sha256"] for b in siblings}) == 1 for siblings in by_source.values())
    assert all(any(b["safe"] for b in siblings) for siblings in by_source.values())
    assert summary["edge_kinds"].get("FORMAL_TRANSITION", 0) == 0


@pytest.mark.parametrize("mutation", ["kind", "clock", "join", "raw", "unknown"])
def test_independent_verifier_rejects_graph_corruption(built, tmp_path, mutation):
    original, _ = built
    nodes = [json.loads(x) for x in (original / "nodes.jsonl").read_text().splitlines()]
    edges = [json.loads(x) for x in (original / "edges.jsonl").read_text().splitlines()]
    if mutation == "kind":
        edges[0]["kind"] = "FORMAL_TRANSITION"
    elif mutation == "clock":
        next(n for n in nodes if n["kind"] == "EXTERNAL_RECEIPT")["clock"]["wall"] += 5
    elif mutation == "join":
        receipt = next(n for n in nodes if n["kind"] == "EXTERNAL_RECEIPT")
        edges[0]["target"] = receipt["id"]
    elif mutation == "raw":
        nodes[0]["raw"] = {"fabricated": True}
    else:
        n = next(n for n in nodes if n["kind"] == "INDEPENDENT_OUTCOME")
        n["attributes"]["bounded_observation_robust_recoverability"] = "PROVEN"
    for name, rows in [("nodes", nodes), ("edges", edges)]:
        (tmp_path / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    with pytest.raises((ValueError, KeyError)):
        verify(ROOT, tmp_path)


def test_evidence_rejects_out_of_root_and_changed_raw_record(tmp_path):
    (tmp_path / "raw.json").write_text('{"a": 1}')
    ref = EvidenceStore(tmp_path).reference("raw.json", "a")
    (tmp_path / "raw.json").write_text('{"a": 2}')
    with pytest.raises(ValueError, match="changed"):
        EvidenceStore(tmp_path).resolve(ref)
    with pytest.raises(ValueError, match="out-of-root"):
        EvidenceStore(tmp_path).read("../outside.json")
