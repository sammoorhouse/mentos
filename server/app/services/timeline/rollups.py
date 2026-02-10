from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.db.models import Transaction


@dataclass
class DayRollup:
    day: date
    spend_total: int = 0
    transaction_ids: list[str] = field(default_factory=list)
    takeaway_txn_ids: list[str] = field(default_factory=list)


TAKEAWAY_CATEGORIES = {"delivery", "takeaway", "food_delivery", "meal_delivery"}
TAKEAWAY_MCC = {5814}


def local_day(ts: datetime, tz: ZoneInfo) -> date:
    return ts.astimezone(tz).date()


def is_takeaway(txn: Transaction) -> bool:
    category = (txn.category or "").lower()
    if category in TAKEAWAY_CATEGORIES:
        return True
    if txn.mcc and txn.mcc in TAKEAWAY_MCC:
        return True
    return False


def spend_amount(txn: Transaction) -> int:
    if txn.amount == 0:
        return 0
    return abs(int(txn.amount))


def build_daily_rollups(transactions: list[Transaction], tz: ZoneInfo) -> dict[date, DayRollup]:
    by_day: dict[date, DayRollup] = defaultdict(lambda: DayRollup(day=date.min))
    for txn in transactions:
        day = local_day(txn.timestamp, tz)
        if by_day[day].day == date.min:
            by_day[day] = DayRollup(day=day)
        rollup = by_day[day]
        rollup.spend_total += spend_amount(txn)
        rollup.transaction_ids.append(txn.id)
        if is_takeaway(txn):
            rollup.takeaway_txn_ids.append(txn.id)
    return by_day


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def day_bounds(day: date, tz: ZoneInfo) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=tz)
    return start, start + timedelta(days=1)
