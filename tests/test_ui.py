"""Streamlit interaction tests. Patched providers are not a live memory test."""
from unittest.mock import patch
from pathlib import Path
from streamlit.testing.v1 import AppTest
from src.models.recommendation import Analysis
from src.services.sample_service import demo_incident
from src.errors import MemoryUnavailable
from tests.test_agent import advice

APP = Path(__file__).resolve().parents[1] / 'app.py'


def button(at, label):
    return next(b for b in at.button if b.label == label)

def field(elements, label):
    return next(e for e in elements if e.label == label)


def test_all_pages_render_without_keys(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("HINDSIGHT_BASE_URL", "")
    at=AppTest.from_file(APP).run()
    for page in ['Dashboard','New Incident','Incidents','Memory','Post-Mortem','Demo']:
        at.radio[0].set_value(page).run()
        assert not at.exception, page


def test_demo_load_validation_and_missing_configuration(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "")
    at=AppTest.from_file(APP).run()
    at.radio[0].set_value('New Incident').run()
    button(at,'Analyze Incident').click().run()
    assert any('Enter a service' in e.value for e in at.error)
    at.radio[0].set_value('Demo').run()
    button(at,'Load Demo Incident').click().run()
    assert at.title[0].value == 'New incident'
    assert field(at.text_input,'Service').value == 'payment-api'
    button(at,'Analyze Incident').click().run()
    assert not at.exception
    assert any('LLM_API_KEY' in e.value for e in at.error)
    assert len(at.session_state['drafts']) == 1


def test_full_ui_flow_with_explicitly_mocked_providers(past):
    def analyze(self, i, progress):
        progress('Searching Hindsight memory…')
        return Analysis(incident=i,baseline=advice(),enhanced=advice(past),historical_incidents=[past],retrieved_facts=[])
    with patch('src.agent.incident_agent.IncidentAgent.analyze', analyze), \
         patch('src.memory.hindsight_memory.HindsightMemory.store_postmortem') as retain:
        at=AppTest.from_file(APP).run()
        at.radio[0].set_value('Demo').run()
        button(at,'Load Demo Incident').click().run()
        button(at,'Analyze Incident').click().run()
        assert not at.exception
        assert any('1 relevant historical' in e.value for e in at.success)
        button(at,'Record actual outcome →').click().run()
        field(at.text_area,'Actual root cause').set_value('Connection leak in exception path')
        field(at.text_area,'Resolution steps / actions attempted · one per line').set_value('Approved rollback\nRolling restart\nVerified payment recovery')
        field(at.text_area,'Post-mortem notes / prevention learning').set_value('Add exception-path connection cleanup test')
        field(at.text_input,'Runbook used · optional').set_value('Database Connection Exhaustion')
        button(at,'Save outcome to Hindsight').click().run()
        assert not at.exception
        retain.assert_called_once()
        learned=at.session_state['last_learned']
        assert learned.outcome == 'Resolved'
        at.radio[0].set_value('Demo').run()
        button(at,'Load similar future incident').click().run()
        assert field(at.text_input,'Service').value == learned.service
        assert at.session_state['expected_memory_id'] == learned.incident_id
        assert field(at.text_area,'Incident description').value == learned.description


def test_failed_save_preserves_draft_and_form():
    incident=demo_incident()
    at=AppTest.from_file(APP)
    at.session_state['drafts']={incident.incident_id:incident}
    at.session_state['nav']='Post-Mortem'
    at.run()
    field(at.text_area,'Actual root cause').set_value('Connection leak')
    field(at.text_area,'Resolution steps / actions attempted · one per line').set_value('Rollback')
    field(at.text_area,'Post-mortem notes / prevention learning').set_value('Add cleanup test')
    with patch('src.memory.hindsight_memory.HindsightMemory.store_postmortem',side_effect=MemoryUnavailable('Hindsight timed out.')):
        button(at,'Save outcome to Hindsight').click().run()
    assert not at.exception
    assert at.session_state['drafts'][incident.incident_id].outcome == 'Active'
    assert field(at.text_area,'Actual root cause').value == 'Connection leak'
    assert any('not confirmed' in e.value for e in at.warning)
