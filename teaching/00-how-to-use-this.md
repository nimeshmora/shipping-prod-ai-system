# Phase 2 Teaching Guide · How to use this

## What this document is

One file per week, written to be read two ways at once.

**Normal text is for students.** They can read it before class, during class, or
afterwards when they have forgotten what you said. It explains every concept in
plain language and gives every command they need to type.

**Boxed notes are for you.** They look like this:

> **INSTRUCTOR** · 10 min
> Ask the room before you show anything. Wait for silence to get awkward — that
> is when the quiet ones answer.

If you hand this to students as-is, they will read your notes too. That is
usually fine. If you would rather they did not, strip lines starting with `>`.

## What Phase 2 is, in one sentence

**Phase 1 built an agent. Phase 2 makes it something a company can actually
run.**

Nothing in Phase 2 changes how the agent thinks. Every week is about the
distance between *"it works on my laptop"* and *"it works for customers, at
3am, when a provider is down, and nobody is watching."*

## The shape of every week

Weeks 2–8 follow the same five beats. Students learn the rhythm and stop
needing to be told what is happening.

**Week 1 is different and does not use beats at all** — it is a four-hour day
in twelve named sections. See **Week 1 slides** at the end of this file.

| Beat | Time | What happens |
|---|---|---|
| **Ask** | 10 min | Questions to the room about last week. No slides. |
| **Break** | 10 min | Something fails on purpose, in front of them. |
| **Concept** | 15 min | The idea they need, explained plainly, at the moment they need it. |
| **Build** | 45 min | Hands on keyboards. You walk the room. |
| **Prove** | 20 min | `make check-week-0N` goes green. Then discuss what is still broken. |

> **INSTRUCTOR** · The **Break** beat is the one people cut when running late.
> Do not cut it. A student who has *watched* memory vanish on redeploy
> remembers it for years. A student who was *told* it happens forgets by
> Thursday.

Four weeks bend the shape deliberately, and each says so at the top:

- **Week 1** is a **four-hour day**, not a two-hour session, and it does not
  use the five-beat shape at all. It runs eleven named sections with two breaks:
  the agent is introduced first, then the tools (terminal, JSON, curl) are
  handed over on toys, and only then does the theory arrive — by which point
  every concept is a name for something the room has already done. See
  **Week 1 slides** at the end of this file for the hour-by-hour shape.
- **Week 2** gives Break 25 minutes, because deploying happens inside it.
- **Week 6** leads with a 35-minute bug hunt and puts Break in the middle, where
  the session changes subject.
- **Week 8** ends with a fourth part — porting and Kubernetes — which is
  discussion, not build.

Every week also closes with **If you finish early** and **Homework**. The
early-finish items are genuine extensions, not filler: several of them are the
cheapest way to make the week's point land twice.

## Five rules that make this work

**1. Teach a concept the moment it is needed, never before.**

We do not have a "networking week". We explain what a URL is in Week 1, at the
minute a student needs to type one. We explain what a container is when they
are about to build one. Concepts taught in advance are concepts forgotten in
advance.

**2. Every command gets typed, not pasted.**

Slower, and worth it. Typing `mkdir` twenty times is how it stops being
magic. Paste the long ones (a `gcloud` deploy line is not a typing exercise),
type the short ones.

**3. Every hard idea gets an everyday picture first.**

Before the technical explanation, something from ordinary life that has the
same shape. Not decoration — the picture is what they keep.

| Concept | The picture that comes first |
|---|---|
| deploying | a shop that is only open when the owner is inside |
| DNS | your phone's contacts list |
| a URL | a building, and a room inside it |
| a port | one building, many numbered doors |
| FastAPI / uvicorn | a doorman, and a translator behind him |
| a container | a food truck, versus a recipe |
| an HTTP request | a counter clerk who helps you, then forgets you |
| a session ID | the ticket the clerk gives you to bring back |
| state in a process | the only record of your order is in one assistant's head |
| context growth | a colleague with no memory, re-read the whole chat each time |
| telemetry vs monitoring | till receipts vs "how were sales this week?" |
| SSRF | asking someone with a badge to fetch a file you cannot reach |
| the eval judge | a checklist, versus a supervisor reading the letter |

> **INSTRUCTOR** · Give the picture, then the mechanism, then say the picture
> again in one line. The third step is the one people skip and it is what makes
> it stick.

**4. Learn the tool on a toy. Then use the tool on our thing.**

This one shapes the whole guide, and it is the rule to protect when you are
running late.

A student's first `curl` is not a three-flag POST at our `/chat` endpoint. It
is `curl -s https://example.com`, which prints some HTML and cannot fail in an
interesting way. Their first Dockerfile is four lines that print `hello from
inside the box`. Their first Redis is `SET greeting "hello"` typed by hand.

The reason is diagnostic, not pedagogical comfort: **when the real thing breaks,
they can tell which part broke.** A student who has only ever run curl against
our agent cannot distinguish *"my JSON is malformed"* from *"my flags are
wrong"* from *"the service is down"*. A student who ran the five curl toys can.

Every tool the course introduces gets this treatment:

| Tool | The toy, before our agent |
|---|---|
| the terminal | `pwd`, `ls`, `mkdir`, `cd` in a scratch folder |
| folders and paths | build a drawn three-level tree by hand, then `ls -R` it |
| a process | `sleep 30`, then Ctrl+C |
| JSON | `echo '{"name":"Ada"}' \| python3 -m json.tool`, then break it |
| curl | example.com → GitHub's API → status codes → POST to an echo service |
| streaming | `curl -N https://httpbin.org/stream/3`, with and without `-N` |
| Docker | a four-line Dockerfile that prints one sentence |
| env vars | `export GREETING=hello`, then read it back |
| Redis | `SET`/`GET`/`SETEX`/`TTL` by hand in `redis-cli` |
| YAML | read a real workflow file and find three things in it |
| shell loops | `for i in $(seq 1 3); do echo "request $i"; done` |
| regex | four strings, three matches, one bypass |
| fakes/mocks | a six-line function with a swappable argument |

Every one of those has verified output printed in the guide, so you know what
they should see before you run it in front of twenty people.

**5. In Week 1 only, the tools come before the theory.**

Rule 1 says teach a concept the moment it is needed. Week 1 has a problem the
other seven do not: the room may never have opened a terminal, so there is no
floor to teach *anything* from.

So Week 1's second beat — **Ground** — hands over five tools on toys before a
word of theory: the terminal, folders, a process and a port, JSON, and curl.
Only then does the Concept beat explain deploying, web services, DNS, URLs and
HTTP.

The payoff is that **every concept becomes a name for something they already
did**:

| When you explain… | They have already… |
|---|---|
| what a URL is | fetched two of them with curl |
| status codes | made a 200, a 404 and a 500 appear |
| method / path / body | typed all three as curl flags |
| a process | run `sleep 30` and killed it with Ctrl+C |
| a port, `localhost` | seen the `:7000` shape |
| why sharing a file fails | waited for `make install` to download everything |

> **INSTRUCTOR** · The temptation when you are running late is to cut Ground and
> lecture the concepts instead. Cut the concepts and keep Ground. A room with
> five working tools and no theory can still build; a room with five concepts
> and no terminal cannot type.
>
> Weeks 2–8 revert to the five-beat shape, because from Week 2 onward the floor
> exists.

## The repo layout

The project is built **layer by layer, one git branch per week**:

```
week-01-package    <- students start here. Working code + this week's gaps.
week-01-solution   <- the answer key
week-02-deploy     <- week 1 complete, plus week 2's assignment
week-02-solution
...
main               <- the finished agent, all eight weeks
```

A student starting Week 5 cold gets a working Weeks 1–4 agent. Nobody ever
debugs someone else's half-finished code.

```bash
git checkout week-01-package
make install
make test              # green: the code you were given works
make check-week-01     # red: this is your assignment
```

Stuck on one file? The answer key is one command away:

```bash
git diff week-01-package..week-01-solution -- app/main.py
```

> **INSTRUCTOR** · Tell them about `git diff` against the solution on day one,
> and tell them it is *allowed*. Someone who is stuck for 40 minutes learns
> nothing; someone who peeks, then retypes it themselves, learns most of it.

## What you need before session one

- Each student has the repo cloned and `make install` working
- Each student has a Buildr Labs API key in `.env`
- Docker Desktop installed (Week 1) — check this *before* the session, it is
  the single most common blocker
- A Google Cloud account with billing enabled (Week 2)

> **INSTRUCTOR** · Send a setup email a week early with exactly two commands:
> `make install` and `make test`. If those pass, they are ready. Budget 20
> minutes of session one for the three people who ignored the email.

## The eight weeks

**Ship it (1–3) → operate it (4–6) → trust it (7–8).**

| Week | Session title | They leave with |
|---|---|---|
| 1 | Package | An agent anyone on the internet could call — if it were online |
| 2 | Deploy | A public URL, and memory that survives a restart |
| 3 | Automate and lock | `git push` deploys it; strangers get a 401 |
| 4 | Cap | It cannot run forever or run up a bill |
| 5 | See | They can tell whether it is healthy |
| 6 | Debug and survive | They found a bug from traces; it survives an outage |
| 7 | Attack | They red-teamed their own service |
| 8 | Gate | A bad change cannot reach users |

---

## Printable version

`teaching/phase-2-teaching-guide.pdf` is all nine files as one 141-page A4
document in the Buildr Labs house style, with the instructor notes keeping
their boxes on paper.

The theme is taken from the tokens the live site publishes — the orange
`#f46622`, warm off-white `#f6f4ee`, near-black ink `#121212`, with **DM Sans**
for text and **Space Mono** for code. The two typefaces are downloaded once and
embedded in the HTML, so the file prints identically on a machine with no
network. (They cache in `teaching/.fonts.css`; delete it to re-fetch. With no
network on the first run, it falls back to system fonts and says so.)

To rebuild it after editing any week:

```bash
python teaching/build-pdf.py
```

That writes `teaching/phase-2-teaching-guide.html`. Open it and press
**Cmd + P** (or **Ctrl + P**) → *Save as PDF*, with **Background graphics**
ticked so the instructor boxes keep their shading.

If you have Chrome installed, one command does the whole thing:

```bash
python teaching/build-pdf.py
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --no-pdf-header-footer \
  --print-to-pdf=teaching/phase-2-teaching-guide.pdf \
  teaching/phase-2-teaching-guide.html
```

The HTML is also perfectly readable on screen, and easier to search than the
PDF — some instructors prefer to teach from it in a browser tab.

---

## Week 1 slides

`teaching/week-01-slides.html` is a 179-slide presenter deck for **day one, run
as a four-hour session**, in the same house style as this guide. Open it in a
browser and press **F** for fullscreen.

The deck deliberately does **not** use the word "beat" or any internal
numbering — students see sections named by what happens in them, and a running
clock in the top-right corner of every slide.

| Key | What it does |
|---|---|
| `→` / `space` / `N` | next slide |
| `←` / `P` | previous slide |
| **`S`** | **toggle the presenter-notes panel** |
| `F` | fullscreen |
| `1`–`9` | jump to a section of the day |
| `0` | the last two sections (press again to cycle) |
| `G` | go to a slide number |
| `?` | show all keys |

**Press `S` before you start.** A hundred and sixty-seven of the slides carry
a presenter cue — the callback to make, the question to ask, the thing *not* to explain
yet — in a side panel the room never sees.

### The four-hour shape

```
   0:00   11   Three questions to the room   settle the room, and read it
   0:11   27   Meet today's agent            described, then RUN step by step
   0:38    8   The project                   a tour BEFORE they download it
   0:46   21   Set it up, and prove it       .env, the key, make install, demo
   1:07   10   break
   1:17   20   The terminal                  a real lesson: 9 commands
   1:37   16   Sending messages              JSON, curl and jq
   1:53   10   break
   2:03   14   What a web service is         the shop story, then the words
   2:17   19   Addresses, then SIX ZOOMS     one request, internet to code
   2:36   38   Build the web service         3 endpoints, line by line, tested
   3:14   36   Packing it up                 containers, then Docker Hub
   3:50   10   Prove it, and what breaks next
   ────────────
   4:00        exactly four hours, including both breaks
```

**168 slides over 220 minutes of content is about 75 seconds each.** That is
the intended pace: one idea, one sentence, take a question, advance.

> **INSTRUCTOR** · Three things about this order, all deliberate.
>
> **It opens with questions, not a plan.** Three of them, and they do different
> jobs. The agenda appears once they have something to hang it on, and never
> again — after that the clock in the corner of each slide is enough.
>
> **Today's agent is introduced before anything is installed.** You cannot
> share what you cannot describe, and the question *"so who else could use
> this?"* only bites once they have seen real code doing real work.
>
> **Only the last hour is typing code.** Say that out loud when you show the
> agenda. The three hours before it are the reason the last hour works.

### The three opening questions

They are ordered on purpose, and the third is the one people skip.

| # | Question | What it is for |
|---|---|---|
| 1 | *What is an agent?* | teaches the loop — the idea the whole day sits on |
| 2 | *Is that different from ChatGPT?* | uses the one example the whole room shares |
| 3 | *Have you ever built a website, and put it somewhere so friends could see it?* | **tells you who is in the room** |

Question 3 runs as **three shows of hands**: made something on your own
computer · put it somewhere others could reach · had to keep it working
afterwards. The deck says what each pattern of answers means for the rest of
your day.

> **INSTRUCTOR** · Question 3 is for *you*, not for them, and it changes how
> you teach the next four hours:
>
> - **Mostly first hands only** — a genuine beginner room. Go slower at 1:05,
>   and say *"no output means it worked"* twice.
> - **Many second hands** — they have already felt the problem. At 2:02, ask
>   *"what did you actually have to do?"* and let them tell it. That saves you
>   ten minutes of explaining.
> - **Any third hands** — you have allies. Ask those people to help their
>   neighbours during the build sections, and call on them by name.
>
> Say *"there is no wrong answer, I am asking so I know where to start"* before
> you ask it. Otherwise the quieter half of the room will not put a hand up.

### Why today's agent is the small one

The deck says this explicitly, on its own slide, because somebody in the room
is always wondering why they are not using the agent they are proud of:

> *"We are not replacing what you built. We are learning the plumbing on
> something small enough that you can see all of it. Once the plumbing is
> second nature, we point it at anything you like."*

One new hard thing at a time. A simple agent plus a hard deployment today; a
complex agent plus a known deployment later. Same skills, learned in an order
where a student can always tell what went wrong.

### Nothing arrives before it is needed

Every one of the 122 transitions was checked for topic jumps. The rule the
deck now follows: **a word is introduced at the moment the room needs it, not
in a lecture beforehand.**

The clearest example is the word **process**. It used to be taught at the end
of the terminal exercise — a definition arriving out of nowhere, straight after
a folder drill. It is now at 2:27, immediately after `make run` refuses to give
the prompt back, so the question *"why has my terminal stopped?"* comes from
the room and the word answers it.

| Was | Now |
|---|---|
| process, after a folder exercise | process, when `make run` will not finish |
| error handling, after testing `/chat` | error handling, before testing it |
| the port warning, five slides after the port line | directly after the port line |
| the day's recap, after homework | before homework, closing the teaching |

One container slide was deleted outright: the shop story already taught what
it said, so it read as a repeat.

> **INSTRUCTOR** · If you ever feel a slide arrive from nowhere while
> teaching, that is a real defect — tell us. The fix is almost never to explain
> it better; it is to **move it to where the need appears.**

### Every section hands over out loud

The last presenter note in each section carries the sentence that leads into
the next one, so the day never changes subject without warning:

| Handover | The line to say |
|---|---|
| terminal → messages | *"You can now find your way around a computer by typing. Everything from here is about talking to something else."* |
| `/health` → `/chat` | *"The door works, but it only says 'I am alive'. Nobody can ask it anything yet."* |
| `/chat` → streaming | *"It works. But how long did that take, and what were you looking at while you waited?"* |
| cart story → image/container | *"So we need to build a cart. Two words first, because people mix them up."* |
| service → container | *"Three of the four gaps are closed. The last one: it still only runs on your laptop."* |

> **INSTRUCTOR** · Read the handover **before** you advance, while the previous
> slide is still up. It is one sentence and it is what makes the day feel like
> one lesson rather than twelve.

### The build sections match the repository exactly

Every code line on a build slide is **the line that goes in the student's
file**, checked against the `week-01-solution` branch. Not a paraphrase, not a
simplified teaching version.

Where a slide shows less than the final line, it is because we add to it
later, and the notes say so:

| Slide shows | Real file ends up with | When |
|---|---|---|
| `from fastapi import FastAPI` | `..., HTTPException` | when errors are added |
| `from app import memory` | `..., stream` | at endpoint 3 |
| `from app.agent import run_turn` | `AgentError, run_turn` | when errors are added |
| `app = FastAPI()` | `FastAPI(title="...")` | optional, mentioned once |

All eight Dockerfile lines match `week-01-solution:Dockerfile` character for
character.

> **INSTRUCTOR** · Every code slide **names its file in the eyebrow** —
> `app/main.py · line 1`, `Endpoint 2 of 3`. Students can follow along in
> their own editor without asking which file they are in.

### Each endpoint is tested the moment it exists

The build does not write the whole file and then run it. It goes:

```
   write /health        (5 lines)  ->  TEST IT   curl /health        ✓
   write /chat          (9 lines)  ->  TEST IT   curl /chat          ✓
                                       and again with the session id ✓
   add error handling               ->
   write /chat/stream   (8 lines)  ->  TEST IT   curl -N /chat/stream ✓
                                   ->  ALL FOUR, one after another
```

> **INSTRUCTOR** · This is the point of the section. **When something breaks,
> it is the thing they just typed** — not one of nine unknowns.
>
> The last slide runs all four commands in order, including the `422` from an
> empty body. Do that one on the projector: it is the demo that makes the
> afternoon feel finished, and every tick is something they wrote.

### Streaming is endpoint 3, not a separate topic

It used to be its own section, which made students ask *why are we talking
about this now.* It is now simply **the third endpoint**, introduced by the
question it answers:

> *"How long did that last answer take? And what were you looking at while you
> waited?"*

Nothing. That is the problem streaming solves, and it arrives immediately
after they have felt it on their own screen.

### The key is finished during setup

`OPENROUTER_API_KEY is not set` used to appear mid-afternoon, which was confusing — a new
concept arriving in the middle of a build. **The whole topic is now closed at
0:43**, with the `set -a && source .env && set +a` command on the whiteboard
and a ten-second demo of why:

```bash
export TEST=hello
echo $TEST          # hello
# now open a NEW window
echo $TEST          # empty
```

> **INSTRUCTOR** · Do that demo rather than describing it. Once they have
> *seen* a setting fail to cross windows, the error never needs explaining
> again — you just point at the board.

### Code is built one line per slide

The two build sections do not show a finished file and explain it. They
**write it in front of the room, one line at a time** — 15 line-by-line slides
in the web service section, 6 in the container section.

Each of those slides has exactly three things on it:

```
   the file so far      lines already written, dimmed
                        THE NEW LINE, bright, marked "new"
                        lines still to come, very faint

   one sentence         what the new line does, in plain English

   a progress strip     which piece of six you are on
```

> **INSTRUCTOR** · This is the format to keep for every week. It costs more
> slides and no more time, because you were going to say these sentences
> anyway — the difference is that **the room can see which line you are
> talking about.**
>
> Advance, read the one sentence, take questions, advance. Do not read the
> dimmed lines again; they have already had their slide.
>
> Median on-screen text is **96 words per slide**. Anything over about 150 is
> a reference table meant to stay up while people work, not something to read
> aloud.

### uvicorn and FastAPI are separated

Students meet these two words together and assume they are one thing. They now
get separate one-line definitions and a four-step journey slide:

| | What it is |
|---|---|
| **uvicorn** | the program that **waits** for network messages on one port. A program you *start* — it is what `make run` runs. |
| **FastAPI** | the library that **reads** each message and picks which of your functions answers it. Code you *import*; you never start it. |

> **INSTRUCTOR** · The sentence that settles it: *"uvicorn listens. FastAPI
> decides who answers. You write the answering."*
>
> Do not explain ASGI, workers or event loops. None of it changes anything
> they do that afternoon.
>
> If somebody asks how uvicorn finds their code: it is the `app.main:app` in
> the run command — the file `app/main.py`, and the thing called `app` inside
> it. That pays off later, when the same string appears in the Dockerfile's
> last line.

The nineteen-line file taught across those slides was written out in full and
run against the real agent: `/health` returns 200, an empty body is refused
with 422, and two turns with the same session id produce a history that grows
from four messages to eight. It is not a paraphrase of the answer key.

### The fix list, applied

A batch of corrections that touch the repo as well as the slides:

| Change | Where it landed |
|---|---|
| **`python3` everywhere** | the Makefile (`python3 -m`, `pip3 install`), every slide command, both guides |
| **`make install` explained** | its own slide — `requirements.txt` is the shopping list, `pip3` fetches it, and a slide showing `cat Makefile` so `make` stops being magic |
| **`set -a && source .env && set +a` explained** | its own slide, taken apart into three parts: turn on sharing, read the file, turn sharing off |
| **`\| jq` on every JSON curl** | plus a slide teaching it, with the `python3 -m json.tool` fallback for anyone without it |
| **Logs** | a slide on reading window 1 — who asked, what for, what number came back |
| **OpenRouter** | `OPENROUTER_API_KEY`, `https://openrouter.ai/api/v1`, vendor-prefixed model ids (`anthropic/claude-sonnet-4.5`), renamed **across all 17 branches** |
| **Port 7000** | replaces 8080 in the Dockerfile, Makefile, `.env.example`, code, tests and every slide |
| **`app/main.py` as TODOs** | eight numbered TODOs instead of one long comment block |
| **Stream command in the README** | already there; now the README also has a second `/chat` call showing the session id, and `\| jq` on the JSON ones |
| **Docker Hub** | a six-slide activity, and an account added to the prerequisites |

> **INSTRUCTOR** · Two of these change what students type, so check them in the
> setup email: **an OpenRouter key** (free at openrouter.ai) and **a Docker Hub
> account** (free at hub.docker.com). The Docker Hub one is only needed at 3:14,
> but signing up mid-session wastes ten minutes.

### The Docker Hub activity — why containers matter, felt

Six slides at the end of the container section. **This is the payoff for the
whole section**, and it lands better than any explanation:

```
   1  add one small endpoint     GET /orders, four lines, same shape as /health
   2  build and name it          docker build -t <username>/ship-agent:v1 .
   3  push it                    docker push  -> now it has a public address
   4  pull a NEIGHBOUR's         docker pull <neighbour>/ship-agent:v1
                              docker run --rm -p 7000:7000 --env-file .env
                                 curl -s localhost:7000/orders | jq
```

Then one slide comparing it with their own morning:

| this morning, at 0:46 | just now |
|---|---|
| **twelve minutes** — clone, install, right Python, right libraries, paste a key, *and it still broke for somebody* | **two commands** — pull, run, nothing to set up, *worked first try* |

> **INSTRUCTOR** · **Have everybody write their image name on the whiteboard**
> as they finish pushing. That is what makes step 4 work.
>
> **The line to say at step 4:** *"You did not install their Python. You did
> not read their requirements file. You did not ask which version of anything
> they used. You ran two commands."*
>
> **Then the honest detail:** they still passed their *own* `.env`. **The code
> travelled; the key did not.** That is the separation from 0:46 working as
> designed — and it is worth naming, because it is the thing people get wrong
> when they first publish an image.

### One idea per slide

The deck was audited for crowding and rebuilt. **Twelve slides carried five or
more separate blocks** — a definition and an example and a caveat and a
punchline, all at once — which makes it hard to know where to start and where
to stop. Each was split.

| | Before | Now |
|---|---|---|
| slides | 147 | **168** |
| median blocks per slide | 2 | **2** |
| slides with 5+ blocks | **12** | **0** |
| median on-screen words | 96 | **88** |

The rule applied: **at most one code block or one figure, plus at most two
supporting cards.** If a slide had a definition *and* an example *and* a
caveat, it became two slides.

> **INSTRUCTOR** · This is what makes the deck teachable rather than just
> correct. **Each slide is now one thing you can open, say, and close** — then
> advance and the next one builds on it.
>
> At ~75 seconds a slide you will feel like you are advancing quickly. That is
> right. **The notes are cues, not scripts** — do not read them aloud.

### A request, traced from the internet inwards

Six slides at 2:13 follow **one question** from a stranger down to the code,
**adding exactly one layer per slide** and keeping the earlier ones on screen:

```
   1  the internet   someone, somewhere, has your address and a question
   2  one computer   the message arrives at the machine
   3  a port         which of the running programs is it for?  (7000)
   4  a program      uvicorn was waiting there; it takes it off the network
   5  your code      FastAPI hands it to your function - the only layer
                     they write
   6  the agent      run_turn(), and the answer travels back out
```

Each slide nests inside the previous one, with an arrow and a caption for the
hop, plus a breadcrumb strip showing how deep you are.

> **INSTRUCTOR** · This sequence exists for the non-technical half of the room,
> and it is the single best thing in the deck for them. **Ninety seconds a
> slide, and do not skip ahead** — the value is in the layers accumulating.
>
> **Slide 5 is the one to land:** *"Of the six layers on screen, this is the
> only one you write."* Point above it, point below it.
>
> **On slide 6, trace it backwards with your finger** — answer, function,
> FastAPI, uvicorn, network, stranger. *"Same path, in reverse."*
>
> Then the hook: *"Six layers. At 3:12 we put a box around all of them."* The
> container section refers back to this picture rather than starting fresh.

### The demo states its model, its key use, and its payload

Three questions the demo was silent about, all now answered on screen. The
command prints them **before** step 1, so nobody has to guess:

```
  MODE: a stand-in for the model - no key, no internet, free
        the LOOP below is the real one
        only the model's choice is scripted

  WHAT GETS SENT, every single question:
     1. the standing rules       105 words, not sent - no model to send them to
     2. the conversation so far  empty - this is question one
     3. the list of tools        3 of them:
           - lookup_order
           - calculator
           - word_count
```

With `--real` the first line reads **`MODE: the real model - anthropic/claude-sonnet-4.5`**
and item 1 reads **"sent with the question"**.

| The question | The answer |
|---|---|
| Which model is underneath? | `anthropic/claude-sonnet-4.5`, through the course gateway. **It is a setting in `.env`**, not baked into the code — Week 6 swaps in a second model by changing it. |
| Is a key used in the demo? | **No.** The stand-in mode needs no key and no internet, which is why we run it first — every laptop sees the same thing. |
| Do the rules really go with every question? | **Yes**, and the payload block proves it. In stand-in mode they are not actually sent, because there is no model to send them to — **and the line says so.** |

Two slides at 0:11 cover this before the demo runs: the two run modes side by
side, and what gets sent with every question.

> **INSTRUCTOR** · **The honesty matters here.** You told them at the
> instructions slide that the rules go with every question. The stand-in does
> not send them — so the command says so rather than letting the slide quietly
> contradict itself. **If you have a key, run `--real` once** and show item 1
> change to "sent with the question". That is the cleanest proof available.
>
> Point at item 2 and plant Week 4: *"That one is empty now. Watch what it
> costs when it is not."*

### The demo is the instructor's, and they run it later

**A real contradiction, caught while reviewing:** the demo runs at 0:12, but
the project is not downloaded until 0:45. Students were shown a command they
could not possibly run yet.

Fixed in two places:

- **At 0:12** the slide says so plainly: *"This one is on my machine, not
  yours. I have the project downloaded already — you will do that at 0:45, and
  then run this exact command yourself."*
- **At 0:45**, after the key is set and `check-week-00` is green, a new slide
  hands it to them: *"The command you watched me run at 0:12."*

> **INSTRUCTOR** · Say that first sentence out loud. Without it, somebody
> spends ten minutes wondering why they cannot follow along — or tries, fails,
> and stops listening.
>
> The 0:45 slide is the payoff. Collect it: *"Remember this from the start of
> the session? Now it is yours."*

**The question is an argument**, so they can poke at the decision from step 2:

```bash
python3 -m checks.demo_turn                        # picks lookup_order
python3 -m checks.demo_turn "what is 12 * 41?"     # picks calculator -> 492
```

That was a false claim on the slide until now — the stand-in model hardcoded
`lookup_order`, so changing the question changed nothing. `checks/demo_turn.py`
now chooses a tool from the question, and both variations are verified on the
`week-01-package` branch.

### `.env` gets three slides, in plain English

Telling a non-technical room to "put your key in `.env`" means nothing. Three
slides at 0:45 build it up **before** the step that asks them to:

1. **Some things must not live in the code** — the code is the same for
   everybody; your key is only yours. *"A shared document everyone edits,
   versus the sticky note with your own password on it."*
2. **That separate place is a file called `.env`** — the format is
   `NAME=value`, one per line, and nothing more. The leading dot means hidden
   (which they met with `ls -la`), and it is on the never-upload list.
3. **Every project works this way** — one copy of the code, a different
   `.env` on your laptop, on a test server, and in production.

> **INSTRUCTOR** · **Do not say "environment variable" on those three
> slides.** That phrase arrives on the next slide, with the command that loads
> the file — the moment it actually means something.
>
> Slide 3 answers the question people ask silently: *"why not just edit the
> code when I need a different setting?"* Because then you have three slightly
> different copies of the code and no way to tell them apart.
>
> It also pre-loads two later moments: next week the hosting platform supplies
> the settings instead of a file, and at 3:10 the container must not have the
> key baked into it.

### The agent is demonstrated one step at a time

The section used to describe the agent and never run it. It now ends by
**watching it work**, through one command:

```bash
python3 -m checks.demo_turn        # no key, no internet, works on any laptop
python3 -m checks.demo_turn --real # with a key: the real model decides
```

`checks/demo_turn.py` prints **four labelled steps with a pause between each**,
so the room can read one before the next appears, then prints the conversation
it kept:

```
  The agent can reach for 3 tools:  lookup_order, calculator, word_count

  STEP 1 · YOU ASK                  where is my order ORD-1002?
  STEP 2 · THE MODEL DECIDES        tool: lookup_order  input: {"order_id": ...}
  STEP 3 · YOUR CODE RUNS THE TOOL  ORD-1002: standing desk, $340.00, shipped...
  STEP 4 · THE MODEL ANSWERS        Your standing desk is shipped and arrives...

  AND IT KEPT THE CONVERSATION - 4 entries
```

**Each step gets its own slide** with what to say on it. The deck does not show
all four at once.

> **INSTRUCTOR** · **Run it twice.** First straight through with no
> commentary — eight seconds, and they see all four steps land. Then again,
> talking over it, using the slides.
>
> **Step 2 is the one to slow down on.** Two things happened and they are worth
> naming separately: it *chose* a tool out of three, and it *filled in the
> input* by reading `ORD-1002` out of an ordinary sentence. Then: *"And now it
> has stopped. It did not fetch anything. It asked, and it is waiting for us."*
>
> **Step 3 carries the reason for the next eight weeks.** *"Our code obeyed. It
> did not check whether the id was reasonable, or who was asking, or how many
> times."* That is why Week 3 adds a locked door and Week 4 adds spending
> limits — **every guard sits in your code, not in the model.**
>
> **If you have time**, ask it `what is 12 * 41?` and watch step 2 pick
> `calculator` instead. Tool choice, visible.

### Is our agent industry-standard? Yes — and there is a slide saying so

Somebody always wonders whether this is a real agent or a classroom version,
so the deck answers it outright. What students watch is **tool use** (also
called function calling): the pattern Anthropic, OpenAI and Google all
document, and what every agent framework does underneath.

| Standard practice | In our agent |
|---|---|
| tools described in JSON Schema | yes — `input_schema` on each tool |
| loop ends when the model answers | yes — on `stop_reason != "tool_use"` |
| tool results returned as messages | yes, as a `tool_result` block |
| a step cap, so it cannot run forever | yes — `MAX_STEPS = 6` |
| a timeout on the model call | yes — `MODEL_TIMEOUT_SECONDS` |
| tool errors returned as readable text | yes — not raised as a crash |

> **INSTRUCTOR** · **One honest detail, for the technical question only.** Our
> gateway speaks the OpenAI message format while the loop internally uses the
> Anthropic block shape, with a small translator between them. That is a
> deliberate production pattern — provider portability — and **Week 6 uses
> exactly that seam to add a fallback model.**
>
> Do not volunteer it to a non-technical room. Keep it for the person who asks.

### The terminal gets a real lesson, not a warm-up

Twenty-six minutes and fifteen slides. It used to be five slides with four
commands crammed onto each, which is unusable for anyone who has not used a
terminal before.

**One command per slide**, each with a numbered plain-English reading:

```
   what it is, and why (no screen on a server)
   the anatomy of a command      command · option · target
   pwd, ls                       where am I, what is here
   NO OUTPUT MEANS IT WORKED     the rule that prevents most panic
   the exercise, drawn           what we are about to build
   mkdir                         and run it twice, to see a useful error
   cd, cd ..                     plus the "cd then pwd" habit
   touch                         and that commands accept a list
   PATHS                         a slash means "go through"
   echo, and >                   print, then redirect into a file
   cat                           look inside · and it is read-only, so safe
   ls -R                         check your work against the whiteboard
   ls -la                        hidden files — in the REAL project folder
   rm -r, and the reference table
```

> **INSTRUCTOR** · Three slides in there are worth protecting if you are short
> of time:
>
> **"No output means it worked."** Say it twice. It costs four seconds and
> prevents a specific confusion five times over.
>
> **Paths.** Beginners `cd` in and out of folders one step at a time for years.
> One slide fixes it: *"a slash means go through"*.
>
> **`ls -la` in the real project folder.** It is the first time the exercise
> touches something that matters, and it catches anyone whose editor saved
> `.env` as `.env.txt` — at 1:20 instead of at 2:40.

The section ends with an explicit bridge, because the handover used to be
abrupt:

> *"Notice what all nine commands have in common: every one talks to THIS
> computer. Nothing we have learned can reach another machine — and your
> agent's whole problem is that nobody else can reach it. So next: how one
> computer sends a message to another."*

### Containers get five worked examples

Three more slides than before, all of them making the abstract concrete:

| Added | Why |
|---|---|
| **What Docker is**, and its four commands | they kept looking for a Docker *window*; it is a background service |
| **`docker images`** | the packages appear as a real list, with sizes — more convincing than any definition |
| **`docker run -it demo2 sh`** | a prompt *inside* a package: `pwd` shows `/app`, `ls` shows their copied file |

> **INSTRUCTOR** · That last one is the most convincing moment of the section,
> and it retires the terminal lesson properly: *"Those nine commands were not
> just for your laptop. That is a Linux computer, and you can already use
> it."*
>
> Remind them to `exit` — otherwise somebody stays inside the container and
> wonders why their next command behaves strangely.

### Containers get 38 minutes, and are taught from nothing

The second-longest section of the day, after the web service build. It is the
topic a non-technical room finds hardest and the one most courses rush.
Twenty-two slides, in this order:

1. **The problem** — they rebuild the setup list from 0:43 themselves
2. **The idea, before the word "Docker"** — send the set-up, not just the code
3. **Image vs container** — the installer you downloaded, versus the app open
   on your screen
4. **The chain**: Dockerfile → build → image → run → container
5. **Example 1** — two lines, prints `hello`
6. **Example 2** — your own file copied in
7. **Proof it is sealed** — delete the file, run it again, it still works
8. **Example 3** — a real web server, and `-p` explained
9. **Layers** — a visual stack of which steps are reused and which are redone
10. **Our agent's Dockerfile** — five slides, one line at a time
11. **`${PORT}`** — why never to write the number in
12. **`.dockerignore`** — and never packaging a secret
13. **Build and run ours** — the same `curl`, from inside a package

> **INSTRUCTOR** · Three things to protect here.
>
> **Say the idea before the tool.** Slide 2 has no Docker in it at all. Once
> they have *"stop sending the recipe, send the finished meal"*, the words are
> just labels.
>
> **Image versus container is the most-confused pair in the topic.** Spend two
> minutes. The installer-versus-open-app comparison is exact, not loose. Then
> check it: *"If I build one image and start it on three computers, how many
> images and how many containers?"* One image, three containers.
>
> **Do example 3 even if you are running late.** It is the only place `-p` is
> taught with two *different* numbers. Our agent uses `-p 7000:7000`, where the
> matching numbers hide the rule — so if you skip example 3, they never learn
> that the outside number comes first.

Three worked examples build up before the agent's own Dockerfile is shown.
Each one runs in under a minute and none of them touch the project, so a
mistake costs nothing.

### Ports get a drawn computer

`port` used to be a one-line definition. It is now a drawn machine with four
numbered programs inside it — a website on 443, a database on 5432, **our
agent on 7000** highlighted, a dashboard on 3000 — beside the anchor that
Zoom, Chrome and Spotify are all running on their laptop right now, and the
port number is how a message finds the right one.

### Every section is bridged to the next

The last presenter note in each section contains the sentence that hands over
to the following one, so the day never changes subject without warning:

| Handover | The line to say |
|---|---|
| agent → project | *"All that code lives in a project you are about to download. Before you do, let me show you what is in it."* |
| break → terminal | *"You have a working agent and nobody but you can reach it. The first thing I need to give you is a way to talk to your own computer."* |
| address → speed | *"It works. But how long did that answer take, and what were you looking at while you waited?"* |
| speed → containers | *"Three of the four gaps are closed. The last one: it still only runs on your laptop."* |

> **INSTRUCTOR** · These are in the notes panel, not on the slides. Read the
> handover line *before* you advance, while the previous slide is still up.

### The repository tour, before they clone it

Six slides at 0:38 walk the **real** project on the projector, before anyone
downloads anything. A beginner who clones twenty unfamiliar files spends the
day quietly lost.

1. What a *program* and a *project* are — anchored to Zoom and a trip folder
2. All twelve top-level items, each with one plain-English purpose
3. The six files in `app/`, with the two empty ones marked "you write these"
4. Why the folders are separated — `app/` works, `tests/` is it correct,
   `checks/` am I done, `guide/` and `solutions/` where to get unstuck
5. One branch per week, and that reading the answer key is allowed

Every filename on those slides was checked against the `week-01-package`
branch, so the tour cannot drift from what students actually receive. Note
that the student branch has **no** `evals/`, `loadtest/`, `observability/` or
`deploy/` — those arrive in later weeks, and the slides do not claim them.

> **INSTRUCTOR** · Read the **right-hand column** of the file listing, not the
> filenames. Purposes, top to bottom, ninety seconds. Then say the line that
> settles the room: *"Eleven of those twelve are already done. You will open
> two files all day."*

### One story carries both hard topics

The two ideas a non-technical room finds hardest — *why a web service* and
*why a container* — are taught through **the same running story**, one stage
apart. It arrives before any technical word, and each stage is followed by a
mapping strip with the story on the left and our agent on the right.

**Stage one, at 1:50 — why a web service.**

> You cook very well and your family loves it. Doors closed, kitchen at the
> back. Now you want to sell sweets to the street. What has to change?

Ask it as a question and let them answer. **They will produce most of the list
themselves** — a table at the front, a sign with the address, set opening
hours, serve whoever turns up, take orders one after another. That is a web
service, arrived at with no technical vocabulary.

The line that lands: *"Notice you did not change your recipe. You changed
everything around it. That is exactly what we are about to do to your agent."*

**Stage two, at 3:19 — why a container.**

> The table works, the sweets sell. Now open a second shop across town. You
> post your cousin the recipe — what goes wrong?

Again they answer it: wrong oven, different pans, other flour, and it comes
out tasting different. Then the reveal: *"A container is a fitted-out food
cart. Your code, plus the oven and the pans and the flour, in one thing. She
opens it and it works."*

That stage also carries **image versus container** before either word is
introduced: **one cart design, ten carts.**

| The story | Our agent |
|---|---|
| you cook only when you feel like it | the agent runs only when you start it |
| only people in the house can eat | only code in the same folder can call it |
| no sign, no address | nothing to type in to reach it |
| you go out, nothing is served | you close the terminal, the agent is gone |
| a table, a sign, opening hours | **a web service** |
| the recipe on its own | your code, sent as files |
| the right oven | the right Python version |
| the right pans and ingredients | the right libraries |
| she sets the kitchen up herself | the twelve-minute setup at 0:43 |
| the fitted-out cart | **a container** |
| ten carts from one design | ten containers from one image |

> **INSTRUCTOR** · **Tell it, do not read it.** Take a full minute on each
> stage, and ask before you show — the value is in them producing the list,
> not in seeing it.
>
> Keep the thread alive when you reach the wrong answers: *"send them the
> files"* is posting the recipe to strangers, *"use my laptop"* is inviting
> them into your kitchen. Neither is a shop.
>
> Two stages of one story beat six unrelated comparisons. Do not add more.

### Anchor every new word to their own laptop

Eleven slides carry a blue box tying a technical term to software the learner
already has. This is the single biggest change for a non-technical room.

| Term | The anchor used |
|---|---|
| program | Zoom, Chrome, Excel — somebody wrote instructions, your laptop follows them |
| process | Zoom while it is open; quit it and it is gone, with anything unsaved |
| port | Zoom, Chrome and Spotify all running — the port keeps their messages apart |
| library | a font you installed, or an Excel plug-in — you did not make it, you use it |
| project | a folder for a trip: flight PDF, photo, costs spreadsheet |
| JSON | a spreadsheet row with column headings, written on one line |
| web service | your banking app holds no money — it asks a service and shows the answer |
| container | a phone app: you install one item, it works, nothing to set up |
| branches | report-v1, report-final, report-final-actually — but tracked properly |

> **INSTRUCTOR** · Give the anchor **first**, then the definition. In that
> order it lands; the other way round they are decoding two things at once.

### The eight-week journey map

Two slides carry a picture of the whole course: **what gets wrapped around the
agent each week.** The agent sits in the middle in green and never changes;
each week adds a ring around it. This week's additions are orange, later weeks
are dimmed.

```
   TODAY    [ agent ][ a web address ][ a container ]
   WEEK 2   [ ...above ][ on the internet ][ memory that lasts ]
   WEEK 3   [ everything above ][ a locked door ][ automatic deploy ]
   WEEK 4   [ everything above ][ spending limits ]
   WEEK 5   [ everything above ][ a health dashboard ]
```

It appears early — before the agenda — and again as a compact recap in the
last ten minutes, with the day's two layers ticked.

> **INSTRUCTOR** · Two minutes on this, no more. **They are not meant to
> remember it.** They are meant to see the shape: the thing they built stays
> in the middle, and everything we ever add goes around it.
>
> Say: *"The green box is what you already have. Everything we add goes around
> it, not inside it."* Then point at this week's orange boxes.
>
> Showing the same picture again at 3:50, with two boxes ticked, does more to
> consolidate the day than any summary slide.

### Two rules the deck follows

**Plain English before analogy.** The deck defines each new term in one
sentence, in a highlighted box, and only reaches for a comparison when the
plain version genuinely is not enough. A web service is *"a program that stays
running, waits for questions to arrive over a network, and sends answers
back"* — not a shop, a clerk, or a phone system. Analogies feel helpful to the
person explaining and often add a second thing to learn.

**Simple pictures.** Diagrams are a few labelled boxes with an arrow between
them, not dense line art. Three or four boxes, one arrow, a short caption. If
a picture needs more than that, it is doing too much and gets split across
two slides.

> **INSTRUCTOR** · The three slides at 2:00–2:25 are the ones to protect. They
> define **web service**, **web API** and **endpoint** separately, because
> students conflate all three for months otherwise:
>
> | Term | One line |
> |---|---|
> | web service | the running program |
> | web API | the list of questions it accepts, and what each returns |
> | endpoint | one of those questions |
>
> Say the compressed version once: *"The service is the program. The API is
> what you may ask it. An endpoint is one question."*

### Code for a non-technical room

Six slides pair a code snippet with a **numbered plain-English reading** of
each line beside it — so somebody who has never programmed can follow what the
code *means* without knowing the syntax.

> **INSTRUCTOR** · Read those numbered lines as English sentences, in order.
> The syntax is noise; the sentences are the meaning. Do not explain
> `stop_reason` or `append` as language features — say "did it answer or ask"
> and "add it to the list".
