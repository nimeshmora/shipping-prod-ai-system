# Guide 00 · The agent you begin with

Before Week 1, read the agent you start from. It is small on purpose.

## The files

```
app/agent.py    the loop + three tools (lookup_order, calculator, word_count)
app/orders.py   a stand-in order system - the data the agent goes and fetches
app/memory.py   session memory (a dict now, Redis in Week 2)
```

## The one idea

**An agent is a loop.** `run_turn(message, history)` sends the conversation to
the model along with the tool list. The model either answers, or asks for a
tool. Your code runs the tool, hands the result back, and loops. It stops when
the model answers — or when it hits the step cap, so it can never spin forever.

Four moves:

```
1. you        "where is order ORD-1002?"
2. model      "call lookup_order with ORD-1002"     <- it asks; it cannot fetch
3. your code  "ORD-1002: standing desk, $340..."    <- you fetch, and reply
4. model      "Your standing desk arrives Thursday" <- now it can answer
```

That is why `len(history) == 4` after one turn with a tool call.

## The inversion worth noticing

You never decide to call a tool. The model asks, and your code obeys. That is
the whole difference between an agent and a program that happens to call an
LLM — and it is also why every later week exists. Code that runs whatever it is
told needs budgets (Week 4), traces (Week 5) and fences (Week 7).

## Two details that matter later

**The tool description is a prompt.** In `TOOLS`, each `description` is the only
thing the model reads when deciding whether that tool fits the question. It is
instructions to an AI, not a comment for a human. Vague here means a tool that
never gets used, or gets used at the wrong moment.

**A tool error is returned, not raised.** Look at `run_tool`. A bad argument
comes back as `"tool error: ..."` text the model can read and recover from.
Raising would kill the whole turn over one typo. Week 5 shows why this needs
recording too — a turn that "succeeded" with a broken tool looks fine from
outside.

## Do this

1. Open `app/agent.py` and find the `while` loop in `run_turn`. Read it once.
2. Find the three tool functions, and the `TOOLS` list that describes them to
   the model. Notice that the list and the handlers are separate.
3. Run the tests to see the loop work against a fake model:

```bash
make test
```

## Check it works

```bash
make check-week-00
```

## Done when

- You can point to the four moves of the loop in `app/agent.py`.
- You can explain why `history` grows by 4 and not 2 on a tool turn.
- `make test` passes.

Then go to `guide/week-01.md`.
