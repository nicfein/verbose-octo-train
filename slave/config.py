"""Slave config pointing to master."""
import os

from dotenv import load_dotenv
from pathlib import Path

dotenv_path = Path(__file__).parent.parent / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)

SLAVE_ID: str = os.getenv("SLAVE_ID", f"slave-{os.getpid()}")
MASTER_URL: str = os.getenv("MASTER_URL", "http://localhost:8000")
MASTER_API_KEY: str = os.getenv("MASTER_API_KEY", "")

MAX_CLIENTS: int = int(os.getenv("SLAVE_MAX_CLIENTS", "5"))
BROWSER_PROFILE: str = os.getenv("BROWSER_PROFILE", "chrome_120")
AUTO_RETRIES: int = int(os.getenv("AUTO_RETRIES", "3"))

BG_SLEEP_MIN: int = int(os.getenv("BG_SLEEP_MIN", "1"))
BG_SLEEP_MAX: int = int(os.getenv("BG_SLEEP_MAX", "5"))
