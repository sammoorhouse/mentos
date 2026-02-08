import json
import unittest
from pathlib import Path

from mentos.insights.llm import LLMClient
from mentos.scenario_runner import run_scenario


class ScenarioRunnerCardFlowTests(unittest.TestCase):
    def test_each_card_can_flow_with_stubbed_llm(self):
        cards = [
            "daily_indulgences_add_up",
            "premium_everyday_bias",
            "delivery_creep",
            "eating_out_frequency",
            "late_night_spend",
            "convenience_tax",
            "subscription_creep",
            "big_ticket_sanity_check",
            "payday_surge",
            "cash_idle",
            "on_plan_praise",
        ]
        for card in cards:
            with self.subTest(card=card):
                fixture = json.loads(Path(f"tests/fixtures/scenarios/{card}.json").read_text())
                llm = LLMClient(mock_response_path=f"tests/fixtures/scenarios/stubs/{card}.response.json")
                result = run_scenario(fixture, llm_client=llm)
                self.assertFalse(result["validation_errors"])
                self.assertTrue(result["notifications"])
                self.assertEqual(result["notifications"][0]["insight_id"], card)


if __name__ == "__main__":
    unittest.main()
