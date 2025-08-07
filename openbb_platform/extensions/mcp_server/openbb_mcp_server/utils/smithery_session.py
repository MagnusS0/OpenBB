from __future__ import annotations

from typing import Any, Dict, Optional
from threading import RLock


class _SessionStore:
    _store: Dict[str, Dict[str, Any]]
    _lock: RLock

    def __init__(self) -> None:
        self._store = {}
        self._lock = RLock()

    def set(self, session_id: str, config: Dict[str, Any]) -> None:
        with self._lock:
            self._store[session_id] = config

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._store.get(session_id)

    def clear(self, session_id: str) -> None:
        with self._lock:
            if session_id in self._store:
                del self._store[session_id]


SESSIONS = _SessionStore()