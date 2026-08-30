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
        "input_tokens": 0,        # billed at a different rate to output
        "output_tokens": 0,
        "retries": 0,             # same model tried again after a blip
        "tools_used": [],
        "tool_errors": [],        # tools that blew up - the model still sees the text
        "step_ms": [],            # how long each trip round the loop took
        "tool_ms": [],            # how long each tool call took
        "tool_output_filtered": False,
        "model_calls": [],
        "error": None,
        "cost_usd": 0.0,
    }


def cost_of(input_tokens, output_tokens):
    """The turn's cost, priced the way the provider actually bills it.

    Input and output are not the same price - output is usually 3-5x dearer.
    A blended average is fine until someone asks why the bill does not match,
    and then it is a bug: an agent with long contexts and short answers is
    mostly input tokens, so a blended rate overstates it several times over.

    Group these by session_id and you have cost per user - the question every
    business asks about an agent, answerable because Week 05 wrote it down.
    """
    return round((input_tokens / 1_000_000) * COST_PER_1M_INPUT
                 + (output_tokens / 1_000_000) * COST_PER_1M_OUTPUT, 6)


def estimate_cost(tokens):
    """Blended fallback, for a turn where the provider sent no usage split.

    Kept because some gateways return only a total. Prefer cost_of().
    """
    blended = (COST_PER_1M_INPUT + COST_PER_1M_OUTPUT) / 2
    return round((tokens / 1_000_000) * blended, 6)


# keys that are counters, not secrets, even though they contain a redact word.
# Easy to get wrong: _REDACT matches on substring, so every new field with
# "token" in its name is redacted by default. That is the right default - it
# fails safe - but it means adding a counter means adding it here too.
_ALLOW = {"token_count", "tokens", "cost_usd",
          "input_tokens", "output_tokens"}


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
    # Idempotent on purpose. The streaming path finalises the trace early so
    # its `done` frame can report real numbers, and the request's finally
    # block still calls emit() to guarantee it happens at all. Whichever runs
    # first wins; the second is a no-op. Without this, every streamed turn is
    # logged twice and /metrics counts it twice.
    if trace.get("_emitted"):
        return trace
    trace["_emitted"] = True
    trace["duration_ms"] = round((time.time() - trace["started_at"]) * 1000)
    _in, _out = trace.get("input_tokens", 0), trace.get("output_tokens", 0)
    trace["cost_usd"] = (cost_of(_in, _out) if (_in or _out)
                         else estimate_cost(trace.get("token_count", 0)))
    trace["severity"] = "ERROR" if trace.get("error") else "INFO"
    trace["message"] = (f"turn {trace['turn_id'][:8]} "
                        f"{'failed' if trace.get('error') else 'ok'} "
                        f"in {trace['duration_ms']}ms")
    print(json.dumps(_redact({k: v for k, v in trace.items()
                              if not k.startswith("_")})))
    return trace
