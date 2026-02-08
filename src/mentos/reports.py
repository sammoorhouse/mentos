import json
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .chatgpt import ChatGPTClient
from .goals import goal_catalog, insight_patterns_for_goals, normalize_selected_goals
from .heuristics import (
    budget_drift,
    category_outliers,
    detect_salary,
    late_night_spend_count,
    recurring_merchants,
)
from .notifications import Notification, PushoverClient
from .storage import get_rule

logger = logging.getLogger("mentos.reports")




def _yesterday_range(tz: ZoneInfo):
    now = datetime.now(tz)
    start = datetime(now.year, now.month, now.day, tzinfo=tz) - timedelta(days=1)
    end = start + timedelta(days=1)
    return start, end


def _build_spending_context(conn, tz: ZoneInfo) -> dict:
    now = datetime.now(tz)
    last_30_days = (now - timedelta(days=30)).isoformat()

    cur = conn.execute(
        """
        SELECT
            SUM(CASE WHEN amount < 0 THEN -amount ELSE 0 END),
            SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END)
        FROM transactions
        WHERE created_at >= ? AND is_pending = 0
        """,
        (last_30_days,),
    )
    spend_30, income_30 = cur.fetchone()

    cur = conn.execute(
        """
        SELECT category, SUM(CASE WHEN amount < 0 THEN -amount ELSE 0 END) AS total
        FROM transactions
        WHERE created_at >= ? AND is_pending = 0
        GROUP BY category
        ORDER BY total DESC
        LIMIT 5
        """,
        (last_30_days,),
    )
    top_categories = [
        {"category": category or "uncategorized", "amount": int(total or 0)}
        for category, total in cur.fetchall()
    ]

    cur = conn.execute(
        """
        SELECT description, amount, created_at
        FROM transactions
        WHERE created_at >= ? AND amount < 0 AND is_pending = 0
        ORDER BY ABS(amount) DESC
        LIMIT 3
        """,
        (last_30_days,),
    )
    big_purchases = [
        {
            "description": description or "",
            "amount": int(-amount),
            "created_at": created_at,
        }
        for description, amount, created_at in cur.fetchall()
    ]

    return {
        "window_days": 30,
        "total_spend_30d": int(spend_30 or 0),
        "total_income_30d": int(income_30 or 0),
        "top_spend_categories": top_categories,
        "late_night_spend_count_7d": late_night_spend_count(conn, tz=tz),
        "budget_drift": budget_drift(conn),
        "recurring_merchants": recurring_merchants(conn),
        "salary_signals": detect_salary(conn),
        "big_purchases": big_purchases,
    }


def _personalize_insights(
    chatgpt_client: ChatGPTClient | None,
    spending_context: dict,
    selected_goals: list[str] | None,
) -> list[dict]:
    patterns = insight_patterns_for_goals(selected_goals)
    personalized = []
    for index, pattern in enumerate(patterns, start=1):
        final_message = pattern.prompt
        if chatgpt_client:
            generated = chatgpt_client.generate_personalized_message(pattern.prompt, spending_context)
            if generated:
                final_message = generated
        personalized.append(
            {
                "id": index,
                "insight_id": pattern.id,
                "insight": pattern.prompt,
                "goals": list(pattern.goals),
                "tags": list(pattern.tags),
                "final_message": final_message,
            }
        )
    return personalized


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


def monthly_review(
    conn,
    tz: ZoneInfo,
    notifier: PushoverClient | None = None,
    chatgpt_client: ChatGPTClient | None = None,
) -> dict:
    salaries = detect_salary(conn)
    recurring = recurring_merchants(conn)

    summary = []
    if salaries:
        salary = salaries[0]
        summary.append(
            f"Possible salary: {salary['description']} (~£{salary['avg_amount'] / 100:.0f})"
        )
    if recurring:
        summary.append(f"Recurring merchants: {', '.join(recurring[:5])}")
    if not summary:
        summary.append("Not enough data yet for strong patterns.")

    selected_goals = normalize_selected_goals(get_rule(conn, "insight_goals"))
    spending_context = _build_spending_context(conn, tz)
    insights = _personalize_insights(chatgpt_client, spending_context, selected_goals)

    payload = {
        "summary": summary,
        "generated_at": datetime.now(tz).isoformat(),
        "goal_catalog": goal_catalog(),
        "selected_goals": selected_goals,
        "spending_context": spending_context,
        "insights": insights,
        "chatgpt_enabled": bool(chatgpt_client and chatgpt_client.is_configured()),
    }

    if notifier:
        top_message = insights[0]["final_message"] if insights else "No insights available"
        notifier.send(Notification(title="Monthly review", message=top_message), conn=conn)

    conn.execute(
        """
        INSERT INTO insights (
            id, user_id, kind, period_start, period_end, summary, detail_json, created_at
        )
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
