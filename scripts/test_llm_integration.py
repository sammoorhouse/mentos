"""Optional real-model harness.

Usage:
  PYTHONPATH=src OPENAI_API_KEY=... python scripts/test_llm_integration.py
"""

from __future__ import annotations

import json
from pathlib import Path

from mentos.scenario_runner import run_scenario

SCENARIOS = [
    "delivery_creep",
    "late_night_spend",
    "on_plan_praise",
]


def main() -> None:
    out_dir = Path("tests/integration_snapshots")
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = []
    for name in SCENARIOS:
        fixture = json.loads(Path(f"tests/fixtures/scenarios/{name}.json").read_text())
        result = run_scenario(fixture)
        path = out_dir / f"{name}.json"
        path.write_text(json.dumps(result, indent=2))
        summary.append((name, [n["insight_id"] for n in result.get("notifications", [])]))

    print("LLM integration summary")
    for name, matched in summary:
        print(f"- {name}: {matched}")


if __name__ == "__main__":
    main()
