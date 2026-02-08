import json
import unittest
from pathlib import Path

from mentos.scenario_runner import generateInsightsFromFixture, runScenario

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(rel: str) -> dict:
    return json.loads((FIXTURES / rel).read_text())


def find_insight(results: dict, insight_id: str):
    return next((i for i in results["insightsFired"] if i["insight_id"] == insight_id), None)


class InsightScenarioTests(unittest.TestCase):
    def test_insight_coffee_streak_5_days_triggers(self):
        results = generateInsightsFromFixture(load_fixture("insights/insight_coffee_streak_5_days_triggers.json"))
        insight = find_insight(results, "coffee_streak")
        self.assertIsNotNone(insight)
        self.assertEqual(insight["severity"], "medium")
        self.assertEqual(insight["evidence"]["consecutive_days"], 5)
        self.assertGreaterEqual(insight["evidence"]["total_spend_last_7_days_gbp"], 20)

    def test_insight_coffee_streak_only_3_days_not_trigger(self):
        results = generateInsightsFromFixture(load_fixture("insights/insight_coffee_streak_only_3_days_not_trigger.json"))
        self.assertIsNone(find_insight(results, "coffee_streak"))

    def test_insight_dining_out_high_frequency_triggers(self):
        insight = find_insight(generateInsightsFromFixture(load_fixture("insights/insight_dining_out_high_frequency_triggers.json")), "dining_out_frequency")
        self.assertIsNotNone(insight)
        self.assertGreaterEqual(insight["evidence"]["dining_out_count_last_7_days"], 4)

    def test_insight_late_night_spend_spike_triggers(self):
        insight = find_insight(generateInsightsFromFixture(load_fixture("insights/insight_late_night_spend_spike_triggers.json")), "late_night_spend")
        self.assertIsNotNone(insight)
        self.assertGreaterEqual(insight["evidence"]["late_night_tx_count_last_7_days"], 3)

    def test_insight_subscription_creep_detects_new_recurring(self):
        insight = find_insight(generateInsightsFromFixture(load_fixture("insights/insight_subscription_creep_detects_new_recurring.json")), "subscription_creep")
        self.assertIsNotNone(insight)
        self.assertGreaterEqual(insight["evidence"]["new_recurring_count"], 1)

    def test_insight_big_ticket_purchase_triggers(self):
        insight = find_insight(generateInsightsFromFixture(load_fixture("insights/insight_big_ticket_purchase_triggers.json")), "big_ticket_purchase")
        self.assertEqual(insight["severity"], "high")
        self.assertGreaterEqual(insight["evidence"]["largest_tx_gbp"], 400)

    def test_insight_premium_everyday_merchants_triggers(self):
        insight = find_insight(generateInsightsFromFixture(load_fixture("insights/insight_premium_everyday_merchants_triggers.json")), "premium_everyday_bias")
        self.assertIsNotNone(insight)
        self.assertGreaterEqual(insight["evidence"]["premium_everyday_count_last_7_days"], 3)

    def test_insight_groceries_consistent_positive_triggers(self):
        insight = find_insight(generateInsightsFromFixture(load_fixture("insights/insight_groceries_consistent_positive_triggers.json")), "grocery_consistency_praise")
        self.assertIsNotNone(insight)
        self.assertGreaterEqual(insight["evidence"]["weeks_consistent"], 4)

    def test_insight_saving_consistency_ready_to_invest_triggers(self):
        insight = find_insight(generateInsightsFromFixture(load_fixture("insights/insight_saving_consistency_ready_to_invest_triggers.json")), "saving_consistency_invest_prompt")
        self.assertIsNotNone(insight)
        self.assertGreaterEqual(insight["evidence"]["weeks_savings_contributions"], 4)

    def test_insight_convenience_spend_high_triggers(self):
        insight = find_insight(generateInsightsFromFixture(load_fixture("insights/insight_convenience_spend_high_triggers.json")), "convenience_spend")
        self.assertIsNotNone(insight)
        self.assertTrue(insight["evidence"]["convenience_count_last_7_days"] >= 5 or insight["evidence"]["convenience_total_last_7_days_gbp"] >= 80)

    def test_insight_on_plan_reward_suggestion_triggers(self):
        insight = find_insight(generateInsightsFromFixture(load_fixture("insights/insight_on_plan_reward_suggestion_triggers.json")), "on_plan_reward")
        self.assertIsNotNone(insight)
        self.assertGreaterEqual(insight["evidence"]["green_weeks_recent"], 2)

    def test_insight_delivery_spend_high_triggers(self):
        insight = find_insight(generateInsightsFromFixture(load_fixture("insights/insight_delivery_spend_high_triggers.json")), "delivery_spend_high")
        self.assertEqual(insight["severity"], "high")

    def test_insight_delivery_spend_low_not_trigger(self):
        results = generateInsightsFromFixture(load_fixture("insights/insight_delivery_spend_low_not_trigger.json"))
        self.assertIsNone(find_insight(results, "delivery_spend_high"))


class BreakthroughAndDriftTests(unittest.TestCase):
    def test_breakthrough_delivery_reduction_25pct_3_weeks_triggers(self):
        results = runScenario(load_fixture("breakthroughs/breakthrough_delivery_reduction_25pct_3_weeks_triggers.json"))
        item = next(b for b in results["breakthroughs"] if b["breakthrough_id"] == "delivery_reduction")
        self.assertGreaterEqual(item["improvement_percent"], 25)
        self.assertEqual(item["duration_weeks"], 3)

    def test_breakthrough_end_of_month_surplus_2_months_triggers(self):
        results = runScenario(load_fixture("breakthroughs/breakthrough_end_of_month_surplus_2_months_triggers.json"))
        item = next(b for b in results["breakthroughs"] if b["breakthrough_id"] == "surplus_two_months")
        self.assertEqual(item["duration_months"], 2)
        self.assertIn("total_saved_month1", item["evidence"])

    def test_breakthrough_healthy_spending_4_of_6_green_triggers(self):
        results = runScenario(load_fixture("breakthroughs/breakthrough_healthy_spending_4_of_6_green_triggers.json"))
        item = next(b for b in results["breakthroughs"] if b["breakthrough_id"] == "healthy_spending_streak")
        self.assertGreaterEqual(item["green_weeks_last_6"], 4)

    def test_breakthrough_late_night_spend_down_30pct_4_weeks_triggers(self):
        results = runScenario(load_fixture("breakthroughs/breakthrough_late_night_spend_down_30pct_4_weeks_triggers.json"))
        item = next(b for b in results["breakthroughs"] if b["breakthrough_id"] == "late_night_reduction")
        self.assertGreaterEqual(item["improvement_percent"], 30)

    def test_drift_delivery_3_red_out_of_4_triggers_checkin(self):
        results = runScenario(load_fixture("drift/drift_delivery_3_red_out_of_4_triggers_checkin.json"))
        self.assertTrue(results["drift_events"])
        self.assertEqual(results["drift_events"][0]["drift_status"], "pending")

    def test_drift_not_triggered_when_not_sustained(self):
        results = runScenario(load_fixture("drift/drift_not_triggered_when_not_sustained.json"))
        self.assertFalse(results["drift_events"])


if __name__ == "__main__":
    unittest.main()
