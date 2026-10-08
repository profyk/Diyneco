"""Fixed-window rate limits per principal and per IP (API spec, Conventions).

Redis when REDIS_URL is set; otherwise an in-process counter, which is allowed only in
development (settings refuse to start elsewhere without Redis).
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Protocol

from redis.asyncio import Redis

LIMITS: dict[str, tuple[int, int]] = {
    # bucket: (requests, window seconds)
    "auth_ip": (10, 60),
    "staff": (600, 60),
    "device": (120, 60),
}


@dataclass(frozen=True)
class RateDecision:
    allowed: bool
    limit: int
    remaining: int
    reset_s: int


class RateLimiter(Protocol):
    async def hit(self, bucket: str, key: str) -> RateDecision: ...
    async def reset(self) -> None: ...


class MemoryRateLimiter:
    def __init__(self) -> None:
        self._counts: dict[tuple[str, str, int], int] = {}
        self._lock = asyncio.Lock()

    async def hit(self, bucket: str, key: str) -> RateDecision:
        limit, window = LIMITS[bucket]
        now = time.time()
        slot = int(now // window)
        async with self._lock:
            k = (bucket, key, slot)
            self._counts[k] = self._counts.get(k, 0) + 1
            count = self._counts[k]
            if len(self._counts) > 50_000:  # drop old windows
                self._counts = {kk: v for kk, v in self._counts.items() if kk[2] >= slot - 1}
        reset = int((slot + 1) * window - now) + 1
        return RateDecision(count <= limit, limit, max(0, limit - count), reset)

    async def reset(self) -> None:
        async with self._lock:
            self._counts.clear()


class RedisRateLimiter:
    def __init__(self, url: str) -> None:
        self._redis = Redis.from_url(url)

    async def hit(self, bucket: str, key: str) -> RateDecision:
        limit, window = LIMITS[bucket]
        now = time.time()
        slot = int(now // window)
        redis_key = f"rl:{bucket}:{key}:{slot}"
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.incr(redis_key)
            pipe.expire(redis_key, window + 5)
            count, _ = await pipe.execute()
        reset = int((slot + 1) * window - now) + 1
        return RateDecision(int(count) <= limit, limit, max(0, limit - int(count)), reset)

    async def reset(self) -> None:  # used by tests only
        await self._redis.flushdb()


def build_rate_limiter(redis_url: str | None) -> RateLimiter:
    return RedisRateLimiter(redis_url) if redis_url else MemoryRateLimiter()
