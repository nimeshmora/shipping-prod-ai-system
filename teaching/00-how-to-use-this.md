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

Every session follows the same five beats. Students learn the rhythm by week
three and stop needing to be told what is happening.

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
| JSON | `echo '{"name":"Ada"}' \| python -m json.tool`, then break it |
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
| a port, `localhost` | seen the `:8080` shape |
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

`teaching/week-01-slides.html` is a 123-slide presenter deck for **day one, run
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

**Press `S` before you start.** A hundred and twelve of the slides carry a
presenter cue — the callback to make, the question to ask, the thing *not* to explain
yet — in a side panel the room never sees.

### The four-hour shape

```
   0:00   16   Three questions to the room   settle the room, and read it
   0:16   16   Meet today's agent            our small teaching agent
   0:32   11   The project                   a tour BEFORE they download it
   0:43   14   Set it up, and prove it       incl. the key, FINISHED here
   0:57   10   break
   1:07   15   The terminal                  practised on a throwaway folder
   1:22   20   Sending messages              JSON and curl, on public services
   1:42   10   break
   1:52   22   What a web service is         the shop story, then the words
   2:14   16   Addresses, then messages
   2:30   42   Build the web service         3 endpoints, line by line, each tested
   3:12   32   Build the container           the cart story, then line by line
   3:44   16   Prove it, and what breaks next
   ────────────
   4:00        exactly four hours, including both breaks
```

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

`KODEKEY is not set` used to appear mid-afternoon, which was confusing — a new
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
**write it in front of the room, one line at a time** — 19 slides for the web
service, 5 for the agent's Dockerfile.

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

### Containers get 32 minutes, and are taught from nothing

This is the longest section of the day, and deliberately so — it is the topic
a non-technical room finds hardest, and the one most courses rush. Fourteen
slides, in this order:

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
> taught with two *different* numbers. Our agent uses `-p 8080:8080`, where the
> matching numbers hide the rule — so if you skip example 3, they never learn
> that the outside number comes first.

Three worked examples build up before the agent's own Dockerfile is shown.
Each one runs in under a minute and none of them touch the project, so a
mistake costs nothing.

### Ports get a drawn computer

`port` used to be a one-line definition. It is now a drawn machine with four
numbered programs inside it — a website on 443, a database on 5432, **our
agent on 8080** highlighted, a dashboard on 3000 — beside the anchor that
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
   WEEK 2   [ agent ][ address ][ container ][ on the internet ][ memory that lasts ]
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
