from unittest.mock import MagicMock
import pytest
from src.agent.incident_agent import IncidentAgent
from src.agent.reasoning import Reasoner, validate_evidence
from src.models.recommendation import Recommendation, EvidenceUse
from src.memory.hindsight_memory import Recall
from src.errors import MemoryUnavailable, RecommendationUnavailable


def advice(past=None):
    return Recommendation(diagnosis="Suspect a client-side connection leak; verify before rollback.",
        recommended_actions=["Inspect checked-out connection ages and recent deployment."],
        why="Current symptoms warrant pool diagnostics." if past is None else "Prior connection cleanup failure suggests inspecting the new exception path.",
        evidence_used=[] if past is None else [EvidenceUse(incident_id=past.incident_id, quote=past.root_cause, influence="Prior cleanup failure informs this inspection.")])


def test_before_after_and_progress(current, past):
    memory, reasoner = MagicMock(), MagicMock()
    memory.retrieve_similar_incidents.return_value = Recall([past],[{"document_id":past.incident_id,"text":past.root_cause}])
    reasoner.recommend.side_effect = [advice(),advice(past)]
    progress=[]
    result = IncidentAgent(memory,reasoner).analyze(current,progress.append)
    assert result.historical_incidents == [past]
    assert result.enhanced.evidence_used[0].quote == past.root_cause
    assert reasoner.recommend.call_args_list[0].args == (current,[])
    assert reasoner.recommend.call_args_list[1].args == (current,[past])
    assert any("Hindsight" in step for step in progress)


def test_no_memory_is_explicit(current):
    memory, reasoner = MagicMock(), MagicMock()
    memory.retrieve_similar_incidents.return_value = Recall([],[])
    reasoner.recommend.return_value = advice()
    result=IncidentAgent(memory,reasoner).analyze(current)
    assert result.baseline == result.enhanced and not result.historical_incidents
    reasoner.recommend.assert_called_once()


def test_irrelevant_candidates_not_used(current, past):
    memory, reasoner = MagicMock(), MagicMock()
    memory.retrieve_similar_incidents.return_value = Recall([past],[])
    reasoner.recommend.return_value = advice()
    result=IncidentAgent(memory,reasoner).analyze(current)
    assert result.historical_incidents == []


def test_retrieval_error_propagates(current):
    memory,reasoner=MagicMock(),MagicMock()
    reasoner.recommend.return_value=advice()
    memory.retrieve_similar_incidents.side_effect=MemoryUnavailable("unavailable")
    with pytest.raises(MemoryUnavailable):
        IncidentAgent(memory,reasoner).analyze(current)


def test_invented_source_rejected(past):
    with pytest.raises(RecommendationUnavailable):
        validate_evidence(advice(past),[])


def test_fabricated_quote_rejected(past):
    result=advice(past)
    result.evidence_used[0].quote="Made up fix"
    with pytest.raises(RecommendationUnavailable,match="quote"):
        validate_evidence(result,[past])


def test_uncited_id_rejected():
    result=advice()
    result.why="INC-INVENTED solved this before."
    with pytest.raises(RecommendationUnavailable,match="uncited"):
        validate_evidence(result,[])


def test_llm_json_response(settings,current,past):
    client=MagicMock()
    client.__enter__.return_value=client
    client.chat.completions.create.return_value.choices[0].message.content=advice(past).model_dump_json()
    result=Reasoner(settings,lambda **_:client).recommend(current,[past])
    assert result.evidence_used[0].incident_id == past.incident_id
    args=client.chat.completions.create.call_args.kwargs
    assert args['response_format'] == {"type":"json_object"}
    assert past.postmortem in args['messages'][1]['content']


def test_invalid_llm_response(settings,current):
    client=MagicMock()
    client.__enter__.return_value=client
    client.chat.completions.create.return_value.choices[0].message.content='{"wrong":true}'
    with pytest.raises(RecommendationUnavailable,match="invalid recommendation"):
        Reasoner(settings,lambda **_:client).recommend(current,[])
