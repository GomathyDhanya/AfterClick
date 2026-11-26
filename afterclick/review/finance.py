"Explicit allocation transfer gate; preserves original charges and absolute ceilings."

import json
from datetime import datetime, timezone
from pathlib import Path

from afterclick.research.finance import Supervisor


class ReviewSupervisor(Supervisor):
    def __init__(self, path, approval_path):
        super().__init__(path)
        self.approval = json.loads(Path(approval_path).read_text())
        a = self.approval
        if a.get("status") != "explicitly_approved_by_user" or not a.get("user_message_sha256"):
            raise ValueError("New review allocation has not been explicitly approved")
        if a.get("experiment_id") != "w4-review-live-development-v1":
            raise ValueError("Wrong experiment")
        if a.get("transfer_from") != "contingency" or a.get("max_usd") != 1.25:
            raise ValueError("Only specified contingency transfer can be admitted")
        if datetime.now(timezone.utc) >= datetime.fromisoformat(a["expires_utc"]):
            raise ValueError("Approval expired")

    def reserve_review(self, billing, provider_cap):
        a = self.approval
        run_id = a["experiment_id"]
        cap = a["max_usd"]
        # Keep the original contingency category so ALL later legacy admissions
        # count this debit against the same 2 USD ceiling. Allocation is metadata,
        # not an extra category that could silently increase total category caps.
        super().reserve(run_id, "contingency", cap, billing, provider_cap)
        self.data["active"].update(
            authorization_source="explicit-review-allocation",
            allocation_id="review_development_v1",
            allocation_path=a.get("record_path"),
        )
        self.save()
        return dict(self.data["active"])
