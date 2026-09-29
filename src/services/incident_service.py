from src.memory.hindsight_memory import HindsightMemory
from src.models.incident import Incident, PostMortem


class IncidentService:
    def __init__(self, memory: HindsightMemory):
        self.memory = memory

    def resolve(self, incident: Incident, postmortem: PostMortem) -> Incident:
        completed = postmortem.apply(incident)
        # Callers update UI state only after Hindsight acknowledges synchronous retain.
        self.memory.store_postmortem(completed)
        return completed
