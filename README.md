# Ship Production AI Systems — Week 1 · Package

> **You are on `week-01-package`: the starting line for Week 1.**
>
> `app/agent.py` and its tools work — 12 tests prove it. Your job is to build
> `app/main.py`, `app/stream.py`, the `Dockerfile` and a `.dockerignore`. Each
> of those files holds a header comment telling you exactly what goes in it.
>
> Read **[`guide/week-01.md`](guide/week-01.md)**, then run
> `make check-week-01` until it is green.
>
> Stuck on one file? The answer key is the `week-01-solution` branch:
> `git diff week-01-package..week-01-solution -- app/main.py`

One small AI agent. Over eight weeks you turn it into something a company could
actually run: online, automatic, locked down, budgeted, watched, and safe.

Phase 1 built the agent. **Phase 2 ships it.**

---

## Where you are

```
  ┌─ SHIP IT ────────────┐  ┌─ OPERATE IT ─────────┐  ┌─ TRUST IT ──────┐
  01 package  ← you are here
      02 deploy              04 cap                    07 attack
      03 automate            05 see                    08 gate
                             06 survive
```

**Week 1 turns an importable agent into a deployable service.**

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

## Start here

```bash
cp .env.example .env          # paste your KodeKey into .env
python -m venv .venv && source .venv/bin/activate
make install
make test                     # 12 tests pass: the loop already works
make check-week-01            # fails, and tells you what to build first
```

Once you have built the service, talk to it for real:

```bash
set -a && source .env && set +a     # load your key into THIS terminal
make run
```

```bash
curl -s -X POST localhost:7000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"where is my order ORD-1002?"}' | jq
```

`| jq` lays the JSON reply out so you can read it. Send the returned
`session_id` back on the next call to continue the same conversation:

```bash
curl -s -X POST localhost:7000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"how much was it?","session_id":"PASTE_ID_HERE"}' | jq
```

To watch the answer arrive in pieces (no `jq` here - it would buffer the
stream, which is the one thing we are trying to see):

```bash
curl -N -X POST localhost:7000/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"message":"where is my order ORD-1002?"}'
```

## Share your container

Once `make docker-build` works, the image is a file on your machine. Push it
to Docker Hub and anyone can run your exact version.

```bash
docker login                                    # once, with your Docker Hub account
docker tag ship-agent <your-username>/ship-agent:v1
docker push <your-username>/ship-agent:v1
```

Then, on any other machine with Docker:

```bash
docker pull <your-username>/ship-agent:v1
docker run --rm -p 7000:7000 --env-file .env <your-username>/ship-agent:v1
curl -s localhost:7000/health | jq
```

Note what did **not** travel with it: your `.env`. The image carries the code
and its dependencies; **the key is supplied separately at run time**, which is
why `--env-file` is on that last command.

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
make check-week-01    # this week's capability
make check-setup      # just runs the tests

make docker-build     # build the container
make docker-run       # run the container
```

---

## What is in here

```
app/
  agent.py       GIVEN  the loop, three tools, the system prompt, a step cap
  orders.py      GIVEN  a stand-in order system — the data the agent fetches
  memory.py      GIVEN  session memory — a dict for now, Redis in Week 02
  main.py        BUILD  the web service: /chat, /chat/stream, /health
  stream.py      BUILD  server-sent events: the same turn, as it happens
Dockerfile       BUILD  package it so it runs the same everywhere
.dockerignore    BUILD  and keep .env out of the image
tests/           unit tests for what you were given
checks/          the weekly checkpoints — this is your test for the week
guide/           read guide/week-01.md
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

## Security

Never commit `.env`. It is in `.gitignore` and `.dockerignore`, and it must stay
in both. Your key goes in `.env`; the shared `.env.example` only ever holds a
placeholder.
