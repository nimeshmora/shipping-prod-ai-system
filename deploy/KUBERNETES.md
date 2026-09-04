# Week 08 appendix: the same agent, in Kubernetes vocabulary

**Read this. Do not build it.** There are no checkpoints here and nothing to
submit. The goal is that when someone at work says "we'll run it on EKS behind
an HPA with a sidecar collector", you know precisely which thing you already
built they are talking about.

Everything below is a *translation*, not new material. You have already solved
all of these problems. Kubernetes solves the same problems with different nouns.

## The translation table

| What you built | Cloud Run | Kubernetes |
|---|---|---|
| `GET /health` | health check | `livenessProbe` + `readinessProbe` |
| `--concurrency 80` | per-instance concurrency | `HorizontalPodAutoscaler` on CPU/RPS |
| `--min-instances 1` | warm instance | `replicas: 1`, no scale-to-zero (needs KEDA) |
| `--set-env-vars` | env vars | `ConfigMap` |
| `--set-secrets` | Secret Manager | `Secret` (+ External Secrets Operator) |
| revisions + `update-traffic` | revision rollback | `Deployment` + `kubectl rollout undo` |
| `--revision-suffix $SHA` | tagged revision | image tag `:$SHA`, never `:latest` |
| OTel exporter env var | Cloud Trace | collector `DaemonSet` or sidecar |
| Redis (Memorystore) | managed | `StatefulSet`, or stay managed |
| `--timeout 3600` | request timeout | Ingress/Gateway timeout annotations |

## The one genuinely new idea: liveness vs readiness

Cloud Run has one health check. Kubernetes has two, and the difference matters
more for an agent than for an ordinary service.

- **liveness** — "is this process wedged? restart it."
- **readiness** — "can this pod take traffic right now? if not, stop routing to
  it, but do NOT restart it."

Why an agent cares: your container can be perfectly alive and still unable to
serve — the model provider is down, or Redis is unreachable. A *liveness* probe
that fails on "provider is down" restarts every pod in a loop during an outage,
turning a degraded service into no service. Readiness sheds traffic instead.

Which means `/health` and `/metrics` map to *different* probes:

```yaml
livenessProbe:                  # is the process alive?
  httpGet: { path: /health, port: 7000 }
  periodSeconds: 10
  failureThreshold: 3

readinessProbe:                 # should it receive requests?
  httpGet: { path: /health, port: 7000 }
  periodSeconds: 5
```

Note both point at `/health`, not `/metrics`. Wiring a readiness probe to
`/metrics` and failing it when `status == "degraded"` is a tempting mistake: a
raised error rate would then pull every pod out of service at once. `/metrics`
is for humans and alerts. Probes are for the scheduler.

## What a Deployment for this agent looks like

Illustrative — read it, do not apply it:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: ship-agent }
spec:
  replicas: 2
  selector: { matchLabels: { app: ship-agent } }
  template:
    metadata: { labels: { app: ship-agent } }
    spec:
      containers:
      - name: agent
        image: ghcr.io/you/ship-agent:a1b2c3d      # never :latest
        ports: [{ containerPort: 7000 }]
        env:
        - name: REDIS_URL
          valueFrom: { configMapKeyRef: { name: agent-config, key: redis-url } }
        - name: OPENROUTER_API_KEY
          valueFrom: { secretKeyRef: { name: agent-secrets, key: kodekey } }
        resources:
          # An agent is I/O bound: it spends its life waiting on a model.
          # Requests are what the scheduler packs on; limits are the ceiling.
          # A CPU limit that is too tight makes p95 worse in a way that looks
          # like a slow model.
          requests: { cpu: 100m, memory: 256Mi }
          limits:   { cpu: 1000m, memory: 512Mi }
        livenessProbe:
          httpGet: { path: /health, port: 7000 }
        readinessProbe:
          httpGet: { path: /health, port: 7000 }
```

## Three things that are harder in Kubernetes, and are honest reasons to wait

1. **You now operate the platform.** Cloud Run has no nodes, no upgrades, no
   etcd. A cluster is a system that itself needs monitoring, patching and an
   on-call rotation. That is a real, recurring cost paid by a team, not a
   deploy flag.
2. **No scale-to-zero out of the box.** For a bursty internal agent, running
   two pods around the clock can cost more than Cloud Run's per-request
   billing. KEDA adds it back, which is another component to run.
3. **Autoscaling an agent is not CPU-shaped.** Your pods sit idle waiting on
   the model, so CPU stays low while latency climbs — an HPA on CPU will not
   react. You want concurrency or queue-depth metrics, which means the metrics
   pipeline becomes load-bearing infrastructure.

## When Kubernetes is genuinely the right answer

- Your company already runs it, and a second deployment story is the larger cost
- You need in-cluster networking to things with no public endpoint
- Compliance requires workloads inside a VPC you control
- You run enough services that per-service platform config is the bottleneck

Not because it is more advanced. "We put the container somewhere that runs
containers" is the actual skill, and you already have it — the image, the config
contract and the telemetry are identical in both worlds. That is the whole point
of this appendix.
