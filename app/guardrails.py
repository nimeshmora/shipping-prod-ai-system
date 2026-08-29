"""Guardrails: the rules every request passes through.

Weeks 03, 04, and 07 all add rules here. Each is a small function that raises
GuardrailError when broken. The web layer turns that into a clean 4xx.

  Week 03  api key + rate limit
  Week 04  step + token budget
  Week 07  input size, blocked input, url allowlist
"""
import ipaddress
import os
import re
import time
from collections import defaultdict, deque
from urllib.parse import urlparse


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


# ---- Week 03: rate limit ---------------------------------------------------
RATE_LIMIT = int(os.environ.get("RATE_LIMIT_PER_MIN", "20"))
_hits = defaultdict(deque)


def check_rate_limit(caller):
    now = time.monotonic()
    window = _hits[caller]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= RATE_LIMIT:
        raise GuardrailError(f"rate limit reached ({RATE_LIMIT}/min)", status=429)
    window.append(now)


def reset_rate_limits():
    _hits.clear()


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
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise GuardrailError("only http and https urls are allowed")
    host = parsed.hostname or ""
    if host not in ALLOWED_HOSTS:
        raise GuardrailError(f"host '{host}' is not on the allowlist")
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise GuardrailError("internal addresses are blocked")
    except ValueError:
        pass


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
