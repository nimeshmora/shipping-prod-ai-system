# Week 3 · Automate and lock

**Goal:** stop deploying by hand, and stop letting strangers spend your budget.

**You start from:** a live service you deploy from your laptop, open to anyone.

**You end with:** `git push` → tested → deployed → verified, and a 401 for
anyone without a key.

---

## Two problems, one week

Last week you deployed by hand. That worked, and it does not scale, for reasons
that have nothing to do with typing:

- Nothing ran your tests. You could have shipped a broken agent and only found
  out from a customer.
- It deployed whatever was in your working directory — not what is on `main`,
  not what anyone reviewed.
- Your key went through your shell history.
- Nobody else on your team can do it.

And your URL is `--allow-unauthenticated`. An open LLM endpoint is somebody
else's free compute. Scanners sweep for these. The first you hear about it is
the bill.

---

## Part 1 — The pipeline

Two workflow files, and **one detail that matters more than the rest**:

```yaml
jobs:
  test:
    # ... pytest, checkpoints ...

  deploy:
    needs: test          # <-- the arrow. No tests, no deploy.
```

**Two separate workflows both triggered by `push: main` do NOT gate each
other.** They start at the same time and race. You get a green tick on a broken
deploy, and a pipeline that looks like a safety net while catching nothing.
`needs:` only works between jobs *inside one workflow* — which is why the tests
live in `deploy.yml` rather than in their own file.

`test.yml` runs on pull requests only, so there is no duplicate run on `main`.
Then make it a **required status check** in branch protection and require PRs
into `main`. That is the layer that actually protects you: a workflow that only
reports is a workflow people learn to ignore.

Three more things in `deploy.yml` worth reading:

**`--revision-suffix "${GITHUB_SHA::7}"`** — tags every revision with its
commit. Without it you get `ship-agent-00042-abc` and no way to tell which
commit it holds, so "roll back to the last good one" becomes guesswork at the
worst possible moment.

**`--set-secrets`, never `--set-env-vars`, for the key** — env vars are visible
in the Cloud Run console and in `gcloud run services describe` output. Anyone
with read access to the project can read them.

**A health check after the deploy, with a rollback** — `gcloud run deploy`
exiting 0 means *the revision was created*. It says nothing about whether the
process inside it can serve a request. A deploy that exits 0 is not the same as
a service that answers, so poll `/health` and roll traffic back if it never
does.

You will need two repo secrets: `GCP_SA_KEY` (a service-account JSON) and,
in Secret Manager, `api-keys` alongside `kodekey`.

---

## Part 2 — The lock

`app/guardrails.py` is new, and every rule this course adds will live there. Two
rules this week.

### The key

```bash
curl -s -X POST $URL/chat -H 'x-api-key: your-key' ...
```

- **401, not 403.** The caller has not proven who they are. Say nothing about
  *why* the key failed — that distinction only helps someone guessing.
- **Keys are read fresh on every call**, from `API_KEYS`. Build the set once at
  import time and the only way to revoke a leaked key is to ship new code.
- **`API_KEYS` unset means auth is off.** A local-dev convenience and a genuine
  production risk: a service deployed without that variable is wide open.

### The rate limit

A **sliding** window, not a fixed one. The naive version — a counter on a
per-minute key — lets a caller send the full allowance at 11:59:59 and the full
allowance again at 12:00:00. A "20/min" limit that permits 40 requests in one
second. Dropping timestamps older than 60 seconds counts what actually happened.

Why an agent needs this more than an ordinary API: one request costs real money
at a provider and may run several model calls. A loop in someone's script is a
bill, not just load.

### Both endpoints, and the ordering

`/chat` **and** `/chat/stream` go through the same checks. The day you add a rule
to one and forget the other is the day you have an unauthenticated path into a
paid model.

For the streaming route the checks run **before the response starts**. Once the
first frame goes out, HTTP 200 has already been sent and there is no status code
left to reject with — a rejected caller would get a 200 with an error frame
inside it. Check first, and they get an honest 401.

Guardrails also run before *any* work: rejecting a request that was never going
to be allowed should cost nothing, and certainly not a model call.

---

## Do this

```bash
# locally
export API_KEYS=local-dev-key
make run

curl -s -X POST localhost:8080/chat -H 'Content-Type: application/json' \
  -d '{"message":"hi"}'                                  # 401

curl -s -X POST localhost:8080/chat -H 'Content-Type: application/json' \
  -H 'x-api-key: local-dev-key' -d '{"message":"hi"}'    # 200

# flood it
for i in $(seq 1 25); do
  curl -s -o /dev/null -w "%{http_code} " -X POST localhost:8080/chat \
    -H 'Content-Type: application/json' -H 'x-api-key: local-dev-key' \
    -d '{"message":"hi"}'
done; echo                                               # 200s then 429s
```

Then commit, open a PR, watch `test.yml` run, merge, and watch `deploy.yml` test
→ deploy → verify.

**Break it on purpose:** push a commit with a failing test and confirm the deploy
never starts. A gate you have not seen block anything is a gate you are trusting
on faith.

---

## Check it works

```bash
make check-week-03
```

It inspects your workflow files too — including whether the deploy job really
declares `needs:`, and whether any secret is being passed as an env var.

---

## Done when

- A push to `main` runs the tests and only then deploys
- A failing test **stops** the deploy (you have watched it happen)
- The pipeline checks `/health` after deploying and rolls back if it fails
- No key requests get 401; too many get 429; both endpoints enforce both
- `make check-week-03` passes

---

## Think about

1. Your rate limiter counts in a Python dict, inside one container. Cloud Run
   runs several. What is your real limit? *(Named now, fixed in Week 7 — after a
   load test makes the cost visible.)*
2. Nothing yet stops one *authorised* caller from running your loop 50 times in
   a single turn. *(Week 4.)*
3. A deploy succeeded and the service answers. How would you know the answers
   got *worse*? *(Weeks 5 and 8.)*
