"""Local project ledger. Estimates are admission guards, not provider billing caps."""

import fcntl
import json
import math
from pathlib import Path

from afterclick.agent.modal_policy import atomic_json

ALLOCATIONS = dict(p1c=3, trajectories=3, controller=4, confirmation=8, contingency=2)


class Supervisor:
    def __init__(self, path):
        self.path = Path(path)
        self.lock = None

    def __enter__(self):
        self.lock = self.path.with_suffix(".lock").open("a")
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.lock.close()
            raise ValueError("Another paid experiment owns the project lock") from None
        self.data = json.loads(self.path.read_text())
        if self.data["active"] is not None or self.data.get("unresolved_request", False):
            self.lock.close()
            raise ValueError("Unreconciled earlier experiment; no automatic paid resume")
        return self

    def __exit__(self, *args):
        self.lock.close()

    def save(self):
        atomic_json(self.path, self.data)

    def reconcile(self, billing):
        value = float(billing["metered_cost"])
        if not math.isfinite(value) or float(billing["billed_cost"]) != 0:
            raise ValueError("Unknown billing or out-of-pocket charges")
        self.data["account_metered_highwater_usd"] = max(
            value, self.data["account_metered_highwater_usd"]
        )
        delta = max(0, value - self.data["baseline_metered_usd"])
        self.data["account_additional_highwater_usd"] = max(
            delta, self.data["account_additional_highwater_usd"]
        )
        self.save()

    def reserve(self, run_id, category, cap, billing, provider_cap):
        self.reconcile(billing)
        if category not in ALLOCATIONS or not 0 < cap <= ALLOCATIONS[category]:
            raise ValueError("Unregistered category or unbounded cost")
        if any(r["run_id"] == run_id for r in self.data["runs"]):
            raise ValueError("Closed approval/run cannot be reused")
        charged = sum(r["guard_charge_usd"] for r in self.data["runs"])
        total = max(charged, self.data["account_additional_highwater_usd"])
        category_spend = sum(
            r["guard_charge_usd"] for r in self.data["runs"] if r["category"] == category
        )
        if (
            total + cap > self.data["allowance_usd"]
            or category_spend + cap > ALLOCATIONS[category]
            or self.data["baseline_credit_usd"] - total - cap < 8
            or provider_cap - self.data["account_metered_highwater_usd"] < cap
        ):
            raise ValueError("Project/category/reserve/provider headroom insufficient")
        self.data["active"] = dict(
            run_id=run_id,
            category=category,
            reserved_usd=cap,
            metered_before_usd=float(billing["metered_cost"]),
        )
        self.save()

    def finish(self, billing, elapsed, rate, *, idle_verified, uncertain=False):
        active = self.data["active"]
        assert active is not None
        self.reconcile(billing)
        estimate = elapsed * rate * 1.25
        # Unknown resource cleanup retains the complete reservation.
        charge = (
            max(
                estimate,
                max(0, float(billing["metered_cost"]) - active["metered_before_usd"]),
            )
            if idle_verified and not uncertain
            else active["reserved_usd"]
        )
        self.data["runs"].append(
            dict(
                **active,
                elapsed_seconds=elapsed,
                estimate_with_margin_usd=estimate,
                guard_charge_usd=charge,
                idle_verified=idle_verified,
                reported_account_delta_usd=max(
                    0, float(billing["metered_cost"]) - active["metered_before_usd"]
                ),
                actual_isolated_invoice_usd=None,
            )
        )
        self.data["active"] = None
        self.data["unresolved_request"] = uncertain
        self.save()
