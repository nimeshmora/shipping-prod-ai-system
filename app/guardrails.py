"""app/guardrails.py - Week 03. BUILD THIS FILE.

Every rule this service enforces lives here, from now until Week 08. Two rules
this week: who is calling, and how often.

Why one file rather than checks inside each handler: this file is the answer to
"what is this service's policy?", and that answer should be readable in one
place. Scattered through route handlers, nobody can tell you what the rules are.

The pattern
-----------
Each rule is a small function that RAISES when broken. The web layer catches
that one exception type and turns it into a clean 4xx - so a broken rule is an
expected outcome with a useful status code, never a 500 and never a stack trace.

What to build
-------------
1. `GuardrailError(Exception)` carrying a `.status` for the web layer:

       class GuardrailError(Exception):
           def __init__(self, message, status=400):
               super().__init__(message)
               self.status = status

   Default to 400. A guardrail failure is a bad REQUEST, not a server error,
   and getting that backwards makes your error rate lie about who is at fault.

2. `check_api_key(key)`

   Read the allowed keys from the environment, comma-separated:

       os.environ.get("API_KEYS", "")

   Read them FRESH on every call, inside the function. A set built once at
   import time means the only way to revoke a leaked key is to ship new code.
   Fresh, and rotating a key is a config change and a restart.

   If API_KEYS is empty or unset, auth is OFF - return without raising. That is
   a deliberate local-dev convenience and a genuine production risk: a service
   deployed without the variable is wide open. Worth knowing which one you are.

   Otherwise, an unrecognised key raises with status 401. Not 403: the caller
   has not proven who they are. And say nothing about WHY it failed - missing,
   malformed and simply wrong are the same answer, because the distinction only
   helps someone guessing.

   Why this matters at all: an unauthenticated LLM endpoint is somebody else's
   free compute. Scanners sweep for open inference endpoints. It will be found,
   and the first you hear of it is the bill.

3. `check_rate_limit(caller)`

       RATE_LIMIT = int(os.environ.get("RATE_LIMIT_PER_MIN", "20"))

   Allow RATE_LIMIT requests per caller per rolling 60 seconds, and raise with
   status 429 beyond that.

   Build a SLIDING window, not a fixed one. This is the part worth getting
   right. The naive version - a counter on a key like "user:2026-08-31T14:23"
   - lets a caller send the full allowance at 11:59:59 and the full allowance
   again at 12:00:00. A "20/min" limit that permits 40 requests in one second.

   Instead keep the TIMESTAMPS of recent requests per caller, drop the ones
   older than 60 seconds, and count what is left. A
   `defaultdict(collections.deque)` and `popleft()` is all it takes.

   Use `time.monotonic()`, not `time.time()`. Monotonic time cannot jump
   backwards when the clock is corrected, which would otherwise let a caller
   through or lock them out for a minute.

   Why an agent needs this more than an ordinary API: one request here costs
   real money at a provider and may run several model calls. A loop in
   someone's script is a bill, not just load.

4. `reset_rate_limits()` clearing the state, so one test cannot leak into
   the next.

Then wire both into app/main.py
-------------------------------
On BOTH /chat and /chat/stream:

    g.check_api_key(x_api_key)
    g.check_rate_limit(x_api_key or "anonymous")

Read the key with FastAPI's Header:

    from fastapi import Header
    def chat(req: ChatRequest, x_api_key: str | None = Header(default=None)):

Three things about the wiring:

  - Guard BOTH endpoints. The day you add a rule to one and forget the other is
    the day you have an unauthenticated path into a paid model.

  - On the streaming route, check BEFORE the response starts. Once the first
    frame goes out, HTTP 200 has already been sent and there is no status code
    left to reject with - your 401 would arrive as a 200 with an error frame
    inside it.

  - Check before ANY work. Rejecting a request that was never going to be
    allowed should cost nothing, and certainly not a model call.

Catch GuardrailError in the handler and re-raise it as an HTTPException using
e.status and str(e).

Done when
---------
    make check-week-03

It inspects your workflow files too - see guide/week-03.md for the pipeline
half of this week.

Stuck? git diff week-03-automate..week-03-solution -- app/guardrails.py
"""

# your code here
