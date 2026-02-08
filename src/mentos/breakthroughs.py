import json
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from .chatgpt import ChatGPTClient

DEFAULT_USER_ID = "user_1"


@dataclass(frozen=True)
class BreakthroughRule:
    goal_type: str
    improvement_target: float
    sustained_weeks: int
    green_threshold_ratio: float
    trigger_green_weeks: int
    trigger_window_weeks: int
    description: str


V1_RULES: dict[str, BreakthroughRule] = {
    "reduce_food_delivery": BreakthroughRule(
        goal_type="spending",
        improvement_target=25.0,
        sustained_weeks=3,
        green_threshold_ratio=0.75,
        trigger_green_weeks=3,
        trigger_window_weeks=3,
        description="Reduce food delivery spend by 25% for 3 weeks.",
    ),
    "save_more_money": BreakthroughRule(
        goal_type="saving",
        improvement_target=0.0,
        sustained_weeks=8,
        green_threshold_ratio=1.0,
        trigger_green_weeks=2,
        trigger_window_weeks=2,
        description="End-of-month surplus for 2 months.",
    ),
    "healthy_spending": BreakthroughRule(
        goal_type="behavioural",
        improvement_target=10.0,
        sustained_weeks=6,
        green_threshold_ratio=0.85,
        trigger_green_weeks=4,
        trigger_window_weeks=6,
        description="Hit 4 green weeks out of 6.",
    ),
    "reduce_nightlife": BreakthroughRule(
        goal_type="spending",
        improvement_target=30.0,
        sustained_weeks=4,
        green_threshold_ratio=0.70,
        trigger_green_weeks=4,
        trigger_window_weeks=4,
        description="Reduce late-night spend by 30% for 4 weeks.",
    ),
}


def week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _money(value: float) -> str:
    return f"£{value / 100:.0f}"


def _get_goals(conn) -> list[dict[str, Any]]:
    cur = conn.execute("SELECT id, name, type, baseline_value FROM goals ORDER BY created_at ASC")
    out = []
    for goal_id, name, goal_type, baseline in cur.fetchall():
        out.append(
            {
                "id": goal_id,
                "name": name,
                "type": goal_type,
                "baseline_value": float(baseline or 0),
            }
        )
    return out


def seed_v1_goals(conn) -> None:
    now = datetime.utcnow().isoformat()
    for name, rule in V1_RULES.items():
        cur = conn.execute("SELECT id FROM goals WHERE name = ?", (name,))
        if cur.fetchone():
            continue
        conn.execute(
            """
            INSERT INTO goals (id, user_id, name, type, baseline_value, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), DEFAULT_USER_ID, name, rule.goal_type, 0.0, now),
        )
    conn.commit()


def _sum_spend_for_window(conn, start: datetime, end: datetime, mode: str) -> float:
    if mode == "delivery":
        cur = conn.execute(
            """
            SELECT SUM(CASE WHEN amount < 0 THEN -amount ELSE 0 END)
            FROM transactions
            WHERE created_at >= ?
              AND created_at < ?
              AND is_pending = 0
              AND (
                    lower(COALESCE(description, '')) LIKE '%deliveroo%'
                 OR lower(COALESCE(description, '')) LIKE '%uber eats%'
                 OR lower(COALESCE(description, '')) LIKE '%just eat%'
                 OR lower(COALESCE(merchant_name, '')) LIKE '%deliveroo%'
                 OR lower(COALESCE(merchant_name, '')) LIKE '%uber eats%'
                 OR lower(COALESCE(merchant_name, '')) LIKE '%just eat%'
              )
            """,
            (start.isoformat(), end.isoformat()),
        )
    elif mode == "nightlife":
        cur = conn.execute(
            """
            SELECT SUM(CASE WHEN amount < 0 THEN -amount ELSE 0 END)
            FROM transactions
            WHERE created_at >= ?
              AND created_at < ?
              AND is_pending = 0
              AND CAST(strftime('%H', created_at) AS INTEGER) >= 22
            """,
            (start.isoformat(), end.isoformat()),
        )
    elif mode == "savings_surplus":
        cur = conn.execute(
            """
            SELECT
              SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END),
              SUM(CASE WHEN amount < 0 THEN -amount ELSE 0 END)
            FROM transactions
            WHERE created_at >= ? AND created_at < ? AND is_pending = 0
            """,
            (start.isoformat(), end.isoformat()),
        )
        income, spend = cur.fetchone()
        return float((income or 0) - (spend or 0))
    elif mode == "healthy_spending":
        cur = conn.execute(
            """
            SELECT
              SUM(CASE WHEN amount < 0 AND category = 'groceries' THEN -amount ELSE 0 END),
              SUM(CASE WHEN amount < 0 THEN -amount ELSE 0 END)
            FROM transactions
            WHERE created_at >= ? AND created_at < ? AND is_pending = 0
            """,
            (start.isoformat(), end.isoformat()),
        )
        groceries, total_spend = cur.fetchone()
        if not total_spend:
            return 0.0
        return float(groceries or 0) / float(total_spend)
    else:
        return 0.0
    row = cur.fetchone()
    return float((row[0] if row else 0) or 0)


def _baseline(conn, metric_mode: str, now: datetime, weeks: int = 6) -> float:
    values = []
    end = week_start(now.date())
    for n in range(weeks, 0, -1):
        ws = end - timedelta(weeks=n)
        we = ws + timedelta(weeks=1)
        values.append(
            _sum_spend_for_window(
                conn,
                datetime.combine(ws, datetime.min.time()),
                datetime.combine(we, datetime.min.time()),
                metric_mode,
            )
        )
    vals = [v for v in values if v > 0]
    if not vals:
        return 0.0
    return sum(vals) / len(vals)


def _metric_mode(goal_name: str) -> str:
    if goal_name == "reduce_food_delivery":
        return "delivery"
    if goal_name == "reduce_nightlife":
        return "nightlife"
    if goal_name == "save_more_money":
        return "savings_surplus"
    if goal_name == "healthy_spending":
        return "healthy_spending"
    return ""


def score_week(metric_value: float, baseline: float, goal_name: str) -> int:
    if goal_name == "save_more_money":
        return 2 if metric_value > 0 else 0
    if goal_name == "healthy_spending":
        if metric_value >= 0.35:
            return 2
        if metric_value >= 0.25:
            return 1
        return 0
    if baseline <= 0:
        return 1
    ratio = metric_value / baseline
    if ratio < 0.75:
        return 2
    if ratio <= 1.0:
        return 1
    return 0


def update_weekly_goal_progress(conn, as_of: datetime | None = None) -> int:
    now = as_of or datetime.utcnow()
    current_week = week_start(now.date())
    previous_week = current_week - timedelta(weeks=1)
    start = datetime.combine(previous_week, datetime.min.time())
    end = datetime.combine(current_week, datetime.min.time())

    updated = 0
    for goal in _get_goals(conn):
        mode = _metric_mode(goal["name"])
        if not mode:
            continue
        baseline = goal["baseline_value"] or _baseline(conn, mode, now)
        metric_value = _sum_spend_for_window(conn, start, end, mode)
        score = score_week(metric_value, baseline, goal["name"])
        conn.execute(
            "UPDATE goals SET baseline_value = ? WHERE id = ?",
            (baseline, goal["id"]),
        )
        conn.execute(
            """
            INSERT INTO goal_progress (id, goal_id, week_start, metric_value, score)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(goal_id, week_start) DO UPDATE
            SET metric_value = excluded.metric_value,
                score = excluded.score
            """,
            (str(uuid.uuid4()), goal["id"], previous_week.isoformat(), metric_value, score),
        )
        updated += 1

    conn.commit()
    return updated


def _compute_improvement_percent(baseline: float, current: float, goal_name: str) -> float:
    if goal_name == "save_more_money":
        return 100.0 if current > 0 else 0.0
    if goal_name == "healthy_spending":
        return max(0.0, (current - baseline) * 100)
    if baseline <= 0:
        return 0.0
    return max(0.0, ((baseline - current) / baseline) * 100)


def _build_fallback_message(
    goal_name: str, baseline: float, current: float, weeks: int
) -> tuple[str, str]:
    if goal_name == "reduce_food_delivery":
        yearly = max(0, int((baseline - current) * 52 / 100))
        message = (
            f"Nice one. You've cut food delivery by about {_money(baseline - current)} a week "
            f"for {weeks} weeks straight. That's roughly £{yearly}/year back in your pocket."
        )
        return message, "Fancy setting a savings or investing goal with it?"
    if goal_name == "reduce_nightlife":
        message = (
            f"Strong shift: late-night spend has stayed down for {weeks} weeks. "
            "Bank balance and mornings should both feel better."
        )
        return message, "Want to redirect the difference into a weekend-fun budget?"
    if goal_name == "save_more_money":
        return (
            "You kept a monthly surplus for two months running. That's real runway.",
            "Want to automate part of that into a savings pot?",
        )
    return (
        "You've stayed aligned with your spending habits for weeks in a row.",
        "Want to level this up with a new goal?",
    )


def _generate_breakthrough_message(
    chatgpt_client: ChatGPTClient | None,
    goal_name: str,
    baseline: float,
    current: float,
    duration_weeks: int,
) -> tuple[str, str]:
    fallback_message, fallback_next = _build_fallback_message(
        goal_name, baseline, current, duration_weeks
    )
    if not chatgpt_client or not chatgpt_client.is_configured():
        return fallback_message, fallback_next

    prompt = (
        "Return JSON with keys headline, celebration_message, impact_summary, "
        "next_goal_suggestion. "
        "Tone: playful coaching. User goal={goal}, baseline={baseline:.2f}, "
        "current={current:.2f}, duration={weeks}."
    ).format(
        goal=goal_name, baseline=baseline, current=current, weeks=duration_weeks
    )
    content = chatgpt_client.generate_personalized_message(prompt, {"goal": goal_name})
    if not content:
        return fallback_message, fallback_next
    try:
        parsed = json.loads(content)
        celebration = str(parsed.get("celebration_message") or fallback_message)
        impact = str(parsed.get("impact_summary") or "").strip()
        next_goal = str(parsed.get("next_goal_suggestion") or fallback_next)
        body = celebration if not impact else f"{celebration} {impact}"
        return body, next_goal
    except Exception:
        return fallback_message, fallback_next


def detect_breakthroughs(conn, chatgpt_client: ChatGPTClient | None = None) -> list[dict[str, Any]]:
    created = []
    for goal in _get_goals(conn):
        rule = V1_RULES.get(goal["name"])
        if not rule:
            continue
        cur = conn.execute(
            """
            SELECT week_start, metric_value, score
            FROM goal_progress
            WHERE goal_id = ?
            ORDER BY week_start DESC
            LIMIT ?
            """,
            (goal["id"], rule.trigger_window_weeks),
        )
        rows = cur.fetchall()
        if len(rows) < rule.trigger_window_weeks:
            continue

        green_weeks = sum(1 for _, _, score in rows if score == 2)
        latest_metric = float(rows[0][1])
        improvement = _compute_improvement_percent(
            float(goal["baseline_value"] or 0), latest_metric, goal["name"]
        )

        if green_weeks < rule.trigger_green_weeks or improvement < rule.improvement_target:
            continue

        latest_week = rows[0][0]
        existing = conn.execute(
            """
            SELECT 1
            FROM breakthroughs
            WHERE goal_id = ?
              AND date(triggered_at) >= date(?, '-6 day')
            """,
            (goal["id"], latest_week),
        ).fetchone()
        if existing:
            continue

        message, next_goal = _generate_breakthrough_message(
            chatgpt_client,
            goal["name"],
            float(goal["baseline_value"] or 0),
            latest_metric,
            rule.sustained_weeks,
        )
        breakthrough = {
            "id": str(uuid.uuid4()),
            "goal_id": goal["id"],
            "triggered_at": datetime.utcnow().isoformat(),
            "improvement_percent": improvement,
            "duration_weeks": rule.sustained_weeks,
            "message": message,
            "next_goal_suggestion": next_goal,
            "goal_name": goal["name"],
        }
        conn.execute(
            """
            INSERT INTO breakthroughs (
                id, goal_id, triggered_at, improvement_percent,
                duration_weeks, message, next_goal_suggestion
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                breakthrough["id"],
                breakthrough["goal_id"],
                breakthrough["triggered_at"],
                breakthrough["improvement_percent"],
                breakthrough["duration_weeks"],
                breakthrough["message"],
                breakthrough["next_goal_suggestion"],
            ),
        )
        created.append(breakthrough)

    conn.commit()
    return created
