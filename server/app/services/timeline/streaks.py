from dataclasses import dataclass
from datetime import date, timedelta

from app.services.timeline.rollups import DayRollup


NOTABLE_STREAKS = {3, 5, 7, 10, 14, 21, 30}


@dataclass
class StreakResult:
    current_length: int
    longest_length: int
    state_by_day: dict[date, bool]


def compute_streak(days: list[date], aligned_by_day: dict[date, bool]) -> StreakResult:
    longest = 0
    current = 0
    states: dict[date, bool] = {}
    for day in sorted(days):
        ok = bool(aligned_by_day.get(day, False))
        states[day] = ok
        if ok:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return StreakResult(current_length=current, longest_length=longest, state_by_day=states)


def compute_alignment(days: list[date], rollups: dict[date, DayRollup], daily_budget: int) -> tuple[dict[date, bool], dict[date, bool]]:
    takeaway_free: dict[date, bool] = {}
    under_budget: dict[date, bool] = {}
    for day in days:
        r = rollups.get(day)
        takeaway_free[day] = not (r and r.takeaway_txn_ids)
        under_budget[day] = bool(r is None or r.spend_total <= daily_budget)
    return takeaway_free, under_budget


def trailing_days(until: date, count: int) -> list[date]:
    start = until - timedelta(days=count - 1)
    return [start + timedelta(days=i) for i in range(count)]
