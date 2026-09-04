# Ship Production AI Systems — Week 4 · Cap

> **You are on `week-04-cap`: the starting line for Week 4.**
>
> Weeks 1-3 are complete and passing. This week you build the `Budget` class in
> `app/guardrails.py`, wire it into the agent loop, and add `trim()` to
> `app/memory.py` so a long conversation cannot grow forever.
>
> Read **[`guide/week-04.md`](guide/week-04.md)**, then run
> `make check-week-04` until it is green.
>
> Stuck? `git diff week-04-cap..week-04-solution -- app/guardrails.py`

One small AI agent. Over eight weeks you turn it into something a company could
actually run: online, automatic, locked down, budgeted, watched, and safe.

Phase 1 built the agent. **Phase 2 ships it.**

---

## Where you are

```
  ┌─ SHIP IT ────────────┐  ┌─ OPERATE IT ─────────┐  ┌─ TRUST IT ──────┐
  01 package  ✓           04 cap  ← you are here    07 attack
  02 deploy   ✓           05 see                    08 gate
  03 automate ✓           06 survive
```

**Week 4 makes it impossible for one turn to run forever or run up a bill.**

---

## What it does

A **customer support agent**. Ask it where an order is and it looks it up.

```
you   →  "where is my order ORD-1002?"
agent →  "Standing desk, $340.00, shipped, arriving Thursday.
          A signature will be required on delivery."
```

Three tools: `lookup_order`, `calculator`, `word_count`. The order lookup is the
interesting one — it fetches data the model could not possibly know, which is
what an agent is actually *for*.

---

## On Windows: do this first

Every command in this course is written for a Linux-style terminal. Windows
has one built in — you just have to turn it on. **In PowerShell, once:**

```powershell
wsl --install
```

Restart, then type `wsl` to enter it. From then on **every command here
works exactly as written** — no substitutions, nothing to translate.

Work inside the WSL home folder (`cd ~`), not under `/mnt/c/`. It is much
faster and avoids a class of permission problems.

Mac and Linux: nothing to do, your terminal is already right.

---

## See what it does, step by step

Before building anything, watch one question go round the loop. This uses
your key, and the model really decides:

```bash
python3 -m checks.demo_turn
```

It prints four labelled steps with a pause between them: the question, the
model asking for a tool, your code running it, and the answer. Then it shows
the conversation it kept, which is the point — **the model remembers nothing,
so the whole list is re-sent every time.**

Change the question and watch it reach for a different tool:

```bash
python3 -m checks.demo_turn "what is 12 * 41?"
```

Load your key first, in the same terminal:

```bash
set -a && source .env && set +a
```

No network? `--offline` runs the same four steps with a scripted stand-in.

---

## Start here

```bash
cp .env.example .env          # paste your OpenRouter key into .env
python3 -m venv .venv && source .venv/bin/activate
make install
make test                     # proves the loop works, no API key needed
```

Then talk to it for real:

```bash
set -a && source .env && set +a     # load your key into THIS terminal
make run
```

```bash
curl -s -X POST localhost:7000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"where is my order ORD-1002?"}'
```

Send the returned `session_id` back on the next call to continue the same
conversation. To watch it stream:

```bash
curl -N -X POST localhost:7000/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"message":"where is my order ORD-1002?"}'
```

> **The most common error in this course** is `OPENROUTER_API_KEY is not set`. It means you
> edited `.env` but did not load it. That `set -a && source .env && set +a` line
> must run in the **same terminal** as `make run`, **every time you open a new
> one**.

---

## Every command

```bash
make install          # install dependencies
make run              # start the agent on http://localhost:7000
make test             # unit tests (fake model, no key needed)

make check-week-00    # the loop you started from
make check-week-01    # a deployable web service
make check-week-02    # memory that survives a redeploy
make check-week-03    # automatic deploys, keys, rate limits
make check-week-04    # this week's capability
make check-setup      # just runs the tests

make docker-build     # build the container
make docker-run       # run the container
```

---

## What is in here

```
app/
  agent.py       the loop, three tools, the system prompt, a step cap
  orders.py      a stand-in order system — the data the agent goes and fetches
  main.py        the web service: /chat, /chat/stream, /health
  stream.py      server-sent events: the same turn, as it happens
  memory.py      BUILD  add trim() so context cannot grow forever
  guardrails.py  BUILD  add the per-turn Budget to the existing rules
tests/           unit tests, all with a fake model
checks/          the weekly checkpoints
guide/           read guide/week-04.md
Dockerfile       package it so it runs the same everywhere
.github/workflows/
  test.yml       tests + checkpoints on every pull request
  deploy.yml     on push to main: test → deploy (needs: test) → verify
```

---

## A note on testing

The real model call is isolated in one function, `call_model` in `app/agent.py`.
Tests inject a **fake model**, so they prove the loop, the tools, the service and
the streaming without an API key — in milliseconds, deterministically, offline.

An agent whose tests need an API key is an agent nobody runs tests on.

The fake model fakes only the model's *decisions* — which tool to ask for. The
answers come back from your **real** code.

---

## Deploying it

```bash
gcloud run deploy ship-agent \
  --source . --region us-central1 --allow-unauthenticated \
  --set-env-vars "MODEL=anthropic/claude-sonnet-4.5,BASE_URL=https://openrouter.ai/api/v1" \
  --set-secrets "OPENROUTER_API_KEY=kodekey:latest" \
  --timeout=3600 --concurrency=80 --min-instances=1
```

The key goes in Secret Manager, never in `--set-env-vars` — env vars are visible
in the console and in `gcloud describe` output.

Set `REDIS_URL` and conversations survive a redeploy. Leave it unset and they do
not, which is Week 2's whole lesson and worth seeing for yourself.

---

## Calling it

```bash
curl -s -X POST $URL/chat \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: your-key' \
  -d '{"message":"where is my order ORD-1002?"}'
```

No key is a 401. Too many requests is a 429. Both apply to `/chat/stream` too —
a streaming endpoint is not a side door.

---

## Security

Never commit `.env`. It is in `.gitignore` and `.dockerignore`, and it must stay
in both. Your key goes in `.env`; the shared `.env.example` only ever holds a
placeholder.
