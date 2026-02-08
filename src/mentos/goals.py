from __future__ import annotations

from dataclasses import dataclass


DEFAULT_GOAL_ID = "balanced"


@dataclass(frozen=True)
class GoalDefinition:
    id: str
    name: str
    description: str
    vibe: str


@dataclass(frozen=True)
class InsightPattern:
    id: str
    prompt: str
    tags: tuple[str, ...]
    goals: tuple[str, ...]


GOAL_DEFINITIONS: tuple[GoalDefinition, ...] = (
    GoalDefinition(
        id="saving_more",
        name="Saving more",
        description="Build stronger savings by reducing excess spend and using idle cash with purpose.",
        vibe="Frugal momentum and long-term resilience",
    ),
    GoalDefinition(
        id="healthy_living",
        name="Healthy living",
        description="Support better wellbeing through meal, routine, and timing-related spending patterns.",
        vibe="Health-first daily choices",
    ),
    GoalDefinition(
        id="mindful_spending",
        name="Mindful spending",
        description="Make purchases that feel intentional, value-driven, and aligned with personal priorities.",
        vibe="Intentional, values-based decisions",
    ),
    GoalDefinition(
        id=DEFAULT_GOAL_ID,
        name="Balanced",
        description="Keep a broad mix of practical, financial, and habit-aware nudges.",
        vibe="A flexible blend of insights",
    ),
)

INSIGHT_PATTERNS: tuple[InsightPattern, ...] = (
    InsightPattern(
        id="daily_luxuries",
        prompt=(
            "Small daily luxuries add up—would homemade alternatives help you keep more "
            "of your money this month?"
        ),
        tags=("daily_spend", "habit_shift", "cash_buffer"),
        goals=("saving_more", "mindful_spending"),
    ),
    InsightPattern(
        id="dining_frequency",
        prompt="Dining out has been frequent lately—does this still align with your monthly savings target?",
        tags=("dining", "frequency", "budget_alignment"),
        goals=("saving_more", "mindful_spending"),
    ),
    InsightPattern(
        id="late_night_impulse",
        prompt="You seem to make impulse buys late at night—do these purchases support your health goals?",
        tags=("timing", "impulse", "wellbeing"),
        goals=("healthy_living", "mindful_spending"),
    ),
    InsightPattern(
        id="subscription_check",
        prompt="Your subscriptions are growing—are all of them still giving you enough value?",
        tags=("subscriptions", "unused_services", "value_for_money"),
        goals=("saving_more", "mindful_spending"),
    ),
    InsightPattern(
        id="big_purchase_reflection",
        prompt="You made a big-ticket purchase recently—does it fit your long-term financial goals?",
        tags=("large_purchase", "future_tradeoff", "planning"),
        goals=("saving_more", "mindful_spending"),
    ),
    InsightPattern(
        id="premium_brand_switch",
        prompt="You often choose premium brands—would a few budget alternatives feel acceptable right now?",
        tags=("brand_choice", "substitution", "value"),
        goals=("saving_more", "mindful_spending"),
    ),
    InsightPattern(
        id="healthy_grocery_progress",
        prompt=(
            "You have been consistently buying healthy groceries—great job; are you ready "
            "to set a new nutrition target?"
        ),
        tags=("nutrition", "progress", "habit_consistency"),
        goals=("healthy_living",),
    ),
    InsightPattern(
        id="saving_consistency",
        prompt=(
            "Your saving pattern has been consistent—are you ready to start investing "
            "part of that momentum?"
        ),
        tags=("savings_momentum", "unused_cash", "wealth_building"),
        goals=("saving_more",),
    ),
    InsightPattern(
        id="convenience_spend",
        prompt="Convenience spending is rising—does it truly serve your priorities this month?",
        tags=("convenience", "tradeoff", "priorities"),
        goals=("mindful_spending", "saving_more"),
    ),
    InsightPattern(
        id="step_goal_reward",
        prompt="You are hitting your weekly step goal—would a planned reward help you stay consistent?",
        tags=("fitness", "reward_design", "consistency"),
        goals=("healthy_living",),
    ),
    InsightPattern(
        id="delivery_routine",
        prompt="Food delivery is frequent—would a weekly grocery routine make your meals easier and cheaper?",
        tags=("food_delivery", "meal_planning", "cost_control"),
        goals=("healthy_living", "saving_more"),
    ),
)


def goal_catalog() -> list[dict]:
    return [
        {
            "id": goal.id,
            "name": goal.name,
            "description": goal.description,
            "vibe": goal.vibe,
        }
        for goal in GOAL_DEFINITIONS
    ]


def normalize_selected_goals(selected_goals: list[str] | None) -> list[str]:
    if not selected_goals:
        return [DEFAULT_GOAL_ID]
    known_ids = {goal.id for goal in GOAL_DEFINITIONS}
    deduped = []
    for goal_id in selected_goals:
        if goal_id in known_ids and goal_id not in deduped:
            deduped.append(goal_id)
    return deduped or [DEFAULT_GOAL_ID]


def insight_patterns_for_goals(selected_goals: list[str] | None) -> list[InsightPattern]:
    resolved_goals = normalize_selected_goals(selected_goals)
    if DEFAULT_GOAL_ID in resolved_goals:
        return list(INSIGHT_PATTERNS)

    relevant = [
        pattern
        for pattern in INSIGHT_PATTERNS
        if any(goal_id in pattern.goals for goal_id in resolved_goals)
    ]
    return relevant or list(INSIGHT_PATTERNS)
