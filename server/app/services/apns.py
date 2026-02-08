from datetime import datetime, timezone

from apns2.client import APNsClient
from apns2.credentials import TokenCredentials
from apns2.payload import Payload
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Device, Notification


def _client() -> APNsClient | None:
    s = get_settings()
    if not (s.apns_key_id and s.apns_team_id and (s.apns_auth_key_path or s.apns_auth_key_p8)):
        return None
    if s.apns_auth_key_path:
        credentials = TokenCredentials(auth_key_path=s.apns_auth_key_path, auth_key_id=s.apns_key_id, team_id=s.apns_team_id)
    else:
        credentials = TokenCredentials(auth_key=s.apns_auth_key_p8, auth_key_id=s.apns_key_id, team_id=s.apns_team_id)
    return APNsClient(credentials=credentials, use_sandbox=s.apns_use_sandbox)


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
    status_ok = True
    payload = Payload(alert={"title": title, "body": body}, sound="default", custom={"deep_link": deep_link})
    for d in devices:
        try:
            client.send_notification(d.apns_token, payload, topic=get_settings().apns_bundle_id)
        except Exception:
            status_ok = False
    note.status = "sent" if status_ok else "failed"
    note.sent_at = datetime.now(timezone.utc)
    db.commit()
