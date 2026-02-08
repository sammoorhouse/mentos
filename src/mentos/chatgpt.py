import json
import logging

import requests

logger = logging.getLogger("mentos.chatgpt")


class ChatGPTClient:
    def __init__(
        self,
        api_key: str | None,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: int = 20,
    ) -> None:
        self.api_key = (api_key or "").strip()
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate_personalized_message(
        self,
        insight_text: str,
        spending_context: dict,
    ) -> str | None:
        if not self.is_configured():
            return None

        url = f"{self.base_url}/chat/completions"
        body = {
            "model": self.model,
            "temperature": 0.4,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a practical and supportive personal finance coach. "
                        "Return exactly one concise personalized message (max 40 words), "
                        "directly referencing the spending context and ending with a question."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "insight": insight_text,
                            "recent_spending_patterns": spending_context,
                        },
                        separators=(",", ":"),
                    ),
                },
            ],
        }

        try:
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            message = (
                payload.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            return message or None
        except Exception as exc:
            logger.warning("ChatGPT generation failed: %s", exc)
            return None
