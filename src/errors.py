"""User-safe domain errors. Never surface provider bodies containing credentials/logs."""
class IncidentMindError(Exception):
    pass

class ConfigurationError(IncidentMindError):
    pass

class MemoryUnavailable(IncidentMindError):
    pass

class RecommendationUnavailable(IncidentMindError):
    pass


def provider_message(provider: str, error: Exception) -> str:
    status = getattr(error, "status_code", None) or getattr(error, "status", None)
    if status in (401, 403):
        return f"{provider} rejected authentication or access. Check the configured key and permissions."
    if status == 429:
        return f"{provider} rate or quota limit reached. Wait, check quota, then retry."
    if "timeout" in type(error).__name__.lower() or isinstance(error, TimeoutError):
        return f"{provider} timed out. Check service health and retry."
    return f"{provider} request failed. Check the endpoint, service health and configuration, then retry."
