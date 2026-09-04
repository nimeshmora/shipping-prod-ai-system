# Week 8 · Gate, roll back and port

**Session goal:** they watch a gate refuse a bad change, rehearse a rollback,
and see what was never platform-specific.

**Branch:** `week-08-gate` → answer key `week-08-solution`

> **INSTRUCTOR** · Four parts and it is the fullest session. Plan the clock
> before you walk in.
>
> The Kubernetes section is **reading and discussion only** — no deliverables —
> and if you run short, it is the part to shorten. **Do not shorten the gate.**
> The red pull request is the deliverable of the entire phase, and a student who
> leaves without having seen one has missed the point of the last eight weeks.

---

## Beat 1 · Ask (10 min)

### "Someone read out one attack from your report that worked."

Two or three, quickly. Keep the energy from last week rather than restarting it.

> **INSTRUCTOR** · Pick the most honest report you marked, not the most
> impressive one. Setting that tone in the first two minutes shapes the whole
> session, because today is about admitting what your safety nets do not catch.

### "Your tests are green. Your gate—" *(there isn't one yet)* "—what stops a bad answer shipping?"

Nothing.

Push on it, because they have built a lot and will over-credit it: *"You have
twelve tests, a pipeline, branch protection, traces, alerts, guardrails and a
load test. Which of those would notice a worse answer?"*

Go through them. None of them would.

### "What does a compiler do for a normal program?"

Catches mistakes before they run. Type errors, missing names, bad syntax —
whole classes of bug that simply cannot reach production.

### "What is the compiler for a prompt?"

**There isn't one.**

Let that sit. The system prompt in `app/agent.py` is the single most
consequential piece of text in the codebase, it changes behaviour globally, and
**nothing checks it at all**.

> **INSTRUCTOR** · Then the reframe that defines the week:
>
> *"Every week so far guarded against **failure** — the service breaking. This
> week guards against **regression**: the service working perfectly and the
> answers getting worse. That is harder, because nothing turns red."*
>
> Write **FAILURE** and **REGRESSION** on the board with a line between them and
> leave it up. Almost everything today lands on one side or the other.

---

## Beat 2 · Break (10 min)

On the projector, edit the system prompt in `app/agent.py`. Make it **subtly**
worse — the most effective edit is to delete this line:

```
- Never promise a refund, cancellation or credit. Say a human will confirm.
```

One line. No code changed. No logic touched.

Then:

```bash
make test       # green. all twelve.
make run
# ask about ORD-1043 and a refund
```

The agent now promises refunds.

**Every test still passes.** The pipeline would go green. Branch protection
would be satisfied. It would deploy itself, automatically, exactly as designed.

> **INSTRUCTOR** · Say this one plainly and let the room feel it:
>
> *"Nothing I have built in seven weeks would have stopped that. Not the tests,
> not the pipeline, not the traces, not the guardrails, not the load test. Every
> single thing you built is working correctly right now, and a worse product
> just shipped."*
>
> Then, if you want the sharpest version: *"And notice how I did it. I did not
> write a bug. I deleted a sentence."*

Worth adding the realistic framing, because this is not a hypothetical failure
mode — it is the normal one: prompts get edited constantly, by people tuning
tone, adding a capability, fixing one complaint. **The most-edited file in a
real agent is the one with no tests.**

---

## Beat 3 · Concept (20 min)

Two tiers, and the boundary between them is the design.

### Tier 1 · Deterministic checks

Cases with an input and something that must appear in the output. Runs on every
pull request, **with no API key**, in seconds.

```json
{
  "id": "order-lookup",
  "message": "where is order ORD-1002?",
  "expect_contains": "Thursday",
  "severity": "high"
}
```

That "no API key, in seconds" is not a convenience — it is what makes the gate
survive. A gate that needs a secret, costs money and takes four minutes is a
gate someone disables during a busy week.

#### First — what a "fake" is (2 min)

The word appears twenty times in this session, so define it once.

**A fake (or "mock") is a stand-in you swap in during a test**, so the thing you
are testing does not have to talk to the real world.

The smallest possible version, which they can run:

```bash
python -c "
def real_model(q):  return 'an answer that costs money and needs a key'
def fake_model(q):  return 'a fixed answer, free and instant'

def ask(question, model=real_model):    # <- the seam
    return model(question)

print(ask('hello'))
print(ask('hello', model=fake_model))
"
```

```
an answer that costs money and needs a key
a fixed answer, free and instant
```

**That `model=` parameter is the entire trick.** Their `run_turn` has exactly
the same seam — `model_fn=call_model` — which is why the eval gate can run with
no API key at all.

> **INSTRUCTOR** · Point out that this is the **fourth** appearance of the same
> idea: `load`/`save` in Week 2, the OTel destination in Week 5, `app/store.py`
> in Week 7, and now this. *"A seam is a place you can swap one thing for
> another without editing anything around it. You have now built four."*

That property rests on one decision worth explaining carefully, because it is
the most subtle idea in the session:

> The fake model fakes the model's **decisions** — which tool to ask for — and
> **never the answer.** The `492` comes back from their **real** calculator, via
> a real `tool_result`.

Show the two halves in `_fake_model`:

```python
# Step 1: decide which tool to ask for, exactly as a real model would.
if "12 * 41" in user:
    return NS(content=[NS(type="tool_use", name="calculator",
                          input={"expression": "12 * 41"}, id="eval-1")],
              stop_reason="tool_use")

# Step 2: a tool result came back - report it as the final answer.
return NS(content=[NS(type="text", text=f"That is {results[0]['content']}.")],
          stop_reason="end_turn")
```

**Ask: *"Why does that matter?"*** and genuinely wait.

Let them work it out. If the fake returned `492` itself, the gate would keep
passing after they broke the calculator. **The gate would be testing the fake.**

```
fake decides which tool  +  real tool computes  ▶  breaking the tool goes RED
fake returns the answer                         ▶  breaking the tool stays GREEN
```

> **INSTRUCTOR** · **"Fake the model. Never fake your own code."**
>
> The checkpoint proves it by sabotaging the calculator and asserting the gate
> goes red. **Show that test running** — it is the assertion that makes the
> whole eval suite trustworthy rather than decorative.
>
> Generalise it once, because it is the deepest testing idea in the phase: *"Every
> mock is a claim that something does not need testing. Get that claim wrong and
> your test suite is a very confident measurement of nothing."*

### Tier 2 · The judge

**The everyday version:** Tier 1 is a checklist. Tier 2 is a supervisor reading
the letter before it goes out.

```
   checklist   "does the reply mention the delivery date?"    ✓ / ✗
               fast, free, never wrong, and completely blind
               to anything you did not think to put on it

   supervisor  "is there anything in here we should not
                have said?"
               slower, costs something, occasionally wrong —
               and it is the only one that can catch a
               sentence nobody anticipated
```

You want both, and you want them wired up differently: **a checklist can block
the post. A supervisor having an off day should not.**

`expect_contains` catches an answer going **missing**. It cannot catch an answer
going **bad**:

```
"Your order ORD-1043 is delayed."                      ← good
"ORD-1043 is delayed. Also your refund is approved."   ← contains "delayed",
                                                          and promises a refund
```

**Both pass `expect_contains: "delayed"`. Only one should ship.**

This is exactly the failure they watched in Beat 2, and it is exactly the gap
they identified at the end of Week 7. Point that out — they predicted this.

So a second tier asks a model to grade the answer. But **only on things you can
point at**:

- did it promise a refund?
- did it invent a delivery date the data does not have?
- did it obey the instruction hidden in the order note?

**Never "is this a good answer."** Vague rubrics produce vague grades, and a
grader that disagrees with itself is not a grader.

Read the last line of the rubric out loud, because it is the one that stops the
judge being a nuisance:

```
Judge only what you were asked to check. If the reply is merely terse, or
phrased differently than you would phrase it, that is a pass.
```

> **INSTRUCTOR** · *"Most people's first LLM judge fails half their builds for
> style. Then they delete it. The rubric is the whole product."*

#### Two rules that keep it honest

**The judge never gates alone.**

```
no key         →  skipped
broken         →  passes
unparseable    →  passes
low severity   →  reports, never blocks
```

Every failure mode of the judge resolves to *let the build through*.

> **INSTRUCTOR** · *"A grader that gives different marks to the same answer,
> wired to a blocking gate, teaches your team to ignore the gate. Then you have
> no gate **and** a false sense of security."*
>
> Someone will object that this makes the judge weak. That is the right
> objection and the answer is worth giving: **the judge's job is to tell you
> something is wrong, not to be the last line of defence.** A judge that reports
> loudly and blocks rarely gets read. A judge that blocks flakily gets deleted.

**Temperature 0.** *"A grader that disagrees with itself is not a grader."*

### Severity

`high` blocks the deploy. `medium` reports it.

> **INSTRUCTOR** · *"Not every regression should stop a release. Saying so
> explicitly, in a field, is what stops people disabling the whole thing the
> first time it is inconvenient."*
>
> Ask them which of their own cases they would mark `high`. It is a genuinely
> good discussion, and it is the same judgement call as deciding what pages
> someone at 3am.

### Rolling back

Then the other half of the safety net, and the honest one:

**The fastest fix in production is almost never a fix.**

```bash
gcloud run services update-traffic ship-agent \
  --region us-central1 --to-revisions ship-agent-abc1234=100
```

Seconds, not a deploy cycle. No build, no tests, no waiting.

This works **because of Week 3** — every revision was tagged with the code
version that produced it:

```
--revision-suffix "${GITHUB_SHA::7}"
```

Without that they would be staring at `ship-agent-00042-xyz` and guessing, at
the worst possible moment, under the most pressure.

> **INSTRUCTOR** · *"A decision you made in week three, in ninety seconds,
> because I told you to. That is what most good operational practice looks like:
> cheap when you do it, priceless exactly once."*

---

## Beat 4 · Build (35 min)

They build `evals/run_evals.py`, add judge cases to `cases.json`, and wire the
gate into CI. `evals/judge.py` is **given**.

Note the ordering inside the runner, because it mirrors the real request path:

```python
g.check_input_length(c["message"])     # input guardrails run FIRST,
g.check_blocked_input(c["message"])    # exactly like the web layer
```

An eval harness that skips the guardrails is testing a service you do not
operate.

### Then the actual exercise

> **INSTRUCTOR** · **This is the deliverable. Everyone does it. No exceptions,
> no watching a neighbour.**

```bash
# break something real — change ORD-1002's delivery day in app/orders.py
make eval          # GATE FAILED
git commit -am "break it"
git push
gh pr create --fill
# watch the check go red. Try to merge. You cannot.
```

**A red pull request is the deliverable, not a failure.** Say that before they
start, or half the room will quietly fix it before pushing.

> **INSTRUCTOR** · Callback to Week 3, and by now they should finish the
> sentence for you:
>
> **"A gate you have never seen block anything is a gate you are trusting on
> faith."**
>
> That sentence has now appeared in Weeks 3, 7 and 8. Point out that it is the
> third time. Repetition across a course is how a slogan becomes a habit.

Then fix it, push, watch it go green, merge. **The whole cycle, in one session:
broken → blocked → fixed → shipped.** That loop is the thing they are actually
taking to work.

### Rehearse the rollback (10 min)

```bash
gcloud run revisions list --service ship-agent --region us-central1
gcloud run services update-traffic ship-agent \
  --region us-central1 --to-revisions PICK_AN_OLDER_ONE=100
curl -s $URL/health
```

**Time them.** Actually time them — phone stopwatch, call it out.

> **INSTRUCTOR** · *"That is how long an outage lasts if you have practised.
> Twice that, at least, if you have not — and that is being generous, because
> the version you have not practised happens at 3am while somebody senior is
> asking you for updates every ninety seconds."*
>
> Then the professional point: **rollback is a rehearsed procedure, not a
> clever idea you have during an incident.** Ask how many of them have ever seen
> a rollback rehearsed at work. Usually nobody.

---

## Beat 5 · Port, and finish (25 min)

### What was portable all along (10 min)

Have them run this themselves — the result is better discovered than told:

```bash
grep -rn "gcloud\|GOOGLE_" app/ evals/ loadtest/ | wc -l
```

**Zero.**

Eight weeks of building on Google Cloud, and not one line of the application
knows it.

Ask: *"Why?"* Three decisions — and the important part is that **they made all
three**, weeks ago, without being told this was the reason:

1. **It is a container.** One image, `$PORT`, runs anywhere. *(Week 1)*
2. **Every setting comes from the environment**, with a working default. No
   `if PRODUCTION:` anywhere in the codebase. *(Weeks 1–7)*
3. **Telemetry is OpenTelemetry.** The destination is a setting. *(Week 5)*

What *is* Cloud Run–specific lives entirely outside the app: the deploy command,
the secret wiring, the traffic splitting.

> **INSTRUCTOR** · **"Your pipeline is vendor-specific. Your agent is not."**
>
> And the honest addendum, because "avoid lock-in" is usually sold as a
> sacrifice: *"None of those three decisions cost you anything. You did not
> design for portability. You just never hardcoded things — and portability fell
> out."*

Prove it. The same image, nothing but settings:

```bash
docker build -t ship-agent .
docker run --rm -p 7000:7000 -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" ship-agent
curl localhost:7000/health
```

Two things that bite on any move, worth naming so nobody thinks it is free:

- **Redis.** One setting, but somebody has to run it.
- **Streaming.** A buffering proxy breaks it *invisibly* — the answer is still
  correct, just all at once. Week 1's `X-Accel-Buffering: no` was aimed at
  exactly this, and every platform has its own version of the problem.

### Kubernetes, as information (10 min)

> **INSTRUCTOR** · Read and discuss. **Nothing to build.** State that up front so
> nobody opens an editor.
>
> The goal is narrow and worth saying out loud: *"When someone at work says
> 'we'll run it on EKS behind an HPA with a sidecar collector', you should know
> exactly which thing you already built they are talking about."*

It is a translation table, not new material:

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

Why an agent cares more than a normal service: **their container can be
perfectly alive and completely unable to serve**, because the *model provider*
is down. That state barely exists for a normal web app and is routine for an
agent.

> **INSTRUCTOR** · *"A liveness probe that fails when the provider is down
> restarts every single box, in a loop, during someone else's outage. You turn a
> degraded service into no service at all — and your restart storm is now part
> of the incident. Readiness sheds traffic instead."*
>
> And the callback: **neither probe should ever point at `/metrics`.** A raised
> error rate would pull the whole fleet out of service. **`/health` is for
> machines. `/metrics` is for humans.** They heard that in Week 5 — this is the
> same rule with a different vendor's words on it.

Close with the honest part, both directions.

**Three reasons to wait:**

- you now operate the platform too
- no scale-to-zero out of the box
- autoscaling an agent is not CPU-shaped — it sits idle waiting on a model, so
  the default CPU-based scaling reads it as unloaded

**Four where it is right:**

- your company already runs it
- you need private networking
- compliance requires it
- you have enough services that per-service config is the bottleneck

> **INSTRUCTOR** · *"Not because it is more advanced. 'We put the container
> somewhere that runs containers' is the actual skill, and you already have
> it."*

### Finish (5 min)

```bash
make check-all
```

Every week, one command, all green. Let it run on the projector and do not talk
over it.

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

> **INSTRUCTOR** · Finish on this, and then genuinely stop:
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

---

## If you finish early

- Have them write one judge case for a regression they personally worry about,
  and defend the rubric wording. Rubric-writing is the actual skill.
- Sabotage the fake model so it returns `492` directly, then break the
  calculator, and watch the gate stay green. Two minutes, and it makes "fake the
  model, never fake your own code" unforgettable.
- Ask what `make check-all` does *not* check. The honest answers are in
  `guide/09-finish.md`.
- Have them roll back, then roll *forward* again. The second one is the
  scarier direction and nobody practises it.

## Homework — the last one

- `make check-all` green
- The **red pull request**, and the green one that followed it
- A rehearsed rollback, with the time it took
- One page: **the three things you would fix first** if this were going live for
  real customers on Monday

> **INSTRUCTOR** · That last question is the best exit assessment in the course,
> and it is worth reading every submission.
>
> `guide/09-finish.md` lists the honest gaps — true streaming, summarising
> memory, an egress proxy, metrics in the log platform, a real eval set. **Anyone
> naming two of those unprompted has understood the phase**, whatever their code
> looks like.
>
> And the failure mode to watch for: a student who says "nothing, it's done".
> Eight weeks of being shown that every safety net has a hole should have cured
> that. If it did not, that is the conversation to have with them before they
> leave.
