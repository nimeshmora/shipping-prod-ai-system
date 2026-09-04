# Week 2 · Deploy

**Session goal:** they leave with a real URL on the internet, and memory that
survives a restart.

**Branch:** `week-02-deploy` → answer key `week-02-solution`

> **INSTRUCTOR** · This is the week with the best moment in the whole course.
> **Do not rush to the fix.** Deploy, break it, sit in the silence, *then* fix
> it. An instructor who explains the problem before demonstrating it has traded
> the most memorable ten minutes of the phase for ten minutes of nodding.
>
> Same method as Week 1: **every new tool gets a toy first.** This week that
> means Redis — they will run `SET` and `GET` by hand, in a database with
> nothing else in it, before any of it touches the agent.
>
> Before the session: check that everyone has a Google Cloud account with
> **billing enabled**. Not billing *charged* — billing *enabled*. It is the
> single most common blocker and it cannot be fixed in the room.

---

## Beat 1 · Ask (10 min)

### "What did we build last week, in one sentence?"

You want: *an agent with an address, that streams, in a box that runs anywhere.*

> **INSTRUCTOR** · Make them compress it to one sentence rather than accepting a
> list. Compression is where you find out whether they have a model of it or a
> memory of it.

### "So is it online?"

No. It runs on their laptop.

The box **can** run anywhere — it just isn't anywhere yet. That distinction is
worth a moment: last week they solved *portability*, which is a different
problem from *availability*, and it is easy to feel like you have done both.

### "Where does the conversation history live?"

This is the important one. Push until someone says **"in the program"** or
**"in memory"** or points at the dictionary in `app/memory.py`.

Open `app/memory.py` on the projector. Strip it back to what mattered last week
— it is eleven lines:

```python
_STORE = {}

def load(session_id):
    return _STORE.get(session_id, [])

def save(session_id, history):
    _STORE[session_id] = history
```

Ask: *"How long does a Python variable live?"*

> As long as the program does.

Connect it back to Week 1's `sleep 30`: **a variable lives inside a process, and
they have already killed a process with Ctrl+C and watched it vanish.** This is
the same fact, about their agent's memory.

*"Hold that thought."*

> **INSTRUCTOR** · Do not let anyone jump ahead. Someone in a technical room
> will already know where this is going and will want to say "so you need a
> database". Cut them off gently: *"Say that again in twenty minutes and I'll
> agree with you. I want everyone to watch it happen first."*

---

## Beat 2 · Break (25 min — the centrepiece)

> **INSTRUCTOR** · This beat is longer than usual because deploying is part of
> it. Do it on the projector; they follow along on their own machines. Expect to
> lose a few minutes to gcloud auth — that is normal, and it is why this beat
> has the budget it does.

### First, get it online

Three concepts, explained **as you go** rather than in advance. This is the
teach-at-the-moment-of-need rule from the introduction, and this beat is the
clearest example of it in the course.

**What "the cloud" actually is.** Somebody else's computer, in a building
somewhere, that you rent by the minute. That is genuinely the whole idea. The
value is not the computer — it is that it is always on, someone else replaces
the broken disks, and you can have another one in thirty seconds.

**What Cloud Run is.** A service that takes your container — the box from Week 1
— and runs it on Google's computers. You hand over the box; they give you back a
URL. You do not manage a server, patch an operating system, or think about
hardware at all.

> **INSTRUCTOR** · If someone asks how it differs from a VM, the one-liner is:
> *"A VM is a computer you rent and look after. This is a box you hand over."*
> Do not go further — the comparison is a rabbit hole and nothing today depends
> on it.

**What the `gcloud` command is.** Same idea as `git` or `curl`: a program you
run in the terminal that talks to Google's systems on your behalf. Everything
they will do in a web console has a `gcloud` equivalent, and the command is the
one you can put in a pipeline later.

First, prove it can see their account:

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud config list
```

That last one prints what it is currently pointed at. **Have everyone run it and
read their own output** — half of all Week 2 problems are "deployed to the wrong
project", and this is the thirty seconds that prevents them.

**What a secret manager is.** Their API key must not be in their code, and must
not be in a plain setting either — settings are visible to anyone who can look at
the project. A secret manager is a locked drawer the platform opens for your
service and nobody else.

```bash
echo -n "$OPENROUTER_API_KEY" | gcloud secrets create kodekey --data-file=-
```

Read that command out. The `-n` matters: without it you store a trailing
newline, and a key with an invisible newline on the end produces a 401 that
takes an hour to diagnose.

Show them, so it is not folklore:

```bash
echo "abc"  | wc -c      # 4  <- the newline is really there
echo -n "abc" | wc -c    # 3
```

> **INSTRUCTOR** · Worth connecting to last week: *"You already made this
> decision once. `.env` in `.dockerignore` was the same rule — never put a secret
> in the box. This is where the key goes instead."*

**What deploying actually does.** Reads your `Dockerfile`, builds the box in the
cloud, starts it, and points a URL at it.

```bash
gcloud run deploy ship-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-secrets "OPENROUTER_API_KEY=kodekey:latest" \
  --timeout=3600 --concurrency=80 --min-instances=1
```

> **INSTRUCTOR** · Paste this one, do not type it — a `gcloud` line is not a
> typing exercise. Then read the last three flags aloud, because they are the
> three things people get wrong about hosting an agent specifically:
>
> - **`--timeout=3600`** — an agent turn is slow and spends most of its life
>   *waiting* on a model. The default five minutes will chop a long turn in
>   half, and the customer sees a truncated answer with no error.
> - **`--concurrency=80`** — one box can serve eighty people at once, precisely
>   *because* each request is mostly waiting rather than computing. This is why
>   agents are surprisingly cheap to host, and it surprises people who assume AI
>   means expensive hardware.
> - **`--min-instances=1`** — keeps one box warm. Without it, the first customer
>   of the day waits for a box to start, Python to load, and every library to
>   import. Costs a few dollars a month; buys a first impression.
>
> Also flag `--allow-unauthenticated` in passing and promise to come back to it.
> *"That word should bother you. It will, next week."*

Wait for it. The first deploy takes a few minutes and looks stuck — warn them
before it starts, or you will field the same question fifteen times.

Then:

```bash
URL=$(gcloud run services describe ship-agent --region us-central1 \
        --format='value(status.url)')
echo $URL
curl -s $URL/health
```

> **INSTRUCTOR** · That first line will look like magic to a beginner, so spend
> twenty seconds: **`$( ... )` runs the command inside the brackets and puts its
> output into the variable.** Nothing more.
>
> ```bash
> NOW=$(date)
> echo $NOW
> ```
>
> Two lines, and the syntax stops being mysterious for the rest of the course.

**That URL is on the public internet.**

And note what `curl -s $URL/health` is: **the exact same command from Week 1**,
with a real address instead of `localhost`. Same tool, same flags — the only
thing that changed is which computer answers.

Have them message it to the person next to them and watch someone else's laptop
talk to their agent.

> **INSTRUCTOR** · **Pause here.** This is the first moment in the course where
> something they built is *real* — reachable by a stranger, from anywhere, with
> no laptop of theirs involved.
>
> Let them enjoy it for a full minute. Ask who has ever had something they built
> be reachable from the internet before; in most rooms it is a minority.
>
> The next fifteen minutes are about breaking it, and the contrast is worth
> setting up properly.

### Now break it

Have everyone do this **on their own deployment**. Watching you do it is not the
same — the memory that matters is *their* conversation being lost.

**Step 1.** Start a conversation, keep the `session_id`:

```bash
curl -s -X POST $URL/chat -H 'Content-Type: application/json' \
  -d '{"message":"where is my order ORD-1002?"}'
```

**Step 2.** Continue it. Confirm it remembers:

```bash
curl -s -X POST $URL/chat -H 'Content-Type: application/json' \
  -d '{"message":"and when will it arrive?","session_id":"PASTE_IT"}'
```

It does. Everything is working perfectly.

**Step 3.** Deploy again. **Change nothing at all:**

```bash
gcloud run deploy ship-agent --source . --region us-central1
```

**Step 4.** Continue the same conversation one more time.

**It has forgotten everything.**

> **INSTRUCTOR** · **Say nothing for a moment.** Let them read their own
> terminal. Then ask: *"What failed?"*
>
> The answer is **nothing failed**. There is no error. No crash. No alert. The
> deployment **succeeded** — that is what caused it. Cloud Run replaced the box,
> and the dictionary inside it went with the old one.
>
> Then say this, slowly, and it is worth writing on the board:
>
> **"Your health check is green. Your logs are clean. Your error rate is zero.
> And every customer mid-conversation was silently reset."**
>
> *"That is the shape of most real AI incidents. Nothing breaks. The product just
> quietly stops working."*
>
> If you want the sharpest version: *"Which of your monitoring would have told
> you? You do not have any monitoring. That is Week 5, and this is the first
> time you will wish you did."*

Write on the board, because deploys are only the most obvious trigger:

```
It also happens when:
  - traffic goes quiet and the platform shuts your box down to save money
  - traffic grows and the platform starts a SECOND box
    (then it depends which one answers you)
```

That second one is worth a beat. **It is not even consistent** — the same
customer gets their history on one request and not the next, depending on
routing. Intermittent bugs that depend on which machine answered are among the
hardest things to diagnose, and they have just created one.

---

## Beat 3 · Concept (10 min)

### The everyday version

Before the rule, the picture. This one lands in about fifteen seconds.

**A shop where the only record of your order is in one assistant's head.**

```
   works fine        you come back, the same assistant is there,
                     they remember you

   breaks            that assistant goes home        → nobody knows your order
                     the shop hires a second one     → they each remember
                                                       different customers
```

Nothing has "gone wrong" in either case. Someone finished their shift; the shop
got busier and hired help. **Both are completely normal events, and both lose
your order.**

The fix is not a better assistant. It is **writing orders in a book that stays
in the shop.**

> **INSTRUCTOR** · Ask which of the two failures is worse. Most say the first;
> the second is worse, because it is *intermittent* — you get your order half
> the time, depending on who serves you. That is exactly the second bullet you
> wrote on the board a minute ago, and it is the one that takes a week to
> diagnose in real life.

### The rule

**Anything a request needs to remember has to live outside the process that
serves it.**

That sentence is most of what people mean by "stateless service", and it is
worth writing down verbatim.

> **INSTRUCTOR** · Note what it does *not* say. It does not say "your service
> cannot have state" — that would be absurd. It says state cannot live *inside
> the process*. The service is stateless; the *system* very much is not.
> Students who hear "stateless" as "no memory" get confused for years.

### Why "outside"

A variable lives inside one program, on one machine. Restart the program: gone.
Run two copies: they each have their own, and disagree.

So the history moves to a **separate program whose entire job is remembering
things** — a database.

**What a database is**, in one sentence, because not everyone has used one: a
program that holds data for other programs, and keeps holding it after they stop
running.

Ours is **Redis**, which is a database optimised for exactly our shape: small
pieces of data, fetched by a key, very fast. It is essentially a dictionary —
the same `{key: value}` idea from `app/memory.py` — that lives in its own
process, so other programs can share it and it outlives all of them.

```
BEFORE                          AFTER
┌──────────────┐                ┌──────────────┐   ┌───────┐
│ your agent   │                │ your agent   │──▶│ Redis │
│  ┌────────┐  │                └──────────────┘   └───────┘
│  │ memory │  │                ┌──────────────┐       ▲
│  └────────┘  │                │ your agent   │───────┘
└──────────────┘                └──────────────┘
 dies with the box               both see the same memory,
                                 and it outlives both
```

Draw the "after" side with two boxes deliberately. The single-box version hides
the second half of the benefit.

### The part that is actually being taught

Look at what changes in the codebase. **Two functions keep their names**:

```python
load(session_id)
save(session_id, history)
```

`app/main.py` calls those, and **does not get edited**. Neither does anything
else. The entire storage layer is replaced and exactly one file changes.

> **INSTRUCTOR** · This is the transferable skill of the week, and it is worth
> naming explicitly and slowly:
>
> **Week 1 put a seam there on purpose. This week is the payoff.**
>
> *"Designing the seam before you need it is most of what makes a change cheap
> later."*
>
> They will do this for the rest of their careers, or they will not, and the
> difference shows up in how much their teams dread changes.
>
> Flag it forward too: the same pattern appears in Week 5 (telemetry:
> instrument once, destination is a setting) and Week 7 (`app/store.py`, same
> shape as this file). By Week 8 they should recognise it on sight.

---

## Beat 4 · Build (35 min)

### Part 0 · Redis by hand, on nothing (7 min)

> **INSTRUCTOR** · Do not skip this to save time. Students who have typed `SET`
> and `GET` themselves understand `app/memory.py` in one read. Students who have
> not are learning Redis, the Python client, and our serialisation problem all
> at once — and when it fails they cannot tell which one broke.

Start a Redis with nothing in it. They have Docker from Week 1:

```bash
docker run -d --name toy-redis -p 6379:6379 redis
```

- `-d` — run in the background (so they get their prompt back)
- `--name toy-redis` — a name, so they can stop it later
- `-p 6379:6379` — connect door 6379 on their computer to door 6379 in the box.
  **Ports, from Week 1.**

Now talk to it:

```bash
docker exec -it toy-redis redis-cli
```

`docker exec` runs a command *inside* a box that is already running. `redis-cli`
is Redis's own terminal. The prompt changes to `127.0.0.1:6379>`.

Type these one at a time:

```
SET greeting "hello"
GET greeting
```

```
OK
"hello"
```

**They just stored something in a database and read it back.** Two commands.

```
SET greeting "hello again"
GET greeting
```

Same key, new value — it replaced it. **A key holds one value.**

```
GET nothing-here
```

```
(nil)
```

**`nil` means "no such key".** That is what `load()` gets for a brand new
session, and it is why the code says `return json.loads(raw) if raw else []`.

Now the expiry, which is the one Redis feature the code depends on:

```
SETEX temporary 10 "I will not last"
GET temporary
```

Wait ten seconds. Ask again:

```
GET temporary
```

```
(nil)
```

**It deleted itself.** `SETEX` = SET with an EXpiry, in seconds. That is exactly
how old conversations get cleaned up without anyone writing a cleanup job.

Two more worth seeing:

```
KEYS *
```

Everything in the database. **This is why namespacing matters** — right now it
is their two toy keys; in production it is every session plus whatever else
anyone put in there.

```
TTL temporary
```

How many seconds a key has left. `-1` means "no expiry set" — which is the bug
they are about to be warned about.

Type `exit` to leave, and leave the container running:

```bash
docker stop toy-redis && docker rm toy-redis    # later, when done
```

> **INSTRUCTOR** · Land the connection explicitly before moving on:
>
> *"That is the entire database. A key, a value, and an expiry. `app/memory.py`
> does exactly what you just did by hand — `SETEX` to save, `GET` to load. The
> only thing the Python adds is turning a conversation into text first."*

### Part 1 · Point the agent at a real Redis

```bash
gcloud run services update ship-agent --region us-central1 \
  --set-env-vars "REDIS_URL=redis://YOUR_HOST:6379"
```

**That setting is an environment variable** — the same idea as `OPENROUTER_API_KEY` in
Week 1. Note it is `--set-env-vars`, not `--set-secrets`: a Redis address is not
a secret in the way an API key is. *"Which of your settings are secrets?"* is a
question worth asking the room.

> **INSTRUCTOR** · Memorystore on Google Cloud, or Upstash's free tier — either
> is fine, and **Upstash is much faster to set up** if the room is impatient or
> the clock is tight.
>
> **Have a working `REDIS_URL` ready as a fallback** for anyone who gets stuck
> in a console. Provisioning is not the lesson; do not let it eat the build.

### Part 2 · Edit one file (20 min)

Then `app/memory.py`. The header comment tells them what to build. Four details
to say out loud while you walk the room — **each maps to something they just
typed in `redis-cli`**:

**`SETEX`, not `SET`.** They used both, five minutes ago. Writes the value *and*
its expiry in one instruction. Do them separately and a crash between the two
leaves a conversation with `TTL -1` — the "no expiry" they saw — living forever.
Redis will happily store your data until the end of time and bill you for it.

> **INSTRUCTOR** · The general shape is worth a sentence: *"Any time you write
> two things that must both happen, ask what happens if the process dies between
> them."* It comes back in Week 7's rate limiter, which sets its expiry in the
> same pipeline for the same reason.

**Namespace the keys** — `session:abc123`, not `abc123`. They ran `KEYS *` and
saw one flat list. Redis is one big shared space, someone will eventually store
something else in there, and future-you needs to tell what is what. It is also
what makes `reset()` possible: `scan_iter("session:*")` can only exist because
the prefix does.

**Connect once, lazily.**

```python
def _redis():
    global _client
    if _client is None and REDIS_URL:
        import redis
        _client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    return _client
```

**Once**, because building a connection for every request is how you run out of
them. **Lazily**, because importing this file must not require a running Redis —
otherwise the tests and their laptops stop working, and a test suite that needs
infrastructure is a test suite people skip.

**Keep the dictionary.** When `REDIS_URL` is not set, fall back to it. The
course has to run on a train with no internet, and more importantly this is the
pattern: one interface, two implementations, chosen by a setting.

### The bug they will hit

Saving a conversation that contains a tool call will fail with:

```
TypeError: Object of type SimpleNamespace is not JSON serializable
```

**Let them hit it.** Do not warn them first.

Then explain, and connect it to Week 1's JSON toy: **JSON is text.** Redis
stores text. A conversation in Python is a list of *objects* — living things in
memory with methods attached. Text and objects are different, and something has
to convert one to the other.

```bash
# from Week 1 — this worked, because it was already plain data
echo '{"name":"Ada"}' | python -m json.tool
```

`json.dumps` knows what to do with dictionaries, lists, strings and numbers. It
does not know what to do with an object it has never seen. So they have to
convert first:

```python
def _block_to_dict(block):
    if isinstance(block, dict):          # a tool_result we built ourselves
        return block
    dump = getattr(block, "model_dump", None)
    if callable(dump):                   # a real block from the SDK
        return dump()
    return dict(vars(block))             # a fake block from the tests
```

> **INSTRUCTOR** · This one is worth dwelling on, because the *shape* of it
> recurs forever:
>
> The content blocks arrive in **three** different shapes — plain dictionaries
> from our own code, real objects from the model provider, and fake objects from
> the tests. Handle only the provider's shape and **every test passes while
> production breaks.** Handle only the test's shape and the reverse.
>
> *"Your tests use one shape. Production uses another. That is not a Python
> problem, that is a testing problem, and it will bite you in every language you
> ever write."*
>
> Flag it forward: this is the same idea as Week 8's *"fake the model, never fake
> your own code"*. Every mock is a claim about what does not need testing.

### Then prove the fix

Redeploy. Start a conversation. **Redeploy again.** Continue it.

**It remembers.**

Have them do the full four steps from Beat 2 again, in the same order. The
symmetry is the point — same actions, different outcome.

And if they still have a local Redis running, they can watch it happen:

```
KEYS session:*
```

**Their conversation, sitting in a database, with their own session id on it.**

```bash
make check-week-02
```

---

## Beat 5 · Prove (10 min)

Green checkpoint, then three questions.

### "How did you deploy today?"

By hand. From a laptop. With a command they half-remembered. Nobody reviewed it.
No tests ran.

*"How many ways can that go wrong?"* Take answers — they will find most of them.

> Week 3.

### "Your URL says `--allow-unauthenticated`. What does that mean?"

Anyone can call it. Anyone at all, anywhere, with no key.

And every call costs real money at the model provider, on their card.

> Also Week 3.

### "Redis is now a thing your agent depends on. What does `/health` say if Redis is down but your agent is running fine?"

Still `ok`. And now that is arguably a lie — the process is healthy and the
product does not work.

> **INSTRUCTOR** · Do not resolve this one. It is a **genuinely hard question**
> with no single right answer, and telling them so is more useful than picking a
> side.
>
> The two positions, briefly: include the dependency and one Redis blip restarts
> your whole fleet; exclude it and your health check reports green during an
> outage. Week 5 gives them the vocabulary (`/health` vs `/metrics`) and Week 8
> gives them the Kubernetes version (liveness vs readiness). *"Notice you now
> have a question you cannot answer. Keep it."*

---

## If you finish early

- Back in `redis-cli`: `SET a 1`, then `DEL a`, then `GET a`. Deleting is a
  thing too, and it is what a "log out" button does.
- Have them run `gcloud run revisions list` and look at what a deploy actually
  created. It is the first sight of the thing they will roll back to in Week 8.
- Set `SESSION_TTL=60`, hold a conversation, wait a minute, and continue it.
  Watch the expiry work — the same `SETEX` behaviour they saw by hand, now on
  their own conversation.
- Have them deploy **without** `--min-instances=1`, wait for it to go cold, and
  time the first request. Then redeploy with it. The number is usually
  persuasive.
- Ask: *"What else in this service still lives inside one box?"* The honest
  answer is *everything you have not built yet* — the rate limiter (Week 3) and
  the metrics window (Week 5), both of which come due in Week 7.

## Homework

- `make check-week-02` green, committed and pushed
- A conversation that **provably** survives a redeploy — have them screenshot
  the before and after
- Leave the service running; Week 3 builds directly on it

> **INSTRUCTOR** · Insist on the screenshot. It is the cheapest possible proof
> and it forces them to actually run the four steps rather than assume the
> checkpoint covered it. It also gives you something to open Week 3 with.
