"""Guided checkpoints. Run one per week to confirm that week's capability works.

    python -m checks.check 00      # the loop you start from
    python -m checks.check 06      # this week
    python -m checks.check setup   # tests all pass

Each check uses a fake model, so it runs with no API key and no cloud, and
prints a plain-English PASS/FAIL. Green means done - not "it looked right on
my screen".
"""
import sys
from types import SimpleNamespace as NS


def _ok(msg): print(f"  PASS  {msg}")


def _no(msg):
    print(f"  FAIL  {msg}")
    raise SystemExit(1)


def _plain_model(text="hello"):
    def model(messages):
        return NS(content=[NS(type="text", text=text)], stop_reason="end_turn")
    return model


def _tool_then_answer(name, args):
    """A stand-in model that asks for one tool, then reports what it got."""
    st = {"n": 0}

    def model(messages):
        st["n"] += 1
        if st["n"] == 1:
            b = NS(type="tool_use", name=name, input=args, id="t1")
            return NS(content=[b], stop_reason="tool_use")
        result = messages[-1]["content"][0]["content"]
        return NS(content=[NS(type="text", text=f"It is {result}.")],
                  stop_reason="end_turn")
    return model


def check_00():
    print("Week 00: the loop runs a tool then answers")
    from app.agent import run_turn
    # run_turn returns (reply, history) until Week 05 adds the trace and makes
    # it (reply, history, trace). This checkpoint spans that change, so it
    # accepts either.
    result = run_turn(
        "where is order ORD-1002?",
        model_fn=_tool_then_answer("lookup_order", {"order_id": "ORD-1002"}))
    reply, hist = result[0], result[1]
    (_ok if "standing desk" in reply else _no)(
        "the agent looked up a real order it could not have known")
    (_ok if len(hist) == 4 else _no)("history has all four moves")
    reply = run_turn(
        "what is 12*41?",
        model_fn=_tool_then_answer("calculator", {"expression": "12 * 41"}))[0]
    (_ok if "492" in reply else _no)("and the calculator still works")


def check_01():
    print("Week 01: the agent is a web service, and it streams")
    try:
        from fastapi.testclient import TestClient
    except ImportError:
        _no("fastapi is not installed - run: make install")

    # --- the service exists at all -----------------------------------------
    try:
        import app.main as main
    except Exception as e:
        _no(f"app/main.py does not import yet: {type(e).__name__}: {e}")

    if not hasattr(main, "app"):
        _no("app/main.py must define `app`, the FastAPI application")
    _ok("app/main.py imports and defines `app`")

    import app.agent as agent
    from app import memory

    # Swap in a fake model so this needs no API key.
    original = main.run_turn
    # Week 05 gives run_turn a `trace` parameter. Accept and forward it only
    # when the real function takes it, so this works either side of that.
    import inspect
    _takes_trace = "trace" in inspect.signature(agent.run_turn).parameters

    def _fake_run_turn(m, history=None, trace=None):
        model = _plain_model("Your order is on its way")
        if _takes_trace:
            return agent.run_turn(m, history, model_fn=model, trace=trace)
        return agent.run_turn(m, history, model_fn=model)

    main.run_turn = _fake_run_turn
    try:
        memory.reset()
        c = TestClient(main.app)

        # --- /health --------------------------------------------------------
        r = c.get("/health")
        if r.status_code != 200:
            _no(f"GET /health returned {r.status_code}, expected 200")
        if r.json() != {"status": "ok"}:
            _no(f'GET /health returned {r.json()}, expected {{"status": "ok"}}')
        _ok('GET /health returns {"status": "ok"}')

        # --- /chat ----------------------------------------------------------
        r = c.post("/chat", json={"message": "where is my order?"})
        if r.status_code != 200:
            _no(f"POST /chat returned {r.status_code}, expected 200")
        body = r.json()
        if "reply" not in body:
            _no(f'POST /chat must return a "reply" key; got {sorted(body)}')
        _ok("POST /chat returns a reply")
        if "session_id" not in body:
            _no(f'POST /chat must return a "session_id" key; got {sorted(body)}')
        _ok("and a session_id, so the caller can continue the conversation")

        # --- memory across turns -------------------------------------------
        sid = body["session_id"]
        c.post("/chat", json={"message": "and again", "session_id": sid})
        if len(memory.load(sid)) != 4:
            _no("sending the same session_id back must continue the same "
                f"conversation; history has {len(memory.load(sid))} messages, "
                "expected 4")
        _ok("sending that session_id back continues the same conversation")

        # --- a bad body is rejected ----------------------------------------
        if c.post("/chat", json={}).status_code != 422:
            _no("POST /chat with no message should be rejected with 422 - "
                "declare `message: str` on a pydantic BaseModel")
        _ok("a request with no message is rejected with 422")

        # --- /chat/stream ---------------------------------------------------
        with c.stream("POST", "/chat/stream",
                      json={"message": "where is my order?"}) as sr:
            if sr.status_code != 200:
                _no(f"POST /chat/stream returned {sr.status_code}, expected 200")
            ctype = sr.headers.get("content-type", "")
            if "text/event-stream" not in ctype:
                _no(f"POST /chat/stream must be text/event-stream, got {ctype!r}")
            headers = dict(sr.headers)
            lines = [l for l in sr.iter_lines() if l]
        _ok("POST /chat/stream returns text/event-stream")

        events = [l[7:] for l in lines if l.startswith("event: ")]
        if not events:
            _no("no SSE frames arrived - each frame is "
                '"event: <name>\\ndata: <json>\\n\\n"')
        if events[0] != "start":
            _no(f'the first frame must be "start", got {events[0]!r}')
        _ok("it opens with a start frame")
        if "token" not in events:
            _no(f'the answer must arrive in "token" frames; got {events}')
        _ok("the answer arrives as token frames")
        if events[-1] != "done":
            _no(f'the last frame must be "done", got {events[-1]!r}')
        _ok("and closes with a done frame")

        if headers.get("x-accel-buffering") != "no":
            _no('the stream needs the header "X-Accel-Buffering: no", or a '
                "proxy will buffer it into one lump and streaming is "
                "invisibly dead")
        _ok("X-Accel-Buffering: no is set, so proxies will not buffer it")
    finally:
        main.run_turn = original
        memory.reset()

    # --- the container ------------------------------------------------------
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dockerfile = os.path.join(root, "Dockerfile")
    if not os.path.exists(dockerfile):
        _no("there is no Dockerfile yet - the service has to be packaged")
    text = open(dockerfile).read()
    if "requirements.txt" not in text:
        _no("the Dockerfile should COPY requirements.txt and pip install it "
            "BEFORE copying the code, so a code change does not reinstall "
            "every dependency")
    _ok("the Dockerfile installs dependencies before copying the code")
    if "PORT" not in text:
        _no("the Dockerfile must respect $PORT - every container platform "
            "tells your service where to listen that way")
    _ok("and it listens on $PORT, not a hardcoded number")


def check_02():
    print("Week 02: memory survives the process that started it")
    from app import memory

    # A tiny working Redis stand-in, so this checkpoint needs no server.
    class FakeRedis:
        def __init__(self): self.data = {}; self.ttls = {}
        def get(self, k): return self.data.get(k)
        def setex(self, k, ttl, v): self.data[k] = v; self.ttls[k] = ttl
        def scan_iter(self, p): return [k for k in list(self.data)
                                        if k.startswith(p.rstrip("*"))]
        def delete(self, k): self.data.pop(k, None); self.ttls.pop(k, None)

    if not hasattr(memory, "REDIS_URL"):
        _no("app/memory.py must read REDIS_URL from the environment")
    _ok("app/memory.py reads REDIS_URL, so storage is a setting not a rewrite")

    saved_url, saved_client = memory.REDIS_URL, memory._client
    fake = FakeRedis()
    memory.REDIS_URL, memory._client = "redis://fake", fake
    try:
        memory.save("chk-1", [{"role": "user", "content": "where is ORD-1002?"}])
        if not fake.data:
            _no("save() did not write to Redis when REDIS_URL is set - it is "
                "still using the in-process dict")
        _ok("save() writes to Redis when REDIS_URL is set")

        key = next(iter(fake.data))
        if not key.startswith("session:"):
            _no(f"keys should be namespaced like 'session:<id>', got {key!r}")
        _ok("keys are namespaced, so the keyspace stays readable")

        if fake.ttls.get(key) is None:
            _no("sessions are written without an expiry - use SETEX, or "
                "abandoned conversations pile up forever")
        _ok(f"sessions expire after {fake.ttls[key]}s, so they clean themselves up")

        # the actual lesson: the process dies, the conversation does not
        memory._FALLBACK.clear()
        kept = memory.load("chk-1")
        if not kept or kept[0].get("content") != "where is ORD-1002?":
            _no("a conversation did not survive the process restarting - "
                "load() must read from Redis, not the dict")
        _ok("a conversation survives a redeploy")

        # the awkward case that only breaks in production
        block = NS(type="text", text="asking for a tool")
        try:
            memory.save("chk-2", [
                {"role": "user", "content": "q"},
                {"role": "assistant", "content": [block]},
                {"role": "user", "content": [{"type": "tool_result",
                                              "tool_use_id": "t",
                                              "content": "ORD-1002: desk"}]}])
        except TypeError as e:
            _no("saving a turn with tool blocks raised "
                f"{type(e).__name__}: {e} - content blocks are objects, not "
                "dicts, and json.dumps refuses them. Convert them in save().")
        back = memory.load("chk-2")
        if back[2]["content"][0]["content"] != "ORD-1002: desk":
            _no("tool results did not survive the round trip to Redis")
        _ok("a turn containing tool blocks round-trips through Redis")
    finally:
        memory.REDIS_URL, memory._client = saved_url, saved_client
        memory._FALLBACK.clear()

    # and it must still work with no Redis at all
    memory.reset()
    memory.save("chk-local", [{"role": "user", "content": "no redis here"}])
    if memory.load("chk-local")[0]["content"] != "no redis here":
        _no("with REDIS_URL unset the in-process fallback must still work - "
            "the course has to run on a laptop with no Redis")
    _ok("with no REDIS_URL it falls back to the dict, so local dev still works")
    memory.reset()


def check_03():
    print("Week 03: strangers are kept out, and deploys are automatic")
    import os
    from fastapi.testclient import TestClient

    try:
        from app import guardrails as g
    except ImportError:
        _no("app/guardrails.py does not exist yet")
    for name in ("check_api_key", "check_rate_limit", "GuardrailError"):
        if not hasattr(g, name):
            _no(f"app/guardrails.py must define {name}")
    _ok("app/guardrails.py defines the rules and a GuardrailError to raise")

    # --- the key ------------------------------------------------------------
    saved = os.environ.get("API_KEYS")
    os.environ["API_KEYS"] = "secret,second"
    try:
        try:
            g.check_api_key("wrong")
            _no("a wrong API key was accepted")
        except g.GuardrailError as e:
            if e.status != 401:
                _no(f"a bad key should be 401 (identity unproven), got {e.status}")
        _ok("a wrong API key is refused with 401")
        g.check_api_key("secret")
        g.check_api_key("second")
        _ok("a valid key passes, and more than one key can be configured")

        os.environ["API_KEYS"] = "rotated"
        try:
            g.check_api_key("secret")
            _no("the old key still works after API_KEYS changed - read the keys "
                "fresh on each call, or revoking a leaked key needs a deploy")
        except g.GuardrailError:
            pass
        _ok("keys are read fresh, so rotating one needs no code change")
    finally:
        if saved is None:
            os.environ.pop("API_KEYS", None)
        else:
            os.environ["API_KEYS"] = saved

    os.environ.pop("API_KEYS", None)
    g.check_api_key(None)
    _ok("with API_KEYS unset, auth is off so local dev still works")

    # --- the rate limit -----------------------------------------------------
    g.reset_rate_limits()
    for _ in range(g.RATE_LIMIT):
        g.check_rate_limit("chk-flood")
    try:
        g.check_rate_limit("chk-flood")
        _no(f"a caller sent more than {g.RATE_LIMIT} requests and was allowed")
    except g.GuardrailError as e:
        if e.status != 429:
            _no(f"a rate-limited caller should get 429, got {e.status}")
    _ok(f"a caller is cut off after {g.RATE_LIMIT} requests, with 429")

    g.check_rate_limit("chk-quiet")
    _ok("and one noisy caller does not lock out everybody else")

    # A sliding window, not a fixed one. The clock lives wherever the counter
    # does - inside guardrails until Week 07 moves it into app/store.py - so
    # find it rather than assuming.
    clock = {"t": 10_000.0}
    _mod, _attr = g.time, "monotonic"
    try:
        from app import store as _s
        if hasattr(_s, "time") and hasattr(_s, "hit_count"):
            _mod, _attr = _s.time, "time"
    except ImportError:
        pass                       # store.py arrives in Week 07
    _real = getattr(_mod, _attr)
    setattr(_mod, _attr, lambda: clock["t"])
    try:
        g.reset_rate_limits()
        for _ in range(g.RATE_LIMIT):
            g.check_rate_limit("chk-slide")
        clock["t"] += 61
        try:
            g.check_rate_limit("chk-slide")
        except g.GuardrailError:
            _no("after 61 seconds the oldest requests should have aged out - "
                "drop timestamps older than 60s rather than counting per minute")
        _ok("the window slides, so it cannot be beaten across a minute boundary")
    finally:
        setattr(_mod, _attr, _real)
        g.reset_rate_limits()

    # --- both endpoints are guarded ----------------------------------------
    import app.main as main
    os.environ["API_KEYS"] = "secret"
    try:
        c = TestClient(main.app)
        if c.post("/chat", json={"message": "hi"}).status_code != 401:
            _no("POST /chat without a key must return 401")
        _ok("POST /chat without a key returns 401")

        r = c.post("/chat/stream", json={"message": "hi"})
        if r.status_code != 401:
            _no("POST /chat/stream without a key must return 401 too - a "
                "streaming endpoint is not a side door")
        if "text/event-stream" in r.headers.get("content-type", ""):
            _no("the rejection arrived as a stream - check the guardrails "
                "BEFORE the response starts, or there is no status code left "
                "to reject with")
        _ok("POST /chat/stream without a key returns 401, not an error frame")
    finally:
        os.environ.pop("API_KEYS", None)
        g.reset_rate_limits()

    # --- the pipeline -------------------------------------------------------
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    wf = os.path.join(root, ".github", "workflows")
    if not os.path.isdir(wf):
        _no("there is no .github/workflows - deploys are still manual")
    files = {f: open(os.path.join(wf, f)).read() for f in os.listdir(wf)
             if f.endswith((".yml", ".yaml"))}
    if not files:
        _no("no workflow files found in .github/workflows")
    _ok(f"a pipeline exists ({', '.join(sorted(files))})")

    deploying = {f: t for f, t in files.items() if "gcloud run deploy" in t}
    if not deploying:
        _no("no workflow deploys to Cloud Run")
    for name, text in deploying.items():
        if "needs:" not in text:
            _no(f"{name} deploys without a `needs:` on a test job. Two separate "
                "workflows on push:main do NOT gate each other - they race.")
        if "pytest" not in text:
            _no(f"{name} deploys without running the tests first")
    _ok("the deploy job declares `needs:` on a job that runs the tests")

    for name, text in deploying.items():
        if "/health" not in text:
            _no(f"{name} never checks /health after deploying. `gcloud run "
                "deploy` exiting 0 means the revision was created, not that it "
                "can serve a request.")
    _ok("the pipeline verifies /health after deploying, not just the exit code")

    # Check the --set-env-vars ARGUMENT only, not the rest of the command.
    # The value is a quoted comma list on the same logical line.
    import re
    for name, text in files.items():
        for match in re.finditer(r'--set-env-vars[ =]+"([^"]*)"', text):
            for pair in match.group(1).split(","):
                key = pair.split("=")[0].strip()
                if key in ("KODEKEY", "API_KEYS") or "SECRET" in key.upper():
                    _no(f"{name} passes {key} through --set-env-vars. Env vars "
                        "are visible in the console and in `gcloud describe` "
                        "output - use --set-secrets.")
    if any("set-secrets" in t for t in deploying.values()):
        _ok("secrets go through --set-secrets, not --set-env-vars")
    else:
        _no("no workflow uses --set-secrets; the key has to reach the service "
            "somehow, and an env var is the wrong way")


def check_04():
    print("Week 04: one turn cannot run forever or run up a bill")
    from app import guardrails as g, memory
    from app.agent import run_turn

    if not hasattr(g, "Budget"):
        _no("app/guardrails.py must define a Budget class")
    _ok("app/guardrails.py defines Budget")

    b = g.Budget(max_steps=2, max_tokens=10 ** 9)
    b.add_step(); b.add_step()
    try:
        b.add_step()
        _no("the step budget allowed more steps than its limit")
    except g.GuardrailError as e:
        if e.status != 400:
            _no(f"an overspending turn should be 400 (the request was too "
                f"expensive), got {e.status}")
    _ok("the step budget refuses the step past its limit, with 400")

    b = g.Budget(max_steps=100, max_tokens=100)
    b.add_tokens(60)
    try:
        b.add_tokens(60)
        _no("the token budget allowed more tokens than its limit")
    except g.GuardrailError:
        pass
    _ok("the token budget catches one enormous call, which steps cannot")

    b = g.Budget(max_tokens=100)
    try:
        b.add_tokens(None)
    except Exception as e:
        _no(f"add_tokens(None) raised {type(e).__name__} - some gateways omit "
            "usage entirely, and that must not break the turn")
    _ok("a provider that reports no usage does not crash the turn")

    # the loop actually uses it
    def always_tool(messages):
        blk = NS(type="tool_use", name="calculator",
                 input={"expression": "1+1"}, id="t")
        return NS(content=[blk], stop_reason="tool_use")

    try:
        run_turn("go", model_fn=always_tool)
        _no("a model that always asks for a tool looped forever - the loop is "
            "not using the Budget")
    except g.GuardrailError:
        pass
    _ok("the agent loop stops a runaway turn")

    calls = {"n": 0}

    def steady(messages):
        calls["n"] += 1
        blk = NS(type="tool_use", name="calculator",
                 input={"expression": "1+1"}, id=f"t{calls['n']}")
        return NS(content=[blk], stop_reason="tool_use",
                  usage=NS(input_tokens=8000, output_tokens=0))

    try:
        run_turn("go", model_fn=steady)
        _no("tokens were never counted from the model's usage")
    except g.GuardrailError as e:
        if "token" not in str(e):
            _no(f"the turn stopped on steps, not tokens: {e}. Tokens must "
                "accumulate ACROSS the turn, not reset each step.")
    _ok("tokens accumulate across the turn, so many medium calls also stop")

    # --- context is a budget too -------------------------------------------
    if not hasattr(memory, "trim"):
        _no("app/memory.py must define trim() - every turn re-sends the whole "
            "history, so a long session grows the prompt until the model "
            "refuses it")
    _ok("app/memory.py defines trim()")

    memory.reset()
    memory.save("chk-trim", [{"role": "user", "content": f"m{i}"}
                             for i in range(200)])
    kept = memory.load("chk-trim")
    if len(kept) > memory.MAX_HISTORY_MESSAGES:
        _no(f"a 200-message session was stored as {len(kept)} messages - "
            "save() should trim it")
    if kept[-1]["content"] != "m199":
        _no("trimming kept the OLDEST messages - keep the newest")
    _ok(f"a long session is trimmed to {memory.MAX_HISTORY_MESSAGES}, newest kept")

    turn = [
        {"role": "user", "content": "q"},
        {"role": "assistant", "content": "asking for a tool"},
        {"role": "user", "content": [{"type": "tool_result",
                                      "tool_use_id": "t", "content": "r"}]},
    ]
    kept = memory.trim(turn * 40)
    if memory._is_tool_result(kept[0]):
        _no("trimming left a tool_result with no matching tool_use. Providers "
            "reject that as malformed, so a long session starts failing every "
            "request. Step past a tool result rather than cutting on one.")
    _ok("trimming never orphans a tool result")
    memory.reset()


def check_05():
    print("Week 05: you can see inside a turn, and tell if it is healthy")
    from fastapi.testclient import TestClient
    from app import monitor, trace
    from app.agent import run_turn

    # --- writing: one trace per turn ---------------------------------------
    for name in ("new_trace", "emit"):
        if not hasattr(trace, name):
            _no(f"app/trace.py must define {name}")
    _ok("app/trace.py defines new_trace() and emit()")

    st = {"n": 0}

    def tool_then_text(messages):
        st["n"] += 1
        if st["n"] == 1:
            b = NS(type="tool_use", name="lookup_order",
                   input={"order_id": "ORD-1002"}, id="t1")
            return NS(content=[b], stop_reason="tool_use",
                      usage=NS(input_tokens=100, output_tokens=20))
        return NS(content=[NS(type="text", text="ok")], stop_reason="end_turn",
                  usage=NS(input_tokens=150, output_tokens=30))

    t = trace.new_trace("chk")
    reply, _, t = run_turn("where is ORD-1002?", model_fn=tool_then_text, trace=t)

    if t.get("steps") != 2:
        _no(f"the trace says {t.get('steps')} steps; that turn took 2")
    _ok("the trace records how many steps the turn took")
    if t.get("tools_used") != ["lookup_order"]:
        _no(f"tools_used is {t.get('tools_used')}, expected ['lookup_order']")
    _ok("and which tools were called")
    if len(t.get("step_ms") or []) != 2 or len(t.get("tool_ms") or []) != 1:
        _no("step_ms and tool_ms must be timed separately - 'the turn took 8s' "
            "is useless unless you know whether the model or your tool was slow")
    _ok("and where the time went: the model, or your own tool")
    if t.get("token_count") != 300:
        _no(f"token_count is {t.get('token_count')}, expected 300")
    _ok("and how many tokens it used")

    trace.emit(t)
    if not t.get("cost_usd"):
        _no("emit() must put a cost on the turn - group these by session and "
            "you have cost per user, the question every business asks")
    _ok(f"emit() prices the turn (${t['cost_usd']})")
    if t.get("severity") != "INFO":
        _no("emit() must set severity - log platforms read that field to "
            "decide whether a line is routine, and without it every line "
            "lands as INFO and nothing ever pages anybody")
    bad = trace.new_trace("chk")
    bad["error"] = "provider down"
    trace.emit(bad)
    if bad.get("severity") != "ERROR":
        _no("a failed turn must be severity ERROR")
    _ok("a failed turn is marked ERROR so a log platform can page someone")

    red = trace._redact({"api_key": "sk-secret", "input_tokens": 120})
    if red.get("api_key") != "[redacted]":
        _no("secrets must be redacted before anything is written")
    if red.get("input_tokens") != 120:
        _no("input_tokens was redacted. _REDACT matches on SUBSTRING, so any "
            "field with 'token' in the name is caught by default - allow the "
            "counters through, or the trace lies about its own inputs.")
    _ok("secrets are redacted, and the token counters are not")

    # a broken tool, on a turn that "succeeded"
    st2 = {"n": 0}

    def broken_tool(messages):
        st2["n"] += 1
        if st2["n"] == 1:
            b = NS(type="tool_use", name="lookup_order",
                   input={"wrong_arg": "x"}, id="t1")
            return NS(content=[b], stop_reason="tool_use", usage=None)
        return NS(content=[NS(type="text", text="sorry")],
                  stop_reason="end_turn", usage=None)

    t2 = trace.new_trace("chk")
    reply2, _, t2 = run_turn("q", model_fn=broken_tool, trace=t2)
    if not reply2 or t2.get("error"):
        _no("that turn should have succeeded - a failing tool hands its error "
            "text back to the model, it does not kill the turn")
    if t2.get("tool_errors") != ["lookup_order"]:
        _no("a tool that failed was not recorded in tool_errors. The turn still "
            "returns 200, so this is the ONLY place the breakage shows up.")
    _ok("a broken tool is recorded even though the turn succeeded")

    # --- reading: monitoring ------------------------------------------------
    for name in ("record", "stats", "alerts"):
        if not hasattr(monitor, name):
            _no(f"app/monitor.py must define {name}")
    _ok("app/monitor.py defines record(), stats() and alerts()")

    def turn(error=None, ms=1000, steps=2, tool_errors=None):
        return {"error": error, "duration_ms": ms, "steps": steps,
                "cost_usd": 0.01, "step_ms": [ms], "model_calls": [],
                "tool_errors": tool_errors or []}

    monitor.reset()
    for _ in range(30):
        monitor.record(turn())
    if monitor.alerts():
        _no(f"a healthy agent raised alerts: {monitor.alerts()}")
    _ok("a healthy agent raises no alerts")

    monitor.reset()
    for _ in range(3):
        monitor.record(turn(error="boom"))
    if monitor.alerts():
        _no("alerts fired on 3 turns - two failures out of three is a "
            "coincidence, not an incident. Wait for enough data.")
    _ok("and it stays quiet until it has enough data to judge")

    monitor.reset()
    for i in range(30):
        monitor.record(turn(error="boom" if i % 2 else None, ms=40000, steps=6))
    fired = " ".join(monitor.alerts())
    for want in ("error rate", "p95", "steps"):
        if want not in fired:
            _no(f"a degrading agent did not raise an alert about {want}: {fired}")
    _ok("a degrading agent raises alerts about errors, latency and steps")

    monitor.reset()
    for i in range(20):
        monitor.record(turn(tool_errors=["lookup_order"] if i % 3 == 0 else []))
    if monitor.stats()["error_rate"] != 0.0:
        _no("those turns all succeeded; error_rate should be 0")
    if not any("tool fail" in a for a in monitor.alerts()):
        _no("a third of turns had a tool break and nothing alerted. Every turn "
            "returned 200, so tool_error_rate is the only signal that sees it.")
    _ok("broken tools alert even when every single turn returns 200")

    # --- the endpoint, and the bug that makes it lie ------------------------
    import app.main as main
    monitor.reset()
    body = TestClient(main.app).get("/metrics").json()
    if "status" not in body or "alerts" not in body:
        _no("/metrics must report a status and an alerts list")
    _ok("/metrics reports status and alerts")

    def boom(m, history=None, trace=None):
        raise RuntimeError("the provider is down")

    original = main.run_turn
    main.run_turn = boom
    try:
        c = TestClient(main.app, raise_server_exceptions=False)
        for _ in range(12):
            c.post("/chat", json={"message": "hi"})
        body = c.get("/metrics").json()
        if body.get("error_rate") != 1.0:
            _no(f"every request failed but error_rate is {body.get('error_rate')}. "
                "The handler must catch EVERY exception and record it on the "
                "trace - otherwise a total outage reports a 0% error rate and "
                "your dashboard lies exactly when you need it.")
        if body.get("status") != "degraded":
            _no("with every request failing, /metrics must say degraded")
    finally:
        main.run_turn = original
        monitor.reset()
    _ok("a total outage is reported as a 100% error rate, not 0%")

    # --- OpenTelemetry is optional -----------------------------------------
    from app import otel
    if otel.ENABLED:
        _no("OTEL must be off unless asked for - the course has to run with no "
            "cloud and no internet")
    with otel.span("check", {"a": 1}) as s:
        s.set("b", 2)
        s.failed("and this")
    _ok("OpenTelemetry is off by default and no-ops cleanly when disabled")


def check_06():
    print("Week 06: a blip is absorbed, an outage is survived")
    import app.agent as agent
    from app import monitor

    for name in ("MAX_RETRIES", "FALLBACK_MODEL", "_is_retryable", "_sleep_for"):
        if not hasattr(agent, name):
            _no(f"app/agent.py must define {name}")
    _ok("app/agent.py has retry settings, a fallback model and a backoff")

    def client_for(behaviour):
        calls = []

        class C:
            def __init__(self): self.chat = self; self.completions = self
            def create(self, model, **kw):
                calls.append(model)
                text = behaviour(model, len(calls))
                msg = NS(content=text, tool_calls=None)
                return NS(choices=[NS(message=msg)],
                          usage=NS(prompt_tokens=1, completion_tokens=1))
        return C, calls

    saved_client, saved_sleep = agent._client, agent.time.sleep
    agent.time.sleep = lambda s: None
    try:
        # --- a blip must NOT change models ---------------------------------
        class Blip(Exception):
            status_code = 429

        def one_blip(model, n):
            if n == 1:
                raise Blip("too many requests")
            return "ok"

        C, calls = client_for(one_blip)
        agent._client = lambda: C()
        tr = {"model_calls": [], "retries": 0}
        agent.call_model([{"role": "user", "content": "hi"}], tr)

        if agent.FALLBACK_MODEL in calls:
            _no("a single 429 sent the request to the FALLBACK model. Retry the "
                "same model first - one blip is normal traffic, and switching "
                "providers silently changes the quality of every answer while "
                "nothing alerts, because the turn still succeeds.")
        if calls != [agent.MODEL, agent.MODEL]:
            _no(f"expected two attempts on the primary, got {calls}")
        _ok("one 429 is retried on the primary, not failed over")
        if tr.get("retries") != 1:
            _no(f"the trace should record 1 retry, got {tr.get('retries')}")
        _ok("and the retry is recorded, so flakiness is visible before it hurts")

        # --- a permanent error must not be retried -------------------------
        class Permanent(Exception):
            status_code = 400

        def always_400(model, n):
            raise Permanent("bad request")

        C, calls = client_for(always_400)
        agent._client = lambda: C()
        try:
            agent.call_model([{"role": "user", "content": "hi"}])
        except Exception:
            pass
        if len(calls) > 2:
            _no(f"a 400 was retried {len(calls)} times. It means the REQUEST is "
                "wrong - retrying only turns one fast failure into a slow one.")
        _ok("a 400 is not retried; only 429s, 5xx and timeouts are")

        # --- a real outage must still answer -------------------------------
        class Down(Exception):
            status_code = 503

        def primary_down(model, n):
            if model == agent.MODEL:
                raise Down("service unavailable")
            return "from the fallback"

        C, calls = client_for(primary_down)
        agent._client = lambda: C()
        tr = {"model_calls": [], "retries": 0}
        resp = agent.call_model([{"role": "user", "content": "hi"}], tr)
        if resp.stop_reason != "end_turn":
            _no("no answer came back despite a working fallback")
        if calls.count(agent.MODEL) != agent.MAX_RETRIES + 1:
            _no(f"the primary was tried {calls.count(agent.MODEL)} times before "
                f"falling back; expected {agent.MAX_RETRIES + 1}")
        _ok("a real outage exhausts the primary's retries, then falls back")
        if not any(c.get("provider") == "fallback" and not c.get("error")
                   for c in tr["model_calls"]):
            _no("the trace does not show the fallback ANSWERING")
        _ok("and the trace shows which provider actually answered")
    finally:
        agent._client, agent.time.sleep = saved_client, saved_sleep

    # --- backoff shape ------------------------------------------------------
    waits = [agent._sleep_for(2) for _ in range(20)]
    if len(set(waits)) == 1:
        _no("the backoff is not jittered. Without jitter every container that "
            "failed at the same moment retries at the same moment, and your "
            "own fleet keeps hammering the thing it is waiting for.")
    if agent._sleep_for(50) > agent.RETRY_MAX_SECONDS:
        _no("the backoff is not capped - a long outage would sleep for hours")
    _ok("backoff grows, is jittered, and is capped")

    # --- the monitor sees it ------------------------------------------------
    monitor.reset()
    for _ in range(20):
        monitor.record({"error": None, "duration_ms": 100, "steps": 1,
                        "cost_usd": 0.001, "step_ms": [100], "retries": 1,
                        "tool_errors": [],
                        "model_calls": [{"provider": "primary", "error": "429"},
                                        {"provider": "primary", "attempts": 2}]})
    s = monitor.stats()
    if "retry_rate" not in s:
        _no("/metrics should report retry_rate - a rising number there is the "
            "early warning that stops fallback_rate being your first clue")
    if s.get("fallback_rate") != 0.0:
        _no("those turns were answered by the PRIMARY after a retry, but "
            "fallback_rate says otherwise. model_calls now holds failed "
            "attempts too - only count a fallback that actually answered.")
    _ok("a failed attempt is not miscounted as a fallback answer")

    monitor.reset()
    for _ in range(20):
        monitor.record({"error": None, "duration_ms": 100, "steps": 1,
                        "cost_usd": 0.001, "step_ms": [100], "retries": 0,
                        "tool_errors": [],
                        "model_calls": [{"provider": "fallback", "model": "b"}]})
    if not any("fallback" in a for a in monitor.alerts()):
        _no("the fallback answered every turn and nothing alerted")
    _ok("a struggling primary raises an alert")
    monitor.reset()


def check_setup():
    print("Setup check: the tests pass")
    import subprocess
    t = subprocess.run([sys.executable, "-m", "pytest", "-q"],
                       capture_output=True, text=True)
    (_ok if t.returncode == 0 else _no)("unit tests pass")


CHECKS = {"00": check_00, "01": check_01, "02": check_02,
          "03": check_03, "04": check_04, "05": check_05,
          "06": check_06, "setup": check_setup}


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "setup"
    fn = CHECKS.get(which)
    if fn is None:
        print(f"usage: python -m checks.check [{'|'.join(CHECKS)}]")
        raise SystemExit(2)
    fn()
    print("\nCheckpoint passed.")
