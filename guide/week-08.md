# Week 8 · Gate, roll back and port

**Goal:** make it impossible for a bad change to reach users — then see what was
never platform-specific in the first place.

**You start from:** a hardened agent whose quality nothing protects.

**You end with:** a gate you have watched block a real change, a rehearsed
rollback, and the same image running somewhere else.

---

## Part 1 — The gate

**Agents have no compiler.** Nothing catches a prompt edit that makes answers
worse. Every other week added a guardrail against *failure*; this one guards
against *regression*, which is harder because the service stays green.

### Tier 1 — deterministic, free, gates every PR

`expect_contains` and `expect_blocked`. Runs in CI with **no API key**, because
of one design decision worth stating plainly:

> `_fake_model` fakes the model's **decisions** — which tool to ask for — and
> never the answer. The `492` comes back from your **real** calculator through a
> real `tool_result`.

If the fake returned `492` itself, the gate would still pass after you broke the
calculator, and this week would be teaching a lie.

**Fake the model. Never fake your own code.**

The checkpoint proves this by sabotaging `calculator` and asserting the gate goes
red.

### Tier 2 — the judge, for regressions substrings cannot see

`expect_contains` catches an answer going **missing**. It cannot catch an answer
going **bad**:

```
"Your order ORD-1043 is delayed."                       <- good
"ORD-1043 is delayed. Also your refund is approved."    <- contains "delayed",
                                                           and promises a refund
                                                           nobody agreed to
```

Both pass `expect_contains: "delayed"`. Only one should ship.

So `evals/judge.py` asks a model to grade specific, pointable-at properties: *did
it promise a refund, did it invent a date, did it obey the note in the data.*
Never "is this a good answer" — vague rubrics produce vague grades.

**Two rules keep this honest:**

1. **The judge never gates alone.** No key → skipped. Broken judge → passes.
   Unparseable reply → passes. A non-deterministic grader wired to a blocking
   gate teaches the team to ignore the gate.
2. **Temperature 0.** A grader that gives different marks to the same answer is
   not a grader.

### Severity, and the exercise

`high` blocks. `medium` reports. Not every regression should stop a release, and
saying so explicitly is what stops people disabling the whole gate.

**Now the actual deliverable: ship a change the gate correctly refuses.**

```bash
# break something real
# e.g. in app/orders.py, change ORD-1002's eta
make eval          # GATE FAILED
git commit && git push && gh pr create
# watch the check go red, and confirm you cannot merge
```

**A red PR is the deliverable, not a failure.** A gate you have never seen block
anything is a gate you are trusting on faith.

---

## Part 2 — The rollback

The fastest fix in production is almost never a fix.

```bash
gcloud run revisions list --service ship-agent --region us-central1

# roll traffic back to a known-good revision
gcloud run services update-traffic ship-agent \
  --region us-central1 --to-revisions ship-agent-abc1234=100
```

This works because `deploy.yml` tags every revision with its commit SHA
(`--revision-suffix`). Without that you get `ship-agent-00042-xyz` and no way to
know which commit it holds — so rollback becomes guesswork at the worst possible
moment.

**Rehearse it now, while nothing is broken.** Time yourself.

---

## Part 3 — What was portable all along

Run this:

```bash
grep -rn "gcloud\|GOOGLE_" app/ evals/ loadtest/ | wc -l
```

**Zero.** Not luck — three decisions:

1. **It is a container.** One image, `$PORT`, runs anywhere.
2. **Config comes from the environment.** Every setting has a working default;
   there is no `if PROD:` anywhere.
3. **Telemetry is OpenTelemetry.** The destination is an env var.

What *is* Cloud Run–specific lives entirely outside the app: `gcloud run deploy`,
`--set-secrets`, revision traffic-splitting, scale-to-zero. **Your pipeline is
vendor-specific. Your agent is not.**

Prove it — same image, nothing but env vars:

```bash
docker build -t ship-agent .
docker run --rm -p 7000:7000 -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" ship-agent
curl localhost:7000/health
```

Read **[`deploy/PORTABILITY.md`](../deploy/PORTABILITY.md)** for the full
boundary, including the two things that bite on any move (Redis, and streaming
through a buffering proxy).

---

## Part 4 — Kubernetes, as information

Read **[`deploy/KUBERNETES.md`](../deploy/KUBERNETES.md)**. **Do not build it.**
No checkpoints, nothing to submit.

The point is that when someone says *"we'll run it on EKS behind an HPA with a
sidecar collector"*, you know exactly which thing you already built they mean.

It is a translation table — `/health` → liveness/readiness probes, concurrency →
HPA, `--set-env-vars` → ConfigMaps, revisions → Deployments — plus the one
genuinely new idea:

> **Liveness vs readiness.** Your container can be perfectly alive and unable to
> serve, because the model provider is down. A *liveness* probe that fails on
> "provider down" restarts every pod during an outage, turning a degraded service
> into no service. *Readiness* sheds traffic instead. And neither should ever
> point at `/metrics`.

Also in there: three honest reasons to wait on Kubernetes, and four where it is
genuinely right.

---

## Check it works

```bash
make check-week-08
make check-all         # every week, one command
```

---

## Done when

- The gate passes on good code, and **you have watched it block a bad PR**
- Sabotaging a tool turns the gate red (it tests your code, not a fake answer)
- Judge cases exist for quality regressions, and the judge cannot break the build
- The deploy job declares `needs:` on the gate, and the gate runs on PRs
- You have **rehearsed a rollback** to a tagged revision
- The same image runs on a second platform
- You have read `deploy/KUBERNETES.md`
- `make check-all` passes

---

## You have shipped it

Eight weeks ago this was a loop in a file. It is now a service that:

- runs anywhere, and streams
- survives a redeploy, and a provider outage
- ships itself, tested, and rolls itself back
- cannot run forever or run up a bill
- tells you when it is unhealthy, in English
- withstands injection in the message *and* in the data
- refuses to fetch what it should not reach
- and will not let a quality regression through

That list is the job. The agent loop was the easy part.
