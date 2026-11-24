"""Configuration loaded from environment variables or a local .env file."""
import os
from pathlib import Path


def _load_env_file() -> None:
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_env_file()

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0") or "0")
PAYMENT_DETAILS = os.environ.get(
    "PAYMENT_DETAILS", "Vodafone Cash: 01XXXXXXXXX"
).replace("\\n", "\n")
CURRENCY = os.environ.get("CURRENCY", "جنيه")
