"""Worker that polls master for tasks - no direct Redis access."""
import socket
_original_getaddrinfo = socket.getaddrinfo

def _fast_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    try:
        return _original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
    except Exception:
        return _original_getaddrinfo(host, port, family, type, proto, flags)

socket.getaddrinfo = _fast_getaddrinfo

import json
import logging
import random
import time
import threading
from typing import Any

import requests

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import slave.config as cfg
from slave.fetcher import SlaveFetcher
from slave.client_pool import get_pool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _bg_sleep():
    delay = random.uniform(cfg.BG_SLEEP_MIN, cfg.BG_SLEEP_MAX)
    time.sleep(delay)


class Worker:
    def __init__(self, slave_id: str | None = None):
        self.slave_id = slave_id or cfg.SLAVE_ID
        self._fetcher = SlaveFetcher()
        self._running = False
        self._thread: threading.Thread | None = None

    def _heartbeat(self):
        try:
            requests.post(
                f"{cfg.MASTER_URL}/slave/heartbeat",
                headers={
                    "X-API-KEY": cfg.MASTER_API_KEY,
                    "X-Slave-Name": self.slave_id,
                },
                timeout=10,
            )
        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")

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
                headers={
                    "X-API-KEY": cfg.MASTER_API_KEY,
                    "X-Slave-Name": self.slave_id,
                },
                timeout=30,
            )
            if resp.ok:
                logger.info(f"Reported result: {entity_type}/{entity_id} -> {success}")
            else:
                logger.warning(f"Failed to report result: {resp.status_code}")
        except Exception as e:
            logger.error(f"Error reporting result to master: {e}")

    def _poll_task(self) -> dict | None:
        try:
            resp = requests.get(
                f"{cfg.MASTER_URL}/slave/poll",
                headers={
                    "X-API-KEY": cfg.MASTER_API_KEY,
                    "X-Slave-Name": self.slave_id,
                },
                timeout=30,
            )
            if resp.ok:
                data = resp.json()
                return data.get("task")
        except Exception as e:
            logger.error(f"Error polling master: {e}")
        return None

    def _process_task(self, task: dict) -> None:
        entity_type = task.get("type", "album")
        entity_id = task.get("id", "")
        priority = task.get("priority", "normal")

        if not entity_id:
            logger.warning("Task missing id, skipping")
            return

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

    def _poll_loop(self) -> None:
        cycle = 0
        while self._running:
            try:
                t0 = time.time()
                task = self._poll_task()
                elapsed = time.time() - t0
                logger.info(f"[DEBUG] poll took {elapsed:.2f}s, got task={task is not None}")
                if task:
                    self._process_task(task)
                    cycle = 0
                else:
                    time.sleep(1)
                    cycle += 1
                if cycle >= 10:
                    self._heartbeat()
                    cycle = 0
            except Exception as e:
                logger.error(f"Poll loop error: {e}")
                time.sleep(5)

    def start(self) -> None:
        self._running = True
        self._heartbeat()
        self._thread = threading.Thread(target=self._poll_loop, daemon=True, name=f"worker-{self.slave_id}")
        self._thread.start()
        logger.info(f"Worker {self.slave_id} started")

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        get_pool().close_all()
        logger.info(f"Worker {self.slave_id} stopped")
