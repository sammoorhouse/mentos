import base64
import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


@dataclass
class Settings:
    db_path: str
    log_level: str
    timezone: ZoneInfo
    encryption_key: bytes | None
    pushover_app_token: str
    pushover_user_key: str
    pushover_device: str | None
    monzo_personal_token: str | None
    monzo_oauth_client_id: str | None
    monzo_oauth_client_secret: str | None
    monzo_oauth_redirect_uri: str | None
    chatgpt_api_key: str | None
    chatgpt_model: str
    chatgpt_base_url: str


def _load_encryption_key() -> bytes | None:
    key_b64 = os.getenv("MENTOS_ENCRYPTION_KEY_BASE64", "").strip()
    if not key_b64:
        return None
    key = base64.b64decode(key_b64)
    if len(key) != 32:
        raise RuntimeError("MENTOS_ENCRYPTION_KEY_BASE64 must be 32 bytes base64")
    return key


def load_settings() -> Settings:
    load_dotenv()
    tz = os.getenv("MENTOS_TIMEZONE", "Europe/London")
    return Settings(
        db_path=os.getenv("MENTOS_DB_PATH", "./mentos.sqlite"),
        log_level=os.getenv("MENTOS_LOG_LEVEL", "info"),
        timezone=ZoneInfo(tz),
        encryption_key=_load_encryption_key(),
        pushover_app_token=os.getenv("PUSHOVER_APP_TOKEN", ""),
        pushover_user_key=os.getenv("PUSHOVER_USER_KEY", ""),
        pushover_device=os.getenv("PUSHOVER_DEVICE") or None,
        monzo_personal_token=os.getenv("MONZO_PERSONAL_TOKEN") or None,
        monzo_oauth_client_id=os.getenv("MONZO_OAUTH_CLIENT_ID") or None,
        monzo_oauth_client_secret=os.getenv("MONZO_OAUTH_CLIENT_SECRET") or None,
        monzo_oauth_redirect_uri=os.getenv("MONZO_OAUTH_REDIRECT_URI") or None,
        chatgpt_api_key=os.getenv("CHATGPT_API_KEY") or None,
        chatgpt_model=os.getenv("CHATGPT_MODEL", "gpt-4o-mini"),
        chatgpt_base_url=os.getenv("CHATGPT_BASE_URL", "https://api.openai.com/v1"),
    )
