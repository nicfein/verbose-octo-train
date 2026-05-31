"""Redis pub/sub subscriber worker - runs on slaves."""
import json
import logging
import random
import time
import threading
from typing import Any

import redis
import requests

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import config
import slave.config as cfg
from slave.fetcher import SlaveFetcher
from slave.client_pool import get_pool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=cfg.REDIS_HOST,
            port=cfg.REDIS_PORT,
            db=cfg.REDIS_DB,
            decode_responses=True,
        )
    return _redis_client


def _bg_sleep():
    delay = random.uniform(cfg.BG_SLEEP_MIN, cfg.BG_SLEEP_MAX)
    time.sleep(delay)


class Worker:
    def __init__(self, slave_id: str | None = None):
        self.slave_id = slave_id or cfg.SLAVE_ID
        self._redis = get_redis()
        self._fetcher = SlaveFetcher()
        self._running = False
        self._thread: threading.Thread | None = None

    def _post_result(self, entity_type: str, entity_id: str, data: dict | None, error: str | None = None):
        success = error is None and data is not None
        payload = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "success": success,
            "data": data,
            "error": error,
        }
        try:
            resp = requests.post(
                f"{cfg.MASTER_URL}/internal/result",
                json=payload,
                headers={"X-API-KEY": cfg.MASTER_API_KEY},
                timeout=30,
            )
            if resp.ok:
                logger.info(f"Reported result: {entity_type}/{entity_id} -> {success}")
            else:
                logger.warning(f"Failed to report result: {resp.status_code}")
        except Exception as e:
            logger.error(f"Error reporting result to master: {e}")

    def _process_task(self, task: dict) -> None:
        entity_type = task.get("type", "album")
        entity_id = task.get("id", "")
        priority = task.get("priority", "normal")

        if not entity_id:
            logger.warning("Task missing id, skipping")
            return

        dedup_key = f"processing:{entity_type}:{entity_id}"
        if self._redis.exists(dedup_key):
            logger.debug(f"Skipping duplicate task: {entity_type}/{entity_id}")
            return
        self._redis.setex(dedup_key, 300, "1")

        logger.info(f"Processing task: {entity_type}/{entity_id} (priority={priority})")

        if priority == "normal":
            _bg_sleep()

        try:
            if entity_type == "album":
                data, artist_id = self._fetcher.fetch_album(entity_id)
                self._post_result("album", entity_id, data)
                logger.info(f"Fetched album {entity_id}")
            elif entity_type == "artist":
                data = self._fetcher.fetch_artist(entity_id)
                self._post_result("artist", entity_id, data)
                logger.info(f"Fetched artist {entity_id}")
            elif entity_type == "song":
                data = self._fetcher.fetch_song(entity_id)
                self._post_result("song", entity_id, data)
                logger.info(f"Fetched song {entity_id}")
            else:
                logger.warning(f"Unknown entity type: {entity_type}")
        except Exception as e:
            logger.error(f"Error fetching {entity_type}/{entity_id}: {e}")
            self._post_result(entity_type, entity_id, None, str(e))
        finally:
            self._redis.delete(dedup_key)

    def _consume_queue(self) -> None:
        while self._running:
            try:
                result = self._redis.brpop(cfg.QUEUE_PRIORITY_KEY, timeout=5)
                if result:
                    _, task_json = result
                    task = json.loads(task_json)
                    self._process_task(task)
                    continue

                result = self._redis.brpop(cfg.QUEUE_KEY, timeout=5)
                if result:
                    _, task_json = result
                    task = json.loads(task_json)
                    self._process_task(task)
            except Exception as e:
                logger.error(f"Queue consumer error: {e}")
                time.sleep(1)

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._consume_queue, daemon=True, name=f"worker-{self.slave_id}")
        self._thread.start()
        logger.info(f"Worker {self.slave_id} started")

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        get_pool().close_all()
        logger.info(f"Worker {self.slave_id} stopped")
