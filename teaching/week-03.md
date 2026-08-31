# Week 3 · Automate and lock

**Session goal:** `git push` deploys it, tested. Strangers get turned away.

**Branch:** `week-03-automate` → answer key `week-03-solution`

---

## Beat 1 · Ask (10 min)

### "Walk me through exactly how you deployed last week."

Get the actual steps. Write them on the board as they say them:

```
1. opened a terminal
2. typed a gcloud command from memory (or scrollback)
3. waited
4. hoped
```

### "What was NOT part of that?"

Let them find the gaps. You want at least:

- **Nobody ran the tests.** They could have shipped a broken agent.
- **It deployed whatever was in their folder** — not what is on the main branch,
  not what anyone reviewed. Uncommitted experiments included.
- **Only they can do it.** Their teammate cannot, and neither can they from a
  different laptop.
- **The key went through their shell history.**

### "And who can call your agent right now?"

Anyone on earth who knows the URL.

> **INSTRUCTOR** · Then this, which lands harder than any explanation:
>
> *"There are programs that do nothing but scan the internet looking for open AI
> endpoints, because a free one is worth money. Yours is open. The first you
> would hear about it is the bill."*

**Two problems, one session.** They share a theme: *things that worked once, by
hand, do not survive contact with a team or the open internet.*

---

## Beat 2 · Break (10 min)

Two demonstrations, both on the projector.

**One — ship something broken.** Deliberately break the agent (delete a line
from `app/main.py`), then deploy it by hand. It goes out. It is live. Nothing
stopped you.

> *"Nothing between you and your customers noticed. That is not a process, that
> is luck."*

**Two — spend someone else's money.** Take a student's URL, and from *your*
laptop, run a loop:

```bash
for i in $(seq 1 20); do
  curl -s -o /dev/null -X POST $THEIR_URL/chat \
    -H 'Content-Type: application/json' -d '{"message":"hello"}'
done
```

Then ask them to check their model usage.

> **INSTRUCTOR** · Ask permission first, and pick someone who will find it
> funny. Twenty requests costs pennies. The point lands regardless of the
> amount: *"I just spent your money, from my machine, and you could not have
> stopped me."*

---

## Beat 3 · Concept (18 min)

Four ideas.

### What a pipeline is

A pipeline is **a robot that does what you did by hand, every time you push
code, in the same order, without forgetting.**

Ours will:

```
you push code
     │
     ▼
  run tests ──── fail? ──▶ STOP. nothing is deployed.
     │
   pass
     │
     ▼
  deploy
     │
     ▼
  check it actually answers ──── no? ──▶ roll back
```

### The one detail people get wrong

You would think two separate robots — "the test robot" and "the deploy robot" —
would work. **They do not.**

Both start when you push. They **race**. The deploy robot does not wait for the
test robot, so you get a green tick on a broken deploy, and a pipeline that
looks like a safety net while catching nothing.

The fix is one word:

```yaml
jobs:
  test:
    # ... run the tests ...

  deploy:
    needs: test          # <-- this. No tests, no deploy.
```

**`needs:` only works between jobs inside one file.** That is why the tests live
in the deploy file rather than their own.

> **INSTRUCTOR** · This is genuinely the most common CI mistake in the industry,
> and it is invisible — everything is green, and nothing is protected. Draw the
> race on the board.

### Why 401 and not 403

Two ways to refuse someone:

- **401** — *"I do not know who you are."*
- **403** — *"I know who you are, and you are not allowed."*

A missing or wrong key is **401**. They have not proven who they are.

And say nothing about *why* it failed. "Key not found", "key expired", "key
malformed" — all useful to someone guessing. One answer for all of them.

### Why the rate limit must slide

The obvious way to build "20 per minute" is a counter that resets each minute.

Watch what that allows:

```
11:59:59   ████████████████████   20 requests. Fine.
12:00:00   ████████████████████   20 requests. Also "fine".
           └─ 40 requests in one second ─┘
```

Instead, keep the **times** of recent requests, throw away anything older than
sixty seconds, and count what is left. That counts what actually happened.

> **INSTRUCTOR** · *"Why does an agent need this more than a normal website?"*
>
> Because one request here costs real money at a provider, and may run several
> model calls. A loop in someone's script is not just load — it is a bill.

---

## Beat 4 · Build (45 min)

### Part 1 · The lock (20 min)

They create `app/guardrails.py`. **Every rule this service ever enforces will
live in this one file** — that is deliberate. It is the answer to *"what is this
service's policy?"*, and that answer should be readable in one place rather than
scattered through the code.

Two rules this week: `check_api_key` and `check_rate_limit`.

Three things to say while they work:

**Read the keys fresh, every single call.** Not once when the program starts. If
you cache them, the only way to revoke a leaked key is to ship new code — at
exactly the moment you need it revoked *now*. Read them fresh and revoking is a
setting change and a restart.

**No keys configured means auth is off.** Convenient locally. **Genuinely
dangerous in production** — a service deployed without that setting is wide
open. Worth knowing which situation you are in.

**Both doors, not one.** `/chat` *and* `/chat/stream`.

> **INSTRUCTOR** · *"The day you add a rule to one endpoint and forget the other
> is the day you have an unauthenticated path into a paid model."*

And one ordering detail that matters:

**On the streaming door, check before the response starts.** Once the first
piece goes out, you have already said "200, here it comes" — there is no status
code left to refuse with. Their 401 would arrive as a *success* with an error
message inside it.

Test it locally:

```bash
export API_KEYS=local-dev-key
make run
```

```bash
# no key
curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost:8080/chat \
  -H 'Content-Type: application/json' -d '{"message":"hi"}'
# 401

# with the key
curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost:8080/chat \
  -H 'Content-Type: application/json' -H 'x-api-key: local-dev-key' \
  -d '{"message":"hi"}'
# 200

# hammer it
for i in $(seq 1 25); do
  curl -s -o /dev/null -w "%{http_code} " -X POST localhost:8080/chat \
    -H 'Content-Type: application/json' -H 'x-api-key: local-dev-key' \
    -d '{"message":"hi"}'
done; echo
# 200 200 200 ... 429 429 429
```

> **INSTRUCTOR** · `-w "%{http_code}"` tells curl to print just the status code.
> Worth explaining once — they will use it every week from here.

### Part 2 · The pipeline (25 min)

Two files in `.github/workflows/`.

`test.yml` — runs on every pull request.
`deploy.yml` — on every push to main: test, then deploy, then verify.

Three things in `deploy.yml` to read aloud:

**`--revision-suffix "${GITHUB_SHA::7}"`** tags every deployment with the code
version that produced it. Without it you get `ship-agent-00042-xyz` and no way
to know what is inside. *"Roll back to the last good one"* becomes guesswork,
at the worst possible moment.

**`--set-secrets`, never `--set-env-vars`, for the key.** Settings are visible in
the console and to anyone who can inspect the service. Secrets are not.

**A health check after deploying, with a rollback.** `gcloud run deploy` exiting
successfully means *the box was created*. It says nothing about whether the
program inside it can answer a request.

> **INSTRUCTOR** · *"A deploy that exits 0 is not the same as a service that
> answers."* Write it down. It is a sentence that saves careers.

They will need two things in the repo settings: a `GCP_SA_KEY` secret (a service
account credential file), and `api-keys` in Secret Manager alongside `kodekey`.

### Then break it on purpose

**This is the part that matters most.**

Have them push a commit with a deliberately failing test, then watch the deploy
never start.

> **INSTRUCTOR** · Make everyone do this, and do not let anyone skip it.
>
> **A gate you have never seen block anything is a gate you are trusting on
> faith.**
>
> That sentence is the whole philosophy of the back half of this course. It comes
> back in Week 7 (a load test that exposes a broken rate limit) and Week 8 (a
> red pull request as the deliverable).

Then mention **branch protection**, which lives in repo settings rather than in
any file: make the test job a *required status check* and require pull requests
into main. That is the layer that actually stops bad code arriving. **A pipeline
that only reports is a pipeline people learn to ignore.**

---

## Beat 5 · Prove (15 min)

```bash
make check-week-03
```

It inspects their workflow files too — including whether the deploy job really
declares `needs:`, and whether any secret is being passed as a plain setting.

Then two questions.

### "Your rate limiter counts in a variable, inside one box. How many boxes is Cloud Run running?"

Could be one. Could be five. **So what is their real limit?**

`20 × however many boxes`. Nobody touched a setting to make that happen.

> **INSTRUCTOR** · Now be explicit, because this is a teaching decision they
> should understand:
>
> *"We are leaving that broken. On purpose. For four weeks."*
>
> *"In Week 7 you will run a load test, and it will show you exactly how broken.
> Then you will fix it. If I fixed it quietly today you would learn nothing —
> but after you have watched a rate limit fail under load, you will ask 'where
> does this state live?' about everything, for the rest of your career."*

### "Nothing yet stops one *authorised* caller from making your agent loop fifty times in a single turn."

> Week 4.

## Homework

- `make check-week-03` green
- A screenshot of the deploy being **blocked** by a failing test
- Branch protection turned on
