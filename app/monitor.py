"""Week 05b: monitoring - reading the traces, not just writing them.

Week 05 gives you one JSON line per turn. That is telemetry. Monitoring is what
turns a pile of lines into a question you can answer at 3am:

    is it healthy RIGHT NOW, and if not, what changed?

Why agents need this more than ordinary services: a broken agent usually keeps
returning 200 OK. Nothing crashes. The answers just quietly get worse, the loop
takes more steps, the fallback starts carrying every request, the bill creeps.
None of that shows up in an HTTP status code - it only shows up if something is
watching the SHAPE of your turns over time.

The four agent signals worth watching, and what a bad number usually means:

    error_rate      turns that failed outright
    tool_error_rate turns where one of YOUR tools broke - the turn still
                    "succeeded", so this is the only place it shows up
    p95_duration    the slow tail users actually feel
    avg_steps       creeping up = the model is flailing, looping, confused
    fallback_rate   above ~0 means your primary provider is struggling
    avg_cost        creeping up = longer contexts or more tool calls per turn

This keeps the last N turns in memory, which is honest for a single container
and enough to teach the idea. In production you ship the same JSON lines to a
log aggregator and compute exactly these numbers there - the concepts do not
change, only where the arithmetic happens.
"""
import os
import statistics
import time
from collections import deque

WINDOW = int(os.environ.get("MONITOR_WINDOW", "200"))

# Alert thresholds. Crossing one is not an outage, it is a "go look now".
ALERT_ERROR_RATE = float(os.environ.get("ALERT_ERROR_RATE", "0.10"))
ALERT_P95_MS = float(os.environ.get("ALERT_P95_MS", "15000"))
ALERT_FALLBACK_RATE = float(os.environ.get("ALERT_FALLBACK_RATE", "0.20"))
ALERT_AVG_STEPS = float(os.environ.get("ALERT_AVG_STEPS", "4.0"))
ALERT_TOOL_ERROR_RATE = float(os.environ.get("ALERT_TOOL_ERROR_RATE", "0.05"))

_turns = deque(maxlen=WINDOW)


def record(trace):
    """Called once per finished turn, straight after the trace is emitted."""
    used_fallback = any(c.get("provider") == "fallback"
                        for c in trace.get("model_calls", []))
    _turns.append({
        "at": time.time(),
        "error": trace.get("error") is not None,
        "tool_error": bool(trace.get("tool_errors")),
        "slowest_step_ms": max(trace.get("step_ms") or [0]),
        "duration_ms": trace.get("duration_ms", 0),
        "steps": trace.get("steps", 0),
        "cost_usd": trace.get("cost_usd", 0.0),
        "fallback": used_fallback,
        "filtered": bool(trace.get("tool_output_filtered")),
    })


def _p95(values):
    if not values:
        return 0
    if len(values) < 20:                       # too few to be meaningful
        return max(values)
    return round(statistics.quantiles(values, n=20)[-1])


def stats():
    """The current health of the agent, as numbers."""
    n = len(_turns)
    if n == 0:
        return {"turns": 0}
    durations = [t["duration_ms"] for t in _turns]
    return {
        "turns": n,
        "error_rate": round(sum(t["error"] for t in _turns) / n, 3),
        "fallback_rate": round(sum(t["fallback"] for t in _turns) / n, 3),
        "avg_steps": round(sum(t["steps"] for t in _turns) / n, 2),
        "p95_duration_ms": _p95(durations),
        "avg_duration_ms": round(sum(durations) / n),
        "avg_cost_usd": round(sum(t["cost_usd"] for t in _turns) / n, 6),
        "total_cost_usd": round(sum(t["cost_usd"] for t in _turns), 4),
        "tool_outputs_filtered": sum(t["filtered"] for t in _turns),
        "tool_error_rate": round(sum(t["tool_error"] for t in _turns) / n, 3),
        "p95_slowest_step_ms": _p95([t["slowest_step_ms"] for t in _turns]),
    }


def alerts():
    """Thresholds currently crossed, in plain English. Empty list = healthy."""
    s = stats()
    if s["turns"] < 10:                        # not enough data to judge
        return []
    out = []
    if s["error_rate"] > ALERT_ERROR_RATE:
        out.append(f"error rate {s['error_rate']:.0%} is above "
                   f"{ALERT_ERROR_RATE:.0%} - turns are failing")
    if s["p95_duration_ms"] > ALERT_P95_MS:
        out.append(f"p95 latency {s['p95_duration_ms']}ms is above "
                   f"{ALERT_P95_MS:.0f}ms - the slow tail is bad")
    if s["fallback_rate"] > ALERT_FALLBACK_RATE:
        out.append(f"fallback answered {s['fallback_rate']:.0%} of turns - "
                   f"the primary model is struggling")
    if s["tool_error_rate"] > ALERT_TOOL_ERROR_RATE:
        out.append(f"{s['tool_error_rate']:.0%} of turns had a tool fail - "
                   f"one of your tools is broken")
    if s["avg_steps"] > ALERT_AVG_STEPS:
        out.append(f"average {s['avg_steps']} steps per turn - the model is "
                   f"looping or confused")
    return out


def reset():
    _turns.clear()
