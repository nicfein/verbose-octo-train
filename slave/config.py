"""Slave config pointing to master."""
import os
import sys
from pathlib import Path

dotenv_path = Path(__file__).parent.parent / ".env"
if dotenv_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path)

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

REDIS_HOST: str = os.getenv("REDIS_HOST", config.REDIS_HOST)
REDIS_PORT: int = int(os.getenv("REDIS_PORT", str(config.REDIS_PORT)))
REDIS_DB: int = int(os.getenv("REDIS_DB", str(config.REDIS_DB)))
SLAVE_ID: str = os.getenv("SLAVE_ID", f"slave-{os.getpid()}")
MASTER_URL: str = os.getenv("MASTER_URL", f"http://localhost:{config.MASTER_PORT}")
MASTER_API_KEY: str = os.getenv("MASTER_API_KEY", config.MASTER_API_KEY)

MAX_CLIENTS: int = int(os.getenv("SLAVE_MAX_CLIENTS", str(config.SLAVE_MAX_CLIENTS)))
BROWSER_PROFILE: str = os.getenv("BROWSER_PROFILE", "chrome_120")
AUTO_RETRIES: int = int(os.getenv("AUTO_RETRIES", "3"))

BG_SLEEP_MIN: int = int(os.getenv("BG_SLEEP_MIN", str(config.BG_SLEEP_MIN)))
BG_SLEEP_MAX: int = int(os.getenv("BG_SLEEP_MAX", str(config.BG_SLEEP_MAX)))
PUBSUB_CHANNEL: str = os.getenv("PUBSUB_CHANNEL", config.PUBSUB_CHANNEL)
QUEUE_KEY: str = os.getenv("QUEUE_KEY", config.QUEUE_KEY)
QUEUE_PRIORITY_KEY: str = os.getenv("QUEUE_PRIORITY_KEY", config.QUEUE_PRIORITY_KEY)
