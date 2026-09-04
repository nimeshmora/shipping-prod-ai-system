# Week 1 · Package

**Goal:** turn the agent from a thing you can import into a thing you can
*deploy* — a web service, streaming, in a container.

**You start from:** a working agent loop with three tools. Phase 1 built that.
Nothing this week changes how the agent thinks.

**You end with:** `POST /chat`, `POST /chat/stream`, `GET /health`, and an image
that runs the same on your laptop and in the cloud.

---

## Why this is a whole week

The loop in `app/agent.py` already works. Run `make test` and watch 12 tests
prove it. So why isn't it shippable?

Because nobody can call it. It has no address, no way to hold a conversation
across two HTTP requests, no way for a deploy pipeline to ask "did that work?",
and no way to run anywhere except a machine where you have already pip-installed
the right things.

Those four gaps are this week. None of them are about AI. All of them are why
agents die in a notebook.

---

## What you build

### 1. `app/main.py` — the front door

Three routes. The contract is exact, because the checkpoint asserts on it and
because a client somewhere depends on it:

| Route | Method | Returns |
|---|---|---|
| `/health` | GET | `{"status": "ok"}` |
| `/chat` | POST | `{"reply": "...", "session_id": "..."}` |
| `/chat/stream` | POST | `text/event-stream` |

Both `/chat` routes accept `{"message": "...", "session_id": "..."}` where
`session_id` is optional.

**The session id is the interesting part.** HTTP is stateless; a conversation is
not. So the first request gets a fresh id, the caller sends it back next time,
and your handler uses it to reload the history. The model itself remembers
nothing — every turn re-sends the whole conversation.

Three things worth getting right:

- **`/health` must not touch the model or a database.** A health check that
  depends on your dependencies fails during someone else's outage and gets your
  container restarted for no reason. Week 2's pipeline polls this to decide
  whether a release worked.
- **Declare the request body as a pydantic `BaseModel`.** Then a request with a
  missing `message` is a 422 before your code runs — a free guardrail.
- **Never let a raw exception reach the client.** Catch it, log what you need,
  return `{"detail": "internal error"}`. Exception text carries internals and
  sometimes secrets, and a stack trace in someone's browser is a security bug.

### 2. `app/stream.py` — server-sent events

Eight seconds of nothing feels broken. Eight seconds with words appearing after
400ms feels fast. Same duration, different product — which is why every
assistant you have used streams.

The frame sequence, which a client relies on:

```
event: start
data: {}

event: token
data: {"text": "Your standing desk "}

event: done
data: {}
```

Each frame is `event: <name>\ndata: <json>\n\n`. **The blank line is not
optional** — it is what tells the client the frame is complete.

Three traps, all of which the checkpoint catches:

- **The blocking loop must not run on the event loop thread.** `run_turn` does
  network I/O; run it on the event loop and it blocks every other request in the
  container. Use `loop.run_in_executor(None, run)`.
- **A mid-stream failure cannot be an HTTP error.** By the time the model fails
  you have already sent `200 OK`. The error has to travel as an `error` frame.
  Miss this and a streamed agent "succeeds" while showing half an answer.
- **Set `X-Accel-Buffering: no`.** Proxies will happily buffer your whole
  response and deliver it in one lump, which defeats the entire feature — and
  the failure is invisible, because the answer is still correct.

### 3. `Dockerfile` — package it

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=7000
EXPOSE 7000
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
```

Two lines carry the lesson:

**`COPY requirements.txt` before `COPY . .`** — Docker caches each layer. Copy
your code first and every one-character edit reinstalls every dependency.

**`--port ${PORT}`** — every container platform tells your service where to
listen through an environment variable. Hardcode `7000` and you have a service
that works locally and fails on deploy.

Also write a `.dockerignore`. Without one you copy `.venv/`, `.git/` and
`__pycache__/` into the image — and, worse, `.env`. **Never bake a secret into
an image layer.** Layers are cached, shared, and pushed to registries.

---

## First, watch it work

One question, four labelled steps, no key needed:

```bash
python3 -m checks.demo_turn
```

This is a teaching aid, not part of the agent. It calls the same
`run_turn()` you are about to wrap in a web service, and only adds a label
and a pause before each step so you can read them.

## Do this

```bash
make install
make test                 # 12 tests pass: the loop already works

# ... build main.py, stream.py, Dockerfile ...

make run                  # then, in another terminal:
curl -s -X POST localhost:7000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"where is my order ORD-1002?"}'

# watch it stream
curl -N -X POST localhost:7000/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"message":"where is my order ORD-1002?"}'

make docker-build
make docker-run           # same thing, in a container
```

`curl -N` disables curl's own buffering. Without it you will think your
streaming is broken when it is fine.

> **The most common error in this course** is `OPENROUTER_API_KEY is not set`. It means you
> edited `.env` but did not load it. Run `set -a && source .env && set +a` in the
> **same terminal** as `make run`, **every time you open a new one**.

---

## Check it works

```bash
make check-week-01
```

Every line is a specific assertion with a specific fix in the failure message.
Green means done.

---

## Done when

- `GET /health` returns `{"status": "ok"}`
- `POST /chat` returns a reply and a `session_id`, and sending that id back
  continues the same conversation
- `POST /chat/stream` sends `start` → `token`(s) → `done`, unbuffered
- `make docker-run` serves the same answers as `make run`
- `make check-week-01` passes

---

## Think about

1. Your `/health` returns 200 whenever the process is up. Suppose the model
   provider is down and every single `/chat` returns 500. What does `/health`
   say? *(Week 5 is about this gap. It is bigger than it looks.)*
2. `memory.py` stores sessions in a dict in this process. What happens to a
   conversation when you deploy a new version? *(Week 2.)*
3. Anyone who finds your URL can spend your API budget. *(Week 3.)*
