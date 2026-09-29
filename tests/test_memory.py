from unittest.mock import MagicMock
import pytest
from hindsight_client_api.models import RecallResponse, RecallResult, DocumentResponse, ListDocumentsResponse, DocumentListItem, RetainResponse
from src.errors import MemoryUnavailable
from src.memory.hindsight_memory import HindsightMemory, TAG
from src.services.incident_service import IncidentService
from src.models.incident import PostMortem


def document(past):
    return DocumentResponse(id=past.incident_id, bank_id="incidentmind-demo", original_text=past.model_dump_json(),
        content_hash=None, created_at="2026-08-01T00:00:00Z",updated_at="2026-08-01T00:00:00Z",memory_unit_count=4)


def test_retain_official_sdk_arguments(settings, sdk, past):
    memory = HindsightMemory(settings, lambda **_: sdk)
    memory.store_incident(past)
    args = sdk.aretain.call_args.kwargs
    assert args['document_id'] == past.incident_id
    assert args['retain_async'] is False
    assert TAG in args['tags']
    assert past.root_cause in args['content'] and past.postmortem in args['content']
    sdk.aclose.assert_awaited_once()


def test_recall_hydrates_actual_source_once(settings, sdk, past, current):
    sdk.arecall.return_value = RecallResponse(results=[
        RecallResult(id="f1", text=past.root_cause, document_id=past.incident_id),
        RecallResult(id="f2", text=past.postmortem, document_id=past.incident_id),
        RecallResult(id="f3", text="No source", document_id=None),
        RecallResult(id="f4", text="Self", document_id=current.incident_id)])
    sdk.documents.get_document.return_value = document(past)
    recalled = HindsightMemory(settings, lambda **_: sdk).retrieve_similar_incidents(current)
    assert recalled.incidents == [past]
    assert len(recalled.facts) == 2
    sdk.documents.get_document.assert_awaited_once()
    args = sdk.arecall.call_args.kwargs
    assert args['tags_match'] == 'all_strict' and args['include_chunks'] is True
    assert current.error_message in args['query']


def test_empty_recall_no_fake_history(settings, sdk, current):
    sdk.arecall.return_value = RecallResponse(results=[])
    recalled = HindsightMemory(settings, lambda **_: sdk).retrieve_similar_incidents(current)
    assert recalled.incidents == []
    sdk.documents.get_document.assert_not_called()


def test_timeout_not_treated_as_empty(settings, sdk, current):
    sdk.arecall.side_effect = TimeoutError("private provider details")
    with pytest.raises(MemoryUnavailable, match="timed out") as err:
        HindsightMemory(settings, lambda **_: sdk).retrieve_similar_incidents(current)
    assert "private" not in str(err.value)
    sdk.aclose.assert_awaited_once()


def test_corrupt_source_fails_closed(settings, sdk, past):
    doc = document(past)
    doc.original_text = 'not a valid record'
    sdk.documents.get_document.return_value = doc
    with pytest.raises(MemoryUnavailable, match="not a valid"):
        HindsightMemory(settings, lambda **_: sdk).retrieve_incident_knowledge(past.incident_id)


@pytest.mark.parametrize("success,background", [(False,False),(True,True)])
def test_unconfirmed_write_does_not_resolve(settings, sdk, current, success, background):
    sdk.aretain.return_value = RetainResponse(success=success, bank_id=settings.bank_id, items_count=1, **{"async":background})
    post = PostMortem(root_cause="leak",resolution_steps=["rollback"],outcome="Resolved",resolution_time=8,postmortem="test cleanup")
    with pytest.raises(MemoryUnavailable):
        IncidentService(HindsightMemory(settings, lambda **_: sdk)).resolve(current, post)
    assert current.outcome == "Active"


def test_active_incident_not_learned(settings, sdk, current):
    with pytest.raises(ValueError, match="actual recorded outcomes"):
        HindsightMemory(settings, lambda **_: sdk).store_incident(current)
    sdk.aretain.assert_not_called()


def test_history_uses_document_pagination(settings, sdk, past):
    sdk.documents.list_documents.return_value = ListDocumentsResponse(items=[DocumentListItem(
        id=past.incident_id,bank_id=settings.bank_id,content_hash=None,created_at="2026-08-01T00:00:00Z",
        updated_at="2026-08-01T00:00:00Z",text_length=1200,memory_unit_count=5)],total=21,limit=20,offset=20)
    sdk.documents.get_document.return_value = document(past)
    records,total = HindsightMemory(settings, lambda **_: sdk).history(offset=20)
    assert total == 21 and records == [past]
    assert sdk.documents.list_documents.call_args.kwargs['offset'] == 20
