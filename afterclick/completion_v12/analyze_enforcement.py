"""Independent rescoring of every frozen enforcement-delay cell, without inference."""

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import replace
from pathlib import Path

from afterclick.completion_v12.evidence import digest, sha
from afterclick.tcope.workload_oracle import evaluate_workload
from afterclick.tcope.workload_specs import workload_suite


def analyze(run, output):
    run, output = Path(run), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    p = json.loads((run / "protocol.json").read_text())
    freeze = json.loads((run / "protocol-freeze.json").read_text())
    if digest(p) != freeze["sha256"]:
        raise ValueError("Registered protocol changed")
    for name, expected in p["sources"].items():
        if sha(name) != expected:
            raise ValueError("Registered mechanism source changed: " + name)
    actual = json.loads((run / "execution-manifest.json").read_text())
    expected_ids = {r["trial_id"] for r in p["rows"]}
    if {r["trial_id"] for r in actual} != expected_ids or len(actual) != len(expected_ids):
        raise ValueError("Incomplete or duplicated registered execution manifest")
    records, lineage = [], defaultdict(set)
    for row in actual:
        if row["status"] != "VALID":
            records.append(dict(trial_id=row["trial_id"], status=row["status"]))
            continue
        directory = run / row["trial_id"]
        final = json.loads((directory / "final.json").read_text())
        envelope = json.loads((run / f"source-{row['template']}-{row['seed']}.json").read_text())
        cp = envelope["payload"]
        if digest(cp) != envelope["sha256"] or row["cut_sha256"] != envelope["sha256"]:
            raise ValueError("Source cut hash changed")
        lineage[row["template"], row["seed"]].add(envelope["sha256"])
        cert = json.loads((directory / "certificate.json").read_text())
        if not cert["valid"] or not all(cert["checks"].values()):
            raise ValueError("Replay certificate invalid")
        spec = replace(
            workload_suite()[row["template"]],
            case_id=f"v12-enforcement-{row['template']}-{row['seed']}",
            seed=row["seed"],
            expected={"description": "Document the API v1 integration."},
            comment=None,
            schedule=dict(
                pending=True, deadline_ms=p["deadline_ms"], read_ms=p["read_ms"], ack_lag_ms=200
            ),
        )
        oracle = evaluate_workload(
            spec,
            cp["initial_state"],
            final,
            "scripted-controller",
            {"scripted-controller", "controlled_environment"},
            [],
        )
        if oracle != row["oracle"]:
            raise ValueError("Independent full oracle rescore differs: " + row["trial_id"])
        receiver = final["tc_receipts"]
        for r in receiver:
            issued = [
                e
                for e in final["tc_events"]
                if e["kind"] == "dispatch.issued" and e["payload"].get("id") == r["id"]
            ]
            acks = [
                e
                for e in final["tc_events"]
                if e["kind"] == "observer.acknowledged"
                and e["payload"].get("receipt_id") == r["id"]
            ]
            if (
                len(issued) != 1
                or len(acks) != 1
                or not issued[0]["wall"] <= r["wall"] <= acks[0]["wall"]
            ):
                raise ValueError("Receiver provenance/clock mismatch")
        command = row["effective_enforcement_event"]
        if command not in final["tc_events"]:
            raise ValueError("No saved enforcement ledger event")
        # Historical field name is retained. It logs inside the transaction, not
        # an exact SQL COMMIT timestamp. Browser click completion may precede response.
        records.append(
            dict(
                trial_id=row["trial_id"],
                template=row["template"],
                seed=row["seed"],
                path=row["path"],
                randomized_delay_ms=row["delay_ms"],
                status="VALID",
                command_ledger_ms=command["ms"],
                command_ledger_wall=command["wall"],
                gateway_start_wall=row["gateway_start_wall"],
                gateway_end_wall=row["gateway_end_wall"],
                exact_enforcement_commit_wall=None,
                safe=oracle["safe_task_success"],
                legitimate=oracle["goal_success"],
                forbidden_receipts=len(oracle["unauthorized_mock_receipt_ids"]),
                final_sha256=sha(directory / "final.json"),
                cut_sha256=envelope["sha256"],
            )
        )
    if any(len(hashes) != 1 for hashes in lineage.values()):
        raise ValueError("Unequal sibling cuts")
    (output / "rescored.json").write_text(json.dumps(records, indent=2) + "\n")
    cells = defaultdict(list)
    for r in records:
        if r["status"] == "VALID":
            cells[r["template"], r["path"], r["randomized_delay_ms"]].append(r)
    rows = [
        dict(
            template=t,
            path=path,
            randomized_delay_ms=d,
            seed_worlds=len(items),
            forbidden=sum(r["forbidden_receipts"] > 0 for r in items),
            joint_safe=sum(r["safe"] for r in items),
        )
        for (t, path, d), items in sorted(cells.items())
    ]
    with (output / "cells.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.3), layout="constrained", sharey=True)
    for ax, t, label in zip(axes, [0, 2, 4], ["Publication", "Delegated read", "Resource"]):
        for path, color in [("http", "#276785"), ("browser", "#ba6240")]:
            selected = [r for r in rows if r["template"] == t and r["path"] == path]
            ax.plot(
                [r["randomized_delay_ms"] for r in selected],
                [r["forbidden"] / r["seed_worlds"] for r in selected],
                marker="o",
                label=path,
                color=color,
            )
        ax.set_title(label)
        ax.set_xlabel("Randomized actuator delay (ms)")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("Observed forbidden receipt fraction")
    axes[0].set_ylim(-0.05, 1.05)
    axes[-1].legend()
    fig.suptitle(
        "Controlled recommendations; 3 legacy fixtures, 2 worlds each; no LLM calls", fontsize=10
    )
    fig.savefig(output / "enforcement-delay.svg")
    fig.savefig(output / "enforcement-delay.png", dpi=160)
    plt.close(fig)
    result = dict(
        expected=p["count"],
        reconciled=len(actual),
        rescored=len(records),
        valid=sum(r["status"] == "VALID" for r in records),
        source_worlds=len(lineage),
        independent_workflow_fixtures=3,
        new_model_calls=0,
        new_paid_compute_usd=0,
        forbidden_branch_histories=sum(r.get("forbidden_receipts", 0) > 0 for r in records),
        limitations=[
            "Not complex v12 TEST or model efficacy",
            "Only three legacy fixture structures",
            "No exact SQL COMMIT timestamp; command-event times are not silently upgraded",
            "Concurrent local qualification load may affect measured latency",
        ],
        cells=rows,
    )
    (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "cells"}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    analyze(args.run, args.output)
