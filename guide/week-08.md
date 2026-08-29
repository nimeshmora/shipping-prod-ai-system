# Guide Week 8 · Gate

**Goal:** block a bad change before it ships, and practise rolling back.

## The idea

The gate is a bouncer for your code. Before a change ships, it runs real cases:
does the agent still do the maths, does it still refuse the dangerous thing. If a
serious case fails, the gate blocks the change. A rollback is the undo button.

## Do this

1. The gate is already here: `evals/cases.json` and `evals/run_evals.py`, wired
   into `.github/workflows/eval.yml` (pull requests) and run again as the
   `gate` job in `.github/workflows/deploy.yml`, which the deploy `needs:`.
2. Run it:

```bash
make eval
```

3. Break something on purpose (edit the agent so a case fails) and watch the gate
   go red.
4. Practise a rollback to the last good version (see the curriculum).

## Check it works

```bash
make check-week-08
```

## Done when

- A serious failing case blocks the change.
- You can roll back quickly.

**Pull request:** `week-08-<your-name>`, `week 08: gate and rollback`.
