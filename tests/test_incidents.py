import pytest
from pydantic import ValidationError
from src.models.incident import Incident, PostMortem
from src.services.sample_service import sample_incidents


def test_valid_incident(current):
    assert current.incident_id.startswith("INC-")
    assert current.timestamp.tzinfo is not None
    assert "v2.8.4" in current.retrieval_context()

@pytest.mark.parametrize("change", [
    {"service":"  "}, {"description":" "}, {"severity":"critical"},
    {"timestamp":"2026-01-01T12:00:00"}, {"logs":"a"*12001},
    {"outcome":"Resolved"}, {"symptoms":[""]}, {"service":"service with spaces"},
])
def test_invalid_incident(current, change):
    with pytest.raises(ValidationError):
        Incident.model_validate({**current.model_dump(), **change})


def test_sample_quality():
    records = sample_incidents()
    assert len(records) == 20
    assert len({i.incident_id for i in records}) == 20
    assert len({i.service for i in records}) == 5
    assert len({i.runbook for i in records}) >= 7
    assert {i.outcome for i in records} == {"Resolved","Mitigated","Unresolved"}
    assert all(i.failed_approaches and i.postmortem for i in records)


def test_postmortem_does_not_mutate_draft(current):
    post = PostMortem(root_cause="Connection leak", resolution_steps=["Rolled back"],
        outcome="Resolved", resolution_time=8, postmortem="Test cancellation cleanup")
    resolved = post.apply(current)
    assert resolved.incident_id == current.incident_id
    assert resolved.outcome == "Resolved"
    assert current.outcome == "Active"

@pytest.mark.parametrize("updates", [{"root_cause":" "},{"resolution_steps":[]},{"resolution_time":-1},{"postmortem":" "}])
def test_invalid_postmortem(updates):
    with pytest.raises(ValidationError):
        PostMortem(**{**dict(root_cause="Leak",resolution_steps=["Rollback"],outcome="Resolved",
            resolution_time=8,postmortem="Add regression test"), **updates})
