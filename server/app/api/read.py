from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import require_user
from app.db.models import Breakthrough, Goal, Insight, MonzoConnection, User, UserPreference
from app.db.session import get_db

router = APIRouter(tags=["read"])


@router.get("/me")
def me(user: User = Depends(require_user), db: Session = Depends(get_db)):
    pref = db.get(UserPreference, user.id)
    monzo = db.get(MonzoConnection, user.id)
    return {"id": user.id, "email": user.email, "preferences": pref.__dict__ if pref else {}, "monzo": {"connected": bool(monzo and monzo.status == "connected"), "status": monzo.status if monzo else "disconnected"}}


@router.get("/settings")
def settings(user: User = Depends(require_user), db: Session = Depends(get_db)):
    pref = db.get(UserPreference, user.id)
    return pref.__dict__


class SettingsIn(BaseModel):
    tone: str
    quiet_hours_start: str
    quiet_hours_end: str
    max_notifications_per_day: int


@router.post("/settings")
def settings_update(body: SettingsIn, user: User = Depends(require_user), db: Session = Depends(get_db)):
    pref = db.get(UserPreference, user.id)
    pref.tone = body.tone
    pref.quiet_hours_start = body.quiet_hours_start
    pref.quiet_hours_end = body.quiet_hours_end
    pref.max_notifications_per_day = body.max_notifications_per_day
    db.commit()
    return {"ok": True}


@router.get("/goals")
def goals(user: User = Depends(require_user), db: Session = Depends(get_db)):
    return db.query(Goal).filter(Goal.user_id == user.id).all()


class GoalIn(BaseModel):
    name: str
    type: str
    tags: str = ""
    active: bool = True


@router.post("/goals")
def goals_create(body: GoalIn, user: User = Depends(require_user), db: Session = Depends(get_db)):
    g = Goal(user_id=user.id, name=body.name, type=body.type, tags=body.tags, active=1 if body.active else 0)
    db.add(g)
    db.commit()
    db.refresh(g)
    return g


@router.get("/insights")
def insights(limit: int = 50, user: User = Depends(require_user), db: Session = Depends(get_db)):
    return db.query(Insight).filter(Insight.user_id == user.id).order_by(Insight.created_at.desc()).limit(limit).all()


@router.get("/insights/{insight_id}")
def insight_detail(insight_id: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    i = db.get(Insight, insight_id)
    if not i or i.user_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    return i


@router.get("/progress/weeks")
def progress_weeks(from_: str | None = None, to: str | None = None, user: User = Depends(require_user)):
    return [{"week_start": "2025-01-06", "score": 0.5, "primaryMetricLabel": "Spend consistency", "primaryMetricValue": "Neutral"} for _ in range(6)]


@router.get("/breakthroughs")
def breakthroughs(limit: int = 20, user: User = Depends(require_user), db: Session = Depends(get_db)):
    return db.query(Breakthrough).filter(Breakthrough.user_id == user.id).order_by(Breakthrough.triggered_at.desc()).limit(limit).all()
