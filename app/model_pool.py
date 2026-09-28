"""Thread-safe pool of model replicas for concurrent inference."""

import logging
import queue
import threading
from contextlib import contextmanager
from typing import Any, Callable

log = logging.getLogger("sloptotal.model_pool")

# Every from_pretrained() call in the process must hold this lock. transformers
# loading is not thread-safe across models: two loads running at once (the
# startup preloader and a first request, say) can leave GPT-2's tied lm_head
# randomly initialised, which showed up as DistilGPT-2 perplexities of 50257
# and 1e15 and pinned Binoculars at 1.0. Reentrant so a loader may call another.
LOAD_LOCK = threading.RLock()


class ModelPool:
    """A fixed-size pool of (model, tokenizer) pairs backed by queue.Queue.

    queue.Queue.get() blocks when all replicas are checked out, providing
    the same backpressure as a Lock but allowing N concurrent users.
    """

    def __init__(self, load_fn: Callable[[], Any], pool_size: int = 1, name: str = ""):
        self._pool: queue.Queue = queue.Queue(maxsize=pool_size)
        self._load_fn = load_fn
        self._pool_size = pool_size
        self._name = name
        self._init_lock = threading.Lock()
        self._initialized = False

    def initialize(self) -> None:
        """Pre-load all replicas (call at startup). Safe to call more than once."""
        with self._init_lock:
            if self._initialized:
                return
            self._load_all()
            self._initialized = True

    def _load_all(self) -> None:
        for i in range(self._pool_size):
            try:
                with LOAD_LOCK:
                    replica = self._load_fn()
                self._pool.put_nowait(replica)
                log.info(
                    f"ModelPool[{self._name}] replica {i + 1}/{self._pool_size} loaded"
                )
            except Exception:
                log.exception(f"ModelPool[{self._name}] failed to load replica {i + 1}")
                raise

    @contextmanager
    def acquire(self, timeout: float = 30.0):
        """Yield a (model, tokenizer) pair, returning it to the pool on exit."""
        try:
            replica = self._pool.get(timeout=timeout)
        except queue.Empty:
            raise TimeoutError(
                f"ModelPool[{self._name}] timed out waiting for a replica "
                f"after {timeout}s"
            )
        try:
            yield replica
        finally:
            self._pool.put_nowait(replica)

    @property
    def size(self) -> int:
        return self._pool_size
