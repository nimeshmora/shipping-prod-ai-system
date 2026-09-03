# Guide Week 1 · Package

**Goal:** run the agent locally, then wrap it in a web service and a container.

## The idea

Right now the agent is a script. You wrap it in a small web service (two doors:
`/chat` and `/health`) and seal it in a container so it runs the same everywhere.

**Why a web service?** Your agent is a Python function, so the only thing that
can call it is Python code, on your machine, in your folder, with your API key.
Sending someone the file means sending them your key and your dependency
problems — and they are stuck on that copy forever.

A web service is how you let something that is **not your program**, on a
computer that is **not yours**, use your code — without giving them the code:

- **one copy, one place** — fix a bug once and everyone has the fix
- **your key stays yours** — it lives on the server, callers never see it
- **anything can call it** — a website, a phone app, another company, a shell
  script. None of them need Python. They need a URL.

FastAPI is just the translator: it turns an arriving `POST /chat` into a Python
function call, and turns what you return into JSON. **Your agent logic does not
change.** You are giving it a front door, not rewriting it.

## The map

You only ever write inside `app/`. Today it is two files.

```
   agentic-ai-cohort-01-phase-02/
   │
   ├── app/                    <- everything you write lives here
   │   ├── main.py                 the web service      <- TODAY
   │   ├── stream.py               streaming replies    <- TODAY
   │   ├── agent.py                the Phase 1 loop     (already works)
   │   ├── orders.py               the tool it calls    (already works)
   │   ├── memory.py               conversation history <- Week 2
   │   ├── store.py                where memory lives   <- Week 2
   │   ├── guardrails.py           keys, limits, fences <- Weeks 3, 4, 7
   │   ├── trace.py                what happened        <- Week 5
   │   ├── otel.py                 traces, standard     <- Week 5
   │   └── monitor.py              is it healthy?       <- Week 5
   │
   ├── tests/test_app.py       <- proves the agent still thinks correctly
   ├── checks/check.py         <- `make check-week-01` lives here
   │
   ├── Makefile                <- the shortcuts. Read this one.
   ├── Dockerfile              <- how to build the box   <- TODAY
   ├── .dockerignore           <- what to keep OUT of it <- TODAY
   ├── .env                    <- your API key. Never committed.
   │
   ├── evals/                  <- Week 8   does it answer WELL?
   ├── loadtest/               <- Week 7   what happens under load
   ├── observability/          <- Week 5   the dashboard stack
   ├── deploy/                 <- Week 8   Kubernetes, portability
   └── guide/                  <- this folder
```

## The three doors

| Door | Method | Answers with |
|---|---|---|
| `/health` | GET | `{"status": "ok"}` |
| `/chat` | POST | `{"reply": "...", "session_id": "..."}` |
| `/chat/stream` | POST | the answer, in pieces, as it arrives |

**Build `/health` first.** It is two lines and cannot fail, so once it answers
you know the plumbing works and everything after that is your handler.

**The session ID** is how a forgetful protocol holds a conversation. The first
reply includes one; send it back next time and your code looks up what was said
before:

```
   request 1   {"message": "where is ORD-1002?"}
   reply 1     {"reply": "Thursday", "session_id": "a3f9"}
   request 2   {"message": "how much was it?", "session_id": "a3f9"}
                                               ^^^^^^^^^^^^^^^^^^^^
                                        your code loads this session's
                                        history and re-sends all of it
```

The model itself remembers nothing. Every turn re-sends the whole conversation.

## Do this

1. Run the service locally:

```bash
make run
```

2. In another terminal, talk to it:

```bash
curl -s -X POST localhost:8080/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"where is my order ORD-1002?"}'
```

3. Build and run the container to prove it is portable:

```bash
make docker-build
make docker-run
```

## Check it works

```bash
make check-week-01
```

## Done when

- The agent answers over `/chat`.
- It runs the same inside the container.

**Pull request:** branch `week-01-<your-name>`, title `week 01: package`.

## Terminal cheat sheet

Everything you need for eight weeks, in one table.

| Command | In plain words |
|---|---|
| `pwd` | where am I standing? |
| `ls` / `ls -la` | what is here? / with detail and hidden files |
| `cd folder` / `cd ..` | go in / go up one |
| `mkdir name` | make a folder |
| `touch name` | make an empty file |
| `cat file` | show me what is in this file |
| `echo "x" > file` | put one line into a file |
| `cmd1 \| cmd2` | feed cmd1's output into cmd2 |
| `rm -r folder` | delete it, and everything inside. No undo. |

**Tab** completes what you are typing. **Up arrow** brings back the last
command. **Ctrl + C** kills whatever is running.

**Silence means it worked.** A terminal only speaks up when something is wrong.

## Two terminals, for the rest of the course

```
   TERMINAL 1                      TERMINAL 2
   ----------                      ----------
   make run                        curl ...
   (never returns --               (asks questions,
    this IS the server)             gets answers)

   leave it alone                  do all your work here
```

## When it says `KODEKEY is not set`

An environment variable is a setting that lives outside your code, attached to
the terminal session. In the **same** terminal as `make run`:

```bash
set -a && source .env && set +a
```

That reads `.env` and exports every line in it.
