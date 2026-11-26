"""Recompute v12 source-cluster summaries and pre-TEST power from saved evidence."""

import argparse
import collections
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import binomtest


def read(path):
    return json.loads(Path(path).read_text())


def rows(root):
    return [(p, read(p)) for p in sorted(root.glob("cloud-batches/**/episodes/*/result.json"))]


def summary(root):
    data = rows(root)
    registration = read(root / "registration.json")
    expected = {e["episode_id"] for e in registration["episodes"]}
    actual = [r["episode_id"] for _, r in data]
    assert len(actual) == len(set(actual)), "Duplicated episode terminal records"
    assert set(actual) <= expected
    arms = collections.defaultdict(collections.Counter)
    for _, r in data:
        a = arms[r["policy"]]
        a["executed"] += 1
        a[r["status"]] += 1
        score = r.get("score") or {}
        a["joint_safe"] += score.get("joint_safe_completion") is True
        a["legitimate_complete"] += score.get("legitimate_complete") is True
        a["forbidden_history"] += bool(score.get("forbidden_history"))
        a["calls"] += len(r.get("model_requests", []))
    return dict(
        registered=len(expected),
        terminal=len(actual),
        missing=sorted(expected - set(actual)),
        arms=dict(arms),
        sources=len({r["task_id"] for _, r in data}),
    )


def power(root, output):
    """Cluster simulation with explicit optimistic and least-favorable correlation.

    A task contributes a paired policy difference averaged over its worlds. Worlds
    and models are never treated as independent task clusters. We simulate a
    correlated categorical paired difference using a task-specific beta mixing
    probability. Simulations include uncertainty beyond observed DEV discordance.
    """
    output.mkdir(parents=True, exist_ok=False)
    data = rows(root)
    assert all(r["task_id"].startswith("DEV-") for _, r in data)
    report = summary(root)
    assert not report["missing"], "Cannot freeze power from incomplete DEV job"
    pairs = collections.defaultdict(dict)
    for _, r in data:
        if r["policy"] in {"P2", "P3"}:
            pairs[(r["task_id"], r["world_seed"], r["timing_regime"])][r["policy"]] = r
    differences = collections.defaultdict(list)
    discordant = n = 0
    for (task, _, _), pair in pairs.items():
        if set(pair) != {"P2", "P3"}:
            continue
        if any(pair[a]["status"] != "VALID" for a in pair):
            continue
        d = int(pair["P3"]["score"]["joint_safe_completion"]) - int(
            pair["P2"]["score"]["joint_safe_completion"]
        )
        differences[task].append(d)
        discordant += d != 0
        n += 1
    rng = np.random.default_rng(611252026)
    simulations = []
    # Discordance cannot be estimated as exactly zero from a floor-effect pilot.
    # Include .5 and 1 sensitivity, rather than advertising spurious 100% power.
    observed_q = discordant / n if n else None
    for worlds in [2, 3, 9]:
        for q in sorted({max(0.2, observed_q or 0), 0.5, 1.0}):
            for rho in [0.0, 0.5, 1.0]:
                for effect in [0.05, 0.10, 0.15]:
                    trials, tasks = 10000, 216
                    if rho == 1:
                        signs = rng.choice(
                            [-1.0, 0.0, 1.0],
                            (trials, tasks),
                            p=[(q - effect) / 2, 1 - q, (q + effect) / 2],
                        )
                        values = signs
                    else:
                        probability = (q + effect) / (2 * q)
                        if rho:
                            concentration = (1 - rho) / rho
                            p = rng.beta(
                                probability * concentration,
                                (1 - probability) * concentration,
                                (trials, tasks, 1),
                            )
                        else:
                            p = probability
                        active = rng.random((trials, tasks, worlds)) < q
                        positive = rng.random((trials, tasks, worlds)) < p
                        values = np.mean(active * (2 * positive - 1), axis=2)
                    means = values.mean(axis=1)
                    se = values.std(axis=1, ddof=1) / np.sqrt(tasks)
                    reject = np.abs(means) > 1.971 * se
                    simulations.append(
                        dict(
                            tasks=tasks,
                            worlds_per_task=worlds,
                            paired_discordance=q,
                            task_mixing_rho=rho,
                            effect=effect,
                            power=float(reject.mean()),
                            monte_carlo_se=float(
                                np.sqrt(reject.mean() * (1 - reject.mean()) / trials)
                            ),
                        )
                    )
    source_discordant = sum(any(v) for v in differences.values())
    interval = (
        binomtest(source_discordant, len(differences)).proportion_ci() if differences else None
    )
    result = dict(
        schema_version=1,
        mode="DEV_ONLY_PRE_TEST",
        dev_summary=report,
        paired_valid_worlds=n,
        source_clusters=len(differences),
        discordant=discordant,
        observed_discordance=observed_q,
        source_any_discordance=source_discordant,
        source_any_discordance_exact95=[interval.low, interval.high] if interval else None,
        intratask_correlation_estimate=(
            None if not discordant else "Use empirical task means; mixing scenarios reported"
        ),
        intratask_correlation_caution="Undefined at a zero-variance floor; never assume zero ICC",
        empirical_task_mean_difference=float(np.mean([np.mean(v) for v in differences.values()]))
        if differences
        else None,
        simulations=simulations,
        primary_significance=0.05,
        two_sided=True,
        simulations_per_cell=10000,
        simulated_cluster_test="Studentized task means, df=215, critical=1.971",
        caution=(
            "Repeated worlds cannot rescue a task-correlated floor effect; "
            "5/10 point effects may remain underpowered. No equivalence or "
            "zero-effect claim follows from nonsignificance."
        ),
        no_test_outcomes_used=True,
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    )
    (output / "power.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in {"simulations", "dev_summary"}}))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=["summary", "power"])
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    if a.mode == "summary":
        print(json.dumps(summary(a.run), indent=2))
    else:
        power(a.run, a.output)
