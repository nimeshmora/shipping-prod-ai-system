# solutions

This project is organised as **one working project you improve week by week**,
not as eight separate copies. The `app/` folder at the repo root is the finished
reference: every week's capability is already there and tested.

Use it two ways:

1. **Build it yourself.** Follow `WEEKS.md`. Each week you add one capability to
   your own copy. When you get stuck, open the matching file in the root `app/`
   and compare.

2. **Read the finished version.** The root `app/` is the answer key. Every module
   says in its top comment which week added which part, so you can read it as a
   week-by-week story:
     - `app/agent.py`   loop (Wk01), budget (Wk04), trace (Wk05), fallback (Wk06)
     - `app/memory.py`  dict (Wk01), Redis (Wk02)
     - `app/guardrails.py` auth + rate limit (Wk03), budget (Wk04), input + url (Wk07)
     - `app/trace.py`   tracing (Wk05)
     - `evals/`         the gate (Wk08)

Keeping it one project is the whole point: real systems are improved in place, not
rewritten every week.
