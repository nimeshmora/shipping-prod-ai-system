# Week 1 · Package

**Session goal:** they leave with an agent that has an address, streams its
answer, and runs inside a container.

**Branch:** `week-01-package` → answer key `week-01-solution`

> **INSTRUCTOR** · This week assumes **nothing**. Not the terminal, not JSON,
> not HTTP, not containers. Every new tool gets a **toy example on something
> that is not our agent** before it gets pointed at our agent.
>
> That ordering is the whole method, and it is worth understanding before you
> teach it: a student who runs `curl https://example.com` and sees HTML has
> learned *what curl is* in isolation, with nothing else to be confused about.
> A student whose first curl is a POST with three flags at our `/chat` endpoint
> is learning curl, JSON, HTTP methods, our API and our agent simultaneously,
> and when it fails they cannot tell you which part broke.
>
> **Learn the tool on a toy. Then use the tool on our thing.** Every time.

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

> **INSTRUCTOR** · Four ideas, and they are deliberately arranged as **one
> story rather than four topics**. Each answers a question the previous one
> raises:
>
> ```
> "put it on another computer"   →  which computer? how do I find it?
> "every computer has an address" →  what do I say when I get there?
> "you send a request"            →  what comes back?
> "a reply, with a number on it"  →  ...and then it forgets you.
> ```
>
> Teach them in order and the last one lands as an obvious consequence rather
> than a new fact to memorise. Skip around and you are back to four topics.

### One picture for the whole session

Draw this once, before anything else, and leave it up:

```
        YOUR LAPTOP                    A COMPUTER THAT IS ALWAYS ON
    ┌─────────────────┐                  ┌─────────────────┐
    │                 │   "where is      │                 │
    │   you, typing   │ ── ORD-1002?" ──▶│   your agent    │
    │                 │◀── "Thursday" ───│                 │
    └─────────────────┘                  └─────────────────┘
                          ▲                        ▲
                   this arrow is           this box is
                   Parts 1 and 2           Part 3
                   (an address, and        (a container)
                    a fast-feeling reply)
```

**Everything today is one of those two things.** Every concept below is either
about the arrow or about the box.

> **INSTRUCTOR** · This costs sixty seconds and it is the single highest-value
> minute of the session. Beginners struggle far less with *"what is a URL"* than
> with *"why are we doing any of this"* — and a student who can see where the
> current five minutes fits into the picture asks better questions and panics
> less.
>
> Point at the diagram every time you change topic. *"Still the arrow. Now the
> box."*

---

### 1 · What "deploying" means

Start with the ordinary version of the word, because they already know it.

**Deploying just means putting something where other people can use it.**

A shop that only opens when the owner is standing in it is not really a shop.
A phone that is only on when you are looking at it cannot receive calls.

Right now their agent runs **on their computer, only while they are watching
it.** That is the shop that is only open when the owner is inside.

Deploying means moving it to a computer that:

| | Their laptop | A deployed computer |
|---|---|---|
| Always on? | no — it sleeps, it moves, it closes | **yes** |
| Belongs to them? | yes | **no, and that is the point** |
| Has an address others can reach? | no | **yes** |

That is it. **There is no other magic in the word.** The rest of this course is
about what goes wrong once that is true.

> **INSTRUCTOR** · Beginners assume "deploy" is a technical ritual they have not
> learned yet. Saying plainly that it means *"put it on an always-on computer
> that has an address"* removes a surprising amount of anxiety, and it is
> completely accurate.
>
> If someone asks *"whose computer?"* — a good question — the honest answer is
> *"a company that rents them out by the minute. We use Google's next week.
> Nothing about today changes if you pick a different one."*

---

### 2 · How one computer finds another

They just heard "a computer with an address". So: **what is an address, for a
computer?**

Use the phone system, all the way through. It maps almost perfectly, and
everyone in the room already understands phones.

**Every computer on the internet has a number** — an **IP address**. Like a
phone number for a machine.

```
   a phone number    +94 71 234 5678
   an IP address     172.217.24.206
```

**But nobody remembers numbers.** So we use names, and something looks the name
up for us:

```
   you want to call        you actually need     what does the lookup
   ──────────────────      ─────────────────     ───────────────────────
   "Mum"                   +94 71 234 5678       your phone's contacts
   "google.com"            172.217.24.206        DNS
```

**DNS is the internet's contacts list.** That is genuinely all they need today.

**Let them watch the lookup happen.** This is the toy for this concept:

```bash
ping -c 1 google.com
```

The first line of the output shows the name turning into a number:

```
PING google.com (172.217.24.206): 56 data bytes
```

**They just watched a name become a number.**

Two more worth trying:

```bash
ping -c 1 example.com
ping -c 1 this-name-does-not-exist-xyz.com
```

The first gives a different number — a different building. The second fails, and
says exactly why:

```
ping: cannot resolve this-name-does-not-exist-xyz.com: Unknown host
```

**"Cannot resolve" means the contacts list had no entry.** Not "the computer is
down" — nobody even found out where to knock.

> **INSTRUCTOR** · Everyone's number will be different from the one printed
> above, and different from their neighbour's. That is worth thirty seconds
> rather than confusion: big sites answer from many machines around the world,
> and DNS hands you a nearby one. *"You and the person next to you are talking
> to different computers, and both of you are right."*

> **INSTRUCTOR** · `ping` also tells you how long the round trip took, in
> milliseconds. Worth pointing at, because it makes distance physical: a server
> in the same city answers in single-digit milliseconds, one on another
> continent takes 200+. *"Nothing is instant. It is just fast."*
>
> That number is the seed of Week 5's p95, and mentioning it now costs nothing.

**Now the sentence that matters, and it follows from everything above:**

**When your agent is on the public internet, anyone who knows its address can
send it a request.** Anyone. Not just your users.

The phone analogy carries this too, and it is worth saying out loud: *"A phone
number that only your friends can dial does not exist. If it can receive calls,
it can receive calls from anyone."*

> **INSTRUCTOR** · Say that sentence twice. It is the seed of Week 3 (a stranger
> spending your model budget) and Week 7 (a stranger attacking you). Let it feel
> slightly uncomfortable now — you are going to spend two entire weeks on it.

---

### 3 · What a URL is

They now have a name that finds a computer. But a computer does many things, so
the address needs one more part.

**Think of a big office building.**

```
   https://shop.example.com/chat
   ─────   ────────────────  ────
     │            │            │
   how you     which        which
   get in     building      room
```

- **`shop.example.com`** — **which building.** The name DNS just looked up.
- **`/chat`** — **which room inside it.** One building has many rooms. One
  computer has many of these, and they do different jobs.
- **`https`** — **how you get in.** The `s` means the conversation is
  scrambled on the way, so nobody in the corridor can listen.

Ours will have four rooms by the end of the course:

| Room | What happens in it | Built in |
|---|---|---|
| `/chat` | ask the agent a question | today |
| `/chat/stream` | the same, but the answer arrives as it is written | today |
| `/health` | "are you alive?" | today |
| `/metrics` | "how are you doing, in detail?" | Week 5 |

> **INSTRUCTOR** · Two things beginners quietly wonder and rarely ask:
>
> **"Is a URL the same as a website?"** No — a website is one kind of thing you
> can find at a URL. They already proved this in Part 0c, where `example.com`
> gave them a page and GitHub's API gave them a sentence. Same kind of address,
> different kind of thing at the end of it.
>
> **"Why does it start with https and not www?"** `www` is just a name someone
> chose, the way a building might be called "North Wing". `https` is the part
> that matters, and it is not part of the name at all.

---

### 4 · What an HTTP request is

They can now find the room. **What do they say when they get there?**

**A question and an answer. That is all.**

It is a counter at an office, not a conversation:

```
   you        "I would like to collect order ORD-1002."        ← the request
   clerk      "Here it is. Arriving Thursday."                 ← the reply
              ...and the clerk immediately forgets you exist.
```

Every **request** has three parts worth knowing:

| Part | What it means | In plain words | Ours |
|---|---|---|---|
| a **method** | what kind of thing you want | am I *collecting* or *handing in*? | `GET` = read, `POST` = send |
| a **path** | which room | which counter am I at? | `/chat` |
| a **body** | what you are handing over | the form you filled in | `{"message": "where is my order?"}` |

Every **reply** has two:

| Part | What it means |
|---|---|
| a **status code** | a number saying how it went |
| a **body** | the actual answer |

**They have already seen every one of these.** In Part 0c: `-X POST` was the
method, `/post` was the path, `-d '{...}'` was the body, and `200` came back as
the status code. Say so — this table is a name for something they have done, not
a new thing to learn.

#### The status codes, as a receptionist would say them

```
200   "here you go"                        fine
400   "you filled the form in wrong"       YOUR mistake
401   "who are you?"                       (Week 3)
429   "you have asked me eleven times,     (Week 3)
       please wait"
500   "something broke on our side,        OUR mistake
       sorry"
```

> **INSTRUCTOR** · The 400-vs-500 distinction matters far more than it looks,
> and the receptionist framing is what makes it stick: **400 is "your form is
> wrong", 500 is "our filing cabinet fell over".**
>
> Week 5 alerts on the error rate. If you return 500 when the caller sent
> nonsense, your dashboard blames you for their mistake, and you will spend a
> morning investigating an outage that never happened. Mention it now; land it
> in Week 5.

#### The consequence that shapes everything else

Go back to the clerk who forgets you.

**The computer forgets you completely after every request.** It keeps nothing.
The next request from the same person looks, to it, exactly like a request from
a stranger.

So ask the room: *"Then how does a conversation work at all?"*

Let them think. Someone usually gets it, and the answer is the same one a real
office uses:

```
   you    "where is my order?"
   them   "Here's your answer — and here's ticket #47."
   you    "Ticket #47. When does it arrive?"
   them   (looks up #47, sees the whole conversation so far)
```

**You get given a ticket, and you bring it back.** That ticket is called a
**session ID**, and building it is Part 1 of the build.

> **INSTRUCTOR** · This is the moment to *not* explain further. They now have a
> question — *"so where does the ticket's information get stored?"* — and the
> answer is the thing they are about to build, then the thing that breaks in
> Week 2.
>
> If someone asks it out loud: *"Brilliant question. Hold it for twenty minutes,
> then hold it for a week."*

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

### Part 0a · Two words you will hear all course (3 min)

Two ideas that everything else sits on. Thirty seconds each, with something to
run.

**A process is a running program.**

A program is a file sitting on disk, doing nothing. A **process** is that file
actually running, right now, in memory. Same program started twice = two
processes.

```bash
sleep 30
```

That is a process. It is running. Your terminal is stuck because it is waiting
for it. Press **Ctrl + C** to kill it.

**You just killed a process.** That is what happens to their agent when they
close the terminal, and it is why the memory disappears in Week 2.

**A port is a numbered door on a computer.**

One computer, many doors. A web server sits behind door `80`, or `443`, or in
our case `8080`. A URL's `:8080` says which door to knock on.

```
   localhost:8080
   ─────────  ────
       │        │
    which     which
   computer    door
```

`localhost` is a special name meaning **this computer, the one I am typing on**.

> **INSTRUCTOR** · That is enough. Do not explain port ranges, TCP, or why 443.
> They need "numbered door" and "localhost means here", and they need it in
> thirty seconds. The rest is Week 2's problem and mostly never.

### Part 0b · JSON, before we send any (5 min)

They are about to send and receive JSON all course. Five minutes now saves
confusion in all eight weeks.

**JSON is a way to write data as text**, so it can travel over a network. That
is its entire purpose: a network can only carry text, so we agree on a way to
write data down.

```json
{"name": "Ada", "age": 36}
```

- `{ }` wraps a set of facts about one thing
- `"name"` is a **label**, always in double quotes
- `:` separates the label from its value
- `,` separates one fact from the next

Values can be text (in quotes), numbers (no quotes), true/false, or another
`{ }` nested inside.

**Run it.** This command reads JSON and prints it back tidily:

```bash
echo '{"name":"Ada","age":36}' | python -m json.tool
```

```json
{
    "name": "Ada",
    "age": 36
}
```

> **INSTRUCTOR** · Explain the `|` once, because it appears all course: *"The
> pipe takes what the left side printed and feeds it to the right side as
> input."* That is enough. Do not explain stdin.

**Now break it on purpose.** Use single quotes around the label — which is legal
in Python and illegal in JSON:

```bash
echo "{'name':'Ada'}" | python -m json.tool
```

```
Expecting property name enclosed in double quotes: line 1 column 2
```

**The error tells you the rule.** JSON labels need double quotes, always.

> **INSTRUCTOR** · This tiny failure is worth the thirty seconds. It is the
> single most common JSON mistake, they have now made it deliberately, and the
> error message that will confuse them in week four is one they have already
> seen and understood.
>
> If anyone knows Python: *"It looks exactly like a dict. The differences that
> bite are double quotes only, and no trailing comma."*

### Part 0c · curl, on things that are not ours (7 min)

**`curl` sends an HTTP request from the terminal.** It is a browser with no
window — it fetches, and prints what came back.

They will use it in every session from here. So learn it on something simple
first, where nothing else can be the problem.

**One — fetch a web page.**

```bash
curl -s https://example.com
```

A pile of HTML comes back. That is what a web page *is* underneath: text your
browser draws. `-s` means "silent" — without it curl prints a progress bar that
gets in the way.

**They have just done what a browser does.**

**Two — call an API.**

```bash
curl -s https://api.github.com/zen
```

One sentence comes back. No HTML, no page — just an answer.

> **INSTRUCTOR** · Name the difference, because it is the difference between a
> website and an API and most people have never had it stated: *"The first one
> sent something for a human to look at. This one sent something for a program
> to use. Same protocol, same tool, different audience. That is all an API is."*

**Three — see the reply's status code and headers.**

```bash
curl -s -i https://api.github.com/zen
```

`-i` includes the reply's **headers** — everything before the blank line.

```
HTTP/2 200
date: Mon, 31 Aug 2026 05:04:25 GMT
content-type: text/plain;charset=utf-8

Keep it logically awesome.
```

There is the **200** from the concept section, in real life. And `content-type`,
which is how the receiver knows what kind of thing it just got.

**Headers are extra facts about the request or reply, that are not the body
itself.** That is the whole idea.

**Four — see other status codes.**

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://httpbin.org/status/404
```

```
404
```

Two new flags, both worth knowing because they recur all course:

- `-o /dev/null` — throw the body away, we do not care about it
- `-w "%{http_code}\n"` — print *just* the status code

Try `200` and `500` in place of `404`. Same command, different numbers.

> **INSTRUCTOR** · Have them run all three. Seeing 200, 404 and 500 come back
> from the same command is what turns status codes from a table on a slide into
> something real. They use `-w "%{http_code}"` heavily in Week 3.

**Five — send something (POST).**

Everything so far was `GET` — *"give me something"*. Now `POST` — *"here, take
this"*.

```bash
curl -s -X POST https://httpbin.org/post \
  -H 'Content-Type: application/json' \
  -d '{"message":"hello"}'
```

Read the command aloud, flag by flag:

- `-X POST` — the **method**. We are *sending*, not just reading.
- `-H 'Content-Type: application/json'` — a **header**, telling the server "the
  body I am sending is JSON".
- `-d '{...}'` — the **body**. The actual thing being sent.

That URL is a free echo service: it replies with a description of whatever you
sent it. In the reply, find this part:

```json
  "json": {
    "message": "hello"
  },
```

**The server received your JSON, understood it, and read the `message` field
out.** That is exactly what our `/chat` endpoint will do in twenty minutes — the
same method, the same header, the same body shape.

> **INSTRUCTOR** · This is the highest-value five minutes in the session. When
> they later type a three-flag POST at our agent and it fails, they can tell
> the difference between *"my JSON is malformed"*, *"my flags are wrong"* and
> *"our service is broken"* — because they have seen all three flags work
> against something that definitely was not broken.
>
> If the room has no internet, `python -m http.server 9000` in one terminal and
> `curl -s localhost:9000` in another covers points one to four.

### Part 0d · Getting the project (5 min)

```bash
git clone https://github.com/nimeshmora/shipping-prod-ai-system.git
cd shipping-prod-ai-system
git checkout week-01-package
```

**Git is a time machine for a folder of code.** It remembers every version, and
lets you move between them.

- **`git clone`** downloads a copy of the project, with all of its history.
- **`git checkout`** switches to a particular version — in our case, this week's
  starting point.

```bash
make install
make test
```

**`make` runs a shortcut that somebody already wrote down.** The shortcuts live
in a file called `Makefile` in the project. `make install` is a nickname for a
longer command; so is `make test`.

```bash
cat Makefile
```

Have them look. **There is no magic in `make`** — it is a list of nicknames, and
they can read every one.

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

This one **does not finish**. It sits there — because it is a server, and a
server's job is to stay running and wait. Same as the `sleep 30` from Part 0a.

**So they need a second terminal.** Open a new window (`Cmd + N` on Mac,
`Ctrl + Shift + N` on Windows/Linux) and `cd` back into the project.

> **INSTRUCTOR** · Say explicitly: *"One terminal runs the server. The other one
> talks to it. That is the arrangement for the rest of the course."* Several
> people will otherwise Ctrl-C the server to get their prompt back and then
> wonder why nothing answers.

In the **second** terminal:

```bash
curl -s http://localhost:8080/health
```

You should get `{"status":"ok"}`.

**Exactly the same command shape as `curl -s https://example.com`** — just
pointed at their own machine, on door 8080, instead of out at the internet.

Now the real thing:

```bash
curl -s -X POST http://localhost:8080/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"where is my order ORD-1002?"}'
```

**That is the same five-flag command they ran against httpbin**, with our
address and our message. Point that out — it is why Part 0c existed.

Copy the `session_id` from the reply and continue the conversation:

```bash
curl -s -X POST http://localhost:8080/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"and when will it arrive?","session_id":"PASTE_IT_HERE"}'
```

**It remembers.** That is the session ID doing its job.

> **INSTRUCTOR** · The error you will see most this week — every week, in fact —
> is `KODEKEY is not set`.
>
> **What an environment variable is**, since this is the moment they need it: a
> setting that lives *outside* your code, attached to the terminal session, that
> a program can read when it starts. It is how you give a program a secret
> without typing the secret into a file that gets shared.
>
> ```bash
> export GREETING=hello
> python -c "import os; print(os.environ.get('GREETING'))"     # hello
> python -c "import os; print(os.environ.get('NOPE'))"         # None
> ```
>
> Thirty seconds, and `KODEKEY is not set` stops being mysterious — it means
> exactly what that second line printed.
>
> The fix, in the *same* terminal as `make run`:
>
> ```bash
> set -a && source .env && set +a
> ```
>
> That reads their `.env` file and exports every line in it. Write it on the
> board. Leave it there for eight weeks.

### Part 2 · Make it feel fast (10 min)

Ask: *"How long did that take?"*

Several seconds. And for all of it, they stared at nothing.

**Eight seconds of nothing feels broken. Eight seconds with words appearing
after 400 milliseconds feels fast.** Same duration. Completely different
product. This is why every AI assistant they have used streams.

**See streaming before building it.** Run this — it sends three lines, one per
second:

```bash
curl -N -s https://httpbin.org/stream/3
```

The lines **appear one at a time**, over three seconds. Nothing waited for the
whole thing to be ready.

Now compare, without `-N`:

```bash
curl -s https://httpbin.org/stream/3
```

Same three lines, same three seconds — but they all appear **at the end, in one
lump**. Identical data, and it feels twice as slow.

> **INSTRUCTOR** · Run both on the projector, in that order. The second one is
> the more important demo, because it is exactly the bug they will report to you
> in twenty minutes: *"streaming isn't working"*, when in fact curl was
> buffering. **`-N` means "do not buffer, show me pieces as they arrive."**

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
point, silently, because the answer is still correct. **They just watched
exactly this happen** with curl and no `-N`. The header `X-Accel-Buffering: no`
is how you tell a proxy not to do it.

Watch it work:

```bash
curl -N -X POST http://localhost:8080/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"message":"where is my order ORD-1002?"}'
```

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

#### First, build a box with nothing in it (5 min)

Before containerising our agent — with its libraries, its port, its key — build
the smallest possible box. Two files, in a fresh folder.

```bash
mkdir ~/box && cd ~/box
```

One file of "code":

```bash
echo 'print("hello from inside the box")' > hello.py
```

And the instructions for building the box. Create `Dockerfile` (no extension —
that exact name):

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY hello.py .
CMD ["python", "hello.py"]
```

Four lines, read one at a time:

- **`FROM python:3.12-slim`** — start from a box that already has Python 3.12
  in it. Somebody else built that; we build on top.
- **`WORKDIR /app`** — work in a folder called `/app` *inside the box*.
- **`COPY hello.py .`** — copy our file from *our computer* into *the box*.
- **`CMD [...]`** — what to run when the box starts.

Build it and run it:

```bash
docker build -t hello-box .
docker run --rm hello-box
```

```
hello from inside the box
```

> **INSTRUCTOR** · Unpack that output, because the significance is easy to miss:
> *"That `print` ran on a Linux machine with a Python you did not install, in a
> folder that does not exist on your laptop. And it will print exactly that on
> anyone else's computer too."*
>
> Explain the two commands once:
> - **`build`** = make the box. `-t hello-box` names it. The `.` means "the
>   Dockerfile is in this folder".
> - **`run`** = start the box. `--rm` = throw it away when it exits.
>
> **Now prove the box is sealed.** Delete the file and run it again:
>
> ```bash
> rm hello.py
> docker run --rm hello-box
> ```
>
> It still prints. **The code was copied *into* the box at build time.** That
> single moment explains containers better than any diagram — the box is not
> pointing at their folder, it *contains* a copy.

#### Now the real one

Their `Dockerfile` is the same four ideas plus three lines:

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

New words: **`RUN`** does something while *building* the box (installing
libraries), where `CMD` runs when the box *starts*. **`ENV`** sets an environment
variable — the same thing they met with `KODEKEY`. **`EXPOSE`** documents which
door the thing inside listens on.

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

**A list of things NOT to copy into the box.** Without it, `COPY . .` copies
everything in the folder.

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

In a variable, inside the running program — **inside the process** they met in
Part 0a.

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
- Point `curl` at a URL that does not exist — `curl -s -i http://localhost:8080/nope`
  — and read the 404 together. They built that without writing it.
- Have them add a second file to the `~/box` toy, rebuild, and watch only the
  changed step re-run. That is the caching lesson, felt rather than described.

## Homework

- `make check-week-01` green, committed and pushed
- Read `guide/week-01.md` in the repo — the same material, written for reference
- Install Docker Desktop if they have not, and check `make docker-build` works
  **before** next session

> **INSTRUCTOR** · Chase the Docker install. Week 2 deploys a container, and one
> student without Docker becomes twenty minutes of everyone else waiting.
