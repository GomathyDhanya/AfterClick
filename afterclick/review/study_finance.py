"New explicitly authorized timing allocation, with untouched historical charges."

import fcntl
import json
import math
from pathlib import Path

from afterclick.agent.modal_policy import atomic_json


class TimingSupervisor:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.lock = Path("research_ops/SPEND_STATE.lock").open("a")
        fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        old = json.loads(Path("research_ops/SPEND_STATE.json").read_text())
        if old["active"] is not None or old.get("unresolved_request"):
            raise ValueError("Historical run unresolved")
        self.data = json.loads(self.path.read_text())
        if self.data["active"] is not None or self.data.get("unresolved_request"):
            raise ValueError("New study unresolved")
        return self

    def __exit__(self, *args):
        self.lock.close()

    def save(self):
        atomic_json(self.path, self.data)

    def reserve(self, run_id, category, cap, billing, provider_cap):
        auth = json.loads(Path("research_ops/TIMING_STUDY_AUTHORIZATION.json").read_text())
        if not auth["approved_by_user"] or auth["additional_ceiling_usd"] != 20:
            raise ValueError("Explicit new authority required")
        if (
            float(billing["billed_cost"]) != 0
            or float(billing["metered_cost_breakdown"]["llm_tokens"]) != 0
        ):
            raise ValueError("Cash/tokenAPI use not allowed")
        meter = float(billing["metered_cost"])
        if not math.isfinite(meter):
            raise ValueError("Unknown meter")
        self.data["account_metered_highwater_usd"] = max(
            self.data["account_metered_highwater_usd"], meter
        )
        charged = sum(r["guard_charge_usd"] for r in self.data["runs"])
        account_delta = max(
            0, self.data["account_metered_highwater_usd"] - self.data["baseline_metered_usd"]
        )
        spent = max(charged, account_delta)
        reported = 30 - abs(float(billing["adjustments"]["credits"]))
        credit = min(reported, self.data["baseline_credit_usd"] - spent)
        category_used = sum(
            r["guard_charge_usd"] for r in self.data["runs"] if r["category"] == category
        )
        if (
            category not in auth["initial_allocations"]
            or cap + category_used > auth["initial_allocations"][category]
        ):
            raise ValueError("New category cap")
        if any(r["run_id"] == run_id for r in self.data["runs"]):
            raise ValueError("Closed run cannot resume")
        if spent + cap > min(
            auth["additional_ceiling_usd"], auth["initial_operational_ceiling_usd"]
        ):
            raise ValueError("Study operational ceiling")
        if credit - cap < 1:
            raise ValueError("Conservative no-cash billing-lag buffer")
        if provider_cap - self.data["account_metered_highwater_usd"] < cap:
            raise ValueError("Provider cap headroom")
        self.data["active"] = dict(
            run_id=run_id,
            category=category,
            reserved_usd=cap,
            metered_before_usd=meter,
            authorization_source="TIMING_STUDY_AUTHORIZATION.json",
        )
        self.save()

    def finish(self, billing, elapsed, rate, *, idle_verified, uncertain=False):
        active = self.data["active"]
        meter = float(billing["metered_cost"])
        self.data["account_metered_highwater_usd"] = max(
            self.data["account_metered_highwater_usd"], meter
        )
        guard = (
            max(elapsed * rate * 1.25, max(0, meter - active["metered_before_usd"]))
            if idle_verified and not uncertain
            else active["reserved_usd"]
        )
        self.data["runs"].append(
            dict(
                **active,
                guard_charge_usd=guard,
                elapsed_seconds=elapsed,
                rate_usd_per_second=rate,
                idle_verified=idle_verified,
                actual_isolated_invoice_usd=None,
            )
        )
        self.data["active"] = None
        self.data["unresolved_request"] = (
            uncertain or not idle_verified or float(billing["billed_cost"]) != 0
        )
        self.save()
