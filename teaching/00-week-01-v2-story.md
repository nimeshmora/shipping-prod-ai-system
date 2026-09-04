# Week 1, v2 — the story version

`teaching/week-01-slides-v2.html` is **a second, separate deck for the same
four hours.** It covers everything v1 covers. It tells it differently.

**v1 is not touched.** Both decks work; pick one and teach it.

| | v1 | v2 |
|---|---|---|
| slides | 218 | **121** |
| seconds per slide | 60 | **110** |
| shape | twelve named sections | **seven chapters of one story** |
| eyebrows | "Endpoint 2 of 3 · the label" | "Door two: the real one" |
| the map | an agenda table, shown once | **a picture that grows, shown six times** |
| coverage | everything | **the same everything** — 52/52 checklist |

## The spine

One sentence, told in seven chapters:

> *"This morning it only worked on my laptop. By tonight a stranger can run it."*

Every chapter **ends with the same picture, one layer taller**. That picture is
the story's spine, and it means the room is never lost about where they are.

```
   ch 1   [ agent ]                          it thinks, but nobody can reach it
   ch 2   [ agent ]                          now you know what is inside it
   ch 3   [ agent ] on your laptop           it runs for you too
   ch 4   + a computer you can drive          you can type, and reach machines
   ch 5   + a front door                      anything can ask it a question
   ch 6   + a box, and a stranger runs it     the payoff
```

Chapter 2 deliberately shows **no new layer** — knowing what a thing is does
not move it anywhere. Say that out loud; it sets up the next three hours.

## The seven chapters

```
   0:00   12   1  "It works on my laptop"     three questions, laptops closed
   0:12   28   2  "Let me show you the thing"  the agent, then run it
   0:40   27   3  "Your turn"                  prerequisites, clone, key, prove
   1:07   10      break
   1:17   36   4  "Learning to drive"          terminal + curl, on toys
   1:53   10      break
   2:03   47   5  "Giving it a front door"     why, then three endpoints
   2:50   60   6  "Putting it in a box"        containers, then GIVE IT AWAY
   3:50   10   7  "Look what you did"          the picture, complete
   ────────────
   4:00        exactly four hours, both breaks included
```

## What makes it a story rather than a lesson

**Chapters open with prose, not a diagram.** Big type, one idea, no code. The
room gets told where they are going before anything technical appears.

**Narrative slides carry the turns.** A `.tale` slide is one told sentence —
*"So how do you let somebody else use it?"* — where v1 would have used a
heading and three bullets.

**Every technical word arrives as a label for something already done.** They
curl GitHub in chapter 4; "web service" is defined in chapter 5 as *the name
for the thing that answered you*. Nothing is introduced before it is needed.

**Chapter 6 ends by giving the agent away.** Add an endpoint, push it to Docker
Hub, pull a neighbour's, run it with your own key. That is the emotional
payoff the whole day is arranged around — and it is the slide that proves the
`.dockerignore` lesson, because their neighbour's key never left their laptop.

## How it got from 218 slides to 121

Nothing was cut from the *content*. What went:

- **v1's duplicate framings.** The same idea introduced in the concept section
  and again in the build. v2 introduces each once, where it is used.
- **Line-by-line code builds** merged into fewer, bigger reveals with a
  numbered reading beside them.
- **Meta-slides.** Anything explaining what the next slide would do.
- **Tables that were only lists**, redrawn as pictures.

Same rule as v1 held throughout: **at most three blocks, one idea per slide.**
Verified by rendering — all 121 measured in a headless browser at the deck's
1280×720 stage, **none overflow.**

## Presenting it

Identical controls to v1: `→` / `←`, **`S`** for notes, `F` fullscreen, `1`–`7`
for chapters, `G` to jump, `?` for keys.

**Every one of the 121 slides has a presenter note.** They are cues, not
scripts — the sentence to say, the callback to make, the thing not to explain
yet.

> **Before you teach it:** run `python3 -m checks.demo_turn` once. The demo is
> live now, so it needs the network. If OpenRouter is down, `--offline` falls
> back to a scripted stand-in and still shows all four steps.

## Rebuilding it

The deck is generated, so edits go in the builder, not the HTML:

```bash
python3 teaching/build-week-01-v2.py
```

It reuses v1's stylesheet and its whole JS shell, so the two decks stay
visually identical and behave the same way.
