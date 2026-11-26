"""Frozen estimators for v12 paired source-cluster comparisons.

Unknown outcomes retain their assignment and yield explicit bounds. A complete-
case estimate is labeled as such. Resampling uses contracts, never tool calls.
"""

import argparse
import collections
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import binomtest, t

CONTRASTS = [("P3", "P2"), ("P2", "P1"), ("P1", "P0"), ("P4", "P1"), ("P5", "P1"), ("P5", "P3")]


def read(path):
    return json.loads(path.read_text())


def holm(values):
    order = sorted(range(len(values)), key=lambda k: values[k])
    result = [None] * len(values)
    floor = 0
    for rank, index in enumerate(order):
        floor = max(floor, min(1.0, values[index] * (len(order) - rank)))
        result[index] = floor
    return result


def analyze(registrations, runs, output, bootstrap=10000):
    output.mkdir(parents=True, exist_ok=False)
    expected = {}
    contracts = {}
    for path in registrations:
        registration = read(path)
        for identifier, entry in registration["contracts"].items():
            c = read(Path(entry["path"]))
            contracts[identifier] = c
        for cell in registration["episodes"]:
            if cell["episode_id"] in expected:
                raise ValueError("Duplicated registered assignment")
            expected[cell["episode_id"]] = cell
    actual = {}
    for root in runs:
        for file in root.glob("cloud-batches/**/episodes/*/result.json"):
            row = read(file)
            key = row["episode_id"]
            assert key in expected, key
            assert key not in actual, key
            actual[key] = dict(
                row,
                evidence=str(file),
                evidence_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
            )
    table = []
    worlds = collections.defaultdict(dict)
    for key, cell in expected.items():
        row = actual.get(key, {"status": "NOT_RUN"})
        score = row.get("score") or {}
        outcome = score.get("joint_safe_completion") if row["status"] == "VALID" else None
        record = dict(
            cell,
            status=row["status"],
            joint_safe_completion=outcome,
            legitimate_complete=score.get("legitimate_complete"),
            forbidden_history=bool(score.get("forbidden_history")) if score else None,
            evidence=row.get("evidence"),
            evidence_sha256=row.get("evidence_sha256"),
        )
        table.append(record)
        if not cell.get("clean", False):
            worlds[(cell["task_id"], cell["world_seed"], cell["timing_regime"])][cell["policy"]] = (
                record
            )
    results = []
    rng = np.random.default_rng(8261125)
    for positive, negative in CONTRASTS:
        source = collections.defaultdict(list)
        disc = [0, 0]
        low_total = high_total = total = 0
        for (task, _, _), pair in worlds.items():
            if not {positive, negative} <= pair.keys():
                continue
            a, b = pair[positive]["joint_safe_completion"], pair[negative]["joint_safe_completion"]
            low = (int(a) if a is not None else 0) - (int(b) if b is not None else 1)
            high = (int(a) if a is not None else 1) - (int(b) if b is not None else 0)
            low_total += low
            high_total += high
            total += 1
            if a is not None and b is not None:
                d = int(a) - int(b)
                source[task].append(d)
                disc[0] += d == 1
                disc[1] += d == -1
        strata = collections.defaultdict(list)
        for task, differences in source.items():
            c = contracts[task]
            strata[(c["application"], c["family"], c["complexity"])].append(
                float(np.mean(differences))
            )
        n = sum(map(len, strata.values()))
        estimate = sum(sum(x) for x in strata.values()) / n if n else None
        samples = np.zeros(bootstrap)
        for values in strata.values():
            values = np.asarray(values)
            samples += rng.choice(values, (bootstrap, len(values)), replace=True).sum(axis=1)
        ci = np.quantile(samples / n, [0.025, 0.975]).tolist() if n else None
        p = binomtest(disc[0], sum(disc), 0.5).pvalue if sum(disc) else 1.0
        # Exact discordant-pair p is only a sensitivity: worlds share tasks.
        # Inferential cluster test uses task mean signs, conservatively discarding ties.
        signs = [np.mean(v) for v in source.values()]
        standard_error = float(np.std(signs, ddof=1) / np.sqrt(n)) if n > 1 else None
        cluster_mean_p = (
            float(2 * t.sf(abs(estimate / standard_error), df=n - 1))
            if standard_error
            else 1.0
            if estimate == 0
            else None
        )
        any_discordant_tasks = sum(any(d != 0 for d in values) for values in source.values())
        zero_discordance_bound = (
            binomtest(0, n).proportion_ci().high if n and not any_discordant_tasks else None
        )
        positive_tasks = sum(int(v > 0) for v in signs)
        negative_tasks = sum(int(v < 0) for v in signs)
        task_p = (
            binomtest(positive_tasks, positive_tasks + negative_tasks, 0.5).pvalue
            if positive_tasks + negative_tasks
            else 1.0
        )
        results.append(
            dict(
                contrast=positive + "-" + negative,
                primary=positive == "P3" and negative == "P2",
                registered_matched_worlds=total,
                complete_pair_source_clusters=n,
                complete_pair_estimate=estimate,
                source_stratified_bootstrap95=ci,
                assignment_bounds=[low_total / total, high_total / total] if total else None,
                discordant_worlds=disc,
                discordant_task_mean_signs=[positive_tasks, negative_tasks],
                task_sign_p=task_p,
                source_studentized_mean_p=cluster_mean_p,
                source_standard_error=standard_error,
                any_discordant_tasks=any_discordant_tasks,
                zero_discordance_task_probability_upper95=zero_discordance_bound,
                degenerate_bootstrap_caution=(
                    "A point interval at a zero-variance floor is not equivalence; "
                    "also report the task-level unobserved-discordance bound"
                    if ci and ci[0] == ci[1]
                    else None
                ),
                world_discordance_p_sensitivity_only=p,
                estimand_caution=(
                    "Source-weighted complete pairs; assignment bounds preserve missing outcomes"
                ),
            )
        )
    secondary = [r for r in results if not r["primary"]]
    for result, p in zip(
        secondary,
        holm(
            [
                r["source_studentized_mean_p"]
                if r["source_studentized_mean_p"] is not None
                else 1.0
                for r in secondary
            ]
        ),
    ):
        result["holm_adjusted_secondary_p"] = p
    counts = collections.defaultdict(collections.Counter)
    for row in table:
        arm = row["policy"] + ("-clean" if row.get("clean") else "-stress")
        counts[arm]["registered"] += 1
        counts[arm][row["status"]] += 1
        for metric in ["joint_safe_completion", "legitimate_complete", "forbidden_history"]:
            counts[arm][metric] += row[metric] is True
    report = dict(
        schema_version=1,
        registered=len(expected),
        terminal=len(actual),
        missing=sorted(set(expected) - set(actual)),
        arms=dict(counts),
        contrasts=results,
        bootstrap_replicates=bootstrap,
        bootstrap_seed=8261125,
        cluster_unit="Source task contract; stratified by application/family/complexity",
        structural_sensitivity=(
            "36 cells and six families are shared designs; "
            "task inference is conditional on these constructed operators"
        ),
        no_superiority_or_equivalence_from_zero_success=True,
        glmm_rule=(
            "Report separation/unidentifiability when any relevant arm has zero/all "
            "successes; do not manufacture finite maximum-likelihood coefficients"
        ),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    )
    from research_ops.scripts.v12_hierarchical import fit

    report["hierarchical_sensitivity"] = fit(table, contracts)
    (output / "episode-table.json").write_text(json.dumps(table, indent=2) + "\n")
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ["missing", "contrasts"]}))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registrations", type=Path, nargs="+", required=True)
    p.add_argument("--runs", type=Path, nargs="+", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    analyze(a.registrations, a.runs, a.output)
