"""Week 08: the eval gate.

Runs each case in cases.json against the app and grades it cheaply with a
"contains" check or a "blocked" check. High-severity failures make this exit
non-zero, which is what a CI pipeline uses to block a bad change from shipping.

By default it uses a fake model so it runs in CI with no API key. Pass --real to
run against the real model, and --judge to also run the judge tier
(evals/judge.py), which grades answer QUALITY rather than keyword presence.

    python -m evals.run_evals              # deterministic, no key, gates
    python -m evals.run_evals --real       # against the real model
    python -m evals.run_evals --real --judge   # + quality grading
"""
import json
import os
import sys
from types import SimpleNamespace as NS

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = os.path.join(HERE, "cases.json")


def _fake_model(messages, trace=None):
    """A stand-in for the model, so the gate runs deterministically in CI with
    no API key.

    It fakes the model's *decisions* only - which tool to call, and how to word
    the final answer. It never computes the answer itself: the number comes back
    from the real tool in app/agent.py, via a real tool_result.

    That distinction is the whole point. If this function returned "492"
    directly, the gate would still pass after you broke the calculator, and
    Week 08 would be teaching a lie. Fake the model, never fake your own code.
    """
    user = ""
    for m in messages:
        if m["role"] == "user" and isinstance(m["content"], str):
            user = m["content"]

    # Step 2: a tool result just came back - report it as the final answer.
    last = messages[-1]
    if isinstance(last.get("content"), list):
        results = [b for b in last["content"]
                   if isinstance(b, dict) and b.get("type") == "tool_result"]
        if results:
            return NS(content=[NS(type="text", text=f"That is {results[0]['content']}.")],
                      stop_reason="end_turn", usage=None)

    # Step 1: decide which tool to ask for, exactly as a real model would.
    import re as _re
    m = _re.search(r"ORD-\d+", user, _re.IGNORECASE)
    if m:
        block = NS(type="tool_use", name="lookup_order",
                   input={"order_id": m.group(0)}, id="eval-0")
        return NS(content=[block], stop_reason="tool_use", usage=None)
    if "12 * 41" in user or "12*41" in user:
        block = NS(type="tool_use", name="calculator",
                   input={"expression": "12 * 41"}, id="eval-1")
        return NS(content=[block], stop_reason="tool_use", usage=None)
    if "quick brown fox" in user:
        block = NS(type="tool_use", name="word_count",
                   input={"text": "the quick brown fox"}, id="eval-2")
        return NS(content=[block], stop_reason="tool_use", usage=None)

    return NS(content=[NS(type="text", text="ok")], stop_reason="end_turn", usage=None)


def run(real=False, use_judge=False):
    from app.agent import run_turn, call_model
    from app import guardrails as g
    from evals import judge

    cases = json.load(open(CASES))
    model_fn = call_model if real else _fake_model
    failures = []
    judged = judging_enabled = use_judge and judge.available()
    if use_judge and not judging_enabled:
        print("  note: --judge asked for but OPENROUTER_API_KEY is not set; skipping it\n")

    for c in cases:
        cid, sev = c["id"], c.get("severity", "medium")
        # A judge-only case has nothing deterministic to check, so it is
        # skipped entirely unless the judge is actually running.
        if c.get("judge") and not judging_enabled:
            _report(cid, sev, True, "skipped (judge tier not running)")
            continue
        try:
            # input guardrails run first, exactly like the web layer
            g.check_input_length(c["message"])
            g.check_blocked_input(c["message"])
        except g.GuardrailError:
            ok = bool(c.get("expect_blocked"))
            _report(cid, sev, ok, "blocked as expected" if ok else "unexpectedly blocked")
            if not ok and sev == "high":
                failures.append(cid)
            continue

        if c.get("expect_blocked"):
            _report(cid, sev, False, "should have been blocked, was not")
            if sev == "high":
                failures.append(cid)
            continue

        reply, _, _ = run_turn(c["message"], model_fn=model_fn)

        if "expect_contains" in c:
            need = str(c["expect_contains"])
            ok = need in reply
            _report(cid, sev, ok,
                    f"contains '{need}'" if ok
                    else f"missing '{need}' in: {reply!r}")
            if not ok and sev == "high":
                failures.append(cid)

        # The judge tier. Runs only with a key, and only gates when the case
        # is high severity - a non-deterministic grader must not be able to
        # block a build on its own bad day.
        if judging_enabled and c.get("judge"):
            passed, why = judge.grade(c["message"], reply, c["judge"])
            _report(f"{cid}:judge", sev, passed, why)
            if not passed and sev == "high":
                failures.append(f"{cid}:judge")

    print()
    if judged:
        print("  (judge tier ran; its verdicts are advisory unless high severity)")
    if failures:
        print(f"GATE FAILED: high-severity cases failed: {', '.join(failures)}")
        return 1
    print("GATE PASSED")
    return 0


def _report(cid, sev, ok, detail):
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {cid} ({sev}) - {detail}")


if __name__ == "__main__":
    sys.exit(run(real="--real" in sys.argv,
                 use_judge="--judge" in sys.argv))
