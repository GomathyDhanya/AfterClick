"""Fixed small local predictors; no endpoint calls or automatic model searches."""

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from afterclick.research.features import vector


class Fixed:
    def __init__(self, kind, value=None):
        self.kind, self.value = kind, value

    def predict_proba(self, x):
        h = np.asarray(x)[:, 0] * 1535
        if self.kind == "base_rate":
            p = np.full(len(x), self.value)
        elif self.kind == "heuristic":
            p = (h >= 128).astype(float)
        else:
            p = np.where(h < 100, 0, np.where(h < 200, 0.5, 1.0))
        return np.column_stack([1 - p, p])


class Hazard:
    def fit(self, rows):
        self.hazards = []
        for start in range(0, 1536, 64):
            risk = events = 0
            for row in rows:
                m = row["metadata"]
                at = m["observed_until"]
                event = m["first_event_time"]
                if at >= start and (event is None or event >= start):
                    risk += 1
                if event is not None and start <= event < start + 64:
                    events += 1
            self.hazards.append((events + 0.5) / (risk + 1) if risk else 0)
        return self

    def predict_proba(self, x):
        h = np.asarray(x)[:, 0] * 1535
        survival = np.ones(len(x))
        for index, hazard in enumerate(self.hazards):
            exposure = np.clip((h - index * 64) / 64, 0, 1)
            survival *= np.power(1 - hazard, exposure)
        return np.column_stack([survival, 1 - survival])


def fit(rows, seed):
    x = np.asarray([vector(r) for r in rows])
    y = np.array([r["outcome"] for r in rows])
    models = dict(
        base_rate=Fixed("base_rate", float(y.mean())),
        heuristic=Fixed("heuristic"),
        known_mixture=Fixed("known_mixture"),
        discrete_hazard=Hazard().fit(rows),
    )
    models["logistic"] = LogisticRegression(C=1, max_iter=500, random_state=seed).fit(x, y)
    models["gradient_boosting"] = GradientBoostingClassifier(
        n_estimators=64, max_depth=2, min_samples_leaf=5, learning_rate=0.1, random_state=seed
    ).fit(x, y)
    visible = np.array([vector(r, visible_only=True) for r in rows])
    models["visible_only_logistic"] = LogisticRegression(C=1, max_iter=500, random_state=seed).fit(
        visible, y
    )
    return models


def predict(model, rows, name):
    x = [vector(r, visible_only=name == "visible_only_logistic") for r in rows]
    return np.clip(model.predict_proba(x)[:, 1], 0, 1)


def metrics(y, p):
    y = np.asarray(y)
    p = np.asarray(p)
    ece = 0
    for index in range(10):
        mask = (p >= index / 10) & (p < (index + 1) / 10 if index < 9 else p <= 1)
        if mask.any():
            ece += mask.mean() * abs(y[mask].mean() - p[mask].mean())
    positives = y == 1
    return dict(
        brier=float(brier_score_loss(y, p)),
        auroc=float(roc_auc_score(y, p)),
        auprc=float(average_precision_score(y, p)),
        ece10=float(ece),
        false_negative_rate_at_half=float(np.mean(p[positives] < 0.5)),
        uncertainty_fraction=float(np.mean((p >= 0.4) & (p <= 0.6))),
        n=len(y),
        prevalence=float(y.mean()),
    )
