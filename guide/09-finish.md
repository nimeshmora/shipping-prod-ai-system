# Finish · What you actually built

Eight weeks ago the agent was a loop in a file. Here is what it is now, and why
each piece is there.

## The list

| It can | Because |
|---|---|
| run anywhere, and stream | a container, `$PORT`, and SSE (Wk 1) |
| survive a redeploy | state moved out of the process (Wk 2) |
| ship itself, tested | `needs:` between two jobs in one workflow (Wk 3) |
| roll itself back | revisions tagged with the commit (Wk 3, 8) |
| refuse strangers | a key, and a *sliding* rate limit (Wk 3) |
| not overspend | steps, tokens **and** context (Wk 4) |
| be seen inside | one JSON trace per turn (Wk 5) |
| say it is unhealthy | `/metrics`, alerts in English (Wk 5) |
| survive a blip | retry the same model first (Wk 6) |
| survive an outage | then, and only then, fall back (Wk 6) |
| be debugged | traces, not guesswork (Wk 6) |
| resist injection | in the message **and in the data** (Wk 7) |
| not be an SSRF proxy | an allowlist, not a blocklist (Wk 7) |
| hold its limits at scale | shared state, proven by load (Wk 7) |
| refuse a regression | a two-tier eval gate (Wk 8) |
| leave Cloud Run | 12-factor config and OTel (Wk 8) |

## The five ideas worth keeping

**1. A broken agent returns 200 OK.** No crash, no red graph — the answers just
get worse. This is why observability is not optional for AI systems in a way it
almost is for CRUD services.

**2. The failure mode of an unbounded agent is an invoice, not an outage.**
Nothing to page on. You only find out from the bill.

**3. Tool output is untrusted input.** Everyone guards the user's message. The
injection that gets you is in the order note, the scraped page, the database row.

**4. Retry the same model before changing models.** One blip that switches
providers silently downgrades every answer, and nothing alerts, because the turn
succeeded.

**5. Ask where state lives.** Every "quietly wrong under scale" bug in this
course — the rate limit, the metrics window, session memory — was the same bug
wearing a different hat.

## The one habit

Every week you broke something on purpose before fixing it: watched memory die
on redeploy, watched the gate block a PR, watched a load test expose a rate limit
that was 5× looser than its setting.

**A guardrail you have never seen fire is a guardrail you are trusting on
faith.** Fire them deliberately, on a schedule, in production. That habit is
worth more than any single thing in this repo.

## Where to go next

The honest gaps this project leaves, roughly in order of what a real deployment
would need:

- **True token streaming** — `stream.py` streams the shape of a turn, not deltas
  off the provider socket.
- **Summarising memory** — `trim()` drops old turns; production summarises them.
- **Egress proxy** — `check_url` leaves a DNS-rebinding hole that belongs in
  infrastructure, not in every tool.
- **Metrics in the log platform** — `/metrics` computes its own rolling sample;
  at volume, that arithmetic belongs where the logs are.
- **A real eval set** — eleven cases is a demo. Mine your traces for the turns
  that actually went wrong and add those.
