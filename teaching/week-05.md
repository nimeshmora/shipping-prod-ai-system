# Week 5 · See

**Session goal:** they leave able to answer *"is it healthy right now?"*

**Branch:** `week-05-see` → answer key `week-05-solution`

> **INSTRUCTOR** · The most important week in the course, and the one with the
> most to build. If you are going to run over on any session, run over on this
> one. If you must cut something, cut the OpenTelemetry section — it is the only
> genuinely optional part, and it is at the end for that reason.
>
> Everything before this week built protections nobody can see. Everything after
> this week depends on being able to see. Week 6's bug hunt is impossible
> without today; Week 7's load test proves itself with today's `/metrics`.

---

## Beat 1 · Ask (10 min, no slides)

### "How do you know a normal website is broken?"

Let several people answer. You will get: it returns an error, the page is blank,
the status code is 500, the graph goes red, the pager goes off.

Write them on the board. Every single one is **something turning red**.

### "How do you know an AGENT is broken?"

Ask it, then stop talking.

**Let it get uncomfortable.** Ten seconds of silence here is worth more than any
slide. Some rooms will offer "the same things" — push back gently: *"Would
they?"*

Then say the sentence the whole week is built on:

> **A broken agent still returns 200 OK.**

Nothing crashes. No exception. No red graph. The answers just quietly get worse.

Go through the list slowly, one line at a time:

```
the loop starts taking more steps           nobody notices
tools start failing, the model apologises   turn returns 200
the model starts refusing to answer         turn returns 200
the fallback carries every request          turn returns 200
the bill creeps up                          next month's problem
the slow tail grows                         only the 95th percentile feels it
```

**None of that appears in a status code.**

> **INSTRUCTOR** · Then name the difference explicitly, because it is the reason
> this week is not just "add logging":
>
> *"This is the single biggest difference between running an agent and running
> an ordinary service. For a normal web app, observability is a nice-to-have —
> you can get a long way on error rates and a status page. For an agent it is
> the **only** thing standing between you and guesswork, because the failure
> modes do not produce errors."*

### "Last week's homework — what should the token limit be?"

Collect a few answers. Read out the best one.

Nobody can *justify* a number, because nobody has data. Some will have reasoned
well from first principles — reward that — but ask the follow-up: *"How would
you check whether you were right?"*

*"By the end of today, you will be able to."*

---

## Beat 2 · Break (10 min)

> **INSTRUCTOR** · Projector. And the crucial staging note: **make the agent
> silently worse, not broken.** If it throws, you have demonstrated the easy
> case and lost the week's point. Rehearse this one beforehand.

Pick one:

- break the order lookup so it returns the **wrong field** (delivery date where
  the status should be),
- or point `MODEL` at something that fails, so the fallback quietly carries
  everything,
- or make a tool return an error string rather than raising.

Then send half a dozen requests, and show them each of these in turn:

| What you check | What it says |
|---|---|
| `/health` | **still `ok`** |
| status codes | **still 200** |
| the logs | **nothing unusual** |
| `make test` | **still green** |
| the replies | **wrong, or apologetic, or missing information** |

Read one bad reply out loud. It will sound *fine* — polite, well-formed,
confident. That is the problem.

> **INSTRUCTOR** · Then the challenge, and mean it:
>
> *"Every dashboard I have is green. My agent is broken. Find it."*
>
> Let them actually try to tell you *how* they would find it. Take suggestions
> for two or three minutes. Every suggestion will be some version of "read the
> code" or "add print statements and redeploy" — which is exactly the position
> they will be in at 3am, and exactly what today removes.
>
> Do not fix it yet. Leave it broken and move to the concept. You will come back
> to this same broken agent at the end of Beat 4, and the contrast is the payoff.

---

## Beat 3 · Concept (18 min)

Two halves. **Keeping them separate is itself the lesson** — most people
conflate them, build only the first, and wonder why they still cannot answer any
questions.

Write the two words on the board with a line between them.

**The everyday version first**, because the two words sound like synonyms and
are not:

```
   TELEMETRY                          MONITORING
   ─────────                          ──────────
   the till receipt for every         "how were sales this week,
   sale in a shop                      and is anything wrong?"

   one per event                      one answer, over many events
   written as it happens              read when you want to know
   useless to read all of             useless without the receipts
```

**A shop with no receipts cannot answer any question about its week.** A shop
with a shoebox full of receipts and nobody adding them up also cannot — it just
*feels* more organised.

You need both, and they are different jobs: **writing it down** and **reading it
back**.

> **INSTRUCTOR** · The reason this distinction earns board space: almost every
> team builds the first half, calls it observability, and is genuinely surprised
> when an incident is still guesswork. *"You have the receipts. Nobody is adding
> them up."*

### Half 1 · Telemetry — writing it down

**Telemetry means writing down what happened.**

One line of structured text per turn, printed to the screen.

#### First — what "structured" means (3 min)

They have all seen logs. Almost none of them have seen the distinction that
makes logs useful, and it takes two minutes to show.

**An ordinary log line** is a sentence for a human:

```
turn finished in 8400ms with 3 steps, cost about 2 cents
```

Fine to read. **Impossible to compute with.** To answer *"what was the average
cost yesterday?"* you would have to pull that number back out of English.

**A structured log line** is the same facts as JSON — the format from Week 1:

```json
{"turn_id": "a3f", "duration_ms": 8400, "steps": 3, "cost_usd": 0.021}
```

Now it is data. Have them prove it, using the pipe and `json.tool` they already
know:

```bash
echo '{"duration_ms": 8400, "steps": 3}' | python -m json.tool
```

> **INSTRUCTOR** · The one-sentence version, worth saying exactly: **"Write logs
> for a program to read, and a human can always read them too. Write logs for a
> human, and no program ever can."**
>
> That is the entire justification for the trace dict, and once they have it the
> field-by-field table below stops feeling like bureaucracy.

And here is the part that genuinely surprises people, so pause on it:

**Printing IS shipping telemetry.**

Cloud Run — and every log platform in existence — reads whatever your program
prints to standard output. There is no agent to install, no library to import,
no endpoint to configure. `print(json.dumps(...))` is a production telemetry
pipeline.

> **INSTRUCTOR** · This deflates a lot of anxiety. Students assume observability
> means buying something. *"The expensive tools are for querying it at scale.
> Getting the data out is one line."*

#### What goes in the line, and why each field earns its place

Do not just show the dict. Go field by field and ask *what question does this
answer?* — a field that answers no question is a field to delete.

| Field | Answers the question |
|---|---|
| `turn_id`, `session_id` | which turn, whose conversation |
| `steps`, `token_count` | how hard did the model work |
| `input_tokens`, `output_tokens` | what did it cost (**priced differently**) |
| `tools_used`, `tool_errors` | which tools ran, which broke |
| `step_ms`, `tool_ms` | **where did the time go** |
| `retries`, `model_calls` | did the provider wobble (Week 6 fills these) |
| `cost_usd` | group by session → **cost per customer** |
| `error`, `severity` | did it fail, should anyone be woken up |

#### Four details worth dwelling on

**Time the model and the tools separately.**

*"This turn took 8 seconds"* is useless on its own. Was the model slow, or was
*your* code slow? Those have completely different fixes — one is a provider
conversation or a smaller prompt, the other is your database.

```python
"step_ms": [1840, 2130, 900],     # each trip round the loop
"tool_ms": [12, 4100],            # each tool call  <- there it is
```

> **INSTRUCTOR** · Point at that second array. *"Four seconds in a tool call.
> You would never have found that from a total."* This exact reading skill is
> what Week 6 asks them to do under pressure.

**`tool_errors` has to exist as its own field.**

This is the most agent-specific field in the trace. A tool that fails hands its
error text back to the model — look at `run_tool`, it returns `"tool error: ..."`
as a *string* — and the model reads it, apologises politely, and finishes the
turn. The turn returns **200**.

**This is the only place that breakage is visible.** Nowhere else in the entire
system does a broken tool leave a mark.

**`severity` is not for you. It is for the log platform.**

Cloud Logging reads that exact field name and that exact word to decide whether
a line is routine or a problem. Leave it out and every line files as INFO — a
failed turn looks identical to a successful one in the console, filters do not
work, and **nothing ever pages anybody.**

```python
trace["severity"] = "ERROR" if trace.get("error") else "INFO"
```

> **INSTRUCTOR** · The general principle is worth naming: *"Some fields are for
> humans reading, and some are protocol — a specific word a specific system is
> looking for. Knowing which is which is most of what makes logging useful
> rather than decorative."*

**Redact secrets before writing.**

And note the trap, which is a genuinely good bug to think about: the redaction
rule matches on *part* of a name, so a rule meant for `api_token` also eats
`input_tokens`.

```python
_REDACT = ("api_key", "apikey", "token", "secret", "password", "authorization")
_ALLOW  = {"token_count", "tokens", "cost_usd", "input_tokens", "output_tokens"}
```

**Fail safe by default, then allow the counters through deliberately.** The
default has to be "redact it" — a new field with `token` in the name should
disappear until someone thinks about it, not leak until someone notices.

> **INSTRUCTOR** · Ask which way round they would have written it. Most people
> write an explicit deny-list and a permissive default, which is exactly
> backwards, and it is the reason keys end up in logs. *"Defaults decide what
> happens on the day nobody was paying attention. Point them at safe."*

### Half 2 · Monitoring — reading it back

**Telemetry is a pile of lines. Monitoring is a question you can answer at 3am.**

The distinction matters because a pile of lines feels like progress and answers
nothing. Nobody greps a million JSON lines during an incident.

Six numbers, computed over the recent past:

```
error_rate        turns that failed outright
tool_error_rate   turns where YOUR tool broke — the turn still "succeeded"
p95_duration      the slow tail people actually feel
avg_steps         creeping up = the model is flailing
avg_cost          creeping up = longer conversations or more tool calls
turns             how much data these numbers rest on
```

Each one is a *shape* of failure that no status code has.

**What p95 means**, since it will come up and half the room is guessing:

Sort every request by how long it took. The 95th percentile is the point where
95% were faster and 5% were slower.

```
        ▁▁▁▂▂▂▂▃▃▃▃▃▄▄▄▄▄▄▅▅▅▅▆▆▇▇█████████████
        └──────────── 95% of requests ────────┘ └─ p95 ─┘
                                                  ▲
                                   this is what your angriest
                                       customers experience
```

**Averages hide disasters.** Nineteen fast requests and one catastrophic one
still average out fine. The average is the number that tells you everything is
OK while a fifth of your users are furious.

**Do not assert that — show it.** Have them run this:

```bash
python -c "
import statistics
d = [100]*19 + [9000]          # 19 fast requests, 1 disaster
print('average:', round(sum(d)/len(d)))
print('p95    :', round(statistics.quantiles(d, n=20)[-1]))
"
```

```
average: 545
p95    : 8555
```

**Same twenty requests. One number says half a second, the other says eight and
a half.** One of those two numbers would have you sleeping soundly while a
customer waits nine seconds.

> **INSTRUCTOR** · Ask which number a dashboard usually shows by default. It is
> the average, essentially everywhere, and that is worth being annoyed about.
>
> Then have them change `[100]*19` to `[100]*99` — one bad request in a hundred
> instead of one in twenty:
>
> ```
> average: 189
> p95    : 100
> ```
>
> **The p95 now hides it too.** The nine-second request is still there, still
> happening to a real person, and both numbers say everything is fine.
>
> **No single number catches everything** — which is the honest lesson, and the
> reason `/metrics` returns six of them rather than one. It is also why the trace
> of every individual turn still matters: aggregates are for noticing, and
> individual traces are for finding.

> **INSTRUCTOR** · If the room is quantitative, the one-liner is: *"The average
> is a number about your service. The p95 is a number about your customers."*

#### Two design decisions to defend

**Stay silent below ten turns.**

```python
if s["turns"] < 10:
    return []                  # not enough data to judge
```

Two failures out of three is a coincidence, not an incident.

> **INSTRUCTOR** · *"An alerting system that cries wolf gets muted. A muted
> alert is worse than no alert, because you still believe you have one."*
>
> This is worth a minute of real discussion — ask if anyone has worked
> somewhere with an alert channel nobody reads. Usually two or three hands.

**`/metrics` is not `/health`.**

They are different endpoints for different audiences and they must never be
wired together.

```
/health   → for machines.  "Is this process running?"  Boring on purpose.
/metrics  → for humans.    "Is this service healthy?"  Rich, and slow to judge.
```

Wire a platform health check to `/metrics` and a raised error rate pulls **every
box** out of service at once — turning a degraded service into no service at all.
You would have built an outage amplifier.

> **INSTRUCTOR** · This comes back verbatim in Week 8 as Kubernetes readiness vs
> liveness. Flag it forward: *"Remember this shape. It has a name, and you will
> meet it again in the last session."*

---

## Beat 4 · Build (45 min)

Two files they write — `app/trace.py` (write it down) and `app/monitor.py` (read
it back) — then wire them into `app/main.py` and add `/metrics`.

`app/otel.py` is **given**. They read it; they do not write it.

> **INSTRUCTOR** · Say that split out loud at the start of the build, or someone
> will spend twenty minutes on the file they were not meant to touch.

### The twelve lines that matter most

**Stop the room for this one.** Everyone's hands off keyboards. Put it on the
projector.

```python
try:
    reply, history, t = run_turn(...)
except Exception as e:
    t["error"] = f"{type(e).__name__}: {e}"
    raise HTTPException(status_code=500, detail="internal error") from e
finally:
    trace.emit(t)
    monitor.record(t)
```

Walk them through what happens **without** that `except` clause.

The exception escapes. It propagates out of the function. And it does so
**before the trace is filled in** — so the turn gets recorded, by the `finally`,
with `"error": null`.

Now follow the consequence all the way down:

```
every request fails
    ↓
every trace records  "error": null
    ↓
monitor.record() counts every turn as a success
    ↓
/metrics reports  "error_rate": 0.0
```

So during a **total outage** — every single request failing, nothing working at
all — `/metrics` cheerfully reports a **0% error rate**.

> **INSTRUCTOR** · Say this slowly, and let it sit:
>
> **"Your dashboard lies to you at exactly the moment you need it most."**
>
> Then two follow-ups worth making explicit:
>
> **Why `finally` and not just the happy path?** Because the trace has to be
> written whether the turn succeeded, failed, or blew a budget. Telemetry you
> only get when things go well is telemetry for the case you did not need it.
>
> **Why re-raise rather than return the error text?** Week 1's rule: never let a
> raw error reach the caller. The trace gets the real error; the customer gets
> `internal error`. Both of those are deliberate, and they point in opposite
> directions on purpose.
>
> The checkpoint tests for this specifically. **Make sure everyone sees that
> test pass** — it is the single most valuable assertion in the repo.

### One more subtlety in `emit()`

Worth thirty seconds because it catches people:

```python
if trace.get("_emitted"):
    return trace
trace["_emitted"] = True
```

The streaming path finalises its trace early, so the `done` frame can report
real numbers. The request's `finally` block still calls `emit()`, to guarantee it
happens at all. Whichever runs first wins; the second is a no-op.

Without this, **every streamed turn is logged twice and `/metrics` counts it
twice** — so your error rate and your costs are quietly halved or doubled
depending on which turns streamed.

> **INSTRUCTOR** · *"Belt and braces is right. Belt and braces that double-counts
> is a bug. When you make something safe to call twice, make it safe to call
> twice."*

### Then look at the traces

```bash
make run
# make a few requests from a second terminal
```

The JSON lines appear in their terminal. **Read one together on the projector,
field by field.** Do not rush this — it is the first time they see their own
service describe itself, and the reading skill is the deliverable.

Ask, pointing at a real line:

- *"How many steps did that take?"*
- *"Where did the time go — the model or the tools?"*
- *"What did that turn cost?"*
- *"How much would a thousand of those cost?"*

Then the aggregate:

```bash
curl -s localhost:8080/metrics | python -m json.tool
```

### Then break it and watch it get noticed

**This is the moment the week pays off.** Go back to the same failure from
Beat 2.

```bash
export MODEL=this-model-does-not-exist
make run
# make a dozen requests — more than ten, or the alerts stay quiet
```

```bash
curl -s localhost:8080/metrics | python -m json.tool
```

`"status": "degraded"`, and an alert in plain English:

```
"error rate 100% is above 10% - turns are failing"
```

> **INSTRUCTOR** · Contrast with Beat 2 **explicitly**. Say the whole sentence:
>
> *"Same broken agent. Forty minutes ago you had no way to find it, and the best
> plan in the room was 'add print statements and redeploy'. Now it tells you, in
> English, without being asked."*
>
> Then have someone read the alert text out loud. The fact that it is a sentence
> and not a number is deliberate — an alert is read by a tired person at 3am.

Have them make fewer than ten requests first and notice **nothing alerts**. That
is the "stay silent below ten turns" rule doing its job, and seeing it is better
than being told.

### Optional · OpenTelemetry (10 min if time)

> **INSTRUCTOR** · Cut this first if you are short. It costs nothing to skip —
> `app/otel.py` is given and works either way, and nothing in Weeks 6–8 depends
> on them having seen Tempo.

The framing that makes this land: **they have already built a tracing system.**
They just built a private one.

`app/otel.py` publishes the *same information* in the format the rest of the
industry reads:

```
our trace dict   →  a SPAN (one unit of work, with a duration)
turn_id          →  trace_id (ties a turn's pieces together)
each loop step   →  a child span
each tool call   →  a child span
cost, tokens     →  attributes on the span
print(json)      →  an exporter
```

```bash
make trace-ui
export OTEL_ENABLED=1
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
make run
# then open http://localhost:3000 → Explore → Tempo → Search
```

They see a turn drawn as a waterfall: the whole turn, with model calls and tool
calls nested inside, each with its own duration bar.

> **INSTRUCTOR** · The point to land, and it is a big one:
>
> **"You instrument once, and where it goes becomes a setting rather than a
> rewrite."**
>
> The same code sends to Grafana on their laptop and Google Cloud Trace in
> production. Two environment variables. Nothing in `app/agent.py` knows or
> cares.
>
> That is the same seam idea from Week 2's `load`/`save`, applied to telemetry —
> and if you have time, say so. Students who spot the repeated pattern have
> learned the actual transferable thing.

```bash
make check-week-05
```

---

## Beat 5 · Prove (17 min)

Green checkpoint.

Then, because this week finally gave them data, **go back and answer last week's
homework properly**. This is the most satisfying loop-closing in the course —
do not skip it for time.

### "Now — what should `MAX_TOKENS_PER_TURN` be?"

Have them look at real token counts from their own turns:

```bash
curl -s localhost:8080/metrics | python -m json.tool
# and scroll back through the trace lines in the run terminal
```

**That is what changed.** Last week the question was unanswerable; this week it
is arithmetic. Have someone propose a number *and the reasoning*: "my normal
turns use about N, so I will set it well above that and watch how often it
fires."

> **INSTRUCTOR** · Name what just happened, because it is the professional habit
> underneath the whole phase: *"You did not get smarter about token limits. You
> got data. Almost every 'good judgement' you will admire in a senior engineer is
> someone who instrumented the thing first."*

Then the hooks into the rest of the phase.

### "Your provider returns a single 429. What happens right now?"

The turn fails. The customer sees an error — for something that would have
worked if you had waited half a second.

> Week 6 — *"and the obvious fix is the wrong one."*

Leave that hanging. Do not let anyone talk you into explaining it now.

### "`avg_steps` has been creeping up all week. How would you find out why?"

You want them reaching for the traces rather than the code.

> Week 6, and they will do exactly this with a bug you plant.

### "`/metrics` describes whichever box answered you. You are running five."

Let that land. The numbers they just learned to trust are per-container.

> Week 7.

---

## If you finish early

- Have them add a field to the trace that answers a question they care about,
  and defend why it earns its place.
- Have them name a field they would *delete*. Harder, and better.
- Point `COST_PER_1M_INPUT` and `COST_PER_1M_OUTPUT` at their provider's real
  prices and re-run some turns. Ask what a thousand daily conversations costs.
- Break the redaction: add a field called `user_token` holding something
  harmless, and watch it come out `[redacted]`. Then rename it `token_count`
  and watch it come through. Ask which behaviour is the bug.

## Homework

- `make check-week-05` green, deployed
- **Find the slowest turn** in their own traces and explain in one paragraph
  where the time went — the model or a tool, and which one

> **INSTRUCTOR** · That homework is the entire skill of Week 6, rehearsed on
> low stakes. Anyone who can do it will find the planted bug in ten minutes;
> anyone who cannot will need help.
>
> **Mark it before next session.** It tells you exactly who to sit next to
> during the bug hunt, which is the highest-leverage forty minutes of the phase.
