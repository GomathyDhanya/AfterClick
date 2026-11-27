"""Protect scientific denominators and fail-closed evidence loading after consolidation."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from research_ops.publication.evidence import verify

ROOT = Path(__file__).resolve().parents[2]


def test_assignment_dispositions_preserve_every_registered_unknown():
    rows = list(csv.DictReader((ROOT / "evidence/publication/normalized/assignments.csv").open()))
    assert len(rows) == 2904
    status = Counter(row["status"] for row in rows)
    assert status["NOT_RUN"] == 1425
    # No unknown assignment may acquire an observed result in cleanup.
    for row in rows:
        if row["status"] == "NOT_RUN":
            assert not row.get("raw_path")


def test_duty_counts_are_independently_recounted_from_witness_rows():
    rows = list(csv.DictReader((ROOT / "evidence/publication/obligations/duties.csv").open()))
    report = json.loads((ROOT / "evidence/publication/obligations/report.json").read_text())
    assert len(rows) == report["duties"] == 617
    assert dict(Counter(row["kind"] for row in rows)) == report["types"]
    assert dict(Counter(row["status"] for row in rows)) == report["statuses"]
    assert all(row["raw_sha256"] and row["trigger_pointer"] for row in rows)


def test_boundary_breakdown_is_complete_and_matches_registered_assignments():
    path = ROOT / "evidence/publication/boundary"
    actual = json.loads((path / "cells.json").read_text())["episodes"]
    registered = json.loads((path / "registration.json").read_text())["episodes"]
    assert {r["id"] for r in actual} == {r["id"] for r in registered}
    assert len(actual) == len({r["id"] for r in actual}) == 72
    assert all(r["status"] == "VALID" for r in actual)
    assert sum(r["pending_received"] for r in actual) == 48
    assert all(r["physical_effect"] == r["pending_received"] for r in actual)


def minimal_evidence(root, pointer="/observed"):
    (root / "evidence/publication").mkdir(parents=True)
    (root / "paper").mkdir()
    source = root / "evidence/publication/report.json"
    source.write_text('{"observed": 7, "unknown": null}')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    (root / "evidence/index.json").write_text(
        json.dumps({"files": {"publication/report.json": {"sha256": digest}}})
    )
    (root / "paper/claim_registry.json").write_text(
        json.dumps(
            {"claim": {"source": "report.json", "source_sha256": digest, "pointer": pointer}}
        )
    )
    (root / "evidence/claim_evidence_matrix.csv").write_text(
        "id,evidence,sha256\nclaim,evidence/publication/report.json," + digest + "\n"
    )
    return source


def test_changed_input_is_rejected_before_presenting_a_claim(tmp_path):
    source = minimal_evidence(tmp_path)
    source.write_text('{"observed": 8}')
    with pytest.raises(AssertionError):
        verify(tmp_path)


def test_matching_file_hash_does_not_certify_a_nonexistent_claim_pointer(tmp_path):
    minimal_evidence(tmp_path, "/unobserved")
    with pytest.raises(KeyError):
        verify(tmp_path)
