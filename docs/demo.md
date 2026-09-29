# A 60-second IncidentMind story

The presentation is designed for approximately 60 seconds **after seeding and
provider readiness**. Real API calls can take longer; do not fake a successful run.

## Before presenting

1. Configure `.env`, start a real Hindsight service and choose a JSON-capable LLM.
2. Run `python -m scripts.seed` in a dedicated demo bank.
3. Run `RUN_LIVE_TESTS=1 python -m pytest -m live -v -s` and investigate failures.
4. Start `python -m streamlit run app.py` and use Check Hindsight connection.
5. Prepare the following post-mortem fields for the simulated payment outage.

| Field | Demo value |
| --- | --- |
| Actual root cause | v2.8.4 exception path left database connections unclosed |
| Resolution steps | Approved rollback of v2.8.4; controlled rolling restart; verified pool occupancy and payment success (enter one step per line) |
| Failed approaches | Increasing pool size only delayed exhaustion |
| Runbook | Database Connection Exhaustion |
| Outcome | Resolved |
| Time | 8 minutes (synthetic demo value, not a measured benchmark) |
| Post-mortem | Add exception-path and cancellation connection-release regression tests before the next release |

## Presentation scenes

| Time | Scene | Action and narration |
| --- | --- | --- |
| 0–5s | 1. Production incident | Demo → Load Demo Incident. “Payments fail after a deployment.” |
| 5–10s | 2. Hindsight search | Analyze Incident. Point to visible recall progress. |
| 10–16s | 3. Historical incidents | Expand one real recalled source. “This comes from our organization's memory.” |
| 16–21s | 4. Root cause | Read the recorded cause. Keep it separate from today's hypothesis. |
| 21–26s | 5. Successful resolution | Show past rollback/restart and the failed pool-size increase, if actually retrieved. |
| 26–32s | 6. Recommendation | Compare Without memory / With Hindsight memory. Explain the quoted source's influence. |
| 32–40s | 7. Post-mortem | Record actual outcome using the prepared synthetic resolution. |
| 40–45s | 8. Memory update | Wait for Memory Updated. No acknowledgement means no success claim. |
| 45–52s | 9. Future incident | Demo → Load similar future incident → Analyze Incident. |
| 52–60s | 10. Memory recall | Inspect the newly saved incident ID in evidence; Demo verifies recall and citation. |

Close with: “Every incident becomes knowledge for the next incident.”

If the new incident is not recalled/cited, say so. Check indexing, bank selection,
provider health and source relevance. Source inspection proving storage is not the
same as semantic recall proving learning. Never display a precomputed answer as a
live result.

## No-memory demonstration

Choose a fresh dedicated bank in `.env`, initialize it without seeding, then analyze:

```bash
python -c "from src.config import Settings; from src.memory.hindsight_memory import HindsightMemory; HindsightMemory(Settings.from_env()).initialize_bank()"
```

The app should show: “No relevant historical incidents were found. This
recommendation is based on the current incident only.” A provider error must show
an error instead. Return to the seeded bank for the memory-enhanced demonstration.
