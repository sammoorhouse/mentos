from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from statistics import mean
from zoneinfo import ZoneInfo

SMALL_PURCHASE_LIMIT_GBP = 10.0

SPEND_CONTEXT_EVIDENCE_KEYS = {
    "windows.last_7d.totals_by_category_gbp",
    "windows.last_7d.top_merchants_by_spend",
    "windows.last_7d.top_merchants_by_frequency",
    "windows.last_7d.late_night_tx_count",
    "windows.last_7d.small_purchase_count",
    "windows.last_14d.category_totals_gbp",
    "windows.last_14d.merchant_frequency",
    "windows.last_14d.top_merchants_by_spend",
    "windows.last_30d.category_totals_gbp",
    "windows.last_30d.merchant_frequency",
    "windows.last_30d.recurring_merchants_candidates",
    "windows.last_90d.baseline_by_category_gbp_per_week",
    "windows.last_90d.payday_candidates",
    "goals.active_goal_ids",
    "goals.active_goal_tags",
    "goals.recent_breakthroughs_count",
    "goals.recent_drift_events_count",
    "preferences.tone",
}


def _to_dt(raw: str, timezone: ZoneInfo) -> datetime:
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(timezone)


def _merchant_name(tx: dict) -> str:
    merchant = tx.get("merchant") or {}
    name = merchant.get("name") or tx.get("description") or "unknown"
    return str(name)


def _spend_gbp(tx: dict) -> float:
    amount = int(tx.get("amount", 0))
    if amount >= 0:
        return 0.0
    return abs(amount) / 100


def _window_transactions(transactions: list[dict], now: datetime, days: int, timezone: ZoneInfo) -> list[dict]:
    start = now - timedelta(days=days)
    return [tx for tx in transactions if start <= _to_dt(tx["created"], timezone) <= now]


def _category_totals(transactions: list[dict]) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for tx in transactions:
        totals[str(tx.get("category") or "uncategorised")] += _spend_gbp(tx)
    return {k: round(v, 2) for k, v in sorted(totals.items()) if v > 0}


def _merchant_spend(transactions: list[dict]) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for tx in transactions:
        totals[_merchant_name(tx)] += _spend_gbp(tx)
    return {k: round(v, 2) for k, v in totals.items() if v > 0}


def _merchant_frequency(transactions: list[dict]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for tx in transactions:
        if int(tx.get("amount", 0)) < 0:
            counter[_merchant_name(tx)] += 1
    return dict(counter)


def _top_by_spend(transactions: list[dict], limit: int = 5) -> list[dict]:
    spend = _merchant_spend(transactions)
    ranked = sorted(spend.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [{"name": name, "spend_gbp": value} for name, value in ranked]


def _top_by_frequency(transactions: list[dict], limit: int = 5) -> list[dict]:
    freq = _merchant_frequency(transactions)
    ranked = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [{"name": name, "count": value} for name, value in ranked]


def _late_night_count(transactions: list[dict], timezone: ZoneInfo) -> int:
    count = 0
    for tx in transactions:
        if int(tx.get("amount", 0)) >= 0:
            continue
        hour = _to_dt(tx["created"], timezone).hour
        if hour >= 22 or hour < 4:
            count += 1
    return count


def _small_purchase_count(transactions: list[dict]) -> int:
    return sum(1 for tx in transactions if 0 < _spend_gbp(tx) < SMALL_PURCHASE_LIMIT_GBP)


def _recurring_candidates(last_30: list[dict], timezone: ZoneInfo) -> list[dict]:
    grouped: dict[str, list[datetime]] = defaultdict(list)
    for tx in last_30:
        if int(tx.get("amount", 0)) >= 0:
            continue
        grouped[_merchant_name(tx)].append(_to_dt(tx["created"], timezone))
    out = []
    for name, dts in grouped.items():
        if len(dts) < 2:
            continue
        ordered = sorted(dts)
        gaps = [(ordered[i] - ordered[i - 1]).days for i in range(1, len(ordered))]
        out.append({"name": name, "approx_period_days": max(1, round(mean(gaps)))})
    return sorted(out, key=lambda x: (x["approx_period_days"], x["name"]))


def _baseline_by_category(last_90: list[dict], now: datetime, timezone: ZoneInfo) -> dict[str, float]:
    start_week = (now - timedelta(days=90)).replace(hour=0, minute=0, second=0, microsecond=0)
    week_count = max(1, (now - start_week).days // 7)
    totals = _category_totals(last_90)
    return {k: round(v / week_count, 2) for k, v in totals.items()}


def _payday_candidates(transactions: list[dict], timezone: ZoneInfo) -> list[dict]:
    inbound_days: Counter[int] = Counter()
    for tx in transactions:
        if int(tx.get("amount", 0)) <= 0:
            continue
        inbound_days[_to_dt(tx["created"], timezone).day] += 1
    if not inbound_days:
        return []
    max_hits = max(inbound_days.values())
    return [
        {"day_of_month": day, "confidence": round(count / max_hits, 2)}
        for day, count in sorted(inbound_days.items(), key=lambda x: x[1], reverse=True)[:3]
    ]


def build_spend_context(*, transactions: list[dict], goals: dict, prefs: dict, meta_now: str, timezone: str) -> dict:
    tz = ZoneInfo(timezone)
    now = _to_dt(meta_now, tz)

    last_7 = _window_transactions(transactions, now, 7, tz)
    last_14 = _window_transactions(transactions, now, 14, tz)
    last_30 = _window_transactions(transactions, now, 30, tz)
    last_90 = _window_transactions(transactions, now, 90, tz)

    return {
        "meta": {"timezone": timezone, "now": now.isoformat(), "currency": "GBP"},
        "windows": {
            "last_7d": {
                "totals_by_category_gbp": _category_totals(last_7),
                "top_merchants_by_spend": _top_by_spend(last_7),
                "top_merchants_by_frequency": _top_by_frequency(last_7),
                "late_night_tx_count": _late_night_count(last_7, tz),
                "small_purchase_count": _small_purchase_count(last_7),
            },
            "last_14d": {
                "category_totals_gbp": _category_totals(last_14),
                "merchant_frequency": _merchant_frequency(last_14),
                "top_merchants_by_spend": _top_by_spend(last_14),
            },
            "last_30d": {
                "category_totals_gbp": _category_totals(last_30),
                "merchant_frequency": _merchant_frequency(last_30),
                "recurring_merchants_candidates": _recurring_candidates(last_30, tz),
            },
            "last_90d": {
                "baseline_by_category_gbp_per_week": _baseline_by_category(last_90, now, tz),
                "payday_candidates": _payday_candidates(last_90, tz),
            },
        },
        "goals": {
            "active_goal_ids": goals.get("active_goal_ids", []),
            "active_goal_tags": goals.get("active_goal_tags", []),
            "recent_breakthroughs_count": int(goals.get("recent_breakthroughs_count", 0)),
            "recent_drift_events_count": int(goals.get("recent_drift_events_count", 0)),
        },
        "preferences": {
            "tone": prefs.get("tone", "supportive"),
            "quiet_hours": prefs.get("quiet_hours", {"start": "22:00", "end": "07:00"}),
            "max_notifications_per_day": int(prefs.get("max_notifications_per_day", 1)),
        },
    }
