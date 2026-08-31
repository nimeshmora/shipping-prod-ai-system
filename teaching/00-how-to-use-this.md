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

Three weeks bend the shape deliberately, and each says so at the top:

- **Week 2** gives Break 25 minutes, because deploying happens inside it.
- **Week 6** leads with a 35-minute bug hunt and puts Break in the middle, where
  the session changes subject.
- **Week 8** ends with a fourth part — porting and Kubernetes — which is
  discussion, not build.

Every week also closes with **If you finish early** and **Homework**. The
early-finish items are genuine extensions, not filler: several of them are the
cheapest way to make the week's point land twice.

## Two rules that make this work

**1. Teach a concept the moment it is needed, never before.**

We do not have a "networking week". We explain what a URL is in Week 1, at the
minute a student needs to type one. We explain what a container is when they
are about to build one. Concepts taught in advance are concepts forgotten in
advance.

**2. Every command gets typed, not pasted.**

Slower, and worth it. Typing `mkdir` twenty times is how it stops being
magic. Paste the long ones (a `gcloud` deploy line is not a typing exercise),
type the short ones.

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
- Each student has a KodeKloud API key in `.env`
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

`teaching/phase-2-teaching-guide.pdf` is all nine files as one 86-page A4
document, with the instructor notes keeping their boxes on paper.

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
