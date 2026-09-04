# Week 08: what is portable, and what is Cloud Run

You shipped to Cloud Run. Good — pick one platform and actually finish. But now
it is worth knowing exactly which parts of your work were about *agents in
production* and which parts were about *Google*, because one set transfers to
your next job and the other does not.

Run this to find out:

```bash
grep -rn "gcloud\|cloudrun\|GOOGLE_" app/ evals/ loadtest/ | wc -l
```

The answer is 0. None of your application code knows where it runs. That is
not luck; it is the result of three decisions.

## The three things that made it portable

**1. It is a container.** One `Dockerfile`, one `CMD`, listening on `$PORT`.
Cloud Run, ECS, Fly, Render, Kubernetes and your laptop all run this image
unchanged. Nothing about the image mentions a vendor.

**2. Config comes from the environment.** Every setting — `MODEL`, `REDIS_URL`,
`API_KEYS`, `MAX_STEPS`, `OTEL_ENABLED` — is read with `os.environ.get` and has
a working default. No config file, no build-time branch, no `if PROD:`. This is
the [12-factor](https://12factor.net/config) rule, and it is what lets the same
artifact be a dev service and a prod service.

**3. Telemetry is OpenTelemetry.** `app/otel.py` sends spans to whatever
`OTEL_EXPORTER_OTLP_ENDPOINT` points at. Tempo on your laptop, Cloud Trace in
production, Honeycomb or Datadog at your next company. The destination is an
env var, not a rewrite.

## What is genuinely Cloud Run specific

Four things, all of them *outside* the application:

| Thing | Where it lives | On another platform |
|---|---|---|
| `gcloud run deploy` | `.github/workflows/deploy.yml` | `docker push` + that platform's deploy |
| `--set-secrets OPENROUTER_API_KEY=...` | same file | AWS Secrets Manager, Vault, sealed secrets |
| Revisions + `update-traffic` | rollback step | ECS task definitions, k8s ReplicaSets |
| Scale-to-zero, `--min-instances` | deploy flags | k8s HPA (does not scale to zero without KEDA) |

That is the whole list. Your deployment *pipeline* is vendor-specific. Your
*agent* is not.

## Prove it: same image, second platform

The point of this exercise is not to adopt another platform. It is to confirm
with your own hands that the boundary is where you think it is.

```bash
# build once
docker build -t ship-agent .

# run it with nothing but env vars - this is what every platform does
docker run --rm -p 7000:7000 \
  -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
  -e MODEL=anthropic/claude-sonnet-4.5 \
  -e RATE_LIMIT_PER_MIN=20 \
  ship-agent

curl localhost:7000/health
```

If that works, the image is portable. Deploying it to Fly (`fly launch`) or
Render (connect the repo) is then a five-minute exercise in *their* config, not
a change to your code.

### The two things that will bite you on any move

**Redis.** `REDIS_URL` is one env var, but somebody has to run the Redis.
Memorystore on GCP, ElastiCache on AWS, Upstash anywhere. Without it,
sessions, the rate limit and `/metrics` all silently fall back to per-container
state — correct-looking and wrong, which is the Week 07 lesson.

**Streaming.** `/chat/stream` needs a platform and proxy that do not buffer
responses. `X-Accel-Buffering: no` handles nginx-family proxies. Some CDNs and
load balancers buffer anyway; test TTFB after every migration with
`python -m loadtest.run_load --stream`, because the failure is invisible — you
get a correct answer, just all at once at the end.
