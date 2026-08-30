# Week 4 · Cap

**Goal:** make it impossible for one turn to run forever or run up a bill.

**You start from:** a locked-down, auto-deploying service with no spending limit.

**You end with:** three bounds — steps, tokens, and context — and a turn that
stops itself.

---

## The failure mode nobody sees coming

Weeks 1–3 protected you from *other people*. This week protects you from **your
own agent**, which is a harder problem because nothing looks wrong.

An unbounded agent does not crash. A model that keeps asking for tools, a tool
whose output invites another call, a context that grows every trip — none of that
raises an exception. It runs, and charges you, and eventually answers.

**The failure mode of an unbounded agent is not an outage. It is an invoice.**

There is no stack trace to find, no alert to fire, no red dashboard. Just a bill
at the end of the month that is 40× what you modelled.

---

## Three bounds, because they catch different runaways

### 1. Steps — how many times round the loop

`Budget.add_step()` at the top of every iteration. Catches a model that is
looping, confused, or being led on by its own tool output.

### 2. Tokens — how much was actually sent and received

`Budget.add_tokens()` after every model call, from the provider's `usage`.
Catches **one** step that is enormous: a huge context, or a tool returning a
whole file.

You need both, and this is the part worth internalising:

- A step limit alone lets **6 colossal calls** through.
- A token limit alone lets **100 tiny calls** through.

They are not redundant. They fence different shapes of the same problem.

Two details:

- **Tokens accumulate across the turn.** Reset the counter per step and 100
  medium calls sail past.
- **`add_tokens(None)` must not crash.** Some gateways omit `usage` entirely,
  and a missing cost report is not a reason to fail a turn.

### 3. Context — how long the conversation may get

This is the one people miss, and it is the most interesting.

Every turn re-sends the **whole history** to the model. So a session that has
been going for an hour sends an hour of conversation on every single request —
until the model refuses it outright.

**And the per-turn token cap never sees this coming, because it resets at the
start of each turn.** A 40-message session that costs a fortune per turn is
comfortably under budget on every individual turn. The two limits look like they
overlap; they do not.

So `memory.trim()` keeps only the most recent messages. One subtlety:

> A `tool_use` block and the `tool_result` that answers it are **one exchange**.
> Cut between them and you have a tool result replying to nothing — which
> providers reject as malformed. A session that grew too long then starts failing
> *every* request with a 400 nobody can explain.

`trim()` steps forward past a tool result rather than cutting on one.

This is deliberately the cheapest possible strategy. Summarising the dropped
turns — so the agent still knows what was agreed an hour ago — is the real-world
upgrade, and a good stretch goal.

---

## One status code decision

A turn that blows its budget returns **400**, not 500.

It is the *request* that was too expensive, not the server that broke. Get this
backwards and your error rate blames you for what callers did — which matters a
lot in Week 5, when you start alerting on that number.

---

## Do this

```bash
export MAX_STEPS=2
make run

# a normal question still works
curl -s -X POST localhost:8080/chat -H 'Content-Type: application/json' \
  -H 'x-api-key: local-dev-key' -d '{"message":"where is ORD-1002?"}'

# now ask for something that needs several tool calls in a row
curl -s -X POST localhost:8080/chat -H 'Content-Type: application/json' \
  -H 'x-api-key: local-dev-key' \
  -d '{"message":"look up ORD-1001, ORD-1002, ORD-1043 and ORD-1077, then add up the totals"}'
```

With `MAX_STEPS=2` the second one stops itself with a 400 rather than working
through all four lookups. Put it back to 6 and it completes.

Then watch the context bound:

```bash
export MAX_HISTORY_MESSAGES=6
# hold a conversation with the same session_id for five or six turns,
# then look at what memory actually kept
```

---

## Check it works

```bash
make check-week-04
```

---

## Done when

- A runaway turn stops itself with a **400**
- A turn stops on **tokens** as well as steps
- A long session stops growing, and trimming never orphans a tool result
- `make check-week-04` passes

---

## Think about

1. Your turn stopped at the step limit. **Which** tools did it call, how long did
   each take, and what did the turn cost? You cannot answer any of that yet.
   *(Week 5 — and this is the biggest gap in the project right now.)*
2. `MAX_TOKENS_PER_TURN=20000` — where did that number come from? What should it
   be for *your* traffic? You need data you do not have. *(Also Week 5.)*
3. The budget stops a turn. It does not tell anyone it happened. If this started
   firing on 30% of requests tomorrow, how long until you noticed? *(Week 5.)*
