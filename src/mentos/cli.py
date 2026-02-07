import argparse
import logging
import os
import time
from datetime import datetime

from .config import load_settings
from .logging import setup_logging
from .db import apply_migrations, connect
from .notifications import Notification, PushoverClient
from .jobs import nightly_report, daily_sweep, monthly_review, poll_and_aggregate
from .storage import ensure_user, set_rule, get_rule, list_rules, store_monzo_token, load_monzo_token
from .sync import sync_all
from .reports import nightly_report as generate_nightly_report
from .sweep import run_daily_sweep

logger = logging.getLogger("mentos.cli")


def cmd_db_init(args) -> None:
    settings = load_settings()
    migrations_dir = os.path.join(os.path.dirname(__file__), "..", "..", "migrations")
    apply_migrations(settings.db_path, migrations_dir)
    conn = connect(settings.db_path)
    user_id = ensure_user(conn)
    if get_rule(conn, "poll_interval_minutes") is None:
        set_rule(conn, user_id, "poll_interval_minutes", int(os.getenv("MENTOS_POLL_INTERVAL_MINUTES", "5")))
    if get_rule(conn, "max_notifications_per_day") is None:
        set_rule(conn, user_id, "max_notifications_per_day", 6)
    if get_rule(conn, "quiet_hours_start") is None:
        set_rule(conn, user_id, "quiet_hours_start", "22:00")
    if get_rule(conn, "quiet_hours_end") is None:
        set_rule(conn, user_id, "quiet_hours_end", "07:00")
    if get_rule(conn, "sweep_enabled") is None:
        set_rule(conn, user_id, "sweep_enabled", False)
    logger.info("DB ready at %s", settings.db_path)


def cmd_notify_test(args) -> None:
    settings = load_settings()
    client = PushoverClient(
        settings.pushover_app_token,
        settings.pushover_user_key,
        settings.pushover_device,
    )
    client.send(Notification(title="mentos", message="Test notification from mentos"))


def cmd_config_set(args) -> None:
    settings = load_settings()
    conn = connect(settings.db_path)
    user_id = ensure_user(conn)
    try:
        import json

        value = json.loads(args.value)
    except Exception:
        value = args.value
    set_rule(conn, user_id, args.key, value)
    logger.info("Set %s", args.key)


def cmd_config_get(args) -> None:
    settings = load_settings()
    conn = connect(settings.db_path)
    value = get_rule(conn, args.key)
    print(value)


def cmd_config_list(args) -> None:
    settings = load_settings()
    conn = connect(settings.db_path)
    rules = list_rules(conn)
    for k, v in rules.items():
        print(f"{k}={v}")


def cmd_token_set(args) -> None:
    settings = load_settings()
    if not settings.encryption_key:
        raise RuntimeError("MENTOS_ENCRYPTION_KEY_BASE64 is required to store token")
    conn = connect(settings.db_path)
    user_id = ensure_user(conn)
    store_monzo_token(conn, user_id, settings.encryption_key, args.token)
    logger.info("Stored Monzo token")


def _resolve_monzo_token(settings, conn) -> str | None:
    if settings.encryption_key:
        token = load_monzo_token(conn, settings.encryption_key)
        if token:
            return token
    if settings.monzo_personal_token:
        if settings.encryption_key:
            user_id = ensure_user(conn)
            store_monzo_token(conn, user_id, settings.encryption_key, settings.monzo_personal_token)
        return settings.monzo_personal_token
    return None


def cmd_sync(args) -> None:
    settings = load_settings()
    conn = connect(settings.db_path)
    token = _resolve_monzo_token(settings, conn)
    if not token:
        raise RuntimeError("Missing Monzo token")
    sync_all(conn, token)
    logger.info("Sync complete")


def cmd_report(args) -> None:
    settings = load_settings()
    conn = connect(settings.db_path)
    notifier = (
        PushoverClient(
            settings.pushover_app_token,
            settings.pushover_user_key,
            settings.pushover_device,
        )
        if args.notify
        else None
    )
    generate_nightly_report(conn, settings.timezone, notifier)


def cmd_sweep(args) -> None:
    settings = load_settings()
    conn = connect(settings.db_path)
    token = _resolve_monzo_token(settings, conn)
    if not token:
        raise RuntimeError("Missing Monzo token")
    result = run_daily_sweep(conn, token)
    logger.info("Sweep result: %s", result)


def cmd_run(args) -> None:
    settings = load_settings()
    conn = connect(settings.db_path)
    tz = settings.timezone
    notifier = PushoverClient(
        settings.pushover_app_token,
        settings.pushover_user_key,
        settings.pushover_device,
    )
    token = _resolve_monzo_token(settings, conn)
    try:
        poll_minutes = int(get_rule(conn, "poll_interval_minutes") or 5)
    except Exception:
        poll_minutes = 5

    logger.info("mentos loop starting")
    while True:
        now = datetime.now(tz)

        if now.minute % poll_minutes == 0 and now.second < 3:
            poll_and_aggregate(conn, token)

        # Daily sweep at 00:05
        if now.hour == 0 and now.minute == 5:
            daily_sweep(conn, tz, token)

        # Nightly report at 00:10
        if now.hour == 0 and now.minute == 10:
            nightly_report(conn, tz, notifier)

        # Monthly review on 1st at 09:00
        if now.day == 1 and now.hour == 9 and now.minute == 0:
            monthly_review(conn, tz, notifier)

        time.sleep(30)


def main() -> None:
    parser = argparse.ArgumentParser(prog="mentos")
    sub = parser.add_subparsers(dest="cmd", required=True)

    db_parser = sub.add_parser("db", help="Database commands")
    db_sub = db_parser.add_subparsers(dest="db_cmd", required=True)
    db_init = db_sub.add_parser("init", help="Initialize database")
    db_init.set_defaults(func=cmd_db_init)

    notify = sub.add_parser("notify-test", help="Send test notification")
    notify.set_defaults(func=cmd_notify_test)

    config = sub.add_parser("config", help="Config rules")
    config_sub = config.add_subparsers(dest="config_cmd", required=True)
    config_set = config_sub.add_parser("set", help="Set config key")
    config_set.add_argument("key")
    config_set.add_argument("value")
    config_set.set_defaults(func=cmd_config_set)
    config_get = config_sub.add_parser("get", help="Get config key")
    config_get.add_argument("key")
    config_get.set_defaults(func=cmd_config_get)
    config_list = config_sub.add_parser("list", help="List config keys")
    config_list.set_defaults(func=cmd_config_list)

    token = sub.add_parser("token", help="Token commands")
    token_sub = token.add_subparsers(dest="token_cmd", required=True)
    token_set = token_sub.add_parser("set", help="Store Monzo personal token")
    token_set.add_argument("token")
    token_set.set_defaults(func=cmd_token_set)

    sync = sub.add_parser("sync", help="Sync Monzo data")
    sync.set_defaults(func=cmd_sync)

    run = sub.add_parser("run", help="Run loop")
    run.set_defaults(func=cmd_run)

    report = sub.add_parser("report", help="Run nightly report now")
    report.add_argument("--notify", action="store_true")
    report.set_defaults(func=cmd_report)

    sweep = sub.add_parser("sweep", help="Run daily sweep now")
    sweep.set_defaults(func=cmd_sweep)

    args = parser.parse_args()

    setup_logging(load_settings().log_level)
    args.func(args)


if __name__ == "__main__":
    main()
