# Guide 00 · The code you begin with

Before Week 1, read the agent you start from. It is small on purpose.

## The files

```
app/agent.py    the loop + three tools (lookup_order, calculator, word_count)
app/orders.py   a stand-in order system - the data the agent goes and fetches
app/main.py     the web service: POST /chat, GET /health
app/memory.py   session memory (a dict now, Redis in Week 2)
```

## The one idea

An agent is a loop. `run_turn(message, history)` sends the conversation to the
model with the tool list. The model either answers, or asks for a tool. Your code
runs the tool, hands back the result, and loops. It stops when the model answers,
or when it hits the step limit so it can never run forever.

## Do this

1. Open `app/agent.py` and find the `while` loop in `run_turn`. Read it once.
2. Notice you never decide to call a tool. The model asks; your code just runs it.
3. Run the tests to see the loop work with a fake model:

```bash
make test
```

## Check it works

```bash
make check-week-00
```

## Done when

- You can point to the four moves of the loop in `app/agent.py`.
- `make test` passes.
