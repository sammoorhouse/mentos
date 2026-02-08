from __future__ import annotations

import json
from pathlib import Path

from .context import SPEND_CONTEXT_EVIDENCE_KEYS
from .types import InsightCard, InsightCooldown

MAX_VIBE_PROMPT_LENGTH = 400


class InsightCardValidationError(ValueError):
    pass


def _validate_card(raw: dict) -> InsightCard:
    required = [
        "id",
        "title",
        "vibe_prompt",
        "goal_tags",
        "evidence_keys_required",
        "cooldown",
        "priority",
    ]
    for field in required:
        if field not in raw:
            raise InsightCardValidationError(f"missing required field: {field}")

    if len(raw["vibe_prompt"]) > MAX_VIBE_PROMPT_LENGTH:
        raise InsightCardValidationError(f"vibe_prompt too long for {raw['id']}")

    for key in raw["evidence_keys_required"]:
        if key not in SPEND_CONTEXT_EVIDENCE_KEYS:
            raise InsightCardValidationError(f"invalid evidence key {key} in {raw['id']}")

    cooldown = raw["cooldown"]
    return InsightCard(
        id=str(raw["id"]),
        title=str(raw["title"]),
        vibe_prompt=str(raw["vibe_prompt"]),
        goal_tags=[str(v) for v in raw["goal_tags"]],
        evidence_keys_required=[str(v) for v in raw["evidence_keys_required"]],
        cooldown=InsightCooldown(
            min_days_between_fires=int(cooldown["min_days_between_fires"]),
            max_fires_per_30d=int(cooldown["max_fires_per_30d"]),
        ),
        priority=int(raw["priority"]),
        enabled=bool(raw.get("enabled", True)),
        examples=[str(v) for v in raw.get("examples", [])],
    )


def get_insight_cards(cards_dir: str = "insights/cards") -> list[InsightCard]:
    paths = sorted(Path(cards_dir).glob("*.json"))
    cards: list[InsightCard] = []
    ids: set[str] = set()
    for path in paths:
        raw = json.loads(path.read_text())
        card = _validate_card(raw)
        if card.id in ids:
            raise InsightCardValidationError(f"duplicate insight id: {card.id}")
        ids.add(card.id)
        if card.enabled:
            cards.append(card)
    return sorted(cards, key=lambda c: c.priority)
