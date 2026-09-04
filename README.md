# Ship Production AI Systems — Week 3 · Automate and lock

> **You are on `week-03-automate`: the starting line for Week 3.**
>
> Weeks 1-2 are complete and passing. This week you build `app/guardrails.py`
> (an API key and a rate limit), wire it into both endpoints in `app/main.py`,
> and replace hand-deploys with a GitHub Actions pipeline that tests before it
> ships.
>
> Read **[`guide/week-03.md`](guide/week-03.md)**, then run
> `make check-week-03` until it is green.
>
> Stuck? `git diff week-03-automate..week-03-solution -- app/guardrails.py`

One small AI agent. Over eight weeks you turn it into something a company could
actually run: online, automatic, locked down, budgeted, watched, and safe.

Phase 1 built the agent. **Phase 2 ships it.**

---

## Where you are

```
  ┌─ SHIP IT ────────────┐  ┌─ OPERATE IT ─────────┐  ┌─ TRUST IT ──────┐
  01 package  ✓           04 cap                    07 attack
  02 deploy   ✓           05 see                    08 gate
  03 automate ← you are here
                          06 survive
```

**Week 3 makes deploys automatic and keeps strangers out.**

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
make check-week-03    # this week's capability
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
  memory.py      session memory: Redis when REDIS_URL is set, else a dict
  guardrails.py  BUILD  the rules every request passes: api key, rate limit
tests/           unit tests, all with a fake model
checks/          the weekly checkpoints
guide/           read guide/week-03.md
Dockerfile       package it so it runs the same everywhere
.github/workflows/  BUILD  test on every PR; test → deploy → verify on main
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
