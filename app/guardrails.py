"""Guardrails: the rules every request passes through.

Each rule is a small function that raises GuardrailError when broken. The web
layer catches that and turns it into a clean 4xx, so a broken rule is an
expected outcome with a useful status code - never a 500 and never a stack
trace.

  Week 03  api key, rate limit
  Week 04  step and token budgets
  Week 07  input size, blocked input, url allowlist, tool output

Why these live in one file rather than inside the handlers: they are the answer
to "what is this service's policy?", and that answer should be readable in one
place. Scattered through route handlers, nobody can tell you what the rules are.
"""
import os
import time
from collections import defaultdict, deque


class GuardrailError(Exception):
    """A rule was broken, and it is the caller's fault.

    Carries the HTTP status the web layer should return. Defaulting to 400 is
    deliberate: a guardrail failure is a bad request, not a server error, and
    getting that wrong makes your error rate lie about who is at fault.
    """

    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


# ---- Week 03: who is calling? ---------------------------------------------
def _valid_keys():
    """Read the keys fresh on every call, from the environment.

    Fresh, so rotating a key is a config change and a restart - not a code
    change and a deploy. A set built once at import time would mean the only
    way to revoke a leaked key is to ship new code.
    """
    return {k.strip() for k in os.environ.get("API_KEYS", "").split(",")
            if k.strip()}


def check_api_key(key):
    """Reject anyone without a valid key.

    With API_KEYS unset, auth is OFF. That is a deliberate local-dev
    convenience and a genuine production risk: a service deployed with the
    variable missing is wide open. Week 08's eval gate is one place to assert
    it is set; Cloud Run's own env config is another.

    An unauthenticated LLM endpoint is somebody else's free compute. It will be
    found - scanners sweep for open inference endpoints - and the first you hear
    of it is the bill.
    """
    valid = _valid_keys()
    if not valid:
        return                      # no keys configured -> auth off (local dev)
    if key not in valid:
        # 401, not 403: the caller has not proven who they are. Say nothing
        # about whether the key was missing, malformed or simply wrong - that
        # distinction is only useful to someone guessing.
        raise GuardrailError("missing or invalid API key", status=401)


# ---- Week 03: how often? --------------------------------------------------
RATE_LIMIT = int(os.environ.get("RATE_LIMIT_PER_MIN", "20"))

# One deque of timestamps per caller. Week 07 moves this into shared storage,
# because a counter in this process counts per CONTAINER - so the platform
# scaling you out to 5 instances quietly turns a 20/min limit into 100/min.
_hits = defaultdict(deque)


def check_rate_limit(caller):
    """Allow RATE_LIMIT requests per caller per rolling 60 seconds.

    A SLIDING window, not a fixed one. The naive version - a counter on a
    per-minute key - lets a caller send the full allowance at 11:59:59 and the
    full allowance again at 12:00:00: a 20/min limit that permits 40 requests
    in one second. Dropping timestamps older than 60s counts what actually
    happened in the last minute.

    Why an agent needs this more than an ordinary API: one request here costs
    real money at a provider, and can run several model calls. A loop in
    someone's script is a bill, not just load.
    """
    now = time.monotonic()          # monotonic: immune to clock changes
    window = _hits[caller]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= RATE_LIMIT:
        # 429 is the honest answer, and it tells a well-behaved client to back
        # off rather than retry immediately.
        raise GuardrailError(f"rate limit reached ({RATE_LIMIT}/min)",
                             status=429)
    window.append(now)


def reset_rate_limits():
    """Used by the tests, so one test cannot leak into the next."""
    _hits.clear()


# ---- Week 04: what one turn is allowed to cost ----------------------------
MAX_STEPS = int(os.environ.get("MAX_STEPS", "6"))
MAX_TOKENS_PER_TURN = int(os.environ.get("MAX_TOKENS_PER_TURN", "20000"))


class Budget:
    """A per-turn allowance for steps and tokens.

    Weeks 01-03 protected you from other people. This protects you from your
    own agent, which is a different problem and a more expensive one.

    Nothing here crashes on its own. A model that keeps asking for tools, a
    tool that keeps returning something the model wants to follow up on, a
    context that grows every trip - none of that raises an exception. It just
    runs, and charges you, and eventually answers. The failure mode of an
    unbounded agent is not an outage; it is an invoice.

    Two limits, because they catch different runaways:

      steps   how many times round the loop. Catches a model that is looping,
              confused, or being led on by tool output.
      tokens  how much was actually sent and received. Catches ONE step that
              is enormous - a huge context, or a tool returning a whole file.

    A step limit alone lets six colossal calls through. A token limit alone
    lets a hundred tiny ones through. You want both.
    """

    def __init__(self, max_steps=MAX_STEPS, max_tokens=MAX_TOKENS_PER_TURN):
        self.max_steps = max_steps
        self.max_tokens = max_tokens
        self.steps = 0
        self.tokens = 0

    def add_step(self):
        self.steps += 1
        if self.steps > self.max_steps:
            raise GuardrailError(f"step limit reached ({self.max_steps})")

    def add_tokens(self, n):
        self.tokens += int(n or 0)
        if self.tokens > self.max_tokens:
            raise GuardrailError(f"token budget reached ({self.max_tokens})")
