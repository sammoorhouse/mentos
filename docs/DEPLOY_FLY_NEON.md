# Deploy Mentos v0.1 on Fly.io + Neon Postgres

This runbook provides a repeatable checklist for deploying the Python server (`server/`) using Fly.io and Neon.

## 1) Create Neon database

1. Create/sign in to a Neon account: https://neon.tech
2. Create a new Postgres project.
3. From the Neon dashboard, open your database connection details and copy a connection string into `DATABASE_URL`.

### Pooled vs direct connection

- **Direct connection**: recommended default for Mentos on Fly (always-on app).
- **Pooled connection**: useful for bursty/serverless workloads.

Use direct unless you explicitly need pooled.

### SSL note

Neon requires SSL. Your `DATABASE_URL` should include SSL settings (commonly `?sslmode=require`).

## 2) Prepare deploy environment file

```bash
cp server/.env.deploy.example server/.env.deploy
```

Fill in all required values in `server/.env.deploy`.

- Required: `FLY_APP_NAME`, `DATABASE_URL`, `JWT_SECRET`, `TOKEN_ENCRYPTION_KEY_B64`
- Optional but recommended for full functionality: Monzo and APNs variables

> Never commit `server/.env.deploy`.

## 3) Generate cryptographic secrets

```bash
./scripts/gen_secrets.sh
```

Copy output values into `server/.env.deploy`.

## 4) Create Fly app (first time only)

```bash
cd server
fly launch --no-deploy --region lhr --name <your-app-name>
```

Confirm your app name matches `FLY_APP_NAME` in `server/.env.deploy`.

## 5) Deploy

Run from repo root:

```bash
./scripts/deploy_fly_neon.sh server/.env.deploy
```

What this script does:

- checks Fly auth
- validates required env vars are present
- sets Fly secrets from `server/.env.deploy`
- optionally sets `APNS_AUTH_KEY_P8` from `APNS_AUTH_KEY_P8_FILE`
- scales web/worker to `1`
- deploys using `server/fly.toml`
- runs smoke tests

## 6) Smoke test manually

```bash
./scripts/smoke_test.sh <your-app-name>
```

or:

```bash
./scripts/smoke_test.sh https://<your-app-name>.fly.dev
```

Checks:
- `/health` returns 200 and includes `ok`
- `/me` returns 401 without auth (warning-only if different)

## 7) Migrations / release command verification

Deploys run migrations automatically via Fly `release_command` in `server/fly.toml`.

To verify:

```bash
fly logs --app <your-app-name>
```

Look for successful release command output.

Manual fallback:

```bash
fly ssh console -C "cd /app && alembic -c alembic.ini upgrade head" --app <your-app-name>
```
