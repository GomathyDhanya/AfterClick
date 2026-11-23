"""Prospective public features. Metadata/oracle fields are rejected, not silently dropped."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Features(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    horizon_ms: int = Field(ge=0, le=1535)
    candidate_action: Literal["mark_reviewed"]
    goal_authorizes_review: bool
    visible_description_ready: bool

    def vector(self, *, visible_only=False):
        # Query horizon is chosen before acting; it is not a measured future event time.
        return [
            0 if visible_only else self.horizon_ms / 1535,
            int(self.goal_authorizes_review),
            int(self.visible_description_ready),
        ]


def vector(row, *, visible_only=False):
    return Features.model_validate(row["features"]).vector(visible_only=visible_only)
