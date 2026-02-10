import json
from datetime import datetime

from app.db.models import Transaction, User
from app.db.session import SessionLocal
from app.services.timeline.generator import generate_timeline


def _load(name: str):
    with open(f"server/tests/fixtures/{name}", "r", encoding="utf-8") as f:
        return json.load(f)


def test_year_review_generates_three_cards():
    db = SessionLocal()
    user = User(apple_sub="a5")
    db.add(user)
    db.commit()
    for row in _load("transactions_yearly.json"):
        db.add(Transaction(user_id=user.id, id=row["id"], amount=row["amount"], timestamp=datetime.fromisoformat(row["timestamp"]), category=row["category"]))
    db.commit()

    page = generate_timeline(db, user.id, None, 500, now_dt=datetime.fromisoformat("2025-01-05T12:00:00+00:00"))
    year = [e for e in page.events if e.type == "year_review"]
    assert len(year) == 3

    db.close()
