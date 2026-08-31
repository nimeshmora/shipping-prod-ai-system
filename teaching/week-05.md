# Week 5 · See

**Session goal:** they leave able to answer *"is it healthy right now?"*

**Branch:** `week-05-see` → answer key `week-05-solution`

> **INSTRUCTOR** · The most important week in the course, and the one with the
> most to build. If you are going to run over on any session, run over on this
> one. If you must cut something, cut the OpenTelemetry section — it is the only
> optional part.

---

## Beat 1 · Ask (10 min)

### "How do you know a normal website is broken?"

They will say: it returns an error, the page is blank, the status code is 500,
the graph goes red.

### "How do you know an AGENT is broken?"

Let it get uncomfortable.

Then say the sentence the whole week is built on:

> **A broken agent still returns 200 OK.**

Nothing crashes. No exception. No red graph. The answers just quietly get worse:

```
the loop starts taking more steps          nobody notices
tools start failing, the model apologises  turn returns 200
the bill creeps up                         next month's problem
the slow tail grows                        only the 95th percentile feels it
```

**None of that appears in a status code.**

> **INSTRUCTOR** · *"This is the single biggest difference between running an
> agent and running an ordinary service. For a normal web app, observability is
> a nice-to-have. For an agent it is the only thing standing between you and
> guesswork."*

### "Last week's homework — what should the token limit be?"

Collect a few answers. Nobody can justify a number, because nobody has data.
*"By the end of today, you will."*

---

## Beat 2 · Break (10 min)

On the projector. Make the agent silently worse — not broken.

Break the order lookup so it returns the wrong field, or point `MODEL` at
something that fails, or make a tool return an error string.

Then send requests and show:

- `/health` — **still `ok`**
- Status codes — **still 200**
- The logs — **nothing unusual**
- The replies — **wrong, or apologetic, or missing information**

> **INSTRUCTOR** · *"Every dashboard I have is green. My agent is broken. Find
> it."*
>
> Let them try to tell you *how* they would find it. They cannot, and that is
> the point.

---

## Beat 3 · Concept (18 min)

Two halves, and keeping them separate is the lesson.

### Half 1 · Telemetry — writing it down

**Telemetry means writing down what happened.**

One line of structured text per turn, printed to the screen. And here is the
part that surprises people: **printing IS shipping telemetry.** Cloud Run, and
every log platform, read whatever your program prints. There is no special
library needed.

What goes in the line, and why each earns its place:

| Field | Answers the question |
|---|---|
| `steps`, `token_count` | how hard did the model work |
| `input_tokens`, `output_tokens` | what did it cost (they are priced differently) |
| `tools_used`, `tool_errors` | which tools ran, which broke |
| `step_ms`, `tool_ms` | **where did the time go** |
| `cost_usd` | group by session → cost per customer |
| `error`, `severity` | did it fail, should anyone be woken up |

Three details worth dwelling on:

**Time the model and the tools separately.** *"This turn took 8 seconds"* is
useless on its own. Was the model slow, or was *your* code slow? Completely
different fixes.

**`tool_errors` has to exist.** A tool that fails hands its error text back to
the model, which apologises politely — and the turn returns 200. **This is the
only place that breakage is visible.**

**`severity` is not for you. It is for the log platform.** Cloud Logging reads
that exact word to decide whether a line is routine or a problem. Leave it out
and every line files as INFO, a failed turn looks identical to a successful one,
and nothing ever pages anybody.

Also: **redact secrets before writing.** And note the trap — the redaction rule
matches on *part* of a name, so a rule meant for `api_token` also eats
`input_tokens`. Fail safe by default, then allow the counters through
deliberately.

### Half 2 · Monitoring — reading it back

**Telemetry is a pile of lines. Monitoring is a question you can answer at 3am.**

Six numbers over the recent past:

```
error_rate        turns that failed outright
tool_error_rate   turns where YOUR tool broke — the turn still "succeeded"
p95_duration      the slow tail people actually feel
avg_steps         creeping up = the model is flailing
avg_cost          creeping up = longer conversations or more tool calls
turns             how much data these numbers rest on
```

**What p95 means**, since it will come up: sort every request by how long it
took; the 95th percentile is the point where 95% were faster. Averages hide
disasters — nineteen fast requests and one catastrophic one still average out
fine. **p95 is what your unhappiest customers experience.**

Two design decisions to defend:

**Stay silent below ten turns.** Two failures out of three is a coincidence, not
an incident. *"An alerting system that cries wolf gets muted. A muted alert is
worse than no alert."*

**`/metrics` is not `/health`.** Wire a platform health check to `/metrics` and a
raised error rate pulls **every box** out of service at once — turning a degraded
service into no service. `/health` is for the machines. `/metrics` is for humans.

---

## Beat 4 · Build (45 min)

Two files: `app/trace.py` (write) and `app/monitor.py` (read), then wire them in
and add `/metrics`.

`app/otel.py` is **given** — they read it, they do not write it.

### The twelve lines that matter most

Stop the room for this one. Put it on the projector.

```python
except Exception as e:
    t["error"] = f"{type(e).__name__}: {e}"
    raise HTTPException(status_code=500, detail="internal error") from e
finally:
    trace.emit(t)
    monitor.record(t)
```

Leave out that `except` and the error escapes **before the trace is filled in**.
The turn gets recorded with `"error": null`.

So during a **total outage** — every single request failing — `/metrics`
cheerfully reports a **0% error rate**.

> **INSTRUCTOR** · Say this slowly:
>
> **"Your dashboard lies to you at exactly the moment you need it most."**
>
> The checkpoint tests for this specifically. Make sure everyone sees that test
> pass — it is the single most valuable assertion in the repo.

### Then look at the traces

```bash
make run
# make a few requests
```

The JSON lines appear in their terminal. Read one together on the projector,
field by field.

```bash
curl -s localhost:8080/metrics | python -m json.tool
```

### Then break it and watch it get noticed

```bash
export MODEL=this-model-does-not-exist
make run
# make a dozen requests
curl -s localhost:8080/metrics | python -m json.tool
```

`"status": "degraded"`, and an alert in plain English.

> **INSTRUCTOR** · Contrast with Beat 2 explicitly. *"Same broken agent. Forty
> minutes ago you had no way to find it. Now it tells you."*

### Optional · OpenTelemetry (10 min if time)

What they built is already a trace. `app/otel.py` publishes the *same
information* in the format the rest of the industry reads:

```
our trace dict   →  a SPAN (one unit of work, with a duration)
turn_id          →  trace_id (ties a turn's pieces together)
each loop step   →  a child span
each tool call   →  a child span
cost, tokens     →  labels on the span
print(json)      →  an exporter
```

```bash
make trace-ui
export OTEL_ENABLED=1
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
make run
# then open http://localhost:3000 → Explore → Tempo → Search
```

They see a turn drawn as a waterfall: the whole turn, with the model calls and
tool calls nested inside.

> **INSTRUCTOR** · The point to land: **"You instrument once, and where it goes
> becomes a setting rather than a rewrite."** Same code sends to Grafana on their
> laptop and Google Cloud Trace in production. Two environment variables.

```bash
make check-week-05
```

---

## Beat 5 · Prove (17 min)

Green checkpoint. Then, since this week gave them data, go back and answer last
week's homework.

### "Now — what should `MAX_TOKENS_PER_TURN` be?"

They look at real token counts from real turns. **That is what changed.**

Then the hooks.

### "Your provider returns a single 429. What happens right now?"

The turn fails. The customer sees an error, for something that would have worked
if you had waited half a second.

> Week 6 — *"and the obvious fix is the wrong one."*

### "`avg_steps` has been creeping up all week. How would you find out why?"

> Week 6, and they will do it with a bug you plant.

### "`/metrics` describes whichever box answered you. You are running five."

> Week 7.

## Homework

- `make check-week-05` green, deployed
- **Find the slowest turn** in their own traces and explain in one paragraph
  where the time went

> **INSTRUCTOR** · That homework is the entire skill of Week 6. Anyone who can
> do it will find the planted bug in ten minutes; anyone who cannot will need
> help. Marking it tells you who to sit next to next week.
