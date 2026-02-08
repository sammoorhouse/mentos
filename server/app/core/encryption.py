import base64
import json
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import get_settings


def _key() -> bytes:
    raw = base64.b64decode(get_settings().token_encryption_key_b64)
    if len(raw) != 32:
        raise ValueError("TOKEN_ENCRYPTION_KEY_B64 must decode to 32 bytes")
    return raw


def encrypt_str(value: str) -> str:
    nonce = os.urandom(12)
    ct = AESGCM(_key()).encrypt(nonce, value.encode(), None)
    payload = {"n": base64.b64encode(nonce).decode(), "c": base64.b64encode(ct).decode()}
    return base64.b64encode(json.dumps(payload).encode()).decode()


def decrypt_str(bundle_b64: str) -> str:
    payload = json.loads(base64.b64decode(bundle_b64).decode())
    nonce = base64.b64decode(payload["n"])
    ct = base64.b64decode(payload["c"])
    pt = AESGCM(_key()).decrypt(nonce, ct, None)
    return pt.decode()
