import base64
import hashlib
import secrets
import urllib.parse
from datetime import datetime, timedelta, timezone

import httpx

from app.core.config import get_settings


def gen_pkce() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    return verifier, challenge


def build_auth_url(state_id: str, challenge: str) -> str:
    s = get_settings()
    q = {
        "client_id": s.monzo_client_id,
        "redirect_uri": s.monzo_redirect_uri,
        "response_type": "code",
        "state": state_id,
        "scope": s.monzo_scopes,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    return f"{s.monzo_auth_url}?{urllib.parse.urlencode(q)}"


async def exchange_code_for_tokens(code: str, verifier: str) -> dict:
    s = get_settings()
    payload = {
        "grant_type": "authorization_code",
        "client_id": s.monzo_client_id,
        "client_secret": s.monzo_client_secret,
        "redirect_uri": s.monzo_redirect_uri,
        "code": code,
        "code_verifier": verifier,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(s.monzo_token_url, data=payload)
    resp.raise_for_status()
    return resp.json()


def expires_soon(minutes=10):
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)
