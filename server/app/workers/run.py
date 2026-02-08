from apscheduler.schedulers.blocking import BlockingScheduler

from app.db.models import MonzoConnection
from app.db.session import SessionLocal
from app.services.insights import run_nightly_for_user


def monzo_poll_job():
    db = SessionLocal()
    try:
        users = db.query(MonzoConnection).filter(MonzoConnection.status == "connected").all()
        for u in users:
            u.last_sync_at = u.last_sync_at
        db.commit()
    finally:
        db.close()


def nightly_job():
    db = SessionLocal()
    try:
        users = db.query(MonzoConnection).filter(MonzoConnection.status == "connected").all()
        for conn in users:
            run_nightly_for_user(db, conn.user_id)
    finally:
        db.close()


def main():
    sched = BlockingScheduler(timezone="Europe/London")
    sched.add_job(monzo_poll_job, "interval", minutes=15)
    sched.add_job(nightly_job, "cron", hour=0, minute=10)
    sched.start()


if __name__ == "__main__":
    main()
