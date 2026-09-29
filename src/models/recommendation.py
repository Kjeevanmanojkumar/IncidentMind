from pydantic import BaseModel, ConfigDict, Field
from src.models.incident import Incident, Text


class EvidenceUse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    incident_id: str
    quote: Text
    influence: Text


class Recommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    diagnosis: Text
    recommended_actions: list[Text] = Field(min_length=1, max_length=10)
    why: Text
    evidence_used: list[EvidenceUse] = Field(default_factory=list, max_length=6)


class Analysis(BaseModel):
    incident: Incident
    baseline: Recommendation
    enhanced: Recommendation
    historical_incidents: list[Incident]
    retrieved_facts: list[dict]
