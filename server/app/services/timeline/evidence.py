from datetime import datetime

from app.services.timeline.models import DateRange, Evidence


def build_evidence(
    start: datetime,
    end: datetime,
    transaction_ids: list[str] | None = None,
    metrics: dict[str, int | float] | None = None,
) -> Evidence:
    return Evidence(
        transaction_ids=transaction_ids or [],
        date_range=DateRange(start=start, end=end),
        metrics=metrics or {},
    )
