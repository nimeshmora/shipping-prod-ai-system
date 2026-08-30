"""Shared state, so more than one container can agree on the truth.

Week 03 built a rate limiter in a module-level dict. Week 05 built a monitor
window in a deque. Both were honest for one container, and both quietly become
wrong the moment the platform scales you out - which Cloud Run does by default:

    RATE_LIMIT_PER_MIN=20 across 5 instances is really a 100/min limit,
    because each container counts to 20 on its own.

    /metrics reports whichever container the load balancer happened to route
    your request to, so the same agent can look healthy and broken depending
    on which answer you get.

The fix is not clever, it is just shared: put the counter somewhere every
container can see. Redis is already here for sessions (Week 02), so there is
no new infrastructure to run - only a decision about WHERE state lives.

Same shape as memory.py: one small interface, two implementations behind it.
With REDIS_URL set you get the shared one. Without it you get an in-process
one, so the course still runs on a laptop with no Redis and no internet - and
so the tests stay fast and deterministic.
"""
import json
import os
import time
from collections import defaultdict, deque

REDIS_URL = os.environ.get("REDIS_URL")

_client = None
_local_hits = defaultdict(deque)
_local_turns = deque(maxlen=1000)


def _redis():
    global _client
    if _client is None and REDIS_URL:
        import redis
        _client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    return _client


def available():
    """True when state is shared across containers."""
    return _redis() is not None


# ---- rate limiting ---------------------------------------------------------
def hit_count(caller, window_seconds=60):
    """Record one request from `caller` and return how many it has made
    inside the window. The caller decides whether that is too many.

    The Redis path uses a sorted set of timestamps rather than a plain INCR
    counter. An INCR on a per-minute key is a FIXED window: a caller can send
    the full allowance at 11:59:59 and the full allowance again at 12:00:00,
    so a 20/min limit permits 40 requests in one second. A sorted set gives a
    SLIDING window - it counts what actually happened in the last 60 seconds.
    """
    now = time.time()
    r = _redis()
    if r is None:
        window = _local_hits[caller]
        while window and now - window[0] > window_seconds:
            window.popleft()
        window.append(now)
        return len(window)

    key = f"rate:{caller}"
    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, now - window_seconds)   # drop what expired
    pipe.zadd(key, {f"{now}:{os.getpid()}": now})         # record this request
    pipe.zcard(key)                                       # how many remain
    pipe.expire(key, window_seconds + 1)                  # let idle keys die
    return pipe.execute()[2]


def reset_rate_limits():
    _local_hits.clear()
    r = _redis()
    if r is not None:
        for key in r.scan_iter("rate:*"):
            r.delete(key)


# ---- the monitor window ----------------------------------------------------
# One trimmed list of recent turns, shared by every container. Note the honest
# limit: this is still a rolling sample your app computes for itself. At real
# volume you ship the JSON lines from trace.py to a log platform and compute
# these numbers there. This teaches the idea and stays correct across
# containers, which is the part Week 07's load test exposes.
_TURNS_KEY = "monitor:turns"


def push_turn(record, window):
    r = _redis()
    if r is None:
        _local_turns.append(record)
        while len(_local_turns) > window:
            _local_turns.popleft()
        return
    pipe = r.pipeline()
    pipe.lpush(_TURNS_KEY, json.dumps(record))
    pipe.ltrim(_TURNS_KEY, 0, window - 1)     # keep only the newest `window`
    pipe.expire(_TURNS_KEY, 86400)
    pipe.execute()


def recent_turns(window):
    r = _redis()
    if r is None:
        return list(_local_turns)[-window:]
    raw = r.lrange(_TURNS_KEY, 0, window - 1)
    out = []
    for item in raw:
        try:
            out.append(json.loads(item))
        except json.JSONDecodeError:
            continue      # a malformed line must not break /metrics
    return out


def reset_turns():
    _local_turns.clear()
    r = _redis()
    if r is not None:
        r.delete(_TURNS_KEY)
