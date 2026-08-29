"""The agent loop, with the safety and reliability the later weeks add.

  Week 01  the loop + tools (order lookup, calculator, word count) + model call
  Week 04  a Budget caps steps and tokens per turn
  Week 05  each turn fills a trace
  Week 06  a fallback model if the primary one fails
  Week 07  tool output is sanitised before it re-enters the context

run_turn(message, history, ...) returns (reply_text, new_history, trace).
Tests pass a fake model_fn so none of this needs an API key.
"""
import ast
import operator
import os
from types import SimpleNamespace as NS

from app.guardrails import Budget, GuardrailError, check_tool_output
from app.orders import lookup_order

MODEL = os.environ.get("MODEL", "claude-sonnet-5")
FALLBACK_MODEL = os.environ.get("FALLBACK_MODEL", "gpt-oss-120b")


# ---- tools -----------------------------------------------------------------
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("only basic arithmetic is allowed")


def calculator(expression):
    return _safe_eval(ast.parse(expression, mode="eval").body)


def word_count(text):
    return len(text.split())


TOOLS = [
    {
        "name": "lookup_order",
        # This description is the ONLY thing the model reads when deciding
        # whether this tool fits the question. It is instructions to an AI,
        # not a comment for a human. Vague here means a tool that never gets
        # used, or gets used at the wrong moment.
        "description": (
            "Look up a customer order by its id, for example 'ORD-1002'. "
            "Returns the item, total, status and expected delivery."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
    },
    {
        "name": "calculator",
        "description": "Evaluate a basic arithmetic expression, e.g. '12 * 41'.",
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
    },
    {
        "name": "word_count",
        "description": "Count how many words are in a piece of text.",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    },
]

_HANDLERS = {"lookup_order": lookup_order,
             "calculator": calculator,
             "word_count": word_count}


def run_tool(name, args):
    fn = _HANDLERS.get(name)
    if fn is None:
        return f"unknown tool: {name}"
    try:
        return str(fn(**args))
    except Exception as e:
        return f"tool error: {e}"


# ---- the model call, with a fallback (Week 06) -----------------------------
# The gateway speaks the OpenAI format, but the loop below reads the Anthropic
# shape (resp.content blocks, resp.stop_reason). So this section adapts at the
# boundary: translate on the way out, translate back on the way in. The loop,
# the budget, the trace, and every test stay exactly as they were, because none
# of them ever learn which provider answered. Same trick as memory.py in Wk02:
# keep the name, swap the guts.

def _client():
    from openai import OpenAI
    key = os.environ.get("KODEKEY")
    if not key:
        raise GuardrailError(
            "KODEKEY is not set. Copy .env.example to .env, paste your key, "
            "then run: set -a && source .env && set +a", status=500)
    return OpenAI(
        api_key=key,
        base_url=os.environ.get("BASE_URL", "https://api.ai.kodekloud.com/v1"),
    )


def _tools_openai():
    """Our Anthropic-style TOOLS, in the shape the gateway expects."""
    return [{"type": "function",
             "function": {"name": t["name"], "description": t["description"],
                          "parameters": t["input_schema"]}}
            for t in TOOLS]


def _to_anthropic_shape(completion):
    """Turn one OpenAI response into the block shape run_turn already reads."""
    import json
    choice = completion.choices[0]
    msg = choice.message
    blocks = []
    if msg.content:
        blocks.append(NS(type="text", text=msg.content))
    for call in (msg.tool_calls or []):
        try:
            args = json.loads(call.function.arguments or "{}")
        except json.JSONDecodeError:
            args = {}
        blocks.append(NS(type="tool_use", name=call.function.name,
                         input=args, id=call.id))
    stop = "tool_use" if msg.tool_calls else "end_turn"

    # usage: the gateway says prompt/completion, the budget reads input/output
    u = getattr(completion, "usage", None)
    usage = None if u is None else NS(
        input_tokens=getattr(u, "prompt_tokens", 0) or 0,
        output_tokens=getattr(u, "completion_tokens", 0) or 0)
    return NS(content=blocks, stop_reason=stop, usage=usage)


def _to_openai_messages(messages):
    """Our conversation history, in the shape the gateway expects."""
    import json
    out = []
    for m in messages:
        content = m["content"]
        if isinstance(content, str):
            out.append({"role": m["role"], "content": content})
            continue
        # a list of blocks: either our assistant reply, or tool results
        tool_results = [b for b in content
                        if isinstance(b, dict) and b.get("type") == "tool_result"]
        if tool_results:
            for b in tool_results:
                out.append({"role": "tool", "tool_call_id": b["tool_use_id"],
                            "content": str(b["content"])})
            continue
        text = "".join(b.text for b in content
                       if getattr(b, "type", None) == "text")
        calls = [{"id": b.id, "type": "function",
                  "function": {"name": b.name, "arguments": json.dumps(b.input)}}
                 for b in content if getattr(b, "type", None) == "tool_use"]
        entry = {"role": "assistant", "content": text or None}
        if calls:
            entry["tool_calls"] = calls
        out.append(entry)
    return out


def call_model(messages, trace=None):
    """Try the primary model; if it errors, try the fallback once.
    Records which provider answered into the trace."""
    client = _client()
    payload = _to_openai_messages(messages)
    for provider, model in (("primary", MODEL), ("fallback", FALLBACK_MODEL)):
        try:
            completion = client.chat.completions.create(
                model=model, max_tokens=1024, tools=_tools_openai(),
                messages=payload)
            resp = _to_anthropic_shape(completion)
            if trace is not None:
                trace["model_calls"].append({"provider": provider, "model": model})
            return resp
        except Exception as e:  # network, overload, etc.
            if provider == "fallback":
                raise
            if trace is not None:
                trace["model_calls"].append({"provider": "primary", "error": str(e)})
    raise RuntimeError("no model answered")


# ---- the loop --------------------------------------------------------------
def run_turn(message, history=None, model_fn=call_model, trace=None):
    messages = list(history or []) + [{"role": "user", "content": message}]
    budget = Budget()

    while True:
        budget.add_step()                      # Week 04: cannot loop forever
        resp = model_fn(messages, trace) if _accepts_trace(model_fn) else model_fn(messages)

        usage = getattr(resp, "usage", None)
        if usage is not None:
            budget.add_tokens(getattr(usage, "input_tokens", 0)
                              + getattr(usage, "output_tokens", 0))

        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason != "tool_use":
            text = "".join(b.text for b in resp.content
                           if getattr(b, "type", None) == "text")
            if trace is not None:
                trace["steps"] = budget.steps
                trace["token_count"] = budget.tokens
            return text, messages, trace

        results = []
        for block in resp.content:
            if getattr(block, "type", None) == "tool_use":
                out = run_tool(block.name, block.input)
                # Week 07: a tool result is untrusted input too. It goes
                # straight back into the model's context, and you did not
                # write what a web page or a file says.
                safe = check_tool_output(out)
                if trace is not None:
                    trace["tools_used"].append(block.name)
                    if safe != out:
                        trace["tool_output_filtered"] = True
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": safe,
                })
        messages.append({"role": "user", "content": results})


def _accepts_trace(fn):
    try:
        import inspect
        return len(inspect.signature(fn).parameters) >= 2
    except (TypeError, ValueError):
        return False
