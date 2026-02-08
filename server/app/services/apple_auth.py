from datetime import datetime, timedelta, timezone

import httpx
from jose import jwt

APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"
_cached = {"keys": None, "exp": datetime.min.replace(tzinfo=timezone.utc)}


async def get_jwks() -> dict:
    now = datetime.now(timezone.utc)
    if _cached["keys"] and _cached["exp"] > now:
        return _cached["keys"]
    async with httpx.AsyncClient(timeout=10) as client:
        data = (await client.get(APPLE_JWKS_URL)).json()
    _cached["keys"] = data
    _cached["exp"] = now + timedelta(hours=24)
    return data


async def verify_identity_token(identity_token: str, audience: str) -> dict:
    jwks = await get_jwks()
    header = jwt.get_unverified_header(identity_token)
    key = next((k for k in jwks["keys"] if k["kid"] == header["kid"]), None)
    if not key:
        raise ValueError("No matching Apple JWKS key")
    claims = jwt.decode(
        identity_token,
        key,
        algorithms=["RS256"],
        audience=audience,
        issuer="https://appleid.apple.com",
    )
    return {"sub": claims["sub"], "email": claims.get("email")}
