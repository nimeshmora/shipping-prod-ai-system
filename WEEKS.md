# What each week adds to this project

You improve the same project every week. This is the map: what you build, which
files it touches, and which settings turn it on. Check your work against the
finished files already in this repo.

## Week 01, Package

Build the agent loop and run it locally, then wrap it in the service and a
container. Add streaming, because 8 seconds of nothing feels broken.

- Files: `app/agent.py`, `app/orders.py`, `app/main.py`, `app/memory.py`,
  `app/stream.py` (SSE), `Dockerfile`
- Run: `make run`, then `curl` the `/chat` endpoint
- Done when: `POST /chat` answers locally and in a container, and
  `POST /chat/stream` sends `start` / `token` / `done` frames

## Week 02, Deploy

Put the container on Cloud Run, watch in-container memory die on redeploy, then
move memory to Redis.

- Files: `app/memory.py` (Redis path, already here)
- Settings: `REDIS_URL` (empty = dict; set = Redis)
- Done when: a conversation survives a redeploy

## Week 03, Automate and lock

A pipeline replaces manual deploys. Auth and a rate limit keep strangers out.

- Files: `.github/workflows/deploy.yml`, `app/guardrails.py` (`check_api_key`,
  `check_rate_limit`), wired in `app/main.py`
- Settings: `API_KEYS`, `RATE_LIMIT_PER_MIN`
- Done when: no key returns 401, too many requests return 429

## Week 04, Cap

The loop could run forever or run up a bill. Add step and token budgets.

- Files: `app/guardrails.py` (`Budget`), used in `app/agent.py`;
  `app/memory.py` (`trim`) bounds the context
- Settings: `MAX_STEPS`, `MAX_TOKENS_PER_TURN`, `MAX_HISTORY_MESSAGES`,
  `MODEL_TIMEOUT_SECONDS`
- Done when: a runaway turn stops itself, and a long session stops growing

## Week 05, See

Bad answers are silent. Write one JSON trace per turn - then read them, because
a broken agent still returns 200 OK.

- Files: `app/trace.py` (write), `app/monitor.py` (read), `/metrics` in
  `app/main.py`; `app/main.py` catches *every* exception so a failed turn is
  recorded - without that, a total outage reports a 0% error rate
- Settings: `COST_PER_1M_INPUT`, `COST_PER_1M_OUTPUT`, `MONITOR_WINDOW`,
  `ALERT_ERROR_RATE`, `ALERT_P95_MS`, `ALERT_FALLBACK_RATE`, `ALERT_AVG_STEPS`,
  `OTEL_ENABLED`, `OTEL_TARGET`
- Cost is priced from the input/output split, not a blended average: output
  tokens cost 3-5x input, so a blended rate overstates a long-context agent
- Done when: every request prints one JSON line with steps, tools, tokens and
  `cost_usd`; and `/metrics` turns "degraded" with a plain-English alert when
  turns start failing, slowing, looping, or falling back

## Week 06, Debug and survive

Find a planted bug from traces, then survive a model outage - retrying the same
model before changing models.

- Files: `app/agent.py` (`call_model`: retry with jittered backoff on the
  primary, then fall back; a timeout on every call)
- Settings: `FALLBACK_MODEL`, `MAX_RETRIES`, `RETRY_BASE_SECONDS`,
  `RETRY_MAX_SECONDS`
- Instructor: `make plant-bug` before the session, `make fix-bug` after
- Done when: a single 429 is absorbed by a retry and never reaches the
  fallback; a real outage still yields an answer with `provider: fallback` in
  the trace; `retry_rate` on `/metrics` shows the flakiness either way

## Week 07, Attack

Red-team your own deployed agent: injection, cost, SSRF, and load.

- Files: `app/guardrails.py` (`check_input_length`, `check_blocked_input`,
  `check_url`), wired in `app/main.py`; `check_tool_output` wired in
  `app/agent.py` so a tool result cannot smuggle instructions back to the model
  (try `ORD-1043` - its note carries an instruction, like real customer data);
  `fetch_url` in `app/agent.py` is the real SSRF surface; `app/store.py` moves
  the rate limit and monitor window into shared state; `loadtest/run_load.py`
- Settings: `MAX_INPUT_CHARS`, `MAX_TOOL_OUTPUT_CHARS`, `FETCH_TIMEOUT_SECONDS`,
  `FETCH_MAX_CHARS`, `REDIS_URL`
- Run: `make load`, `make load-stream`
- Done when: oversized and dangerous input are refused; an instruction hidden
  in a tool result is neutralised; `fetch_url` refuses the cloud metadata
  address, `file://`, private IPs and non-allowlisted hosts; and the rate limit
  holds under `make load` with `shared_state: true` on `/metrics`
- The deferred fix, now due: the Week 03 rate limiter counted per container, so
  5 instances meant 5x the limit. Load makes that visible; `app/store.py` fixes
  it.

## Week 08, Gate, roll back and port

An eval gate blocks a bad change before it ships. Practise rolling back. Then
see what was portable all along.

- Files: `evals/cases.json`, `evals/run_evals.py`, `evals/judge.py`,
  `.github/workflows/eval.yml`, `deploy/PORTABILITY.md`, `deploy/KUBERNETES.md`
- Run: `make eval` (deterministic, no key), `make eval-judge` (quality, needs
  a key)
- Two tiers, on purpose: `expect_contains` catches an answer going *missing*;
  the judge catches an answer going *bad*. The judge never gates alone - a
  non-deterministic grader wired to a blocking gate teaches the team to ignore
  the gate.
- Done when: a high-severity failure makes the gate exit non-zero and blocks
  the PR; you have rolled back to a tagged revision; and the same image runs on
  a second platform
- Read, do not build: `deploy/KUBERNETES.md` maps everything you built onto
  k8s vocabulary, so you can hold the conversation without spending three weeks
  on YAML
