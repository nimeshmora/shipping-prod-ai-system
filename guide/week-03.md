# Guide Week 3 · Automate and lock

**Goal:** deploy automatically on push, and lock the door with keys and a rate
limit.

## The idea

A pipeline deploys for you the same way every time. A key is a ticket at the door
(no key, 401). A rate limit is the bouncer (too many requests, 429).

## Do this

1. Add the deploy pipeline (`.github/workflows/deploy.yml` is already here).
   Read it before you push. Two jobs, one arrow: `deploy` declares
   `needs: gate`, so a failing gate means the deploy never starts. Two
   *separate* workflows on the same trigger would only race, which is the
   mistake this file exists to avoid.
2. Make some keys and store them as `API_KEYS`.
3. The checks are already in `app/guardrails.py` and wired in `app/main.py`.
   Turn them on by setting the env vars:

```bash
export API_KEYS="my-first-key,my-second-key"
export RATE_LIMIT_PER_MIN=20
make run
```

4. Prove the lock:

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost:8080/chat \
  -H 'Content-Type: application/json' -d '{"message":"hi"}'          # 401
curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost:8080/chat \
  -H 'Content-Type: application/json' -H 'X-API-Key: my-first-key' \
  -d '{"message":"hi"}'                                              # 200
```

## Check it works

```bash
make check-week-03
```

## Done when

- No key returns 401. Too many requests return 429.
- Pushing to main deploys automatically.

**Pull request:** `week-03-<your-name>`, `week 03: automate and lock`.
