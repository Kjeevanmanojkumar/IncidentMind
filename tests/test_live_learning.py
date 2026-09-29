"""Real acceptance test. No mocks. Opt in explicitly; uses paid providers.

Creates a uniquely named Hindsight bank and leaves evidence there for inspection.
No credentials -> skipped, never reported as a successful live learning loop.
"""
import os
import time
from dataclasses import replace
from uuid import uuid4
import pytest
from src.config import Settings
from src.memory.hindsight_memory import HindsightMemory
from src.agent.reasoning import Reasoner
from src.agent.incident_agent import IncidentAgent
from src.models.incident import PostMortem
from src.services.incident_service import IncidentService
from src.services.sample_service import demo_incident, seed

@pytest.mark.live
@pytest.mark.skipif(os.getenv('RUN_LIVE_TESTS') != '1',reason='Set RUN_LIVE_TESTS=1 with real Hindsight and LLM credentials')
def test_real_hindsight_learning_loop():
    settings=replace(Settings.from_env(),bank_id='incidentmind-test-'+uuid4().hex[:10])
    settings.validate_memory()
    settings.validate_llm()
    memory=HindsightMemory(settings)
    print(f'Live evidence bank: {settings.bank_id}')
    assert seed(memory) == 20
    incident_a=demo_incident()
    agent=IncidentAgent(memory,Reasoner(settings))
    before=agent.analyze(incident_a)
    assert before.historical_incidents, 'No relevant seeded incident recalled'
    assert any(i.runbook == 'Database Connection Exhaustion' for i in before.historical_incidents)
    marker='Cleanup regression '+uuid4().hex[:8]
    post=PostMortem(root_cause='v2.8.4 exception path failed to close database connections',
        resolution_steps=['Rolled back v2.8.4 with approval','Performed rolling restart','Verified payment errors and pool occupancy recovered'],
        failed_approaches=['Increasing pool size delayed but did not stop the leak'],
        runbook='Database Connection Exhaustion', outcome='Resolved',resolution_time=8,
        postmortem=marker+': add cancellation and exception-path connection release tests.')
    saved=IncidentService(memory).resolve(incident_a,post)
    assert memory.retrieve_incident_knowledge(saved.incident_id).postmortem == post.postmortem
    # New object / client guarantees no application-local memory is used.
    fresh=HindsightMemory(settings)
    incident_b=demo_incident()
    found=False
    for attempt in range(6):
        recalled=fresh.retrieve_similar_incidents(incident_b)
        if saved.incident_id in {i.incident_id for i in recalled.incidents}:
            found=True
            break
        if attempt < 5:
            time.sleep(5)
    assert found, 'Newly learned incident not returned by real Hindsight recall'
    after=IncidentAgent(fresh,Reasoner(settings)).analyze(incident_b)
    citations={e.incident_id:e for e in after.enhanced.evidence_used}
    assert saved.incident_id in citations, 'New source did not influence the future recommendation'
    assert citations[saved.incident_id].influence.strip()
    assert any(marker in i.postmortem for i in after.historical_incidents)
