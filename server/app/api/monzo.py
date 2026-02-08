from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.encryption import decrypt_str, encrypt_str
from app.core.security import require_user
from app.db.models import AuditEvent, MonzoConnection, OAuthState, User
from app.db.session import get_db
from app.services.monzo import build_auth_url, exchange_code_for_tokens, expires_soon, gen_pkce

router = APIRouter(prefix="/monzo", tags=["monzo"])


@router.get("/connect/start")
def connect_start(user: User = Depends(require_user), db: Session = Depends(get_db)):
    verifier, challenge = gen_pkce()
    state_id = str(uuid4())
    db.add(
        OAuthState(
            id=state_id,
            user_id=user.id,
            provider="monzo",
            pkce_verifier_encrypted=encrypt_str(verifier),
            expires_at=expires_soon(10),
        )
    )
    db.commit()
    return {"authUrl": build_auth_url(state_id, challenge), "stateId": state_id}


class CompleteIn(BaseModel):
    code: str
    stateId: str


@router.post("/connect/complete")
async def connect_complete(body: CompleteIn, user: User = Depends(require_user), db: Session = Depends(get_db)):
    state = db.get(OAuthState, body.stateId)
    now = datetime.now(timezone.utc)
    if not state or state.user_id != user.id or state.used_at or state.expires_at < now:
        raise HTTPException(status_code=400, detail="Invalid state")
    tokens = await exchange_code_for_tokens(body.code, decrypt_str(state.pkce_verifier_encrypted))
    conn = db.get(MonzoConnection, user.id) or MonzoConnection(user_id=user.id)
    conn.access_token_encrypted = encrypt_str(tokens["access_token"])
    conn.refresh_token_encrypted = encrypt_str(tokens.get("refresh_token", ""))
    conn.scopes = tokens.get("scope", "")
    conn.status = "connected"
    state.used_at = now
    db.add(conn)
    db.add(AuditEvent(user_id=user.id, type="monzo_connected", payload_json={"scopes": conn.scopes}))
    db.commit()
    return {"connected": True}


@router.get("/status")
def status(user: User = Depends(require_user), db: Session = Depends(get_db)):
    conn = db.get(MonzoConnection, user.id)
    return {"connected": bool(conn and conn.status == "connected"), "status": conn.status if conn else "disconnected", "lastSyncAt": conn.last_sync_at if conn else None, "health": "ok"}


@router.post("/disconnect")
def disconnect(user: User = Depends(require_user), db: Session = Depends(get_db)):
    conn = db.get(MonzoConnection, user.id)
    if conn:
        conn.status = "disconnected"
        conn.access_token_encrypted = None
        conn.refresh_token_encrypted = None
    db.add(AuditEvent(user_id=user.id, type="monzo_disconnected", payload_json={}))
    db.commit()
    return {"ok": True}
