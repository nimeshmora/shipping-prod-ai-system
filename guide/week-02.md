# Week 2 · Deploy

**Goal:** get a public URL — then watch your agent forget everything, and fix it.

**You start from:** a containerised service that works locally.

**You end with:** a live HTTPS URL where a conversation survives a redeploy.

---

## The week in one sentence

Deploying is the easy part. The interesting part is what breaks *because* you
deployed.

---

## Part 1 — Ship it

```bash
gcloud run deploy ship-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "MODEL=claude-sonnet-5,BASE_URL=https://api.ai.kodekloud.com/v1" \
  --set-secrets "KODEKEY=kodekey:latest" \
  --timeout=3600 --concurrency=80 --min-instances=1
```

First, put your key in Secret Manager — **never** in `--set-env-vars`, where it
shows up in the console, in `gcloud describe` output, and in your shell history:

```bash
echo -n "$KODEKEY" | gcloud secrets create kodekey --data-file=-
```

Those last three flags matter more than they look:

- **`--timeout=3600`** — an agent turn is slow and spends most of its life
  waiting on a model. The default 5 minutes will cut off a long turn.
- **`--concurrency=80`** — one container can serve many people at once, because
  each request is mostly idle. This is why an agent is cheap to host and why
  Week 7's load test is interesting.
- **`--min-instances=1`** — keeps one container warm. Without it the first
  customer of the day waits for a cold start: a new container, a Python
  interpreter, and every import. Costs a few dollars a month; buys a first
  impression.

Now confirm it:

```bash
URL=$(gcloud run services describe ship-agent --region us-central1 \
        --format='value(status.url)')
curl -s $URL/health
curl -s -X POST $URL/chat -H 'Content-Type: application/json' \
  -d '{"message":"where is my order ORD-1002?"}'
```

---

## Part 2 — Break it (do this, it is the lesson)

1. Start a conversation and **keep the `session_id`**:

```bash
curl -s -X POST $URL/chat -H 'Content-Type: application/json' \
  -d '{"message":"where is my order ORD-1002?"}'
# note the session_id that comes back
```

2. Continue it, and confirm it remembers:

```bash
curl -s -X POST $URL/chat -H 'Content-Type: application/json' \
  -d '{"message":"and when will it arrive?", "session_id":"<paste it>"}'
```

3. Now **redeploy** — change nothing at all, just deploy again:

```bash
gcloud run deploy ship-agent --source . --region us-central1
```

4. Continue that same conversation one more time.

It has forgotten everything. Not because anything crashed — because the
deployment *succeeded*. Cloud Run replaced your container, and your `_STORE`
dict went with it.

**Sit with that for a second.** Your health check is green. Your logs are clean.
Your error rate is zero. And every customer mid-conversation was silently reset.
This is the shape of most real agent incidents: nothing fails, the product just
quietly stops working.

The same thing happens when traffic goes quiet and Cloud Run scales you to zero,
and again the moment it scales you to *two* containers — because then it depends
which one answers you.

---

## Part 3 — Fix it

Anything a request needs to remember has to live outside the process that serves
it. That sentence is most of what "stateless service" means.

Provision Redis, then set `REDIS_URL`:

```bash
# Memorystore, or Upstash's free tier — either is fine for this
gcloud run services update ship-agent --region us-central1 \
  --set-env-vars "REDIS_URL=redis://<host>:6379"
```

`app/memory.py` already does the rest. Look at what changed:

- **`load` and `save` kept their names.** No other file in the codebase was
  edited. That is not luck — Week 1 put the seam there deliberately, and this
  week is the payoff. *Designing the seam before you need it is most of what
  makes a change cheap later.*
- **`SETEX`, not `SET`.** Value and expiry in one round trip. Set them
  separately and a crash between the two leaves a session that never expires.
- **Namespaced keys** (`session:<id>`), because Redis is one flat keyspace that
  you will eventually share with something else.
- **A lazy, single connection.** Importing the module must not require a running
  Redis, and building a connection pool per request is how you run out of file
  descriptors under load.
- **The dict is still there** as a fallback when `REDIS_URL` is unset, so the
  tests and your laptop keep working with no Redis at all.

One subtlety worth reading in `_block_to_dict`: content blocks arrive as three
different shapes — plain dicts, pydantic models from the SDK, and
`SimpleNamespace` from the fake model in tests. Handle only the pydantic case
and you get a bug that passes every test and fails in production.

Now repeat Part 2. The conversation survives.

---

## Check it works

```bash
make check-week-02
```

Runs against a Redis stand-in, so it needs no server.

---

## Done when

- The agent answers on a public HTTPS URL
- You have **seen** a conversation die on redeploy
- With `REDIS_URL` set, a conversation survives a redeploy
- `make check-week-02` passes

---

## Think about

1. You deployed by hand, from your laptop, with a key in your shell history. How
   many ways can that go wrong? *(Week 3.)*
2. Your URL is `--allow-unauthenticated`. Anyone who finds it can spend your
   model budget. *(Week 3.)*
3. Redis is now a dependency. What does `/health` say when Redis is down but the
   process is fine — and what *should* it say? *(Week 5, and it is a genuinely
   hard question.)*
