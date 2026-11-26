"""Offline saved-data reproduction with read-only path relocation.

Never invokes a provider, inference runner, browser or cloud SDK. Original
registrations, model traces and hashes remain byte-identical. Absolute paths in
archived evidence are mapped only in the reader, not rewritten on disk.
"""

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path


def main(root, output):
    root = root.resolve()
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    index = json.loads(
        (root / "research_ops/completion_v12/final_package/RELEASE_INDEX.json").read_text()
    )
    old = index["original_workspace_root"]
    real_path = Path

    def relocated(value):
        p = real_path(value)
        if not p.is_absolute():
            return root / p
        # A relocated checkout may itself live below the original workspace.
        # Its already-local __file__ and output paths must not be mapped twice.
        if p.is_relative_to(root) or p.is_relative_to(output):
            return p
        try:
            return root / p.relative_to(old)
        except ValueError:
            return p

    sys.path.insert(0, str(root))
    freeze = root / index["freeze"]
    f = json.loads(freeze.read_text())
    assert hashlib.sha256(freeze.read_bytes()).hexdigest() == index["freeze_sha256"]
    checked = 0
    for category in ["source_hashes", "gate_hashes"]:
        for name, expected in f[category].items():
            path = root / name if not real_path(name).is_absolute() else relocated(name)
            assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
            checked += 1
    from research_ops.scripts import v12_confirmatory_analysis as stats
    from research_ops.scripts import v12_graphs as graphs
    from research_ops.scripts import v12_verify_graphs as verifier
    from research_ops.scripts import verify_afterclick_v12_outcomes as outcomes

    for module in [stats, graphs, verifier, outcomes]:
        module.Path = relocated
    comparisons = {}
    for tag in ["primary", "larger"]:
        spec = index[tag]
        runs = [root / p for p in spec["runs"]]
        registration = root / spec["registration"]
        target = output / (tag + "-analysis")
        stats.analyze([registration], runs, target)
        result = json.loads((target / "report.json").read_text())
        reference = json.loads((root / spec["analysis_report"]).read_text())
        # Paths and runtime-dependent optimizer diagnostics are excluded from
        # this exact numeric/assignment comparison, never outcomes or intervals.
        keys = [
            "registered",
            "terminal",
            "missing",
            "arms",
            "contrasts",
            "bootstrap_replicates",
            "bootstrap_seed",
            "cluster_unit",
        ]

        def equal(a, b):
            if isinstance(a, dict) and isinstance(b, dict):
                return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
            if isinstance(a, list) and isinstance(b, list):
                return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
            if isinstance(a, float) and isinstance(b, (float, int)):
                return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
            return a == b

        for key in keys:
            assert equal(result[key], reference[key]), (tag, key)
        outcomes.main(
            runs,
            root / "research_ops/completion_v12/candidate_contracts_v7",
            output / (tag + "-oracle-verification"),
        )
        outcome_report = json.loads(
            (output / (tag + "-oracle-verification") / "report.json").read_text()
        )
        assert outcome_report["passed"] and outcome_report["disagreements"] == 0
        graphdir = output / (tag + "-graphs")
        graphs.build(runs, graphdir)
        verified = verifier.verify(graphdir)
        (graphdir / "independent-verification.json").write_text(
            json.dumps(verified, indent=2) + "\n"
        )
        comparisons[tag] = dict(
            numeric_and_assignment_results_match=True, graph_verification=verified
        )
    report = dict(
        passed=True,
        zero_model_calls=True,
        zero_provider_calls=True,
        relocation_reader_only=True,
        frozen_files_checked=checked,
        comparisons=comparisons,
        full_matrix_complete=index["full_matrix_complete"],
    )
    (output / "reproduction-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    main(a.root, a.output)
