"""Supported saved-data entrypoints. No command launches paid inference/cloud jobs."""

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def command(args):
    print("Executing " + args[2] if len(args) > 2 else str(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "command",
        choices=["verify-data", "reproduce-existing", "analyze", "generate-paper", "test", "demo"],
    )
    p.add_argument("--output", type=Path)
    p.add_argument("--archive", type=Path)
    p.add_argument("--restore-to", type=Path)
    p.add_argument("--pdf-python", default=sys.executable)
    a = p.parse_args()
    data = ROOT / "evidence/publication"
    if a.command == "verify-data" and a.archive:
        from research_ops.publication.analysis.archive import verify

        verify(a.archive, a.restore_to)
    elif a.command == "verify-data":
        manifest = json.loads((data / "MANIFEST.json").read_text())
        for name, row in manifest["files"].items():
            assert hashlib.sha256((data / name).read_bytes()).hexdigest() == row["sha256"], name
        registry = ROOT / "paper/current/CLAIM_REGISTRY.json"
        if registry.exists():
            for row in json.loads(registry.read_text()).values():
                assert (
                    hashlib.sha256((data / row["source"]).read_bytes()).hexdigest()
                    == row["source_sha256"]
                )
        matrix = ROOT / "research_ops/publication/claim_evidence_matrix.csv"
        matrix_rows = list(csv.DictReader(matrix.open()))
        for row in matrix_rows:
            assert (
                hashlib.sha256((ROOT / row["evidence"]).read_bytes()).hexdigest() == row["sha256"]
            )
        print(
            json.dumps(
                dict(
                    claim_matrix_rows_verified=len(matrix_rows),
                    compact_files_verified=len(manifest["files"]),
                    claim_registry_verified=registry.exists(),
                    raw_archive_verification=(
                        "See separate restored-data/Linux reports; "
                        "compact verification does not verify absent raw files"
                    ),
                    provider_calls=0,
                    model_calls=0,
                )
            )
        )
    elif a.command == "reproduce-existing":
        if a.output is None:
            p.error("--output must be a fresh directory")
        command(
            [
                sys.executable,
                "research_ops/scripts/reproduce_afterclick_v12.py",
                "--root",
                str(ROOT),
                "--output",
                str(a.output.resolve()),
            ]
        )
    elif a.command == "analyze":
        if a.output is None:
            p.error("--output must be a fresh directory")
        out = a.output.resolve()
        out.mkdir(parents=True, exist_ok=False)
        for module, flags in [
            ("normalize", ["--output", str(out / "normalized")]),
            (
                "verify_normalized",
                ["--data", str(out / "normalized"), "--output", str(out / "verified")],
            ),
            (
                "analyze_existing",
                ["--data", str(out / "normalized"), "--output", str(out / "analysis")],
            ),
            (
                "obligation_audit",
                ["--data", str(out / "normalized"), "--output", str(out / "obligations")],
            ),
            (
                "verify_actuator",
                [
                    "--run",
                    str(ROOT / "artifacts/research_runs/v12-31-complex-controlled-enforcement-v1"),
                    "--output",
                    str(out / "actuator-verification"),
                ],
            ),
        ]:
            command([sys.executable, "-m", "research_ops.publication.analysis." + module, *flags])
    elif a.command == "generate-paper":
        from research_ops.publication.analysis.figures import generate
        from research_ops.publication.analysis.manuscript import build

        target = ROOT / "paper/current"
        generate(data, target / "figures")
        build(data, target)
        for name in ["MANUSCRIPT", "APPENDIX"]:
            command(
                [
                    a.pdf_python,
                    "research_ops/scripts/render_afterclick_pdf.py",
                    str(target / (name + ".md")),
                    str(ROOT / "output/pdf" / ("AFTERCLICK_CURRENT_" + name + ".pdf")),
                    "--anonymous",
                ]
            )
    elif a.command == "test":
        command(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/completion_v12/benchmark/test_scientific_estimators.py",
                "tests/completion_v12/benchmark/test_financial_closure.py",
                "tests/completion_v12/benchmark/test_oracle_alternatives.py",
                "tests/publication",
                "-q",
            ]
        )
    else:
        if a.output is None:
            p.error("--output must be a fresh directory")
        command(
            [
                sys.executable,
                "-m",
                "research_ops.publication.boundary_probe",
                "--dev",
                "--output",
                str(a.output.resolve()),
            ]
        )


if __name__ == "__main__":
    main()
