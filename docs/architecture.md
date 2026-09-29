# Architecture and team handoff

## Data path

1. The Streamlit form constructs a frozen Pydantic `Incident`. Active incidents
   are session drafts, not historical memories.
2. `IncidentAgent` calls `Reasoner` with only current facts for the baseline.
3. The Hindsight adapter submits a retrieval query composed of service, symptom,
   error, deployment and log information. It requests world/experience facts with
   strict `incidentmind-v1` tag matching from the configured bank.
4. Unique returned document IDs (maximum six, preserving rank) are hydrated with
   Hindsight `documents.get_document`. Current incident ID is excluded. Invalid or
   mismatched sources fail closed instead of becoming invented history.
5. The LLM receives current facts plus complete historical records. It selects
   relevant evidence, diagnoses possible mechanisms and recommends reviewable actions.
6. Pydantic validates output. Source IDs must exist, citations must be unique and
   quotes must be literal substrings of allowed historical fields. Uncited incident
   IDs are rejected. If no candidates are judged relevant, the baseline is reused
   with an explicit no-relevant-memory notice.
7. The UI displays historical sections directly from typed source records, including
   whether actions actually resolved, merely mitigated or failed to resolve the issue.
8. `IncidentService.resolve` combines the engineer's `PostMortem` with the incident,
   validates it and calls Hindsight retain. No generated recommendation is silently
   saved as a confirmed root cause.
9. Only a successful synchronous retain acknowledgement updates session outcome and
   displays Memory Updated. On timeout, the write may have happened remotely; retry
   the same document ID. Do not infer failure means the server committed nothing.
10. A future incident traverses the same recall path using no session memory. The
    demo verifies that the recently stored incident was recalled and cited.

## Module boundaries

| Path | Responsibility |
| --- | --- |
| `app.py` | Configuration, routing, shared sidebar and styling |
| `src/models/` | Incident, post-mortem, recommendation and analysis schemas |
| `src/memory/hindsight_memory.py` | Retain, recall, source hydration, history and bank access |
| `src/agent/incident_agent.py` | Baseline → recall → memory-informed recommendation orchestration |
| `src/agent/reasoning.py` | LLM boundary, JSON parsing and evidence validation |
| `src/agent/prompts.py` | Instructions and historical grounding rules |
| `src/services/incident_service.py` | Actual outcome transaction boundary |
| `src/services/sample_service.py` | Explicit seed import and demo input only |
| `src/ui/` | Six views and reusable source/response rendering |
| `src/config.py`, `src/errors.py` | Environment validation and safe provider-facing errors |
| `data/` | Synthetic seed incidents and reference runbooks; never a fallback memory store |
| `tests/` | Unit, SDK contract, UI, startup and opt-in real learning test |

## Persistence and isolation

The configured Hindsight bank holds all completed incident documents and facts.
`document_id=incident_id` is the idempotency/update identity; the stable application
tag filters unrelated documents. Different organizations require different banks.
There is no authentication layer in this prototype, so do not expose it publicly.
The dashboard and incident history use source listing, not semantic search.

No production dictionary, file, database or browser session is read as agent memory.
Test mocks exercise boundaries and are confined to tests. Local seed files are used
only by explicit seeding. Raw source evidence is auditable in the Memory view.

## LLM and reliability boundaries

One agent orchestrates deterministic calls; there is no multi-agent system. Tool
calling is not necessary for this fixed workflow: Python invokes Hindsight explicitly
before the memory-informed LLM call. The configured chat model supports JSON output.
The OpenAI-compatible SDK is used only for text reasoning, not memory storage.

Provider errors use safe messages and suppress raw provider bodies. Authentication,
quota and timeout errors are distinct where their SDK status/type is available.
No retries are hidden in the provider clients. Operations are synchronous in the UI
with visible progress; actual per-request latency depends on the providers.

Untrusted logs and memories are delimited as JSON data under a system instruction.
This reduces prompt-injection risk but is not a formal security guarantee. Historical
sections and quotes remain source-grounded; generated causal reasoning still needs
engineer review. No shell or infrastructure execution tools exist in the app.

## Team continuation order

1. Configure Hindsight and the reasoning model in `.env`.
2. Run the opt-in live learning test; inspect the printed bank and any failure.
3. Rehearse the actual UI demo with the real providers.
4. Supply the intended GitHub repository URL and push the preserved Git history.
5. Address session-draft durability/authentication only if the team proceeds beyond
   the hackathon. Do not expand into a generic DevOps management product.
