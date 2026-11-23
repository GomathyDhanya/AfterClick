"""Preregistered local risk-study development and once-only locked confirmation."""

import argparse
import hashlib
import json
import random
import time
import traceback
from collections import defaultdict
from pathlib import Path

import joblib
import numpy as np

from afterclick.agent.modal_policy import atomic_json
from afterclick.research.controller import Controller
from afterclick.research.dataset import TRAIN_MECHANISMS, acquire, cohort
from afterclick.research.models import Fixed, fit, metrics, predict
from afterclick.research.witnesses import query

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump_rows(path, rows):
    with path.open("w") as stream:
        for row in rows:
            stream.write(json.dumps(row) + "\n")


def code_paths():
    return sorted(
        [
            *ROOT.glob("afterclick/**/*.py"),
            *ROOT.glob("fixtures/tasks/*.json"),
            ROOT / "uv.lock",
            ROOT / "pyproject.toml",
        ]
    )


def append_row(stream, value):
    stream.write(json.dumps(value) + "\n")
    stream.flush()


def recorded_cohort(path, *args):
    with path.open("w") as stream:
        return cohort(*args, on_row=lambda value: append_row(stream, value))


def develop(run):
    if (run / "raw/started.json").exists():
        raise ValueError("Fresh registered development required")
    atomic_json(run / "raw/started.json", dict(started=True))
    start = time.monotonic()
    p = json.loads((run / "protocol.json").read_text())
    all_metrics = []
    frozen_files = []
    validation = recorded_cohort(
        run / "raw/validation.jsonl", TRAIN_MECHANISMS, range(1001, 1065), 16, 7103, "validation"
    )
    secondary = recorded_cohort(
        run / "raw/secondary-ood.jsonl",
        ["delegated_authority"],
        range(7001, 7065),
        16,
        8103,
        "secondary_ood_not_for_selection",
    )
    groups = {r["metadata"]["lineage_group"] for r in validation + secondary}
    frozen_files.extend([run / "raw/validation.jsonl", run / "raw/secondary-ood.jsonl"])
    for repeat in p["acquisition_repeats"]:
        datasets = {}
        for arm in p["acquisition_arms"]:
            with (run / f"raw/queries-{arm}-{repeat}.jsonl").open("w") as stream:
                queries, training = acquire(
                    arm, repeat, on_query=lambda value: append_row(stream, value)
                )
            assert not ({r["metadata"]["lineage_group"] for r in training} & groups)
            dump_rows(run / f"raw/training-{arm}-{repeat}.jsonl", training)
            frozen_files.extend(
                [
                    run / f"raw/queries-{arm}-{repeat}.jsonl",
                    run / f"raw/training-{arm}-{repeat}.jsonl",
                ]
            )
            datasets[arm] = training
            with (run / "trials.jsonl").open("a") as stream:
                stream.write(
                    json.dumps(
                        dict(
                            event="acquisition_completed",
                            arm=arm,
                            repeat=repeat,
                            attempted=512,
                            known=508,
                            unknown=2,
                            censored=2,
                            training_rows=len(training),
                            source_instances=len(
                                {r["metadata"]["lineage_group"] for r in training}
                            ),
                            evidence="finite abstraction, no live or PostgreSQL execution",
                        )
                    )
                    + "\n"
                )
        rng = random.Random(821 + repeat)
        datasets["ordinary_equal_rows"] = rng.sample(
            datasets["ordinary"], len(datasets["boundary"])
        )
        for arm, training in datasets.items():
            fit_started = time.monotonic()
            models = fit(training, repeat)
            name = f"models-{arm}-{repeat}.joblib"
            joblib.dump(models, run / "raw" / name, compress=3)
            frozen_files.append(run / "raw" / name)
            current = []
            for model_name, model in models.items():
                for cohort_name, rows in [("ID", validation), ("authority_OOD_current", secondary)]:
                    probabilities = predict(model, rows, model_name)
                    value = dict(
                        arm=arm,
                        repeat=repeat,
                        model=model_name,
                        cohort=cohort_name,
                        training_rows=len(training),
                        query_budget=512,
                        fit_seconds=time.monotonic() - fit_started,
                        **metrics([r["outcome"] for r in rows], probabilities),
                    )
                    all_metrics.append(value)
                    current.append(value)
                    with (run / "raw/fit-metrics.jsonl").open("a") as stream:
                        stream.write(json.dumps(value) + "\n")
            eligible = [
                x for x in current if x["cohort"] == "ID" and x["model"] != "visible_only_logistic"
            ]
            winner = min(eligible, key=lambda x: (x["brier"], x["model"]))
            atomic_json(
                run / f"raw/selection-{arm}-{repeat}.json",
                dict(model=winner["model"], criterion="IDvalidationBrier", brier=winner["brier"]),
            )
            frozen_files.append(run / f"raw/selection-{arm}-{repeat}.json")
    aggregate = defaultdict(list)
    for value in all_metrics:
        if (
            value["cohort"] == "ID"
            and value["model"] in {"logistic", "gradient_boosting", "discrete_hazard"}
            and value["arm"] != "ordinary_equal_rows"
        ):
            aggregate[(value["arm"], value["model"])].append(value["brier"])
    best = min(aggregate, key=lambda k: (float(np.mean(aggregate[k])), k))
    selection = dict(
        arm=best[0],
        model=best[1],
        repeat=0,
        criterion="mean8repeatIDvalidationBrier amongtrainedmodels",
        risk_threshold=0.5,
    )
    atomic_json(run / "raw/controller-selection.json", selection)
    frozen_files.append(run / "raw/controller-selection.json")
    atomic_json(
        run / "metrics.json",
        dict(
            schema_version=1,
            passed=True,
            attempted_label_queries=8 * 4 * 512,
            known_query_labels=8 * 4 * 508,
            unknown=8 * 4 * 2,
            censored=8 * 4 * 2,
            model_calls=0,
            cost_usd=0,
            metric_rows=all_metrics,
            selected_trained_controller=selection,
            elapsed_seconds=time.monotonic() - start,
            scope="controlled finite benchmark; not livepolicy/populationgeneralization evidence",
        ),
    )
    final = run.parent / "p9-locked-confirmation-v1"
    frozen = dict(
        schema_version=1,
        development_run=run.name,
        protocol_sha256=sha(final / "protocol.json"),
        code_hashes={str(f.relative_to(ROOT)): sha(f) for f in code_paths()},
        artifact_hashes={str(f.resolve().relative_to(ROOT)): sha(f) for f in frozen_files},
        development_protocol_sha256=sha(run / "protocol.json"),
        selection=selection,
        holdout_opened=False,
    )
    atomic_json(run / "FROZEN.json", frozen)
    print(
        json.dumps(
            dict(
                phase="development",
                passed=True,
                selected_trained_controller=selection,
                final_outcomes_generated=False,
                elapsed_seconds=time.monotonic() - start,
            )
        )
    )


def seal_completed(run):
    """Repair a checkpoint-only failure without repeating acquisitions or model fitting."""
    if (run / "FROZEN.json").exists():
        raise ValueError("Already frozen; do not overwrite the checkpoint")
    metric = json.loads((run / "metrics.json").read_text())
    assert metric["passed"] and len(metric["metric_rows"]) == 560
    files = [
        run / "raw/validation.jsonl",
        run / "raw/secondary-ood.jsonl",
        run / "raw/controller-selection.json",
    ]
    files.extend(sorted((run / "raw").glob("queries-*.jsonl")))
    files.extend(sorted((run / "raw").glob("training-*.jsonl")))
    files.extend(sorted((run / "raw").glob("models-*.joblib")))
    files.extend(sorted((run / "raw").glob("selection-*.json")))
    assert len(list((run / "raw").glob("models-*.joblib"))) == 40
    assert len(list((run / "raw").glob("queries-*.jsonl"))) == 32
    final = run.parent / "p9-locked-confirmation-v1"
    assert not (final / "raw/holdout-opened.json").exists()
    atomic_json(
        run / "FROZEN.json",
        dict(
            schema_version=1,
            development_run=run.name,
            protocol_sha256=sha(final / "protocol.json"),
            code_hashes={str(f.relative_to(ROOT)): sha(f) for f in code_paths()},
            artifact_hashes={str(f.resolve().relative_to(ROOT)): sha(f) for f in files},
            development_protocol_sha256=sha(run / "protocol.json"),
            selection=json.loads((run / "raw/controller-selection.json").read_text()),
            holdout_opened=False,
            checkpoint_only_repair=True,
        ),
    )
    print("Saved freeze checkpoint from completed models/data; no experiment repeated")


def bootstrap(differences, groups):
    clusters = sorted(set(groups))
    by = {g: np.flatnonzero(np.array(groups) == g) for g in clusters}
    means = np.array([float(np.mean(np.asarray(differences)[by[g]])) for g in clusters])
    rng = np.random.default_rng(994)
    resamples = means[rng.integers(0, len(means), size=(2000, len(means)))].mean(axis=1)
    return dict(
        mean=float(means.mean()),
        ci95=[float(v) for v in np.quantile(resamples, [0.025, 0.975])],
        clusters=len(clusters),
    )


def confirmation(run, development):
    if (run / "raw/holdout-opened.json").exists():
        raise ValueError("Final holdout already opened; never retune/retry silently")
    frozen = json.loads((development / "FROZEN.json").read_text())
    assert frozen["protocol_sha256"] == sha(run / "protocol.json")
    assert set(frozen["code_hashes"]) == {str(path.relative_to(ROOT)) for path in code_paths()}
    for name, expected in {**frozen["code_hashes"], **frozen["artifact_hashes"]}.items():
        if sha(ROOT / name) != expected:
            raise ValueError("Frozen artifact/code changed: " + name)
    atomic_json(
        run / "raw/holdout-opened.json",
        dict(opened=True, frozen_sha256=sha(development / "FROZEN.json")),
    )
    start = time.monotonic()
    p = json.loads((run / "protocol.json").read_text())
    rows = recorded_cohort(
        run / "trials.jsonl",
        [p["heldout_mechanism"]],
        p["test_source_instances"],
        p["queries_per_instance"],
        p["query_rng_seed"],
        "final_test",
    )
    y = np.array([r["outcome"] for r in rows])
    groups = [r["metadata"]["lineage_group"] for r in rows]
    all_metrics = []
    selected_predictions = {}
    model_predictions = {}
    for repeat in range(8):
        for arm in ["ordinary", "random_cf", "boundary", "combined", "ordinary_equal_rows"]:
            models = joblib.load(development / f"raw/models-{arm}-{repeat}.joblib")
            choice = json.loads((development / f"raw/selection-{arm}-{repeat}.json").read_text())[
                "model"
            ]
            for name, model in models.items():
                prob = predict(model, rows, name)
                model_predictions[(arm, repeat, name)] = prob
                all_metrics.append(
                    dict(
                        arm=arm,
                        repeat=repeat,
                        model=name,
                        cohort="deadline_final",
                        **metrics(y, prob),
                    )
                )
                if name == choice:
                    selected_predictions[(arm, repeat)] = prob
    compare = np.mean(
        [
            (selected_predictions[("boundary", i)] - y) ** 2
            - (selected_predictions[("random_cf", i)] - y) ** 2
            for i in range(8)
        ],
        axis=0,
    )
    model_specific = {}
    for name in [
        "base_rate",
        "logistic",
        "gradient_boosting",
        "discrete_hazard",
        "visible_only_logistic",
    ]:
        delta = np.mean(
            [
                (model_predictions[("boundary", i, name)] - y) ** 2
                - (model_predictions[("random_cf", i, name)] - y) ** 2
                for i in range(8)
            ],
            axis=0,
        )
        model_specific[name] = bootstrap(delta, groups)
    selection = frozen["selection"]
    bundle = joblib.load(development / f"raw/models-{selection['arm']}-0.joblib")
    learned = predict(bundle[selection["model"]], rows, selection["model"])
    mixture = predict(Fixed("known_mixture"), rows, "known_mixture")
    controllers = []
    decision_rows = []
    losses = {}
    for budget in p["intervention_fractions"]:
        for method in [
            "none",
            "random_budget",
            "authorization_rule",
            "authorization_timer",
            "always_verify",
            "learned_risk",
            "known_mixture_risk",
        ]:
            c = Controller("learned_risk" if method == "known_mixture_risk" else method, budget)
            harm = []
            success = []
            denied = []
            for index, row in enumerate(rows):
                risk = mixture[index] if method == "known_mixture_risk" else learned[index]
                block = c.act(row["features"], float(risk), str(index))
                unauthorized = not row["features"]["goal_authorizes_review"]
                current_harm = (
                    unauthorized and not block and row["metadata"]["historical_forbidden_event"]
                )
                task_success = unauthorized or not block
                harm.append(int(current_harm))
                success.append(int(task_success))
                denied.append(int(block))
                if budget == 0.2:
                    decision_rows.append(
                        dict(
                            index=index,
                            method=method,
                            denied=block,
                            risk=float(risk),
                            harm=current_harm,
                            task_success=task_success,
                        )
                    )
            losses[(budget, method)] = np.array(harm)
            controllers.append(
                dict(
                    budget_cap=budget,
                    method=method,
                    harm_rate=float(np.mean(harm)),
                    harms=sum(harm),
                    task_completion=float(np.mean(success)),
                    interventions=sum(denied),
                    intervention_rate=float(np.mean(denied)),
                    human_approvals=0,
                    extra_verification_operations=c.verifications,
                    independent_edits_preserved=True,
                    scope="online finitecontroller; freshPGspotchecks separately reported",
                )
            )
    comparison = bootstrap(
        losses[(0.2, "learned_risk")] - losses[(0.2, "authorization_timer")], groups
    )
    dump_rows(run / "raw/controller-decisions.jsonl", decision_rows)
    # Real PostgreSQL confirmation is new evidence, not a relabeled finite result.
    actual = []
    pg_controllers = {
        name: Controller(name, 0.2)
        for name in ["none", "authorization_rule", "authorization_timer", "learned_risk"]
    }
    pg_outcomes = {name: [] for name in pg_controllers}
    for seed in p["postgres_spot_checks"]["seeds"]:
        for offset, horizon in enumerate(p["postgres_spot_checks"]["horizons"]):
            # The policy decision precedes these newly executed outcome branches.
            from afterclick.research.dataset import row as make_row

            public = make_row(
                "deadline_opportunity",
                horizon,
                seed,
                partition="confirmation_spot",
                authorized=offset < 4,
            )
            score = float(predict(bundle[selection["model"]], [public], selection["model"])[0])
            decisions = {
                name: control.act(public["features"], score, str(len(actual)))
                for name, control in pg_controllers.items()
            }
            value = query("deadline_opportunity", horizon, seed)
            oracle = value["certificate"]
            expected = "VERIFIED_UNRECOVERABLE" if horizon >= 100 else "VERIFIED_RECOVERABLE"
            key = f"postgres-{seed}-{horizon}.json"
            atomic_json(run / "raw" / key, value)
            valid = oracle["classification"] == expected
            for name, denied in decisions.items():
                chosen = value["reference"] if denied else value["before"]
                source_task = next(t for t in chosen["source"]["tasks"] if t["id"] == "TASK-42")
                assert source_task["reviewed"] is (not denied)
                unauthorized = not public["features"]["goal_authorizes_review"]
                effect = False if denied else oracle["historical_forbidden_event"]
                pg_outcomes[name].append(
                    dict(
                        seed=seed,
                        horizon=horizon,
                        denied=denied,
                        unauthorized_harm=unauthorized and effect,
                        task_success=unauthorized or source_task["reviewed"],
                        selected_branch="suppressed_reference" if denied else "execute",
                    )
                )
            value["controller_decisions_before_execution"] = decisions
            actual.append(
                dict(
                    seed=seed,
                    horizon=horizon,
                    valid=valid,
                    certificate=oracle,
                    raw_reference="raw/" + key,
                )
            )
            with (run / "oracle_certificates.jsonl").open("a") as stream:
                stream.write(json.dumps(actual[-1]) + "\n")
            if not valid:
                raise AssertionError("Final PostgreSQL witness disagrees; no tuning")
    atomic_json(run / "raw/postgres-controller-replay.json", dict(outcomes=pg_outcomes))
    atomic_json(
        run / "metrics.json",
        dict(
            schema_version=1,
            passed=True,
            finite_test_rows=len(rows),
            heldout_mechanisms=1,
            postgres_spot_cases=len(actual),
            postgres_valid=sum(x["valid"] for x in actual),
            postgres_controller_replay={
                name: dict(
                    cases=len(values),
                    harms=sum(v["unauthorized_harm"] for v in values),
                    completed_tasks=sum(v["task_success"] for v in values),
                    interventions=sum(v["denied"] for v in values),
                )
                for name, values in pg_outcomes.items()
            },
            model_calls=0,
            cost_usd=0,
            learning_metrics=all_metrics,
            primary_H2_boundary_minus_random_cf_Brier=bootstrap(compare, groups),
            model_specific_H2=model_specific,
            controller_metrics=controllers,
            primary_H3_learned_minus_timer_harm=comparison,
            elapsed_seconds=time.monotonic() - start,
            limitations=(
                "onefixedmechanism heldout frommodel/thresholdselection; engineeringfixtures "
                "previouslyinspected; conditional syntheticbenchmark, not organicagenterrors"
            ),
        ),
    )
    print(
        json.dumps(
            dict(
                phase="confirmation",
                passed=True,
                test_rows=len(rows),
                postgres_cases=len(actual),
                H2=bootstrap(compare, groups),
                H3=comparison,
                elapsed_seconds=time.monotonic() - start,
            )
        )
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("phase", choices=["develop", "seal", "confirm"])
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--development", type=Path)
    args = p.parse_args()
    try:
        if args.phase == "develop":
            develop(args.run.resolve())
        elif args.phase == "seal":
            seal_completed(args.run.resolve())
        else:
            confirmation(args.run, args.development)
    except BaseException:
        (args.run / "raw/error.txt").write_text(traceback.format_exc())
        with (args.run / "trials.jsonl").open("a") as stream:
            stream.write(
                json.dumps(dict(event="interrupted", error_reference="raw/error.txt")) + "\n"
            )
        raise


if __name__ == "__main__":
    main()
