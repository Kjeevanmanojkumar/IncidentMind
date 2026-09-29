"""LLM reasoning with schema and citation validation; no scripted fallback advice."""
import json
import re
from openai import OpenAI
from src.agent.prompts import SYSTEM
from src.config import Settings
from src.errors import RecommendationUnavailable, provider_message
from src.models.incident import Incident
from src.models.recommendation import Recommendation


def validate_evidence(result: Recommendation, records: list[Incident]):
    by_id = {i.incident_id: i for i in records}
    used = set()
    for citation in result.evidence_used:
        if citation.incident_id not in by_id or citation.incident_id in used:
            raise RecommendationUnavailable("The model returned an unknown or duplicate memory citation. Retry analysis.")
        i = by_id[citation.incident_id]
        fields = [i.description, i.error_message, i.root_cause, i.postmortem, i.runbook,
                  *i.symptoms, *i.resolution_steps, *i.failed_approaches]
        if not any(citation.quote in field for field in fields):
            raise RecommendationUnavailable("The model's evidence quote does not match the Hindsight source. Retry analysis.")
        used.add(citation.incident_id)
    mentioned = set(re.findall(r"\bINC-[A-Z0-9-]+", result.model_dump_json()))
    if mentioned - used:
        raise RecommendationUnavailable("The model mentioned an uncited incident. Retry analysis.")


class Reasoner:
    def __init__(self, settings: Settings, client_factory=OpenAI):
        self.settings = settings
        self.client_factory = client_factory

    def recommend(self, current: Incident, records: list[Incident]) -> Recommendation:
        self.settings.validate_llm()
        try:
            with self.client_factory(api_key=self.settings.llm_key, base_url=self.settings.llm_url,
                    timeout=self.settings.timeout, max_retries=0) as client:
                response = client.chat.completions.create(model=self.settings.llm_model,
                    response_format={"type": "json_object"},
                    messages=[{"role": "system", "content": SYSTEM},
                              {"role": "user", "content": json.dumps({
                                  "current_incident": current.model_dump(mode="json", exclude={"incident_id"}),
                                  "historical_records": [i.model_dump(mode="json") for i in records],
                              })}])
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty model output")
            result = Recommendation.model_validate_json(content)
            validate_evidence(result, records)
            return result
        except RecommendationUnavailable:
            raise
        except (ValueError, IndexError):
            raise RecommendationUnavailable("The model returned an invalid recommendation. Retry or choose a JSON-capable model.") from None
        except Exception as exc:
            raise RecommendationUnavailable(provider_message("LLM", exc)) from None
