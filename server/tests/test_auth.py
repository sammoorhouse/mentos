import time

import jwt


def test_apple_auth_and_refresh_rotation(client, monkeypatch):
    from app.services import apple_auth

    async def fake_verify(token, aud):
        return {"sub": "apple-123", "email": "a@example.com"}

    monkeypatch.setattr(apple_auth, "verify_identity_token", fake_verify)
    r = client.post("/auth/apple", json={"identityToken": "abc"})
    assert r.status_code == 200
    data = r.json()
    r2 = client.post("/auth/refresh", json={"refreshToken": data["refreshToken"]})
    assert r2.status_code == 200
    assert r2.json()["refreshToken"] != data["refreshToken"]
    r3 = client.post("/auth/refresh", json={"refreshToken": data["refreshToken"]})
    assert r3.status_code == 401


def test_expired_access_token_rejected(client):
    token = jwt.encode({"sub": "x", "exp": int(time.time()) - 10}, "test-secret", algorithm="HS256")
    r = client.get("/auth/me-token-check", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
