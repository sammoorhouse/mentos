import json
import tempfile
import unittest
from pathlib import Path

from mentos.insights.cards import InsightCardValidationError, get_insight_cards


class CardLoaderTests(unittest.TestCase):
    def test_loads_all_cards(self):
        cards = get_insight_cards("insights/cards")
        self.assertEqual(len(cards), 11)

    def test_rejects_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path("insights/cards/daily_indulgences_add_up.json").read_text()
            Path(tmp, "a.json").write_text(src)
            Path(tmp, "b.json").write_text(src)
            with self.assertRaises(InsightCardValidationError):
                get_insight_cards(tmp)

    def test_rejects_invalid_evidence_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            card = json.loads(Path("insights/cards/daily_indulgences_add_up.json").read_text())
            card["id"] = "invalid_key_card"
            card["evidence_keys_required"] = ["windows.last_7d.not_a_key"]
            Path(tmp, "invalid.json").write_text(json.dumps(card))
            with self.assertRaises(InsightCardValidationError):
                get_insight_cards(tmp)


if __name__ == "__main__":
    unittest.main()
