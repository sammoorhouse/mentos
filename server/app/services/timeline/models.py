from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


EventType = Literal[
    "status",
    "weekly_progress",
    "insight",
    "goal_update",
    "breakthrough",
    "streak_update",
    "streak_broken",
    "monthly_framing",
    "quarterly_review",
    "year_review",
]


class DateRange(BaseModel):
    start: datetime
    end: datetime


class Evidence(BaseModel):
    transaction_ids: list[str] = Field(default_factory=list)
    date_range: DateRange
    metrics: dict[str, float | int]


class TimelineAction(BaseModel):
    id: str
    label: str
    kind: Literal["primary", "secondary"]
    action_type: Literal["accept_targets", "open_goal_realign", "view_insight", "open_settings"]
    payload: dict[str, Any] = Field(default_factory=dict)


class TimelineEvent(BaseModel):
    id: str
    type: EventType
    occurred_at: datetime
    title: str
    body: str
    meta: dict[str, Any] = Field(default_factory=dict)
    evidence: Evidence
    actions: list[TimelineAction] = Field(default_factory=list)
    priority: int = 0
    schema_version: int = 1


class TimelinePage(BaseModel):
    events: list[TimelineEvent]
    next_cursor: str | None = None
