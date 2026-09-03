"""A narrated single turn, for showing the room what the agent does.

    python -m checks.demo_turn

Prints the four moves as they happen. Uses a stand-in model, so it needs
no API key and no internet - which means it works for every laptop in the
room, on the first morning, before anything is configured.

With a real key set, pass --real to watch the same four moves with the
actual model deciding for itself:

    python -m checks.demo_turn --real
"""
import sys
from types import SimpleNamespace as NS

from app.agent import run_turn

QUESTION = "where is my order ORD-1002?"


def _narrating_model():
    """A stand-in that asks for one tool, then answers - printing as it goes."""
    state = {"n": 0}

    def model(messages):
        state["n"] += 1
        if state["n"] == 1:
            print("  [2] the model asks   for a tool: lookup_order, with ORD-1002")
            return NS(
                content=[NS(type="tool_use", name="lookup_order",
                            input={"order_id": "ORD-1002"}, id="t1")],
                stop_reason="tool_use")

        result = messages[-1]["content"][0]["content"]
        print(f"  [3] your code runs   it -> {result[:58]}...")
        return NS(content=[NS(type="text",
                              text="Your standing desk is shipped and arrives "
                                   "Thursday.")],
                  stop_reason="end_turn")
    return model


def main(real=False):
    print(f"\n  [1] you ask          {QUESTION}")

    if real:
        # The real model decides for itself. The four moves are the same; only
        # the wording of the answer changes.
        result = run_turn(QUESTION)
    else:
        result = run_turn(QUESTION, model_fn=_narrating_model())

    reply, history = result[0], result[1]
    print(f"  [4] the model answers {reply}\n")

    print(f"  the conversation is now {len(history)} entries long:")
    for m in history:
        content = m["content"]
        if isinstance(content, str):
            print(f"    {m['role']:<10} {content[:56]}")
            continue
        for block in content:
            if isinstance(block, dict):
                print(f"    {m['role']:<10} tool result: "
                      f"{str(block['content'])[:44]}")
            else:
                label = getattr(block, "name", None) or getattr(block, "text", "")
                print(f"    {m['role']:<10} {getattr(block, 'type', '')} {label[:44]}")
    print("\n  Every new question re-sends this whole list. The model remembers"
          " nothing.\n")


if __name__ == "__main__":
    main(real="--real" in sys.argv)
