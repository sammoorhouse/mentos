from __future__ import annotations

import json
import os
from typing import Any

import requests

from .types import InsightCard


class LLMError(RuntimeError):
    pass


def build_prompt(*, spend_context: dict, cards: list[InsightCard], max_matches: int = 3) -> str:
    card_payload = [
        {
            "id": c.id,
            "title": c.title,
            "vibe_prompt": c.vibe_prompt,
            "evidence_keys_required": c.evidence_keys_required,
            "goal_tags": c.goal_tags,
            "priority": c.priority,
        }
        for c in cards
    ]
    schema = {
        "matches": [
            {
                "insight_id": "string",
                "message": "string",
                "evidence": {"spend_context.path": "value_from_context"},
            }
        ],
        "non_matches": ["string"],
    }
    return (
        "You are a financial insight selector.\n"
        f"Select at most {max_matches} insights.\n"
        "Only select cards when required evidence keys are present and directly grounded in SpendContext.\n"
        "Evidence keys in each match MUST be dot-paths that exist in SpendContext and values must come from context.\n"
        "If uncertain, list card IDs in non_matches.\n"
        f"Respect user tone in preferences.tone: {spend_context.get('preferences', {}).get('tone', 'supportive')}.\n"
        "No moralizing. Return JSON only.\n"
        f"Output schema: {json.dumps(schema)}\n"
        f"Insight cards: {json.dumps(card_payload)}\n"
        f"SpendContext: {json.dumps(spend_context)}"
    )


class LLMClient:
    def __init__(self, mock_response_path: str | None = None):
        self.mock_response_path = mock_response_path

    def complete(self, prompt: str) -> dict[str, Any]:
        if self.mock_response_path:
            with open(self.mock_response_path, "r", encoding="utf-8") as handle:
                return json.loads(handle.read())

        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        if not api_key:
            raise LLMError("OPENAI_API_KEY is required unless running in mock mode")
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
            },
            timeout=45,
        )
        response.raise_for_status()
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        return json.loads(content)
