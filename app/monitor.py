"""app/monitor.py - Week 05. BUILD THIS FILE.

Reading the traces, not just writing them.

app/trace.py gives you one JSON line per turn. That is TELEMETRY. Monitoring is
what turns a pile of lines into a question you can answer at 3am:

    is it healthy RIGHT NOW, and if not, what changed?

Why agents need this more than ordinary services: a broken agent keeps
returning 200 OK. Nothing crashes. The answers just get worse, the loop takes
more steps, the bill creeps. It only shows up if something is watching the
SHAPE of your turns over time.

What to build
-------------
1. A rolling window of the last WINDOW turns (env MONITOR_WINDOW, default 200).
   A `collections.deque(maxlen=WINDOW)` is all it takes. This is honest for one
   container and enough to teach the idea; Week 07 moves it into shared storage
   once a load test has shown you why.

2. `record(trace)` - called once per finished turn, straight after emit().
   Keep only what the numbers below need: error, tool_error, duration_ms,
   steps, cost_usd, slowest step.

3. `stats()` - the current health, as numbers:

       turns             how much data these numbers rest on
       error_rate        turns that failed outright
       tool_error_rate   turns where one of YOUR tools broke - the turn still
                         "succeeded", so this is the only signal that sees it
       p95_duration_ms   the slow tail users actually feel
       avg_duration_ms
       avg_steps         creeping up = the model is flailing, looping, confused
       avg_cost_usd      creeping up = longer contexts or more tool calls
       total_cost_usd

   For p95, fall back to max() below ~20 samples - a percentile of 5 points is
   theatre.

4. `alerts()` - thresholds currently crossed, in plain English. Empty list
   means healthy. Read the thresholds from the env:

       ALERT_ERROR_RATE       0.10
       ALERT_P95_MS           15000
       ALERT_AVG_STEPS        4.0
       ALERT_TOOL_ERROR_RATE  0.05

   RETURN NOTHING BELOW ~10 TURNS. Two failures out of three is a coincidence,
   not an incident. An alerting system that cries wolf gets muted, and a muted
   alert is worse than no alert.

   Write the messages for someone woken up by them: say what the number is,
   what the threshold was, and what it probably means.

5. `reset()` for the tests.

Then add GET /metrics in app/main.py
------------------------------------
    {"status": "degraded" if alerts else "ok", "alerts": [...], **stats()}

/metrics IS NOT /health. Keep them separate and resist the temptation to wire a
platform health check to this one: a raised error rate would then pull EVERY
container out of service at once, turning a degraded service into no service.
/health is for the scheduler. /metrics is for humans and alerts.

THE BUG THAT MAKES ALL OF THIS LIE
----------------------------------
In app/main.py, the handler must catch EVERY exception and record it on the
trace before re-raising:

    except Exception as e:
        t["error"] = f"{type(e).__name__}: {e}"
        raise HTTPException(status_code=500, detail="internal error") from e
    finally:
        trace.emit(t)
        monitor.record(t)

Leave that out and the exception escapes BEFORE the trace is filled, so the
turn is recorded with "error": null. During a total outage - every single
request failing - /metrics then reports a 0% error rate. Your dashboard lies to
you at exactly the moment you need it most.

The checkpoint tests for this specifically.

Done when
---------
    make check-week-05

Stuck? git diff week-05-see..week-05-solution -- app/monitor.py
"""

# your code here
