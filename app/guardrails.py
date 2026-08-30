"""Guardrails: the rules every request passes through.

Weeks 03, 04, and 07 all add rules here. Each is a small function that raises
GuardrailError when broken. The web layer turns that into a clean 4xx.

  Week 03  api key + rate limit
  Week 04  step + token budget
  Week 07  input size, blocked input, url allowlist, shared counters
"""
import ipaddress
import os
import re
from urllib.parse import urlparse

from app import store


class GuardrailError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


# ---- Week 03: API key ------------------------------------------------------
def _valid_keys():
    return {k.strip() for k in os.environ.get("API_KEYS", "").split(",") if k.strip()}


def check_api_key(key):
    valid = _valid_keys()
    if not valid:
        return  # no keys configured -> auth off (local dev)
    if key not in valid:
        raise GuardrailError("missing or invalid API key", status=401)


# ---- Week 03: rate limit (made correct in Week 07) ------------------------
# The counter lives in app/store.py, not in a dict here. That is the whole
# difference between a rate limit and a rate suggestion: a module-level dict
# counts per container, so the platform scaling you out to 5 instances turns
# your 20/min limit into 100/min without anyone touching a config file.
#
# A rate limit is a security control. A security control that is quietly 5x
# looser than its own setting says is worse than none, because you trust it.
RATE_LIMIT = int(os.environ.get("RATE_LIMIT_PER_MIN", "20"))


def check_rate_limit(caller):
    if store.hit_count(caller) > RATE_LIMIT:
        raise GuardrailError(f"rate limit reached ({RATE_LIMIT}/min)", status=429)


def reset_rate_limits():
    store.reset_rate_limits()


# ---- Week 07: input checks -------------------------------------------------
MAX_INPUT_CHARS = int(os.environ.get("MAX_INPUT_CHARS", "4000"))
BLOCKED_PATTERNS = [r"rm\s+-rf", r"__import__", r"subprocess", r"eval\s*\("]
ALLOWED_HOSTS = {"example.com", "api.github.com"}


def check_input_length(text):
    if len(text) > MAX_INPUT_CHARS:
        raise GuardrailError(f"message too long (limit {MAX_INPUT_CHARS})")


def check_blocked_input(text):
    for pat in BLOCKED_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            raise GuardrailError("input was blocked by a safety rule")


def check_url(url):
    """Decide whether a tool may fetch this URL. Week 07.

    This is the guard that stops SSRF - Server-Side Request Forgery. The shape
    of the attack: your agent runs inside your cloud account, so it can reach
    things the internet cannot. Ask it to "summarise this page" and point it at

        http://169.254.169.254/computeMetadata/v1/instance/service-accounts/

    and a fetch tool without this check will happily read your instance's
    service-account token and put it in the chat reply. The model did nothing
    wrong. Your tool did.

    Order matters below. The allowlist is checked FIRST and is what actually
    protects you: an allowlist of hosts you meant to talk to cannot be talked
    around. The private-IP checks are defence in depth for the day someone
    widens that list.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        # file://, gopher://, and friends. A fetch tool that accepts file://
        # is a "read any file on the server" tool.
        raise GuardrailError("only http and https urls are allowed")

    host = (parsed.hostname or "").lower()
    if not host:
        raise GuardrailError("that url has no host")

    # Literal IPs, including the cloud metadata address and anything on the
    # internal network. Checked before the allowlist so the error message is
    # the useful one.
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
    # connecting to that address - because between your check and the
    # library's own lookup, DNS can change its answer (a TOCTOU / "DNS
    # rebinding" attack). In production you put egress behind a proxy that
    # enforces this once, instead of in every tool.


# ---- Week 07: what a TOOL hands back --------------------------------------
# The agent-shaped half of injection. check_input_length and check_blocked_input
# guard what the *user* types. But a tool result also goes straight back into
# the model's context, and you did not write what a web page or a file says.
# Treat tool output as untrusted input, because that is exactly what it is.
MAX_TOOL_OUTPUT_CHARS = int(os.environ.get("MAX_TOOL_OUTPUT_CHARS", "4000"))

# Phrases that only ever appear when someone is trying to talk to the model
# through your tool, rather than answer your tool's question.
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|above)",
    r"you\s+are\s+now\s+",
    r"new\s+instructions?\s*:",
    r"system\s+prompt\s*:",
]


def check_tool_output(text):
    """Sanitise what a tool returns before it re-enters the model's context.

    Never raises: a hostile web page must not take the whole turn down. It
    truncates what is too long and neutralises instructions aimed at the model,
    then hands back something safe to show the model.
    """
    text = str(text)
    if len(text) > MAX_TOOL_OUTPUT_CHARS:
        text = text[:MAX_TOOL_OUTPUT_CHARS] + "\n[truncated]"
    for pat in INJECTION_PATTERNS:
        text = re.sub(pat, "[filtered]", text, flags=re.IGNORECASE)
    return text


# ---- Week 04: step + token budget -----------------------------------------
MAX_STEPS = int(os.environ.get("MAX_STEPS", "6"))
MAX_TOKENS_PER_TURN = int(os.environ.get("MAX_TOKENS_PER_TURN", "20000"))


class Budget:
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
