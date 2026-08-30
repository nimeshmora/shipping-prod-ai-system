"""Tests for the agent you start from. Every one uses a fake model, so no
API key is needed.

That is not a convenience - it is the design. The real model call is isolated
in one function (`call_model`), so everything else can be tested for free, in
milliseconds, deterministically, offline. An agent whose tests need an API key
is an agent nobody runs tests on.
"""
from types import SimpleNamespace as NS

import pytest

from app import agent, memory
from app.agent import AgentError


# ---- fake models -----------------------------------------------------------
def tool_then_answer(name, args):
    """A stand-in model that asks for one tool, then reports what came back."""
    state = {"n": 0}

    def model(messages):
        state["n"] += 1
        if state["n"] == 1:
            block = NS(type="tool_use", name=name, input=args, id="t1")
            return NS(content=[block], stop_reason="tool_use")
        result = messages[-1]["content"][0]["content"]
        return NS(content=[NS(type="text", text=f"It is {result}.")],
                  stop_reason="end_turn")
    return model


def plain_answer(text="hello"):
    def model(messages):
        return NS(content=[NS(type="text", text=text)], stop_reason="end_turn")
    return model


@pytest.fixture(autouse=True)
def _clean_memory():
    memory.reset()
    yield
    memory.reset()


# ---- the loop --------------------------------------------------------------
def test_the_loop_runs_a_tool_then_answers():
    reply, history = agent.run_turn(
        "where is order ORD-1002?",
        model_fn=tool_then_answer("lookup_order", {"order_id": "ORD-1002"}))
    assert "standing desk" in reply
    # four moves: user asks, model asks for a tool, tool answers, model replies
    assert len(history) == 4


def test_the_loop_returns_straight_away_when_no_tool_is_needed():
    reply, history = agent.run_turn("hello", model_fn=plain_answer("hi there"))
    assert reply == "hi there"
    assert len(history) == 2


def test_history_carries_forward_into_the_next_turn():
    _, history = agent.run_turn("hello", model_fn=plain_answer("hi"))
    _, history2 = agent.run_turn("again", history, model_fn=plain_answer("ok"))
    assert len(history2) == 4


def test_a_runaway_loop_stops_itself():
    """A model that always asks for a tool would spin forever, and every trip
    costs money."""
    def always_tool(messages):
        block = NS(type="tool_use", name="calculator",
                   input={"expression": "1+1"}, id="t")
        return NS(content=[block], stop_reason="tool_use")

    with pytest.raises(AgentError):
        agent.run_turn("go", model_fn=always_tool)


# ---- the tools -------------------------------------------------------------
def test_the_calculator_works_and_refuses_to_run_code():
    assert agent.run_tool("calculator", {"expression": "12 * 41"}) == "492"
    assert agent.run_tool("calculator", {"expression": "2 ** 8"}) == "256"
    assert "error" in agent.run_tool("calculator",
                                     {"expression": "__import__('os')"})


def test_word_count():
    assert agent.run_tool("word_count", {"text": "a b c d"}) == "4"


def test_order_lookup_finds_data_the_model_could_not_know():
    out = agent.run_tool("lookup_order", {"order_id": "ORD-1002"})
    assert "standing desk" in out and "shipped" in out


def test_order_lookup_is_not_fussy_about_case():
    assert "standing desk" in agent.run_tool("lookup_order",
                                             {"order_id": "ord-1002"})


def test_an_unknown_order_says_so_instead_of_crashing():
    assert "no order found" in agent.run_tool("lookup_order",
                                              {"order_id": "ORD-9999"})


def test_a_broken_tool_call_is_reported_not_raised():
    """The model asked for this tool. Telling it "that did not work" lets it
    recover; raising would kill the turn over one bad argument."""
    out = agent.run_tool("lookup_order", {"wrong_argument": "x"})
    assert out.startswith("tool error:")
    assert agent.run_tool("nonexistent", {}).startswith("unknown tool:")


def test_every_tool_the_model_is_offered_can_actually_be_run():
    """A tool in TOOLS with no handler is a tool the model will confidently
    call and always fail at."""
    for tool in agent.TOOLS:
        assert tool["name"] in agent._HANDLERS
        assert tool["description"]                    # the model reads this


# ---- memory ----------------------------------------------------------------
def test_memory_keeps_a_session_apart_from_another():
    memory.save("a", [{"role": "user", "content": "one"}])
    memory.save("b", [{"role": "user", "content": "two"}])
    assert memory.load("a")[0]["content"] == "one"
    assert memory.load("b")[0]["content"] == "two"
    assert memory.load("never-seen") == []


# ---- the web service and streaming -----------------------------------------
# The tests for /chat, /chat/stream and /health live in the solution branch.
# They cannot pass until you have built app/main.py and app/stream.py, and a
# suite that fails from the first minute teaches you to ignore red.
#
# `make check-week-01` is your test for this week: it asserts every route, the
# session behaviour, the SSE frame sequence and the container, and each failure
# names the exact thing to fix.
#
# Once it is green, compare your work against the full suite:
#
#     git diff week-01-package..week-01-solution -- tests/test_app.py
