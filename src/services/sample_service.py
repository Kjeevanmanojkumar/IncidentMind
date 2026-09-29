"""Seed import is explicit; sample files are never a runtime memory fallback."""
import json
from pathlib import Path
from src.models.incident import Incident

DATA = Path(__file__).resolve().parents[2] / "data"


def sample_incidents() -> list[Incident]:
    return [Incident.model_validate(i) for i in json.loads((DATA / "sample_incidents.json").read_text())]


def demo_incident() -> Incident:
    return Incident(service="payment-api", severity="SEV-1",
        description="Payment requests started failing ten minutes after deployment.",
        error_message="Timeout acquiring database connection",
        symptoms=["HTTP 503 errors increasing", "Database connection pool exhausted"],
        logs="pool.active=100 pool.idle=0 acquisition_timeout=30000ms",
        recent_change="payment-api v2.8.4 deployed 10 minutes ago")


def seed(memory, progress=lambda _n, _total: None):
    records = sample_incidents()
    memory.initialize_bank()
    for n, record in enumerate(records, 1):
        memory.store_incident(record)
        progress(n, len(records))
    return len(records)
