from abc import ABC, abstractmethod
from typing import List

from app.config import get_settings


class SessionStore(ABC):
    """Conversation memory store keyed by session_id."""

    @abstractmethod
    async def get_history(self, session_id: str) -> List[tuple[str, str]]:
        """Return list of (role, content) pairs, oldest first."""

    @abstractmethod
    async def append(self, session_id: str, role: str, content: str) -> None:
        """Append a message to the session history."""

    @abstractmethod
    async def clear(self, session_id: str) -> None:
        """Remove a session's history."""


class InMemorySessionStore(SessionStore):
    def __init__(self) -> None:
        self._data: dict[str, List[tuple[str, str]]] = {}

    async def get_history(self, session_id: str) -> List[tuple[str, str]]:
        return list(self._data.get(session_id, []))

    async def append(self, session_id: str, role: str, content: str) -> None:
        self._data.setdefault(session_id, []).append((role, content))

    async def clear(self, session_id: str) -> None:
        self._data.pop(session_id, None)


class RedisSessionStore(SessionStore):
    def __init__(self, redis_url: str, ttl: int) -> None:
        import redis.asyncio as aioredis

        self._redis = aioredis.from_url(redis_url, decode_responses=True)
        self._ttl = ttl

    async def get_history(self, session_id: str) -> List[tuple[str, str]]:
        raw = await self._redis.lrange(session_id, 0, -1)
        return [(r.split(":", 1)[0], r.split(":", 1)[1]) for r in raw if ":" in r]

    async def append(self, session_id: str, role: str, content: str) -> None:
        await self._redis.rpush(session_id, f"{role}:{content}")
        await self._redis.expire(session_id, self._ttl)

    async def clear(self, session_id: str) -> None:
        await self._redis.delete(session_id)


_store: SessionStore | None = None


def get_session_store() -> SessionStore:
    global _store
    if _store is None:
        settings = get_settings()
        if settings.redis_url:
            _store = RedisSessionStore(settings.redis_url, settings.session_ttl_seconds)
        else:
            _store = InMemorySessionStore()
    return _store
