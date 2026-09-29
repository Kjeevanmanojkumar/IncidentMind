from unittest.mock import AsyncMock, MagicMock
import pytest
from hindsight_client_api.models import RetainResponse
from src.config import Settings
from src.services.sample_service import sample_incidents, demo_incident


@pytest.fixture
def current():
    return demo_incident()

@pytest.fixture
def past():
    return sample_incidents()[0]

@pytest.fixture
def settings():
    return Settings(hindsight_url="http://localhost:8888", allow_unauthenticated=True,
        llm_key="unit-test-not-a-real-key", llm_model="test-model")

@pytest.fixture
def sdk():
    client = MagicMock()
    client.aclose = AsyncMock()
    client.aretain = AsyncMock(return_value=RetainResponse(success=True, bank_id="incidentmind-demo", items_count=1, **{"async":False}))
    client.arecall = AsyncMock()
    client.acreate_bank = AsyncMock()
    client.documents.get_document = AsyncMock()
    client.documents.list_documents = AsyncMock()
    return client
