import logging
from collections import defaultdict
from datetime import datetime, timedelta
from statistics import median

from .spend_filters import build_spend_filter_clause

logger = logging.getLogger("mentos.heuristics")


def _median_absolute_deviation(values: list[float]) -> float:
    if not values:
        return 0.0
    m = median(values)
    deviations = [abs(v - m) for v in values]
    return median(deviations)


def category_outliers(conn, days: int = 60) -> list[dict]:
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    cur = conn.execute(
        """
        SELECT day, category, total_amount
        FROM aggregates_daily
        WHERE day >= date(?)
        """,
        (since,),
    )
    data = defaultdict(list)
    for day, category, total_amount in cur.fetchall():
        data[category].append(float(total_amount))

    outliers = []
    for category, values in data.items():
        if len(values) < 7:
            continue
        m = median(values)
        mad = _median_absolute_deviation(values)
        outliers.append({"category": category, "median": m, "mad": mad})
    return outliers


def late_night_spend_count(conn, days: int = 7, tz=None) -> int:
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    filter_clause, filter_params = build_spend_filter_clause(conn)
    cur = conn.execute(
        f"""
        SELECT created_at, amount FROM transactions
        WHERE created_at >= ? AND amount < 0 AND is_pending = 0{filter_clause}
        """,
        (since, *filter_params),
    )
    count = 0
    for created_at, amount in cur.fetchall():
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except Exception:
            continue
        if tz:
            dt = dt.astimezone(tz)
        hour = dt.hour
        if hour >= 22 or hour < 4:
            count += 1
    return count


def budget_drift(conn) -> dict:
    now = datetime.utcnow()
    last_7 = (now - timedelta(days=7)).isoformat()
    prev_35 = (now - timedelta(days=35)).isoformat()
    prev_7 = (now - timedelta(days=7)).isoformat()
    filter_clause, filter_params = build_spend_filter_clause(conn)

    cur = conn.execute(
        f"""
        SELECT SUM(CASE WHEN amount < 0 THEN -amount ELSE 0 END)
        FROM transactions
        WHERE created_at >= ? AND is_pending = 0{filter_clause}
        """,
        (last_7, *filter_params),
    )
    last7 = cur.fetchone()[0] or 0

    cur = conn.execute(
        f"""
        SELECT SUM(CASE WHEN amount < 0 THEN -amount ELSE 0 END)
        FROM transactions
        WHERE created_at >= ? AND created_at < ? AND is_pending = 0{filter_clause}
        """,
        (prev_35, prev_7, *filter_params),
    )
    prev28 = cur.fetchone()[0] or 0

    baseline_per_day = prev28 / 28 if prev28 else 0
    drift_ratio = (last7 / 7) / baseline_per_day if baseline_per_day else 0
    return {"last7": last7, "baseline_per_day": baseline_per_day, "drift_ratio": drift_ratio}


def recurring_merchants(conn, months: int = 6) -> list[str]:
    since = (datetime.utcnow() - timedelta(days=months * 30)).isoformat()
    filter_clause, filter_params = build_spend_filter_clause(conn)
    cur = conn.execute(
        f"""
        SELECT merchant_name, date(created_at) as day
        FROM transactions
        WHERE created_at >= ? AND amount < 0 AND is_pending = 0 AND merchant_name IS NOT NULL{filter_clause}
        """,
        (since, *filter_params),
    )
    by_merchant = defaultdict(set)
    for merchant_name, day in cur.fetchall():
        month = day[:7]
        by_merchant[merchant_name].add(month)
    recurring = [m for m, months_set in by_merchant.items() if len(months_set) >= 3]
    return sorted(recurring)[:10]


def detect_salary(conn, months: int = 6) -> list[dict]:
    since = (datetime.utcnow() - timedelta(days=months * 30)).isoformat()
    cur = conn.execute(
        """
        SELECT description, amount, date(created_at) as day
        FROM transactions
        WHERE created_at >= ? AND amount > 0 AND is_pending = 0
        """,
        (since,),
    )
    candidates = defaultdict(list)
    for desc, amount, day in cur.fetchall():
        key = (desc or "")[:32]
        candidates[key].append({"day": day, "amount": amount})

    results = []
    for desc, items in candidates.items():
        if len(items) < 3:
            continue
        days = [int(i["day"].split("-")[2]) for i in items]
        avg_day = sum(days) / len(days)
        if all(abs(d - avg_day) <= 3 for d in days):
            avg_amount = sum(i["amount"] for i in items) / len(items)
            results.append({"description": desc, "avg_amount": avg_amount, "avg_day": avg_day})
    return results
