# Guide Week 1 · Package

**Goal:** run the agent locally, then wrap it in a web service and a container.

## The idea

Right now the agent is a script. You wrap it in a small web service (two doors:
`/chat` and `/health`) and seal it in a container so it runs the same everywhere.

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
