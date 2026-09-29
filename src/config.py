from dataclasses import dataclass
import os
from urllib.parse import urlparse
from dotenv import load_dotenv
from src.errors import ConfigurationError


@dataclass(frozen=True)
class Settings:
    hindsight_url: str = ""
    hindsight_key: str = ""
    bank_id: str = "incidentmind-demo"
    allow_unauthenticated: bool = False
    llm_key: str = ""
    llm_url: str = "https://api.openai.com/v1"
    llm_model: str = ""
    timeout: float = 120.0

    @classmethod
    def from_env(cls):
        load_dotenv()
        try:
            timeout = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "120"))
        except ValueError:
            raise ConfigurationError("REQUEST_TIMEOUT_SECONDS must be a number.") from None
        if not 1 <= timeout <= 600:
            raise ConfigurationError("REQUEST_TIMEOUT_SECONDS must be between 1 and 600.")
        return cls(
            hindsight_url=os.getenv("HINDSIGHT_BASE_URL", "").strip(),
            hindsight_key=os.getenv("HINDSIGHT_API_KEY", "").strip(),
            bank_id=os.getenv("HINDSIGHT_BANK_ID", "incidentmind-demo").strip(),
            allow_unauthenticated=os.getenv("HINDSIGHT_ALLOW_UNAUTHENTICATED", "false").lower() == "true",
            llm_key=os.getenv("LLM_API_KEY", "").strip(),
            llm_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").strip(),
            llm_model=os.getenv("LLM_MODEL", "").strip(), timeout=timeout,
        )

    def validate_memory(self):
        self._url(self.hindsight_url, "HINDSIGHT_BASE_URL")
        if not self.bank_id or len(self.bank_id) > 100 or not all(c.isalnum() or c in "-_" for c in self.bank_id):
            raise ConfigurationError("HINDSIGHT_BANK_ID must contain 1–100 letters, numbers, hyphens or underscores.")
        if not self.hindsight_key and not self.allow_unauthenticated:
            raise ConfigurationError("Set HINDSIGHT_API_KEY, or explicitly allow an unauthenticated local server in .env.")
        if not self.hindsight_key and urlparse(self.hindsight_url).hostname not in ("localhost", "127.0.0.1", "::1"):
            raise ConfigurationError("Unauthenticated Hindsight access is permitted only for localhost.")

    def validate_llm(self):
        self._url(self.llm_url, "LLM_BASE_URL")
        if not self.llm_key or not self.llm_model:
            raise ConfigurationError("Set LLM_API_KEY and LLM_MODEL in .env to generate recommendations.")

    @staticmethod
    def _url(value, name):
        u = urlparse(value)
        if u.scheme not in ("https", "http") or not u.hostname or u.username or u.password or u.query or u.fragment:
            raise ConfigurationError(f"Set {name} to a valid HTTP(S) endpoint without embedded credentials, query or fragment.")
        if u.scheme == "http" and u.hostname not in ("localhost", "127.0.0.1", "::1"):
            raise ConfigurationError(f"{name} must use HTTPS outside localhost.")
