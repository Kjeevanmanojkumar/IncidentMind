# Verification report — 2026-09-29

## Result

**47 passed, 1 skipped** from `python -m pytest -q` under Python 3.12.
The skipped test is the real Hindsight + LLM learning-loop acceptance test.
No provider credentials or Hindsight endpoint were available to run it.

## Actually performed

| Check | Result and scope |
| --- | --- |
| Incident and post-mortem models | Valid records accepted; blank/invalid fields, missing outcomes and bad times rejected |
| Seed data | 20 unique incidents, five services, nine runbook categories, mixed outcomes and failed fixes validated |
| Hindsight boundary | Official SDK response models used in tests; retain/recall/source/history arguments checked with mocked methods |
| Storage failure | Unsuccessful/background-only acknowledgements rejected; incident remains an active draft |
| Retrieval failure | Timeout remains an error, not empty memory; client cleanup verified |
| Source integrity | Malformed source documents, invented source IDs, fabricated quotes and uncited IDs rejected |
| Reasoning boundary | JSON schema, current-only baseline, source-bearing prompts and invalid output handling tested using a mocked LLM |
| Agent orchestration | Correct baseline/recall/recommendation order, relevance selection, no-memory behavior and progress messages verified |
| Configuration | Missing credentials/endpoint, insecure remote URL, invalid bank ID and timeout rejected; error messages do not expose provider bodies |
| Streamlit pages | All six pages rendered through Streamlit AppTest without uncaught exceptions |
| Streamlit workflow | Demo load → analyze → evidence → post-mortem → future incident exercised with explicitly mocked providers |
| Failed post-mortem UI | Draft and entered root cause preserved after simulated Hindsight timeout |
| Actual server startup | Real `python -m streamlit run app.py` process started; root and health endpoints returned HTTP 200; health body was `ok` |
| Compile | `python -m compileall -q app.py src scripts tests` completed |
| Credential scan | Source tree scanned for common API-token/private-key patterns; no matches found. `.env` absent and ignored |
| Git whitespace | `git diff --cached --check` completed before commit |

The first UI test run exposed a relative test-path issue; tests now resolve the
entrypoint from the test file's absolute project root. The suite was rerun after
that correction. Local HTTP probes must run in the same sandbox invocation as the
server here because execution calls have isolated network namespaces; the automated
startup check does so and passed. No access-control changes were made.

## Not performed / open acceptance gates

- Real Hindsight connection, retained fact extraction and semantic recall.
- Real LLM diagnosis/recommendation and semantic relevance quality.
- Incident A → real retention → fresh-client Incident B recall → actual model
  citation of the new resolution. A strict opt-in test is included, but skipped.
- Full manual browser/visual walkthrough with real providers. Programmatic
  Streamlit interaction tests are not claimed as a manual browser review.
- GitHub push: the repository URL in the brief was blank, and no remote was supplied.

## Reproduce

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m compileall -q app.py src scripts tests
```

After configuring `.env`, run the genuine acceptance gate:

```bash
RUN_LIVE_TESTS=1 python -m pytest -m live -v -s
```

This test is deliberately not marked passed without real provider evidence.
