from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from app.services.timeline.evidence import build_evidence
from app.services.timeline.models import TimelineAction, TimelineEvent
from app.services.timeline.targets import suggested_target


def _at_day(day: date, tz: ZoneInfo) -> datetime:
    return datetime.combine(day, time.min, tzinfo=tz)


def monthly_event(user_id: str, month_start: date, under_budget_days: int, longest_streak: int, last_month_takeaway: int, prev_takeaway: int, tz: ZoneInfo, event_id: str) -> TimelineEvent:
    delta = 0
    if prev_takeaway > 0:
        delta = round(((last_month_takeaway - prev_takeaway) / prev_takeaway) * 100)
    target = suggested_target(max(last_month_takeaway, 1), 1.3)
    payload = {"targets": [{"focus": "takeaway_spend", "period": "month", "amount": target}]}
    body = f"Last month: {under_budget_days} under-budget days, longest streak {longest_streak} days."
    if prev_takeaway > 0:
        body += f" Takeaway spend changed {delta}% month-over-month."
    return TimelineEvent(
        id=event_id,
        type="monthly_framing",
        occurred_at=_at_day(month_start, tz),
        title="Set your month direction",
        body=body,
        meta={"month_start": str(month_start), "suggested_targets": payload["targets"]},
        evidence=build_evidence(
            _at_day(month_start, tz),
            _at_day(month_start, tz),
            metrics={"under_budget_days": under_budget_days, "longest_streak": longest_streak, "takeaway_delta_pct": delta},
        ),
        actions=[
            TimelineAction(id="accept_targets", label="Take this direction", kind="primary", action_type="accept_targets", payload=payload),
            TimelineAction(id="open_goal_realign", label="Choose a different focus", kind="secondary", action_type="open_goal_realign", payload={}),
        ],
        priority=80,
    )


def quarterly_event(user_id: str, quarter_start: date, under_budget_days: int, longest_streak: int, quarter_takeaway: int, prev_takeaway: int, tz: ZoneInfo, event_id: str) -> TimelineEvent:
    target = suggested_target(max(quarter_takeaway, 1), 1.2)
    delta = 0
    if prev_takeaway > 0:
        delta = round(((quarter_takeaway - prev_takeaway) / prev_takeaway) * 100)
    payload = {"targets": [{"focus": "takeaway_spend", "period": "quarter", "amount": target}]}
    return TimelineEvent(
        id=event_id,
        type="quarterly_review",
        occurred_at=_at_day(quarter_start, tz),
        title="Quarterly review",
        body=f"{under_budget_days} under-budget days and a longest streak of {longest_streak} days. Takeaway trend: {delta}%.",
        meta={"quarter_start": str(quarter_start), "suggested_targets": payload["targets"]},
        evidence=build_evidence(_at_day(quarter_start, tz), _at_day(quarter_start, tz), metrics={"under_budget_days": under_budget_days, "longest_streak": longest_streak, "takeaway_delta_pct": delta}),
        actions=[
            TimelineAction(id="accept_targets", label="Take this direction", kind="primary", action_type="accept_targets", payload=payload),
            TimelineAction(id="open_goal_realign", label="Choose a different focus", kind="secondary", action_type="open_goal_realign", payload={}),
        ],
        priority=85,
    )


def yearly_events(year: int, tz: ZoneInfo, longest_streak: int, under_budget_days: int, takeaway_total: int, event_ids: list[str]) -> list[TimelineEvent]:
    when = _at_day(date(year, 1, 1), tz)
    return [
        TimelineEvent(id=event_ids[0], type="year_review", occurred_at=when, title=f"Your {year - 1} in review", body="A quick look at your progress over the last year.", meta={"card": 1}, evidence=build_evidence(when, when, metrics={"year": year - 1}), actions=[], priority=95),
        TimelineEvent(id=event_ids[1], type="year_review", occurred_at=when, title="Biggest shift", body=f"Longest streak: {longest_streak} days.", meta={"card": 2}, evidence=build_evidence(when, when, metrics={"longest_streak": longest_streak}), actions=[], priority=94),
        TimelineEvent(id=event_ids[2], type="year_review", occurred_at=when, title="Build on momentum", body=f"{under_budget_days} under-budget days and takeaway spend {takeaway_total} this year.", meta={"card": 3}, evidence=build_evidence(when, when, metrics={"under_budget_days": under_budget_days, "takeaway_total": takeaway_total}), actions=[TimelineAction(id="open_goal_realign", label="Set this year’s goals", kind="primary", action_type="open_goal_realign", payload={})], priority=93),
    ]
