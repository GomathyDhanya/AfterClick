"""Rebuild the additive T-COPE report from sealed evidence, without network or models."""

import argparse
import hashlib
import json
from pathlib import Path

from afterclick.agent.modal_policy import atomic_json
from afterclick.tcope.analyze import lines, summarize
from research_ops.scripts.plot_tcope import plot


def selected_timelines(runs, output):
    """Plot selected valid development twins; retain rejected attempts in the ledger."""
    import matplotlib.pyplot as plt

    selected = {}
    for run in runs:
        protocol = json.loads((run / "protocol.json").read_text())
        for row in lines(run / "trials.jsonl"):
            if row.get("role") != "primary_controller":
                continue
            key = (row["source_group"], row["arm"])
            if key in selected:
                old_run, old = selected[key]
                if old["valid"] or protocol.get("amendment_of") != old_run.name:
                    raise ValueError("Unregistered timeline replacement")
            selected[key] = run, row
    groups = sorted({key[0] for key in selected})
    fig, axes = plt.subplots(len(groups), 1, figsize=(12, 3.3 * len(groups)), squeeze=False)
    for group, ax in zip(groups, axes[:, 0]):
        labels = []
        for (_, arm), (run, row) in sorted(selected.items()):
            if row["source_group"] != group or not row["valid"]:
                continue
            d = json.loads((run / "raw" / arm / "world/report.json").read_text())
            state = d["state"]
            y = len(labels)
            labels.append(arm + (" [wall-censored]" if row["censored"] else ""))
            start = d["initial_state"]["tc_runtime"][0]["clock_ms"] / 1000
            stop = d.get("agent_stop_state", state)["tc_runtime"][0]["clock_ms"] / 1000
            ax.plot([start, stop], [y, y], color="#8293a0", lw=2)
            for e in state["tc_events"]:
                if e["kind"] in {
                    "command.cancel_notice",
                    "command.cancel_resource",
                    "command.revoke_access",
                }:
                    ax.scatter(e["ms"] / 1000, y, marker="v", color="#26834b", zorder=4)
                if e["kind"] in {"dispatch.issued", "access.ticket_snapshot"}:
                    ax.scatter(e["ms"] / 1000, y, marker="|", s=140, color="#7153a4", zorder=4)
            for receipt in state["tc_receipts"]:
                ax.scatter(receipt["ms"] / 1000, y, marker="x", color="#c33e45", zorder=5)
        deadline = state["tc_runtime"][0]["state"]["deadline"] / 1000
        ax.axvline(deadline, color="#666666", ls="--")
        ax.set(
            yticks=range(len(labels)),
            yticklabels=labels,
            title=group,
            xlabel="Actual branch clock (seconds)",
        )
    fig.suptitle(
        "Development only: protection ▼, dispatch/ticket |, receipt ×; dashed scheduled D\n"
        "Selected valid twins; invalid attempt retained separately; no confirmation estimate",
        fontsize=11,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(output / "timelines.png", dpi=180)
    plt.close(fig)


def reproduce(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    base = root / "artifacts/research_runs"
    if output.is_relative_to(base):
        raise ValueError("Choose a new output outside immutable research runs")
    if output.exists():
        raise ValueError("Use a fresh output directory; preserve previous regenerations")
    freeze = json.loads((root / "research_ops/TCOPE_FINAL_FREEZE.json").read_text())
    cohort = base / "t9-locked-native-confirmation-v1"
    protocol = json.loads((cohort / "protocol.json").read_text())
    runs = [base / name for name in protocol["child_run_ids"]]
    mismatches = []
    checked = 0
    for name, expected in freeze["source_hashes"].items():
        checked += 1
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            mismatches.append(name)
    locks = json.loads((cohort / "raw/child-protocol-hashes.json").read_text())
    for run in [cohort, *runs]:
        seal = json.loads((run / "checksums.json").read_text())
        for name, expected in seal["file_sha256"].items():
            checked += 1
            if hashlib.sha256((run / name).read_bytes()).hexdigest() != expected:
                mismatches.append(str(run / name))
        if run != cohort:
            actual = hashlib.sha256((run / "protocol.json").read_bytes()).hexdigest()
            if actual != locks["protocol_sha256"][run.name]:
                mismatches.append(str(run / "protocol.json"))
    if mismatches:
        raise ValueError("Evidence/freeze mismatch: " + repr(mismatches))
    output.mkdir(parents=True)
    confirmation = summarize(runs, output / "confirmation")
    if not sum(row["valid"] for row in confirmation["arms"]):
        # The frozen analyzer counts verified completions over planned sources.
        # With no valid branches that is a count, not an efficacy estimate.
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(9, 3), layout="constrained")
        ax.axis("off")
        ax.text(0.5, 0.6, "Locked confirmation: INCONCLUSIVE", ha="center", fontsize=19)
        ax.text(
            0.5,
            0.32,
            "7 reconstruction-invalid branches; 49 unattempted; 0 valid efficacy outcomes.\n"
            "No confirmation safety rate or policy comparison can be estimated.",
            ha="center",
            fontsize=12,
        )
        fig.savefig(output / "confirmation/safety-compute.png", dpi=180)
        plt.close(fig)
        (output / "confirmation/interpretation.md").write_text(
            "INCONCLUSIVE: zero valid efficacy branches. Zeros in the frozen analyzer's "
            "verified-completion counts are not zero safety rates. Original stop rule applied; "
            "do not use invalid/unattempted rows in a safety comparison.\n"
        )
    else:
        plot(runs, output / "confirmation")
    dev_names = [
        "t6-dev01-controller-v1",
        "t6-dev01-controller-v2",
        "t6-dev03-controller-v2",
        "t6-dev05-controller-v2",
    ]
    dev = [base / name for name in dev_names]
    summarize(dev, output / "development")
    plot(dev, output / "development")
    selected_timelines(dev, output / "development")
    roles, families, status = {}, {}, {}
    for run in runs:
        for row in lines(run / "trials.jsonl"):
            role = row["role"]
            roles[role] = roles.get(role, 0) + 1
            if role == "primary_controller":
                family = row["family"]
                families[family] = families.get(family, 0) + 1
                for key in ["valid", "invalid", "unknown", "censored"]:
                    status[key] = status.get(key, 0) + int(row[key])
    audit = dict(
        schema_version=1,
        evidence_files_verified=checked,
        mismatches=mismatches,
        roles=roles,
        primary_family_attempts=families,
        primary_status=status,
        mode="saved_evidence_only_no_network_no_model_loading",
        frozen_source_commit=freeze["source_git_commit"],
        scope="New source instances and timing shifts, four familiar mechanisms",
    )
    atomic_json(output / "reproduction-audit.json", audit)
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=Path(__file__).resolve().parents[2], type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    reproduce(args.root, args.output)
