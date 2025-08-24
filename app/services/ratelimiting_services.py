import time, math
from fastapi import Request, HTTPException

class TokenBucket:
    __slots__ = ("tokens", "last_access")
    def __init__(self, tokens: float, last_access: float):
        self.tokens = tokens
        self.last_access = last_access

class RateLimitManager:
    """
    In-memory token bucket rate-limiter for FastAPI server.
    """
    def __init__(self, rate_per_second: float = 1.0, capacity: float = 20.0, idle_ttl: int = 3600):
        self.rate = float(rate_per_second)
        self.capacity = float(capacity)
        self.idle_ttl = idle_ttl
        self._buckets: dict[str, TokenBucket] = {}
        self._last_seen: dict[str, float] = {}
        self._next_sweep = time.time() + 60

    #access the bucket key based on user ID
    def generate_bucket_key(self, req: Request) -> str:
        uid = getattr(getattr(req.state, "user", None), "id", None)
        return f"user:{uid}"

    #method to clean up any idle buckets, in case user is inactive for a while
    def _clean_up_idle_buckets(self) -> None:
        now = time.time()
        if now < self._next_sweep:
            return
        self._next_sweep = now + 60
        for bucket_id, user_last_seen_at in list(self._last_seen.items()):
            if now - user_last_seen_at > self.idle_ttl:
                self._last_seen.pop(bucket_id, None)
                self._buckets.pop(bucket_id, None)

    #actual algorithm to keep track of the bucket for each user and check if they can access the resource
    def check_bucket(self, key: str, cost: float = 1.0) -> tuple[bool, int, int, int]:
        now = time.time()
        current_bucket = self._buckets.get(key)

        #the user is new to bucket so create a new bucket for user
        if current_bucket is None:
            current_bucket = TokenBucket(tokens=self.capacity, last_access=now)
            self._buckets[key] = current_bucket

        #refill bucket by elapsed time
        elapsed = now - current_bucket.last_access
        current_bucket.tokens = min(self.capacity, current_bucket.tokens + self.rate * elapsed)
        current_bucket.last_access = now

        #if the user has enough tokens in bucket, then allow the api access
        if current_bucket.tokens >= cost:
            current_bucket.tokens -= cost
            self._last_seen[key] = now
            reset_sec = int((self.capacity - current_bucket.tokens) / self.rate) if self.rate > 0 else 0
            return True, 0, int(current_bucket.tokens), reset_sec

        #user does not have enough tokens, so compute how long to wait and return that
        deficit = cost - current_bucket.tokens
        retry_after = math.ceil(deficit / max(self.rate, 1e-6))
        self._last_seen[key] = now
        return False, retry_after, int(current_bucket.tokens), retry_after

    def middleware(self, cost_getter=None, skip=None):
        """
        Middleware wrapper for FastAPI to apply token bucket rate limiting.
        cost_getter(Request): float lets you charge heavy routes more.
        skip(Request): bool lets you bypass rate limiting for certain requests.
        """
        async def _mw(request: Request, call_next):
            if skip and skip(request):
                return await call_next(request)

            key = self.generate_bucket_key(request)
            cost = float(cost_getter(request)) if cost_getter else 1.0
            allowed, retry_after, remaining, reset = self.check_bucket(key, cost)

            if not allowed:
                raise HTTPException(429, "rate_limited", headers={"Retry-After": str(retry_after)})

            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = f"{self.rate}/sec; burst={self.capacity}"
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset)
            self._clean_up_idle_buckets()
            return response
        return _mw
