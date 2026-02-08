import asyncio
from datetime import datetime, timezone
from pathlib import Path

from aioapns import APNs, NotificationRequest, PushType
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Device, Notification


def _client() -> APNs | None:
    s = get_settings()
    if not (s.apns_key_id and s.apns_team_id and (s.apns_auth_key_path or s.apns_auth_key_p8)):
        return None
    if s.apns_auth_key_path:
        key = Path(s.apns_auth_key_path).read_text()
    else:
        key = s.apns_auth_key_p8
    return APNs(
        key=key,
        key_id=s.apns_key_id,
        team_id=s.apns_team_id,
        topic=s.apns_bundle_id,
        use_sandbox=s.apns_use_sandbox,
    )


def _build_message(title: str, body: str, deep_link: str | None) -> dict:
    message = {"aps": {"alert": {"title": title, "body": body}, "sound": "default"}}
    if deep_link:
        message["deep_link"] = deep_link
    return message


async def _send_all(client: APNs, devices: list[Device], message: dict) -> bool:
    status_ok = True
    for d in devices:
        try:
            req = NotificationRequest(
                device_token=d.apns_token,
                message=message,
                push_type=PushType.ALERT,
            )
            await client.send_notification(req)
        except Exception:
            status_ok = False
    return status_ok


def send_push_to_user(db: Session, user_id: str, title: str, body: str, deep_link: str | None = None):
    devices = db.query(Device).filter(Device.user_id == user_id).all()
    note = Notification(user_id=user_id, title=title, body=body, deep_link=deep_link, status="queued")
    db.add(note)
    db.flush()
    client = _client()
    if not client:
        note.status = "failed"
        db.commit()
        return
    message = _build_message(title, body, deep_link)
    status_ok = asyncio.run(_send_all(client, devices, message))
    note.status = "sent" if status_ok else "failed"
    note.sent_at = datetime.now(timezone.utc)
    db.commit()
