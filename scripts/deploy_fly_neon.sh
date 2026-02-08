#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${1:-${REPO_ROOT}/server/.env.deploy}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Error: env file not found at ${ENV_FILE}" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

required_vars=(
  FLY_APP_NAME
  DATABASE_URL
  JWT_SECRET
  TOKEN_ENCRYPTION_KEY_B64
)

for var_name in "${required_vars[@]}"; do
  if [[ -z "${!var_name:-}" ]]; then
    echo "Error: required variable ${var_name} is missing in ${ENV_FILE}" >&2
    exit 1
  fi
done

warn_if_missing() {
  local label="$1"
  shift
  local missing=()
  for var_name in "$@"; do
    if [[ -z "${!var_name:-}" ]]; then
      missing+=("${var_name}")
    fi
  done
  if (( ${#missing[@]} > 0 )); then
    echo "Warning: ${label} variables missing: ${missing[*]}" >&2
    echo "         ${label} features may not work until set." >&2
  fi
}

warn_if_missing "Monzo" MONZO_CLIENT_ID MONZO_CLIENT_SECRET MONZO_REDIRECT_URI MONZO_SCOPES
warn_if_missing "APNs" APNS_TEAM_ID APNS_KEY_ID APNS_BUNDLE_ID APNS_USE_SANDBOX

echo "Checking Fly authentication..."
fly auth whoami >/dev/null

fly apps list >/dev/null || true

secret_args=(
  "DATABASE_URL=${DATABASE_URL}"
  "JWT_SECRET=${JWT_SECRET}"
  "TOKEN_ENCRYPTION_KEY_B64=${TOKEN_ENCRYPTION_KEY_B64}"
)

optional_secret_vars=(
  APPLE_AUDIENCE
  MONZO_CLIENT_ID
  MONZO_CLIENT_SECRET
  MONZO_REDIRECT_URI
  MONZO_SCOPES
  APNS_TEAM_ID
  APNS_KEY_ID
  APNS_BUNDLE_ID
  APNS_USE_SANDBOX
)

for var_name in "${optional_secret_vars[@]}"; do
  if [[ -n "${!var_name:-}" ]]; then
    secret_args+=("${var_name}=${!var_name}")
  fi
done

if [[ -n "${APNS_AUTH_KEY_P8:-}" ]]; then
  secret_args+=("APNS_AUTH_KEY_P8=${APNS_AUTH_KEY_P8}")
elif [[ -n "${APNS_AUTH_KEY_P8_FILE:-}" ]]; then
  if [[ ! -f "${APNS_AUTH_KEY_P8_FILE}" ]]; then
    echo "Error: APNS_AUTH_KEY_P8_FILE is set but file not found: ${APNS_AUTH_KEY_P8_FILE}" >&2
    exit 1
  fi
  secret_args+=("APNS_AUTH_KEY_P8=$(cat "${APNS_AUTH_KEY_P8_FILE}")")
fi

echo "Setting Fly secrets for app ${FLY_APP_NAME}..."
fly secrets set --app "${FLY_APP_NAME}" "${secret_args[@]}"

echo "Ensuring web and worker process counts are set..."
fly scale count web=1 worker=1 --app "${FLY_APP_NAME}"

echo "Deploying app ${FLY_APP_NAME} using server/fly.toml..."
fly deploy --app "${FLY_APP_NAME}" --config "${REPO_ROOT}/server/fly.toml" --remote-only

BASE_URL="https://${FLY_APP_NAME}.fly.dev"
echo "Running smoke tests against ${BASE_URL}..."
"${SCRIPT_DIR}/smoke_test.sh" "${BASE_URL}" "${FLY_APP_NAME}"
