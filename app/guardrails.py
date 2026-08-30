"""Guardrails: the rules every request passes through.

Each rule is a small function that raises GuardrailError when broken. The web
layer catches that and turns it into a clean 4xx, so a broken rule is an
expected outcome with a useful status code - never a 500 and never a stack
trace.

  Week 03  api key, rate limit
  Week 04  step and token budgets
  Week 07  input size, blocked input, url allowlist, tool output; and the
           rate-limit counter moves into shared storage so it is real

Why these live in one file rather than inside the handlers: they are the answer
to "what is this service's policy?", and that answer should be readable in one
place. Scattered through route handlers, nobody can tell you what the rules are.
"""
import ipaddress
import os
import re
from urllib.parse import urlparse

from app import store


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


# ---- Week 03: how often? (made correct in Week 07) -----------------------
# The counter lives in app/store.py, not in a dict here. That is the whole
# difference between a rate limit and a rate suggestion: a module-level dict
# counts per CONTAINER, so the platform scaling you out to 5 instances turns
# your 20/min limit into 100/min without anyone touching a config file.
#
# A rate limit is a security control. A security control that is quietly 5x
# looser than its own setting is worse than none, because you trust it.
RATE_LIMIT = int(os.environ.get("RATE_LIMIT_PER_MIN", "20"))


def check_rate_limit(caller):
    """Allow RATE_LIMIT requests per caller per rolling 60 seconds."""
    if store.hit_count(caller) > RATE_LIMIT:
        raise GuardrailError(f"rate limit reached ({RATE_LIMIT}/min)",
                             status=429)


def reset_rate_limits():
    """Used by the tests, so one test cannot leak into the next."""
    store.reset_rate_limits()


# ---- Week 07: what the USER sends ---------------------------------------
MAX_INPUT_CHARS = int(os.environ.get("MAX_INPUT_CHARS", "4000"))

# Patterns that only ever appear when someone is probing rather than asking
# about an order. Cheap, and honest about being a speed bump: this is a filter,
# not the control. The real defence against a hostile user is that the agent
# has no dangerous tools to reach in the first place.
BLOCKED_PATTERNS = [r"rm\s+-rf", r"__import__", r"subprocess", r"eval\s*\("]

# Hosts fetch_url may reach. An ALLOWLIST, not a blocklist - you cannot
# enumerate the hosts an attacker might think of, but you can enumerate the
# ones you meant to talk to.
ALLOWED_HOSTS = {"example.com", "api.github.com"}


def check_input_length(text):
    """Cap the input.

    Not a nicety: input length is a COST attack. One 200KB message becomes
    200KB of prompt on every trip round the loop, several times over, at
    someone else's expense. Week 04's token budget catches it eventually;
    this catches it before you pay for a single call.
    """
    if len(text) > MAX_INPUT_CHARS:
        raise GuardrailError(f"message too long (limit {MAX_INPUT_CHARS})")


def check_blocked_input(text):
    for pat in BLOCKED_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            raise GuardrailError("input was blocked by a safety rule")


def check_url(url):
    """Decide whether a tool may fetch this URL.

    This is the guard that stops SSRF - Server-Side Request Forgery. The shape
    of the attack: your agent runs inside your cloud account, so it can reach
    things the internet cannot. Ask it to "summarise this page" and point it at

        http://169.254.169.254/computeMetadata/v1/instance/service-accounts/

    and a fetch tool without this check will happily read your instance's
    service-account token and put it in the chat reply. The model did nothing
    wrong. Your tool did.

    The allowlist is what actually protects you: an allowlist of hosts you
    meant to talk to cannot be talked around. The private-IP checks are
    defence in depth for the day someone widens that list.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        # file://, gopher:// and friends. A fetch tool that accepts file:// is
        # a "read any file on the server" tool.
        raise GuardrailError("only http and https urls are allowed")

    host = (parsed.hostname or "").lower()
    if not host:
        raise GuardrailError("that url has no host")

    # Literal IPs, including the cloud metadata address and anything on the
    # internal network. Checked before the allowlist so the error is the
    # useful one.
    try:
        ip = ipaddress.ip_address(host)
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast):
            raise GuardrailError("internal addresses are blocked")
    except ValueError:
        pass                      # not a literal IP; it is a hostname

    if host not in ALLOWED_HOSTS:
        raise GuardrailError(f"host '{host}' is not on the allowlist")

    # NOTE the hole this leaves, because it is worth knowing rather than
    # papering over: a hostname on the allowlist whose DNS record points at
    # 169.254.169.254 passes every check above. Closing it properly means
    # resolving the name yourself, validating the resolved address, and
    # connecting to THAT - because between your check and the library's own
    # lookup, DNS can change its answer (a TOCTOU / "DNS rebinding" attack).
    # In production you put egress behind a proxy that enforces this once,
    # rather than in every tool.


# ---- Week 07: what a TOOL hands back ------------------------------------
# The agent-shaped half of injection, and the half people miss.
#
# check_input_length and check_blocked_input guard what the USER types. But a
# tool result also goes straight back into the model's context - and you did
# not write what a web page, a database row, or a customer's order note says.
# Treat tool output as untrusted input, because that is exactly what it is.
MAX_TOOL_OUTPUT_CHARS = int(os.environ.get("MAX_TOOL_OUTPUT_CHARS", "4000"))

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|above)",
    r"you\s+are\s+now\s+",
    r"new\s+instructions?\s*:",
    r"system\s+prompt\s*:",
]


def check_tool_output(text):
    """Sanitise what a tool returns before it re-enters the model's context.

    NEVER RAISES. A hostile web page must not be able to take a whole turn
    down - that would just be a different denial of service. It truncates what
    is too long and neutralises instructions aimed at the model.

    Be honest about what this is: five regexes are a speed bump, and a
    paraphrase walks straight past them. The real defences are structural -
    the system prompt telling the model that order notes are information and
    never instructions, and the fact that this agent has no tool that could
    action a refund even if it were convinced to try. This layer buys you the
    obvious cases and a signal in the trace when someone tries.
    """
    text = str(text)
    if len(text) > MAX_TOOL_OUTPUT_CHARS:
        text = text[:MAX_TOOL_OUTPUT_CHARS] + "\n[truncated]"
    for pat in INJECTION_PATTERNS:
        text = re.sub(pat, "[filtered]", text, flags=re.IGNORECASE)
    return text


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
