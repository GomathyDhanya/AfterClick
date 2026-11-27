"""Post-freeze interval diagnostics; frozen estimates and tests remain untouched.

One selected source per design cell cannot support within-cell bootstrap
resampling. Report that limitation and derive the predeclared t-test interval
from its already frozen standard error; add a six-family sensitivity interval.
"""

import argparse
import collections
import json
from pathlib import Path

import numpy as np
from scipy.stats import t


def main(analysis, contracts, output):
    report = json.loads((analysis / "report.json").read_text())
    rows = json.loads((analysis / "episode-table.json").read_text())
    worlds = collections.defaultdict(dict)
    for r in rows:
        if not r.get("clean"):
            worlds[(r["task_id"], r["world_seed"])][r["policy"]] = r["joint_safe_completion"]
    rng = np.random.default_rng(8261126)
    out = []
    for c in report["contrasts"]:
        a, b = c["contrast"].split("-")
        tasks = collections.defaultdict(list)
        for (task, _), v in worlds.items():
            if a in v and b in v and v[a] is not None and v[b] is not None:
                tasks[task].append(int(v[a]) - int(v[b]))
        means = {k: float(np.mean(v)) for k, v in tasks.items()}
        cells = collections.Counter()
        families = collections.defaultdict(list)
        for task, value in means.items():
            d = json.loads((contracts / (task + ".json")).read_text())
            cells[(d["application"], d["family"], d["complexity"])] += 1
            families[d["family"]].append(value)
        singletons = sum(n == 1 for n in cells.values())
        se = c["source_standard_error"]
        n = c["complete_pair_source_clusters"]
        estimate = c["complete_pair_estimate"]
        interval = (
            [estimate - t.ppf(0.975, n - 1) * se, estimate + t.ppf(0.975, n - 1) * se]
            if n > 1 and se is not None
            else None
        )
        keys = list(families)
        samples = []
        for _ in range(10000):
            sampled = rng.choice(keys, len(keys), replace=True) if keys else []
            values = [v for k in sampled for v in families[k]]
            if values:
                samples.append(np.mean(values))
        out.append(
            dict(
                contrast=c["contrast"],
                source_clusters=n,
                design_cells=len(cells),
                singleton_cells=singletons,
                frozen_stratified_bootstrap_validity="UNINFORMATIVE_SINGLETON_CELLS"
                if singletons == len(cells) and cells
                else "PARTIAL_SINGLETON_CELLS"
                if singletons
                else "WITHIN_CELL_RESAMPLING_SUPPORTED",
                derived_frozen_studentized95=interval,
                six_family_bootstrap95=np.quantile(samples, [0.025, 0.975]).tolist()
                if samples
                else None,
                family_clusters=len(keys),
                exploratory_family_sensitivity=True,
            )
        )
    output.mkdir(parents=True, exist_ok=False)
    (output / "report.json").write_text(
        json.dumps(
            dict(
                contrasts=out,
                frozen_results_unchanged=True,
                post_freeze_diagnostic=True,
                no_retuning_of_enrollment_prompts_oracle_or_policies=True,
            ),
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(out))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--analysis", type=Path, required=True)
    p.add_argument(
        "--contracts", type=Path, default=Path("research_ops/completion_v12/candidate_contracts_v7")
    )
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    main(a.analysis, a.contracts, a.output)
