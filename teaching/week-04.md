# Week 4 · Cap

**Session goal:** they leave unable to bankrupt themselves.

**Branch:** `week-04-cap` → answer key `week-04-solution`

> **INSTRUCTOR** · The pivot point of the course. Weeks 1–3 protected the
> service from *other people*. From here on, everything protects it from
> *itself*. Say that out loud at the start.

---

## Beat 1 · Ask (10 min)

### "Last week we stopped strangers. Who else can cost you money?"

Wait. Someone will say "our own users". Push further.

**The agent itself.**

### "Look at the loop in `app/agent.py`. What makes it stop?"

Put it on the projector:

```python
while True:
    resp = model_fn(messages)
    if resp.stop_reason != "tool_use":
        return text, messages          # <- the ONLY way out
    # ... run the tool, go round again
```

**The model decides.** Their code goes round again as many times as it is told
to.

### "What happens if the model never stops asking for tools?"

Forever. And every trip costs money.

> **INSTRUCTOR** · Then ask the question that reframes the week:
>
> *"What would that look like on your dashboard?"*
>
> Let them guess. The answer is **nothing**. No crash. No error. No alert. The
> turn just takes a long time and then succeeds.
>
> **"The failure mode of an unbounded agent is not an outage. It is an
> invoice."**
>
> Write that on the board.

---

## Beat 2 · Break (10 min)

On the projector, with a fake model that always asks for a tool:

```python
def always_tool(messages):
    return NS(content=[NS(type="tool_use", name="calculator",
                          input={"expression": "1+1"}, id="t")],
              stop_reason="tool_use")
```

Run a turn. It spins. Let it spin for thirty seconds while you talk over it.

> **INSTRUCTOR** · *"Nothing is wrong. There is no bug. No exception. No log
> line saying anything is unusual. If this were production, it would just be
> costing money, and the only way you would find out is the bill or a very
> patient customer."*
>
> Then Ctrl-C it. *"I stopped it because I was watching. Nothing else would
> have."*

Second demo, if you have a real key: send one enormous message (paste a few
pages of text) and show the token count on one single call.

---

## Beat 3 · Concept (15 min)

Three bounds. **They are not redundant** — that is the lesson.

### Bound 1 · Steps

*How many times round the loop.* Catches a model that is looping, confused, or
being led on by its own tool output.

### Bound 2 · Tokens

**What a token is** — models charge by the piece of text, and a token is roughly
three-quarters of a word. Every request tells you how many it used.

*How much was actually sent and received.* Catches **one** step that is
enormous.

### Why you need both

```
step limit only    ▶  6 gigantic calls sail through
token limit only   ▶  100 tiny calls sail through
```

They fence different shapes of the same problem.

### Bound 3 · Context — the one people miss

Here is the thing that surprises everybody.

**Every turn sends the whole conversation back to the model.** The model
remembers nothing, so the entire history is re-sent every single time.

Draw it:

```
turn 1   sends:  [msg 1]
turn 2   sends:  [msg 1, msg 2]
turn 3   sends:  [msg 1, msg 2, msg 3]
turn 20  sends:  [msg 1 ... msg 20]      <- paying for all of it, again
```

A conversation that has been going for an hour sends an hour of conversation on
every request. Until the model refuses it entirely.

**And the per-turn token cap can never catch this.** Ask them why.

> Because it **resets at the start of every turn**. A forty-message session that
> costs a fortune per turn is comfortably under budget on each individual turn.

> **INSTRUCTOR** · This is the best "aha" of the week. The two limits look like
> they overlap, and they do not. One bounds a *turn*; the other bounds a
> *conversation*. Nothing else bounds the conversation.

So `memory.trim()` keeps only the most recent messages.

**One subtlety, and it is a real bug if they get it wrong.** A tool request and
the tool's answer are **one exchange**. Cut between them and you have an answer
replying to nothing — which the model provider rejects as malformed. A
conversation that grew too long would then start failing *every* request with an
error nobody can explain.

So trimming steps *past* a tool result rather than cutting on one.

### One status code decision

A turn that blows its budget returns **400**, not 500.

It is the *request* that was too expensive, not the server that broke.

> **INSTRUCTOR** · *"Get this backwards and your error rate blames you for what
> callers did. Next week you start alerting on that number, so it matters."*

---

## Beat 4 · Build (40 min)

They build `Budget` in `app/guardrails.py` and `trim()` in `app/memory.py`, then
wire the budget into the loop.

Three things to say while walking the room:

**Tokens accumulate across the turn**, not per step. Reset the counter each step
and a hundred medium calls sail past.

**`add_tokens(None)` must not crash.** Some providers do not report usage at
all. *"A missing cost report is not a reason to fail a customer's request."*

**Keep the newest messages, not the oldest.**

### See it work

```bash
export MAX_STEPS=2
make run
```

```bash
# a normal question still works
curl -s -X POST localhost:8080/chat -H 'Content-Type: application/json' \
  -H 'x-api-key: local-dev-key' -d '{"message":"where is ORD-1002?"}'

# now something needing several tool calls in a row
curl -s -X POST localhost:8080/chat -H 'Content-Type: application/json' \
  -H 'x-api-key: local-dev-key' \
  -d '{"message":"look up ORD-1001, ORD-1002, ORD-1043 and ORD-1077, then add up the totals"}'
```

The second stops itself with a 400. Put `MAX_STEPS` back to 6 and it completes.

Then the context bound:

```bash
export MAX_HISTORY_MESSAGES=6
```

Hold a conversation for five or six turns with the same `session_id`, then look
at what memory actually kept.

```bash
make check-week-04
```

---

## Beat 5 · Prove (20 min)

Green, then the three questions — and this week they are unusually pointed,
because Week 5 is the answer to all of them.

### "Your turn stopped at the step limit. Which tools did it call? How long did each take? What did it cost?"

They cannot answer any of it. **Nothing is written down.**

### "`MAX_TOKENS_PER_TURN=20000`. Where did that number come from?"

You made it up. **What should it be for their traffic?** They have no idea,
because they have no data.

### "Suppose the budget starts firing on 30% of requests tomorrow. How long until you notice?"

Until a customer complains.

> **INSTRUCTOR** · Then close the session with this:
>
> *"You have now built four weeks of protection, and you cannot see any of it
> working. Next week is the biggest week in the course."*

## Homework

- `make check-week-04` green
- Deployed, with the budget settings configured
- One paragraph: *what should `MAX_TOKENS_PER_TURN` be for a real support agent,
  and what would you need to know to decide?*

> **INSTRUCTOR** · That written question is worth marking. The right answer is
> *"I would look at the distribution of real turns"* — which is precisely what
> next week builds.
