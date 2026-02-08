from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, hash_token, mint_refresh_token, require_user
from app.db.models import RefreshToken, User, UserPreference
from app.db.session import get_db
from app.services.apple_auth import verify_identity_token

router = APIRouter(prefix="/auth", tags=["auth"])


class AppleIn(BaseModel):
    identityToken: str


class RefreshIn(BaseModel):
    refreshToken: str


def _make_refresh(db: Session, user_id: str) -> str:
    raw = mint_refresh_token()
    expiry = datetime.now(timezone.utc) + timedelta(days=get_settings().refresh_token_days)
    db.add(RefreshToken(user_id=user_id, token_hash=hash_token(raw), expires_at=expiry))
    db.commit()
    return raw


@router.post("/apple")
async def auth_apple(body: AppleIn, db: Session = Depends(get_db)):
    claims = await verify_identity_token(body.identityToken, get_settings().apple_audience)
    user = db.query(User).filter(User.apple_sub == claims["sub"]).first()
    if not user:
        user = User(apple_sub=claims["sub"], email=claims.get("email"))
        db.add(user)
        db.commit()
        db.refresh(user)
        db.add(UserPreference(user_id=user.id))
        db.commit()
    pref = db.get(UserPreference, user.id)
    refresh = _make_refresh(db, user.id)
    return {
        "accessToken": create_access_token(user.id),
        "refreshToken": refresh,
        "user": {"id": user.id, "email": user.email},
        "preferences": {
            "tone": pref.tone,
            "quietHoursStart": pref.quiet_hours_start,
            "quietHoursEnd": pref.quiet_hours_end,
            "maxNotificationsPerDay": pref.max_notifications_per_day,
        },
    }


@router.post("/refresh")
def refresh_token(body: RefreshIn, db: Session = Depends(get_db)):
    hashed = hash_token(body.refreshToken)
    tok = db.query(RefreshToken).filter(RefreshToken.token_hash == hashed).first()
    now = datetime.now(timezone.utc)
    if not tok or tok.revoked_at or tok.expires_at < now:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    tok.revoked_at = now
    new_refresh = _make_refresh(db, tok.user_id)
    return {"accessToken": create_access_token(tok.user_id), "refreshToken": new_refresh}


@router.get("/me-token-check")
def me_check(user: User = Depends(require_user)):
    return {"user_id": user.id}
