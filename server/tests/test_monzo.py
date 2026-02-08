from app.core.encryption import decrypt_str
from app.db.models import MonzoConnection, OAuthState
from app.db.session import SessionLocal


def _auth(client, monkeypatch, sub="s1"):
    from app.services import apple_auth

    async def fake_verify(token, aud):
        return {"sub": sub, "email": "a@x.com"}

    monkeypatch.setattr(apple_auth, "verify_identity_token", fake_verify)
    return client.post("/auth/apple", json={"identityToken": "abc"}).json()["accessToken"]


def test_state_one_time_and_encrypted_storage(client, monkeypatch):
    from app.services import monzo

    async def fake_exchange(code, verifier):
        return {"access_token": "plain-access", "refresh_token": "plain-refresh", "scope": "accounts"}

    monkeypatch.setattr(monzo, "exchange_code_for_tokens", fake_exchange)
    token = _auth(client, monkeypatch)
    h = {"Authorization": f"Bearer {token}"}
    start = client.get("/monzo/connect/start", headers=h).json()
    c = client.post("/monzo/connect/complete", json={"code": "x", "stateId": start["stateId"]}, headers=h)
    assert c.status_code == 200
    c2 = client.post("/monzo/connect/complete", json={"code": "x", "stateId": start["stateId"]}, headers=h)
    assert c2.status_code == 400
    db = SessionLocal()
    conn = db.query(MonzoConnection).first()
    assert "plain-access" not in conn.access_token_encrypted
    assert decrypt_str(conn.access_token_encrypted) == "plain-access"
    db.close()


def test_tenant_cannot_use_other_state(client, monkeypatch):
    t1 = _auth(client, monkeypatch, "u1")
    t2 = _auth(client, monkeypatch, "u2")
    h1 = {"Authorization": f"Bearer {t1}"}
    h2 = {"Authorization": f"Bearer {t2}"}
    start = client.get("/monzo/connect/start", headers=h1).json()
    r = client.post("/monzo/connect/complete", json={"code": "x", "stateId": start["stateId"]}, headers=h2)
    assert r.status_code == 400
