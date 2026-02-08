from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class InsightCooldown:
    min_days_between_fires: int
    max_fires_per_30d: int


@dataclass(frozen=True)
class InsightCard:
    id: str
    title: str
    vibe_prompt: str
    goal_tags: list[str]
    evidence_keys_required: list[str]
    cooldown: InsightCooldown
    priority: int
    enabled: bool = True
    examples: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Preferences:
    tone: str
    quiet_hours: dict[str, str]
    max_notifications_per_day: int


@dataclass(frozen=True)
class SpendContext:
    meta: dict[str, Any]
    windows: dict[str, Any]
    goals: dict[str, Any]
    preferences: dict[str, Any]


@dataclass(frozen=True)
class Match:
    insight_id: str
    message: str
    evidence: dict[str, Any]


@dataclass(frozen=True)
class MatchResult:
    matches: list[Match]
    non_matches: list[str]
    raw: dict[str, Any]


@dataclass(frozen=True)
class NotificationRecord:
    insight_id: str
    dedupe_key: str
    evidence_signature: str
    status: str
    sent_at: datetime
    payload: dict[str, Any]
