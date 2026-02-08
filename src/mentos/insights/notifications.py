from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .cards import get_insight_cards


@dataclass(frozen=True)
class GateDecision:
    allowed: list[dict]
    suppressed: list[dict]


def _in_quiet_hours(now: datetime, quiet_hours: dict[str, str]) -> bool:
    start_h, start_m = [int(v) for v in quiet_hours["start"].split(":")]
    end_h, end_m = [int(v) for v in quiet_hours["end"].split(":")]
    start = now.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
    end = now.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
    if start <= end:
        return start <= now < end
    return now >= start or now < end


def _week_start_key(now: datetime) -> str:
    start = (now - timedelta(days=now.weekday())).date().isoformat()
    return start


def dedupe_key(insight_id: str, now: datetime, evidence: dict) -> str:
    signature = json.dumps(evidence, sort_keys=True)
    base = f"{insight_id}:{_week_start_key(now)}:{signature}".encode("utf-8")
    return hashlib.sha256(base).hexdigest()


def apply_notification_policy(*, matches: list[dict], prefs: dict, previous_notifications: list[dict], now_iso: str, timezone: str, cards_dir: str = "insights/cards") -> GateDecision:
    now = datetime.fromisoformat(now_iso.replace("Z", "+00:00")).astimezone(ZoneInfo(timezone))
    cards = {c.id: c for c in get_insight_cards(cards_dir)}

    allowed: list[dict] = []
    suppressed: list[dict] = []

    if _in_quiet_hours(now, prefs["quiet_hours"]):
        return GateDecision(allowed=[], suppressed=[{"reason": "quiet_hours", "insight_id": m["insight_id"]} for m in matches])

    sent_today = [n for n in previous_notifications if n.get("status") == "sent" and n.get("sent_at", "")[:10] == now.date().isoformat()]

    for match in matches:
        insight_id = match["insight_id"]
        card = cards[insight_id]
        if len(allowed) + len(sent_today) >= prefs["max_notifications_per_day"]:
            suppressed.append({"insight_id": insight_id, "reason": "daily_cap"})
            continue

        key = dedupe_key(insight_id, now, match.get("evidence", {}))
        prior = [n for n in previous_notifications if n.get("insight_id") == insight_id and n.get("status") == "sent"]
        if any(n.get("dedupe_key") == key for n in prior):
            suppressed.append({"insight_id": insight_id, "reason": "dedupe"})
            continue

        recent_30d = [n for n in prior if datetime.fromisoformat(n["sent_at"]) >= now - timedelta(days=30)]
        if len(recent_30d) >= card.cooldown.max_fires_per_30d:
            suppressed.append({"insight_id": insight_id, "reason": "max_fires_per_30d"})
            continue

        if prior:
            last_sent = max(datetime.fromisoformat(n["sent_at"]) for n in prior)
            if last_sent > now - timedelta(days=card.cooldown.min_days_between_fires):
                suppressed.append({"insight_id": insight_id, "reason": "cooldown_days"})
                continue

        allowed_match = {**match, "dedupe_key": key}
        allowed.append(allowed_match)

    return GateDecision(allowed=allowed, suppressed=suppressed)


def serialize_notification(match: dict, status: str, now_iso: str) -> dict:
    return {
        "insight_id": match["insight_id"],
        "dedupe_key": match.get("dedupe_key"),
        "evidence_signature": json.dumps(match.get("evidence", {}), sort_keys=True),
        "status": status,
        "sent_at": now_iso,
        "payload": match,
    }
