from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import Insight, MonzoConnection
from app.services.apns import send_push_to_user


def run_nightly_for_user(db: Session, user_id: str) -> Insight | None:
    conn = db.get(MonzoConnection, user_id)
    if not conn or conn.status != "connected":
        return None
    insight = Insight(
        user_id=user_id,
        insight_card_id="v0_spend_checkin",
        headline="Nightly spending check-in",
        message="You stayed within normal spend range today.",
        severity="info",
        evidence_json={"refs": ["transactions:last_24h"], "confidence": 0.6},
        created_at=datetime.now(timezone.utc),
    )
    db.add(insight)
    db.commit()
    db.refresh(insight)
    send_push_to_user(db, user_id, insight.headline, "Tap to view your latest insight", deep_link=f"mentos://insights/{insight.id}")
    return insight
