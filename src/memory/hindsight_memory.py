"""Only persistent agent memory implementation. All history is read from Hindsight.

SDK 0.10.2 async clients are created and closed inside a single event loop per
operation, avoiding Streamlit rerun / cross-thread aiohttp session problems.
"""
import asyncio
from dataclasses import dataclass
from typing import Callable
from hindsight_client import Hindsight
from src.config import Settings
from src.errors import MemoryUnavailable, provider_message
from src.models.incident import Incident

TAG = "incidentmind-v1"


@dataclass
class Recall:
    incidents: list[Incident]
    facts: list[dict]


class HindsightMemory:
    def __init__(self, settings: Settings, client_factory: Callable = Hindsight):
        self.settings = settings
        self.client_factory = client_factory

    def _run(self, operation):
        self.settings.validate_memory()

        async def execute():
            client = self.client_factory(base_url=self.settings.hindsight_url,
                api_key=self.settings.hindsight_key or None, timeout=self.settings.timeout, max_attempts=1)
            try:
                return await operation(client)
            finally:
                await client.aclose()
        try:
            return asyncio.run(execute())
        except MemoryUnavailable:
            raise
        except Exception as exc:
            raise MemoryUnavailable(provider_message("Hindsight", exc)) from None

    def check_connection(self):
        async def op(client):
            return await client.documents.list_documents(bank_id=self.settings.bank_id, limit=1,
                _request_timeout=self.settings.timeout)
        self._run(op)

    def initialize_bank(self):
        async def op(client):
            await client.acreate_bank(bank_id=self.settings.bank_id, name="IncidentMind",
                retain_mission="Remember incident IDs, services, confirmed causes, successful and failed fixes, runbooks and post-mortem lessons. Preserve the difference between resolved, mitigated and unresolved outcomes.")
        self._run(op)

    def store_incident(self, incident: Incident):
        if incident.outcome == "Active":
            raise ValueError("Only actual recorded outcomes belong in persistent incident memory.")

        async def op(client):
            result = await client.aretain(bank_id=self.settings.bank_id,
                content=incident.model_dump_json(indent=2), timestamp=incident.timestamp,
                context="Confirmed IncidentMind incident record; synthetic demo if incident_id starts INC-SEED.",
                document_id=incident.incident_id,
                metadata={"service": incident.service, "incident_id": incident.incident_id, "outcome": incident.outcome},
                tags=[TAG, "service:" + incident.service], retain_async=False)
            if not result.success or result.var_async:
                raise MemoryUnavailable("Hindsight has not confirmed a completed memory write. Retry the same incident ID before marking it learned.")
        self._run(op)

    def store_postmortem(self, incident: Incident):
        self.store_incident(incident)

    async def _document(self, client, document_id: str) -> Incident:
        doc = await client.documents.get_document(bank_id=self.settings.bank_id,
            document_id=document_id, _request_timeout=self.settings.timeout)
        try:
            record = Incident.model_validate_json(doc.original_text or "")
        except ValueError:
            raise MemoryUnavailable("A Hindsight source document is not a valid IncidentMind record. Inspect this bank before retrying.") from None
        if record.incident_id != doc.id or record.outcome == "Active":
            raise MemoryUnavailable("A Hindsight document has inconsistent incident identity or outcome.")
        return record

    def retrieve_incident_knowledge(self, incident_id: str) -> Incident:
        return self._run(lambda client: self._document(client, incident_id))

    def retrieve_similar_incidents(self, current: Incident) -> Recall:
        async def op(client):
            recalled = await client.arecall(bank_id=self.settings.bank_id,
                query=current.retrieval_context(), types=["world", "experience"],
                budget="high", max_tokens=5000, include_chunks=True, max_chunk_tokens=6000,
                tags=[TAG], tags_match="all_strict")
            # Preserve Hindsight ranking. Hydrate only real recalled document IDs;
            # neither local samples nor local UI state are consulted.
            ids = list(dict.fromkeys(r.document_id for r in recalled.results
                if r.document_id and r.document_id != current.incident_id))[:6]
            records = [await self._document(client, doc_id) for doc_id in ids]
            facts = [r.model_dump(mode="json") for r in recalled.results if r.document_id in ids]
            return Recall(records, facts)
        return self._run(op)

    def history(self, offset: int = 0, limit: int = 20) -> tuple[list[Incident], int]:
        async def op(client):
            page = await client.documents.list_documents(bank_id=self.settings.bank_id,
                tags=[TAG], tags_match="all_strict", limit=limit, offset=offset,
                _request_timeout=self.settings.timeout)
            records = [await self._document(client, item.id) for item in page.items]
            return records, page.total
        return self._run(op)
