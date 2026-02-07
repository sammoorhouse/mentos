import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import uuid

from .aggregates import rebuild_daily
from .notifications import PushoverClient, can_send
from .reports import nightly_report as generate_nightly_report, monthly_review as generate_monthly_review
from .storage import get_rule
from .sync import sync_all
from .sweep import run_daily_sweep

logger = logging.getLogger("mentos.jobs")


def run_idempotent(conn, job_name: str, run_key: str, func):
    try:
        conn.execute(
            "INSERT INTO job_runs (id, job_name, run_key, status, started_at) VALUES (?, ?, ?, ?, datetime('now'))",
            (str(uuid.uuid4()), job_name, run_key, "running"),
        )
        conn.commit()
    except Exception:
        logger.info("Job already ran: %s %s", job_name, run_key)
        return

    try:
        func()
        conn.execute(
            "UPDATE job_runs SET status = ?, finished_at = datetime('now') WHERE job_name = ? AND run_key = ?",
            ("ok", job_name, run_key),
        )
        conn.commit()
    except Exception as exc:
        conn.execute(
            "UPDATE job_runs SET status = ?, finished_at = datetime('now'), detail = ? WHERE job_name = ? AND run_key = ?",
            ("error", str(exc), job_name, run_key),
        )
        conn.commit()
        raise


def nightly_report(conn, tz: ZoneInfo, notifier: PushoverClient | None = None):
    def _run():
        if notifier and can_send(
            conn,
            tz,
            int(get_rule(conn, "max_notifications_per_day") or 6),
            str(get_rule(conn, "quiet_hours_start") or ""),
            str(get_rule(conn, "quiet_hours_end") or ""),
        ):
            generate_nightly_report(conn, tz, notifier)
        else:
            generate_nightly_report(conn, tz, None)
    day = (datetime.now(tz) - timedelta(days=1)).date().isoformat()
    run_idempotent(conn, "nightly_report", day, _run)


def daily_sweep(conn, tz: ZoneInfo, token: str | None):
    def _run():
        if not token:
            logger.info("Skipping sweep: missing token")
            return
        run_daily_sweep(conn, token)
    day = datetime.now(tz).date().isoformat()
    run_idempotent(conn, "daily_sweep", day, _run)


def monthly_review(conn, tz: ZoneInfo, notifier: PushoverClient | None = None):
    def _run():
        if notifier and can_send(
            conn,
            tz,
            int(get_rule(conn, "max_notifications_per_day") or 6),
            str(get_rule(conn, "quiet_hours_start") or ""),
            str(get_rule(conn, "quiet_hours_end") or ""),
        ):
            generate_monthly_review(conn, tz, notifier)
        else:
            generate_monthly_review(conn, tz, None)
    today = datetime.now(tz).date()
    run_key = f"{today.year}-{today.month:02d}"
    run_idempotent(conn, "monthly_review", run_key, _run)


def poll_and_aggregate(conn, token: str | None) -> None:
    if not token:
        logger.info("Skipping sync: missing token")
        return
    sync_all(conn, token)
    rebuild_daily(conn)
