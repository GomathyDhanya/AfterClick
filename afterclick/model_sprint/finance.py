"""Additional $6 sprint gate on top of all standing financial safeguards."""

import json
from pathlib import Path

from afterclick.research.finance import Supervisor


class SprintSupervisor(Supervisor):
    def reserve(self, run_id, category, cap, billing, provider_cap):
        auth = json.loads(Path("research_ops/SPRINT_AUTHORIZATION.json").read_text())
        baseline = set(auth["baseline_closed_runs"])
        charged = sum(
            r["guard_charge_usd"] for r in self.data["runs"] if r["run_id"] not in baseline
        )
        account_delta = max(
            0, float(billing["metered_cost"]) - auth["baseline_metered_highwater_usd"]
        )
        if max(charged, account_delta) + cap > auth["additional_cap_usd"]:
            raise ValueError("Sprint $6 envelope exhausted")
        super().reserve(run_id, category, cap, billing, provider_cap)
