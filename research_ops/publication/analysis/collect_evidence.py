"""Copy compact actual outputs with source-to-copy hashes; never touches raw inputs."""

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "evidence/publication"
SOURCES = {
    "analysis": "publication-20261126-existing-analysis-final",
    "normalized": "publication-20261126-normalized-v3",
    "normalization-verification": "publication-20261126-normalized-independent-v1",
    "obligations": "publication-20261126-obligation-audit-v1",
    "checks": "publication-20261126-final-checks-v1",
    "actuator-verification": "publication-20261126-actuator-independent-v3",
    "boundary": "publication-20261126-boundary-confirmation-v1",
    "replay": "publication-20261126-review-replay-v1",
    "temporal-verification": "publication-20261126-temporal-independent-v1",
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {}

    def copy(src, dst):
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        digest = hashlib.sha256(src.read_bytes()).hexdigest()
        assert hashlib.sha256(dst.read_bytes()).hexdigest() == digest
        manifest[str(dst.relative_to(OUT))] = dict(
            source=str(src.relative_to(ROOT)), sha256=digest, bytes=dst.stat().st_size
        )

    keep = {
        "normalized": {"report.json", "episodes.csv", "assignments.csv"},
        "obligations": {"report.json", "duties.csv", "episode-debt.csv"},
    }
    for label, names in keep.items():
        for old in (OUT / label).glob("*"):
            if old.is_file() and old.name not in names:
                old.unlink()  # Compact copies only; raw artifact sources remain.
    for label, source in SOURCES.items():
        base = ROOT / "artifacts/research_runs" / source
        for p in base.glob("*"):
            if (
                p.is_file()
                and (label not in keep or p.name in keep[label])
                and p.name
                not in {"parser-source.py", "input-manifest.json", "source.py", "probe-source.py"}
                and p.suffix in {".json", ".csv", ".jsonl"}
            ):
                copy(p, OUT / label / p.name)
        if label == "analysis":
            for p in (base / "cases").glob("*.md"):
                copy(p, OUT / label / "cases" / p.name)
    # Compact historical metrics remain at their existing evidence/v12 paths.
    copy(
        ROOT
        / "artifacts/publication-release"
        / "AfterClick_v12_Public_Evidence_Candidate.tar.gz.summary.json",
        OUT / "data-candidate.json",
    )
    copy(ROOT / "research_ops/publication/FINANCE_STATE.json", OUT / "finance.json")
    linux = ROOT / "artifacts/research_runs/publication-20261126-linux-reproduction-v2"
    if (linux / "restored/report.json").exists():
        for p in (linux / "restored").rglob("*.json"):
            if p.name in {
                "report.json",
                "reproduction-report.json",
                "data-verification.json",
                "environment.json",
                "steps.json",
            }:
                copy(p, OUT / "linux" / p.relative_to(linux / "restored"))
        copy(linux / "lifecycle.json", OUT / "linux/lifecycle.json")
    regression = ROOT / "artifacts/research_runs/publication-20261126-linux-regression-v3"
    if (regression / "restored/report.json").exists():
        initial = json.loads((linux / "restored/report.json").read_text())
        corrected = json.loads((linux / "restored/corrected-v3/report.json").read_text())
        full = json.loads((regression / "restored/report.json").read_text())
        followup = ROOT / "artifacts/research_runs/publication-20261126-linux-followup-v4"
        if not (followup / "restored/report.json").exists():
            raise RuntimeError("Terminal fixture follow-up is required")
        final = json.loads((followup / "restored/report.json").read_text())
        assert len(full["failures"]) == 22
        assert all(
            "p1c-qwen35-9b-smoke-v2/raw/inputs.json" in x["message"] for x in full["failures"]
        )
        assert final["all_registered_rechecked"]
        agreement = json.loads((linux / "portability-agreement.json").read_text())
        initial_required = [
            s
            for s in initial["steps"]
            if s["name"]
            in {
                "existing-reproduction",
                "controlled-timing",
                "boundary-dev",
                "postgres-start",
                "postgres-stop",
            }
        ]
        summary = dict(
            complete=True,
            all_steps_passed=False,
            final_required_checks_passed=all(s["returncode"] == 0 for s in initial_required)
            and corrected["all_steps_passed"]
            and final["all_passed"]
            and agreement["passed"],
            steps=[dict(s, name="initial/" + s["name"]) for s in initial["steps"]]
            + [dict(s, name="corrected-analysis/" + s["name"]) for s in corrected["steps"]]
            + [dict(s, name="full-source/" + s["name"]) for s in full["steps"]]
            + [
                dict(
                    name="fixture-followup/lifecycle",
                    returncode=final["returncode"],
                    elapsed=json.loads((followup / "lifecycle.json").read_text())[
                        "elapsed_seconds"
                    ],
                )
            ],
            original_archive_only_regression=dict(tests=414, passed=336, failed=78),
            corrected_full_regression=full["pytest"],
            missing_fixture_followup=final,
            cumulative_distinct_tests_passed=int(full["pytest"]["tests"])
            - int(full["pytest"]["failures"])
            + int(final["pytest"]["tests"]),
            single_complete_suite_pass_claim=False,
            zero_model_calls=True,
            zero_provider_calls=True,
            independent_cloud_machines=True,
            independent_human_operator=False,
            original_failures_preserved=True,
        )
        summary_path = regression / "publication-linux-summary.json"
        summary_path.write_text(json.dumps(summary, indent=2) + "\n")
        copy(summary_path, OUT / "linux/report.json")
        copy(regression / "restored/report.json", OUT / "linux/full-source/report.json")
        copy(regression / "lifecycle.json", OUT / "linux/full-source/lifecycle.json")
        copy(followup / "lifecycle.json", OUT / "linux/lifecycle.json")
        copy(followup / "restored/report.json", OUT / "linux/fixture-followup/report.json")
        copy(linux / "restored/report.json", OUT / "linux/initial/report.json")
        copy(linux / "portability-agreement.json", OUT / "linux/portability-agreement.json")
    (OUT / "MANIFEST.json").write_text(
        json.dumps(
            dict(files=manifest, raw_originals_modified=False, public_raw_upload_performed=False),
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            dict(compact_files=len(manifest), bytes=sum(r["bytes"] for r in manifest.values()))
        )
    )


if __name__ == "__main__":
    main()
