from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import require_user
from app.db.models import AuditEvent, Device, User
from app.db.session import get_db

router = APIRouter(prefix="/devices", tags=["devices"])


class DeviceIn(BaseModel):
    apnsToken: str
    platform: str = "ios"
    appVersion: str | None = None


@router.post("")
def upsert_device(body: DeviceIn, user: User = Depends(require_user), db: Session = Depends(get_db)):
    d = db.query(Device).filter(Device.apns_token == body.apnsToken).first()
    if not d:
        d = Device(user_id=user.id, apns_token=body.apnsToken, platform=body.platform, app_version=body.appVersion)
        db.add(d)
    else:
        d.user_id = user.id
        d.platform = body.platform
        d.app_version = body.appVersion
    d.last_seen_at = datetime.now(timezone.utc)
    db.add(AuditEvent(user_id=user.id, type="device_registered", payload_json={"device": body.apnsToken[-6:]}))
    db.commit()
    db.refresh(d)
    return {"id": d.id}


@router.delete("/{device_id}")
def delete_device(device_id: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    d = db.get(Device, device_id)
    if not d or d.user_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(d)
    db.add(AuditEvent(user_id=user.id, type="device_deleted", payload_json={"id": device_id}))
    db.commit()
    return {"ok": True}
