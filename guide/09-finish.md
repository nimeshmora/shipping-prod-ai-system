# Guide 09 · Finish

You are done. Your one small agent is now online, automatic, locked, capped,
watched, reliable, hardened, and gated. You did each hard part once, by hand, so
none of it is magic.

## Capstone

Add one real capability of your own, end to end, using every habit from the course:

- a new tool the model can call
- a guardrail for it (input check or allowlist)
- a trace field so you can see it work
- an eval case in `evals/cases.json` so the gate protects it

Run the full check before you open the pull request:

```bash
make check-setup
make eval
```

## The habits to keep

- Run the app after every change.
- Keep function names stable while you swap what is behind them.
- Let a broken rule return a clean error, never a crash.
- Never trust a throwaway container to hold anything important.

Ship it. Then write down what broke.
