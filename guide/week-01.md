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
