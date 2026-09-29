from collections.abc import Callable
from src.agent.reasoning import Reasoner, validate_evidence
from src.memory.hindsight_memory import HindsightMemory
from src.models.incident import Incident
from src.models.recommendation import Analysis


class IncidentAgent:
    def __init__(self, memory: HindsightMemory, reasoner: Reasoner):
        self.memory = memory
        self.reasoner = reasoner

    def analyze(self, incident: Incident, progress: Callable[[str], None] = lambda _: None) -> Analysis:
        progress("Analyzing current incident without memory…")
        baseline = self.reasoner.recommend(incident, [])
        validate_evidence(baseline, [])
        progress("Searching Hindsight memory…")
        recalled = self.memory.retrieve_similar_incidents(incident)
        progress(f"Reviewing {len(recalled.incidents)} candidate incidents for relevance…")
        if recalled.incidents:
            progress("Generating a recommendation from relevant historical evidence…")
            enhanced = self.reasoner.recommend(incident, recalled.incidents)
            validate_evidence(enhanced, recalled.incidents)
        else:
            enhanced = baseline
        used = {e.incident_id for e in enhanced.evidence_used}
        records = [i for i in recalled.incidents if i.incident_id in used]
        # Avoid displaying ungrounded historical prose when relevance selection is empty.
        if not records:
            enhanced = baseline
        return Analysis(incident=incident, baseline=baseline, enhanced=enhanced,
            historical_incidents=records,
            retrieved_facts=[f for f in recalled.facts if f.get("document_id") in used])
