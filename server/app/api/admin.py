from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import require_user
from app.db.models import User
from app.db.session import get_db
from app.services.apns import send_push_to_user
from app.services.insights import run_nightly_for_user

router = APIRouter(prefix="/admin", tags=["admin"])


def require_debug_admin(user: User = Depends(require_user)) -> User:
    s = get_settings()
    allow = set(x.strip() for x in s.admin_sub_allowlist.split(",") if x.strip())
    if not s.debug and user.apple_sub not in allow:
        raise HTTPException(status_code=403, detail="Forbidden")
    return user


class PushIn(BaseModel):
    title: str
    body: str


@router.post("/test-push")
def test_push(body: PushIn, user: User = Depends(require_debug_admin), db: Session = Depends(get_db)):
    send_push_to_user(db, user.id, body.title, body.body)
    return {"ok": True}


@router.post("/run-nightly-now")
def run_nightly_now(user: User = Depends(require_debug_admin), db: Session = Depends(get_db)):
    insight = run_nightly_for_user(db, user.id)
    return {"ran": bool(insight), "insightId": insight.id if insight else None}
