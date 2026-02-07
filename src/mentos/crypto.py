import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def encrypt(key: bytes, plaintext: bytes) -> bytes:
    nonce = os.urandom(12)
    aes = AESGCM(key)
    ciphertext = aes.encrypt(nonce, plaintext, None)
    return nonce + ciphertext


def decrypt(key: bytes, payload: bytes) -> bytes:
    if len(payload) < 13:
        raise ValueError("Invalid payload")
    nonce = payload[:12]
    ciphertext = payload[12:]
    aes = AESGCM(key)
    return aes.decrypt(nonce, ciphertext, None)
