# Ship Production AI Systems

One small AI agent. Over eight weeks you turn it into something a company could
actually run: online, automatic, locked down, budgeted, watched, and safe.

You improve **the same project** every week. This repo already contains the
finished version of every week, so you can run it today, read it, and check your
own work against it.

---

## What it does right now

It is a **customer support agent**. Ask it where an order is and it looks it up.

```
you   →  "where is my order ORD-1002?"
agent →  "Standing desk, $340.00, shipped, arriving Thursday.
          A signature will be required on delivery."
```

It has three tools: `lookup_order`, `calculator` and `word_count`. The order
lookup is the interesting one — it fetches data the model could not possibly
know, which is what an agent is actually *for*.

---

## Start here

New to the course? Read **[`START-HERE.md`](START-HERE.md)**, then follow
**[`guide/`](guide/)** week by week.

### 1. Set up once

```bash
cp .env.example .env          # paste your KodeKey into .env
python -m venv .venv && source .venv/bin/activate
make install
```

### 2. Prove it works — no API key, no cloud, no internet

```bash
make check-setup
```

This runs the tests and the eval gate against a **fake model**, so it works on a
plane. You should see `Checkpoint passed.`

### 3. Talk to it for real

```bash
set -a && source .env && set +a     # load your key into THIS terminal
make run
```

Then in a second terminal:

```bash
curl -s -X POST localhost:8080/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"where is my order ORD-1002?"}'
```

You get a reply and a `session_id`. Send that id back on the next call to
continue the same conversation.

> **The most common error in this course** is `KODEKEY is not set`. It means you
> edited `.env` but did not load it. That `set -a && source .env && set +a` line
> must run in the **same terminal** as `make run`, **every time you open a new
> one**.

Try these too — `ORD-1001`, `ORD-1077`, and an id that does not exist. Then try
`ORD-1043`, which is more interesting than it looks (see Week 07).

---

## Every command you need

```bash
make install          # install dependencies
make run              # start the agent on http://localhost:8080
make test             # unit tests (fake model, no key needed)
make eval             # the Week 08 eval gate (fake model, no key needed)

make check-setup      # tests + gate: run this first
make check-week-01    # ... through check-week-08
make check-all        # every weekly checkpoint at once

make docker-build     # build the container
make docker-run       # run the container
```

Every checkpoint tells you in plain English whether that week's capability
actually works. **Green means done** — not "it looked right on my screen".

---

## What is in here

```
app/
  agent.py       the loop + tools + budget (Wk04) + trace (Wk05) + fallback (Wk06)
  orders.py      a stand-in order system — the data the agent goes and fetches
  main.py        the web service: /chat, /health, /metrics
  memory.py      session memory: a dict now, Redis when REDIS_URL is set (Wk02)
  guardrails.py  api key, rate limit, input checks, tool-output checks, budgets
  trace.py       one JSON record per turn, with cost, secrets redacted (Wk05)
  monitor.py     reads those records: rates, p95, alerts — served on /metrics
evals/
  cases.json     the eval cases
  run_evals.py   the gate: a high-severity failure exits non-zero (Wk08)
tests/           unit tests, all with a fake model
checks/          the weekly checkpoints
guide/           one short guide per week — start with 00-start-here.md
.github/workflows/
  eval.yml       tests + eval gate on every pull request
  deploy.yml     on push to main: gate → deploy (needs: gate) → health check
```

`WEEKS.md` maps each week to the files and settings it touches.

---

## The eight weeks

| Week | You add | You end up with |
|------|---------|-----------------|
| 01 | Package it in a container | It runs anywhere |
| 02 | Deploy it; move memory to Redis | It survives a restart |
| 03 | A deploy pipeline, keys, a rate limit | It ships itself, safely |
| 04 | Step, token and context budgets | It cannot overspend |
| 05 | A trace per turn, plus `/metrics` | You can see inside it |
| 06 | Read traces to debug; a fallback model | It survives an outage |
| 07 | Input checks **and** tool-output checks | It survives an attacker |
| 08 | An eval gate and a rollback | Bad code cannot ship |

---

## Deploying it

The pipeline in `.github/workflows/deploy.yml` does this for you on every push
to `main` — after the gate passes. To do it by hand once (Week 02):

```bash
gcloud run deploy ship-agent \
  --source . --region us-central1 --allow-unauthenticated \
  --set-env-vars "MODEL=claude-sonnet-5,BASE_URL=https://api.ai.kodekloud.com/v1,RATE_LIMIT_PER_MIN=20" \
  --set-secrets "KODEKEY=kodekey:latest" \
  --timeout=3600 --concurrency=80 --min-instances=1
```

Those last three flags matter more than they look. An agent turn is slow and
spends most of its time waiting, so it needs patience (`--timeout`), can serve
many people per container (`--concurrency`), and should never make the first
customer of the day wait for a cold start (`--min-instances`).

---

## A note on testing

The real model call is isolated in `app/agent.py`. Tests and the eval gate
inject a **fake model** so they can prove the loop, the tools, the guardrails,
the budgets and the gate without an API key.

The fake model fakes only the model's *decisions* — which tool to ask for. The
answers come back from your **real** code. That distinction is the whole of
Week 08: *fake the model, never fake your own code.*

---

## Security

Never commit `.env`. It is in `.gitignore` and it must stay there. Your key goes
in `.env`; the shared example file `.env.example` only ever holds a placeholder.

## Licence

MIT — see [LICENSE](LICENSE).
