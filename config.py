"""Shared configuration for the Spotify metadata retrieval system."""
import os
from pathlib import Path

dotenv_path = Path(__file__).parent / ".env"
if dotenv_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path)
    except Exception:
        pass

REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

REDIS_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

MONGO_HOST: str = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT: int = int(os.getenv("MONGO_PORT", "27017"))
MONGO_DATABASE: str = os.getenv("MONGO_DATABASE", "spotify_metadata")
MONGO_USERNAME: str = os.getenv("MONGO_USERNAME", "")
MONGO_PASSWORD: str = os.getenv("MONGO_PASSWORD", "")
MONGO_COLLECTION_METADATA: str = "metadata"
MONGO_COLLECTION_FETCH_LOG: str = "fetch_log"

ALBUM_QUEUE_LIMIT: int = int(os.getenv("ALBUM_QUEUE_LIMIT", "10"))
DATA_TTL_SECONDS: int = int(os.getenv("DATA_TTL_SECONDS", str(24 * 60 * 60)))

BG_SLEEP_MIN: int = int(os.getenv("BG_SLEEP_MIN", "1"))
BG_SLEEP_MAX: int = int(os.getenv("BG_SLEEP_MAX", "5"))

PUBSUB_CHANNEL: str = "spotify:fetch:tasks"
QUEUE_KEY: str = "spotify:queue:albums"
QUEUE_PRIORITY_KEY: str = "spotify:queue:priority"

MASTER_HOST: str = os.getenv("MASTER_HOST", "0.0.0.0")
MASTER_PORT: int = int(os.getenv("MASTER_PORT", "8000"))
MASTER_API_KEY: str = os.getenv("MASTER_API_KEY", "changeme")

SLAVE_MAX_CLIENTS: int = int(os.getenv("SLAVE_MAX_CLIENTS", "5"))

RATE_LIMIT_FREETIER: int = int(os.getenv("RATE_LIMIT_FREETIER", "30"))
RATE_LIMIT_TOKEN: int = int(os.getenv("RATE_LIMIT_TOKEN", "100"))
RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
RATE_LIMIT_BURST: int = int(os.getenv("RATE_LIMIT_BURST", "10"))

MONGO_COLLECTION_TOKENS: str = "api_tokens"

ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "")
ADMIN_EMAIL_PASSWORD: str = os.getenv("ADMIN_EMAIL_PASSWORD", "")

CRAWLER_ENABLED: bool = os.getenv("CRAWLER_ENABLED", "false").lower() in ("true", "1", "yes")
CRAWLER_INTERVAL: int = int(os.getenv("CRAWLER_INTERVAL", "60"))
CRAWLER_QUEUE_THRESHOLD: int = int(os.getenv("CRAWLER_QUEUE_THRESHOLD", "50"))
CRAWLER_BATCH_SIZE: int = int(os.getenv("CRAWLER_BATCH_SIZE", "10"))
CRAWLER_GENRES: str = os.getenv("CRAWLER_GENRES", "pop,rock,hip-hop,electronic,jazz,classical,r&b,metal,indie,latin,folk,blues,country,reggae,punk,ambient")
CRAWLER_ARTIST_TTL: int = int(os.getenv("CRAWLER_ARTIST_TTL", str(7 * 24 * 3600)))
CRAWLER_PAUSE_THRESHOLD: int = int(os.getenv("CRAWLER_PAUSE_THRESHOLD", "500"))
