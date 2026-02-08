import json
import unittest
from pathlib import Path

from mentos.insights.context import build_spend_context


class SpendContextBuilderTests(unittest.TestCase):
    def test_context_rollups_are_deterministic(self):
        fixture = json.loads(Path("tests/fixtures/scenarios/eating_out_frequency.json").read_text())
        context = build_spend_context(
            transactions=fixture["monzo"]["transactions"],
            goals=fixture["goals"],
            prefs=fixture["preferences"],
            meta_now=fixture["meta"]["now"],
            timezone=fixture["meta"]["timezone"],
        )
        self.assertEqual(context["meta"]["currency"], "GBP")
        self.assertGreater(context["windows"]["last_7d"]["totals_by_category_gbp"]["eating_out"], 60)
        self.assertEqual(context["windows"]["last_7d"]["late_night_tx_count"], 0)
        self.assertTrue(context["windows"]["last_7d"]["top_merchants_by_spend"])


if __name__ == "__main__":
    unittest.main()
