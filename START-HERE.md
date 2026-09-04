# START HERE

Welcome. This repo is a guided build. You take one small AI agent and, over eight
weeks, turn it into something a company could run: online, automatic, locked
down, budgeted, watched, and safe. **You improve the same project the whole way.**

The finished code is already here, so you can run it today and check your work
against it any time. The point is to build it yourself, week by week.

---

## 1. Set up once

```bash
cp .env.example .env        # paste your KodeKey into .env
python -m venv .venv && source .venv/bin/activate
make install
```

## 2. Prove it runs — before you need a key

```bash
make check-setup
```

No API key, no cloud, no internet. You should see `Checkpoint passed.`

## 3. Talk to it

```bash
set -a && source .env && set +a     # load your key into THIS terminal
make run
```

In another terminal:

```bash
curl -s -X POST localhost:7000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"where is my order ORD-1002?"}'
```

You get a reply and a `session_id`. **That is the agent you are going to grow.**

> If you see `OPENROUTER_API_KEY is not set`, you edited `.env` but did not load it. That
> `set -a && source .env && set +a` line has to run in the same terminal as
> `make run`, every time you open a new one. Everybody hits this once.

---

## 4. Follow the weeks

Open the guides in order. Each is short and tells you the goal, the idea, what to
do, and how to check it worked.

```
guide/00-start-here.md   the code you begin with
guide/week-01.md         Package        — it runs anywhere
guide/week-02.md         Deploy         — it survives a restart
guide/week-03.md         Automate+lock  — it ships itself
guide/week-04.md         Cap            — it cannot overspend
guide/week-05.md         See            — you can watch it
guide/week-06.md         Debug          — it survives an outage
guide/week-07.md         Attack         — it survives an attacker
guide/week-08.md         Gate           — bad code cannot ship
guide/09-finish.md       wrap up and capstone
```

Each week has a checkpoint:

```bash
make check-week-01        # ... through check-week-08
```

Most run with no API key and no cloud. They tell you in plain English whether
that week's capability is working. **Green means done.**

---

## 5. Open a pull request each week

Branch `week-01-<your-name>`, title `week 01: package`. From Week 03 onwards a
pipeline checks every pull request automatically before anything can ship.

---

## The three documents

- **This repo** is where you build and run.
- **The easy breakdown** explains each week in plain English. Read it first.
- **The full curriculum** has every exact command and the complete code.

Build here. Understand with the breakdown. Look up details in the curriculum.

---

## If you get stuck

1. Re-run `make check-setup`. It usually names the problem.
2. Check `(.venv)` is at the start of your prompt.
3. Check you are in the repo root — `ls` should show `app/` and `Makefile`.
4. Compare your file against the finished one in `app/`. It is the answer key,
   and every module says which week added which part.
