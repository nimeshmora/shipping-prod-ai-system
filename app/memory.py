"""Conversation memory.

`load(session_id)` and `save(session_id, history)` are the only two names the
rest of the app knows. That is deliberate, and it is the point of this file.

Right now they are backed by a dict in this process. In Week 02 you deploy,
watch that dict die on every redeploy, and swap it for Redis - and because the
interface is these two functions, nothing else in the codebase changes.

Designing the seam before you need it is most of what makes a change cheap
later.
"""

_STORE = {}


def load(session_id):
    """Everything said so far in this session, oldest first."""
    return _STORE.get(session_id, [])


def save(session_id, history):
    _STORE[session_id] = history


def reset():
    """Used by the tests, so one test cannot leak into the next."""
    _STORE.clear()
