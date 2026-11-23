"""Matched local timing explorers. All candidate queries, including repeats, are charged."""

import argparse
import csv
import hashlib
import json
import random
import statistics
import time
import traceback
from pathlib import Path

from afterclick.agent.modal_policy import atomic_json
from afterclick.research.kernel import MECHANISMS, frontiers, point
from afterclick.research.witnesses import query


def bracket(points):
    ordered = sorted(points)
    candidates = [
        (b - a, a, b) for a, b in zip(ordered, ordered[1:]) if b - a > 1 and points[a] != points[b]
    ]
    if not candidates:
        return None
    _, left, right = min(candidates)
    return (left + right) // 2


def widest(points):
    if 0 not in points:
        return 0
    if 1535 not in points:
        return 1535
    ordered = sorted(points)
    gap, left, right = max((b - a, a, b) for a, b in zip(ordered, ordered[1:]))
    return (left + right) // 2 if gap > 1 else 0


def choose(method, points, rng, cursors, mechanism):
    if method in {"random_min", "coverage_min", "local_frontier"}:
        value = bracket(points)
        if value is not None:
            return value
    if method in {"plain_random", "random_min"}:
        return rng.randrange(1536)
    if method == "coverage_min":
        return widest(points)
    index = cursors[mechanism]
    cursors[mechanism] += 1
    if method == "enumeration":
        return index
    steps = [0, 1, *[2**k for k in range(1, 11)], 1535]
    return steps[index] if index < len(steps) else widest(points)


def interval(values):
    rng = random.Random(314159)
    means = []
    for _ in range(2000):
        means.append(statistics.mean(rng.choices(values, k=len(values))))
    means.sort()
    return [means[49], means[1949]]


def run(directory):
    p = json.loads((directory / "protocol.json").read_text())
    if (directory / "raw/started.json").exists():
        raise ValueError("Fresh registered run required")
    assert p["query_budget_per_method_seed"] == 96 and p["cost_cap_usd"] == 0
    atomic_json(directory / "raw/started.json", dict(started=True))
    started = time.monotonic()
    results = []
    all_frontiers = set()
    curves = {}
    attempted = 0
    error = None
    try:
        with (directory / "trials.jsonl").open("a") as stream:
            for method_index, method in enumerate(p["methods"]):
                curves[method] = []
                for seed in p["search_seeds"]:
                    rng = random.Random(1009 * seed + method_index)
                    archive = {m: {} for m in MECHANISMS}
                    cursors = {m: 0 for m in MECHANISMS}
                    coverage = []
                    duplicates = 0
                    first = {}
                    for index in range(96):
                        mechanism = MECHANISMS[index % 4]
                        at = choose(method, archive[mechanism], rng, cursors, mechanism)
                        duplicate = at in archive[mechanism]
                        duplicates += duplicate
                        attempted += 1
                        label = point(mechanism, at)["unrecoverable"]
                        archive[mechanism][at] = label
                        boundaries = frontiers(archive)
                        all_frontiers.update(boundaries)
                        found = {b[0] for b in boundaries}
                        coverage.append(len(found))
                        for m in found:
                            first.setdefault(m, index + 1)
                        stream.write(
                            json.dumps(
                                dict(
                                    schema_version=1,
                                    method=method,
                                    seed=seed,
                                    evaluation=index + 1,
                                    mechanism=mechanism,
                                    recovery_time=at,
                                    unrecoverable=label,
                                    duplicate=duplicate,
                                    mechanisms_found=len(found),
                                    transition_witnesses_found=len(boundaries),
                                    partition="development",
                                    evidence=(
                                        "finite abstraction query; requires PostgreSQL witness"
                                    ),
                                )
                            )
                            + "\n"
                        )
                        stream.flush()
                    curves[method].append(coverage)
                    results.append(
                        dict(
                            method=method,
                            seed=seed,
                            attempted=96,
                            unique_mechanisms=coverage[-1],
                            unique_transitions=len(frontiers(archive)),
                            coverage_auc=statistics.mean(coverage),
                            duplicate_rate=duplicates / 96,
                            first_discovery=first,
                        )
                    )
        truth = []
        for mechanism in MECHANISMS:
            last = point(mechanism, 0)["unrecoverable"]
            for at in range(1, 1536):
                label = point(mechanism, at)["unrecoverable"]
                if label != last:
                    truth.append((mechanism, at - 1, at, "loss" if label else "return"))
                last = label
        assert all_frontiers <= set(truth)
        witness_cases = 0
        for mechanism, left, right, direction in sorted(all_frontiers):
            for at in [left, right]:
                raw = query(mechanism, at)
                witness_cases += 1
                cert = raw["certificate"]
                expected = point(mechanism, at)["unrecoverable"]
                actual = cert["classification"]
                valid = actual == ("VERIFIED_UNRECOVERABLE" if expected else "VERIFIED_RECOVERABLE")
                name = f"postgres-{mechanism}-{at}.json"
                atomic_json(directory / "raw" / name, raw)
                with (directory / "oracle_certificates.jsonl").open("a") as stream:
                    stream.write(
                        json.dumps(
                            dict(
                                mechanism=mechanism,
                                recovery_time=at,
                                direction=direction,
                                independent_certificate=cert,
                                model_agreement=valid,
                                raw_reference="raw/" + name,
                            )
                        )
                        + "\n"
                    )
                if not valid:
                    raise AssertionError("PostgreSQL abstraction disagreement: " + name)
        summary = {}
        for method in p["methods"]:
            values = [r for r in results if r["method"] == method]
            summary[method] = dict(
                mean_coverage_auc=statistics.mean(r["coverage_auc"] for r in values),
                mean_unique_mechanisms=statistics.mean(r["unique_mechanisms"] for r in values),
                mean_unique_transitions=statistics.mean(r["unique_transitions"] for r in values),
                mean_duplicate_rate=statistics.mean(r["duplicate_rate"] for r in values),
                mean_curve=[statistics.mean(c[i] for c in curves[method]) for i in range(96)],
            )
        baseline = {r["seed"]: r["coverage_auc"] for r in results if r["method"] == "coverage_min"}
        for method in p["methods"]:
            differences = [
                r["coverage_auc"] - baseline[r["seed"]] for r in results if r["method"] == method
            ]
            summary[method]["paired_auc_difference_vs_coverage"] = statistics.mean(differences)
            summary[method]["paired_bootstrap95_vs_coverage"] = interval(differences)
        atomic_json(directory / "raw/per-seed-results.json", dict(results=results))
        with (directory / "figures/search_results.csv").open("w") as stream:
            writer = csv.writer(stream)
            writer.writerow(
                [
                    "method",
                    "mean_coverage_auc",
                    "mean_unique_mechanisms",
                    "mean_unique_transitions",
                    "auc_difference_vs_coverage",
                    "ci_low",
                    "ci_high",
                ]
            )
            for method, metric in summary.items():
                writer.writerow(
                    [
                        method,
                        metric["mean_coverage_auc"],
                        metric["mean_unique_mechanisms"],
                        metric["mean_unique_transitions"],
                        metric["paired_auc_difference_vs_coverage"],
                        *metric["paired_bootstrap95_vs_coverage"],
                    ]
                )
        metrics = dict(
            schema_version=1,
            passed=True,
            attempted_candidate_queries=attempted,
            finite_reference_grid_queries=6144,
            postgres_witness_cases=witness_cases,
            discovered_distinct_mechanisms=len({b[0] for b in all_frontiers}),
            verified_semantic_transitions=len(all_frontiers),
            truth_transitions=len(truth),
            methods=summary,
            model_calls=0,
            cost_usd=0,
            elapsed_seconds=time.monotonic() - started,
            scope=(
                "conditional on4fixed benchmark mechanisms; "
                "CI over algorithm RNG, not workflow population"
            ),
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        )
    except BaseException:
        error = traceback.format_exc()
        (directory / "raw/error.txt").write_text(error)
        with (directory / "trials.jsonl").open("a") as stream:
            stream.write(json.dumps(dict(event="interrupted", error=error)) + "\n")
        metrics = dict(
            schema_version=1,
            passed=False,
            attempted_candidate_queries=attempted,
            error=error,
            model_calls=0,
            cost_usd=0,
        )
    atomic_json(directory / "metrics.json", metrics)
    print(json.dumps({k: v for k, v in metrics.items() if k != "methods"}))
    if error:
        raise RuntimeError("Search failed, preserved raw trace")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, required=True)
    run(p.parse_args().run)


if __name__ == "__main__":
    main()
