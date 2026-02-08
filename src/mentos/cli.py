import argparse
import json
import logging
import os
import time
from datetime import datetime

from rich.console import Console
from rich.table import Table

from .chatgpt import ChatGPTClient
from .config import load_settings
from .db import apply_migrations, connect
from .jobs import (
    daily_sweep,
    monthly_review,
    nightly_report,
    poll_and_aggregate,
    weekly_breakthrough_review,
)
from .logging import setup_logging
from .monzo_client import MonzoClient
from .notifications import Notification, PushoverClient
from .reports import nightly_report as generate_nightly_report
from .storage import (
    ensure_user,
    get_rule,
    list_rules,
    load_monzo_token,
    set_rule,
    store_monzo_token,
)
from .sweep import run_daily_sweep
from .sync import sync_all

logger = logging.getLogger("mentos.cli")
console = Console()


def _print_table(title: str, columns: list[str], rows: list[list[str]]) -> None:
    table = Table(title=title)
    for column in columns:
        table.add_column(column)
    for row in rows:
        table.add_row(*row)
    console.print(table)


def cmd_db_init(args) -> None:
    settings = load_settings()
    migrations_dir = os.path.join(os.path.dirname(__file__), "..", "..", "migrations")
    apply_migrations(settings.db_path, migrations_dir)
    conn = connect(settings.db_path)
    user_id = ensure_user(conn)
    if get_rule(conn, "poll_interval_minutes") is None:
        set_rule(
            conn,
            user_id,
            "poll_interval_minutes",
            int(os.getenv("MENTOS_POLL_INTERVAL_MINUTES", "5")),
        )
    if get_rule(conn, "max_notifications_per_day") is None:
        set_rule(conn, user_id, "max_notifications_per_day", 6)
    if get_rule(conn, "quiet_hours_start") is None:
        set_rule(conn, user_id, "quiet_hours_start", "22:00")
    if get_rule(conn, "quiet_hours_end") is None:
        set_rule(conn, user_id, "quiet_hours_end", "07:00")
    if get_rule(conn, "sweep_enabled") is None:
        set_rule(conn, user_id, "sweep_enabled", False)
    if get_rule(conn, "exclude_categories") is None:
        set_rule(conn, user_id, "exclude_categories", ["transfers", "savings"])
    if get_rule(conn, "exclude_description_keywords") is None:
        set_rule(conn, user_id, "exclude_description_keywords", ["pot_"])
    if get_rule(conn, "insight_goals") is None:
        set_rule(conn, user_id, "insight_goals", ["balanced"])
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
    _print_table(
        "Config Value",
        ["Key", "Value"],
        [[args.key, json.dumps(value)]],
    )


def cmd_config_list(args) -> None:
    settings = load_settings()
    conn = connect(settings.db_path)
    rules = list_rules(conn)
    rows = [[k, json.dumps(v)] for k, v in sorted(rules.items())]
    _print_table("Config", ["Key", "Value"], rows)


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


def cmd_accounts(args) -> None:
    settings = load_settings()
    conn = connect(settings.db_path)
    token = _resolve_monzo_token(settings, conn)
    if not token:
        raise RuntimeError("Missing Monzo token")
    client = MonzoClient(token)
    data = client.list_accounts()
    rows = []
    for acc in data.get("accounts", []):
        rows.append(
            [
                str(acc.get("id") or ""),
                str(acc.get("description") or ""),
                str(acc.get("type") or ""),
                str(acc.get("created") or ""),
            ]
        )
    _print_table("Monzo Accounts", ["ID", "Description", "Type", "Created"], rows)


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
    chatgpt_client = ChatGPTClient(
        settings.chatgpt_api_key,
        model=settings.chatgpt_model,
        base_url=settings.chatgpt_base_url,
    )
    token = _resolve_monzo_token(settings, conn)
    try:
        poll_minutes = int(get_rule(conn, "poll_interval_minutes") or 5)
    except Exception:
        poll_minutes = 5

    logger.info("mentos loop starting")
    last_poll_key = None
    last_sweep_key = None
    last_report_key = None
    last_monthly_key = None
    last_breakthrough_key = None
    while True:
        now = datetime.now(tz)

        poll_key = now.strftime("%Y-%m-%d %H:%M")
        if now.minute % poll_minutes == 0 and last_poll_key != poll_key:
            poll_and_aggregate(conn, token)
            last_poll_key = poll_key

        # Daily sweep at 00:05
        sweep_key = f"{now.strftime('%Y-%m-%d')} 00:05"
        if now.hour == 0 and now.minute == 5 and last_sweep_key != sweep_key:
            daily_sweep(conn, tz, token)
            last_sweep_key = sweep_key

        # Nightly report at 00:10
        report_key = f"{now.strftime('%Y-%m-%d')} 00:10"
        if now.hour == 0 and now.minute == 10 and last_report_key != report_key:
            nightly_report(conn, tz, notifier)
            last_report_key = report_key

        # Weekly breakthrough review on Monday at 09:05
        breakthrough_key = f"{now.strftime('%G-W%V')} 09:05"
        if (
            now.weekday() == 0
            and now.hour == 9
            and now.minute == 5
            and last_breakthrough_key != breakthrough_key
        ):
            weekly_breakthrough_review(conn, tz, notifier, chatgpt_client=chatgpt_client)
            last_breakthrough_key = breakthrough_key

        # Monthly review on 1st at 09:00
        monthly_key = f"{now.strftime('%Y-%m')}-01 09:00"
        if now.day == 1 and now.hour == 9 and now.minute == 0 and last_monthly_key != monthly_key:
            monthly_review(conn, tz, notifier, chatgpt_client=chatgpt_client)
            last_monthly_key = monthly_key

        time.sleep(30)

def cmd_transactions(args) -> None:
    settings = load_settings()
    conn = connect(settings.db_path)
    limit = int(args.limit)
    days = int(args.days) if args.days else None
    pot_only = bool(args.pot_only)
    pot_lookup = {}
    try:
        cur_pots = conn.execute("SELECT id, name FROM pots")
        for pot_id, pot_name in cur_pots.fetchall():
            pot_lookup[pot_id] = pot_name
    except Exception:
        pass
    if days:
        cur = conn.execute(
            """
            SELECT created_at, amount, description, merchant_name, category, is_pending, account_id
            FROM transactions
            WHERE created_at >= datetime('now', ?)
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (f"-{days} day", limit),
        )
    else:
        cur = conn.execute(
            """
            SELECT created_at, amount, description, merchant_name, category, is_pending, account_id
            FROM transactions
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
    rows = cur.fetchall()
    table_rows = []
    for row in rows:
        created_at, amount, description, merchant_name, category, is_pending, account_id = row
        pot_name = ""
        is_pot = False
        if description and description in pot_lookup:
            pot_name = pot_lookup.get(description, "")
            is_pot = True
        if category in ("transfers", "savings") and description and description.startswith("pot_"):
            is_pot = True
            pot_name = pot_lookup.get(description, pot_name)
        if pot_only and not is_pot:
            continue
        table_rows.append(
            [
                str(created_at or ""),
                str(amount or 0),
                str(description or ""),
                str(merchant_name or ""),
                str(category or ""),
                str(pot_name or ""),
                str(account_id or ""),
                str(is_pending),
            ]
        )

    _print_table(
        "Transactions",
        [
            "Created At",
            "Amount",
            "Description",
            "Merchant",
            "Category",
            "Pot",
            "Account",
            "Pending",
        ],
        table_rows,
    )

def cmd_status(args) -> None:
    settings = load_settings()
    conn = connect(settings.db_path)
    cur = conn.execute(
        "SELECT last_sync_at FROM monzo_connections WHERE id = ?",
        ("monzo_default",),
    )
    row = cur.fetchone()
    last_sync = row[0] if row else None

    _print_table("Status", ["Key", "Value"], [["Last sync", str(last_sync or "never")]])

    cur = conn.execute(
        "SELECT job_name, run_key, status, started_at, finished_at "
        "FROM job_runs ORDER BY started_at DESC LIMIT 5"
    )
    jobs = cur.fetchall()
    job_rows = [
        [
            str(job[0] or ""),
            str(job[1] or ""),
            str(job[2] or ""),
            str(job[3] or ""),
            str(job[4] or ""),
        ]
        for job in jobs
    ]
    _print_table("Recent Jobs", ["Job", "Run Key", "Status", "Started", "Finished"], job_rows)

    cur = conn.execute(
        "SELECT created_at, amount, description, merchant_name, category, is_pending "
        "FROM transactions ORDER BY created_at DESC LIMIT 5"
    )
    txs = cur.fetchall()
    tx_rows = [
        [
            str(tx[0] or ""),
            str(tx[1] or 0),
            str(tx[2] or ""),
            str(tx[3] or ""),
            str(tx[4] or ""),
            str(tx[5]),
        ]
        for tx in txs
    ]
    _print_table(
        "Recent Transactions",
        ["Created At", "Amount", "Description", "Merchant", "Category", "Pending"],
        tx_rows,
    )


def cmd_pots(args) -> None:
    settings = load_settings()
    conn = connect(settings.db_path)
    cur = conn.execute("SELECT id, name, balance, currency FROM pots ORDER BY name")
    rows = cur.fetchall()
    table_rows = [
        [str(name or ""), str(pot_id or ""), str(balance or 0), str(currency or "")]
        for pot_id, name, balance, currency in rows
    ]
    _print_table("Pots", ["Name", "ID", "Balance", "Currency"], table_rows)


def cmd_breakthroughs(args) -> None:
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
    chatgpt_client = ChatGPTClient(
        settings.chatgpt_api_key,
        model=settings.chatgpt_model,
        base_url=settings.chatgpt_base_url,
    )
    weekly_breakthrough_review(conn, settings.timezone, notifier, chatgpt_client=chatgpt_client)
    logger.info("Breakthrough review complete")


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

    accounts = sub.add_parser("accounts", help="List Monzo accounts")
    accounts.set_defaults(func=cmd_accounts)

    run = sub.add_parser("run", help="Run loop")
    run.set_defaults(func=cmd_run)

    report = sub.add_parser("report", help="Run nightly report now")
    report.add_argument("--notify", action="store_true")
    report.set_defaults(func=cmd_report)

    breakthroughs = sub.add_parser("breakthroughs", help="Run weekly breakthrough detection now")
    breakthroughs.add_argument("--notify", action="store_true")
    breakthroughs.set_defaults(func=cmd_breakthroughs)

    sweep = sub.add_parser("sweep", help="Run daily sweep now")
    sweep.set_defaults(func=cmd_sweep)

    tx = sub.add_parser("transactions", help="List recent transactions")
    tx.add_argument("--limit", default="50")
    tx.add_argument("--days", default=None, help="Limit to last N days")
    tx.add_argument("--pot-only", action="store_true", help="Only show pot-related transfers")
    tx.set_defaults(func=cmd_transactions)

    status = sub.add_parser("status", help="Show last sync, recent jobs, recent transactions")
    status.set_defaults(func=cmd_status)

    pots = sub.add_parser("pots", help="List pots")
    pots.set_defaults(func=cmd_pots)

    args = parser.parse_args()

    setup_logging(load_settings().log_level)
    args.func(args)


if __name__ == "__main__":
    main()
