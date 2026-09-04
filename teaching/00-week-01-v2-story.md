# Week 1 — the story deck

`teaching/week-01-slides-v2.html` — **172 slides, four hours**, told as one
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
   0:00   10   1  "It works on my laptop"      three questions, laptops closed
   0:10   24   2  "Let me show you the thing"  the agent, then run it live
   0:34   20   3  "Your turn"                  prerequisites, clone, key, prove
   0:54   10      break
   1:04   38   4  "Two new skills"             terminal, then the browser -> curl
   1:42   10      break
   1:52   56   5  "Giving it a front door"     why, then three endpoints
   2:48   62   6  "Giving it to somebody else" the problem, Docker, then GIVE IT AWAY
   3:50   10   7  "Look what you did"          the picture, complete
   ────────────
   4:00        exactly four hours, both breaks included
```

About **77 seconds a slide** — one idea, said once, then advance.

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

## Every slide is checked by rendering it, not by measuring it

**A height check is not enough, and two real bugs proved it.**

The prerequisites slide reused a grid from the other deck whose first column is
a **28px checkbox slot**. The names landed in that column, wrapped to two and
three lines each, collided with the commands beside them, and pushed the last
row **under the progress rail**. A `scrollHeight` check saw nothing wrong,
because the overflow was *inside* the slide's own box.

The practice-folder tree had the same shape of fault: `.tree` is a
`white-space: pre` block that expects inline `<span>`s, and it had block
`<div>`s, so every filename became a full-height row and the punchline sat on
top of the rail.

```bash
python3 teaching/check-slide-layout.py teaching/week-01-slides-v2.html
```

It renders **all 172 slides** in a headless browser and reports any slide whose
content reaches the bottom rail, passes either side edge, or exceeds the stage.
Exits non-zero, so it can gate a commit.

> **INSTRUCTOR** · The check is **verified against the bug it was written for** —
> re-inject the old markup and it reports
> `slide 30: hits the bottom rail (gap -36px)`. A checker nobody has seen fail
> is not a checker.

**Both decks pass:** 172/172 here, 218/218 in the other one.

## Chapter six starts with the problem, not with Docker

**The word "Docker" does not appear on screen for the first seven slides**, and
that is the point. It used to arrive on slide two of the chapter, which turns a
real problem into a product pitch.

The chapter now opens on a task they cannot do:

```
   1  a real request        your friend says "that is great, send it to me"
   2  so you send it        THE EMAIL NOBODY WANTS TO RECEIVE - read it aloud
   3  what can go wrong     their Python, the libraries, the folders, their OS
   4  and worse tomorrow    you fix a bug; they still run this morning's copy
   5  so what would fix it? ask it, and let them answer
   6  it is called a container    the name arrives as a RELIEF
   7  and the update problem goes too
```

**Slide 2 is the one that does the work.** It is the message they would have to
send with the folder, written out in full:

> *"Install Python 3.12 — not 3.11, that breaks. Then `pip install` these six
> libraries. Keep the folders exactly as they are. Make a file called `.env`,
> put your own key in it, then run `set -a && source .env && set +a` in the same
> window. Oh, and are you on Windows?"*

> **INSTRUCTOR** · **Read that out loud, in full, in one breath.** It gets a
> laugh, and the laugh is the lesson — *every clause in it is something they
> personally did an hour ago.* Then land it: *"That took you twenty minutes,
> with me in the room, on a laptop you chose. Now send it to a customer."*
>
> **Ask the room how they would send it before you show anything.** They will
> say email the folder, put it on GitHub, zip it up. All reasonable, all wrong,
> and the next four slides do the correcting for you.

**Slide 4 is the one professionals care about.** The first four problems are
annoying; that one is structural — every copy you send is frozen at the moment
you sent it, and you cannot fix it for them. Multiply by twenty people and
nobody knows which version anybody is running.

Only then does the chapter name the thing, explain what Docker is, and go on to
the three toys, the Dockerfile line by line, and the swap.

**The chapter is called "Giving it to somebody else"**, not "Putting it in a
box" — the box is the means, and naming the goal keeps the problem in front.

## Every command is taken apart on screen

**A command is one intimidating string to somebody who has never used a
terminal.** Ten slides now break the important ones into pieces, each with a
plain-English line beside it — and crucially **on the slide**, not only in the
presenter notes, where the room never saw them.

The one that needed it most:

```
   set -a         From now on, share every setting I make with programs I start.
   &&             and then
   source .env    Read that file and set everything listed in it.
   &&             and then
   set +a         Stop sharing. Back to normal.
```

Read the four glosses aloud as one sentence — *"start sharing, read the file,
stop sharing"* — and the line stops being nonsense.

**What gets broken down, and the one thing each slide fixes:**

| Command | The piece people trip on |
|---|---|
| `set -a && source .env && set +a` | all of it — this is the worst offender in the day |
| `git clone` / `cd` / `git checkout` / `make` | **`cd`** — forget it and every later command runs in the wrong place |
| `curl -s <url>` | that a dash-letter is *an option*, a shape they will see all day |
| `curl -o /dev/null -w "%{http_code}"` | the **backslash**, which is not part of the command |
| `curl -X POST -H … -d …` | that `-H` is a label on the outside of the message |
| `docker build -t demo1 .` | **the dot** — it is the folder to look in, not punctuation |
| `docker run --rm -p 9000:80 nginx` | that nginx was **never downloaded deliberately** |
| `make run` + `curl localhost:7000/health` | **`localhost`** means *this very computer* |
| `docker login` / `tag` / `push` / `pull` | **`tag`** does not copy — it adds a second name |
| `code app/main.py` | the slash, a callback to the path idea from chapter four |

The glue — `&&`, the trailing backslash, the pipe — is styled **dimmer than the
real pieces**, so it reads as minor rather than as another thing to learn.

> **INSTRUCTOR** · The pattern is always: **show the command, then take it
> apart on the next slide.** Do not do both on one slide — the point of the
> breakdown is that nothing on it is a mystery, and that only works if it has
> the screen to itself.
>
> Two conventions worth saying once, early: **one dash is a single letter, two
> dashes is a word** (`-s`, `--rm`), and **a trailing backslash just means the
> command carries on next line.** Say those at the first `curl` and you save
> yourself twenty small questions.

## Plain English on screen, always

The words the room reads are **statements of fact**, not gestures at one. A
headline says the thing; it does not hint at it and leave you to explain.

| Never | Always |
|---|---|
| *"You can drive a computer, and reach one."* | *"You can type commands, and ask other computers questions."* |
| *"One thing exists. Nothing can reach it."* | *"Your agent works. Nobody else can use it."* |
| *"Which is the point."* | *"Next week and Weeks 3 and 5 answer these."* |
| *"Six things."* | *"Six things you could not do this morning."* |
| *"In plain English."* | *"What each of those four lines means."* |
| *"The most satisfying thirty seconds of the day."* | *"Watch the answer arrive in pieces."* |

**Metaphors are out unless the plain version is genuinely longer.** Chapter four
was called *"Learning to drive"* — a metaphor a non-native speaker has to
decode before they can start learning. It is now **"Two new skills"**, and the
lede says which two.

The six spine slides now read as one plain sentence each, and together they are
the story of the day:

```
   ch 1   Your agent works. Nobody else can use it.
   ch 2   Now you know what it does. Still only you can use it.
   ch 3   It runs on your laptop now. Only yours.
   ch 4   You can type commands, and ask other computers questions.
   ch 5   Anything can ask it a question now. But only while your laptop is on.
   ch 6   Somebody else ran your agent. That was the whole day.
```

> **INSTRUCTOR** · Read those six aloud in order before you teach, as a check on
> yourself. **If a slide's headline needs you to explain what it means, it is
> the wrong headline** — the explanation belongs in the presenter note, and the
> screen should carry the fact.

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

- **All 172 slides measured** in a headless browser at the deck's own
  1280×720 stage — **none overflow**.
- **Max three blocks per slide**, one idea each.
- **Exactly 220 teaching minutes + two ten-minute breaks = 4:00.** One clock
  label per chapter, checked mechanically.
- **Every slide has a presenter note** — 172 of 172.
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
