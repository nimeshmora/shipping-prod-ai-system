"""Conversation memory. Week 01 built this over a dict. WEEK 02 REPLACES IT.

You have just watched a redeploy erase every conversation. Nothing crashed -
the deployment SUCCEEDED, Cloud Run replaced the container, and `_STORE` went
with it. Fix that here.

The rule that matters
---------------------
Anything a request needs to remember has to live outside the process that
serves it. That sentence is most of what "stateless service" means, and it is
why this file is the only one you touch this week.

The constraint
--------------
`load(session_id)` and `save(session_id, history)` KEEP THEIR NAMES AND
SIGNATURES. app/main.py already calls them and must not be edited. Week 01 put
that seam here on purpose; this week is the payoff. Designing the seam before
you need it is most of what makes a change cheap later.

Storage becomes a setting, not a rewrite:

    REDIS_URL unset  ->  the in-process dict below. Local dev, tests, and a
                         laptop on a plane all keep working.
    REDIS_URL set    ->  Redis, which survives a redeploy.

Both paths have to work. A course that only runs with Redis installed is a
course nobody finishes.

What to build
-------------
1. Read the settings from the environment:

       REDIS_URL    = os.environ.get("REDIS_URL")
       TTL_SECONDS  = int(os.environ.get("SESSION_TTL", 60 * 60 * 24))

2. A lazy `_redis()` that builds ONE client, the first time it is needed:

       import redis
       redis.Redis.from_url(REDIS_URL, decode_responses=True)

   Lazily, because importing this module must not require a running Redis -
   the tests and the checkpoints have none. Once, because building a
   connection pool per request is a good way to run out of file descriptors
   under load. `decode_responses=True` gives you str back instead of bytes,
   so json can read it directly.

3. Namespace the keys: `session:<session_id>`.

   Redis is one flat keyspace, and you will eventually share it with something
   else. A bare session id tells the next person nothing.

4. `save()` must use SETEX - the value AND its expiry in one call:

       r.setex(key, TTL_SECONDS, serialised)

   Not SET followed by EXPIRE. A crash between those two calls leaves a
   session that never expires, and a dict that grows forever is exactly the
   problem you came here to fix - Redis would just do it with a bill attached.

5. `load()` returns [] for a session it has never seen. Not None - main.py
   passes the result straight to run_turn as a list.

6. Serialising the history is the part that will bite you.

   json.dumps cannot write the history as-is. Assistant messages hold content
   BLOCKS, and those arrive in three different shapes:

       dict              a tool_result your own loop built
       pydantic model    a real block from the SDK - has .model_dump()
       SimpleNamespace   a block from the fake model your tests use

   Handle all three. Handle only the pydantic case and you get the worst kind
   of bug: every test passes (they use SimpleNamespace), and it fails the
   moment a real model answers in production.

7. Keep `reset()` working for the tests, clearing both the dict and any
   `session:*` keys in Redis.

Add `redis` to requirements.txt.

Done when
---------
    make check-week-02

Then deploy, start a conversation, redeploy, and continue it. Before this
change it forgets. After it, it does not.

Stuck? git diff week-02-deploy..week-02-solution -- app/memory.py
"""
import os

# --- Week 01's implementation. Replace it. ---------------------------------
# Left here so the app keeps running while you work. It is also the fallback
# you keep for when REDIS_URL is unset - do not delete it, move it behind the
# same two functions.

_STORE = {}


def load(session_id):
    """Everything said so far in this session, oldest first."""
    return _STORE.get(session_id, [])


def save(session_id, history):
    _STORE[session_id] = history


def reset():
    """Used by the tests, so one test cannot leak into the next."""
    _STORE.clear()
