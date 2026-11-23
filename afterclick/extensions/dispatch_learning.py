"""Fixed local baselines and equal-query acquisition for the independent workload."""

import random

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from afterclick.extensions.dispatch_world import Visible, generate, hidden_record, label_panel

ARMS = ["ordinary", "random_cf", "boundary", "uncertainty_boundary", "combined"]
MODELS = [
    "base_rate",
    "timer",
    "observable_heuristic",
    "declared_train_law",
    "logistic",
    "gradient_boosting",
    "discrete_hazard",
]


def declared(features):
    x = Visible.model_validate(features)
    pu = (0.35 * (0.85 if x.alert else 0.15)) / (
        0.35 * (0.85 if x.alert else 0.15) + 0.65 * (0.15 if x.alert else 0.85)
    )
    pb = (0.45 * (0.8 if x.congestion else 0.2)) / (
        0.45 * (0.8 if x.congestion else 0.2) + 0.55 * (0.2 if x.congestion else 0.8)
    )
    h = x.query_horizon_ms
    sums = np.zeros(3)
    for busy, weight in [(False, 1 - pb), (True, pb)]:
        times = np.array(
            [
                a + b + c
                for a in ([60, 90, 120] if busy else [8, 16, 24])
                for b in [4, 12, 20]
                for c in range(16)
            ]
        )
        f = float(np.mean(times <= h))
        fv = float(
            np.mean([np.mean(times <= h + x.probe_eta_ms + 20 * busy + j) for j in range(21)])
        )
        sums += weight * np.array([pu * f, pu * fv, (1 - pu) * (1 - f)])
    return sums.tolist()


def acquire(arm, repeat, budget=256, on_row=None):
    rng = random.Random(1801 + repeat)
    rows = []
    origin = 10000 + repeat * 1000

    def query(i, h):
        row = dict(
            features=i.visible(h).model_dump(),
            outcomes=label_panel(i, h),
            metadata=dict(
                source=i.seed,
                mechanism=i.mechanism,
                lineage_group=f"train-{i.seed}",
                hidden=hidden_record(i),
                event_time=i.frontier if i.unsafe and i.frontier <= h else None,
                censor_time=h,
            ),
        )
        index = len(rows)
        row["measurement"] = (
            ("UNKNOWN" if index % 128 == 0 else "CENSORED") if index % 64 == 0 else "KNOWN"
        )
        rows.append(row)
        if on_row:
            on_row(row)
        return row["outcomes"][0]

    def boundaries(ids):
        for id in ids:
            i = generate(id)
            a, b = 0, 200
            ya = query(i, a)
            yb = query(i, b)
            for k in range(14):
                if ya != yb and b - a > 1:
                    h = (a + b) // 2
                    y = query(i, h)
                    if y == ya:
                        a, ya = h, y
                    else:
                        b, yb = h, y
                else:
                    query(
                        i,
                        max(0, min(200, b + rng.randint(-8, 8)))
                        if ya != yb
                        else rng.randrange(201),
                    )

    if arm == "ordinary":
        for k in range(budget):
            query(generate(origin + k), rng.randrange(201))
    elif arm == "random_cf":
        for k in range(budget // 2):
            i = generate(origin + k)
            query(i, rng.randrange(201))
            query(i, rng.randrange(201))
    elif arm in {"boundary", "uncertainty_boundary"}:
        ids = list(range(origin, origin + 64))
        if arm == "uncertainty_boundary":
            ids.sort(key=lambda j: abs(declared(generate(j).visible().model_dump())[1] - 0.5))
        boundaries(ids[: budget // 16])
    elif arm == "combined":
        for k in range(budget // 2):
            query(generate(origin + k), rng.randrange(201))
        boundaries(range(origin + 500, origin + 500 + budget // 32))
    else:
        raise ValueError(arm)
    assert len(rows) == budget
    # Predeclared incomplete-observation probes, never quietly converted to negatives.
    for k in range(0, budget, 64):
        rows[k]["measurement"] = "UNKNOWN" if k % 128 == 0 else "CENSORED"
    for row in rows:
        row.setdefault("measurement", "KNOWN")
    return rows


def fit(rows, seed):
    known = [r for r in rows if r["measurement"] == "KNOWN"]
    X = np.array([Visible.model_validate(r["features"]).vector() for r in known])
    Y = np.array([r["outcomes"] for r in known])
    result = {
        "base_rate": Y.mean(axis=0),
        "timer": {},
        "observable_heuristic": {},
        "declared_train_law": {},
        "logistic": [],
        "gradient_boosting": [],
        "discrete_hazard": {},
    }
    # Same query-time bins, with and without observable state. Hazard uses observed
    # first loss-of-prevention times, right censoring, not external receipt arrival.
    for observable in [False, True]:
        for alert in [0, 1] if observable else [-1]:
            for congestion in [0, 1] if observable else [-1]:
                group = [
                    r
                    for r in known
                    if not observable
                    or (
                        r["features"]["alert"] == alert
                        and r["features"]["congestion"] == congestion
                    )
                ]
                if not group:
                    group = known
                hazards = []
                survival = 1.0
                for end in range(10, 201, 10):
                    risk = sum(
                        (r["metadata"]["event_time"] or r["metadata"]["censor_time"]) >= end - 10
                        for r in group
                    )
                    events = sum(
                        r["metadata"]["event_time"] is not None
                        and end - 10 <= r["metadata"]["event_time"] < end
                        for r in group
                    )
                    survival *= 1 - min(1, events / max(1, risk))
                    hazards.append(1 - survival)
                result["discrete_hazard" if observable else "timer"][(alert, congestion)] = hazards
    for j in range(3):
        for name, model in [
            ("logistic", LogisticRegression(C=1, max_iter=300)),
            (
                "gradient_boosting",
                GradientBoostingClassifier(
                    n_estimators=32, max_depth=2, min_samples_leaf=5, random_state=seed
                ),
            ),
        ]:
            if len(set(Y[:, j])) < 2:
                model = DummyClassifier(strategy="constant", constant=int(Y[0, j]))
            model.fit(X, Y[:, j])
            result[name].append(model)
    return result


def predict(bundle, name, features):
    x = Visible.model_validate(features)
    if name == "declared_train_law":
        return declared(features)
    if name == "base_rate":
        return list(bundle[name])
    if name in {"logistic", "gradient_boosting"}:
        result = []
        for model in bundle[name]:
            p = model.predict_proba([x.vector()])[0]
            result.append(float(p[list(model.classes_).index(1)]) if 1 in model.classes_ else 0.0)
        return result
    if name == "observable_heuristic":
        pu = 0.8 if x.alert else 0.1
        f = min(1, x.query_horizon_ms / (130 if x.congestion else 45))
        fv = min(1, (x.query_horizon_ms + x.probe_eta_ms) / (130 if x.congestion else 45))
        return [pu * f, pu * fv, (1 - pu) * (1 - f)]
    table = bundle[name]
    key = (-1, -1) if name == "timer" else (x.alert, x.congestion)
    curve = table[key]

    def f(at):
        return curve[max(0, min(19, int(at) // 10))]

    return [
        f(x.query_horizon_ms),
        f(x.query_horizon_ms + x.probe_eta_ms + 10),
        0.65 * (1 - f(x.query_horizon_ms)),
    ]


def scores(y, p):
    y = np.asarray(y)
    p = np.asarray(p)
    bins = []
    for b in range(10):
        mask = (p >= b / 10) & ((p < (b + 1) / 10) if b < 9 else (p <= 1))
        if mask.any():
            bins.append(
                dict(
                    predicted=float(p[mask].mean()),
                    observed=float(y[mask].mean()),
                    n=int(mask.sum()),
                )
            )
    return dict(
        n=len(y),
        brier=float(brier_score_loss(y, p)),
        auroc=float(roc_auc_score(y, p)) if len(set(y)) == 2 else None,
        auprc=float(average_precision_score(y, p)) if y.any() else None,
        ece10=sum(x["n"] * abs(x["predicted"] - x["observed"]) for x in bins) / len(y),
        fnr_at_half=float(((p < 0.5) & (y == 1)).sum() / max(1, y.sum())),
        calibration_bins=bins,
    )
