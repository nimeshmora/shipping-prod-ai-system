"""Conversation memory - now durable.

`load(session_id)` and `save(session_id, history)` are still the only two names
the rest of the app knows. That has not changed, and that is the entire point:
you swapped the storage underneath and no other file needed editing.

    REDIS_URL unset  -> a dict in this process (Week 01; still used by tests)
    REDIS_URL set    -> Redis, which survives a redeploy

Why this had to change
----------------------
Week 01's dict lived inside the container. Cloud Run replaces the container on
every deploy and can shut it down whenever traffic goes quiet, so every
conversation vanished - not on a crash, but on a *successful* release. The
service looked perfectly healthy while every customer mid-conversation was
silently reset.

Anything a request needs to remember has to live outside the process that
serves it. That sentence is most of what "stateless service" means.

Two things Redis gives you that a dict cannot
---------------------------------------------
1. It is shared. Two containers serving the same user see the same history,
   which matters the moment the platform scales you past one instance.
2. It expires. A dict grows until the process dies; SETEX drops a session
   after SESSION_TTL, so abandoned conversations clean themselves up instead
   of becoming a slow memory leak with a bill attached.
"""
import json
import os

REDIS_URL = os.environ.get("REDIS_URL")

# How long an idle conversation lives. A day is a reasonable default for
# support chat: long enough to come back after lunch, short enough that you are
# not storing last month's conversations forever.
TTL_SECONDS = int(os.environ.get("SESSION_TTL", 60 * 60 * 24))

_client = None
_FALLBACK = {}


def _redis():
    """Connect lazily, once.

    Lazily, because importing this module must not require a running Redis -
    the tests, the checkpoints and `make run` on a laptop all work without one.
    Once, because building a connection pool per request is a good way to run
    out of file descriptors under load.
    """
    global _client
    if _client is None and REDIS_URL:
        import redis
        # decode_responses gives us str back instead of bytes, so the json
        # module can read it directly.
        _client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    return _client


def _key(session_id):
    # Namespace every key. Redis is one flat keyspace, usually shared with
    # something else eventually, and "session:abc" tells the next person what
    # they are looking at.
    return f"session:{session_id}"


def _block_to_dict(block):
    """One content block as something json.dumps will accept.

    Three shapes turn up here and all three have to work:

      dict              a tool_result we built ourselves
      pydantic model    a real block from the SDK - has .model_dump()
      SimpleNamespace   a block from a fake model in the tests

    Getting this wrong is a bug you only see in production, because the tests
    use the third shape and the SDK returns the second. Handle all of them.
    """
    if isinstance(block, dict):
        return block
    dump = getattr(block, "model_dump", None)
    if callable(dump):
        return dump()
    # SimpleNamespace and anything else with a __dict__
    return dict(vars(block))


def _serialise(history):
    """Turn the history into JSON.

    The awkward part: assistant messages hold content blocks that are objects,
    not dicts, and json.dumps refuses them outright. They get converted here
    rather than in the agent loop, because the loop should not have to know
    that something downstream wants to write it to a database.
    """
    plain = []
    for msg in history:
        content = msg["content"]
        if isinstance(content, list):
            content = [_block_to_dict(b) for b in content]
        plain.append({"role": msg["role"], "content": content})
    return json.dumps(plain)


def load(session_id):
    """Everything said so far in this session, oldest first."""
    r = _redis()
    if r is None:
        return _FALLBACK.get(session_id, [])
    raw = r.get(_key(session_id))
    return json.loads(raw) if raw else []


def save(session_id, history):
    r = _redis()
    if r is None:
        _FALLBACK[session_id] = history
        return
    # SETEX, not SET: write the value and its expiry in one round trip. Setting
    # them separately means a crash between the two calls leaves a session that
    # never expires.
    r.setex(_key(session_id), TTL_SECONDS, _serialise(history))


def reset():
    """Used by the tests, so one test cannot leak into the next."""
    _FALLBACK.clear()
    r = _redis()
    if r is not None:
        for key in r.scan_iter("session:*"):
            r.delete(key)


# ---- Week 04: context is a budget, not a container -----------------------
# BUILD trim(), and call it from save().
#
# This is the bound people miss, and it is the most interesting of the three.
#
# Every turn sends the WHOLE history back to the model. So a session that has
# been going an hour sends an hour of conversation on every single request -
# until the model refuses it outright.
#
# And the per-turn token cap NEVER SEES THIS COMING, because it resets at the
# start of each turn. A 40-message session that costs a fortune per turn is
# comfortably under budget on every individual turn. The two limits look like
# they overlap. They do not.
#
# What to build:
#
#   MAX_HISTORY_MESSAGES = int(os.environ.get("MAX_HISTORY_MESSAGES", "40"))
#
#   trim(history)  -> keep the last MAX_HISTORY_MESSAGES messages
#   _is_tool_result(msg) -> True if msg["content"] is a list containing a
#                           block with type == "tool_result"
#
# Then call trim() at the top of save(), so nothing can store an unbounded
# history.
#
# THE SUBTLETY, and it is a real bug if you get it wrong:
#
#   A tool_use block and the tool_result that answers it are ONE exchange.
#   Cut between them and you have a tool result replying to nothing - which
#   providers reject as malformed. A session that grew too long would then
#   start failing EVERY request with a 400 nobody can explain.
#
#   So if the cut point lands on a tool result, step forward past it.
#
# Keep the NEWEST messages, not the oldest.
#
# This is deliberately the cheapest possible strategy. Summarising the dropped
# turns - so the agent still knows what was agreed an hour ago - is the
# real-world upgrade, and a good stretch goal.
#
# Done when:  make check-week-04
# Stuck? git diff week-04-cap..week-04-solution -- app/memory.py
