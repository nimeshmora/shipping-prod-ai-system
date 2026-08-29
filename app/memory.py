"""Conversation memory.

load(session_id) and save(session_id, history) are the only names the app knows.
Week 01 uses the in-process dict. Week 04 trims history so it cannot grow
forever. Week 02 sets REDIS_URL and the same two
functions store in Redis instead, surviving restarts. Nothing else changes.
"""
import json
import os

REDIS_URL = os.environ.get("REDIS_URL")
TTL_SECONDS = int(os.environ.get("SESSION_TTL", 60 * 60 * 24))

# Week 04: context is a budget, not a container.
# Every turn sends the WHOLE history back to the model. Left alone, a long
# session grows the prompt until the model refuses it - and the per-turn token
# cap never sees this coming, because it is reset at the start of each turn.
# So we keep only the most recent messages. This is the cheapest possible
# strategy on purpose; summarising the dropped turns is the real-world upgrade.
MAX_HISTORY_MESSAGES = int(os.environ.get("MAX_HISTORY_MESSAGES", "40"))

_client = None
_FALLBACK = {}


def _redis():
    global _client
    if _client is None and REDIS_URL:
        import redis
        _client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    return _client


def trim(history):
    """Keep the last MAX_HISTORY_MESSAGES messages, without splitting a turn.

    A tool_use block and its tool_result must stay together, so if the cut
    would land on a tool result we step back one more message.
    """
    if len(history) <= MAX_HISTORY_MESSAGES:
        return history
    cut = len(history) - MAX_HISTORY_MESSAGES
    while cut < len(history) and _is_tool_result(history[cut]):
        cut += 1
    return history[cut:]


def _is_tool_result(msg):
    content = msg.get("content")
    return isinstance(content, list) and any(
        isinstance(b, dict) and b.get("type") == "tool_result" for b in content)


def _serialise(history):
    plain = []
    for msg in history:
        content = msg["content"]
        if isinstance(content, list):
            content = [b if isinstance(b, dict) else getattr(b, "model_dump", lambda: b)()
                       for b in content]
        plain.append({"role": msg["role"], "content": content})
    return json.dumps(plain)


def load(session_id):
    r = _redis()
    if r is None:
        return _FALLBACK.get(session_id, [])
    raw = r.get(f"session:{session_id}")
    return json.loads(raw) if raw else []


def save(session_id, history):
    history = trim(history)          # Week 04: bound the context
    r = _redis()
    if r is None:
        _FALLBACK[session_id] = history
        return
    r.setex(f"session:{session_id}", TTL_SECONDS, _serialise(history))
