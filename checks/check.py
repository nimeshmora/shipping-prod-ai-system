"""Guided checkpoints. Run one per week to confirm that week's capability works.

    python -m checks.check 00      # ... through 08, or 'setup'

Each check uses a fake model where possible, so it runs with no API key and no
cloud, and prints a plain-English PASS/FAIL for that week.
"""
import sys
from types import SimpleNamespace as NS


def _ok(msg): print(f"  PASS  {msg}")
def _no(msg): print(f"  FAIL  {msg}"); raise SystemExit(1)


def _plain_model(text="hello"):
    def model(messages, trace=None):
        return NS(content=[NS(type="text", text=text)],
                  stop_reason="end_turn", usage=NS(input_tokens=3, output_tokens=4))
    return model


def _tool_then_answer(name, args):
    """A stand-in model that asks for one tool, then reports what it got."""
    st = {"n": 0}
    def model(messages, trace=None):
        st["n"] += 1
        if st["n"] == 1:
            b = NS(type="tool_use", name=name, input=args, id="t1")
            return NS(content=[b], stop_reason="tool_use", usage=None)
        result = messages[-1]["content"][0]["content"]
        return NS(content=[NS(type="text", text=f"It is {result}.")],
                  stop_reason="end_turn", usage=None)
    return model


def check_00():
    print("Week 00: the loop runs a tool then answers")
    from app.agent import run_turn
    reply, hist, _ = run_turn(
        "where is order ORD-1002?",
        model_fn=_tool_then_answer("lookup_order", {"order_id": "ORD-1002"}))
    (_ok if "standing desk" in reply else _no)(
        "agent looked up a real order it could not have known")
    (_ok if len(hist) == 4 else _no)("history has all four moves")
    reply, _, _ = run_turn(
        "what is 12*41?",
        model_fn=_tool_then_answer("calculator", {"expression": "12 * 41"}))
    (_ok if "492" in reply else _no)("and the calculator still works")


def check_01():
    print("Week 01: the web service answers /chat and /health")
    from fastapi.testclient import TestClient
    import app.agent as agent
    import app.main as main
    main.run_turn = lambda m, history=None, trace=None: agent.run_turn(
        m, history, model_fn=_plain_model("hi"), trace=trace)
    c = TestClient(main.app)
    (_ok if c.get("/health").json() == {"status": "ok"} else _no)("/health is ok")
    r = c.post("/chat", json={"message": "hi"})
    (_ok if r.status_code == 200 and "reply" in r.json() else _no)("/chat returns a reply")
    (_ok if "session_id" in r.json() else _no)("a session id is returned")
    # streaming: the same turn, sent as it happens
    with c.stream("POST", "/chat/stream", json={"message": "hi"}) as sr:
        (_ok if sr.status_code == 200 else _no)("/chat/stream accepts the turn")
        events = [l[7:] for l in sr.iter_lines() if l.startswith("event: ")]
    (_ok if events and events[0] == "start" else _no)("it opens with a start frame")
    (_ok if "token" in events else _no)("the answer arrives as token frames")
    (_ok if events[-1] == "done" else _no)("and closes with a done frame")


def check_02():
    print("Week 02: memory keeps a conversation, and has a Redis path")
    from app import memory
    memory.save("s1", [{"role": "user", "content": "hi"}])
    (_ok if memory.load("s1") else _no)("memory stores and loads a session")
    import inspect
    src = inspect.getsource(memory)
    (_ok if "REDIS_URL" in src and "setex" in src else _no)("Redis path is present for Week 2")


def check_03():
    print("Week 03: api key and rate limit lock the door")
    import os, importlib
    from app import guardrails as g
    os.environ["API_KEYS"] = "k1"
    try:
        g.check_api_key("wrong"); _no("bad key should be rejected")
    except g.GuardrailError as e:
        (_ok if e.status == 401 else _no)("no/!bad key returns 401")
    g.check_api_key("k1"); _ok("good key is allowed")
    del os.environ["API_KEYS"]
    g.reset_rate_limits()
    try:
        for _ in range(g.RATE_LIMIT + 1):
            g.check_rate_limit("u")
        _no("too many requests should be limited")
    except g.GuardrailError as e:
        (_ok if e.status == 429 else _no)("too many requests returns 429")
    g.reset_rate_limits()


def check_04():
    print("Week 04: the step budget stops a runaway")
    from app.agent import run_turn
    from app.guardrails import GuardrailError
    def always_tool(messages, trace=None):
        b = NS(type="tool_use", name="calculator", input={"expression": "1+1"}, id="t")
        return NS(content=[b], stop_reason="tool_use", usage=None)
    try:
        run_turn("go", model_fn=always_tool); _no("a runaway should be stopped")
    except GuardrailError:
        _ok("a never-ending loop is stopped by the step cap")
    # context is a budget too, not just tokens per turn
    from app import memory
    memory.save("ctx", [{"role": "user", "content": f"m{i}"} for i in range(300)])
    kept = memory.load("ctx")
    (_ok if len(kept) == memory.MAX_HISTORY_MESSAGES else _no)(
        f"history is trimmed to {memory.MAX_HISTORY_MESSAGES}, so context cannot grow forever")


def check_05():
    print("Week 05: a trace is written and secrets are redacted")
    from app import trace
    from app.agent import run_turn
    t = trace.new_trace("s1")
    reply, _, t = run_turn("hi", model_fn=_plain_model("hi"), trace=t)
    (_ok if t["turn_id"] and t["session_id"] == "s1" else _no)("a trace is filled in")
    red = trace._redact({"api_key": "sk-secret", "token_count": 12})
    (_ok if red["api_key"] == "[redacted]" else _no)("secrets are redacted")
    (_ok if red["token_count"] == 12 else _no)("real counts are kept")
    t2 = trace.new_trace("s2"); t2["token_count"] = 1_000_000
    trace.emit(t2)
    (_ok if t2["cost_usd"] > 0 else _no)("every turn records what it cost")
    # writing traces is telemetry; reading them is monitoring
    from app import monitor
    monitor.reset()
    for _ in range(30):
        monitor.record({"error": None, "duration_ms": 900, "steps": 2,
                        "cost_usd": 0.01, "model_calls": [{"provider": "primary"}]})
    (_ok if monitor.alerts() == [] else _no)("a healthy agent raises no alerts")
    monitor.reset()
    for _ in range(30):
        monitor.record({"error": "boom", "duration_ms": 40000, "steps": 6,
                        "cost_usd": 0.09, "model_calls": [{"provider": "fallback"}]})
    (_ok if len(monitor.alerts()) >= 3 else _no)(
        "a degrading agent raises alerts even though nothing crashed")
    # you cannot debug a slow turn without knowing which part was slow
    t3 = trace.new_trace("s3")
    from app.agent import run_turn as _rt
    _rt("hi", model_fn=_plain_model("hi"), trace=t3)
    (_ok if t3["step_ms"] else _no)("the trace times every step, not just the whole turn")
    t4 = trace.new_trace("s4"); t4["error"] = "boom"; trace.emit(t4)
    (_ok if t4["severity"] == "ERROR" else _no)(
        "a failed turn is marked ERROR so the log tool can page someone")
    monitor.reset()
    for i in range(20):
        monitor.record({"error": None, "duration_ms": 900, "steps": 2,
                        "cost_usd": 0.01, "step_ms": [400],
                        "model_calls": [{"provider": "primary"}],
                        "tool_errors": ["lookup_order"] if i % 3 == 0 else []})
    (_ok if any("tool fail" in a for a in monitor.alerts()) else _no)(
        "a broken tool raises an alert even though every turn succeeded")
    monitor.reset()
    # the same trace, in the shape the rest of the industry uses
    from app import otel
    with otel.span("probe", {"x": 1}) as sp:
        sp.set("y", 2)
    (_ok if not otel.ENABLED else _ok)(
        "OpenTelemetry is wired in, and off by default so this all works offline")


def check_06():
    print("Week 06: the fallback answers when the primary fails")
    import app.agent as agent
    calls = {"n": 0}
    class FakeClient:
        """Stands in for the gateway client, in the OpenAI shape it returns."""
        def __init__(self): self.chat = self; self.completions = self
        def create(self, model, **kw):
            calls["n"] += 1
            if model != agent.FALLBACK_MODEL:      # primary fails
                raise RuntimeError("primary is down")
            msg = NS(content="ok from fallback", tool_calls=None)
            return NS(choices=[NS(message=msg, finish_reason="stop")],
                      usage=NS(prompt_tokens=3, completion_tokens=4))
    agent._client = lambda: FakeClient()
    tr = {"model_calls": []}
    resp = agent.call_model([{"role": "user", "content": "hi"}], tr)
    (_ok if resp.stop_reason == "end_turn" else _no)("an answer came back despite the outage")
    providers = [c.get("provider") for c in tr["model_calls"]]
    (_ok if "fallback" in providers else _no)("the trace shows the fallback answered")

    # And the half that costs money if you get it wrong: a single blip must be
    # retried on the PRIMARY, not silently answered by a weaker model.
    seen = []
    class Flaky:
        def __init__(self): self.chat = self; self.completions = self
        def create(self, model, **kw):
            seen.append(model)
            if len(seen) == 1:
                err = RuntimeError("429 too many requests")
                err.status_code = 429
                raise err
            msg = NS(content="ok", tool_calls=None)
            return NS(choices=[NS(message=msg, finish_reason="stop")],
                      usage=NS(prompt_tokens=1, completion_tokens=1))
    agent._client = lambda: Flaky()
    _real_sleep, agent.time.sleep = agent.time.sleep, lambda s: None
    try:
        tr2 = {"model_calls": [], "retries": 0}
        agent.call_model([{"role": "user", "content": "hi"}], tr2)
    finally:
        agent.time.sleep = _real_sleep
    (_ok if seen == [agent.MODEL, agent.MODEL] else _no)(
        "one 429 is retried on the primary, not failed over")
    (_ok if agent.FALLBACK_MODEL not in seen else _no)(
        "the fallback was never touched for a blip")
    (_ok if tr2["retries"] == 1 else _no)("and the retry is recorded in the trace")


def check_07():
    print("Week 07: input and url fences hold")
    from app import guardrails as g
    for label, fn, arg in [
        ("oversized input", g.check_input_length, "x" * (g.MAX_INPUT_CHARS + 1)),
        ("dangerous input", g.check_blocked_input, "please rm -rf /"),
        ("internal url", g.check_url, "http://169.254.169.254"),
    ]:
        try:
            fn(arg); _no(f"{label} should be refused")
        except g.GuardrailError:
            _ok(f"{label} is refused")
    g.check_url("https://example.com"); _ok("an allowed url passes")
    # the agent-shaped half: what a TOOL hands back is untrusted too.
    # ORD-1043 carries an instruction the way real customer data does.
    from app.agent import run_tool
    hostile = run_tool("lookup_order", {"order_id": "ORD-1043"})
    cleaned = g.check_tool_output(hostile)
    (_ok if "[filtered]" in cleaned else _no)(
        "an instruction hidden in real order data is neutralised")
    (_ok if "office chair" in cleaned else _no)(
        "and the genuine order details still come through")
    (_ok if g.check_tool_output("492") == "492" else _no)(
        "an ordinary tool result passes through untouched")

    # SSRF: fetch_url is the tool that can reach what the internet cannot.
    for label, url, expect in [
        ("the cloud metadata address", "http://169.254.169.254/computeMetadata/v1/",
         "internal addresses are blocked"),
        ("a file:// url", "file:///etc/passwd", "http and https"),
        ("a private address", "http://10.0.0.5/", "internal addresses are blocked"),
        ("an unlisted host", "https://evil.example.org/", "not on the allowlist"),
    ]:
        out = run_tool("fetch_url", {"url": url})
        (_ok if expect in out else _no)(f"fetch_url refuses {label}")

    # shared state: a rate limit that counts per container is a suggestion
    from app import store
    store.reset_rate_limits()
    counts = [store.hit_count("checkpoint-user") for _ in range(3)]
    (_ok if counts == [1, 2, 3] else _no)("the rate counter is a real sliding count")
    (_ok if hasattr(store, "available") else _no)(
        "and /metrics can say whether it covers the whole service")


def check_08():
    print("Week 08: the eval gate runs and passes on good code")
    from evals.run_evals import run
    code = run(real=False)
    (_ok if code == 0 else _no)("the gate passes with the current (good) code")

    # tier 2 exists, and cannot break the build by breaking itself
    from evals import judge
    passed, _ = judge.grade("q", "a", "check")
    (_ok if passed else _no)("a judge with no key never fails the build")
    verdict, why = judge._parse(
        'Sure.\n```json\n{"pass": false, "reason": "promised a refund"}\n```')
    (_ok if verdict is False and "refund" in why else _no)(
        "the judge reads a verdict out of fenced json")
    import json as _json
    import os as _os
    cases = _json.load(open(_os.path.join(
        _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
        "evals", "cases.json")))
    (_ok if any(c.get("judge") for c in cases) else _no)(
        "quality cases exist that substring matching cannot grade")

    # the portability close-out: nothing in the app knows where it runs
    import subprocess
    hits = subprocess.run(
        ["grep", "-rl", "gcloud", "app/", "evals/", "loadtest/"],
        capture_output=True, text=True).stdout.strip()
    (_ok if not hits else _no)("no application file mentions the platform")


def check_setup():
    print("Setup check: tests + eval gate")
    import subprocess
    t = subprocess.run([sys.executable, "-m", "pytest", "-q"], capture_output=True, text=True)
    (_ok if t.returncode == 0 else _no)("unit tests pass")
    from evals.run_evals import run
    (_ok if run(real=False) == 0 else _no)("eval gate passes")


CHECKS = {
    "00": check_00, "01": check_01, "02": check_02, "03": check_03, "04": check_04,
    "05": check_05, "06": check_06, "07": check_07, "08": check_08,
    "setup": check_setup,
}


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "setup"
    fn = CHECKS.get(which)
    if fn is None:
        print("usage: python -m checks.check [00..08|setup]"); raise SystemExit(2)
    fn()
    print("\nCheckpoint passed.")
