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
    reply, history, _ = agent.run_turn(
        "where is order ORD-1002?",
        model_fn=tool_then_answer("lookup_order", {"order_id": "ORD-1002"}))
    assert "standing desk" in reply
    # four moves: user asks, model asks for a tool, tool answers, model replies
    assert len(history) == 4


def test_the_loop_returns_straight_away_when_no_tool_is_needed():
    reply, history, _ = agent.run_turn("hello", model_fn=plain_answer("hi there"))
    assert reply == "hi there"
    assert len(history) == 2


def test_history_carries_forward_into_the_next_turn():
    _, history, _t = agent.run_turn("hello", model_fn=plain_answer("hi"))
    _, history2, _t2 = agent.run_turn("again", history, model_fn=plain_answer("ok"))
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
    from app import monitor
    monitor.reset()
    main.run_turn = lambda m, history=None, trace=None: agent.run_turn(
        m, history, model_fn=plain_answer(text), trace=trace)
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

    def boom(m, history=None, trace=None):
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
    main.run_turn = lambda m, history=None, trace=None: agent.run_turn(
        m, history, model_fn=plain_answer("Your standing desk arrives Thursday"),
        trace=trace)
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

    def boom(m, history=None, trace=None):
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
    main.run_turn = lambda m, history=None, trace=None: agent.run_turn(
        m, history, model_fn=plain_answer("a b c d e f g h i j k l m n o p"),
        trace=trace)
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
    from app import monitor
    monitor.reset()
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
    main.run_turn = lambda m, history=None, trace=None: agent.run_turn(
        m, history, model_fn=plain_answer("ok"), trace=trace)
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
    main.run_turn = lambda m, history=None, trace=None: agent.run_turn(
        m, history, model_fn=plain_answer("ok"), trace=trace)
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
    main.run_turn = lambda m, history=None, trace=None: agent.run_turn(
        m, history, model_fn=counting_model, trace=trace)
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
    main.run_turn = lambda m, history=None, trace=None: agent.run_turn(
        m, history, model_fn=always_tool, trace=trace)
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


# ---- Week 05: one trace per turn -------------------------------------------
def test_the_trace_shows_where_the_time_went():
    """A turn that took 8 seconds is useless information on its own. The trace
    must say WHICH part was slow - the model, or your own tool."""
    from app import trace
    import time as _time

    state = {"n": 0}

    def slow_first_call(messages):
        state["n"] += 1
        if state["n"] == 1:
            _time.sleep(0.05)
            block = NS(type="tool_use", name="lookup_order",
                       input={"order_id": "ORD-1002"}, id="t1")
            return NS(content=[block], stop_reason="tool_use", usage=None)
        return NS(content=[NS(type="text", text="done")],
                  stop_reason="end_turn", usage=None)

    t = trace.new_trace("s")
    agent.run_turn("where is ORD-1002?", model_fn=slow_first_call, trace=t)

    assert len(t["step_ms"]) == 2         # one entry per trip round the loop
    assert t["step_ms"][0] >= 50          # the slow one is visible
    assert len(t["tool_ms"]) == 1         # and the tool was timed separately
    assert t["tools_used"] == ["lookup_order"]


def test_a_broken_tool_is_recorded_even_though_the_turn_succeeds():
    """A tool that fails hands its error text back to the model, so the turn
    still returns 200. Without tool_errors the breakage is invisible."""
    from app import trace
    state = {"n": 0}

    def asks_for_a_broken_call(messages):
        state["n"] += 1
        if state["n"] == 1:
            block = NS(type="tool_use", name="lookup_order",
                       input={"wrong_argument": "x"}, id="t1")
            return NS(content=[block], stop_reason="tool_use", usage=None)
        return NS(content=[NS(type="text", text="sorry, I could not check")],
                  stop_reason="end_turn", usage=None)

    t = trace.new_trace("s")
    reply, _, t = agent.run_turn("where is my order?",
                                 model_fn=asks_for_a_broken_call, trace=t)

    assert reply                             # the turn "succeeded"
    assert t["error"] is None                # no top-level error either
    assert t["tool_errors"] == ["lookup_order"]   # but it is recorded


def test_secrets_are_redacted_before_anything_is_written():
    from app import trace
    red = trace._redact({"api_key": "sk-secret", "authorization": "Bearer x",
                         "ok": 1})
    assert red["api_key"] == "[redacted]"
    assert red["authorization"] == "[redacted]"
    assert red["ok"] == 1


def test_token_counters_are_not_mistaken_for_secrets():
    """_REDACT matches on substring, so anything with 'token' in the name is
    redacted by default. The counters must be allowed through, or the trace
    lies about its own inputs."""
    from app import trace
    red = trace._redact({"input_tokens": 120, "output_tokens": 30,
                         "token_count": 150, "api_token": "sk-secret"})
    assert red["input_tokens"] == 120
    assert red["output_tokens"] == 30
    assert red["token_count"] == 150
    assert red["api_token"] == "[redacted]"


def test_cost_uses_the_real_input_output_split():
    """Output tokens cost 3-5x input. A blended rate badly overstates an
    input-heavy agent, which is most of them."""
    from app import trace
    t = trace.new_trace("s")
    t["input_tokens"], t["output_tokens"] = 900_000, 100_000
    trace.emit(t)
    assert t["cost_usd"] == trace.cost_of(900_000, 100_000)
    assert t["cost_usd"] < trace.estimate_cost(1_000_000)


def test_a_failed_turn_is_marked_ERROR_for_the_log_platform():
    """Cloud Logging reads a field called "severity" to decide whether a line
    is routine. Without it every line lands as INFO and nothing pages."""
    from app import trace
    ok = trace.new_trace("s")
    trace.emit(ok)
    assert ok["severity"] == "INFO"

    bad = trace.new_trace("s")
    bad["error"] = "provider is down"
    trace.emit(bad)
    assert bad["severity"] == "ERROR"


def test_emit_is_idempotent_so_a_turn_is_logged_once():
    from app import trace
    t = trace.new_trace("s")
    trace.emit(t)
    first = t["duration_ms"]
    trace.emit(t)
    assert t["duration_ms"] == first


# ---- Week 05b: monitoring, not just telemetry ------------------------------
def _fake_turn(error=None, ms=1000, steps=2, cost=0.01, tool_errors=None):
    return {"error": error, "duration_ms": ms, "steps": steps,
            "cost_usd": cost, "step_ms": [ms], "model_calls": [],
            "tool_errors": tool_errors or []}


def test_the_monitor_is_quiet_when_the_agent_is_healthy():
    from app import monitor
    monitor.reset()
    for _ in range(30):
        monitor.record(_fake_turn())
    assert monitor.alerts() == []
    assert monitor.stats()["error_rate"] == 0.0


def test_the_monitor_says_nothing_before_it_has_enough_data():
    """Two failures out of three is not an incident, it is a coincidence."""
    from app import monitor
    monitor.reset()
    for _ in range(3):
        monitor.record(_fake_turn(error="boom"))
    assert monitor.alerts() == []


def test_the_monitor_alerts_on_a_degrading_agent():
    from app import monitor
    monitor.reset()
    for i in range(30):
        monitor.record(_fake_turn(error="boom" if i % 2 else None,
                                  ms=40000, steps=6))
    fired = " ".join(monitor.alerts())
    assert "error rate" in fired
    assert "p95 latency" in fired
    assert "steps" in fired


def test_broken_tools_raise_an_alert_even_when_every_turn_succeeds():
    """The signal that only exists here. Every turn returned 200; a third of
    them had a tool fail."""
    from app import monitor
    monitor.reset()
    for i in range(20):
        monitor.record(_fake_turn(
            tool_errors=["lookup_order"] if i % 3 == 0 else []))
    assert monitor.stats()["error_rate"] == 0.0
    assert any("tool fail" in a for a in monitor.alerts())


def test_the_window_only_keeps_the_most_recent_turns():
    from app import monitor
    monitor.reset()
    for _ in range(monitor.WINDOW + 50):
        monitor.record(_fake_turn())
    assert monitor.stats()["turns"] == monitor.WINDOW


def test_metrics_reports_status_and_alerts():
    from fastapi.testclient import TestClient
    from app import monitor
    import app.main as main
    monitor.reset()
    body = TestClient(main.app).get("/metrics").json()
    assert body["status"] == "ok"
    assert "alerts" in body


def test_an_unexpected_crash_is_recorded_so_the_dashboard_cannot_lie():
    """THE Week 05 lesson. If an unexpected exception escapes before the trace
    is filled, a total outage is reported as a 0% error rate. Every request
    here fails; /metrics must say so."""
    from fastapi.testclient import TestClient
    import app.main as main
    from app import monitor
    monitor.reset()

    def boom(m, history=None, trace=None):
        raise RuntimeError("the model provider is down")

    original = main.run_turn
    main.run_turn = boom
    try:
        client = TestClient(main.app, raise_server_exceptions=False)
        for _ in range(12):
            assert client.post("/chat", json={"message": "hi"}).status_code == 500
        body = client.get("/metrics").json()
        assert body["error_rate"] == 1.0          # not 0.0
        assert body["status"] == "degraded"
        assert any("error rate" in a for a in body["alerts"])
    finally:
        main.run_turn = original
        monitor.reset()


def test_a_streamed_turn_is_recorded_exactly_once():
    from fastapi.testclient import TestClient
    import app.main as main
    from app import monitor
    monitor.reset()
    original = main.run_turn
    main.run_turn = lambda m, history=None, trace=None: agent.run_turn(
        m, history, model_fn=plain_answer("hi there"), trace=trace)
    try:
        client = TestClient(main.app)
        for _ in range(3):
            with client.stream("POST", "/chat/stream",
                               json={"message": "hi"}) as r:
                list(r.iter_lines())
        assert monitor.stats()["turns"] == 3        # not 6
    finally:
        main.run_turn = original
        monitor.reset()


def test_the_done_frame_carries_real_numbers_not_zeros():
    """The trace is finalised before `done` is built. Without that, cost and
    duration are still the zeros the trace was born with."""
    from fastapi.testclient import TestClient
    import app.main as main
    from app import monitor
    monitor.reset()

    def model(messages):
        return NS(content=[NS(type="text", text="Order ORD-1002 is shipped")],
                  stop_reason="end_turn",
                  usage=NS(input_tokens=140, output_tokens=25))

    original = main.run_turn
    main.run_turn = lambda m, history=None, trace=None: agent.run_turn(
        m, history, model_fn=model, trace=trace)
    try:
        client = TestClient(main.app)
        with client.stream("POST", "/chat/stream",
                           json={"message": "hi"}) as r:
            frames = _frames([l for l in r.iter_lines() if l])
    finally:
        main.run_turn = original
        monitor.reset()

    done = [d for e, d in frames if e == "done"][0]
    assert done["tokens"] == 165
    assert done["cost_usd"] > 0


# ---- Week 05: OpenTelemetry, the same trace in the industry's shape --------
def test_the_app_works_perfectly_with_otel_switched_off():
    """OTel is a bonus layer, never a dependency. Week 05 must keep running on
    a laptop with no key, no cloud and no internet."""
    from app import otel
    assert otel.ENABLED is False
    with otel.span("anything", {"a": 1}) as s:
        s.set("b", 2)
        s.failed("even this")


def test_a_turn_produces_one_parent_span_with_children():
    import os
    import subprocess
    import sys
    # A subprocess: the tracer provider is global and set once per process.
    code = (
        "from types import SimpleNamespace as NS\n"
        "from app import otel, trace as tr\n"
        "from app.agent import run_turn\n"
        "st={'n':0}\n"
        "def m(msgs):\n"
        "    st['n']+=1\n"
        "    if st['n']==1:\n"
        "        b=NS(type='tool_use',name='lookup_order',"
        "input={'order_id':'ORD-1002'},id='t')\n"
        "        return NS(content=[b],stop_reason='tool_use',usage=None)\n"
        "    return NS(content=[NS(type='text',text='ok')],"
        "stop_reason='end_turn',usage=None)\n"
        "with otel.span('chat_turn',{'turn.id':'abc'}):\n"
        "    run_turn('hi',model_fn=m,trace=tr.new_trace('s'))\n"
        "from opentelemetry import trace as ot\n"
        "ot.get_tracer_provider().force_flush()\n"
    )
    env = {**os.environ, "OTEL_ENABLED": "1"}
    out = subprocess.run([sys.executable, "-c", code], capture_output=True,
                         text=True, env=env).stdout

    assert '"name": "chat_turn"' in out       # the turn itself
    assert '"name": "model_call"' in out      # each trip round the loop
    assert '"name": "tool"' in out            # and each tool call
    assert '"parent_id": null' in out         # chat_turn is the root
