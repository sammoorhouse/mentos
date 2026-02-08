from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .cards import get_insight_cards


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: list[str]


def _resolve_path(payload: dict[str, Any], path: str) -> Any:
    current: Any = payload
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise KeyError(path)
    return current


def validate_llm_response(*, response: dict, spend_context: dict, max_matches: int = 3, cards_dir: str = "insights/cards") -> ValidationResult:
    errors: list[str] = []
    cards = {c.id: c for c in get_insight_cards(cards_dir)}
    matches = response.get("matches")
    non_matches = response.get("non_matches")

    if not isinstance(matches, list):
        errors.append("matches must be a list")
        return ValidationResult(valid=False, errors=errors)
    if non_matches is not None and not isinstance(non_matches, list):
        errors.append("non_matches must be a list")

    if len(matches) > max_matches:
        errors.append(f"too many matches: {len(matches)} > {max_matches}")

    for idx, match in enumerate(matches):
        insight_id = match.get("insight_id")
        if insight_id not in cards:
            errors.append(f"match[{idx}] unknown insight_id: {insight_id}")
            continue
        evidence = match.get("evidence", {})
        if not isinstance(evidence, dict):
            errors.append(f"match[{idx}] evidence must be object")
            continue
        required = set(cards[insight_id].evidence_keys_required)
        present = set(evidence.keys())
        if not required.issubset(present):
            errors.append(f"match[{idx}] missing required evidence keys")
        for path, value in evidence.items():
            try:
                context_value = _resolve_path(spend_context, path)
            except KeyError:
                errors.append(f"match[{idx}] invalid evidence path: {path}")
                continue
            if context_value != value:
                errors.append(f"match[{idx}] evidence mismatch for path: {path}")

    return ValidationResult(valid=not errors, errors=errors)
