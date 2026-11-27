"""Current paper entrypoints. Saved-data commands cannot launch inference or cloud jobs."""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def command(args, *, cwd=ROOT, env=None):
    subprocess.run(args, cwd=cwd, env=env, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=[
            "verify-data",
            "reproduce-existing",
            "analyze",
            "rq1",
            "rq2",
            "rq3",
            "rq4",
            "generate-paper",
            "test",
            "demo",
        ],
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=ROOT,
        help="Restored raw evidence root; does not alter original files",
    )
    parser.add_argument(
        "--historical-root",
        type=Path,
        help="Exact source restored by archive/restore.py, with raw evidence",
    )
    parser.add_argument("--tex-engine", default="tectonic")
    args = parser.parse_args()
    if args.command == "verify-data":
        from research_ops.publication.evidence import verify

        verify()
    elif args.command == "reproduce-existing":
        if args.historical_root is None or args.output is None:
            parser.error(
                "--historical-root and fresh --output are required; "
                "integrity checks run in that exact restored source"
            )
        history = args.historical_root.resolve()
        command(
            [
                sys.executable,
                str(history / "research_ops/scripts/reproduce_afterclick_v12.py"),
                "--root",
                str(history),
                "--output",
                str(args.output.resolve()),
            ],
            cwd=history,
        )
    elif args.command in {"analyze", "rq1", "rq2", "rq3", "rq4"}:
        if args.output is None:
            parser.error("--output must be a fresh directory")
        out = args.output.resolve()
        out.mkdir(parents=True, exist_ok=False)
        raw = args.raw_root.resolve()
        env = dict(os.environ, AFTERCLICK_DATA_ROOT=str(raw))
        steps = [
            ("normalize", ["--output", str(out / "normalized")]),
            (
                "verify_normalized",
                [
                    "--root",
                    str(raw),
                    "--data",
                    str(out / "normalized"),
                    "--output",
                    str(out / "verified"),
                ],
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
                    str(raw / "artifacts/research_runs/v12-31-complex-controlled-enforcement-v1"),
                    "--output",
                    str(out / "actuator-verification"),
                ],
            ),
        ]
        # One shared normalized population keeps RQ denominators synchronized.
        for module, flags in steps:
            command(
                [sys.executable, "-m", "research_ops.publication.analysis." + module, *flags],
                env=env,
            )
    elif args.command == "generate-paper":
        from research_ops.publication.evidence import verify

        verify()
        command([sys.executable, "paper/figures.py"])
        command([sys.executable, "paper/tables.py"])
        build = ROOT / "artifacts/paper-build"
        build.mkdir(parents=True, exist_ok=True)
        command(
            [
                args.tex_engine,
                "--untrusted",
                "--keep-logs",
                "--outdir",
                str(build),
                str(ROOT / "paper/main.tex"),
            ]
        )
        shutil.copy2(build / "main.pdf", ROOT / "paper/AfterClick.pdf")
    elif args.command == "test":
        command(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                *(["--junitxml=" + str(args.output.resolve())] if args.output else []),
            ]
        )
    else:
        if args.output is None:
            parser.error("--output must be a fresh directory")
        command(
            [
                sys.executable,
                "-m",
                "research_ops.publication.boundary_probe",
                "--dev",
                "--output",
                str(args.output.resolve()),
            ]
        )


if __name__ == "__main__":
    main()
