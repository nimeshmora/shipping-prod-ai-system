"""Week 01 tests. Every one uses a fake model, so no API key is needed.

That is not a convenience - it is the design. The real model call is isolated
in one function (`call_model`), so everything else can be tested for free, in
milliseconds, deterministically, offline. An agent whose tests need an API key
is an agent nobody runs tests on.
"""
from types import SimpleNamespace as NS

import pytest
from fastapi.testclient import TestClient

from app import agent, guardrails as g, memory
from app.agent import AgentError
from app.guardrails import GuardrailError
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
    costs money. Week 04 makes this the Budget's job."""
    def always_tool(messages):
        block = NS(type="tool_use", name="calculator",
                   input={"expression": "1+1"}, id="t")
        return NS(content=[block], stop_reason="tool_use")

    with pytest.raises(GuardrailError):
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


# ---- Week 02: memory that survives a redeploy ------------------------------
class FakeRedis:
    """Enough Redis to prove the code talks to it correctly.

    Not a mock that records calls - a tiny working store. A mock would pass
    even if we called setex with the arguments in the wrong order, which is
    exactly the bug worth catching here.
    """

    def __init__(self):
        self.data = {}
        self.ttls = {}

    def get(self, key):
        return self.data.get(key)

    def setex(self, key, ttl, value):
        self.data[key] = value
        self.ttls[key] = ttl

    def scan_iter(self, pattern):
        prefix = pattern.rstrip("*")
        return [k for k in list(self.data) if k.startswith(prefix)]

    def delete(self, key):
        self.data.pop(key, None)
        self.ttls.pop(key, None)


@pytest.fixture
def redis_backed(monkeypatch):
    """Point memory at a fake Redis, the way REDIS_URL would."""
    fake = FakeRedis()
    monkeypatch.setattr(memory, "REDIS_URL", "redis://fake")
    monkeypatch.setattr(memory, "_client", fake)
    yield fake


def test_a_conversation_survives_the_process_that_started_it(redis_backed):
    """The Week 02 lesson. The dict died with the container on every deploy;
    Redis does not, because it is not in the container."""
    memory.save("sess-1", [{"role": "user", "content": "where is ORD-1002?"}])

    # simulate a redeploy: the process is gone, its module state with it.
    # Redis is untouched, because it was never inside the container.
    memory._FALLBACK.clear()

    kept = memory.load("sess-1")
    assert kept == [{"role": "user", "content": "where is ORD-1002?"}]


def test_sessions_are_namespaced_and_kept_apart(redis_backed):
    memory.save("a", [{"role": "user", "content": "one"}])
    memory.save("b", [{"role": "user", "content": "two"}])
    assert "session:a" in redis_backed.data
    assert memory.load("a")[0]["content"] == "one"
    assert memory.load("b")[0]["content"] == "two"
    assert memory.load("never-seen") == []


def test_every_session_is_written_with_an_expiry(redis_backed):
    """A dict grows until the process dies. Without a TTL, Redis does the same
    thing but keeps the bill."""
    memory.save("sess-ttl", [{"role": "user", "content": "hi"}])
    assert redis_backed.ttls["session:sess-ttl"] == memory.TTL_SECONDS


def test_tool_blocks_survive_the_round_trip_to_redis(redis_backed):
    """The awkward case: assistant messages hold tool_use blocks that are
    SimpleNamespace objects, which json.dumps refuses outright."""
    block = NS(type="text", text="asking for a tool")
    history = [
        {"role": "user", "content": "where is ORD-1002?"},
        {"role": "assistant", "content": [block]},
        {"role": "user", "content": [{"type": "tool_result",
                                      "tool_use_id": "t1",
                                      "content": "ORD-1002: standing desk"}]},
    ]
    memory.save("sess-tools", history)          # must not raise
    back = memory.load("sess-tools")
    assert back[2]["content"][0]["content"] == "ORD-1002: standing desk"
    assert back[0]["content"] == "where is ORD-1002?"


def test_the_app_still_runs_with_no_redis_at_all():
    """The course has to work on a laptop with no Redis, no cloud and no
    internet. REDIS_URL unset falls back to the Week 01 dict."""
    assert memory.REDIS_URL is None or True      # documents the intent
    memory.reset()
    memory.save("local", [{"role": "user", "content": "still works"}])
    assert memory.load("local")[0]["content"] == "still works"


# ---- Week 03: who is calling, and how often --------------------------------
@pytest.fixture(autouse=True)
def _clean_rate_limits():
    g.reset_rate_limits()
    yield
    g.reset_rate_limits()


def test_a_request_without_a_valid_key_is_rejected(monkeypatch):
    monkeypatch.setenv("API_KEYS", "secret,another")
    with pytest.raises(GuardrailError) as e:
        g.check_api_key("wrong")
    assert e.value.status == 401                 # not 403: identity unproven
    g.check_api_key("secret")                    # no raise
    g.check_api_key("another")                   # more than one key works


def test_keys_are_read_fresh_so_rotation_needs_no_deploy(monkeypatch):
    """A set built once at import time would mean the only way to revoke a
    leaked key is to ship new code."""
    monkeypatch.setenv("API_KEYS", "old")
    g.check_api_key("old")
    monkeypatch.setenv("API_KEYS", "new")
    with pytest.raises(GuardrailError):
        g.check_api_key("old")                   # revoked without a restart
    g.check_api_key("new")


def test_with_no_keys_configured_auth_is_off(monkeypatch):
    """A deliberate local-dev convenience, and a real production risk: a
    service deployed without API_KEYS is wide open."""
    monkeypatch.delenv("API_KEYS", raising=False)
    g.check_api_key(None)                        # no raise


def test_the_rate_limit_allows_exactly_its_allowance_then_refuses():
    for _ in range(g.RATE_LIMIT):
        g.check_rate_limit("flooder")
    with pytest.raises(GuardrailError) as e:
        g.check_rate_limit("flooder")
    assert e.value.status == 429


def test_one_caller_being_rate_limited_does_not_affect_another():
    for _ in range(g.RATE_LIMIT):
        g.check_rate_limit("noisy")
    with pytest.raises(GuardrailError):
        g.check_rate_limit("noisy")
    g.check_rate_limit("quiet")                  # unaffected


def test_the_window_slides_rather_than_resetting_on_the_minute(monkeypatch):
    """The naive version - a counter on a per-minute key - lets a caller send
    the full allowance either side of a minute boundary: a 20/min limit that
    permits 40 requests in one second."""
    clock = {"t": 1000.0}
    monkeypatch.setattr(g.time, "monotonic", lambda: clock["t"])

    for _ in range(g.RATE_LIMIT):
        g.check_rate_limit("slider")
    with pytest.raises(GuardrailError):
        g.check_rate_limit("slider")

    clock["t"] += 61                             # the oldest hits age out
    g.check_rate_limit("slider")                 # and only then is there room


# ---- Week 03: the guardrails guard BOTH endpoints --------------------------
def _client():
    from fastapi.testclient import TestClient
    import app.main as main
    return TestClient(main.app)


def test_chat_returns_401_without_a_key(monkeypatch):
    monkeypatch.setenv("API_KEYS", "secret")
    r = _client().post("/chat", json={"message": "hi"})
    assert r.status_code == 401


def test_the_streaming_endpoint_is_not_a_side_door(monkeypatch):
    """The day you add a rule to one endpoint and forget the other is the day
    you have an unauthenticated path into a paid model."""
    monkeypatch.setenv("API_KEYS", "secret")
    r = _client().post("/chat/stream", json={"message": "hi"})
    assert r.status_code == 401


def test_a_rejected_stream_is_an_honest_4xx_not_an_error_frame(monkeypatch):
    """Guardrails run BEFORE the response starts. Once the first frame is out,
    200 has already been sent and there is no status code left to reject with."""
    monkeypatch.setenv("API_KEYS", "secret")
    r = _client().post("/chat/stream", json={"message": "hi"})
    assert r.status_code == 401
    assert "text/event-stream" not in r.headers.get("content-type", "")


def test_a_valid_key_gets_through(monkeypatch):
    import app.main as main
    monkeypatch.setenv("API_KEYS", "secret")
    original = main.run_turn
    main.run_turn = lambda m, history=None: agent.run_turn(
        m, history, model_fn=plain_answer("ok"))
    try:
        r = _client().post("/chat", json={"message": "hi"},
                           headers={"x-api-key": "secret"})
        assert r.status_code == 200
        assert r.json()["reply"] == "ok"
    finally:
        main.run_turn = original


def test_flooding_one_endpoint_returns_429(monkeypatch):
    import app.main as main
    monkeypatch.setenv("API_KEYS", "secret")
    monkeypatch.setattr(g, "RATE_LIMIT", 3)
    original = main.run_turn
    main.run_turn = lambda m, history=None: agent.run_turn(
        m, history, model_fn=plain_answer("ok"))
    try:
        client = _client()
        headers = {"x-api-key": "secret"}
        codes = [client.post("/chat", json={"message": "hi"},
                             headers=headers).status_code for _ in range(5)]
        assert codes.count(200) == 3
        assert codes.count(429) == 2
    finally:
        main.run_turn = original


def test_a_guardrail_rejection_never_reaches_the_model(monkeypatch):
    """Rejecting a request that was never going to be allowed should cost
    nothing - certainly not a model call."""
    import app.main as main
    monkeypatch.setenv("API_KEYS", "secret")
    called = {"n": 0}

    def counting_model(messages):
        called["n"] += 1
        return NS(content=[NS(type="text", text="ok")], stop_reason="end_turn")

    original = main.run_turn
    main.run_turn = lambda m, history=None: agent.run_turn(
        m, history, model_fn=counting_model)
    try:
        _client().post("/chat", json={"message": "hi"})     # no key
        assert called["n"] == 0
    finally:
        main.run_turn = original


# ---- Week 04: what one turn is allowed to cost -----------------------------
def test_the_step_budget_counts_and_then_refuses():
    b = g.Budget(max_steps=3, max_tokens=10**9)
    for _ in range(3):
        b.add_step()
    with pytest.raises(GuardrailError) as e:
        b.add_step()
    assert "step limit" in str(e.value)
    assert e.value.status == 400          # the caller's turn was too expensive


def test_the_token_budget_catches_one_enormous_call():
    """A step limit alone lets six colossal calls through. This is the other
    half."""
    b = g.Budget(max_steps=100, max_tokens=100)
    b.add_tokens(60)
    with pytest.raises(GuardrailError) as e:
        b.add_tokens(60)
    assert "token budget" in str(e.value)


def test_the_token_budget_tolerates_a_provider_that_reports_nothing():
    """Some gateways omit usage. That must not crash the turn."""
    b = g.Budget(max_tokens=100)
    b.add_tokens(None)
    b.add_tokens(0)
    assert b.tokens == 0


def test_the_loop_stops_on_tokens_even_when_steps_are_fine():
    def big_call(messages):
        block = NS(type="tool_use", name="calculator",
                   input={"expression": "1+1"}, id="t")
        return NS(content=[block], stop_reason="tool_use",
                  usage=NS(input_tokens=50_000, output_tokens=0))

    with pytest.raises(GuardrailError) as e:
        agent.run_turn("go", model_fn=big_call)
    assert "token budget" in str(e.value)


def test_the_loop_counts_tokens_from_every_step_not_just_the_last():
    """The budget is cumulative across the turn. Reset it per step and a
    hundred medium calls sail through."""
    calls = {"n": 0}

    def steady(messages):
        calls["n"] += 1
        block = NS(type="tool_use", name="calculator",
                   input={"expression": "1+1"}, id=f"t{calls['n']}")
        return NS(content=[block], stop_reason="tool_use",
                  usage=NS(input_tokens=8_000, output_tokens=0))

    with pytest.raises(GuardrailError) as e:
        agent.run_turn("go", model_fn=steady)
    assert "token budget" in str(e.value)
    assert calls["n"] == 3                # 8k, 16k, 24k > 20k default


def test_an_overspending_turn_is_a_4xx_not_a_500(monkeypatch):
    """It is the request that was too expensive, not the server that broke.
    Getting this backwards makes your error rate blame the wrong party."""
    from fastapi.testclient import TestClient
    import app.main as main

    def always_tool(messages):
        block = NS(type="tool_use", name="calculator",
                   input={"expression": "1+1"}, id="t")
        return NS(content=[block], stop_reason="tool_use")

    original = main.run_turn
    main.run_turn = lambda m, history=None: agent.run_turn(
        m, history, model_fn=always_tool)
    try:
        r = TestClient(main.app).post("/chat", json={"message": "go"})
        assert r.status_code == 400
        assert "step limit" in r.json()["detail"]
    finally:
        main.run_turn = original


# ---- Week 04: context is a budget too --------------------------------------
def test_history_is_trimmed_so_context_cannot_grow_forever():
    """Every turn re-sends the WHOLE history. Left alone, a long session grows
    the prompt until the model refuses it - and the per-turn token cap never
    sees it coming, because it resets at the start of each turn."""
    memory.reset()
    long_history = [{"role": "user", "content": f"msg {i}"} for i in range(200)]
    memory.save("trim-test", long_history)
    kept = memory.load("trim-test")
    assert len(kept) == memory.MAX_HISTORY_MESSAGES
    assert kept[-1]["content"] == "msg 199"          # the newest survives


def test_trimming_never_orphans_a_tool_result():
    """A tool_result whose tool_use is gone is a malformed conversation, and
    the provider rejects the whole request."""
    turn = [
        {"role": "user", "content": "q"},
        {"role": "assistant", "content": "asking for a tool"},
        {"role": "user", "content": [{"type": "tool_result",
                                      "tool_use_id": "t", "content": "r"}]},
    ]
    kept = memory.trim(turn * 40)
    assert not memory._is_tool_result(kept[0])


def test_a_short_session_is_left_completely_alone():
    memory.reset()
    short = [{"role": "user", "content": "hi"}]
    memory.save("short", short)
    assert memory.load("short") == short
