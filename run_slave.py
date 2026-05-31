"""Entry point for a slave worker."""
import signal
import sys

import slave.config as cfg
from slave.worker import Worker

worker_instance = None


def signal_handler(sig, frame):
    print("\nShutting down worker...")
    if worker_instance is not None:
        worker_instance.stop()
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    worker_instance = Worker(slave_id=cfg.SLAVE_ID)

    print(f"Starting slave worker: {cfg.SLAVE_ID}")
    print(f"Connecting to master at: {cfg.MASTER_URL}")
    print(f"Connecting to Redis at: {cfg.REDIS_HOST}:{cfg.REDIS_PORT}")
    print(f"Max TLS clients: {cfg.MAX_CLIENTS}")

    worker_instance.start()

    print("Worker running. Press Ctrl+C to stop.")
    try:
        signal.pause()
    except AttributeError:
        import time
        while True:
            time.sleep(1)
