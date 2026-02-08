# mentos (Python)

Local-first personal finance nudges, with a fixed Insight Card library + LLM matching.

## Insight architecture

- Insight cards are stored in `insights/cards/*.json` with stable `snake_case` IDs.
- `build_spend_context` creates deterministic rollups from Monzo-style transactions.
- The LLM performs non-deterministic matching/copywriting with strict JSON validation.
- Server-side validation rejects unknown `insight_id`s and invalid evidence paths.
- Notification gating enforces quiet hours, daily caps, per-card cooldowns, and dedupe.

## Merchant-name policy

Production logic must remain merchant-name-agnostic.

Allowed merchant-name usage:
- Monzo transaction evidence in SpendContext output.
- Test fixtures under `tests/fixtures`.
- Optional LLM-generated user copy that references context evidence.

Not allowed:
- Hard-coded merchant-name matching logic in `src/mentos`.

Enforced by unit test: `tests/unit/test_merchant_name_policy.py`.

## Add a new Insight Card

1. Add `insights/cards/<new_id>.json`.
2. Include required fields (`id`, `title`, `vibe_prompt`, `goal_tags`, `evidence_keys_required`, `cooldown`, `priority`).
3. Use only valid `evidence_keys_required` from SpendContext schema.
4. Add scenario fixture `tests/fixtures/scenarios/<new_id>.json`.
5. Add stub LLM response `tests/fixtures/scenarios/stubs/<new_id>.response.json`.
6. Ensure the card is covered by deterministic tests.

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test*.py'
```

## Optional real-LLM harness

```bash
PYTHONPATH=src OPENAI_API_KEY=... python scripts/test_llm_integration.py
```

This writes snapshots to `tests/integration_snapshots/*.json` and is not required for CI.
