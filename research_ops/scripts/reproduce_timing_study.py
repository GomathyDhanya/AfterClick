"""Re-score and regenerate the completed timing study without network or inference."""

import argparse
import json
from pathlib import Path

from afterclick.agent.modal_policy import atomic_json
from afterclick.model_sprint.records import sha
from research_ops.scripts.analyze_timing_study import analyze
from research_ops.scripts.audit_timing_components import audit
from research_ops.scripts.render_timing_study import render
from research_ops.scripts.verify_timing_study import verify

BASE = Path("artifacts/research_runs")
NAMES = [
    "x3-progressing-qwen-confirmation-b1-v2",
    "x3-progressing-qwen-confirmation-b2-v3",
    "x3-progressing-qwen-confirmation-b3-v3",
]


def reproduce(output):
    output.mkdir(parents=True, exist_ok=False)
    runs = [BASE / name for name in NAMES]
    inputs = [BASE / "x1-progressing-qwen-development-v1", *runs]
    checked = 0
    for run in inputs:
        seal = json.loads((run / "checksums.json").read_text())
        for name, expected in seal["file_sha256"].items():
            assert sha(run / name) == expected, str(run / name)
            checked += 1
    rescored = [verify(r) for r in inputs]
    current = analyze(runs, output / "derived")
    expected = json.loads(
        (BASE / "x4-prospective-timing-analysis-v1/derived/timing-analysis.json").read_text()
    )
    assert current == expected, "Saved numerical reproduction differs"
    audit(runs, output / "operational-timing-v2.json")
    render(output / "derived/timing-analysis.json", output / "figures")
    figures_equal = {
        p.name: sha(p) == sha(Path("paper/timing-generated") / p.name)
        for p in (output / "figures").glob("*.png")
    }
    assert all(figures_equal.values()), figures_equal
    report = dict(
        schema_version=1,
        new_model_calls=0,
        modal_usd=0,
        sealed_file_hashes_verified=checked,
        rescored=rescored,
        numerical_metrics_equal=True,
        figure_bytes_equal=figures_equal,
    )
    atomic_json(output / "reproduction-report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    reproduce(parser.parse_args().output)
