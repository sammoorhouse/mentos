import re
import unittest
from pathlib import Path


class MerchantNamePolicyTests(unittest.TestCase):
    def test_no_hardcoded_merchant_name_rules_in_production(self):
        banned = ["starbucks", "waitrose", "tesco", "deliveroo", "uber eats", "pret"]
        src_dir = Path("src/mentos")
        py_files = [p for p in src_dir.glob("**/*.py") if "tests" not in str(p)]
        violations = []
        for path in py_files:
            text = path.read_text().lower()
            for token in banned:
                if re.search(rf"\b{re.escape(token)}\b", text):
                    violations.append(f"{path}:{token}")
        self.assertFalse(violations, f"merchant-name deterministic rule violation(s): {violations}")


if __name__ == "__main__":
    unittest.main()
