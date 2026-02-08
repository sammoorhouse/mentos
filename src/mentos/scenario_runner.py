from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from statistics import mean
from zoneinfo import ZoneInfo


PREMIUM_MERCHANTS = ("gail", "waitrose", "pret", "whole foods")
BUDGET_MERCHANTS = ("greggs", "tesco", "co-op", "coop")
COFFEE_MERCHANTS = ("starbucks", "caff", "nero", "costa")
DINING_HINTS = ("restaurant", "pizza", "sushi", "burger")
DELIVERY_MERCHANTS = ("deliveroo", "just eat", "uber eats")
CONVENIENCE_MERCHANTS = ("uber", "deliveroo", "getir", "gorillas")
SUBSCRIPTION_MERCHANTS = ("netflix", "spotify", "icloud", "youtube premium")


@dataclass(frozen=True)
class InsightResult:
    insight_id: str
    severity: str
    evidence: dict


def _norm(value: str | None) -> str:
    return (value or "").lower().replace("’", "'").strip()


def _merchant_or_description(tx: dict) -> str:
    merchant = tx.get("merchant") or {}
    return f"{_norm(merchant.get('name'))} {_norm(tx.get('description'))}".strip()


def _to_dt(raw: str, tz: ZoneInfo) -> datetime:
    parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(tz)


def _spend_gbp(tx: dict) -> float:
    amount = int(tx.get("amount", 0))
    return abs(amount) / 100 if amount < 0 else 0.0


def _in_last_days(dt: datetime, now: datetime, days: int) -> bool:
    return now - timedelta(days=days) <= dt <= now


def _weekly_buckets(transactions: list[dict], now: datetime, weeks: int, tz: ZoneInfo, *, matcher) -> list[float]:
    end_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    out: list[float] = []
    for idx in range(weeks):
        week_start = end_week - timedelta(weeks=weeks - 1 - idx)
        week_end = week_start + timedelta(weeks=1)
        total = 0.0
        for tx in transactions:
            dt = _to_dt(tx["created"], tz)
            if week_start <= dt < week_end and matcher(tx):
                total += _spend_gbp(tx)
        out.append(total)
    return out


def _score_week(goal_id: str, week: dict) -> int:
    if goal_id == "goal_save_money":
        if week["delivery"] <= 25 and week["dining"] <= 35 and week["saved"] >= 20:
            return 2
        if week["delivery"] <= 45 and week["saved"] >= 10:
            return 1
        return 0
    return 2 if week["groceries"] >= 20 and week["delivery"] <= 20 else 1


def generateInsightsFromFixture(fixture_json: dict) -> dict:
    tz = ZoneInfo(fixture_json["meta"]["timezone"])
    now = _to_dt(fixture_json["meta"]["now"], tz)
    txs = fixture_json["monzo"].get("transactions", [])
    pot_transfers = fixture_json["monzo"].get("pot_transfers", [])

    last_7 = [tx for tx in txs if _in_last_days(_to_dt(tx["created"], tz), now, 7)]
    last_14 = [tx for tx in txs if _in_last_days(_to_dt(tx["created"], tz), now, 14)]
    last_30 = [tx for tx in txs if _in_last_days(_to_dt(tx["created"], tz), now, 30)]
    prior_60_to_30 = [
        tx
        for tx in txs
        if now - timedelta(days=90) <= _to_dt(tx["created"], tz) < now - timedelta(days=30)
    ]

    fired: list[dict] = []

    # 1 coffee streak
    coffee_days = sorted(
        {
            _to_dt(tx["created"], tz).date()
            for tx in last_7
            if any(k in _merchant_or_description(tx) for k in COFFEE_MERCHANTS) and tx.get("amount", 0) < 0
        }
    )
    streak = 0
    if coffee_days:
        streak = 1
        for i in range(1, len(coffee_days)):
            streak = streak + 1 if coffee_days[i] - coffee_days[i - 1] == timedelta(days=1) else 1
    coffee_total = sum(
        _spend_gbp(tx)
        for tx in last_7
        if any(k in _merchant_or_description(tx) for k in COFFEE_MERCHANTS)
    )
    if streak >= 5 and coffee_total >= 20:
        fired.append({"insight_id": "coffee_streak", "severity": "medium", "evidence": {"consecutive_days": streak, "total_spend_last_7_days_gbp": round(coffee_total, 2), "merchant_count": 1}})

    # 2 dining out
    dining = [tx for tx in last_7 if tx.get("category") == "eating_out" or any(k in _merchant_or_description(tx) for k in DINING_HINTS)]
    dining_total = sum(_spend_gbp(tx) for tx in dining)
    baseline = fixture_json.get("meta", {}).get("baselines", {}).get("dining_out_weekly_gbp", 40)
    if len(dining) >= 4 and dining_total > baseline:
        fired.append({"insight_id": "dining_out_frequency", "severity": "high" if dining_total >= baseline * 1.5 else "medium", "evidence": {"dining_out_count_last_7_days": len(dining), "dining_out_total_last_7_days_gbp": round(dining_total, 2), "baseline_gbp": baseline}})

    # 3 late night
    late_night = [tx for tx in last_7 if ((_to_dt(tx["created"], tz).hour >= 22) or (_to_dt(tx["created"], tz).hour < 4)) and tx.get("amount", 0) < 0]
    if len(late_night) >= 3:
        fired.append({"insight_id": "late_night_spend", "severity": "medium", "evidence": {"late_night_tx_count_last_7_days": len(late_night)}})

    # 4 subscription creep
    def subs_name(tx: dict) -> str | None:
        name = _merchant_or_description(tx)
        return next((s for s in SUBSCRIPTION_MERCHANTS if s in name), None)

    recent_subs = {subs_name(tx) for tx in last_30 if subs_name(tx)}
    previous_subs = {subs_name(tx) for tx in prior_60_to_30 if subs_name(tx)}
    new_subs = {s for s in recent_subs if s not in previous_subs}
    if new_subs:
        recent_total = sum(_spend_gbp(tx) for tx in last_30 if subs_name(tx))
        prev_total = sum(_spend_gbp(tx) for tx in prior_60_to_30 if subs_name(tx))
        if recent_total >= prev_total:
            fired.append({"insight_id": "subscription_creep", "severity": "medium", "evidence": {"new_recurring_count": len(new_subs), "recurring_total_monthly_gbp": round(recent_total, 2), "baseline_gbp": round(prev_total, 2)}})

    # 5 big ticket
    spends_last_7 = [tx for tx in last_7 if tx.get("amount", 0) < 0]
    if spends_last_7:
        biggest = max(spends_last_7, key=_spend_gbp)
        if _spend_gbp(biggest) >= 400:
            fired.append({"insight_id": "big_ticket_purchase", "severity": "high", "evidence": {"largest_tx_gbp": round(_spend_gbp(biggest), 2), "largest_tx_merchant": _merchant_or_description(biggest).strip()}})

    # 6 premium bias
    premium = [tx for tx in last_7 if any(k in _merchant_or_description(tx) for k in PREMIUM_MERCHANTS)]
    food_total = sum(_spend_gbp(tx) for tx in last_7 if tx.get("category") in {"groceries", "eating_out"})
    premium_total = sum(_spend_gbp(tx) for tx in premium)
    premium_share = (premium_total / food_total * 100) if food_total else 0
    if len(premium) >= 3 and premium_share >= 45:
        fired.append({"insight_id": "premium_everyday_bias", "severity": "medium", "evidence": {"premium_everyday_count_last_7_days": len(premium), "premium_share_of_food_spend_percent": round(premium_share, 2)}})

    # 7 grocery consistency positive
    grocery_weeks = _weekly_buckets(txs, now, 4, tz, matcher=lambda tx: tx.get("category") == "groceries")
    delivery_4w = _weekly_buckets(txs, now, 4, tz, matcher=lambda tx: any(k in _merchant_or_description(tx) for k in DELIVERY_MERCHANTS))
    non_zero = [w for w in grocery_weeks if w > 0]
    if len(non_zero) == 4 and (max(non_zero) - min(non_zero)) <= 20 and sum(delivery_4w) <= 60:
        fired.append({"insight_id": "grocery_consistency_praise", "severity": "low", "evidence": {"weeks_consistent": 4, "delivery_total_last_4_weeks": round(sum(delivery_4w), 2)}})

    # 8 savings consistency
    savings_weekly = defaultdict(float)
    for transfer in pot_transfers:
        if transfer.get("direction") != "into_pot":
            continue
        dt = _to_dt(transfer["created"], tz)
        if _in_last_days(dt, now, 28):
            wk = (dt - timedelta(days=dt.weekday())).date().isoformat()
            savings_weekly[wk] += float(transfer.get("amount", 0)) / 100
    if len(savings_weekly) >= 4 and sum(savings_weekly.values()) >= 80:
        fired.append({"insight_id": "saving_consistency_invest_prompt", "severity": "low", "evidence": {"weeks_savings_contributions": len(savings_weekly), "total_saved_last_4_weeks_gbp": round(sum(savings_weekly.values()), 2)}})

    # 9 convenience heavy
    convenience = [tx for tx in last_7 if any(k in _merchant_or_description(tx) for k in CONVENIENCE_MERCHANTS)]
    convenience_total = sum(_spend_gbp(tx) for tx in convenience)
    if len(convenience) >= 5 or convenience_total >= 80:
        fired.append({"insight_id": "convenience_spend", "severity": "medium", "evidence": {"convenience_count_last_7_days": len(convenience), "convenience_total_last_7_days_gbp": round(convenience_total, 2)}})

    # 10 on-plan reward
    week_data = []
    for week in range(2):
        start = now - timedelta(days=(week + 1) * 7)
        end = now - timedelta(days=week * 7)
        week_txs = [tx for tx in txs if start <= _to_dt(tx["created"], tz) < end]
        week_data.append(
            {
                "delivery": sum(_spend_gbp(tx) for tx in week_txs if any(k in _merchant_or_description(tx) for k in DELIVERY_MERCHANTS)),
                "dining": sum(_spend_gbp(tx) for tx in week_txs if tx.get("category") == "eating_out"),
                "saved": sum(float(t.get("amount", 0)) / 100 for t in pot_transfers if start <= _to_dt(t["created"], tz) < end and t.get("direction") == "into_pot"),
                "groceries": sum(_spend_gbp(tx) for tx in week_txs if tx.get("category") == "groceries"),
            }
        )
    green_weeks = sum(1 for week in week_data if _score_week(fixture_json["goal"]["id"], week) == 2)
    if green_weeks >= 2:
        fired.append({"insight_id": "on_plan_reward", "severity": "low", "evidence": {"green_weeks_recent": green_weeks}})

    # 11 delivery too high
    delivery = [tx for tx in last_7 if any(k in _merchant_or_description(tx) for k in DELIVERY_MERCHANTS)]
    delivery_total = sum(_spend_gbp(tx) for tx in delivery)
    if delivery_total >= 100 or len(delivery) >= 4:
        fired.append({"insight_id": "delivery_spend_high", "severity": "high", "evidence": {"delivery_total_last_7_days_gbp": round(delivery_total, 2), "delivery_count_last_7_days": len(delivery)}})

    return {
        "insightsFired": fired,
        "aggregates": {"tx_count": len(txs), "pot_transfer_count": len(pot_transfers)},
        "debug": {"now": now.isoformat()},
    }


def runScenario(fixture: dict) -> dict:
    results = generateInsightsFromFixture(fixture)
    tz = ZoneInfo(fixture["meta"]["timezone"])
    now = _to_dt(fixture["meta"]["now"], tz)
    txs = fixture["monzo"].get("transactions", [])
    pot_transfers = fixture["monzo"].get("pot_transfers", [])

    weekly_delivery = _weekly_buckets(txs, now, 8, tz, matcher=lambda tx: any(k in _merchant_or_description(tx) for k in DELIVERY_MERCHANTS))
    weekly_late_night = _weekly_buckets(txs, now, 8, tz, matcher=lambda tx: ((_to_dt(tx["created"], tz).hour >= 22) or (_to_dt(tx["created"], tz).hour < 4)))

    breakthroughs = []
    baseline_window = [v for v in weekly_delivery[:4] if v > 0]
    baseline = mean(baseline_window) if baseline_window else 0
    improve = mean(weekly_delivery[4:7]) if weekly_delivery[4:7] else 0
    if baseline > 0 and improve <= baseline * 0.75 and all(v <= baseline * 0.75 for v in weekly_delivery[4:7]):
        breakthroughs.append({"breakthrough_id": "delivery_reduction", "duration_weeks": 3, "improvement_percent": round((baseline - improve) / baseline * 100, 2), "triggered_at": "week_7"})

    monthly_saved = defaultdict(float)
    for transfer in pot_transfers:
        if transfer.get("direction") == "into_pot":
            dt = _to_dt(transfer["created"], tz)
            monthly_saved[dt.strftime("%Y-%m")] += float(transfer.get("amount", 0)) / 100
    if len(monthly_saved) >= 2:
        months = sorted(monthly_saved.keys())[-2:]
        if all(monthly_saved[m] >= fixture.get("meta", {}).get("saving_target_monthly_gbp", 150) for m in months):
            breakthroughs.append({"breakthrough_id": "surplus_two_months", "duration_months": 2, "evidence": {"total_saved_month1": round(monthly_saved[months[0]], 2), "total_saved_month2": round(monthly_saved[months[1]], 2)}})

    green_6 = fixture.get("meta", {}).get("green_weeks_last_6")
    if isinstance(green_6, int) and green_6 >= 4:
        breakthroughs.append({"breakthrough_id": "healthy_spending_streak", "green_weeks_last_6": green_6})

    baseline_ln_window = [v for v in weekly_late_night[:4] if v > 0]
    baseline_ln = mean(baseline_ln_window) if baseline_ln_window else 0
    improve_ln = mean(weekly_late_night[4:8]) if weekly_late_night[4:8] else 0
    if baseline_ln > 0 and improve_ln <= baseline_ln * 0.7:
        breakthroughs.append({"breakthrough_id": "late_night_reduction", "duration_weeks": 4, "improvement_percent": round((baseline_ln - improve_ln) / baseline_ln * 100, 2)})

    red_weeks_last_4 = fixture.get("meta", {}).get("red_weeks_last_4", 0)
    drift_events = []
    if red_weeks_last_4 >= 3:
        drift_events.append({"drift_event_created": True, "drift_status": "pending", "suggested_actions": ["keep", "relax", "switch", "pause"]})

    return {**results, "breakthroughs": breakthroughs, "drift_events": drift_events}
