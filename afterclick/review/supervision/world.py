"""Versioned pre-dispatch access workload; old workload implementations stay frozen."""

from sqlalchemy import select, update

from afterclick.review.progressing import ProgressingWorld
from afterclick.tcope.workloads import runtime


class SupervisionWorld(ProgressingWorld):
    def action(self, name, action_id, actor, nonce):
        result = super().action(name, action_id, actor, nonce)
        if name == "Grant access" and self.spec.schedule.get("dispatch_on_grant", False):
            with self.db.transaction() as c:
                row = c.execute(select(runtime)).mappings().one()
                state = dict(row["state"])
                if not state["pending"] and not state["ticket_checked"] and not state["done"]:
                    ms = self.elapsed()
                    state.update(
                        pending=True,
                        deadline=ms + self.spec.schedule.get("action_delay_ms", 1000),
                        read_due=ms + self.spec.schedule.get("action_delay_ms", 1000) + 1500,
                        action_id=action_id,
                        source_actor=actor,
                    )
                    self._event(c, "request.scheduled_after_grant", state, ms)
                    c.execute(update(runtime).values(state=state, clock_ms=ms))
            result = self.public()
        return result
