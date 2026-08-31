# Week 4 · Cap

**Session goal:** they leave unable to bankrupt themselves.

**Branch:** `week-04-cap` → answer key `week-04-solution`

> **INSTRUCTOR** · The pivot point of the course. Weeks 1–3 protected the
> service from *other people*. From here on, everything protects it from
> *itself*. Say that out loud at the start — it reframes the whole back half,
> and students who hear it stop asking "wait, who are we defending against?"

---

## Beat 1 · Ask (10 min, no slides)

### "Last week we stopped strangers. Who else can cost you money?"

Wait. Someone will say "our own users". Push further. Someone else will say "a
bug in our code". Closer, but still not it.

**The agent itself.**

Not a bug. Not an attacker. The agent, working exactly as designed, doing
precisely what the model asked it to do.

> **INSTRUCTOR** · That distinction is the reason this week exists and the
> reason it is hard to sell to a room that has just spent three weeks on
> attackers. *"This week's threat is your own service on a normal Tuesday."*

### "Look at the loop in `app/agent.py`. What makes it stop?"

Put it on the projector. Do not summarise it — make them read it.

```python
while True:
    resp = model_fn(messages)
    if resp.stop_reason != "tool_use":
        return text, messages          # <- the ONLY way out
    # ... run the tool, go round again
```

Give them thirty seconds of silence to find the exit. There is exactly one, and
it is a condition on something *the model* sent back.

**The model decides.** Their code goes round again as many times as it is told
to.

> **INSTRUCTOR** · Ask it as a direct question: *"Whose decision is it that this
> loop stops?"* You want someone to say **"the model's"** and then look slightly
> alarmed. If nobody does, say it yourself and let it sit.
>
> This is the Week 1 point coming due. In Week 1 you told them: *the model asks,
> your code runs it.* The flip side, which nobody notices until now, is that
> **your code also decides how many times to keep asking** — and right now it
> has decided "as many as you like".

### "What happens if the model never stops asking for tools?"

Forever. And every trip costs money.

Push once more, because the first answer is usually too comfortable:

*"How would it end? Would something eventually stop it?"*

The honest answers: Cloud Run's request timeout, which they set to **an hour**
in Week 2. Or the model provider refusing a prompt that has grown too large.
Or their card declining.

**None of those are safety features.** They are accidents of other systems, and
two of the three cost money the whole way there.

### "What would that look like on your dashboard?"

> **INSTRUCTOR** · This is the question that reframes the week. Ask it, then
> genuinely wait — let them guess. You will get "an error", "a spike", "a red
> line".
>
> The answer is **nothing**. No crash. No exception. No alert. No 500. The turn
> just takes a long time and then, eventually, succeeds.
>
> **"The failure mode of an unbounded agent is not an outage. It is an
> invoice."**
>
> Write that on the board and leave it there all session. It is one of the five
> sentences from this phase they should still have in a year.

---

## Beat 2 · Break (10 min)

> **INSTRUCTOR** · Projector, not their machines. This one is better watched
> than done — the whole effect is the passage of time, and twenty people running
> it simultaneously turns a tense thirty seconds into admin.

On the projector, with a fake model that always asks for a tool:

```python
def always_tool(messages):
    return NS(content=[NS(type="tool_use", name="calculator",
                          input={"expression": "1+1"}, id="t")],
              stop_reason="tool_use")
```

Point out what this fake is *not* doing. It is not returning an error. It is not
malformed. It is not misbehaving. It is a model that has decided it needs one
more tool call — which is a completely normal thing for a model to decide. It
just decides it every time.

Run a turn. It spins.

**Let it spin for thirty full seconds while you talk over it.** Resist the urge
to cut it short; the discomfort is the teaching.

> **INSTRUCTOR** · Talk track while it spins, roughly:
>
> *"Nothing is wrong. There is no bug. No exception. No log line saying anything
> is unusual. Health check is green. Error rate is zero. If this were
> production, it would just be costing money, and the only way you would find
> out is the bill — or a very patient customer."*
>
> Then Ctrl-C it. *"I stopped it because I was watching. Nothing else would
> have."*
>
> That last sentence is the one to land. Say it, then move on quickly — do not
> over-explain a moment that just explained itself.

### Second demo — one call, enormous

If you have a real key, this is worth the two minutes.

Send one enormous message — paste a few pages of text into it — and show the
token count on that **single** call.

```bash
python -c "print('{\"message\":\"' + 'the quick brown fox '*8000 + '\"}')" > big.json
curl -s -X POST localhost:8080/chat -H 'Content-Type: application/json' \
  -H 'x-api-key: local-dev-key' -d @big.json
```

Ask: *"How many steps did that take?"*

**One.** A step limit would not have blinked.

> **INSTRUCTOR** · This is the setup for the "why you need both bounds" section
> ten minutes from now. If you do this demo, refer back to it explicitly — *"one
> step, and it cost more than fifty normal turns"* — rather than making the
> point abstractly.

---

## Beat 3 · Concept (15 min)

Three bounds. **They are not redundant** — that is the entire lesson, and it is
the thing people get wrong when they build this themselves.

Draw three empty boxes on the board and fill them in as you go.

### Bound 1 · Steps

*How many times round the loop.*

Catches a model that is looping, confused, or being led on by its own tool
output — a tool returns something ambiguous, the model asks again, the tool
returns something ambiguous, and round it goes.

```python
MAX_STEPS = int(os.environ.get("MAX_STEPS", "6"))
```

> **INSTRUCTOR** · Someone will ask *"why six?"* Good — answer honestly: **it is
> a guess.** A real support question needs one or two tool calls. Six leaves
> room for a genuinely complicated question and still stops a runaway fast.
>
> Then flag it forward: *"Next week you get data, and you come back and choose
> this number properly. Every number in this file is a placeholder until you
> have measured something."*

### Bound 2 · Tokens

First, the thing several of them are quietly unsure about:

**What a token is.** Models charge by the piece of text. A token is roughly
three-quarters of a word — `unhappiness` might be three tokens, `the` is one.
You do not need to predict them; every response tells you how many were used.

```python
usage.input_tokens      # what you sent  (the whole conversation, every time)
usage.output_tokens     # what came back
```

> **INSTRUCTOR** · Say why they are counted separately, because it looks like
> pedantry until you see a bill: **they are priced differently**, and output is
> usually several times more expensive than input. A turn that reads a lot and
> says little costs very differently from the reverse. Week 5 splits them in the
> trace for exactly this reason.

*What this bound catches:* **one** step that is enormous. The 200KB message from
the break demo. A tool that returned a whole web page.

### Why you need both

This is the bit to make concrete, on the board:

```
step limit only    ▶  6 gigantic calls sail through
token limit only   ▶  100 tiny calls sail through
```

They fence different shapes of the same problem. A step limit bounds *how many
times*; a token limit bounds *how much*. Neither implies the other.

> **INSTRUCTOR** · Ask the room to invent an attack that beats one and is caught
> by the other, in both directions. It takes ninety seconds and it is far
> stickier than being told.

### Bound 3 · Context — the one people miss

Here is the thing that surprises everybody, including people who have shipped
agents.

**Every turn sends the whole conversation back to the model.** The model
remembers nothing between requests — that is not a limitation of your code, it
is how the models work. So the entire history is re-sent, every single time.

Draw it, and let the shape do the work:

```
turn 1   sends:  [msg 1]
turn 2   sends:  [msg 1, msg 2]
turn 3   sends:  [msg 1, msg 2, msg 3]
turn 20  sends:  [msg 1 ....................... msg 20]   <- paying for all
                                                             of it, again
```

A conversation that has been going for an hour sends an hour of conversation on
every request. The cost of turn twenty is not the cost of turn twenty. It is the
cost of turns one through twenty, again.

Until, eventually, the model refuses the request entirely because the prompt is
too large — and then the session is not expensive, it is **dead**.

**And the per-turn token cap can never catch this.** Ask them why, and wait.

> Because it **resets at the start of every turn**. A forty-message session that
> costs a fortune per turn is comfortably under budget on each individual turn.
> The cap is doing its job perfectly. Its job is just not this.

> **INSTRUCTOR** · This is the best "aha" of the week — protect the two minutes
> it needs. The two limits *look* like they overlap, and they do not overlap at
> all. One bounds a **turn**; the other bounds a **conversation**. Nothing else
> in the entire system bounds a conversation.
>
> If you want it to land harder: *"Which of your users has the most expensive
> sessions? The ones who like you enough to keep talking."*

So `memory.trim()` keeps only the most recent messages:

```python
MAX_HISTORY_MESSAGES = int(os.environ.get("MAX_HISTORY_MESSAGES", "40"))
```

Be honest about what this is: **the cheapest possible strategy, chosen on
purpose.** It forgets the beginning of long conversations. The real-world
upgrade is summarising what you drop rather than discarding it, and that is
named as a known gap in `guide/09-finish.md`.

> **INSTRUCTOR** · Naming the cheap solution *as* cheap is worth doing every
> time. Students who think this is The Answer will build it at work and be
> confused when a customer says "you forgot what I told you". Students who know
> it is a deliberate floor will reach for summarisation when they need it.

### The subtlety that is a real bug

**A tool request and the tool's answer are one exchange.** They must stay
together.

```
[ ... older messages ... ] │ assistant: "call lookup_order(ORD-1002)"
                           │ user:      tool_result "standing desk, $340"
                           └── cutting HERE leaves an answer replying
                               to nothing
```

Cut between them and you have a tool result with no tool request — which the
provider rejects as malformed. The failure mode is nasty: a conversation that
grew too long would start failing **every** request, with an error message that
points at the provider rather than at your trimming code.

The fix is three lines, and it is in `app/memory.py`:

```python
cut = len(history) - MAX_HISTORY_MESSAGES
while cut < len(history) and _is_tool_result(history[cut]):
    cut += 1                      # step PAST the orphan, never cut on it
```

> **INSTRUCTOR** · Worth pointing out that this bug is invisible in testing.
> Short test conversations never reach the trim threshold, so every test passes.
> It appears only for your most engaged users, in production, weeks later.
> *"That pattern — works in tests, breaks for heavy users — is worth learning to
> smell."*

### One status code decision

A turn that blows its budget returns **400**, not 500.

It is the *request* that was too expensive, not the server that broke. The
service is working correctly; it is refusing, on purpose.

> **INSTRUCTOR** · Callback to Week 1, where you first drew the 400/500 line.
> *"Get this backwards and your error rate blames you for what callers did. Next
> week you start alerting on that number, so it stops being a matter of taste."*

---

## Beat 4 · Build (40 min)

> **INSTRUCTOR** · Hands on keyboards. Walk the room. The build itself is small
> this week — the concepts took the time — so you will have room to sit with
> individuals. Use it on whoever struggled with Week 3's pipeline.

They build `Budget` in `app/guardrails.py` and `trim()` in `app/memory.py`, then
wire the budget into the loop in `app/agent.py`.

### The shape of it

`Budget` is deliberately tiny — a counter with an opinion:

```python
class Budget:
    def __init__(self, max_steps=MAX_STEPS, max_tokens=MAX_TOKENS_PER_TURN):
        self.steps = 0
        self.tokens = 0

    def add_step(self):
        self.steps += 1
        if self.steps > self.max_steps:
            raise GuardrailError(f"step limit reached ({self.max_steps})")
```

Note where it lives: **`app/guardrails.py`**, alongside the API key check and
the rate limit from Week 3.

> **INSTRUCTOR** · Make the point about the file, not just the class. *"Three
> weeks in, someone asks 'what are this service's rules?' — and the answer is
> one file they can read in two minutes."* That is worth more than any single
> rule in it.

### Three things to say while walking the room

**Tokens accumulate across the turn**, not per step. The counter belongs to the
`Budget`, which is created once per turn, at the top of `run_turn`. Reset it
each step and a hundred medium calls sail past a cap that never sees more than
one call's worth.

**`add_tokens(None)` must not crash.** Some providers do not report usage at
all; some report it only sometimes.

```python
self.tokens += int(n or 0)
```

> **INSTRUCTOR** · Give the reasoning, not just the rule: *"A missing cost report
> is not a reason to fail a customer's request."* Then generalise it, because it
> is a habit worth having — **your telemetry breaking must never break your
> product.** That principle comes back hard in Week 5, where an entire `finally`
> block exists to honour it.

**Keep the newest messages, not the oldest.** It sounds obvious in a sentence
and gets written backwards surprisingly often, because `history[:N]` is what
your fingers type. It is `history[cut:]`.

### See it work

The point of this section is that they *watch their own limit fire*. Do not let
anyone skip to the checkpoint.

```bash
export MAX_STEPS=2
make run
```

In a second terminal:

```bash
# a normal question still works
curl -s -X POST localhost:8080/chat -H 'Content-Type: application/json' \
  -H 'x-api-key: local-dev-key' -d '{"message":"where is ORD-1002?"}'
```

```bash
# now something needing several tool calls in a row
curl -s -X POST localhost:8080/chat -H 'Content-Type: application/json' \
  -H 'x-api-key: local-dev-key' \
  -d '{"message":"look up ORD-1001, ORD-1002, ORD-1043 and ORD-1077, then add up the totals"}'
```

The second stops itself with a **400** and a message naming the limit it hit.

Put `MAX_STEPS` back to 6, restart, and run the same request. It completes.

> **INSTRUCTOR** · Ask the room: *"Which of those two outcomes is correct?"*
>
> It is a genuinely good question and the answer is **both**, depending on what
> you meant. With `MAX_STEPS=2` the service refused work it could have done.
> With `6` it did the work. **The limit is a policy choice, not a correctness
> property** — which is exactly why it is a setting and not a constant, and
> exactly why next week's data matters.

Then the context bound:

```bash
export MAX_HISTORY_MESSAGES=6
make run
```

Hold a conversation for five or six turns with the same `session_id`, then look
at what memory actually kept:

```bash
curl -s -X POST localhost:8080/chat -H 'Content-Type: application/json' \
  -H 'x-api-key: local-dev-key' \
  -d '{"message":"what was the very first thing I asked you?"}' \
  -d '{"session_id":"PASTE_IT"}'
```

**It does not know.** Have them sit with that for a second — this is the cost of
the cheap strategy, and they should feel it rather than read about it.

```bash
make check-week-04
```

---

## Beat 5 · Prove (20 min)

Green checkpoint. Read the output together — it runs a turn with a model that
never stops asking for tools and proves the step cap stops it.

Then the three questions, and this week they are unusually pointed, because
**Week 5 is the answer to all three**. Do not soften them.

### "Your turn stopped at the step limit. Which tools did it call? How long did each take? What did it cost?"

Let them try. They cannot answer any of it.

**Nothing is written down.** The limit fired, the request was refused, and the
entire event left no trace beyond a 400 in a log line that says nothing useful.

### "`MAX_TOKENS_PER_TURN=20000`. Where did that number come from?"

You made it up. *(You did — say so.)*

**What should it be for their traffic?** They have no idea, because they have no
data. They cannot even say whether their current limit fires once a week or
never.

> **INSTRUCTOR** · Put the discomfort into words: *"You have just spent forty
> minutes building limits, and not one of you can tell me whether your limits
> are in the right place. That is not a criticism — it is the setup for next
> week."*

### "Suppose the budget starts firing on 30% of requests tomorrow. How long until you notice?"

Until a customer complains.

And note what makes this worse than it sounds: a budget refusal is a **400**,
which they correctly classified as *not our fault* — so even a dashboard that
watched error rates would be filtering these out.

> **INSTRUCTOR** · Close the session on this:
>
> *"You have now built four weeks of protection, and you cannot see a single
> piece of it working. Next week is the biggest week in the course."*
>
> Then stop. Do not summarise. Ending on an admitted gap is what makes them
> turn up.

---

## If you finish early

- Set `MAX_TOKENS_PER_TURN` absurdly low (say `200`) and watch a completely
  normal question get refused. Ask what a customer would think that meant.
- Have them find, in `app/memory.py`, the exact line that would break if
  `trim()` cut between a tool call and its result. Then have them break it on
  purpose and watch the provider reject the conversation.
- Ask: *"Where else in this codebase does something unbounded live?"* Good
  answers: the tool output size (Week 7), how long one model call may take
  (Week 6 adds `MODEL_TIMEOUT_SECONDS`), how many sessions Redis will hold
  (the `SETEX` expiry from Week 2 is the answer, and they built it).

## Homework

- `make check-week-04` green, committed and pushed
- Deployed, with the budget settings configured on the service
- One paragraph: *what should `MAX_TOKENS_PER_TURN` be for a real support
  agent, and what would you need to know to decide?*

> **INSTRUCTOR** · That written question is worth actually marking, and it is
> the best predictor of who is thinking like an operator.
>
> The right answer is not a number. It is **"I would look at the distribution of
> real turns and set it above the 99th percentile"** — which is precisely what
> next week builds, and you can open Week 5 by reading out whichever student got
> closest.
