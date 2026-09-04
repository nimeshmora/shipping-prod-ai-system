# Week 1 — the story deck

`teaching/week-01-slides-v2.html` — **158 slides, four hours**, told as one
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
   0:40   18   3  "Your turn"                  prerequisites, clone, key, prove
   0:58   10      break
   1:08   38   4  "Learning to drive"          terminal, then the browser -> curl
   1:46   10      break
   1:56   56   5  "Giving it a front door"     why, then three endpoints
   2:52   58   6  "Putting it in a box"        containers, then GIVE IT AWAY
   3:50   10   7  "Look what you did"          the picture, complete
   ────────────
   4:00        exactly four hours, both breaks included
```

About **84 seconds a slide** — one idea, said once, then advance.

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

## Everybody's agent has a different name

The sharing activity is **six numbered steps**, and the first four exist so that
no two containers in the room are the same:

| Step | What they do |
|---|---|
| 1 | **Pick a name.** "Desk Detective", "Order Bot 3000" — anything |
| 2 | **Put it in `.env`** — one line, `AGENT_NAME=...`. No code yet |
| 3 | **Read it in code** — `os.environ.get("AGENT_NAME", "Support Agent")` and a `/whoami` door |
| 4 | **Try it** — restart, curl `/whoami`, see your own name come back |
| 5 | **Push it** to Docker Hub |
| 6 | **Pull a neighbour's and run it** — and *their* name appears |

**Step 6 is the payoff, and the name is the proof.** The name on screen is not
the one they chose. It came from somebody else's image, running on their
machine, with their own key.

> **INSTRUCTOR** · Ask two people to read out the name they got. That is the
> moment the day lands — and it beats any explanation of why containers matter.

**Why a name and not an extra endpoint:** a name is a *setting*, so it teaches
the thing that makes the swap work — **code travels in the image, settings are
handed in at run time.** That is the same idea as the key, proven twice.

**Verified against a real clone** of `week-01-solution`: with no `AGENT_NAME`
set it returns `{"agent": "Support Agent", "orders": [...]}`; with
`AGENT_NAME="Nimesha's Order Helper"` it returns that name. `all_ids()` exists
in `app/orders.py`. `AGENT_NAME` is now in `.env.example` on all sixteen week
branches.

**The three toys** in chapter six (`alpine` → your own file → `nginx` with
`-p 9000:80`) each build and run standalone, before anything of theirs is at
stake.

## JSON and curl start in the browser

**The old order taught JSON as a format, then curl as a tool.** Both were new
words arriving before there was anything to attach them to. The new order
starts with the one thing every person in the room already does daily.

```
   1  you already do this      type an address, a computer sends back a page
   2  now type THIS address    api.github.com/users/torvalds   <- in the browser
   3  what came back           name, company, location, followers - all readable
   4  that shape has a name    JSON  <- named AFTER they have read one
   5  try a wrong address      "Not Found", and a number: 404
   6  so why not the browser?  your CODE cannot read a browser window
   7  the same thing, a command   curl, same address, same answer
   8  pick out one bit         | jq -r '.name'  ->  Linus Torvalds
   9  ask for the number       200, then 404 - what the browser hid
  10  what the numbers mean    200 / 4xx you asked wrong / 5xx it broke
  11  and you can SEND too     -X POST, which a browser cannot do
```

**Why this order works.** Slide 3 is the moment that matters: they look at raw
JSON in their own browser and realise **they can already read it.** Name,
company, location. Nobody explains it to them. The word "JSON" then lands on
slide 4 as a label for something familiar rather than a new concept.

And **curl is introduced as a need, not a tool.** Slide 6 asks *"so why not
just use the browser?"* and answers it: your code cannot read a browser window,
you cannot send anything, and you cannot see the number. **Only then** does a
command appear — as the same thing they just did, in a form a program can use.

> **INSTRUCTOR** · Have everybody type the address at the same time and wait
> for the room. Somebody will say *"it looks broken"* — that is the reaction
> you want, because thirty seconds later they are reading it fluently.
>
> **Have them try their own GitHub username.** Suddenly it is their own data,
> which is worth the noise.

**Every command on these slides was run.** `users/torvalds` returns 200;
a nonsense username returns 404 **with `"status": "404"` in readable JSON**;
`jq -r '.name'` returns `Linus Torvalds`; and the `httpbin.org/post` example
echoes back `{"message": "hello"}`.

**One correction worth knowing:** an earlier version of the jq slide claimed
that without `| jq` you get "one long unreadable line". **GitHub already
pretty-prints**, so students would have seen that was false the moment they
ran it. The slide now teaches what jq is actually for — **pulling out one
field by the label they just read on screen** — which is both true and more
useful.

## The teaching added where rooms get stuck

**Docker** — five slides before any Dockerfile is written, because "write a
Dockerfile" means nothing until these are true:

| Slide | The one thing it teaches |
|---|---|
| So what do you actually write? | it is a text file, one instruction per line — and the naming trap |
| The six words you will use | `FROM WORKDIR COPY RUN ENV CMD`, and **`RUN` builds, `CMD` starts** |
| Why images are built in layers | stacked like tracing paper — which explains caching *and* fast pulls |
| What happens when you run one | `docker run` takes a **copy**; `--rm` throws it away |
| Inside the box is a different computer | its own folders, its own `localhost` — the single biggest confusion |

That last one is why `COPY` has to exist and why `--host 0.0.0.0` is needed.
**Teach it before the Dockerfile, not after.**

**Web service** — four slides for the same reason:

| Slide | The one thing it teaches |
|---|---|
| What actually travels | a question out, an answer back. **Both are just text** |
| The question has three parts | method, path, body — GET fetches, POST sends |
| What "always running" costs you | somebody's computer is on at 3am, and somebody pays |
| One address, many numbered doors | what a **port** is, drawn on a computer |

The port slide matters most for a non-technical room: **7000 appears in `.env`,
in the Dockerfile, and in `-p 7000:7000`** — same number, three places, and it
is meaningless until they have seen this picture.

## Coverage

**89 of 89** on the Week 1 checklist: the agent and its tools, the loop, the
demo, why there is no memory, prerequisites, the repo tour, clone and branch,
`.env` and `set -a`, both checkpoints, nine terminal commands, `ls -la` and
hidden files, paths, JSON, curl, jq, status codes, web service vocabulary, the
seven-layer zoom, all three endpoints, session ids, error hiding, logs, image
vs container, all seven Dockerfile instructions, the build process and caching,
ports, `.dockerignore`, `--env-file`, Docker Hub push and pull, the swap, the
recap, homework, and the Week 2 hook.

## The deck refers to itself by chapter, never by clock

**Every callback names a chapter**, not a time and not "the break":

| Never | Always |
|---|---|
| *"before the break"* | *"in chapter four"* |
| *"you saw this at 0:20"* | *"you saw this in chapter two"* |
| *"after the break you build..."* | *"next chapter you build..."* |

Two reasons this matters. **There are two breaks**, so "the break" is ambiguous
the moment you say it twice. And **clock times drift** every time a slide is
added or the pacing is rebalanced, which turns a helpful callback into a wrong
one that the room notices before you do.

Chapter names cannot drift. If you add slides, the callbacks stay true.

> **INSTRUCTOR** · The same rule applies out loud. Say *"remember chapter four,
> when you asked GitHub a question"* rather than *"remember before lunch"* —
> the room tracks the story, not the timetable.

## Verified, not assumed

- **All 158 slides measured** in a headless browser at the deck's own
  1280×720 stage — **none overflow**.
- **Max three blocks per slide**, one idea each.
- **Exactly 220 teaching minutes + two ten-minute breaks = 4:00.** One clock
  label per chapter, checked mechanically.
- **Every slide has a presenter note** — 158 of 158.
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
