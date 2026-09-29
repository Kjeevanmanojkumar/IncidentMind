from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]
Line = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


class Incident(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", frozen=True)
    incident_id: str = Field(default_factory=lambda: "INC-" + uuid4().hex[:12].upper(), pattern=r"^INC-[A-Z0-9-]{1,60}$")
    service: str = Field(min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_.-]+$")
    severity: Literal["SEV-1", "SEV-2", "SEV-3", "SEV-4"]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    description: Text
    error_message: str = Field(default="", max_length=4000)
    symptoms: list[Line] = Field(default_factory=list, max_length=30)
    logs: str = Field(default="", max_length=12000)
    recent_change: str = Field(default="", max_length=4000)
    root_cause: str = Field(default="", max_length=4000)
    resolution_steps: list[Line] = Field(default_factory=list, max_length=30)
    failed_approaches: list[Line] = Field(default_factory=list, max_length=30)
    runbook: str = Field(default="", max_length=1000)
    outcome: Literal["Active", "Resolved", "Mitigated", "Unresolved"] = "Active"
    resolution_time: float | None = Field(default=None, ge=0, le=525600)
    postmortem: str = Field(default="", max_length=6000)

    @model_validator(mode="after")
    def check_record(self):
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must include a timezone")
        if self.outcome != "Active" and (not self.root_cause or not self.resolution_steps or not self.postmortem or self.resolution_time is None):
            raise ValueError("A recorded outcome needs root cause, steps attempted, duration and post-mortem notes")
        return self

    def retrieval_context(self) -> str:
        return (
            f"Service: {self.service}\nIncident: {self.description}\nError: {self.error_message}\n"
            f"Symptoms: {'; '.join(self.symptoms)}\nRecent change: {self.recent_change}\n"
            f"Logs: {self.logs[:6000]}\nFind similar failures, root causes, successful and failed fixes, runbooks and lessons."
        )


class PostMortem(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    root_cause: Text
    resolution_steps: list[Line] = Field(min_length=1, max_length=30)
    failed_approaches: list[Line] = Field(default_factory=list, max_length=30)
    runbook: str = Field(default="", max_length=1000)
    outcome: Literal["Resolved", "Mitigated", "Unresolved"]
    resolution_time: float = Field(ge=0, le=525600)
    postmortem: Text

    def apply(self, incident: Incident) -> Incident:
        return Incident.model_validate({**incident.model_dump(), **self.model_dump()})
