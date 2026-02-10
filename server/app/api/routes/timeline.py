from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import require_user
from app.db.models import AuditEvent, TimelineTarget, User
from app.db.session import get_db
from app.services.timeline.generator import generate_timeline
from app.services.timeline.models import TimelineEvent, TimelinePage

router = APIRouter(tags=["timeline"])


class TimelineResponse(TimelinePage):
    events: list[TimelineEvent]


@router.get(
    "/timeline",
    response_model=TimelineResponse,
    summary="Get timeline event feed",
    description="Returns a stable, deterministic, versioned timeline feed ordered newest-first.",
)
def get_timeline(
    cursor: str | None = None,
    limit: int = 50,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    safe_limit = max(1, min(limit, 100))
    return generate_timeline(db, user.id, cursor, safe_limit)


class TimelineActionIn(BaseModel):
    action_id: str
    payload: dict[str, Any] = Field(default_factory=dict)


@router.post(
    "/timeline/actions",
    summary="Submit timeline action",
    description="Processes timeline actions; target acceptance persists server-side target rows.",
)
def post_timeline_action(body: TimelineActionIn, user: User = Depends(require_user), db: Session = Depends(get_db)):
    created_targets: list[dict[str, Any]] = []
    if body.action_id == "accept_targets":
        for target in body.payload.get("targets", []):
            row = TimelineTarget(
                user_id=user.id,
                focus=str(target.get("focus", "unknown")),
                period=str(target.get("period", "month")),
                amount=int(target.get("amount", 0)),
            )
            db.add(row)
            created_targets.append({"focus": row.focus, "period": row.period, "amount": row.amount})
    db.add(
        AuditEvent(
            user_id=user.id,
            type="timeline_action",
            payload_json={"action_id": body.action_id, "payload": body.payload},
        )
    )
    db.commit()
    return {"ok": True, "created_targets": created_targets}
