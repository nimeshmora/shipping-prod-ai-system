"""app/store.py - Week 07. BUILD THIS FILE.

Shared state, so more than one container can agree on the truth.

WHY THIS EXISTS
---------------
Week 03 built a rate limiter in a module-level dict. Week 05 built the monitor
window in a deque. Both were honest for one container, and both are quietly
wrong the moment the platform scales you out - which Cloud Run does by default:

    RATE_LIMIT_PER_MIN=20 across 5 instances is really a 100/min limit,
    because each container counts to 20 on its own.

    /metrics reports whichever container the load balancer happened to route
    you to, so the same agent can look healthy or broken depending on which
    answer you get.

A rate limit is a SECURITY CONTROL. A security control that is quietly 5x
looser than its own setting is worse than none, because you trust it.

This was left wrong for four weeks on purpose. Run `make load` BEFORE you fix
it: feeling a load test expose the gap teaches you to ask "where does this state
live?" about everything. Getting it right silently in Week 03 would have taught
you nothing.

The fix is not clever, it is just shared: put the counter somewhere every
container can see. Redis is already here for sessions (Week 02), so there is no
new infrastructure - only a decision about WHERE state lives.

Same shape as memory.py: one small interface, two implementations behind it.
With REDIS_URL set you get the shared one; without it, an in-process one, so
the course still runs on a laptop with no Redis and the tests stay fast.

What to build
-------------
    REDIS_URL   = os.environ.get("REDIS_URL")
    _redis()    lazy single client, exactly like memory.py
    available() True when state is actually shared

1. `hit_count(caller, window_seconds=60)`

   Record one request from `caller` and return how many it has made inside the
   window. The CALLER decides whether that is too many - this function just
   counts, which keeps the policy in guardrails.py where the rest of it lives.

   For the Redis path use a SORTED SET of timestamps, not a plain INCR counter.

   An INCR on a per-minute key is a FIXED window: a caller can send the full
   allowance at 11:59:59 and the full allowance again at 12:00:00, so a 20/min
   limit permits 40 requests in one second. A sorted set gives a SLIDING
   window - it counts what actually happened in the last 60 seconds.

       pipe.zremrangebyscore(key, 0, now - window_seconds)   drop what expired
       pipe.zadd(key, {unique_member: now})                  record this one
       pipe.zcard(key)                                       how many remain
       pipe.expire(key, window_seconds + 1)                  let idle keys die

   Use a pipeline, so that is one round trip rather than four. Make each member
   unique (timestamp plus pid) or two requests in the same millisecond collapse
   into one.

2. `push_turn(record, window)` and `recent_turns(window)`

   A trimmed list of recent turns, shared by every container. LPUSH then LTRIM
   to `window` entries, with an expiry. On the way back out, skip anything that
   will not parse - one malformed line must not break /metrics.

3. `reset_rate_limits()` and `reset_turns()` for the tests, clearing both the
   in-process fallbacks and any matching Redis keys.

Then rewire the two callers
---------------------------
app/guardrails.py:

    def check_rate_limit(caller):
        if store.hit_count(caller) > RATE_LIMIT:
            raise GuardrailError(f"rate limit reached ({RATE_LIMIT}/min)",
                                 status=429)

app/monitor.py: record() pushes to the store, stats() reads from it, and add a
`shared_state` field so whoever reads /metrics knows whether those numbers
describe the SERVICE or just the container that answered them.

Note the honest limit that remains: this is still a rolling sample your app
computes for itself. At real volume you ship the JSON lines from trace.py to a
log platform and compute these numbers there. The concepts do not change, only
where the arithmetic happens.

Done when
---------
    make check-week-07
    make load          # and the rate limit holds

Stuck? git diff week-07-attack..week-07-solution -- app/store.py
"""

# your code here
