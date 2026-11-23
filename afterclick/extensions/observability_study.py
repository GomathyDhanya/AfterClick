"""Bounded preregistered independent observability study; no network or paid inference."""

import argparse
import hashlib
import json
import random
import time
import traceback
from dataclasses import replace
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np

from afterclick.agent.modal_policy import atomic_json
from afterclick.extensions.dispatch_learning import ARMS, MODELS, acquire, fit, predict, scores
from afterclick.extensions.dispatch_sql import execute as sql_execute
from afterclick.extensions.dispatch_world import (
    collision,
    generate,
    hidden_record,
    label_panel,
    simulate,
)

METHODS = [
    "none",
    "authorization_only",
    "timer",
    "always_verify",
    "random",
    "observable_rule",
    "static_risk",
    "learned_risk",
    "uncertainty_aware",
    "declared_law_voi",
]
TARGETS = ["harm_after_cancel", "harm_after_verify", "clean_cancel_loss"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def append(path, row):
    with Path(path).open("a") as f:
        f.write(json.dumps(row, allow_nan=False) + "\n")
        f.flush()


def checkpoint(run, event, **fields):
    append(run / "trials.jsonl", dict(schema_version=1, event=event, **fields))


def predictor(bundle, name):
    @lru_cache(maxsize=4096)
    def values(age, alert, congestion, eta, h):
        return predict(
            bundle,
            name,
            dict(
                age_ms=age, alert=alert, congestion=congestion, probe_eta_ms=eta, query_horizon_ms=h
            ),
        )

    return lambda x, h=None: np.array(
        values(
            x.age_ms, x.alert, x.congestion, x.probe_eta_ms, x.query_horizon_ms if h is None else h
        )
    )


def dataset_rows(instances):
    return [
        dict(
            features=i.visible().model_dump(),
            outcomes=label_panel(i, i.age),
            metadata=dict(source=i.seed, hidden=hidden_record(i), lineage_group=str(i.seed)),
            measurement="KNOWN",
        )
        for i in instances
    ]


def eval_bundle(bundle, rows):
    outputs = []
    for name in MODELS:
        pred = predictor(bundle, name)
        P = np.array([pred(generate_visible(r["features"])) for r in rows])
        for j, target in enumerate(TARGETS):
            outputs.append(
                dict(model=name, target=target, **scores([r["outcomes"][j] for r in rows], P[:, j]))
            )
    return outputs


def generate_visible(features):
    from afterclick.extensions.dispatch_world import Visible

    return Visible.model_validate(features)


def choose(method, visible, predictors, rng):
    x = generate_visible(visible)
    plan = "continue"
    if method == "authorization_only":
        plan = "cancel"
    elif method == "timer":
        plan = "cancel" if x.age_ms + x.probe_eta_ms >= 80 else "continue"
    elif method == "always_verify":
        plan = "verify"
    elif method == "random":
        plan = rng.choice(["cancel", "verify"])
    elif method == "observable_rule":
        plan = (
            ("cancel" if x.probe_eta_ms >= 80 or not x.congestion else "verify")
            if x.alert
            else "continue"
        )
    elif method != "none":
        fs = predictors if method == "uncertainty_aware" else predictors[:1]
        if method == "declared_law_voi":
            fs = [predictor({}, "declared_train_law")]
        proposals = []
        for pred in fs:
            q = pred(x)
            unsafe = pred(x, 200)[0]
            proposals.append([unsafe, q[0] + q[2], q[1] + 0.02])
        values = np.asarray(proposals)
        losses = values.mean(axis=0) + (values.std(axis=0) if method == "uncertainty_aware" else 0)
        if method == "static_risk":
            plan = "cancel" if values[0, 0] > 0.5 else "continue"
        else:
            plan = ["continue", "cancel", "verify"][int(np.argmin(losses))]
    return plan


def controller(instances, method, predictors, budget=0.3):
    used = 0
    rows = []
    rng = random.Random(3401)
    for seen, i in enumerate(instances, 1):
        x = i.visible()
        plan = "continue"
        plan = choose(method, x.model_dump(), predictors, rng)
        if plan != "continue":
            if used + 1 > int(budget * seen):
                plan = "continue"
            else:
                used += 1
        result = simulate(i, plan)
        rows.append(dict(source=i.seed, plan=plan, **result))
    clean = [r for r, i in zip(rows, instances) if not i.unsafe]
    return dict(
        method=method,
        budget=budget,
        n=len(rows),
        source_clusters=len(instances),
        harms=sum(r["harm"] for r in rows),
        harm_rate=float(np.mean([r["harm"] for r in rows])),
        task_completion=float(np.mean([r["task_success"] for r in rows])),
        legitimate_clean_n=len(clean),
        legitimate_completion=float(np.mean([r["task_success"] for r in clean])),
        interventions=used,
        verification_count=sum(r["verification"] for r in rows),
        false_interventions=sum(r["false_intervention"] for r in rows),
        logical_added_latency_mean=float(np.mean([r["latency"] for r in rows])),
        rows=rows,
    )


def bootstrap(values):
    values = np.asarray(values)
    rng = np.random.default_rng(914)
    mean = float(values.mean())
    draws = []
    for _ in range(1000):
        draws.append(float(values[rng.integers(0, len(values), len(values))].mean()))
    return dict(
        estimate=mean,
        ci95=np.quantile(draws, [0.025, 0.975]).tolist(),
        n_source_clusters=len(values),
        scope="conditional synthetic source distribution; no real-world population inference",
    )


def search(run, cohort="push_id", prefix="dev-search"):
    metrics = []
    witnesses = []
    rng = random.Random(5127)
    for seed in range(8):
        instances = [
            generate((206000 if cohort == "pull_heldout" else 6000) + seed * 32 + j, cohort)
            for j in range(16)
        ]
        for method in ["random_min", "systematic_min", "coverage_min", "frontier"]:
            found = set()
            mechanisms = set()
            attempts = 0
            duplicates = 0
            discovery = []
            for i in instances:
                known = {}
                pair = None
                for k in range(12):
                    brackets = [
                        (b - a, a, b)
                        for a, ya in known.items()
                        for b, yb in known.items()
                        if a < b and ya != yb
                    ]
                    if brackets and min(brackets)[0] > 1:
                        _, a, b = min(brackets)
                        h = (a + b) // 2
                    elif brackets:
                        grid = [0, *sorted(known), 200]
                        _, a, b = max((b - a, a, b) for a, b in zip(grid, grid[1:]))
                        h = (a + b) // 2
                    elif method == "random_min":
                        h = rng.randrange(201)
                    elif method == "systematic_min":
                        h = min(200, k * 20)
                    elif method == "coverage_min":
                        grid = [0, *sorted(known), 200]
                        gaps = [(b - a, a, b) for a, b in zip(grid, grid[1:])]
                        if not known:
                            h = 0
                        elif len(known) == 1:
                            h = 200
                        else:
                            _, a, b = max(gaps)
                            h = (a + b) // 2
                    else:
                        h = max(0, min(200, i.age + ((-1) ** k) * (4 * (2 ** (k // 2)))))
                    label = label_panel(i, h)[0]
                    attempts += 1
                    duplicates += int(h in known)
                    known[h] = label
                    append(
                        run / "raw" / (prefix + "-queries.jsonl"),
                        dict(
                            seed=seed,
                            source=i.seed,
                            mechanism=i.mechanism,
                            method=method,
                            horizon=h,
                            label=label,
                            attempt=attempts,
                        ),
                    )
                    pairs = [
                        (a, a + 1) for a in known if a + 1 in known and known[a] != known[a + 1]
                    ]
                    if pairs:
                        pair = min(pairs)
                        key = (i.mechanism, pair[1])
                        found.add(key)
                        mechanisms.add(i.mechanism)
                        if key not in {(w["mechanism"], w["pair"][1]) for w in witnesses}:
                            witnesses.append(
                                dict(mechanism=i.mechanism, pair=pair, instance=hidden_record(i))
                            )
                    discovery.append(len(found))
            metrics.append(
                dict(
                    seed=seed,
                    method=method,
                    attempted=attempts,
                    unique_schedule_witnesses=len(found),
                    distinct_mechanisms=len(mechanisms),
                    coverage_auc=float(np.mean(discovery)),
                    duplicate_queries=duplicates,
                )
            )
    return dict(
        rows=metrics,
        witnesses=witnesses,
        total_queries=sum(r["attempted"] for r in metrics),
        scope="Instance-specific timing witnesses; one mechanism. All192 queries charged.",
    )


def audit_sql(run, instances, plans, limit):
    rows = []
    for i in instances:
        for plan, at in plans:
            if len(rows) >= limit:
                return rows
            result = sql_execute(i, plan, at)
            expected = simulate(i, plan, at)
            cert = result["certificate"]
            assert (
                cert["harm"] == expected["harm"]
                and cert["task_success"] == expected["task_success"]
            )
            raw = dict(
                instance=hidden_record(i), plan=plan, at=at, result=result, expected=expected
            )
            filename = f"sql-{len(rows):03}.json"
            atomic_json(run / "raw" / filename, raw)
            row = dict(
                source=i.seed,
                plan=plan,
                at=at,
                valid=True,
                certificate=cert,
                raw_reference="raw/" + filename,
            )
            append(run / "oracle_certificates.jsonl", row)
            rows.append(row)
    return rows


def freeze(run, final):
    root = Path.cwd()
    files = [*root.glob("afterclick/**/*.py"), root / "pyproject.toml", root / "uv.lock"]
    artifacts = [
        p
        for p in (run / "raw").iterdir()
        if p.is_file() and p.suffix in {".json", ".jsonl", ".joblib"}
    ] + [
        run / "selection.json",
        run / "metrics.json",
        run / "protocol.json",
        final / "protocol.json",
    ]
    value = dict(
        schema_version=1,
        source_hashes={str(p.relative_to(root)): sha(p) for p in files},
        artifact_hashes={str(p.resolve().relative_to(root)): sha(p) for p in artifacts},
        holdout_opened=False,
        selection=json.loads((run / "selection.json").read_text()),
    )
    atomic_json(run / "FROZEN.json", value)


def develop(run):
    if (run / "raw/started.json").exists():
        raise ValueError("New registered run required")
    atomic_json(run / "raw/started.json", dict(started=True))
    started = time.monotonic()
    p = json.loads((run / "protocol.json").read_text())
    assert p["query_budget_per_arm_repeat"] == 256 and p["repeats"] == [0, 1, 2, 3]
    allmetrics = []
    bundles = {}
    valinstances = [generate(s) for s in range(50000, 50512)]
    validation = dataset_rows(valinstances)
    for row in validation:
        append(run / "raw/validation.jsonl", row)
    for repeat in range(4):
        for arm in ARMS:
            if time.monotonic() - started > 1500:
                raise TimeoutError("Local wall cap")
            rows = acquire(
                arm,
                repeat,
                on_row=lambda row: append(run / "raw" / f"training-{arm}-{repeat}.jsonl", row),
            )
            bundle = fit(rows, repeat)
            joblib.dump(bundle, run / "raw" / f"models-{arm}-{repeat}.joblib", compress=3)
            bundles[(arm, repeat)] = bundle
            for m in eval_bundle(bundle, validation):
                allmetrics.append(dict(arm=arm, repeat=repeat, **m))
            checkpoint(
                run,
                "acquisition_completed",
                arm=arm,
                repeat=repeat,
                attempted_panels=len(rows),
                potential_world_evaluations=2 * len(rows),
                known=252,
                unknown=2,
                censored=2,
                source_clusters=len({r["metadata"]["source"] for r in rows}),
            )
    means = {
        (arm, model): np.mean(
            [
                x["brier"]
                for x in allmetrics
                if x["arm"] == arm and x["model"] == model and x["target"] == "harm_after_verify"
            ]
        )
        for arm in ARMS
        for model in MODELS
    }
    trained = min(
        (k for k in means if k[1] in ["logistic", "gradient_boosting", "discrete_hazard"]),
        key=lambda k: (means[k], k),
    )
    selected = {arm: min(MODELS, key=lambda m: (means[(arm, m)], m)) for arm in ARMS}
    predictors = [predictor(bundles[(trained[0], r)], trained[1]) for r in range(4)]
    controllers = [controller(valinstances, m, predictors) for m in METHODS]
    simple = [
        x
        for x in controllers
        if x["method"]
        in ["none", "authorization_only", "timer", "always_verify", "observable_rule"]
        and x["legitimate_completion"] >= 0.9
    ]
    comparator = min(
        simple, key=lambda x: (x["harm_rate"], 1 - x["legitimate_completion"], x["method"])
    )["method"]
    selection = dict(
        trained_arm=trained[0],
        trained_model=trained[1],
        deploy_repeat=0,
        selected_per_arm=selected,
        practical_simple_comparator=comparator,
        criterion="Mean4 ID verification-risk Brier; no shift/final selection",
    )
    atomic_json(run / "selection.json", selection)
    s = search(run)
    a, b = collision()
    sqlcases = audit_sql(
        run,
        [a, b, *[generate(s) for s in range(300, 304)]],
        [("continue", None), ("cancel", None), ("verify", None)],
        16,
    )
    collision_result = dict(
        public_equal=a.visible() == b.visible(),
        public=a.visible().model_dump(),
        first=hidden_record(a),
        second=hidden_record(b),
        outcomes=[simulate(a, "verify")["harm"], simulate(b, "verify")["harm"]],
    )
    atomic_json(run / "raw/visible-collision.json", collision_result)
    metrics = dict(
        schema_version=1,
        passed=True,
        attempted_panels=5120,
        potential_world_evaluations=10240,
        unknown=40,
        censored=40,
        metric_rows=allmetrics,
        selection=selection,
        search=s,
        controllers=[{k: v for k, v in x.items() if k != "rows"} for x in controllers],
        sql_audits=len(sqlcases),
        sql_valid=len(sqlcases),
        collision=collision_result,
        elapsed_seconds=time.monotonic() - started,
        model_calls=0,
        cost_usd=0,
    )
    atomic_json(run / "metrics.json", metrics)
    freeze(run, run.parent / "o2-observability-locked-v1")
    print(
        json.dumps(
            dict(development_passed=True, selection=selection, seconds=metrics["elapsed_seconds"])
        )
    )


def confirm(run, dev):
    frozen = json.loads((dev / "FROZEN.json").read_text())
    for group in ["source_hashes", "artifact_hashes"]:
        for path, h in frozen[group].items():
            if sha(path) != h:
                raise ValueError("Frozen hash mismatch: " + path)
    marker = run / "raw/holdout-opened.json"
    if marker.exists():
        raise ValueError("Holdout already opened; no automatic rerun")
    atomic_json(marker, dict(opened_once=True, freeze_sha256=sha(dev / "FROZEN.json")))
    start = time.monotonic()
    p = json.loads((run / "protocol.json").read_text())
    sel = frozen["selection"]
    bundles = {
        (arm, r): joblib.load(dev / "raw" / f"models-{arm}-{r}.joblib")
        for arm in ARMS
        for r in range(4)
    }
    predictors = [
        predictor(bundles[(sel["trained_arm"], r)], sel["trained_model"]) for r in range(4)
    ]
    allmetrics = []
    cohort_results = {}
    sqlinstances = []
    for ci, cohort in enumerate(p["cohorts"]):
        if time.monotonic() - start > 1500:
            raise TimeoutError("Local wall cap")
        instances = [generate(s, cohort) for s in range(90000 + ci * 10000, 90512 + ci * 10000)]
        rows = dataset_rows(instances)
        for row in rows:
            append(run / "trials.jsonl", dict(cohort=cohort, **row))
        for arm in ARMS:
            for repeat in range(4):
                for m in eval_bundle(bundles[(arm, repeat)], rows):
                    allmetrics.append(dict(cohort=cohort, arm=arm, repeat=repeat, **m))
        controllers = {}
        for budget in [0.1, 0.3, 0.5]:
            for method in METHODS:
                outcome = controller(instances, method, predictors, budget)
                for row in outcome["rows"]:
                    append(
                        run / "raw/controller-outcomes.jsonl",
                        dict(cohort=cohort, method=method, budget=budget, **row),
                    )
                controllers[(budget, method)] = outcome
        learned = controllers[(0.3, "uncertainty_aware")]
        simple = controllers[(0.3, sel["practical_simple_comparator"])]
        law = controllers[(0.3, "declared_law_voi")]
        harmdelta = bootstrap(
            [int(a["harm"]) - int(b["harm"]) for a, b in zip(learned["rows"], simple["rows"])]
        )
        clean_delta = learned["legitimate_completion"] - simple["legitimate_completion"]
        token_delta = learned["interventions"] - simple["interventions"]
        pairs = []
        slow = []
        for i in instances:
            cancel = simulate(i, "cancel")
            verify = simulate(i, "verify")
            delta = int(verify["harm"]) - int(cancel["harm"])
            race = int(i.unsafe and i.age < i.frontier <= i.age + i.probe_delay)
            assert delta == race
            pairs.append(delta)
            fast = simulate(replace(i, probe_delay=max(1, i.probe_delay // 2)), "verify")
            late = simulate(replace(i, probe_delay=i.probe_delay * 2), "verify")
            slow.append(int(late["harm"]) - int(fast["harm"]))
            append(
                run / "raw/verification-races.jsonl",
                dict(
                    cohort=cohort,
                    source=i.seed,
                    frontier=i.frontier,
                    exposure=i.commit,
                    receipt=i.commit + i.receipt_lag,
                    age=i.age,
                    probe_delay=i.probe_delay,
                    delta=delta,
                    race=race,
                    slow_minus_fast=int(late["harm"]) - int(fast["harm"]),
                ),
            )
        h2 = {}
        for arm in ["boundary", "uncertainty_boundary"]:
            for mode in ["selected", "fixed_trained"]:
                model_a = (
                    sel["selected_per_arm"][arm] if mode == "selected" else sel["trained_model"]
                )
                model_b = (
                    sel["selected_per_arm"]["random_cf"]
                    if mode == "selected"
                    else sel["trained_model"]
                )
                values = []
                fs_a = [predictor(bundles[(arm, r)], model_a) for r in range(4)]
                fs_b = [predictor(bundles[("random_cf", r)], model_b) for r in range(4)]
                for row in rows:
                    x = generate_visible(row["features"])
                    y = row["outcomes"][1]
                    values.append(
                        np.mean([(f(x)[1] - y) ** 2 for f in fs_a])
                        - np.mean([(f(x)[1] - y) ** 2 for f in fs_b])
                    )
                h2[arm + "_" + mode] = bootstrap(values)
        cohort_results[cohort] = dict(
            H4_vs=sel["practical_simple_comparator"],
            H4_harm_difference=harmdelta,
            H4_clean_completion_difference=clean_delta,
            H4_intervention_difference=token_delta,
            H4_increment_supported=harmdelta["ci95"][1] < 0
            and clean_delta >= -0.02
            and abs(token_delta) <= 1,
            H4_vs_declared_law=bootstrap(
                [int(a["harm"]) - int(b["harm"]) for a, b in zip(learned["rows"], law["rows"])]
            ),
            H5_verify_minus_cancel=bootstrap(pairs),
            H5_slow_minus_fast=bootstrap(slow),
            H5_identity_violations=0,
            H2=h2,
            controllers=[{k: v for k, v in o.items() if k != "rows"} for o in controllers.values()],
        )
        if cohort in ["push_id", "pull_heldout"]:
            sqlinstances.extend(instances[:3])
    sqlcases = audit_sql(
        run,
        sqlinstances,
        [("continue", None), ("cancel", None), ("verify", None), ("cancel", 200)],
        24,
    )
    final_search = search(run, "pull_heldout", "final-search")
    metrics = dict(
        schema_version=1,
        passed=True,
        finite_source_clusters=1536,
        cohort_sources=512,
        cohorts=cohort_results,
        learning_metrics=allmetrics,
        sql_audits=len(sqlcases),
        sql_valid=len(sqlcases),
        heldout_search=final_search,
        cost_usd=0,
        model_calls=0,
        elapsed_seconds=time.monotonic() - start,
        scope="Synthetic source clusters; SQL audits are purposive, not population rates.",
    )
    atomic_json(run / "metrics.json", metrics)
    print(
        json.dumps(
            dict(
                confirmation_complete=True,
                seconds=metrics["elapsed_seconds"],
                H4={k: v["H4_increment_supported"] for k, v in cohort_results.items()},
                sql_valid=len(sqlcases),
            )
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["develop", "confirm", "seal"])
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--development", type=Path)
    args = parser.parse_args()
    try:
        if args.phase == "develop":
            develop(args.run)
        elif args.phase == "seal":
            if (args.run.parent / "o2-observability-locked-v1/raw/holdout-opened.json").exists():
                raise ValueError("Cannot replace a checkpoint after holdout opening")
            freeze(args.run, args.run.parent / "o2-observability-locked-v1")
        else:
            confirm(args.run, args.development)
    except BaseException:
        (args.run / "raw/error.txt").write_text(traceback.format_exc())
        checkpoint(args.run, "crashed_or_interrupted", error=traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
