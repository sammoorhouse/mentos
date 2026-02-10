import json
from datetime import datetime

from app.db.models import Transaction, User
from app.db.session import SessionLocal
from app.services.timeline.generator import generate_timeline


def _load(name: str):
    with open(f"server/tests/fixtures/{name}", "r", encoding="utf-8") as f:
        return json.load(f)


def test_streak_events_and_breakthrough_persisted_once():
    db = SessionLocal()
    user = User(apple_sub="a1")
    db.add(user)
    db.commit()
    for row in _load("transactions_streaks.json"):
        db.add(Transaction(user_id=user.id, id=row["id"], amount=row["amount"], timestamp=datetime.fromisoformat(row["timestamp"]), category=row["category"]))
    db.commit()

    page = generate_timeline(db, user.id, None, 200, now_dt=datetime.fromisoformat("2025-01-20T12:00:00+00:00"))
    assert any(e.type == "streak_update" for e in page.events)
    first_count = len([e for e in page.events if e.type == "breakthrough"])
    page2 = generate_timeline(db, user.id, None, 200, now_dt=datetime.fromisoformat("2025-01-20T12:00:00+00:00"))
    second_count = len([e for e in page2.events if e.type == "breakthrough"])
    assert first_count >= 1
    assert second_count == 0

    db.close()
