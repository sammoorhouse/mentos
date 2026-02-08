import json
import uuid
from datetime import datetime
from typing import Any

from .chatgpt import ChatGPTClient

DRIFT_WINDOW_WEEKS = 4
RED_WEEKS_THRESHOLD = 3
CONSECUTIVE_OFFTRACK_THRESHOLD = 4
RECENT_EVENT_COOLDOWN_DAYS = 14


def _build_fallback_message(goal_name: str, weeks_off_track: int) -> str:
    return (
        f"Looks like {goal_name.replace('_', ' ')} has felt tougher for the last "
        f"{weeks_off_track} weeks. Is life unusually hectic right now, and would a "
        "small goal tweak feel better?"
    )


def _generate_drift_message(
    chatgpt_client: ChatGPTClient | None,
    goal_name: str,
    weeks_off_track: int,
    red_weeks: int,
) -> str:
    fallback = _build_fallback_message(goal_name, weeks_off_track)
    if not chatgpt_client or not chatgpt_client.is_configured():
        return fallback

    prompt = (
        "Return JSON with key message only. Keep it supportive and non-judgmental, "
        "max 35 words, and end with a gentle question. "
        "Context: goal={goal}, weeks_off_track={weeks_off_track}, red_weeks={red_weeks}."
    ).format(goal=goal_name, weeks_off_track=weeks_off_track, red_weeks=red_weeks)

    content = chatgpt_client.generate_personalized_message(
        prompt,
        {
            "goal": goal_name,
            "weeks_off_track": weeks_off_track,
            "red_weeks": red_weeks,
            "event_type": "goal_drift",
        },
    )
    if not content:
        return fallback

    try:
        parsed = json.loads(content)
        return str(parsed.get("message") or fallback)
    except Exception:
        return content.strip() or fallback


def detect_goal_drift_events(
    conn,
    chatgpt_client: ChatGPTClient | None = None,
) -> list[dict[str, Any]]:
    created: list[dict[str, Any]] = []
    goals = conn.execute(
        "SELECT id, name, baseline_value FROM goals ORDER BY created_at ASC"
    ).fetchall()

    for goal_id, goal_name, baseline in goals:
        progress_rows = conn.execute(
            """
            SELECT week_start, metric_value, score
            FROM goal_progress
            WHERE goal_id = ?
            ORDER BY week_start DESC
            LIMIT ?
            """,
            (goal_id, DRIFT_WINDOW_WEEKS),
        ).fetchall()
        if len(progress_rows) < DRIFT_WINDOW_WEEKS:
            continue

        red_weeks = sum(1 for _, _, score in progress_rows if score == 0)
        off_track_weeks = sum(1 for _, _, score in progress_rows if score <= 1)
        consecutive_off_track = all(score <= 1 for _, _, score in progress_rows)

        average_spend = sum(float(metric_value or 0) for _, metric_value, _ in progress_rows) / len(
            progress_rows
        )
        baseline_value = float(baseline or 0)
        average_above_baseline = baseline_value > 0 and average_spend > baseline_value

        triggered = (
            red_weeks >= RED_WEEKS_THRESHOLD
            or consecutive_off_track
            or (average_above_baseline and off_track_weeks >= CONSECUTIVE_OFFTRACK_THRESHOLD)
        )
        if not triggered:
            continue

        latest_week = progress_rows[0][0]
        existing = conn.execute(
            """
            SELECT 1
            FROM goal_drift_events
            WHERE goal_id = ?
              AND date(triggered_at) >= date(?, ?)
            """,
            (goal_id, latest_week, f"-{RECENT_EVENT_COOLDOWN_DAYS} day"),
        ).fetchone()
        if existing:
            continue

        message = _generate_drift_message(chatgpt_client, goal_name, off_track_weeks, red_weeks)
        event = {
            "id": str(uuid.uuid4()),
            "goal_id": goal_id,
            "triggered_at": datetime.utcnow().isoformat(),
            "weeks_off_track": off_track_weeks,
            "message": message,
            "status": "pending",
            "goal_name": goal_name,
        }
        conn.execute(
            """
            INSERT INTO goal_drift_events (
                id, goal_id, triggered_at, weeks_off_track, message, status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event["id"],
                event["goal_id"],
                event["triggered_at"],
                event["weeks_off_track"],
                event["message"],
                event["status"],
            ),
        )
        created.append(event)

    conn.commit()
    return created
