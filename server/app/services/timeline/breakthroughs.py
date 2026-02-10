from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import UserBreakthrough
from app.services.timeline.evidence import build_evidence
from app.services.timeline.models import TimelineAction, TimelineEvent

THRESHOLDS = {7, 14, 30}


def ensure_breakthrough(
    db: Session,
    *,
    user_id: str,
    key: str,
    occurred_at: datetime,
) -> bool:
    existing = db.query(UserBreakthrough).filter(UserBreakthrough.user_id == user_id, UserBreakthrough.breakthrough_key == key).first()
    if existing:
        return False
    db.add(UserBreakthrough(user_id=user_id, breakthrough_key=key, occurred_at=occurred_at))
    db.commit()
    return True


def breakthrough_event(event_id: str, occurred_at: datetime, streak_len: int) -> TimelineEvent:
    return TimelineEvent(
        id=event_id,
        type="breakthrough",
        occurred_at=occurred_at,
        title="Breakthrough unlocked",
        body=f"You hit a {streak_len}-day streak. Ready to raise your targets?",
        meta={"celebration_type": "fireworks", "streak_length": streak_len},
        evidence=build_evidence(occurred_at, occurred_at, metrics={"streak_length": streak_len}),
        actions=[
            TimelineAction(
                id="open_goal_realign",
                label="You’ve hit a savings breakthrough—ready to invest?",
                kind="primary",
                action_type="open_goal_realign",
                payload={},
            )
        ],
        priority=90,
    )
