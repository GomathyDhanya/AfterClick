"""Initialize a NEW belief world with already-known public facts, never source internals."""

from contextlib import contextmanager
from uuid import uuid4

import httpx
from sqlalchemy import select, update

from afterclick.tcope.controllers import PublicDecision, service_state
from afterclick.tcope.workloads import WorkloadWorld, runtime


class BeliefWorld(WorkloadWorld):
    def __init__(self, spec, public):
        if not isinstance(public, PublicDecision):
            raise TypeError("Public projection required")
        self.public_initial = service_state(public.observation)
        self.known_count = self.public_initial.get("observed_receipts", 0)
        if type(self.known_count) is not int or not 0 <= self.known_count <= 3:
            raise ValueError("Unsupported public receipt count")
        self.known_seeded = False
        super().__init__(spec)

    def initialize(self, checkpoint=None):
        super().initialize(checkpoint)
        if checkpoint:
            return
        visible = self.public_initial
        with self.db.transaction() as c:
            row = c.execute(select(runtime)).mappings().one()
            state = dict(row["state"])
            state.update(
                permission=visible.get("permission") == "granted",
                staged=visible.get("preparation") == "staged",
                canceled=visible.get("cancellation") == "requested",
            )
            # Public resolved + zero observed receipts is evidence, not private
            # exact future. This handles the actually observed successful protection.
            if visible.get("request_resolved"):
                state.update(
                    pending=False,
                    inflight=False,
                    done=True,
                    outcome_known=True,
                    ticket=False,
                    ticket_checked=self.spec.family == "access",
                    ack_at=0,
                )
            age = visible.get("age_ms", 0)
            if visible.get("acknowledgment") == "verified":
                state.update(
                    verified=True,
                    verify_resolved=visible.get("request_resolved", False),
                    verified_ms=age - (visible.get("verification_age_ms") or 0),
                )
            c.execute(update(runtime).values(state=state, clock_ms=age))
            self.offset = age

    @contextmanager
    def serve(self):
        with super().serve() as origin:
            if self.known_count and not self.known_seeded:
                # Represent public count with NEW forecast-only identities. Never
                # copy a source receipt, timestamp, action ID or hidden history.
                ids = []
                kind = {
                    "publication": "notice.delivered",
                    "resource": "resource.consumed",
                    "access": "external.read",
                }[self.spec.family]
                for index in range(self.known_count):
                    identity = "belief-known-" + uuid4().hex
                    payload = dict(
                        id=identity,
                        kind=kind,
                        action_id=identity,
                        payload=dict(synthetic=True, source="public_known_count"),
                    )
                    stamp = dict(action_id=identity, source_actor="belief-initializer")
                    with self.db.transaction() as c:
                        self._event(c, "dispatch.issued", stamp, self.offset, payload)
                    response = httpx.post(
                        self.receiver_url + "/observe", json=payload, timeout=5, trust_env=False
                    )
                    response.raise_for_status()
                    with self.db.transaction() as c:
                        self._event(c, "observer.acknowledged", stamp, self.offset, response.json())
                    ids.append(identity)
                with self.db.transaction() as c:
                    row = c.execute(select(runtime)).mappings().one()
                    state = dict(
                        row["state"], verify_receipts=ids, pending=False, inflight=False, done=True
                    )
                    c.execute(update(runtime).values(state=state))
                self.known_seeded = True
            yield origin
