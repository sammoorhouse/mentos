import logging
import time
import requests
from typing import Any, Dict, Optional

logger = logging.getLogger("mentos.monzo")


class MonzoClient:
    BASE_URL = "https://api.monzo.com"

    def __init__(self, access_token: str):
        self.access_token = access_token

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Any] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ):
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{self.BASE_URL}{path}"
        backoff = 1
        for attempt in range(5):
            resp = requests.request(
                method, url, headers=headers, params=params, json=json_body, timeout=20
            )
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", backoff))
                logger.warning("Rate limited, retrying in %s", retry_after)
                time.sleep(retry_after)
                backoff = min(backoff * 2, 30)
                continue
            if resp.status_code >= 500:
                logger.warning("Server error %s, retrying", resp.status_code)
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)
                continue
            resp.raise_for_status()
            return resp.json()
        raise RuntimeError("Monzo request failed after retries")

    def list_accounts(self):
        return self._request("GET", "/accounts")

    def list_pots(self, account_id: str):
        params = {"current_account_id": account_id}
        return self._request("GET", "/pots", params=params)

    def list_transactions(
        self, account_id: str, since: Optional[str] = None, before: Optional[str] = None
    ):
        params: list[tuple[str, Any]] = [
            ("account_id", account_id),
            ("limit", 100),
            ("expand[]", "merchant"),
        ]
        if since:
            params.append(("since", since))
        if before:
            params.append(("before", before))
        return self._request("GET", "/transactions", params=params)

    def deposit_to_pot(self, pot_id: str, account_id: str, amount: int, dedupe_id: str):
        data = {
            "source_account_id": account_id,
            "amount": amount,
            "dedupe_id": dedupe_id,
        }
        return self._request("PUT", f"/pots/{pot_id}/deposit", json_body=data)

    def withdraw_from_pot(self, pot_id: str, account_id: str, amount: int, dedupe_id: str):
        data = {
            "destination_account_id": account_id,
            "amount": amount,
            "dedupe_id": dedupe_id,
        }
        return self._request("PUT", f"/pots/{pot_id}/withdraw", json_body=data)
