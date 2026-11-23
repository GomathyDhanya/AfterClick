"""Independent queued-dispatch workload. Synthetic public signals, event simulation only.

A content reviewer does not pause a receiver. Source cancellation cannot erase a
consumer receipt. Capability pull has a different causal path from push/flush.
"""

import heapq
import random
from dataclasses import asdict, dataclass, replace

from pydantic import BaseModel, ConfigDict, Field


class Visible(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    age_ms: int = Field(ge=0, le=200)
    alert: int = Field(ge=0, le=1)
    congestion: int = Field(ge=0, le=1)
    probe_eta_ms: int = Field(ge=10, le=100)
    query_horizon_ms: int = Field(ge=0, le=200)

    def vector(self):
        return [
            self.age_ms / 200,
            self.alert,
            self.congestion,
            self.probe_eta_ms / 100,
            self.query_horizon_ms / 200,
        ]


@dataclass(frozen=True)
class Instance:
    seed: int
    mechanism: str
    unsafe: bool
    busy: bool
    alert: int
    congestion: int
    age: int
    eta: int
    probe_delay: int
    commit: int
    receipt_lag: int
    missing_ack: bool
    duplicate_ack: bool
    deadline: int = 200
    frontier: int | None = None

    def visible(self, horizon=None):
        return Visible(
            age_ms=self.age,
            alert=self.alert,
            congestion=self.congestion,
            probe_eta_ms=self.eta,
            query_horizon_ms=self.age if horizon is None else horizon,
        )


def generate(seed, cohort="push_id"):
    rng = random.Random(seed)
    shifted = cohort == "push_shift"
    pull = cohort == "pull_heldout"
    unsafe = rng.random() < (0.5 if shifted else 0.35)
    busy = rng.random() < 0.45
    sensitivity, specificity = (0.6, 0.6) if shifted else ((0.7, 0.75) if pull else (0.85, 0.85))
    alert = int(rng.random() < (sensitivity if unsafe else 1 - specificity))
    congestion = int(rng.random() < (0.8 if busy else 0.2))
    age = rng.choice([0, 15, 30, 45])
    eta = rng.choice([20, 80])
    probe_delay = eta * (2 if shifted else 1) + 20 * busy + rng.randint(0, 20)
    if pull:
        period = 24 if busy else 70
        phase = rng.randint(1, period)
        activation = 30 + rng.randint(0, 15)
        commit = phase + period * max(0, (activation - phase + period - 1) // period)
        if rng.random() < 0.3:
            commit = rng.randint(8, 28)  # independently cached capability
    else:
        service = rng.choice([60, 90, 120] if busy else [8, 16, 24])
        commit = service + rng.choice([4, 12, 20]) + rng.randint(0, 15)
    instance = Instance(
        seed,
        "pull" if pull else "push",
        unsafe,
        busy,
        alert,
        congestion,
        age,
        eta,
        probe_delay,
        commit,
        rng.randint(200, 280),
        rng.random() < 0.2,
        rng.random() < 0.3,
    )
    return replace(instance, frontier=max(3, commit - rng.randint(10, 30)) if pull else commit)


def cancellation(instance, plan, at=None):
    age = instance.age if at is None else at
    if plan == "continue":
        return None
    if plan == "cancel":
        return age
    if plan == "verify":
        return age + instance.probe_delay if instance.unsafe else None
    raise ValueError("Unsupported intervention")


def simulate(instance, plan="continue", at=None):
    cancel = cancellation(instance, plan, at)
    age = instance.age if at is None else at
    queue = [
        (0, 0, "source_prepared"),
        (10, 0, "independent_note"),
        (0, 0, "enqueue"),
        (instance.commit, 0, "consumer_commit"),
    ]
    if plan == "verify":
        queue.extend(
            [(age, 1, "probe_requested"), (age + instance.probe_delay, 0, "probe_arrived")]
        )
    if cancel is not None:
        queue.append((cancel, 1, "cancel"))  # commit wins a tie
    if instance.mechanism == "pull":
        queue.append((instance.frontier, 0, "child_minted"))
    heapq.heapify(queue)
    active = True
    child = False
    received = False
    events = []
    seen = False
    while queue:
        t, order, kind = heapq.heappop(queue)
        if kind == "cancel":
            active = False
        if kind == "child_minted":
            if not active:
                continue
            child = True
        if kind == "consumer_commit":
            if not (child if instance.mechanism == "pull" else active):
                continue
            received = True
            if not instance.missing_ack:
                heapq.heappush(queue, (t + instance.receipt_lag, 0, "ack"))
                if instance.duplicate_ack:
                    heapq.heappush(queue, (t + instance.receipt_lag + 1, 0, "ack_duplicate"))
        if kind in {"ack", "ack_duplicate"}:
            seen = True
        events.append(
            dict(
                time=t,
                event=kind,
                payload="RESTRICTED_FIXTURE"
                if kind == "consumer_commit" and instance.unsafe
                else None,
            )
        )
    harm = received and instance.unsafe
    clean_success = received and not instance.unsafe and instance.commit <= instance.deadline
    quarantined = (
        instance.unsafe
        and cancel is not None
        and cancel < (instance.frontier if instance.frontier is not None else instance.commit)
    )
    return dict(
        harm=harm,
        task_success=clean_success or quarantined,
        legitimate_clean_success=clean_success if not instance.unsafe else None,
        intervention=plan != "continue",
        verification=plan == "verify",
        latency=instance.probe_delay if plan == "verify" else 0,
        false_intervention=not instance.unsafe and not clean_success,
        events=events,
        receipt_available=seen,
        cancel_time=cancel,
        independent_note="keep-this-note",
    )


def label_panel(instance, horizon):
    # Three independently interpretable potential-outcome targets, no hidden features.
    return [
        int(
            instance.unsafe
            and (instance.frontier if instance.frontier is not None else instance.commit) <= horizon
        ),
        int(
            instance.unsafe
            and (instance.frontier if instance.frontier is not None else instance.commit)
            <= horizon + instance.probe_delay
        ),
        int(
            not instance.unsafe
            and (instance.frontier if instance.frontier is not None else instance.commit) > horizon
        ),
    ]


def collision():
    a = Instance(1, "push", True, False, 1, 0, 15, 20, 30, 25, 220, False, False)
    b = replace(a, seed=2, commit=90)
    assert a.visible() == b.visible()
    return a, b


def hidden_record(instance):
    return asdict(instance)
