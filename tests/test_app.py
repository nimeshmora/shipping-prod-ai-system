"""Week 01 tests. Every one uses a fake model, so no API key is needed.

That is not a convenience - it is the design. The real model call is isolated
in one function (`call_model`), so everything else can be tested for free, in
milliseconds, deterministically, offline. An agent whose tests need an API key
is an agent nobody runs tests on.
"""
from types import SimpleNamespace as NS

import pytest
from fastapi.testclient import TestClient

from app import agent, memory
from app.agent import AgentError
from app.main import app as fastapi_app


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


# ---- the web service -------------------------------------------------------
def _client_with_fake_model(text="Your order is on its way"):
    import app.main as main
    main.run_turn = lambda m, history=None: agent.run_turn(
        m, history, model_fn=plain_answer(text))
    return TestClient(fastapi_app)


def test_health_is_up():
    assert TestClient(fastapi_app).get("/health").json() == {"status": "ok"}


def test_chat_answers_and_returns_a_session_id():
    import app.main as main
    original = main.run_turn
    try:
        client = _client_with_fake_model()
        body = client.post("/chat", json={"message": "hi"}).json()
        assert body["reply"] == "Your order is on its way"
        assert body["session_id"]
    finally:
        main.run_turn = original


def test_the_same_session_id_continues_the_conversation():
    import app.main as main
    original = main.run_turn
    try:
        client = _client_with_fake_model()
        first = client.post("/chat", json={"message": "hi"}).json()
        sid = first["session_id"]
        client.post("/chat", json={"message": "again", "session_id": sid})
        assert len(memory.load(sid)) == 4        # both turns are remembered
    finally:
        main.run_turn = original


def test_a_bad_request_body_is_rejected_before_our_code_runs():
    """Pydantic validates ChatRequest, so this never reaches the agent."""
    assert TestClient(fastapi_app).post("/chat", json={}).status_code == 422


def test_an_internal_failure_never_leaks_details_to_the_caller():
    import app.main as main
    original = main.run_turn

    def boom(m, history=None):
        raise RuntimeError("connection string: postgres://user:hunter2@db")

    main.run_turn = boom
    try:
        client = TestClient(fastapi_app, raise_server_exceptions=False)
        r = client.post("/chat", json={"message": "hi"})
        assert r.status_code == 500
        assert "hunter2" not in r.text            # the secret stayed inside
        assert r.json()["detail"] == "internal error"
    finally:
        main.run_turn = original


# ---- streaming -------------------------------------------------------------
def _frames(lines):
    """Parse SSE lines into (event, data) pairs."""
    import json
    out, event = [], None
    for line in lines:
        if line.startswith("event: "):
            event = line[7:]
        elif line.startswith("data: ") and event:
            out.append((event, json.loads(line[6:])))
    return out


def test_the_stream_sends_start_then_tokens_then_done():
    import app.main as main
    original = main.run_turn
    main.run_turn = lambda m, history=None: agent.run_turn(
        m, history, model_fn=plain_answer("Your standing desk arrives Thursday"))
    try:
        client = TestClient(fastapi_app)
        with client.stream("POST", "/chat/stream",
                           json={"message": "where is it?"}) as r:
            assert r.status_code == 200
            assert "text/event-stream" in r.headers["content-type"]
            frames = _frames([l for l in r.iter_lines() if l])
    finally:
        main.run_turn = original

    events = [e for e, _ in frames]
    assert events[0] == "start"
    assert events[-1] == "done"
    assert "token" in events
    text = "".join(d["text"] for e, d in frames if e == "token")
    assert "standing desk" in text


def test_a_failure_mid_stream_arrives_as_an_error_frame():
    """Once streaming starts the 200 is already sent, so there is no status
    code left to fail with. The error has to travel as a frame."""
    import app.main as main
    original = main.run_turn

    def boom(m, history=None):
        raise RuntimeError("the provider is down")

    main.run_turn = boom
    try:
        client = TestClient(fastapi_app)
        with client.stream("POST", "/chat/stream",
                           json={"message": "hi"}) as r:
            assert r.status_code == 200            # already committed
            frames = _frames([l for l in r.iter_lines() if l])
    finally:
        main.run_turn = original

    assert [e for e, _ in frames][-1] == "error"


def test_the_stream_does_not_buffer_itself_into_one_lump():
    """X-Accel-Buffering tells proxies not to hold the response. Without it a
    streamed answer arrives all at once and the feature is invisibly dead."""
    import app.main as main
    original = main.run_turn
    main.run_turn = lambda m, history=None: agent.run_turn(
        m, history, model_fn=plain_answer("a b c d e f g h i j k l m n o p"))
    try:
        client = TestClient(fastapi_app)
        with client.stream("POST", "/chat/stream", json={"message": "hi"}) as r:
            assert r.headers["x-accel-buffering"] == "no"
            assert r.headers["cache-control"] == "no-cache"
            frames = _frames([l for l in r.iter_lines() if l])
    finally:
        main.run_turn = original

    # a long answer must arrive in more than one piece
    assert len([e for e, _ in frames if e == "token"]) > 1


# ---- the model boundary ----------------------------------------------------
def test_the_system_prompt_is_sent_on_every_turn():
    """The model has no memory, so its standing instructions have to be
    re-sent every single time."""
    seen = {}

    class FakeClient:
        def __init__(self):
            self.chat = self
            self.completions = self

        def create(self, model, messages, **kw):
            seen["messages"] = messages
            seen["timeout"] = kw.get("timeout")
            msg = type("M", (), {"content": "ok", "tool_calls": None})()
            choice = type("C", (), {"message": msg})()
            return type("R", (), {"choices": [choice]})()

    original = agent._client
    agent._client = lambda: FakeClient()
    try:
        agent.call_model([{"role": "user", "content": "hi"}])
    finally:
        agent._client = original

    assert seen["messages"][0]["role"] == "system"
    assert "customer support" in seen["messages"][0]["content"].lower()
    assert seen["timeout"] == agent.MODEL_TIMEOUT_SECONDS   # calls are bounded


def test_a_missing_api_key_says_exactly_how_to_fix_it():
    """The most common error in this course. The message has to be the
    instructions, not just the diagnosis."""
    import os
    saved = os.environ.pop("OPENROUTER_API_KEY", None)
    try:
        with pytest.raises(AgentError) as e:
            agent._client()
        assert "source .env" in str(e.value)
    finally:
        if saved is not None:
            os.environ["OPENROUTER_API_KEY"] = saved
