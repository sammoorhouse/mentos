import json
from datetime import datetime

from app.db.models import Transaction, User
from app.db.session import SessionLocal
from app.services.timeline.generator import generate_timeline


def _load(name: str):
    with open(f"server/tests/fixtures/{name}", "r", encoding="utf-8") as f:
        return json.load(f)


def test_quarterly_review_targets_present():
    db = SessionLocal()
    user = User(apple_sub="a4")
    db.add(user)
    db.commit()
    for row in _load("transactions_quarterly.json"):
        db.add(Transaction(user_id=user.id, id=row["id"], amount=row["amount"], timestamp=datetime.fromisoformat(row["timestamp"]), category=row["category"]))
    db.commit()

    page = generate_timeline(db, user.id, None, 200, now_dt=datetime.fromisoformat("2025-04-02T12:00:00+00:00"))
    quarterly = [e for e in page.events if e.type == "quarterly_review"]
    assert quarterly
    assert quarterly[0].meta["suggested_targets"]

    db.close()
