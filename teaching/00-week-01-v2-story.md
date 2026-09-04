# Week 1 — the story deck

`teaching/week-01-slides-v2.html` — **140 slides, four hours**, told as one
continuous story. Written for a room that includes people who have never
opened a terminal.

## The spine

One sentence, and the whole day serves it:

> *"This morning it only worked on my laptop. By tonight a stranger can run it."*

Seven chapters. **Each one ends with the same picture, one layer taller.** That
picture is why nobody gets lost — the room can always see how far in they are
and what is still dashed.

```
   ch 1   [ agent ]                          it thinks, nobody can reach it
   ch 2   [ agent ]                          now you know what is inside
   ch 3   [ agent ] on your laptop           it runs for you too
   ch 4   + a computer you can drive         you can type, and reach machines
   ch 5   + a front door                     anything can ask it a question
   ch 6   + a box, and a stranger runs it    the payoff
```

**Chapter 2 deliberately adds no layer.** Knowing what a thing is does not move
it anywhere. Say that out loud — it is what makes the next three hours feel
necessary rather than arbitrary.

## The seven chapters

```
   0:00   12   1  "It works on my laptop"      three questions, laptops closed
   0:12   28   2  "Let me show you the thing"  the agent, then run it live
   0:40   22   3  "Your turn"                  prerequisites, clone, key, prove
   1:02   10      break
   1:12   36   4  "Learning to drive"          terminal + curl, on toys
   1:48   10      break
   1:58   52   5  "Giving it a front door"     why, then three endpoints
   2:50   60   6  "Putting it in a box"        containers, then GIVE IT AWAY
   3:50   10   7  "Look what you did"          the picture, complete
   ────────────
   4:00        exactly four hours, both breaks included
```

About **95 seconds a slide** — one idea, said once, then advance.

## How the story is told

**Chapters open with prose.** Big type, one idea, no code. The room is told
where it is going before anything technical appears.

**Narrative slides carry the turns.** *"So how do you let somebody else use
it?"* on its own slide, and you take answers before showing any.

**Every technical word arrives as a label for something already done.** They
curl GitHub in chapter 4; "web service" is defined in chapter 5 as *the name
for the thing that answered you.* Nothing is named before it is needed.

## Follow one question — the seven-layer zoom

Chapter 5 has the sequence that matters most for the non-technical half of the
room. **One question, traced from outside the computer all the way to the
agent, adding exactly one layer per slide** and keeping the earlier ones on
screen:

```
   1  outside        somebody has your address and a question
   2  one computer   the message arrives at the machine
   3  a port         which of the running programs is it for?  (7000)
   4  a program      uvicorn was waiting there
   5  a library      FastAPI reads /chat and finds whose function handles it
   6  your code      YOUR FOUR LINES - the only layer they write
   7  the agent      run_turn(), and the answer travels back out
```

> **INSTRUCTOR** · Ninety seconds a slide, and **do not skip ahead** — the value
> is entirely in the layers accumulating. Point at ring 6 and say *"this is the
> only one you write."* Beginners are never told which part is theirs, and it
> is the single most orienting fact in the day.

## The Dockerfile is written line by line

Eight slides, **one instruction each**, matching the solution file exactly:

| Line | What the slide teaches |
|---|---|
| `FROM python:3.12-slim` | start from a computer that already has Python; why *slim* |
| `WORKDIR /app` | a folder **inside the image** — every later path is inside the box |
| `COPY requirements.txt .` | the shopping list **only**, and why just one file |
| `RUN pip install --no-cache-dir` | the slow step, and why the cache is dead weight in an image |
| `COPY . .` | **now** the code — and the line `.dockerignore` protects you from |
| `ENV PORT=7000` | a setting with a default, and why next week's platform needs it |
| `EXPOSE 7000` | honest: this documents, it does not open. `-p` opens |
| `CMD exec uvicorn ...` | three details: `--host 0.0.0.0`, `${PORT}`, and why `exec` |

**And what happens when you press build.** Two slides show the real output —
one line per instruction — then run the same build again so `CACHED` appears
and the time drops from 2.1s to 0.1s. **Run it twice live; it is the fastest
way to teach layer caching**, and it sets up why line order matters.

## The web service is written line by line too

Imports → `app` object → `/health` → test it → `ChatRequest` → `/chat` →
error handling → test it → `/chat/stream` → test it → **the whole file
assembled.** That last slide matters: they have only ever seen fragments, and
seeing twenty finished lines with three labels in it is what makes "I could add
a fourth door" feel true — which is exactly what they do in chapter 6.

Every code slide matches `week-01-solution` exactly, including
`uuid.uuid4().hex` and the two-branch `except`.

## The extra tasks are real, and they were run

- **`/orders`** uses `all_ids()` from `app/orders.py` — a function that exists.
  Verified against `week-01-solution`: returns
  `{"order_ids": ["ORD-1001","ORD-1002","ORD-1043","ORD-1077"]}` with a 200.
- **The three toys** in chapter 6 (`alpine` → your own file → `nginx` with
  `-p 9000:80`) each build and run on their own, before anything of theirs is
  at stake.
- **The swap** at the end: add `/orders`, push to Docker Hub, pull a
  neighbour's, run it with **your** key. That last part proves the
  `.dockerignore` lesson — their neighbour's key never left their laptop.

## Coverage

**89 of 89** on the Week 1 checklist: the agent and its tools, the loop, the
demo, why there is no memory, prerequisites, the repo tour, clone and branch,
`.env` and `set -a`, both checkpoints, nine terminal commands, `ls -la` and
hidden files, paths, JSON, curl, jq, status codes, web service vocabulary, the
seven-layer zoom, all three endpoints, session ids, error hiding, logs, image
vs container, all seven Dockerfile instructions, the build process and caching,
ports, `.dockerignore`, `--env-file`, Docker Hub push and pull, the swap, the
recap, homework, and the Week 2 hook.

## Verified, not assumed

- **All 140 slides measured** in a headless browser at the deck's own
  1280×720 stage — **none overflow**.
- **Max three blocks per slide**, one idea each.
- **Exactly 220 teaching minutes + two ten-minute breaks = 4:00.** One clock
  label per chapter, checked mechanically.
- **Every slide has a presenter note** — 140 of 140.
- Code checked against `week-01-solution`; `/orders` executed against a real
  clone.

## Presenting it

`→` / `←` to move · **`S`** for notes · `F` fullscreen · `1`–`7` for chapters ·
`G` to jump · `?` for keys.

The notes are **cues, not scripts** — the sentence to say, the callback to
make, the thing not to explain yet. Do not read them aloud.

> **Before you teach:** run `python3 -m checks.demo_turn` once. It uses the
> real model now, so it needs the network. If OpenRouter is down,
> `--offline` falls back to a scripted stand-in and still shows all four steps.

> **Docker warning:** chapter 6 needs Docker Desktop *running*, not just
> installed. Check `docker --version` at the start of the chapter — it catches
> anyone who restarted their laptop over lunch.

## Rebuilding

The deck is generated, so edits go in the builder:

```bash
python3 teaching/build-week-01-v2.py
```

Parts live in `teaching/v2-parts/`. It reuses the same stylesheet and JS shell
as the other Week 1 deck, so both look and behave identically.
