"""Supplementary paired comparison of both models on fixed common task support."""

import argparse
import collections
import json
from pathlib import Path
import numpy as np
from scipy.stats import t


def main(primary, larger, output):
    p = json.loads((primary / "episode-table.json").read_text())
    q = json.loads((larger / "episode-table.json").read_text())

    def key(r):
        return (r["task_id"], r["policy"], r["world_seed"], r.get("clean", False))

    p = {key(r): r for r in p}
    groups = collections.defaultdict(list)
    for r in q:
        k = key(r)
        assert k in p
        groups[r["policy"] + ("-clean" if r.get("clean") else "-stress")].append((p[k], r))
    rng = np.random.default_rng(251127)
    summaries = []
    for arm, pairs in groups.items():
        differences = collections.defaultdict(list)
        lo = hi = 0
        for a, b in pairs:
            x, y = a["joint_safe_completion"], b["joint_safe_completion"]
            lo += (int(y) if y is not None else 0) - (int(x) if x is not None else 1)
            hi += (int(y) if y is not None else 1) - (int(x) if x is not None else 0)
            if x is not None and y is not None:
                differences[a["task_id"]].append(int(y) - int(x))
        means = np.array([np.mean(v) for v in differences.values()])
        n = len(means)
        estimate = float(np.mean(means)) if n else None
        se = float(np.std(means, ddof=1) / np.sqrt(n)) if n > 1 else None
        ci = (
            [estimate - t.ppf(0.975, n - 1) * se, estimate + t.ppf(0.975, n - 1) * se]
            if se is not None
            else None
        )
        bootstrap = np.mean(rng.choice(means, (10000, n), replace=True), axis=1) if n else None
        summaries.append(
            dict(
                arm=arm,
                registered_pairs=len(pairs),
                complete_source_clusters=n,
                larger_minus_primary_source_mean=estimate,
                studentized95=ci,
                exploratory_source_bootstrap95=np.quantile(bootstrap, [0.025, 0.975]).tolist()
                if n
                else None,
                full_assignment_bounds=[lo / len(pairs), hi / len(pairs)],
                primary_safe=sum(a["joint_safe_completion"] is True for a, b in pairs),
                larger_safe=sum(b["joint_safe_completion"] is True for a, b in pairs),
            )
        )
    output.mkdir(parents=True, exist_ok=False)
    report = dict(
        supplementary=True,
        scope="Fixed 36-source common support, not a full second-model core replication",
        model_scale_only_causal_claim=False,
        hardware_precision_serving_and_model_revision_differ=True,
        contrasts=summaries,
    )
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--primary", type=Path, required=True)
    p.add_argument("--larger", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    main(a.primary, a.larger, a.output)
