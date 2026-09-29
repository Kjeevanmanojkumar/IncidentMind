from src.config import Settings
from src.errors import IncidentMindError
from src.memory.hindsight_memory import HindsightMemory
from src.services.sample_service import seed


def main():
    try:
        settings = Settings.from_env()
        print(f"Seeding Hindsight bank: {settings.bank_id}")
        count = seed(HindsightMemory(settings), lambda n, total: print(f"Confirmed {n}/{total}"))
        print(f"Stored {count} incident records in Hindsight.")
    except IncidentMindError as exc:
        raise SystemExit(str(exc)) from None

if __name__ == "__main__":
    main()
