# Week 5 · See

**Goal:** be able to answer "is it healthy right now, and if not, what changed?"

**You start from:** a bounded, locked-down, auto-deploying agent you cannot see
inside.

**You end with:** one JSON trace per turn, a `/metrics` endpoint that alerts in
plain English, and the same traces in Grafana.

---

## The one thing to understand

**A broken agent still returns 200 OK.**

Nothing crashes. No exception, no 500, no red graph. The answers just quietly get
worse: the loop takes more steps, tools start failing and the model apologises
instead, the bill creeps up, the slow tail grows.

None of that shows up in an HTTP status code. It only shows up if something is
watching the **shape** of your turns over time.

This is the single biggest difference between operating an agent and operating an
ordinary service, and it is why this week exists.

---

## Two halves, deliberately separate

### Half 1 — Write: `app/trace.py`

One JSON line per turn, printed to stdout. Cloud Run and every log platform read
stdout, so "printing" *is* shipping telemetry.

What goes in it, and why each field earns its place:

| Field | Answers |
|---|---|
| `steps`, `token_count` | how hard did the model work |
| `input_tokens`, `output_tokens` | what did it actually cost (they price differently) |
| `tools_used`, `tool_errors` | which tools ran, which broke |
| `step_ms`, `tool_ms` | **where the time went** |
| `cost_usd` | group by `session_id` → cost per user |
| `error`, `severity` | did it fail, and should anyone be paged |

Three details that are bugs if you miss them:

**`step_ms` and `tool_ms` are separate.** "This turn took 8 seconds" is useless
on its own. You need to know whether the model was slow or *your* tool was slow,
because those have completely different fixes.

**`tool_errors` exists at all.** A tool that fails hands its error text back to
the model, which apologises politely — and the turn returns 200. This is the only
place that breakage is visible.

**`severity` is not for you, it is for the log platform.** Cloud Logging reads
that exact field to decide whether a line is routine. Without it, every line
lands as INFO, a failed turn looks identical to a successful one, and nothing
ever pages anybody.

Also: **redact secrets before writing**, and note the trap — `_REDACT` matches on
*substring*, so `input_tokens` gets caught by a rule meant for `api_token`. Fail
safe by default, then allow the counters through explicitly.

Cost uses the **input/output split**, not a blended average. Output tokens cost
3–5× input. A long-context agent is mostly input tokens, so a blended rate
overstates it several times over — and then nobody trusts the number.

### Half 2 — Read: `app/monitor.py`

Telemetry is a pile of lines. **Monitoring is a question you can answer at 3am.**

Six numbers over a rolling window:

```
error_rate       turns that failed outright
tool_error_rate  turns where YOUR tool broke - the turn still "succeeded"
p95_duration     the slow tail users actually feel
avg_steps        creeping up = the model is flailing, looping, confused
avg_cost         creeping up = longer contexts or more tool calls
turns            how much data these numbers are based on
```

`alerts()` turns thresholds into English, and `/metrics` serves it.

**`alerts()` stays silent below 10 turns.** Two failures out of three is a
coincidence, not an incident. An alerting system that cries wolf gets muted, and
a muted alert is worse than none.

**`/metrics` is not `/health`.** Wire a platform health check to `/metrics` and a
raised error rate pulls *every container* out of service at once — turning a
degraded service into no service. `/health` is for the scheduler; `/metrics` is
for humans and alerts.

---

## The bug that makes your dashboard lie

This is the most important twelve lines of the week:

```python
except Exception as e:
    t["error"] = f"{type(e).__name__}: {e}"
    raise HTTPException(status_code=500, detail="internal error") from e
finally:
    trace.emit(t)
    monitor.record(t)
```

Leave out that `except` and the exception escapes **before the trace is filled**.
The turn is recorded with `"error": null`. So during a total outage — every
single request failing — `/metrics` cheerfully reports a **0% error rate**.

Your dashboard lies to you at exactly the moment you need it most. The
checkpoint tests for this specifically.

---

## Then: the same trace, in the industry's shape

`app/otel.py` publishes what you already built as OpenTelemetry spans:

```
our trace dict  ->  a SPAN            (one unit of work, with a duration)
turn_id         ->  trace_id          (ties a turn's spans together)
each loop step  ->  a child span
each tool call  ->  a child span
cost, tokens    ->  span attributes
error           ->  span status
print(json)     ->  an exporter
```

Same information, a format Grafana, Jaeger, Honeycomb, Datadog and Cloud Trace
all read. Look at it locally:

```bash
make trace-ui                                    # grafana + tempo
export OTEL_ENABLED=1
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
make run
# then http://localhost:3000 -> Explore -> Tempo -> Search
```

In production you already have Cloud Trace, so it is two env vars:
`OTEL_ENABLED=1`, `OTEL_TARGET=gcp`.

**That is the whole promise of OpenTelemetry: you instrument once, and the
destination becomes a setting rather than a rewrite.** It is off by default, so
the course keeps working with no cloud and no internet.

---

## Do this

```bash
make run
# make a few requests, then watch the JSON lines in the terminal

curl -s localhost:7000/metrics | python -m json.tool
```

Then **break it on purpose** and watch `/metrics` notice:

```bash
export MODEL=this-model-does-not-exist
make run
# make a dozen requests
curl -s localhost:7000/metrics | python -m json.tool
# status: degraded, and an alert saying turns are failing
```

Find the slow part of a real turn in Grafana. That skill is what Week 6 is
built on.

---

## Check it works

```bash
make check-week-05
```

---

## Done when

- Every request prints one JSON line with steps, tools, tokens and `cost_usd`
- Secrets are redacted; the token counters are not
- A failed turn is `severity: ERROR`
- `/metrics` turns `degraded` with a plain-English alert
- A **total outage** reports a 100% error rate, not 0%
- A broken tool alerts even though every turn returned 200
- `make check-week-05` passes

---

## Think about

1. Your provider returns one 429. What happens right now? *(Week 6 — and the
   obvious fix is the wrong one.)*
2. `avg_steps` is creeping up over a week. How would you find out *why*?
   *(Week 6's debugging exercise.)*
3. `/metrics` describes whichever container answered you. You are running five.
   *(Week 7.)*
