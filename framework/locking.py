"""Hold an optional shared lock for the ENTIRE integration session."""
import threading
from contextlib import contextmanager
from hashlib import sha256
import redis


@contextmanager
def sandbox_lock(base_url: str, redis_url: str | None):
    if not redis_url:
        yield lambda: None
        return
    client = redis.Redis.from_url(redis_url)
    key = "parabank:qa:" + sha256(base_url.rstrip("/").lower().encode()).hexdigest()
    lock = client.lock(key, timeout=120, blocking_timeout=300, thread_local=False)
    if not lock.acquire():
        raise RuntimeError("Cannot acquire shared ParaBank lock; refusing reset")
    stop = threading.Event()
    lost = threading.Event()

    def renew():
        while not stop.wait(30):
            try:
                lock.extend(120, replace_ttl=True)
            except Exception:
                lost.set()
                return

    def assert_owned():
        if lost.is_set() or not lock.owned():
            raise RuntimeError("Shared sandbox lease lost; refusing further scenario actions")

    worker = threading.Thread(target=renew, daemon=True)
    worker.start()
    try:
        yield assert_owned
        assert_owned()
    finally:
        stop.set()
        worker.join(timeout=5)
        if lock.owned():
            lock.release()
        client.close()
