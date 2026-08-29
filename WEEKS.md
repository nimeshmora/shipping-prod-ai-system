# What each week adds to this project

You improve the same project every week. This is the map: what you build, which
files it touches, and which settings turn it on. Check your work against the
finished files already in this repo.

## Week 01, Package

Build the agent loop and run it locally, then wrap it in the service and a
container.

- Files: `app/agent.py`, `app/orders.py`, `app/main.py`, `app/memory.py`, `Dockerfile`
- Run: `make run`, then `curl` the `/chat` endpoint
- Done when: `POST /chat` answers locally and in a container

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
- Settings: `MAX_STEPS`, `MAX_TOKENS_PER_TURN`, `MAX_HISTORY_MESSAGES`
- Done when: a runaway turn stops itself, and a long session stops growing

## Week 05, See

Bad answers are silent. Write one JSON trace per turn - then read them, because
a broken agent still returns 200 OK.

- Files: `app/trace.py` (write), `app/monitor.py` (read), `/metrics` in
  `app/main.py`; `app/main.py` catches *every* exception so a failed turn is
  recorded - without that, a total outage reports a 0% error rate
- Settings: `COST_PER_1M_INPUT`, `COST_PER_1M_OUTPUT`, `MONITOR_WINDOW`,
  `ALERT_ERROR_RATE`, `ALERT_P95_MS`, `ALERT_FALLBACK_RATE`, `ALERT_AVG_STEPS`
- Done when: every request prints one JSON line with steps, tools, tokens and
  `cost_usd`; and `/metrics` turns "degraded" with a plain-English alert when
  turns start failing, slowing, looping, or falling back

## Week 06, Debug

Find a planted bug from traces, then survive a model outage with a fallback.

- Files: `app/agent.py` (`call_model` tries primary then fallback, with a
  timeout on every call)
- Settings: `FALLBACK_MODEL`, `MODEL_TIMEOUT_SECONDS`
- Instructor: `make plant-bug` before the session, `make fix-bug` after
- Done when: the primary failing still yields an answer; the trace shows
  `provider: fallback`

## Week 07, Attack

Harden the tools and inputs so a hostile message cannot do damage.

- Files: `app/guardrails.py` (`check_input_length`, `check_blocked_input`,
  `check_url`), wired in `app/main.py`; `check_tool_output` wired in
  `app/agent.py` so a tool result cannot smuggle instructions back to the model
  (try `ORD-1043` - its note carries an instruction, like real customer data)
- Settings: `MAX_INPUT_CHARS`, `MAX_TOOL_OUTPUT_CHARS`
- Done when: oversized input, dangerous input, and non-allowlisted URLs are
  refused, and an instruction hidden in a tool result is neutralised

## Week 08, Gate

An eval gate blocks a bad change before it ships. Practise rolling back.

- Files: `evals/cases.json`, `evals/run_evals.py`, `.github/workflows/eval.yml`
- Run: `make eval`
- Done when: a high-severity failure makes the gate exit non-zero and blocks the PR
