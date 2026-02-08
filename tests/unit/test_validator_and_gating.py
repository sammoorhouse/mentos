import json
import unittest
from pathlib import Path

from mentos.insights.context import build_spend_context
from mentos.insights.notifications import apply_notification_policy
from mentos.insights.validator import validate_llm_response


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        fixture = json.loads(Path("tests/fixtures/scenarios/delivery_creep.json").read_text())
        self.context = build_spend_context(
            transactions=fixture["monzo"]["transactions"],
            goals=fixture["goals"],
            prefs=fixture["preferences"],
            meta_now=fixture["meta"]["now"],
            timezone=fixture["meta"]["timezone"],
        )

    def test_rejects_unknown_insight_id(self):
        response = {"matches": [{"insight_id": "unknown", "message": "x", "evidence": {}}], "non_matches": []}
        result = validate_llm_response(response=response, spend_context=self.context)
        self.assertFalse(result.valid)

    def test_rejects_invalid_evidence_path(self):
        response = {
            "matches": [{"insight_id": "delivery_creep", "message": "x", "evidence": {"windows.last_7d.bad": 1}}],
            "non_matches": [],
        }
        result = validate_llm_response(response=response, spend_context=self.context)
        self.assertFalse(result.valid)

    def test_rejects_too_many_matches(self):
        match = {
            "insight_id": "delivery_creep",
            "message": "x",
            "evidence": {
                "windows.last_30d.category_totals_gbp": self.context["windows"]["last_30d"]["category_totals_gbp"],
                "windows.last_14d.category_totals_gbp": self.context["windows"]["last_14d"]["category_totals_gbp"],
            },
        }
        result = validate_llm_response(response={"matches": [match, match, match, match], "non_matches": []}, spend_context=self.context)
        self.assertFalse(result.valid)

    def test_accepts_valid_response(self):
        response = json.loads(Path("tests/fixtures/scenarios/stubs/delivery_creep.response.json").read_text())
        result = validate_llm_response(response=response, spend_context=self.context)
        self.assertTrue(result.valid)


class GatingTests(unittest.TestCase):
    def setUp(self):
        self.match = json.loads(Path("tests/fixtures/scenarios/stubs/delivery_creep.response.json").read_text())["matches"][0]
        self.prefs = {"quiet_hours": {"start": "22:00", "end": "07:00"}, "max_notifications_per_day": 1}

    def test_quiet_hours_suppression(self):
        decision = apply_notification_policy(
            matches=[self.match], prefs=self.prefs, previous_notifications=[], now_iso="2026-01-31T23:00:00+00:00", timezone="Europe/London"
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.suppressed[0]["reason"], "quiet_hours")

    def test_daily_cap_suppression(self):
        previous = [{"status": "sent", "sent_at": "2026-01-31T09:00:00+00:00", "insight_id": "other", "dedupe_key": "x"}]
        decision = apply_notification_policy(
            matches=[self.match], prefs=self.prefs, previous_notifications=previous, now_iso="2026-01-31T12:00:00+00:00", timezone="Europe/London"
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.suppressed[0]["reason"], "daily_cap")

    def test_cooldown_and_dedupe_suppression(self):
        previous = [{"status": "sent", "sent_at": "2026-01-30T12:00:00+00:00", "insight_id": "delivery_creep", "dedupe_key": "keep"}]
        decision = apply_notification_policy(
            matches=[self.match], prefs={**self.prefs, "max_notifications_per_day": 3}, previous_notifications=previous, now_iso="2026-01-31T12:00:00+00:00", timezone="Europe/London"
        )
        self.assertFalse(decision.allowed)
        self.assertIn(decision.suppressed[0]["reason"], {"cooldown_days", "dedupe"})


if __name__ == "__main__":
    unittest.main()
