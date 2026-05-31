"""TLSClient pool management for slaves."""
import threading
import logging
from typing import Optional

from spotapi.http.request import TLSClient

import slave.config as cfg

logger = logging.getLogger(__name__)


class ClientPool:
    def __init__(self, max_size: int | None = None):
        self._max_size = max_size or cfg.MAX_CLIENTS
        self._clients: list[TLSClient] = []
        self._lock = threading.Lock()
        self._created = 0

    def get(self) -> TLSClient:
        with self._lock:
            if self._clients:
                return self._clients.pop()
            if self._created < self._max_size:
                client = TLSClient(
                    cfg.BROWSER_PROFILE, "",
                    auto_retries=cfg.AUTO_RETRIES,
                )
                self._created += 1
                logger.info(f"Created new TLSClient (total: {self._created}/{self._max_size})")
                return client
            while not self._clients:
                pass
            return self._clients.pop()

    def put(self, client: TLSClient) -> None:
        with self._lock:
            if len(self._clients) < self._max_size:
                self._clients.append(client)
            else:
                client.close()

    def close_all(self) -> None:
        with self._lock:
            for c in self._clients:
                c.close()
            self._clients.clear()
            self._created = 0


_pool: Optional[ClientPool] = None


def get_pool() -> ClientPool:
    global _pool
    if _pool is None:
        _pool = ClientPool()
    return _pool
