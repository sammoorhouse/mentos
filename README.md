# mentos v0.1 (Python server + iOS scaffold)

This repo now includes:
- Existing insight-card library and validator pipeline (`src/mentos`, `insights/cards`)
- New FastAPI multi-user backend (`server/app`)
- APScheduler worker process (`python -m app.workers.run`)
- iOS SwiftUI v0.1 scaffold (`ios/mentos`)

## A) Server quickstart (local dev)

### Requirements
- Python 3.11+
- Postgres 14+
- (Optional) Redis **not required** for v0.1

### Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp server/.env.example server/.env
```

Set values in `server/.env`.

### Database
```bash
createdb mentos
# Ensure DATABASE_URL in server/.env points to your Postgres
```

### Migrations
For this tranche, schema is created on API startup via SQLAlchemy metadata. Alembic scaffolding exists in `server/alembic` and can be extended.

### Run API
```bash
PYTHONPATH=server uvicorn app.main:app --reload --port 8000
```

### Run worker
```bash
PYTHONPATH=server python -m app.workers.run
```

### Run tests
```bash
PYTHONPATH=server pytest server/tests -q
```

## B) Apple setup

1. In Apple Developer, create/update your App ID + Bundle ID.
2. Enable **Sign In with Apple**.
3. Create APNs Auth Key (`.p8`) and capture:
   - Team ID
   - Key ID
4. Configure server env:
   - `APNS_TEAM_ID`
   - `APNS_KEY_ID`
   - `APNS_AUTH_KEY_P8` (inline) **or** `APNS_AUTH_KEY_PATH`
   - `APNS_BUNDLE_ID`
   - `APNS_USE_SANDBOX=true` for dev
5. Set `APPLE_AUDIENCE` to your iOS app audience/bundle expectation.

> Push delivery requires a real iOS device.

## C) Monzo setup

1. Create a Monzo developer OAuth app.
2. Set redirect URI to `mentos://oauth/monzo` (or HTTPS callback if you proxy).
3. Configure env:
   - `MONZO_CLIENT_ID`
   - `MONZO_CLIENT_SECRET`
   - `MONZO_REDIRECT_URI`
   - `MONZO_SCOPES`
4. Test flow:
   - `GET /monzo/connect/start`
   - open returned `authUrl`
   - pass callback `code` + `state` to `POST /monzo/connect/complete`

## D) iOS setup

1. Create/open Xcode project under `ios/` (bundle must match Apple/APNs config).
2. Enable capabilities:
   - Sign In with Apple
   - Push Notifications
3. URL Types:
   - scheme: `mentos`
   - callback example: `mentos://oauth/monzo`
4. Wire networking to your dev server base URL.
5. Run on a real device.

### Verify end-to-end
1. Apple login (`POST /auth/apple`)
2. Monzo connect (start + complete)
3. APNs token registration (`POST /devices`)
4. Push smoke test (`POST /admin/test-push`)
5. Nightly simulation (`POST /admin/run-nightly-now`)

## E) Troubleshooting

- **401 refresh loop**: verify refresh token is rotated/stored and system clock is correct.
- **OAuth redirect mismatch**: ensure Monzo redirect and app URL type match exactly.
- **APNs sandbox/prod mismatch**: set `APNS_USE_SANDBOX` to match provisioning profile.
- **Device token not registering**: confirm notification permission accepted and `/devices` called with bearer token.

## Security notes (v0.1)

- Multi-user auth: Apple sign-in + server access/refresh tokens.
- Refresh token hash persisted; raw token returned once.
- Monzo tokens encrypted at rest with AES-GCM (`TOKEN_ENCRYPTION_KEY_B64`).
- CORS allowlist controlled via `CORS_ORIGINS`.
- Basic rate limiting via `slowapi` middleware.
- Audit events logged for sensitive operations.

## Existing insight architecture and policy

- Insight cards remain fixed library IDs in `insights/cards/*.json`.
- Server behavior remains merchant-name-agnostic in production matching.
- Merchant literal policy remains enforced in tests.

## Deploy to Fly.io (v0.1)

### Prerequisites
- Install Fly CLI (`flyctl`): https://fly.io/docs/hands-on/install-flyctl/
- Sign in: `fly auth login`
- Provision Postgres (`DATABASE_URL`) via Fly Postgres or Neon (Neon free tier is a good default)

### Create the Fly app
```bash
cd server
fly launch --region lhr --no-deploy
# if the name is already taken:
fly launch --name mentos-<suffix> --region lhr --no-deploy
```

### Configure required secrets
Set all runtime secrets via Fly (never commit plaintext secrets):
- `DATABASE_URL`
- `JWT_SECRET`
- `TOKEN_ENCRYPTION_KEY_B64`
- `APPLE_AUDIENCE`
- `APNS_TEAM_ID`
- `APNS_KEY_ID`
- `APNS_BUNDLE_ID`
- `APNS_AUTH_KEY_P8` (or `APNS_AUTH_KEY_PATH` strategy)
- `APNS_USE_SANDBOX`
- `MONZO_CLIENT_ID`
- `MONZO_CLIENT_SECRET` (if used)
- `MONZO_REDIRECT_URI`
- `MONZO_SCOPES`

Example:
```bash
fly secrets set \
  DATABASE_URL='postgresql://<user>:<pass>@<host>/<db>?sslmode=require' \
  JWT_SECRET='<jwt-secret>' \
  TOKEN_ENCRYPTION_KEY_B64='<base64-key>' \
  APPLE_AUDIENCE='com.example.mentos' \
  APNS_TEAM_ID='<team-id>' \
  APNS_KEY_ID='<key-id>' \
  APNS_BUNDLE_ID='com.example.mentos' \
  APNS_USE_SANDBOX='true' \
  MONZO_CLIENT_ID='<client-id>' \
  MONZO_CLIENT_SECRET='<client-secret>' \
  MONZO_REDIRECT_URI='mentos://oauth/monzo' \
  MONZO_SCOPES='accounts balance:read transactions:read'
```

For multiline APNs auth keys:
```bash
fly secrets set APNS_AUTH_KEY_P8="$(cat /path/to/AuthKey_ABC123.p8)"
```
(Alternative: mount a secret file and set `APNS_AUTH_KEY_PATH`.)

### Deploy
```bash
fly deploy
```

### Ensure both processes are running
```bash
fly scale count web=1 worker=1
```

### Verify deployment
```bash
fly status
curl https://<your-app>.fly.dev/health
fly logs --app <your-app>
```

### Migrations
Deploys run migrations automatically via Fly release command:
- `alembic -c alembic.ini upgrade head`

Manual fallback:
```bash
fly ssh console -C "cd /app && alembic -c alembic.ini upgrade head"
```

### Troubleshooting
- **Health check failing**: verify `PORT=8080`, `/health` returns `{"status":"ok"}`, and web process is healthy.
- **Worker not running**: ensure process scaling is set (`fly scale count web=1 worker=1`) and inspect `fly logs`.
- **APNs sandbox mismatch**: set `APNS_USE_SANDBOX` to match the app provisioning profile/environment.
- **Monzo redirect mismatch**: ensure `MONZO_REDIRECT_URI` exactly matches your Monzo developer app config.
