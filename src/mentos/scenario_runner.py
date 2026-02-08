from __future__ import annotations

from .insights.cards import get_insight_cards
from .insights.context import build_spend_context
from .insights.llm import LLMClient, build_prompt
from .insights.notifications import apply_notification_policy, serialize_notification
from .insights.validator import validate_llm_response


def run_scenario(
    fixture: dict,
    *,
    llm_client: LLMClient | None = None,
    max_matches: int = 3,
    cards_dir: str = "insights/cards",
) -> dict:
    llm = llm_client or LLMClient()
    meta = fixture["meta"]
    context = build_spend_context(
        transactions=fixture["monzo"].get("transactions", []),
        goals=fixture.get("goals", {}),
        prefs=fixture.get("preferences", {}),
        meta_now=meta["now"],
        timezone=meta["timezone"],
    )

    cards = get_insight_cards(cards_dir)
    prompt = build_prompt(spend_context=context, cards=cards, max_matches=max_matches)
    response = llm.complete(prompt)

    validation = validate_llm_response(
        response=response,
        spend_context=context,
        max_matches=max_matches,
        cards_dir=cards_dir,
    )

    if not validation.valid:
        return {
            "spend_context": context,
            "validation_errors": validation.errors,
            "notifications": [],
            "suppressed": [{"reason": "validation_failed"}],
        }

    gate = apply_notification_policy(
        matches=response["matches"],
        prefs=context["preferences"],
        previous_notifications=fixture.get("previous_notifications", []),
        now_iso=context["meta"]["now"],
        timezone=context["meta"]["timezone"],
        cards_dir=cards_dir,
    )

    notifications = [serialize_notification(m, "queued", context["meta"]["now"]) for m in gate.allowed]

    return {
        "spend_context": context,
        "validation_errors": validation.errors,
        "notifications": notifications,
        "suppressed": gate.suppressed,
        "llm_raw": response,
    }
