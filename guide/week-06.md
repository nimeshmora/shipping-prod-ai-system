# Guide Week 6 · Debug

**Goal:** find a bug from traces, and survive a model outage with a fallback.

## The idea

The trace is your map to the bug: read the broken turn instead of guessing. The
fallback is a spare tire: if the main model fails, the agent tries a backup and
keeps going, and the trace notes which one answered.

## Do this

1. Reproduce a bad turn and read its trace top to bottom to find the wrong step.
2. The fallback is already in `app/agent.py` (`call_model` tries primary then
   `FALLBACK_MODEL`). Set the backup:

```bash
export FALLBACK_MODEL=openai/gpt-4o-mini
```

3. Run the outage drill: make the primary fail and confirm the fallback answers.

## Check it works

```bash
make check-week-06
```

This forces the primary model to fail and proves the fallback answers.

## Done when

- You found the bug from its trace.
- With the primary down, the agent still answers via the fallback.

**Pull request:** `week-06-<your-name>`, `week 06: debug and fallback`.
