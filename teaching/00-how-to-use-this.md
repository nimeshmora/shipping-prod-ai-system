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

`teaching/week-01-slides.html` is an 83-slide presenter deck for **day one, run
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

**Press `S` before you start.** Seventy-two of the slides carry a presenter
cue — the callback to make, the question to ask, the thing *not* to explain
yet — in a side panel the room never sees.

### The four-hour shape

```
   0:00   22   Three questions to the room   settle the room, and read it
   0:22   20   Meet today's agent            our small teaching agent
   0:42   13   Get set up, and prove it      the checklist, and check-week-00
   0:55   10   break
   1:05   20   The terminal                  practised on a throwaway folder
   1:25   27   Sending messages              JSON and curl, on public services
   1:52   10   break
   2:02   25   What a web service is         service, API, endpoint
   2:27   25   Addresses, then messages
   2:52   28   Build: the address
   3:20   12   Build: make it feel fast
   3:32   18   Build: the container
   3:50   10   Prove it, and what breaks next
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
