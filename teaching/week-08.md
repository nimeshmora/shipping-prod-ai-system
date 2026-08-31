# Week 8 · Gate, roll back and port

**Session goal:** they watch a gate refuse a bad change, rehearse a rollback,
and see what was never platform-specific.

**Branch:** `week-08-gate` → answer key `week-08-solution`

> **INSTRUCTOR** · Four parts and it is the fullest session. The Kubernetes
> section is **reading and discussion only** — no deliverables — and if you run
> short, it is the part to shorten. Do not shorten the gate.

---

## Beat 1 · Ask (10 min)

### "Someone read out one attack from your report that worked."

Two or three. Keep it quick.

### "Your tests are green. Your gate—" *(there isn't one yet)* "—what stops a bad answer shipping?"

Nothing.

### "What does a compiler do for a normal program?"

Catches mistakes before they run.

### "What is the compiler for a prompt?"

**There isn't one.**

> **INSTRUCTOR** · *"Every week so far guarded against FAILURE — the service
> breaking. This week guards against REGRESSION: the service working perfectly
> and the answers getting worse. That is harder, because nothing turns red."*

---

## Beat 2 · Break (10 min)

On the projector, edit the system prompt in `app/agent.py`. Make it subtly
worse — remove the line about never promising refunds, say.

Then:

```bash
make test       # green
make run
# ask about ORD-1043 and a refund
```

The agent now promises refunds. **Every test still passes.** Deploy it and it
would go straight out.

> **INSTRUCTOR** · *"Nothing I have built in seven weeks would have stopped
> that. Not the tests, not the pipeline, not the traces, not the guardrails.
> That is today."*

---

## Beat 3 · Concept (20 min)

### Tier 1 · Deterministic checks

Cases with an input and something that must appear in the output. Runs on every
pull request, **with no API key**, in seconds.

That last bit rests on one decision worth explaining carefully:

> The fake model fakes the model's **decisions** — which tool to ask for — and
> **never the answer.** The `492` comes back from their **real** calculator.

Ask: *"Why does that matter?"*

Let them work it out. If the fake returned `492` itself, the gate would keep
passing after they broke the calculator. **The gate would be testing the fake.**

> **INSTRUCTOR** · **"Fake the model. Never fake your own code."**
>
> The checkpoint proves it by sabotaging the calculator and asserting the gate
> goes red. Show that test running.

### Tier 2 · The judge

`expect_contains` catches an answer going **missing**. It cannot catch an answer
going **bad**:

```
"Your order ORD-1043 is delayed."                      ← good
"ORD-1043 is delayed. Also your refund is approved."   ← contains "delayed",
                                                          and promises a refund
```

**Both pass `expect_contains: "delayed"`. Only one should ship.**

So a second tier asks a model to grade the answer — but only on things you can
point at:

- did it promise a refund?
- did it invent a delivery date the data does not have?
- did it obey the instruction hidden in the order note?

**Never "is this a good answer."** Vague rubrics produce vague grades.

Two rules that keep it honest:

**The judge never gates alone.** No key → skipped. Broken → passes. Unparseable
reply → passes.

> **INSTRUCTOR** · *"A grader that gives different marks to the same answer, wired
> to a blocking gate, teaches your team to ignore the gate. Then you have no gate
> AND a false sense of security."*

**Temperature 0.** *"A grader that disagrees with itself is not a grader."*

### Severity

`high` blocks the deploy. `medium` reports it.

> **INSTRUCTOR** · *"Not every regression should stop a release. Saying so
> explicitly is what stops people disabling the whole thing the first time it is
> inconvenient."*

### Rolling back

The fastest fix in production is almost never a fix.

```bash
gcloud run services update-traffic ship-agent \
  --region us-central1 --to-revisions ship-agent-abc1234=100
```

This works **because of Week 3** — every revision was tagged with the code
version that produced it. Without that they would be guessing, at the worst
possible moment.

---

## Beat 4 · Build (35 min)

They build `evals/run_evals.py`, add judge cases, and wire the gate into CI.
`evals/judge.py` is given.

### Then the actual exercise

> **INSTRUCTOR** · **This is the deliverable. Everyone does it.**

```bash
# break something real — change ORD-1002's delivery day in app/orders.py
make eval          # GATE FAILED
git commit -am "break it"
git push
gh pr create --fill
# watch the check go red. Try to merge. You cannot.
```

**A red pull request is the deliverable, not a failure.**

> **INSTRUCTOR** · Callback to Week 3, which they should now recognise:
>
> **"A gate you have never seen block anything is a gate you are trusting on
> faith."**

Then fix it, push, watch it go green, merge.

### Rehearse the rollback (10 min)

```bash
gcloud run revisions list --service ship-agent --region us-central1
gcloud run services update-traffic ship-agent \
  --region us-central1 --to-revisions PICK_AN_OLDER_ONE=100
curl -s $URL/health
```

**Time them.** *"That is how long an outage lasts if you have practised. Twice
that, at least, if you have not."*

---

## Beat 5 · Port, and finish (25 min)

### What was portable all along (10 min)

Have them run this:

```bash
grep -rn "gcloud\|GOOGLE_" app/ evals/ loadtest/ | wc -l
```

**Zero.**

Ask: *"Why?"* Three decisions, and they made all of them:

1. **It is a container.** One image, `$PORT`, runs anywhere. (Week 1)
2. **Every setting comes from the environment**, with a working default. No
   `if PRODUCTION:` anywhere. (Weeks 1–7)
3. **Telemetry is OpenTelemetry.** The destination is a setting. (Week 5)

What *is* Cloud Run–specific lives entirely outside the app: the deploy command,
the secret wiring, traffic splitting.

> **INSTRUCTOR** · **"Your pipeline is vendor-specific. Your agent is not."**

Prove it — the same image, nothing but settings:

```bash
docker build -t ship-agent .
docker run --rm -p 8080:8080 -e KODEKEY="$KODEKEY" ship-agent
curl localhost:8080/health
```

Two things that bite on any move, worth naming: **Redis** (one setting, but
somebody has to run it) and **streaming** (a buffering proxy breaks it
invisibly — the answer is still correct, just all at once).

### Kubernetes, as information (10 min)

> **INSTRUCTOR** · Read and discuss. **Nothing to build.** The goal is that when
> someone at work says *"we'll run it on EKS behind an HPA with a sidecar
> collector"*, they know exactly which thing they already built is meant.

It is a translation table:

| What they built | In Kubernetes |
|---|---|
| `GET /health` | liveness and readiness probes |
| `--concurrency 80` | a HorizontalPodAutoscaler |
| `--set-env-vars` | a ConfigMap |
| `--set-secrets` | a Secret |
| revisions + traffic split | a Deployment and `kubectl rollout undo` |
| the OTel setting | a collector running alongside |

Plus **one genuinely new idea**, which is worth the ten minutes on its own:

**Liveness vs readiness.** Kubernetes asks two different questions:

- **liveness** — *"is this process wedged? restart it."*
- **readiness** — *"can this take traffic right now? if not, stop routing to it —
  but do not restart it."*

Why an agent cares more than a normal service: their container can be perfectly
alive and unable to serve, because the *model provider* is down.

> **INSTRUCTOR** · *"A liveness probe that fails when the provider is down
> restarts every single box, in a loop, during someone else's outage. You turn a
> degraded service into no service at all. Readiness sheds traffic instead."*
>
> And: **neither probe should ever point at `/metrics`.** A raised error rate
> would pull the whole fleet out of service. `/metrics` is for humans.

Close with the honest part: three reasons to wait on Kubernetes (you now operate
the platform too; no scale-to-zero out of the box; autoscaling an agent is not
CPU-shaped, since it sits idle waiting on a model) and four where it is right
(your company already runs it; you need private networking; compliance; enough
services that per-service config is the bottleneck).

> **INSTRUCTOR** · *"Not because it is more advanced. 'We put the container
> somewhere that runs containers' is the actual skill, and you already have it."*

### Finish (5 min)

```bash
make check-all
```

Every week, one command, all green.

Then read the list out. Eight weeks ago this was a loop in a file. It now:

- runs anywhere, and streams
- survives a redeploy, and a provider outage
- ships itself, tested, and rolls itself back
- cannot run forever or run up a bill
- tells you when it is unhealthy, in English
- withstands injection in the message *and* in the data
- refuses to fetch what it should not reach
- holds its limits when it scales out
- will not let a quality regression through

> **INSTRUCTOR** · Finish on this:
>
> **"That list is the job. The agent loop was the easy part."**

Then the five ideas worth keeping, on a slide they photograph:

1. **A broken agent returns 200 OK.**
2. **The failure mode of an unbounded agent is an invoice, not an outage.**
3. **Tool output is untrusted input.**
4. **Retry the same model before changing models.**
5. **Ask where state lives.**

And the one habit:

> Every week you broke something on purpose before fixing it. **A guardrail you
> have never seen fire is a guardrail you are trusting on faith.** Fire them
> deliberately, on a schedule, in production.

## Homework — the last one

- `make check-all` green
- The **red pull request**, and the green one that followed it
- A rehearsed rollback, with the time it took
- One page: **the three things you would fix first** if this were going live for
  real customers on Monday

> **INSTRUCTOR** · That last question is the best exit assessment in the course.
> `guide/09-finish.md` lists the honest gaps — true streaming, summarising
> memory, an egress proxy, metrics in the log platform, a real eval set. Anyone
> naming two of those unprompted has understood the phase.
