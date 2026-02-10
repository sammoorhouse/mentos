import json
from datetime import datetime

from app.db.models import Transaction, User
from app.db.session import SessionLocal
from app.services.timeline.generator import generate_timeline


def _load(name: str):
    with open(f"server/tests/fixtures/{name}", "r", encoding="utf-8") as f:
        return json.load(f)


def test_weekly_progress_days_array():
    db = SessionLocal()
    user = User(apple_sub="a2")
    db.add(user)
    db.commit()
    for row in _load("transactions_weekly.json"):
        db.add(Transaction(user_id=user.id, id=row["id"], amount=row["amount"], timestamp=datetime.fromisoformat(row["timestamp"]), category=row["category"]))
    db.commit()

    page = generate_timeline(db, user.id, None, 200, now_dt=datetime.fromisoformat("2025-01-12T12:00:00+00:00"))
    weekly = [e for e in page.events if e.type == "weekly_progress"]
    assert weekly
    assert set(weekly[0].meta["days"]).issubset((0, 1, 2))

    db.close()
