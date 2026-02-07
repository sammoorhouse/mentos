import json
import logging
import requests
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .storage import log_notification

logger = logging.getLogger("mentos.notifications")


@dataclass
class Notification:
    title: str
    message: str
    url: Optional[str] = None


class PushoverClient:
    def __init__(self, app_token: str, user_key: str, device: Optional[str] = None):
        self.app_token = app_token
        self.user_key = user_key
        self.device = device

    def send(self, notification: Notification, conn=None, user_id: str = "user_1") -> None:
        if not self.app_token or not self.user_key:
            raise RuntimeError("Pushover is not configured")

        payload = {
            "token": self.app_token,
            "user": self.user_key,
            "title": notification.title,
            "message": notification.message,
        }
        if self.device:
            payload["device"] = self.device
        if notification.url:
            payload["url"] = notification.url

        resp = requests.post("https://api.pushover.net/1/messages.json", data=payload, timeout=15)
        if resp.status_code >= 400:
            logger.error("Pushover error: %s", resp.text)
            resp.raise_for_status()

        logger.info("Pushover sent: %s", json.dumps({"title": notification.title}))
        if conn is not None:
            log_notification(conn, user_id, "pushover", payload, "sent")


def can_send(conn, tz, max_per_day: int, quiet_start: str, quiet_end: str) -> bool:
    now = datetime.now(tz)
    if quiet_start and quiet_end:
        try:
            qs_h, qs_m = [int(x) for x in quiet_start.split(":")]
            qe_h, qe_m = [int(x) for x in quiet_end.split(":")]
            quiet_start_min = qs_h * 60 + qs_m
            quiet_end_min = qe_h * 60 + qe_m
            now_min = now.hour * 60 + now.minute
            if quiet_start_min < quiet_end_min:
                if quiet_start_min <= now_min < quiet_end_min:
                    return False
            else:
                if now_min >= quiet_start_min or now_min < quiet_end_min:
                    return False
        except Exception:
            pass

    cur = conn.execute(
        "SELECT COUNT(1) FROM notifications WHERE date(created_at) = date('now')"
    )
    count = cur.fetchone()[0] or 0
    if max_per_day > 0 and count >= max_per_day:
        return False
    return True
