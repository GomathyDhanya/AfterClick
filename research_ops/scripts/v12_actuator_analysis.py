"""Analyze all registered fixed-recommendation live actuator branches."""

import argparse
import collections
import csv
import json
from pathlib import Path

import numpy as np


def analyze(root, output):
    output.mkdir(parents=True, exist_ok=False)
    registration = json.loads((root / "registration.json").read_text())
    expected = {c["episode_id"]: c for c in registration["episodes"]}
    records = []
    for file in sorted(root.glob("episodes/*/result.json")):
        row = json.loads(file.read_text())
        assert row["episode_id"] in expected
        assert all(row[k] == v for k, v in expected[row["episode_id"]].items())
        folder = file.parent
        score = row.get("score") or {}
        final = folder / "final.json"
        if not final.exists():
            final = folder / "failed-snapshot.json"
        snapshot = json.loads(final.read_text()) if final.exists() else None
        events = snapshot["v12_events"] if snapshot else []
        controls = [
            e
            for e in events
            if e["kind"] == "control.command"
            and e["payload"]["command"] == "Suspend pending service"
        ]
        admits = [
            e
            for e in events
            if e["kind"] == "external.admitted" and e["payload"]["effect_id"] == "pending"
        ]
        receipts = [r for r in (snapshot or {}).get("v12_receipts", []) if r["id"] == "pending"]
        cert = json.loads((folder / "source-certificate.json").read_text())
        assert cert["valid"]
        # The receipt remains useful integrity evidence even when the treatment
        # execution was invalid. Primary causal pair contrasts retain UNKNOWN.
        record = dict(
            episode_id=row["episode_id"],
            task_id=row["task_id"],
            world_seed=row["world_seed"],
            admission_ms=row["admission_ms"],
            gateway=row["gateway"],
            gateway_delay_ms=row["gateway_delay_ms"],
            status=row["status"],
            harm=bool(score.get("forbidden_history")) if row["status"] == "VALID" else None,
            independently_observed_pending_receipt=bool(receipts),
            safe_complete=score.get("joint_safe_completion"),
            legitimate_complete=score.get("legitimate_complete"),
            source_sha256=cert["actual_sha256"],
            issue_ms=row.get("issue_from_anchor_ms"),
            response_upper_ms=row.get("response_upper_from_anchor_ms"),
            first_control_audit_ms=min((e["ms"] for e in controls), default=None),
            actual_admission_ms=min((e["ms"] for e in admits), default=None),
            receipt_wall=min((r["wall"] for r in receipts), default=None),
            evidence=str(file),
        )
        records.append(record)
    assert len({r["episode_id"] for r in records}) == len(records)
    paired = collections.defaultdict(dict)
    for row in records:
        paired[(row["task_id"], row["world_seed"], row["admission_ms"])][
            (row["gateway"], row["gateway_delay_ms"])
        ] = row
    contrasts = []
    rng = np.random.default_rng(6112531)
    for treatment in [("direct_http", 0), ("browser", 300), ("browser", 1500)]:
        by_source = collections.defaultdict(list)
        bounds = []
        for key, world in paired.items():
            if treatment not in world or ("browser", 0) not in world:
                continue
            a, b = world[treatment], world[("browser", 0)]
            assert a["source_sha256"] == b["source_sha256"]
            x, y = a["harm"], b["harm"]
            bounds.append(
                (
                    (int(x) if x is not None else 0) - (int(y) if y is not None else 1),
                    (int(x) if x is not None else 1) - (int(y) if y is not None else 0),
                )
            )
            if x is not None and y is not None:
                by_source[key[0]].append(int(x) - int(y))
        values = np.asarray([np.mean(v) for v in by_source.values()])
        boot = rng.choice(values, (10000, len(values))).mean(axis=1) if len(values) else []
        contrasts.append(
            dict(
                treatment=list(treatment),
                reference=["browser", 0],
                complete_source_clusters=len(values),
                matched_worlds=len(bounds),
                estimate=float(values.mean()) if len(values) else None,
                source_bootstrap95=np.quantile(boot, [0.025, 0.975]).tolist()
                if len(values)
                else None,
                unknown_bounds=np.mean(bounds, axis=0).tolist() if bounds else None,
                caution=(
                    "12 constructed source contracts across six shared mechanisms; no LLM "
                    "decision effect inferred"
                ),
            )
        )
    cells = collections.defaultdict(collections.Counter)
    for row in records:
        cell = cells[str((row["admission_ms"], row["gateway"], row["gateway_delay_ms"]))]
        cell["registered"] += 1
        cell[row["status"]] += 1
        cell["forbidden_history"] += row["harm"] is True
        cell["safe_complete"] += row["safe_complete"] is True
    with (output / "branches.csv").open("w") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    report = dict(
        registered=len(expected),
        terminal=len(records),
        valid=sum(r["status"] == "VALID" for r in records),
        invalid=sum(r["status"] != "VALID" for r in records),
        model_calls=0,
        cells=dict(cells),
        contrasts=contrasts,
        complete=len(records) == len(expected),
        scope=(
            "Real fixed-recommendation gateway and eligibility interventions on full L3 "
            "DEV workflows; no new LLM calls or invented deadlines"
        ),
    )
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in {"cells", "contrasts"}}))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    analyze(a.run, a.output)
