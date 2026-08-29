"""Week 05: one JSON trace per turn, so you can see what happened.

A trace is a plain dict you fill in during a turn and print as one JSON line at
the end. Later weeks read these to find bugs and to confirm the fallback fired.
Secrets are redacted before anything is written.
"""
import json
import os
import time
import uuid

# Week 05: what did this turn actually cost?
# Rough dollars per 1M tokens for the primary model. Not billing-accurate - the
# point is that every turn carries a number you can sum by user, per day.
COST_PER_1M_INPUT = float(os.environ.get("COST_PER_1M_INPUT", "3.00"))
COST_PER_1M_OUTPUT = float(os.environ.get("COST_PER_1M_OUTPUT", "15.00"))

_REDACT = ("api_key", "apikey", "token", "secret", "password", "authorization")


def new_trace(session_id):
    return {
        "turn_id": uuid.uuid4().hex,
        "session_id": session_id,
        "started_at": time.time(),
        "steps": 0,
        "token_count": 0,
        "tools_used": [],
        "tool_errors": [],        # tools that blew up - the model still sees the text
        "step_ms": [],            # how long each trip round the loop took
        "tool_ms": [],            # how long each tool call took
        "tool_output_filtered": False,
        "model_calls": [],
        "error": None,
        "cost_usd": 0.0,
    }


def estimate_cost(tokens):
    """A blended estimate from the turn's total token count.

    Group these by session_id and you have cost per user - the question every
    business asks about an agent, answerable because Week 05 wrote it down.
    """
    blended = (COST_PER_1M_INPUT + COST_PER_1M_OUTPUT) / 2
    return round((tokens / 1_000_000) * blended, 6)


# keys that are counters, not secrets, even though they contain a redact word
_ALLOW = {"token_count", "tokens", "cost_usd"}


def _redact(value):
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if k in _ALLOW:
                out[k] = _redact(v)
            elif any(s in k.lower() for s in _REDACT):
                out[k] = "[redacted]"
            else:
                out[k] = _redact(v)
        return out
    if isinstance(value, list):
        return [_redact(v) for v in value]
    return value


def emit(trace):
    """Finish and print the trace as one JSON line to stdout.

    Two of these fields are not for you - they are for the log platform.
    Cloud Run (and most log tools) read stdout, and they look for a field
    called "severity" to decide whether a line is routine or a problem.
    Without it every line lands as INFO, so a failed turn looks exactly like
    a successful one in the console and nothing ever pages anybody.
    """
    trace["duration_ms"] = round((time.time() - trace["started_at"]) * 1000)
    trace["cost_usd"] = estimate_cost(trace.get("token_count", 0))
    trace["severity"] = "ERROR" if trace.get("error") else "INFO"
    trace["message"] = (f"turn {trace['turn_id'][:8]} "
                        f"{'failed' if trace.get('error') else 'ok'} "
                        f"in {trace['duration_ms']}ms")
    print(json.dumps(_redact(trace)))
    return trace
