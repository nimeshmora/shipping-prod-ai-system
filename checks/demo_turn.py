"""Show, step by step, what the agent does with one question.

    python -m checks.demo_turn          # no API key needed
    python -m checks.demo_turn --real   # uses your key, the real model decides

Prints one labelled step at a time, pausing between them, so a room can follow
what happens and when. This is a teaching aid, not part of the agent.
"""
import json
import os
import re
import sys
import time
from types import SimpleNamespace as NS

from app.agent import MODEL, SYSTEM_PROMPT, TOOLS, run_turn

QUESTION = "where is my order ORD-1002?"
PAUSE = 1.2          # seconds between steps, so the room can read each one


def _step(n, who, what, detail=None):
    print(f"\n  STEP {n} · {who}")
    print(f"     {what}")
    if detail:
        for line in detail:
            print(f"     {line}")
    sys.stdout.flush()
    time.sleep(PAUSE)


def _pick_tool(question):
    """Stand in for the model's choice of tool.

    The real model reads the question and decides. This mimics that decision
    just well enough for the demo to be honest when the question changes:
    an order id means look it up, an arithmetic expression means calculate.
    """
    order = re.search(r"ORD-\d+", question, re.I)
    if order:
        return ("lookup_order", {"order_id": order.group().upper()},
                "Your standing desk is shipped and arrives Thursday.")

    sum_ = re.search(r"(\d+)\s*([*+/-])\s*(\d+)", question)
    if sum_:
        expr = f"{sum_.group(1)} {sum_.group(2)} {sum_.group(3)}"
        return ("calculator", {"expression": expr}, None)

    return ("word_count", {"text": question}, None)


def _fake_model(question):
    """Stands in for the model. Asks for one tool, then reports the result."""
    name, args, canned = _pick_tool(question)
    calls = {"n": 0}

    def model(messages):
        calls["n"] += 1
        if calls["n"] == 1:
            _step(2, "THE MODEL DECIDES",
                  "It cannot work this out on its own. So it asks for a tool:",
                  [f"tool:  {name}",
                   f"input: {json.dumps(args)}"])
            return NS(content=[NS(type="tool_use", name=name,
                                  input=args, id="t1")],
                      stop_reason="tool_use")

        result = messages[-1]["content"][0]["content"]
        _step(3, "YOUR CODE RUNS THE TOOL",
              "It ran the tool and handed the answer back:",
              [result])
        answer = canned or f"The answer is {result}."
        return NS(content=[NS(type="text", text=answer)],
                  stop_reason="end_turn")
    return model


def main(real=False, question=None):
    print("\n" + "=" * 62)
    print("  ONE QUESTION, STEP BY STEP")
    print("=" * 62)

    global QUESTION
    if question:
        QUESTION = question

    # Say up front which of the two modes this is. Without it the room cannot
    # tell whether a real model answered or a scripted stand-in did.
    if real:
        print(f"\n  MODE: the real model - {MODEL}")
        print(f"        reached through {os.environ.get('BASE_URL', 'the course gateway')}")
        print("        uses your KODEKEY. Costs a fraction of a cent.")
    else:
        print("\n  MODE: a stand-in for the model - no key, no internet, free")
        print("        the LOOP below is the real one")
        print("        only the model's choice is scripted")
    time.sleep(PAUSE)

    print("\n  WHAT GETS SENT, every single question:")
    rules = f"{len(SYSTEM_PROMPT.split())} words"
    print(f"     1. the standing rules      {rules}, "
          f"{'sent with the question' if real else 'not sent - no model to send them to'}")
    print("     2. the conversation so far  empty - this is question one")
    print(f"     3. the list of tools        {len(TOOLS)} of them:")
    for t in TOOLS:
        print(f"           - {t['name']}")
    time.sleep(PAUSE)

    _step(1, "YOU ASK", QUESTION)

    result = run_turn(QUESTION) if real else run_turn(QUESTION,
                                                     model_fn=_fake_model(QUESTION))
    reply, history = result[0], result[1]

    _step(4, "THE MODEL ANSWERS", "Now it has the facts, so now it can answer:",
          [reply])

    print("\n" + "-" * 62)
    print(f"  AND IT KEPT THE CONVERSATION - {len(history)} entries:")
    print("-" * 62)
    for i, m in enumerate(history, 1):
        content = m["content"]
        if isinstance(content, str):
            print(f"    {i}. {m['role']:<9} {content[:46]}")
            continue
        for block in content:
            if isinstance(block, dict):
                print(f"    {i}. {m['role']:<9} tool result: "
                      f"{str(block['content'])[:34]}")
            else:
                label = getattr(block, "name", None) or getattr(block, "text", "")
                print(f"    {i}. {m['role']:<9} {getattr(block, 'type', '')}"
                      f"  {label[:34]}")

    print("\n  Every new question re-sends this whole list.")
    print("  The model itself remembers nothing.\n")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(real="--real" in sys.argv,
         question=" ".join(args) or None)
