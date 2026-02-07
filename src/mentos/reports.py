import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json

from .heuristics import budget_drift, category_outliers, late_night_spend_count, recurring_merchants, detect_salary
from .notifications import Notification, PushoverClient

logger = logging.getLogger("mentos.reports")


def _yesterday_range(tz: ZoneInfo):
    now = datetime.now(tz)
    start = datetime(now.year, now.month, now.day, tzinfo=tz) - timedelta(days=1)
    end = start + timedelta(days=1)
    return start, end


def nightly_report(conn, tz: ZoneInfo, notifier: PushoverClient | None = None) -> dict:
    start, end = _yesterday_range(tz)
    cur = conn.execute(
        """
        SELECT category, SUM(CASE WHEN amount < 0 THEN -amount ELSE 0 END) AS total
        FROM transactions
        WHERE created_at >= ? AND created_at < ? AND is_pending = 0
        GROUP BY category
        ORDER BY total DESC
        """,
        (start.isoformat(), end.isoformat()),
    )
    rows = cur.fetchall()
    summary_lines = []
    total_spend = 0
    for category, total in rows:
        total_spend += total or 0
        summary_lines.append(f"{category or 'uncategorized'}: £{(total or 0)/100:.2f}")

    nudges = []
    outliers = category_outliers(conn)
    for o in outliers:
        if o["mad"] == 0:
            continue
        # compare yesterday to median + 2*MAD
        for category, total in rows:
            if category == o["category"] and total and total > (o["median"] + 2 * o["mad"]):
                nudges.append(f"{category} was higher than usual yesterday.")
                break

    drift = budget_drift(conn)
    if drift["drift_ratio"] and drift["drift_ratio"] > 1.25:
        nudges.append("Spending is running hot vs the last month.")

    late_night = late_night_spend_count(conn, tz=tz)
    if late_night >= 5:
        nudges.append("Late-night spending is up this week.")

    if not nudges:
        nudges.append("Nice steady day yesterday.")

    headline = f"Yesterday: £{total_spend/100:.2f} spent"
    why = summary_lines[0] if summary_lines else "No spend recorded"
    action = nudges[0]

    payload = {
        "headline": headline,
        "why": why,
        "action": action,
        "summary": summary_lines,
    }

    if notifier:
        message = f"{why}. {action}"
        notifier.send(Notification(title=headline, message=message), conn=conn)

    return payload


def monthly_review(conn, tz: ZoneInfo, notifier: PushoverClient | None = None) -> dict:
    salaries = detect_salary(conn)
    recurring = recurring_merchants(conn)

    summary = []
    if salaries:
        summary.append(f"Possible salary: {salaries[0]['description']} (~£{salaries[0]['avg_amount']/100:.0f})")
    if recurring:
        summary.append(f"Recurring merchants: {', '.join(recurring[:5])}")
    if not summary:
        summary.append("Not enough data yet for strong patterns.")

    payload = {"summary": summary, "generated_at": datetime.now(tz).isoformat()}

    if notifier:
        notifier.send(Notification(title="Monthly review", message=" | ".join(summary[:2])), conn=conn)

    conn.execute(
        """
        INSERT INTO insights (id, user_id, kind, period_start, period_end, summary, detail_json, created_at)
        VALUES (hex(randomblob(16)), ?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (
            "user_1",
            "monthly_review",
            None,
            None,
            "\n".join(summary),
            json.dumps(payload),
        ),
    )
    conn.commit()

    return payload
