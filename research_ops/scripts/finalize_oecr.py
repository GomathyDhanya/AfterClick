"""Seal a closed OECR run from saved evidence; never performs live requests."""

import argparse
import json
from pathlib import Path

from afterclick.agent.modal_policy import atomic_json
from afterclick.model_sprint.records import seal, sha
from afterclick.oecr.analyze import analyze
from afterclick.tcope.driver import append


def finalize(run):
    if (run / "checksums.json").exists():
        raise ValueError("Already sealed")
    lifecycle = json.loads((run / "lifecycle-metrics.json").read_text())
    reconciliation = run / "raw/post-cleanup-reconciliation.json"
    if not lifecycle["idle_verified"] and not (
        reconciliation.exists() and json.loads(reconciliation.read_text())["idle_verified"]
    ):
        raise ValueError("Resolve endpoint cleanup before sealing")
    summary = analyze(run, run / "summary.json")
    ledger = json.loads(Path("research_ops/SPEND_STATE.json").read_text())
    cost = next(r for r in ledger["runs"] if r["run_id"] == run.name)
    counts = dict(
        attempted=summary["attempted"],
        valid=sum(r.get("causal_valid", False) for r in summary["rows"]),
        invalid=sum("oracle" in r and not r.get("causal_valid", False) for r in summary["rows"]),
        censored=sum("oracle" not in r for r in summary["rows"]),
        unknown=0,
        unattempted=summary["unattempted"],
    )
    atomic_json(
        run / "metrics.json",
        dict(
            schema_version=1,
            **counts,
            usage=lifecycle["usage"],
            cost=cost,
            complete_source_groups=summary["complete_source_groups"],
            summary=summary["summary"],
        ),
    )
    for row in summary["rows"]:
        if "oracle" in row:
            append(
                run / "oracle_certificates.jsonl",
                dict(
                    kind="independent_post_run_sql_oracle",
                    source=row["source"],
                    arm=row["arm"],
                    oracle=row["oracle"],
                ),
            )
    lines = [
        "# Saved-data analysis",
        "",
        f"Complete source groups: {summary['complete_source_groups']}/"
        f"{summary['planned_sources']}. "
        f"Counts: {counts}.",
        "",
        f"Genuine generations: {lifecycle['usage']['calls']}; "
        f"tokens: {lifecycle['usage']['known_total_tokens']}. "
        f"Conservative cost ${cost['guard_charge_usd']:.6f}; invoice unknown. Idle verified.",
        "",
    ]
    for arm, data in summary["summary"].items():
        lines.append(f"- {arm}: `{json.dumps(data, sort_keys=True)}`")
    lines += [
        "",
        (
            "Fresh-browser siblings are intentionally reconstruction-invalid; "
            "their outcomes are diagnostic, not efficacy evidence. Source and "
            "faithful comparisons require exact certificates. Priority target "
            "refers to the original visible label; raw text is preserved to di"
            "stinguish local compliance in a changed world. Description comple"
            "tion independently requires collaborator preservation."
        ),
        "",
        (
            "At most two task templates and one app. Source-level Wilson inter"
            "vals are descriptive; do not treat three siblings as independent "
            "or claim new-mechanism generalization. Temperature zero does not "
            "establish deterministic policy identity. The controlled clock exc"
            "ludes deadline-safety efficacy."
        ),
        "",
        (
            "Next decision must use paired outcomes and first-action differenc"
            "es, not favor a method merely because its certificate passes."
        ),
    ]
    correction = run / "analysis-correction-notice.md"
    if correction.exists():
        lines.extend(["", correction.read_text()])
    (run / "analysis.md").write_text("\n".join(lines) + "\n")
    files = {str(p): sha(p) for p in Path("afterclick/oecr").glob("*.py")}
    atomic_json(run / "raw/final-analysis-source-hashes.json", files)
    (run / "next_experiment.md").write_text(
        "Stop paid exploration after the independent cohort. Verify seals and historical hashes, "
        "regenerate analysis/figures, run full regression suite, and finish the bounded report.\n"
    )
    seal(run, "completed" if lifecycle["passed"] else "failed")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--run", type=Path, required=True)
    a = p.parse_args()
    finalize(a.run)
