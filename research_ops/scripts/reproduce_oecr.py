"""Reproduce closed OECR evidence into a new directory; no provider requests."""

import argparse
import json
from pathlib import Path

from afterclick.agent.modal_policy import atomic_json
from afterclick.oecr.analyze import analyze
from research_ops.scripts.audit_oecr_identity import audit
from research_ops.scripts.oecr_statistics import statistics
from research_ops.scripts.plot_oecr import plot
from research_ops.scripts.verify_oecr import verify


def reproduce(output):
    output.mkdir(parents=True, exist_ok=False)
    (output / "raw").mkdir()
    source = Path("artifacts/research_runs/u5-oecr-independent-confirmation-v2")
    correction = Path("artifacts/research_runs/u7-oecr-identity-audit-local-v1")
    verify(output / "seals.json")
    analyze(source, output / "original-summary.json")
    audit(source, output)
    for new, old in [
        (output / "original-summary.json", source / "summary.json"),
        (output / "corrected-summary.json", correction / "corrected-summary.json"),
    ]:
        if json.loads(new.read_text()) != json.loads(old.read_text()):
            raise ValueError(f"Saved-data analysis mismatch: {new.name}")
    statistics(output / "corrected-summary.json", output / "template-sensitivity.json")
    plot(output / "corrected-summary.json", output / "figures")
    for figure in (output / "figures").iterdir():
        if figure.read_bytes() != (correction / "figures" / figure.name).read_bytes():
            raise ValueError(f"Figure regeneration mismatch: {figure.name}")
    atomic_json(
        output / "result.json",
        dict(schema_version=1, passed=True, modal_usd=0, model_calls=0),
    )
    print("Seals, original/corrected analyses and figures reproduce; no model calls.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    reproduce(parser.parse_args().output)
