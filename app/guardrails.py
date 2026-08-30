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


# ---- Week 07: hostile input, and hostile DATA ----------------------------
# BUILD THIS.
#
# Four things, and the third is the one people miss.
#
# 1. check_input_length(text), against MAX_INPUT_CHARS (env, default 4000)
#
#    Not a nicety - input length is a COST attack. One 200KB message becomes
#    200KB of prompt on EVERY trip round the loop, several times over, at your
#    expense. Week 04's token budget catches it eventually; this catches it
#    before you pay for a single call.
#
# 2. check_blocked_input(text), against a few obvious probe patterns
#    (rm -rf, __import__, subprocess, eval(). Cheap, and honest about being a
#    speed bump rather than the control.
#
# 3. check_tool_output(text), against MAX_TOOL_OUTPUT_CHARS
#
#    THE AGENT-SHAPED HALF OF INJECTION. The two functions above guard what the
#    USER types. But a tool result also goes straight back into the model's
#    context, and you did not write what a web page, a database row, or a
#    customer's order note says.
#
#    Go and read app/orders.py, and look at ORD-1043's note. That is where
#    injection actually lives: the request "what is happening with ORD-1043?"
#    is completely innocent.
#
#    Truncate what is too long, then neutralise instructions aimed at the model
#    ("ignore all previous instructions", "new instructions:", "system prompt:"
#    and friends) by replacing them with "[filtered]".
#
#    IT MUST NEVER RAISE. A hostile page taking a whole turn down is just a
#    different denial of service. Return something safe instead.
#
#    Be honest with yourself about what this is. Five regexes are a speed bump,
#    and a paraphrase walks straight past them. The real defences are
#    structural: the system prompt telling the model that order notes are
#    information and never instructions, and the fact that this agent has no
#    tool that could action a refund even if it were convinced to try. This
#    layer buys you the obvious cases and a signal in the trace.
#
# 4. check_url(url), for the new fetch_url tool
#
#    This is the guard that stops SSRF. Your agent runs INSIDE your cloud
#    account, so it can reach things the internet cannot:
#
#        http://169.254.169.254/computeMetadata/v1/instance/service-accounts/
#
#    A fetch tool without this check will read your instance's service-account
#    token and put it in the chat reply. The model did nothing wrong. Your tool
#    did.
#
#    Refuse, in this order:
#      - any scheme that is not http/https. A tool that accepts file:// is a
#        "read any file on the server" tool.
#      - literal IPs that are private, loopback, link-local, reserved or
#        multicast (ipaddress.ip_address, then the is_* properties)
#      - any host not in an ALLOWED_HOSTS allowlist
#
#    The ALLOWLIST is what actually protects you. You cannot enumerate the
#    hosts an attacker might think of; you can enumerate the ones you meant to
#    talk to. The IP checks are depth for the day someone widens the list.
#
#    Know the hole you are leaving: a hostname ON the allowlist whose DNS points
#    at 169.254.169.254 passes every check above. Closing it means resolving the
#    name yourself and connecting to the validated address, because DNS can
#    change its answer between your check and the library's lookup (DNS
#    rebinding). In production you put egress behind a proxy that enforces this
#    once, rather than in every tool.
#
# Then wire them in:
#
#   app/main.py    check_input_length and check_blocked_input on BOTH endpoints
#   app/agent.py   check_tool_output on every tool result before it goes back
#                  to the model, and set trace["tool_output_filtered"] when it
#                  changed something - otherwise you cannot tell how often
#                  someone is trying.
#   app/agent.py   a fetch_url tool that calls check_url, with a timeout, a
#                  size cap, and follow_redirects=False (a permitted host that
#                  replies "302 -> 169.254.169.254" walks straight past the
#                  allowlist you just checked). Register it in TOOLS and
#                  _HANDLERS - a guardrail on a tool nobody wired up protects
#                  nothing.
#
# And move the rate-limit counter into app/store.py - see that file.
#
# Done when:  make check-week-07
# Stuck? git diff week-07-attack..week-07-solution -- app/guardrails.py
