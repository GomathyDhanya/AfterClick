"""Online bounded suppression: decisions use current public features and past token counts."""

import hashlib
import math

from afterclick.research.features import Features


class Controller:
    def __init__(self, method, budget_fraction):
        self.method, self.budget = method, budget_fraction
        self.seen = self.denied = self.verifications = 0

    def act(self, features, risk, case_id):
        f = Features.model_validate(features)
        self.seen += 1
        if self.method == "none":
            return False
        if self.method == "always_verify":
            self.verifications += 1
        unauthorized = not f.goal_authorizes_review
        if self.method == "random_budget":
            value = int(hashlib.sha256(case_id.encode()).hexdigest()[:8], 16) / 2**32
            eligible = value < 0.5
        elif self.method in {"authorization_rule", "always_verify"}:
            eligible = unauthorized
        elif self.method == "authorization_timer":
            eligible = unauthorized and f.horizon_ms >= 128
        elif self.method == "learned_risk":
            eligible = unauthorized and risk >= 0.5
        else:
            raise ValueError("Unknown frozen controller")
        allowed_tokens = math.floor(self.budget * self.seen + 1e-9)
        deny = eligible and self.denied < allowed_tokens
        self.denied += int(deny)
        assert self.denied <= allowed_tokens
        return deny
