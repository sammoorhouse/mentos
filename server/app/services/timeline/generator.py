import base64
import hashlib
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.db.models import Transaction, UserPreference
from app.services.timeline.breakthroughs import THRESHOLDS, breakthrough_event, ensure_breakthrough
from app.services.timeline.framing import monthly_event, quarterly_event, yearly_events
from app.services.timeline.models import TimelineEvent, TimelinePage
from app.services.timeline.rollups import build_daily_rollups, day_bounds, week_start
from app.services.timeline.streaks import NOTABLE_STREAKS, compute_alignment, compute_streak, trailing_days


def _decode_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        return int(base64.urlsafe_b64decode(cursor.encode()).decode())
    except Exception:
        return 0


def _encode_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(str(offset).encode()).decode()


def _event_id(user_id: str, kind: str, *parts: str) -> str:
    src = "|".join([user_id, kind, *parts])
    return hashlib.sha1(src.encode()).hexdigest()


def _month_start(d: date) -> date:
    return d.replace(day=1)


def _quarter_start(d: date) -> date:
    return date(d.year, ((d.month - 1) // 3) * 3 + 1, 1)


def _timezone_for_user(db: Session, user_id: str) -> ZoneInfo:
    pref = db.get(UserPreference, user_id)
    tz_name = getattr(pref, "timezone", None) or "Europe/London"
    return ZoneInfo(tz_name)


def _daily_budget(pref: UserPreference | None) -> int:
    raw = getattr(pref, "daily_budget", None)
    if raw and int(raw) > 0:
        return int(raw)
    return 3000


def generate_timeline(db: Session, user_id: str, cursor: str | None, limit: int, now_dt: datetime | None = None) -> TimelinePage:
    tz = _timezone_for_user(db, user_id)
    pref = db.get(UserPreference, user_id)
    daily_budget = _daily_budget(pref)

    now = now_dt.astimezone(tz) if now_dt else datetime.now(tz)
    today = now.date()
    lookback_start = today - timedelta(days=400)
    txns = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id, Transaction.timestamp >= datetime.combine(lookback_start, time.min, tzinfo=tz))
        .order_by(Transaction.timestamp.asc())
        .all()
    )

    rollups = build_daily_rollups(txns, tz)
    days = trailing_days(today, 120)
    takeaway_aligned, budget_aligned = compute_alignment(days, rollups, daily_budget)
    takeaway_streak = compute_streak(days, takeaway_aligned)
    budget_streak = compute_streak(days, budget_aligned)

    events: list[TimelineEvent] = []

    # weekly progress
    weeks: dict[date, list[date]] = defaultdict(list)
    for d in days:
        weeks[week_start(d)].append(d)
    for ws, ws_days in weeks.items():
        day_states = []
        for d in sorted(ws_days):
            score = int(takeaway_aligned.get(d, False)) + int(budget_aligned.get(d, False))
            day_states.append(score)
        occurred_at = datetime.combine(ws, time.min, tzinfo=tz)
        events.append(
            TimelineEvent(
                id=_event_id(user_id, "weekly_progress", str(ws)),
                type="weekly_progress",
                occurred_at=occurred_at,
                title="Weekly progress",
                body=f"Takeaway-free streak {takeaway_streak.current_length}d, under-budget streak {budget_streak.current_length}d.",
                meta={"week_start": str(ws), "days": day_states[:7]},
                evidence={
                    "transaction_ids": [t for d in ws_days for t in rollups.get(d, type("x", (), {"transaction_ids": []})()).transaction_ids],
                    "date_range": {"start": occurred_at, "end": occurred_at + timedelta(days=7)},
                    "metrics": {"takeaway_streak": takeaway_streak.current_length, "budget_streak": budget_streak.current_length},
                },
                priority=70,
            )
        )

    # streak updates and breaks
    curr_takeaway = 0
    curr_budget = 0
    for d in days:
        day_rollup = rollups.get(d)
        take_ok = takeaway_aligned[d]
        bud_ok = budget_aligned[d]
        curr_takeaway = curr_takeaway + 1 if take_ok else 0
        curr_budget = curr_budget + 1 if bud_ok else 0

        if curr_takeaway in NOTABLE_STREAKS:
            at = day_bounds(d, tz)[1]
            events.append(TimelineEvent(id=_event_id(user_id, "streak_update", "takeaway", str(d), str(curr_takeaway)), type="streak_update", occurred_at=at, title="Takeaway-free streak", body=f"{curr_takeaway} days takeaway-free.", meta={"streak_type": "takeaway_free", "length": curr_takeaway}, evidence={"transaction_ids": [], "date_range": {"start": day_bounds(d, tz)[0], "end": at}, "metrics": {"length": curr_takeaway}}, priority=75))
        if curr_budget in NOTABLE_STREAKS:
            at = day_bounds(d, tz)[1]
            events.append(TimelineEvent(id=_event_id(user_id, "streak_update", "budget", str(d), str(curr_budget)), type="streak_update", occurred_at=at, title="Under-budget streak", body=f"{curr_budget} days under budget.", meta={"streak_type": "under_daily_budget", "length": curr_budget}, evidence={"transaction_ids": day_rollup.transaction_ids if day_rollup else [], "date_range": {"start": day_bounds(d, tz)[0], "end": at}, "metrics": {"length": curr_budget, "daily_budget": daily_budget}}, priority=75))

        if not take_ok and curr_takeaway == 0 and day_rollup and day_rollup.takeaway_txn_ids:
            at = day_bounds(d, tz)[1]
            events.append(TimelineEvent(id=_event_id(user_id, "streak_broken", "takeaway", str(d)), type="streak_broken", occurred_at=at, title="Takeaway-free streak broken", body="A takeaway transaction ended your streak.", meta={"streak_type": "takeaway_free"}, evidence={"transaction_ids": day_rollup.takeaway_txn_ids, "date_range": {"start": day_bounds(d, tz)[0], "end": at}, "metrics": {"takeaway_transactions": len(day_rollup.takeaway_txn_ids)}}, priority=76))

        if curr_budget in THRESHOLDS:
            at = day_bounds(d, tz)[1]
            key = f"budget_streak_{curr_budget}_{d.isoformat()}"
            if ensure_breakthrough(db, user_id=user_id, key=key, occurred_at=at):
                events.append(breakthrough_event(_event_id(user_id, "breakthrough", key), at, curr_budget))

    # monthly and quarterly framing on boundaries
    months = sorted({_month_start(d) for d in days})
    for m in months:
        prev = (m - timedelta(days=1)).replace(day=1)
        m_days = [d for d in days if _month_start(d) == m]
        prev_days = [d for d in days if _month_start(d) == prev]
        if not m_days:
            continue
        if m.day == 1:
            under_budget_days = sum(1 for d in prev_days if budget_aligned.get(d, False))
            longest = compute_streak(prev_days, budget_aligned).longest_length if prev_days else 0
            last_takeaway = sum(len(rollups.get(d).takeaway_txn_ids) for d in prev_days if rollups.get(d))
            prev_takeaway = sum(len(rollups.get(d).takeaway_txn_ids) for d in days if _month_start(d) == (prev - timedelta(days=1)).replace(day=1) and rollups.get(d))
            events.append(monthly_event(user_id, m, under_budget_days, longest, last_takeaway, prev_takeaway, tz, _event_id(user_id, "monthly_framing", str(m))))

    quarters = sorted({_quarter_start(d) for d in days})
    for q in quarters:
        q_days = [d for d in days if _quarter_start(d) == q]
        prev_q_marker = q - timedelta(days=1)
        prev_q_days = [d for d in days if _quarter_start(d) == _quarter_start(prev_q_marker)]
        under = sum(1 for d in prev_q_days if budget_aligned.get(d, False))
        longest = compute_streak(prev_q_days, budget_aligned).longest_length if prev_q_days else 0
        q_take = sum(len(rollups.get(d).takeaway_txn_ids) for d in prev_q_days if rollups.get(d))
        pq_take = sum(len(rollups.get(d).takeaway_txn_ids) for d in q_days if rollups.get(d))
        events.append(quarterly_event(user_id, q, under, longest, q_take, pq_take, tz, _event_id(user_id, "quarterly_review", str(q))))

    # year review (3 cards)
    year_start = date(today.year, 1, 1)
    if today.month == 1:
        prev_year_days = [d for d in days if d.year == today.year - 1]
        longest = compute_streak(prev_year_days, budget_aligned).longest_length if prev_year_days else 0
        under = sum(1 for d in prev_year_days if budget_aligned.get(d, False))
        take = sum(len(rollups.get(d).takeaway_txn_ids) for d in prev_year_days if rollups.get(d))
        ids = [_event_id(user_id, "year_review", str(year_start), str(i)) for i in range(1, 4)]
        events.extend(yearly_events(today.year, tz, longest, under, take, ids))

    ordered = sorted(events, key=lambda e: (e.occurred_at, e.priority, e.id), reverse=True)
    offset = _decode_cursor(cursor)
    page = ordered[offset : offset + limit]
    next_cursor = _encode_cursor(offset + limit) if offset + limit < len(ordered) else None
    return TimelinePage(events=page, next_cursor=next_cursor)
