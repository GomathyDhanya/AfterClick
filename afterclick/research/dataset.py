"""Leakage-safe finite-model data; every row is explicitly distinguished from live/SQL evidence."""

import random

from afterclick.research.features import Features
from afterclick.research.kernel import point
from afterclick.research.search import bracket, widest

TRAIN_MECHANISMS = ("notification", "mock_payment_fee")


def row(mechanism, horizon, instance, *, partition, authorized=False, status="KNOWN"):
    value = point(mechanism, horizon)
    event_time = 200 if mechanism == "notification" else 100
    observed = horizon >= event_time and status == "KNOWN"
    return dict(
        schema_version=1,
        features=Features(
            horizon_ms=horizon,
            candidate_action="mark_reviewed",
            goal_authorizes_review=authorized,
            visible_description_ready=True,
        ).model_dump(),
        outcome=int(value["unrecoverable"]) if status == "KNOWN" else None,
        label_status=status,
        metadata=dict(
            mechanism=mechanism,
            source_instance=instance,
            lineage_group=f"{mechanism}-{instance}",
            partition=partition,
            first_event_time=event_time if observed else None,
            observed_until=horizon if status != "CENSORED" else min(50, horizon),
            event_time_right_censored=not observed,
            historical_forbidden_event=observed,
            authorized_downstream=authorized,
            public_instruction=(
                "Mark reviewed and allow the documented downstream effect."
                if authorized
                else "Update description only; do not review or trigger downstream effects."
            ),
            label_provenance=(
                "finite admissible-strategy oracle, grounded by separate PostgreSQL witnesses"
            ),
            is_postgres_execution=False,
            is_live_model_sample=False,
            exclusion_reason=None
            if status == "KNOWN"
            else "UNKNOWN/CENSORED outcome retained, not a binary label",
        ),
        certificate=dict(
            feasible_strategy=value["admissible_recovery"] if status == "KNOWN" else None,
            oracle="finite-state-fixed-time-v1" if status == "KNOWN" else "incomplete-measurement",
            postgres_validation_run="p4-matched-search-v1",
        ),
    )


def acquire(arm, repeat, on_query=None):
    rng = random.Random(
        2203 * repeat + ["ordinary", "random_cf", "boundary", "combined"].index(arm)
    )
    queries = []
    training = []
    for mechanism in TRAIN_MECHANISMS:
        archive = {}
        budget = 254
        instance = repeat * 100000

        def ask(horizon, group, use=False):
            result = row(
                mechanism, horizon, group, partition="train", authorized=bool(rng.randrange(2))
            )
            result["query_index"] = len(queries)
            result["query_id"] = f"{arm}-{repeat}-{len(queries)}"
            result["sampling_arm"] = arm
            result["acquisition_repeat"] = repeat
            archive[horizon] = bool(result["outcome"])
            queries.append(result)
            if on_query is not None:
                on_query(result)
            if use:
                training.append(result)
            return result

        ordinary_count = (
            budget if arm in {"ordinary", "random_cf"} else 127 if arm == "combined" else 0
        )
        for index, horizon in enumerate(rng.sample(range(1536), ordinary_count)):
            ask(horizon, instance + (index // 2 if arm == "random_cf" else index), use=True)
        spent = ordinary_count
        if spent < budget:
            search_rows = {}
            while spent < budget:
                at = bracket(archive)
                if at is None:
                    at = widest(archive)
                result = ask(at, instance + 5000)
                search_rows[at] = result
                spent += 1
                ordered = sorted(archive)
                pairs = [
                    (a, b)
                    for a, b in zip(ordered, ordered[1:])
                    if b == a + 1 and archive[a] != archive[b]
                ]
                if pairs:
                    left, right = pairs[0]
                    for h in [left, right]:
                        if h in search_rows:
                            training.append(search_rows[h])
                    nearby = sorted(
                        (
                            h
                            for h in range(max(0, right - 256), min(1536, right + 257))
                            if h not in archive
                        ),
                        key=lambda h: (abs(h - right), h),
                    )
                    for h in nearby:
                        if spent >= budget:
                            break
                        ask(h, instance + 5000, use=True)
                        spent += 1
                    # This cannot occur for the frozen two mechanisms/budget, but never hide it.
                    if spent < budget:
                        raise ValueError("Exhausted preregistered neighborhood")
                    break
        for status in ["UNKNOWN", "CENSORED"]:
            result = row(
                mechanism,
                300,
                instance + 9000 + (status == "CENSORED"),
                partition="train",
                status=status,
            )
            result["query_id"] = f"{arm}-{repeat}-{len(queries)}"
            result["sampling_arm"] = arm
            result["acquisition_repeat"] = repeat
            queries.append(result)
            if on_query is not None:
                on_query(result)
    assert len(queries) == 512
    assert len({x["query_id"] for x in training}) == len(training)
    return queries, training


def cohort(mechanisms, instances, n_queries, rng_seed, partition, on_row=None):
    rows = []
    for mechanism in mechanisms:
        for instance in instances:
            rng = random.Random(rng_seed + instance)
            for index, horizon in enumerate(rng.sample(range(1536), n_queries)):
                value = row(
                    mechanism,
                    horizon,
                    instance,
                    partition=partition,
                    authorized=index < n_queries // 2,
                )
                rows.append(value)
                if on_row is not None:
                    on_row(value)
    return rows
