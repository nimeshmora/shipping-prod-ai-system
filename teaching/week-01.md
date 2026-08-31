# Week 1 · Package

**Session goal:** they leave with an agent that has an address, streams its
answer, and runs inside a container.

**Branch:** `week-01-package` → answer key `week-01-solution`

---

## Beat 1 · Ask (10 min, no slides)

> **INSTRUCTOR** · Laptops closed. Slides off. Just talk. This is the only part
> of the session where nobody types anything, and it sets up everything else.

Three questions to the room, in this order.

### "What is an agent?"

Let them answer. You are listening for **a loop**.

The answer you want to arrive at, in their words if possible:

> An agent is a loop. You send a question to the model along with a list of
> tools it may use. The model either answers, or it asks for a tool. Your code
> runs the tool, hands back the result, and goes round again.

> **INSTRUCTOR** · If you get "it's an AI that does things", push once: *"Does
> the model run the tool, or does your code?"* That distinction is the whole
> lesson of Phase 1 and the foundation of every Phase 2 guardrail. Your code
> runs whatever the model asks for. That is why budgets, traces and fences
> exist.

### "Someone tell me what you built in Phase 1."

Pick a volunteer. Let them talk for two minutes.

> **INSTRUCTOR** · Pick someone who is *not* the most confident person in the
> room. You want a plain description, not a performance. Ask them to draw the
> four moves on the whiteboard if they are willing:
>
> ```
> 1. you        "where is order ORD-1002?"
> 2. model      "call lookup_order with ORD-1002"   <- it asks; it cannot fetch
> 3. your code  "ORD-1002: standing desk, $340..."  <- you fetch, and reply
> 4. model      "Your standing desk arrives Thursday"
> ```
>
> Keep that on the board all session.

### "So — who else can use it?"

This is the trap question. The honest answer is **nobody**.

Their Phase 1 agent works when *they* run it, on *their* laptop, in *their*
terminal, with *their* Python installed. That is not a product. It is a demo.

> **INSTRUCTOR** · Let that land. Then: *"Today we fix that, and it has nothing
> to do with AI."*

---

## Beat 2 · Break (10 min)

> **INSTRUCTOR** · Do this on the projector, not on their machines.

Show them the Phase 1 agent working. Then:

1. Close your terminal.
2. Ask: *"Where is the agent now?"* — Gone. It was a process, and you killed it.
3. Ask: *"How would my colleague in another city use this?"* — They cannot.
4. Ask: *"How would a website use it?"* — It has no address to call.

Write the four gaps on the board:

```
no address          nobody can reach it
no memory of who    it cannot hold a conversation across two requests
no health signal    nothing can check whether it is alive
runs in one place   only where Python is already set up just right
```

**Those four gaps are today.** None of them are AI problems. All of them are why
agents die in notebooks.

---

## Beat 3 · Concept (15 min)

Four ideas. Explain each one only as far as they need it today.

### What "deploying" means

Right now the agent runs **on your computer, only while you are watching it.**

Deploying means putting it on a computer that:

- is always on
- is not yours
- has an address anyone can reach

That is it. There is no other magic in the word. The rest of this course is
about what goes wrong once that is true.

### What the public internet means

Every computer on the internet has a number, called an **IP address**. Like a
phone number for a machine.

Numbers are hard to remember, so we use names. `google.com` is a name that
points at a number. Something called DNS does the lookup, the way a phone book
turns a person's name into their number.

**When your agent is on the public internet, anyone who knows its address can
send it a request.** Anyone. Not just your users.

> **INSTRUCTOR** · Say that sentence twice. It is the seed of Week 3 (a stranger
> spending your model budget) and Week 7 (a stranger attacking you). Let it feel
> slightly uncomfortable now.

### What a URL is

A URL is an address. It has three parts that matter today:

```
   https://shop.example.com/chat
   ─────   ────────────────  ────
     │            │            │
   how to      which        which
    talk      computer      door
```

- **`https`** — how to talk. The `s` means encrypted, so nobody in between can
  read it.
- **`shop.example.com`** — which computer.
- **`/chat`** — which door on that computer. One computer can have many doors.
  Ours will have four: `/chat`, `/chat/stream`, `/health`, and later `/metrics`.

### What an HTTP request is

**A question and an answer.** That is all.

Your browser asks a computer for something. The computer answers. Then the
conversation is over — the computer forgets you entirely.

Every request has:

| Part | What it means | Ours |
|---|---|---|
| a **method** | what kind of thing you want | `GET` = read something, `POST` = send something |
| a **path** | which door | `/chat` |
| a **body** | the thing you are sending | `{"message": "where is my order?"}` |

Every answer has:

| Part | What it means |
|---|---|
| a **status code** | a number saying how it went |
| a **body** | the actual answer |

The status codes worth knowing, and we will use every one of these:

```
200   fine
400   YOU sent something wrong
401   who are you? (Week 3)
429   you are asking too often (Week 3)
500   WE broke (and it is our fault)
```

> **INSTRUCTOR** · The 400-vs-500 distinction matters more than it looks. Week 5
> alerts on error rate. If you return 500 when the caller sent nonsense, your
> dashboard blames you for their mistake. Mention it now, land it in Week 5.

**The important consequence:** the computer forgets you after every request. So
how does a conversation work? We send an ID back and forth. More on that in the
build.

---

## Beat 4 · Build (45 min)

> **INSTRUCTOR** · *"Hands on keyboards. Everyone open a terminal — the black
> window."* Then walk the room. Do not stay at the front.

### Part 0 · Terminal warm-up (8 min)

> **INSTRUCTOR** · Do not skip this even with a technical room. It costs eight
> minutes and it stops the next six weeks being about typos.

A terminal is a window where you **type commands instead of clicking**. Nothing
more mysterious than that.

Open one:

- **Mac** — press `Cmd + Space`, type `terminal`, press Enter
- **Windows** — press the Start key, type `powershell`, press Enter
- **Linux** — `Ctrl + Alt + T`

Now type each of these and press Enter. Type them — do not paste.

```bash
pwd
```

**Where am I?** Prints the folder you are currently in. Every terminal is always
"in" a folder.

```bash
ls
```

**What is in here?** Lists the files and folders.

```bash
mkdir practice
```

**Make a folder** called `practice`. `mkdir` = make directory. Nothing prints —
in a terminal, silence means it worked.

> **INSTRUCTOR** · Say that out loud: **silence means it worked.** Beginners
> assume no output means failure and run the command four more times.

```bash
cd practice
pwd
```

**Go into it.** `cd` = change directory. Now `pwd` shows you have moved.

```bash
cd ..
```

**Go back up.** `..` always means "the folder above this one".

Two more that save everybody's afternoon:

- **Tab** completes what you are typing. Type `cd prac` then press Tab.
- **Up arrow** brings back the last command. You will use this constantly.

```bash
rm -r practice
```

Deletes the practice folder. `rm` = remove, `-r` = including everything inside.

> **INSTRUCTOR** · *"`rm` does not ask, and there is no recycle bin. Read it
> twice before you press Enter."* Then move on — do not turn it into a horror
> story.

### Part 0b · Getting the project (5 min)

```bash
git clone https://github.com/nimeshmora/shipping-prod-ai-system.git
cd shipping-prod-ai-system
git checkout week-01-package
```

**`git clone`** downloads a copy of the project. **`git checkout`** switches to a
particular version of it — in our case, this week's starting point.

```bash
make install
make test
```

`make install` fetches the libraries the project needs. `make test` runs the
tests. You should see **12 passed**.

> **INSTRUCTOR** · Twelve green tests before they have written a line is
> deliberate. *"The agent loop already works. Phase 1 did that. Nothing you do
> today changes how it thinks."*

```bash
make check-week-01
```

This one **fails**, and says:

```
FAIL  app/main.py must define `app`, the FastAPI application
```

**That is the assignment.** Every week works this way: one command tells you
exactly what is missing, and you make it green.

### Part 1 · Give it an address (15 min)

Open `app/main.py`. It is a long comment telling you what to build — read it
together on the projector.

They build three doors:

| Door | Method | Answers with |
|---|---|---|
| `/health` | GET | `{"status": "ok"}` |
| `/chat` | POST | `{"reply": "...", "session_id": "..."}` |
| `/chat/stream` | POST | the answer, as it arrives |

Three things to say while they work:

**`/health` must be boring.** No model call, no database. It answers one
question: *is this process running?* A health check that depends on other things
fails when *those* things fail, and your container gets restarted for no reason.

**The session ID is how a forgetful protocol holds a conversation.** The
computer forgets you after every request — so the first reply includes an ID, and
the caller sends it back next time. Your code uses it to look up what was said
before. The model itself remembers nothing; every turn re-sends the whole
conversation.

> **INSTRUCTOR** · Demo it with two volunteers. One is the browser, one is the
> server. *"Hi, I'm asking about an order."* — *"Here's your answer, and here's
> ticket #47."* — *"Hi, ticket #47, what about delivery?"* Thirty seconds, and
> nobody is confused about session IDs again.

**Never let a raw error reach the caller.** If something breaks, return
`{"detail": "internal error"}` — not the actual error text. Error messages
contain file paths, database addresses, sometimes passwords. That is a security
bug, not a debugging aid.

Run it:

```bash
make run
```

In a **second** terminal window:

```bash
curl -s http://localhost:8080/health
```

**`curl`** sends an HTTP request from the terminal. It is a browser with no
window. You should get `{"status":"ok"}`.

> **INSTRUCTOR** · `localhost` = "this computer". `8080` is the port — a
> numbered door on that computer. Say it once, in passing.

Now the real thing:

```bash
curl -s -X POST http://localhost:8080/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"where is my order ORD-1002?"}'
```

Reading that command aloud:

- `-X POST` — the method. We are *sending* something, not just reading.
- `-H 'Content-Type: application/json'` — a header, telling the server the body
  is JSON.
- `-d '{...}'` — the body. The actual question.

Copy the `session_id` from the reply and continue the conversation:

```bash
curl -s -X POST http://localhost:8080/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"and when will it arrive?","session_id":"PASTE_IT_HERE"}'
```

**It remembers.** That is the session ID doing its job.

> **INSTRUCTOR** · The error you will see most this week — every week, in fact —
> is `KODEKEY is not set`. It means they edited `.env` but did not load it. The
> fix, in the *same* terminal as `make run`:
>
> ```bash
> set -a && source .env && set +a
> ```
>
> Write it on the board. Leave it there for eight weeks.

### Part 2 · Make it feel fast (10 min)

Ask: *"How long did that take?"*

Several seconds. And for all of it, they stared at nothing.

**Eight seconds of nothing feels broken. Eight seconds with words appearing
after 400 milliseconds feels fast.** Same duration. Completely different
product. This is why every AI assistant they have used streams.

They build `app/stream.py`, which sends the answer in pieces:

```
event: start          the turn was accepted
event: token          a piece of the answer (many of these)
event: done           finished
event: error          it failed
```

Three traps, all of which the checkpoint catches:

**The blank line after each piece is not optional.** It is what tells the
receiver "that piece is complete". Leave it out and the client waits forever for
something you already sent.

**An error mid-stream cannot be an error code.** By the time the model fails,
you already said "200, here it comes". There is no status code left to change.
The error has to arrive as another piece of the stream — and the client has to
read it. Miss this and a broken agent shows the user half an answer and calls it
success.

**Proxies buffer.** Something between you and the user will happily collect your
whole streamed answer and deliver it in one lump — which destroys the entire
point, silently, because the answer is still correct. The header
`X-Accel-Buffering: no` is how you say "do not do that".

Watch it work:

```bash
curl -N -X POST http://localhost:8080/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"message":"where is my order ORD-1002?"}'
```

**`-N` matters.** Without it, `curl` does its own buffering and they will think
streaming is broken when it is fine.

> **INSTRUCTOR** · Have someone shout when they see text appear in pieces. It is
> the most satisfying moment of the session — use it.

### Part 3 · Make it run anywhere (12 min)

Ask: *"What would my colleague need to run your agent?"*

The right Python. The right libraries, at the right versions. The right folder
layout. The right environment variables. **"Works on my machine" is not a
deployment.**

A **container** is a box holding your code *and* everything it needs to run.
Hand the box to any computer and it behaves identically.

> **INSTRUCTOR** · The analogy that works: a food truck versus a recipe. A
> recipe needs the other kitchen to already have the right oven, pans and
> ingredients. A food truck brings the whole kitchen with it and works in any
> car park.

They write a `Dockerfile` — the instructions for building that box:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8080
EXPOSE 8080
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
```

Read it line by line. **Two lines carry the whole lesson:**

**`COPY requirements.txt` comes before `COPY . .`** — Docker remembers each step,
and redoes every step after the first thing that changed. Copy your code first
and every one-character edit reinstalls every library. Three seconds becomes
three minutes.

**`--port ${PORT}`, not `--port 8080`** — every hosting platform tells your
service which door to use, through a setting. Hardcode the number and you have a
service that works on your laptop and fails the moment you deploy it.

Also worth pointing at, since they will ask:

- `--host 0.0.0.0` — accept connections from outside the box. The default only
  accepts them from *inside*, so the platform's health check could never reach
  you.
- `exec` — makes uvicorn the main process, so a "please shut down" signal
  actually reaches it. Without this the platform waits, gives up, and kills you
  — a slow, ugly deploy every single time.

They also write `.dockerignore`:

```
.venv/
.git/
__pycache__/
.env
```

**That last line matters most.** Without it, your API key gets baked into the
box. Boxes get copied, cached, and uploaded to servers other people can read.
**Never put a secret in a container.**

Build and run:

```bash
make docker-build
make docker-run
```

Then, from another terminal, the same `curl` as before. **Same answers, from
inside a box that could run anywhere.**

> **INSTRUCTOR** · Two things that will happen:
>
> 1. The first build takes a few minutes and looks stuck. Warn them.
> 2. Every build prints a warning about `JSONArgsRecommended` and OS signals.
>    It is safe to ignore — the `exec` in our `CMD` already solves the problem
>    the warning is about, but the build tool cannot tell. Say so before someone
>    panics.

---

## Beat 5 · Prove (20 min)

```bash
make check-week-01
```

Green, line by line. Read the output together — each line is a promise about the
service they just built.

Then close the loop by asking three questions they cannot yet answer. **These are
next week's hooks, and the honest answer to each is "we don't know".**

### "Your `/health` says ok. Suppose the model provider is down and every single
`/chat` returns 500. What does `/health` say?"

Still `ok`. The process is fine. It just cannot do its job.

> That gap is Week 5, and it is much bigger than it looks.

### "Where does the conversation history live?"

In a variable, inside the running program.

*"So what happens to it when we deploy a new version?"* Let them work it out.

> That is Week 2, and we are going to watch it happen.

### "Anyone who finds your URL can use it. What does that cost you?"

Real money, at the model provider, on your card.

> That is Week 3.

---

## If you finish early

- Have them try `ORD-1001`, `ORD-1077`, and an ID that does not exist.
- Then `ORD-1043`. Do not explain it. *"Note that one. We come back to it in
  Week 7."*
- Have them break their own service: return the wrong status code from
  `/health`, then watch `make check-week-01` catch it.

## Homework

- `make check-week-01` green, committed and pushed
- Read `guide/week-01.md` in the repo — the same material, written for reference
- Install Docker Desktop if they have not, and check `make docker-build` works
  **before** next session

> **INSTRUCTOR** · Chase the Docker install. Week 2 deploys a container, and one
> student without Docker becomes twenty minutes of everyone else waiting.
