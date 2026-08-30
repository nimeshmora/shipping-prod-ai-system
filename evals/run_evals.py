"""evals/run_evals.py - Week 08. BUILD THIS FILE.

The eval gate: the thing that stops a bad change reaching users.

WHY THIS IS THE LAST WEEK
-------------------------
Agents have no compiler. Nothing catches a prompt edit that makes answers worse.
Every other week guarded against FAILURE; this one guards against REGRESSION,
which is harder, because the service stays perfectly green while the answers
get worse.

Two tiers, because they catch different things.

TIER 1 - deterministic, free, gates every PR
--------------------------------------------
"contains" and "blocked" checks against evals/cases.json. Must run in CI with
NO API KEY, which rests on one design decision worth stating plainly:

    _fake_model fakes the model's DECISIONS - which tool to ask for - and
    NEVER the answer. The "492" comes back from your REAL calculator, through
    a real tool_result.

If the fake returned "492" itself, the gate would still pass after you broke
the calculator, and this week would be teaching a lie.

    Fake the model. Never fake your own code.

The checkpoint proves this by sabotaging the calculator and asserting the gate
goes red. If your gate passes that, it is testing nothing.

TIER 2 - the judge, for what substrings cannot see
--------------------------------------------------
evals/judge.py is GIVEN - read it, it needs no changes. Your job is to call it,
and to add judge cases to cases.json.

Why it exists:

    "Your order ORD-1043 is delayed."                      <- good
    "ORD-1043 is delayed. Also your refund is approved."   <- contains
                                                              "delayed", and
                                                              promises a refund
                                                              nobody agreed to

Both pass `expect_contains: "delayed"`. Only one should ship.

What to build
-------------
1. `_fake_model(messages, trace=None)`

   Look at the last user message. If it mentions an ORD-nnnn id, return a
   tool_use block asking for lookup_order. If it looks like the arithmetic
   case, ask for calculator. Word count, ask for word_count. Otherwise answer
   plainly.

   When the LAST message contains a tool_result, report that result as the
   final answer ("That is {result}.") with stop_reason "end_turn".

   That is the whole trick: it makes the decisions a real model would make, and
   your own code produces every actual value.

2. `run(real=False, use_judge=False) -> exit code`

   For each case in cases.json:

     - run the input guardrails first, exactly like the web layer does
       (check_input_length, check_blocked_input). If a case declares
       expect_blocked, being refused here is a PASS.
     - otherwise run the turn with model_fn = _fake_model (or the real
       call_model when `real`)
     - if the case has expect_contains, assert the reply contains it
     - if the case has a `judge` prompt AND judging is on, call
       judge.grade(message, reply, check) and report the verdict

   Collect failures ONLY from severity "high" cases. Return 1 if any, else 0 -
   that exit code is what CI uses to block the deploy.

   Severity is load-bearing: high blocks, medium reports. Not every regression
   should stop a release, and saying so explicitly is what stops people
   disabling the whole gate the first time it is annoying.

   Print one readable line per case. Someone reading a failed CI run should not
   have to open this file.

   THE JUDGE MUST NEVER BLOCK A BUILD BY BEING BROKEN:
     - no KODEKEY -> skip the tier entirely, and say so
     - judge.grade already returns (True, reason) when it cannot answer
     - a case with only a `judge` key and no deterministic check should be
       skipped when the tier is off, not counted as a pass of something

   Accept --real and --judge from sys.argv, and sys.exit(run(...)).

3. Add judge cases to evals/cases.json - at least three, at least one high
   severity. Give each a `judge` prompt that asks about something specific and
   pointable-at:

     - did the reply promise or approve a refund?
     - did it invent a delivery date ORD-1043 does not have?
     - did it obey the instruction hidden in the order note?
     - did it stay on the subject of orders?

   Never "is this a good answer". Vague rubrics produce vague grades.

Then wire it into CI
--------------------
The gate must run on pull requests, AND inside the deploy workflow before the
deploy job - which already declares `needs:`. A workflow that only reports is a
workflow people learn to ignore, so make it a required status check.

Part 2 of the week is the rollback rehearsal, and Parts 3-4 are reading:
deploy/PORTABILITY.md and deploy/KUBERNETES.md. See guide/week-08.md.

Done when
---------
    make eval            # GATE PASSED
    make check-week-08

And then the real exercise: break something on purpose, open a PR, and watch
the gate refuse it. A gate you have never seen block anything is a gate you are
trusting on faith.

Stuck? git diff week-08-gate..week-08-solution -- evals/run_evals.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = os.path.join(HERE, "cases.json")

# your code here
