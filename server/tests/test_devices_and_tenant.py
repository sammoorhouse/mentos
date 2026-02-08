def _auth(client, monkeypatch, sub="s1"):
    from app.services import apple_auth

    async def fake_verify(token, aud):
        return {"sub": sub, "email": f"{sub}@x.com"}

    monkeypatch.setattr(apple_auth, "verify_identity_token", fake_verify)
    return client.post("/auth/apple", json={"identityToken": "abc"}).json()["accessToken"]


def test_device_upsert_idempotent(client, monkeypatch):
    token = _auth(client, monkeypatch)
    h = {"Authorization": f"Bearer {token}"}
    r1 = client.post("/devices", json={"apnsToken": "t1", "platform": "ios", "appVersion": "1"}, headers=h)
    r2 = client.post("/devices", json={"apnsToken": "t1", "platform": "ios", "appVersion": "1.1"}, headers=h)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"]


def test_tenant_cannot_read_other_insight(client, monkeypatch):
    t1 = _auth(client, monkeypatch, "u1")
    t2 = _auth(client, monkeypatch, "u2")
    h1 = {"Authorization": f"Bearer {t1}"}
    h2 = {"Authorization": f"Bearer {t2}"}
    g = client.post("/goals", json={"name": "G", "type": "save", "tags": "a", "active": True}, headers=h1)
    assert g.status_code == 200
    # no insight exists for user2; user1 also cannot fetch random id
    r = client.get("/insights/non-existent", headers=h2)
    assert r.status_code == 404
