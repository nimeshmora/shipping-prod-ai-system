# Guide Week 4 · Cap

**Goal:** stop the agent running forever or overspending, with step and token
caps.

## The idea

A taxi meter. The step cap stops the loop after N turns. The token cap stops it
after so much spend. Hit either, it stops cleanly. A billing alert is your backstop
for the hole you did not code.

## Do this

1. The `Budget` is already in `app/guardrails.py` and used in `app/agent.py`.
2. Tune the caps with env vars:

```bash
export MAX_STEPS=6
export MAX_TOKENS_PER_TURN=20000
```

3. Set a billing alert in your cloud console (see the curriculum).

## Check it works

```bash
make check-week-04
```

This runs a turn with a model that never stops asking for tools, and proves the
step cap stops it.

## Done when

- A runaway turn stops itself at the limit.

**Pull request:** `week-04-<your-name>`, `week 04: cap`.
