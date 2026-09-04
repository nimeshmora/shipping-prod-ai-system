# Guide Week 5 · See

**Goal:** write one JSON record per turn so you can see what happened.

## The idea

A flight recorder. Each turn quietly writes down steps, tools used, timing, and any
error. Secrets are blanked out before anything is written.

## Do this

1. The trace is already in `app/trace.py`, filled in `app/agent.py`, and printed
   in `app/main.py`.
2. Run the service and make a request, then look at the JSON line it prints:

```bash
make run
# in another terminal, send a /chat request, then read the server log line
```

3. Confirm no key or secret appears in the record.

## Check it works

```bash
make check-week-05
```

## The other half: monitoring

Writing traces is **telemetry**. Reading them is **monitoring**, and only the
second one wakes you up. This matters more for agents than for ordinary
services, because a broken agent usually still returns `200 OK` - nothing
crashes, the answers just quietly get worse.

`app/monitor.py` keeps the recent turns and `/metrics` reports them:

```bash
curl -s localhost:7000/metrics
```

Four signals, and what a bad number means:

| Signal | Creeping up means |
|---|---|
| `error_rate` | turns are failing outright |
| `p95_duration_ms` | the slow tail users actually feel |
| `avg_steps` | the model is looping or confused |
| `fallback_rate` | your primary provider is struggling |

When one crosses its threshold, `status` becomes `degraded` and `alerts`
explains it in plain English.

## Done when

- Every request prints one JSON record, with `cost_usd`.
- No secret appears in it.
- `/metrics` answers, and turns `degraded` when the agent misbehaves.

**Pull request:** `week-05-<your-name>`, `week 05: see`.
