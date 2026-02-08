#!/usr/bin/env bash
set -euo pipefail

arg1="${1:-}"
arg2="${2:-}"

BASE_URL="${BASE_URL:-}"
FLY_APP_NAME="${FLY_APP_NAME:-}"

if [[ -n "${arg1}" ]]; then
  if [[ "${arg1}" =~ ^https?:// ]]; then
    BASE_URL="${arg1%/}"
    if [[ -n "${arg2}" ]]; then
      FLY_APP_NAME="${arg2}"
    elif [[ -z "${FLY_APP_NAME}" && "${BASE_URL}" =~ ^https://([^.]+)\.fly\.dev$ ]]; then
      FLY_APP_NAME="${BASH_REMATCH[1]}"
    fi
  else
    FLY_APP_NAME="${arg1}"
  fi
fi

if [[ -z "${BASE_URL}" ]]; then
  if [[ -n "${FLY_APP_NAME}" ]]; then
    BASE_URL="https://${FLY_APP_NAME}.fly.dev"
  else
    echo "Usage: $0 [BASE_URL|FLY_APP_NAME] [FLY_APP_NAME]" >&2
    echo "Or set BASE_URL / FLY_APP_NAME env vars." >&2
    exit 1
  fi
fi

health_response="$(curl -fsS "${BASE_URL}/health")"
if [[ "${health_response}" != *"ok"* ]]; then
  echo "Error: /health response did not include 'ok': ${health_response}" >&2
  exit 1
fi

auth_status="$(curl -sS -o /dev/null -w '%{http_code}' "${BASE_URL}/me")"
if [[ "${auth_status}" != "401" ]]; then
  echo "Warning: expected /me without auth to return 401, got ${auth_status}" >&2
else
  echo "Auth middleware check passed: /me returned 401 without auth."
fi

echo "Health check passed: ${BASE_URL}/health"
if [[ -n "${FLY_APP_NAME}" ]]; then
  echo "Helpful follow-up commands:"
  echo "  fly status --app ${FLY_APP_NAME}"
  echo "  fly logs --app ${FLY_APP_NAME}"
fi
