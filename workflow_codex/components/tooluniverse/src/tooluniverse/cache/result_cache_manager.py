"""
Result cache manager that coordinates in-memory and persistent storage.
"""

from __future__ import annotations

import logging
import os
import queue
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterator, Optional, Sequence

from .memory_cache import LRUCache, SingleFlight
from .sqlite_backend import CacheEntry, PersistentCache

logger = logging.getLogger(__name__)


@dataclass
class CacheRecord:
    value: Any
    expires_at: Optional[float]
    namespace: str
    version: str


class ResultCacheManager:
    """Facade around memory + persistent cache layers."""

    def __init__(
        self,
        *,
        memory_size: int = 256,
        persistent_path: Optional[str] = None,
        enabled: bool = True,
        persistence_enabled: bool = True,
        singleflight: bool = True,
        default_ttl: Optional[int] = None,
        async_persist: Optional[bool] = None,
        async_queue_size: int = 10000,
    ):
        self.enabled = enabled
        self.default_ttl = default_ttl

        self.memory = LRUCache(max_size=memory_size)
        persistence_path = persistent_path
        if persistence_path is None:
            cache_dir = os.environ.get("TOOLUNIVERSE_CACHE_DIR")
            if cache_dir:
                persistence_path = os.path.join(cache_dir, "tooluniverse_cache.sqlite")
        self.persistent = None
        if persistence_enabled and persistence_path:
            try:
                self.persistent = PersistentCache(persistence_path, enable=True)
            except Exception as exc:
                logger.warning("Failed to initialize persistent cache: %s", exc)
                self.persistent = None

        self.singleflight = SingleFlight() if singleflight else None
        self._init_async_persistence(async_persist, async_queue_size)

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    @staticmethod
    def compose_key(namespace: str, version: str, cache_key: str) -> str:
        return f"{namespace}::{version}::{cache_key}"

    def _now(self) -> float:
        return time.time()

    def _ttl_or_default(self, ttl: Optional[int]) -> Optional[int]:
        return ttl if ttl is not None else self.default_ttl

    def _init_async_persistence(
        self, async_persist: Optional[bool], async_queue_size: int
    ) -> None:
        if async_persist is None:
            async_persist = os.getenv(
                "TOOLUNIVERSE_CACHE_ASYNC_PERSIST", "true"
            ).lower() in ("true", "1", "yes")

        self.async_persist = (
            async_persist and self.persistent is not None and self.enabled
        )

        self._persist_queue: Optional["queue.Queue[tuple[str, Dict[str, Any]]]"] = None
        self._worker_thread: Optional[threading.Thread] = None

        if not self.async_persist:
            return

        queue_size = max(1, async_queue_size)
        self._persist_queue = queue.Queue(maxsize=queue_size)
        self._worker_thread = threading.Thread(
            target=self._async_worker,
            name="ResultCacheWriter",
            daemon=True,
        )
        self._worker_thread.start()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get(self, *, namespace: str, version: str, cache_key: str) -> Optional[Any]:
        if not self.enabled:
            return None

        composed = self.compose_key(namespace, version, cache_key)
        record = self.memory.get(composed)
        if record:
            if record.expires_at and record.expires_at <= self._now():
                self.memory.delete(composed)
            else:
                return record.value

        entry = self._get_from_persistent(composed)
        if entry:
            expires_at = entry.created_at + entry.ttl if entry.ttl else None
            self.memory.set(
                composed,
                CacheRecord(
                    value=entry.value,
                    expires_at=expires_at,
                    namespace=namespace,
                    version=version,
                ),
            )
            return entry.value
        return None

    def set(
        self,
        *,
        namespace: str,
        version: str,
        cache_key: str,
        value: Any,
        ttl: Optional[int] = None,
    ):
        if not self.enabled:
            return

        effective_ttl = self._ttl_or_default(ttl)
        expires_at = self._now() + effective_ttl if effective_ttl else None
        composed = self.compose_key(namespace, version, cache_key)

        self.memory.set(
            composed,
            CacheRecord(
                value=value,
                expires_at=expires_at,
                namespace=namespace,
                version=version,
            ),
        )

        if self.persistent:
            payload = {
                "composed": composed,
                "value": value,
                "namespace": namespace,
                "version": version,
                "ttl": effective_ttl,
            }
            if not self._schedule_persist("set", payload):
                self._perform_persist_set(**payload)

    def delete(self, *, namespace: str, version: str, cache_key: str):
        composed = self.compose_key(namespace, version, cache_key)
        self.memory.delete(composed)
        if self.persistent:
            try:
                self.persistent.delete(composed)
            except Exception as exc:
                logger.warning("Persistent cache delete failed: %s", exc)

    def clear(self, namespace: Optional[str] = None):
        if namespace:
            # Clear matching namespace in memory
            keys_to_remove = [
                key
                for key, record in self.memory.items()
                if hasattr(record, "namespace") and record.namespace == namespace
            ]
            for key in keys_to_remove:
                self.memory.delete(key)
        else:
            self.memory.clear()

        if self.persistent:
            try:
                self.flush()
                self.persistent.clear(namespace=namespace)
            except Exception as exc:
                logger.warning("Persistent cache clear failed: %s", exc)

    def bulk_get(self, requests: Sequence[Dict[str, str]]) -> Dict[str, Any]:
        """Fetch multiple cache entries at once.

        Args:
            requests: Iterable of dicts containing ``namespace``, ``version`` and ``cache_key``.

        Returns
            Mapping of composed cache keys to cached values.
        """

        if not self.enabled:
            return {}

        hits: Dict[str, Any] = {}
        for request in requests:
            namespace = request["namespace"]
            version = request["version"]
            cache_key = request["cache_key"]
            value = self.get(
                namespace=namespace,
                version=version,
                cache_key=cache_key,
            )
            if value is not None:
                composed = self.compose_key(namespace, version, cache_key)
                hits[composed] = value

        return hits

    def stats(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "memory": self.memory.stats(),
            "persistent": (
                self.persistent.stats() if self.persistent else {"enabled": False}
            ),
            "async_persist": self.async_persist,
            "pending_writes": (
                self._persist_queue.qsize()
                if self.async_persist and self._persist_queue is not None
                else 0
            ),
        }

    def dump(self, namespace: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        if not self.persistent:
            return iter([])
        self.flush()
        return (
            {
                "cache_key": entry.key,
                "namespace": entry.namespace,
                "version": entry.version,
                "ttl": entry.ttl,
                "created_at": entry.created_at,
                "last_accessed": entry.last_accessed,
                "hit_count": entry.hit_count,
                "value": entry.value,
            }
            for entry in self._iter_persistent(namespace=namespace)
        )

    def _get_from_persistent(self, composed_key: str) -> Optional[CacheEntry]:
        if not self.persistent:
            return None
        try:
            return self.persistent.get(composed_key)
        except Exception as exc:
            logger.warning("Persistent cache read failed: %s", exc)
            self.persistent = None
            return None

    def _iter_persistent(self, namespace: Optional[str]):
        if not self.persistent:
            return iter([])
        try:
            return self.persistent.iter_entries(namespace=namespace)
        except Exception as exc:
            logger.warning("Persistent cache iterator failed: %s", exc)
            return iter([])

    # ------------------------------------------------------------------
    # Context manager for singleflight
    # ------------------------------------------------------------------
    def singleflight_guard(self, composed_key: str):
        if self.singleflight:
            return self.singleflight.acquire(composed_key)
        return _DummyContext()

    def close(self):
        self.flush()
        self._shutdown_async_worker()
        if self.persistent:
            try:
                self.persistent.close()
            except Exception as exc:
                logger.warning("Persistent cache close failed: %s", exc)

    # ------------------------------------------------------------------
    # Async persistence helpers
    # ------------------------------------------------------------------

    def flush(self):
        if self.async_persist and self._persist_queue is not None:
            self._persist_queue.join()

    def _schedule_persist(self, op: str, payload: Dict[str, Any]) -> bool:
        if not self.async_persist or self._persist_queue is None:
            return False
        try:
            self._persist_queue.put_nowait((op, payload))
            return True
        except queue.Full:
            logger.warning(
                "Async cache queue full; falling back to synchronous persistence"
            )
            return False

    def _async_worker(self):
        queue_ref = self._persist_queue
        if queue_ref is None:
            return

        while True:
            try:
                op, payload = queue_ref.get()
            except Exception:
                continue

            if op == "__STOP__":
                queue_ref.task_done()
                break

            try:
                if op == "set":
                    self._perform_persist_set(**payload)
                else:
                    logger.warning("Unknown async cache operation: %s", op)
            except Exception as exc:
                logger.warning("Async cache write failed: %s", exc)
                # Disable async persistence to avoid repeated failures
                self.async_persist = False
            finally:
                queue_ref.task_done()

    def _perform_persist_set(
        self,
        *,
        composed: str,
        value: Any,
        namespace: str,
        version: str,
        ttl: Optional[int],
    ):
        if not self.persistent:
            return
        try:
            self.persistent.set(
                composed,
                value,
                namespace=namespace,
                version=version,
                ttl=ttl,
            )
        except Exception as exc:
            logger.warning("Persistent cache write failed: %s", exc)
            self.persistent = None
            raise

    def _shutdown_async_worker(self) -> None:
        if not self.async_persist or self._persist_queue is None:
            return

        try:
            self._persist_queue.put_nowait(("__STOP__", {}))
        except queue.Full:
            self._persist_queue.put(("__STOP__", {}))

        if self._worker_thread is not None:
            self._worker_thread.join(timeout=5)

        self._worker_thread = None
        self._persist_queue = None


class _DummyContext:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
