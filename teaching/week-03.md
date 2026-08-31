# Week 3 · Automate and lock

**Session goal:** `git push` deploys it, tested. Strangers get turned away.

**Branch:** `week-03-automate` → answer key `week-03-solution`

> **INSTRUCTOR** · Two problems in one session, and they can feel unrelated —
> "robots that deploy" and "locks on the door". Say the connecting theme early
> and come back to it: *things that worked once, by hand, do not survive contact
> with a team or the open internet.*
>
> Same method as Weeks 1 and 2: **new tool, toy first.** This week the new
> things are YAML (a file format they have never read) and GitHub Actions (a
> robot they have never watched run). Both get a small deliberate example before
> the real one.
>
> Before the session: this week needs a `GCP_SA_KEY` in repo settings and
> `api-keys` in Secret Manager. Neither is hard, both are fiddly, and doing them
> live for twenty people is slow. Consider sending the steps out beforehand.

---

## Beat 1 · Ask (10 min)

### "Walk me through exactly how you deployed last week."

Get the **actual** steps, not the idealised ones. Write them on the board as
they say them:

```
1. opened a terminal
2. typed a gcloud command from memory (or scrollback)
3. waited
4. hoped
```

> **INSTRUCTOR** · Write step 4 down even though nobody says it. It gets a laugh
> and it is completely accurate — there was no verification step of any kind.

### "What was NOT part of that?"

Let them find the gaps. Take answers until they run dry, then fill in what they
missed. You want at least:

- **Nobody ran the tests.** They could have shipped a broken agent and would not
  have known until a customer told them.
- **It deployed whatever was in their folder** — not what is on the main branch,
  not what anyone reviewed. Uncommitted experiments included. Half-finished
  debugging included.
- **Only they can do it.** Their teammate cannot, and neither can they from a
  different laptop, or on holiday, or at 3am from a phone.
- **The key went through their shell history.**

> **INSTRUCTOR** · That third one is worth pressing on, because students think of
> it as a convenience problem and it is a resilience problem: *"What happens to
> your product when you get flu?"*

### "And who can call your agent right now?"

Anyone on earth who knows the URL.

> **INSTRUCTOR** · Then this, which lands harder than any explanation:
>
> *"There are programs that do nothing but scan the internet looking for open AI
> endpoints, because a free one is worth money. Yours is open. The first you
> would hear about it is the bill."*
>
> Let it sit for a second. Then be fair: *"Your URL is long and random, so
> nobody has found it. That is not security, that is obscurity, and it has a
> half-life."*

**Two problems, one session.** They share a theme, and it is worth naming
plainly: *things that worked once, by hand, do not survive contact with a team
or the open internet.*

---

## Beat 2 · Break (10 min)

Two demonstrations, both on the projector.

### One — ship something broken

Deliberately break the agent — delete a line from `app/main.py` — then deploy it
by hand, exactly the way they deployed last week.

It goes out. It is live. **Nothing stopped you.**

Then hit the URL and show it failing for real. Not a hypothetical: a broken
service, on the internet, that they deployed in front of everyone.

> *"Nothing between you and your customers noticed. That is not a process, that
> is luck."*

> **INSTRUCTOR** · Worth pointing out how *little* effort that took. No override,
> no force flag, no warning to click through. The path to production and the
> path to a broken production are the same path.

### Two — spend someone else's money

Take a student's URL, and from *your* laptop, run a loop:

```bash
for i in $(seq 1 20); do
  curl -s -o /dev/null -X POST $THEIR_URL/chat \
    -H 'Content-Type: application/json' -d '{"message":"hello"}'
done
```

> **INSTRUCTOR** · A beginner has probably never written a loop in a terminal,
> so decode it in one line as you type: *"`for i in $(seq 1 20)` means do the
> thing between `do` and `done`, twenty times."* If you want it to land, run
> this first:
>
> ```bash
> for i in $(seq 1 3); do echo "request $i"; done
> ```
>
> Three lines print. Now the same structure with `curl` in the middle is
> obvious rather than intimidating, and they will use this loop again in twenty
> minutes to trigger their own rate limit.

Then ask them to check their model usage.

> **INSTRUCTOR** · **Ask permission first**, and pick someone who will find it
> funny rather than someone who will be embarrassed. Twenty requests costs
> pennies.
>
> The point lands regardless of the amount: *"I just spent your money, from my
> machine, and you could not have stopped me. Now imagine I wrote 200,000
> instead of 20 — the loop is the same length."*
>
> Then the second-order point, which is the one they will meet at work: *"And I
> am in the room. The person who actually does this is not, and does not stop."*

---

## Beat 3 · Concept (18 min)

Four ideas, and they answer the two problems from Beat 2 in order:

```
   "I shipped something broken"      →  1. what a pipeline is
   "...and nothing stopped me"       →  2. the one detail people get wrong

   "I spent your money"              →  3. how you turn a stranger away
   "...as often as I liked"          →  4. how you slow down someone invited
```

> **INSTRUCTOR** · Say that out loud before starting. Two problems, two ideas
> each. Students who can see the shape stop wondering why a session about robots
> suddenly became a session about locks — and the honest answer is that both are
> *"the thing that worked once, by hand, does not survive other people."*

**A note on the order:** the pipeline comes first because it is the one they
watched fail. The lock comes second because it is the one that costs money. If
you are running short, teach both halves shallowly rather than one deeply — a
student with a gate and no lock is as exposed as one with a lock and no gate.

### What a pipeline is

A pipeline is **a robot that does what you did by hand, every time you push
code, in the same order, without forgetting.**

That is the whole idea. It is not a technology so much as a promise about
consistency.

**Where the robot lives:** GitHub. When they push, GitHub reads a file in their
repo that says what to do, then rents a fresh computer, runs those steps on it,
and throws it away. **A fresh computer every time** is the point — no leftover
state, no "works on my machine", no forgotten step.

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

Walk the diagram twice: once for the happy path, once for each failure branch.
The branches are the product.

### What YAML is (4 min)

They are about to read two files in a format they have probably never seen. Four
minutes now, or twenty minutes of indentation bugs later.

**YAML is a way to write settings as text.** Same job as JSON — data written
down so a program can read it — but shaped for humans to type.

```yaml
name: deploy
on:
  push:
    branches: [main]
```

Three rules cover almost everything:

- **`key: value`** — a fact. Same as JSON's `"key": "value"`, without the quotes
  and commas.
- **Indentation means "belongs to".** `push` is indented under `on`, so it is
  part of `on`. **Spaces only — never tabs.**
- **A `-` starts a list item.**

```yaml
steps:
  - run: make test
  - run: make deploy
```

That is a list of two steps, each with a `run` in it.

> **INSTRUCTOR** · Compare it side by side with the JSON they already know from
> Week 1 — the same data, two spellings:
>
> ```json
> {"steps": [{"run": "make test"}, {"run": "make deploy"}]}
> ```
>
> *"Same facts. YAML uses position on the page where JSON uses brackets."*
>
> Then the warning that saves an afternoon: **indentation is not decoration in
> YAML, it is the syntax.** A line indented one space too far belongs to a
> different thing, and the error message will point somewhere unhelpful.

Have them open a real one and read it before writing any:

```bash
cat .github/workflows/deploy.yml
```

Do not explain every line. Ask them to find three things: **what triggers it**
(`on: push`), **what jobs it has** (`gate` and `deploy`), and **the one line
that connects them**. That third one is the next section.

### The one detail people get wrong

You would think two separate robots — "the test robot" and "the deploy robot" —
would work. **They do not.**

Both start when you push. They **race**.

```
      you push
          │
   ┌──────┴──────┐
   ▼             ▼
  gate        deploy          <- starts immediately, does not wait
   │             │
   │  (4 min)    │  (2 min)
   ▼             ▼
  FAIL         SHIPPED        <- your broken code is already live
```

The deploy robot does not wait for the test robot, so you get a **green tick on
a broken deploy**, and a pipeline that looks like a safety net while catching
nothing.

The fix is one word, and it is in the file they just read:

```yaml
jobs:
  gate:
    # ... run the tests ...

  deploy:
    needs: gate          # <-- the arrow. No gate, no deploy.
```

**`needs:` only works between jobs inside one file.** That is why the tests live
in the deploy workflow rather than in their own — a constraint that looks
arbitrary until you know what it prevents.

> **INSTRUCTOR** · This is genuinely one of the most common CI mistakes in the
> industry, and what makes it dangerous is that **it is invisible**. Everything
> is green. Every badge says passing. Nothing is protected.
>
> Draw the race on the board. Then ask: *"How would you ever notice?"* You would
> not, until the day a failing test does not stop a bad deploy — which is
> precisely the day you were counting on it.

### What an API key is, and why 401 not 403

**An API key is a password for a program.** A long random string the caller
sends with every request, that says "I am allowed to be here". No username, no
login screen — one secret, attached to each call.

Where it goes: in a **header**, which they met in Week 1 with
`Content-Type`. Ours is `x-api-key`.

```bash
curl -s -i https://api.github.com/zen        # headers, from Week 1
```

*"Same mechanism. We are just adding one of our own, and refusing anyone who
does not send it."*

Two ways to refuse someone, and the difference is not pedantry:

- **401** — *"I do not know who you are."*
- **403** — *"I know who you are, and you are not allowed."*

A missing or wrong key is **401**. They have not proven who they are, so there
is nothing to be *not allowed* about.

And say nothing about *why* it failed. "Key not found", "key expired", "key
malformed" — all useful to someone guessing. **One answer for all of them.**

> **INSTRUCTOR** · The principle generalises: *"Every distinct error message you
> return is a bit of information you hand to someone probing you."* Connect it
> to Week 1's rule about never returning raw errors — same instinct, different
> application.

### Why the rate limit must slide

**A rate limit is a cap on how often one caller may ask.** "Twenty per minute,
then I start refusing you."

The obvious way to build it is a counter that resets each minute.

Watch what that allows:

```
11:59:59   ████████████████████   20 requests. Fine.
12:00:00   ████████████████████   20 requests. Also "fine".
           └─ 40 requests in one second ─┘
```

**Double your limit, instantly, with no rule broken.** This is called a *fixed
window*, and the bug is that the window's edges are arbitrary and the attacker
knows where they are.

Instead, keep the **times** of recent requests, throw away anything older than
sixty seconds, and count what is left. That is a *sliding window*, and it counts
what actually happened rather than what happened since an arbitrary reset.

> **INSTRUCTOR** · *"Why does an agent need this more than a normal website?"*
>
> Because one request here costs real money at a provider, and may run several
> model calls. A loop in someone's script is not just load — it is a bill. A
> normal website serving 40 requests in a second has a busy second; yours has an
> expensive one.
>
> Flag forward, because this exact bug returns: *"Remember the shape of the
> fixed-window mistake. You will meet it again in Week 7, in Redis, and it will
> look completely different."*

---

## Beat 4 · Build (45 min)

### Part 1 · The lock (20 min)

They create `app/guardrails.py`.

**Every rule this service ever enforces will live in this one file** — that is
deliberate, and worth explaining rather than just asserting. It is the answer to
*"what is this service's policy?"*, and that answer should be readable in one
place in two minutes rather than scattered across the code.

> **INSTRUCTOR** · Tell them what is coming, so the file's purpose is obvious
> from the start: *"Week 4 adds budgets here. Week 7 adds input limits, an
> injection filter and a URL allowlist. By the end this file is the whole
> security posture of the service, and a new engineer can read it in one
> sitting."*

Two rules this week: `check_api_key` and `check_rate_limit`.

Three things to say while they work:

**Read the keys fresh, every single call.**

```python
def _valid_keys():
    return {k.strip() for k in os.environ.get("API_KEYS", "").split(",") if k.strip()}
```

Not once when the program starts. If you cache them, the only way to revoke a
leaked key is to ship new code — at exactly the moment you need it revoked
*now*. Read them fresh and revoking is a setting change and a restart.

> **INSTRUCTOR** · *"Design for the bad day. On the good day it makes no
> difference; on the bad day it is the difference between two minutes and two
> hours."*

**No keys configured means auth is off.**

```python
if not valid:
    return          # no keys configured -> auth off (local dev)
```

Convenient locally. **Genuinely dangerous in production** — a service deployed
without that setting is wide open, and nothing complains.

Ask the room whether they would have designed it this way. It is a real
trade-off: fail-open is friendly to developers and hostile to operators. Note
that this is the *opposite* default from the redaction rule they meet in Week 5,
and both are defensible. **Knowing which situation you are in is the skill.**

**Both doors, not one.** `/chat` *and* `/chat/stream`.

> **INSTRUCTOR** · *"The day you add a rule to one endpoint and forget the other
> is the day you have an unauthenticated path into a paid model."*
>
> Have them actually test both. Someone will have protected only the one they
> use.

And one ordering detail that matters:

**On the streaming door, check before the response starts.** Once the first
piece goes out, you have already said "200, here it comes" — there is no status
code left to refuse with. Their 401 would arrive as a **success** with an error
message inside it.

Callback to Week 1, where they met this exact constraint with mid-stream errors.
Same protocol fact, second consequence.

### Test it locally

```bash
export API_KEYS=local-dev-key
make run
```

That `export` is the environment variable from Week 1 — they are configuring
their own service from outside its code.

In the second terminal, three tests. **Same `-w "%{http_code}"` flag they
learned in Week 1 against httpbin**, now pointed at their own service:

```bash
# no key
curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost:8080/chat \
  -H 'Content-Type: application/json' -d '{"message":"hi"}'
# 401
```

```bash
# with the key
curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost:8080/chat \
  -H 'Content-Type: application/json' -H 'x-api-key: local-dev-key' \
  -d '{"message":"hi"}'
# 200
```

One extra `-H`. That is the whole authentication mechanism.

```bash
# hammer it — the same loop from Beat 2, now aimed at yourself
for i in $(seq 1 25); do
  curl -s -o /dev/null -w "%{http_code} " -X POST localhost:8080/chat \
    -H 'Content-Type: application/json' -H 'x-api-key: local-dev-key' \
    -d '{"message":"hi"}'
done; echo
# 200 200 200 ... 429 429 429
```

> **INSTRUCTOR** · Watching the row of 200s turn into 429s is the satisfying
> moment of this half. Make sure everyone gets there rather than skipping to the
> checkpoint.
>
> Point out that they have now *been* both parties: you attacked them in Beat 2
> with that exact loop, and now the same loop bounces off. **That is the entire
> lesson of the first half, demonstrated rather than asserted.**

### Part 2 · The pipeline (25 min)

Two files in `.github/workflows/`.

`deploy.yml` — on every push to main: **gate**, then deploy, then verify.
`eval.yml` — the quality gate on pull requests (Week 8 fills this in).

Three things in `deploy.yml` to read aloud:

**`--revision-suffix "${GITHUB_SHA::7}"`** tags every deployment with the code
version that produced it.

> **INSTRUCTOR** · Beginners will not know what a SHA is, so: *"Every git commit
> has a unique fingerprint — a long string of letters and numbers. `::7` takes
> the first seven characters, which is enough to identify it."*
>
> ```bash
> git log --oneline -3
> ```
>
> Those short codes on the left are exactly it. Now the flag makes sense.

Without it you get `ship-agent-00042-xyz` and no way to know what is inside.
*"Roll back to the last good one"* becomes guesswork, at the worst possible
moment.

> **INSTRUCTOR** · Flag it forward hard, because this is the clearest example in
> the course of a cheap decision paying off later: *"This is ninety seconds of
> work today. In Week 8 it is the difference between a thirty-second rollback
> and a panicked hunt through a deploy log."*

**`--set-secrets`, never `--set-env-vars`, for the key.** Settings are visible in
the console and to anyone who can inspect the service. Secrets are not. Same
rule as Week 2, now enforced in the pipeline rather than remembered by a human.

**A health check after deploying, with a rollback.**

`gcloud run deploy` exiting successfully means *the box was created*. It says
nothing whatsoever about whether the program inside it can answer a request.

> **INSTRUCTOR** · *"A deploy that exits 0 is not the same as a service that
> answers."* Write it down. It is a sentence that saves careers, and it applies
> to every deployment tool anyone has ever built.
>
> **What "exits 0" means**, since it will not be obvious: *"Every command
> finishes with a number. Zero means it worked; anything else means it failed.
> That is how one step in a pipeline knows whether the last one succeeded."*
>
> ```bash
> ls; echo $?          # 0
> ls /nope; echo $?    # not 0
> ```

They will need two things in the repo settings: a `GCP_SA_KEY` secret (a service
account credential file — **a login for a robot rather than a person**), and
`api-keys` in Secret Manager alongside `kodekey`.

### Then break it on purpose

**This is the part that matters most in the whole session.**

Have them push a commit with a deliberately failing test, then **watch the
robot** on GitHub — Actions tab, click the run, watch `gate` go red and `deploy`
never start at all.

> **INSTRUCTOR** · Make them actually watch it in the browser, live. The greyed
> out `deploy` job that never ran is the whole point made visual — it is not
> that the deploy failed, it is that **it never happened**.
>
> **Make everyone do this, and do not let anyone skip it** — not the fast
> students, not the ones who "already understand it".
>
> **A gate you have never seen block anything is a gate you are trusting on
> faith.**
>
> That sentence is the whole philosophy of the back half of this course. It
> comes back in Week 7 (a load test that exposes a broken rate limit) and Week 8
> (a red pull request as the deliverable). By the third time, they should be
> finishing it for you.

Then mention **branch protection**, which lives in repo settings rather than in
any file: make the gate job a *required status check*, and require pull requests
into main.

That is the layer that actually stops bad code arriving. **A pipeline that only
reports is a pipeline people learn to ignore.**

> **INSTRUCTOR** · Worth being explicit about the distinction: the workflow file
> *runs* the tests; branch protection is what makes the result *matter*. Teams
> routinely build the first and skip the second, then wonder why red builds get
> merged.

---

## Beat 5 · Prove (15 min)

```bash
make check-week-03
```

It inspects their workflow files too — including whether the deploy job really
declares `needs:`, and whether any secret is being passed as a plain setting.

> **INSTRUCTOR** · Point that out. *"The checkpoint is reading your YAML. A
> configuration mistake is as shippable as a code mistake, so it gets checked
> the same way."*

Then two questions.

### "Your rate limiter counts in a variable, inside one box. How many boxes is Cloud Run running?"

Could be one. Could be five. They have no way to know, and it changes with
traffic.

**So what is their real limit?**

`20 × however many boxes`. Nobody touched a setting to make that happen.

> **INSTRUCTOR** · Now be explicit, because this is a **teaching decision they
> should understand rather than a gap you are hiding**:
>
> *"We are leaving that broken. On purpose. For four weeks."*
>
> *"In Week 7 you will run a load test, and it will show you exactly how broken.
> Then you will fix it. If I fixed it quietly today you would learn nothing —
> but after you have watched a rate limit fail under load, you will ask 'where
> does this state live?' about everything, for the rest of your career."*
>
> Saying this out loud matters. A student who spots the flaw and thinks you
> missed it learns to distrust the material; a student who knows it is deliberate
> learns to look for the same flaw everywhere.

### "Nothing yet stops one *authorised* caller from making your agent loop fifty times in a single turn."

They have locked the door. They have not bounded what an invited guest can do.

> Week 4.

---

## If you finish early

- Have them try the rate limit from **two different terminals** with the same
  key, then with two different keys. Ask what the limiter is actually counting.
- Have them revoke a key: change `API_KEYS` on the service, restart, and watch
  the old key stop working — without a deploy. That is the "read fresh" decision
  paying off in real time.
- Have them deliberately break the YAML — indent one line by a single extra
  space — push, and read GitHub's error. Learning to recognise that error costs
  two minutes now and saves an hour later.
- Have them push a commit that fails on a **pull request** rather than main, and
  see the difference between a blocked merge and a blocked deploy.
- Ask: *"What could still reach production without passing the gate?"* Good
  answers: a direct `gcloud run deploy` from a laptop, and anyone with console
  access. Both are real, and both are why branch protection is necessary but not
  sufficient.

## Homework

- `make check-week-03` green, committed and pushed
- A screenshot of the deploy being **blocked** by a failing gate
- Branch protection turned on

> **INSTRUCTOR** · Insist on the blocked-deploy screenshot specifically, not a
> green run. Anyone can produce a green pipeline; the artefact that proves they
> built a *gate* is the one where it said no.
