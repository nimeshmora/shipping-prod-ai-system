"""The web service: the agent's front door.

    POST /chat          the whole reply, as one JSON object
    POST /chat/stream   the same reply, streamed as server-sent events
    GET  /health        is this process up? the deploy pipeline asks this

Request flow, top to bottom:

    1. api key       (Week 03)
    2. rate limit    (Week 03)
    3. input size    (Week 07)
    4. blocked input (Week 07)
    5. run the turn: budget + trace + retry/fallback  (Weeks 04, 05, 06)
    6. record the turn for monitoring                 (Week 05)
    7. return, or a clean 4xx if a rule was broken

One engine, two surfaces - and BOTH go through the same guardrails. A streaming
endpoint is not a side door; the day you add a rule to one and forget the other
is the day you have an unauthenticated path into a paid model.
"""
import os
import uuid

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app import guardrails as g
from app import memory, monitor, otel, stream, trace
from app.agent import AgentError, run_turn

app = FastAPI(title="Ship Production AI agent")


class ChatRequest(BaseModel):
    """The request body. Pydantic validates this for you, so a request with a
    missing or wrong-typed `message` is rejected with a 422 before your code
    runs. That is a guardrail you get for free by declaring the shape."""
    message: str
    session_id: str | None = None


@app.get("/metrics")
def metrics():
    """Week 05: is the agent HEALTHY, not just alive?

    /health answers "is the process up", and a broken agent answers that
    perfectly. These numbers are how you see it going wrong: turns failing,
    the slow tail growing, the loop taking more steps, the bill creeping up.

    Deliberately separate from /health. Wiring a platform health check to
    THIS would restart every container the moment error rate rose - turning a
    degraded service into no service at all.
    """
    current = monitor.alerts()
    return {
        "status": "degraded" if current else "ok",
        "alerts": current,
        **monitor.stats(),
    }


@app.get("/health")
def health():
    """Liveness: is the process up?

    Deliberately trivial - no database call, no model call. A health check that
    depends on your dependencies will fail during someone else's outage and get
    your container restarted for no reason. Week 02's deploy pipeline polls
    this to decide whether a release worked.
    """
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest, x_api_key: str | None = Header(default=None)):
    """One turn of conversation.

    The session id is how a stateless HTTP service holds a conversation: the
    caller sends it back on the next request, and this handler reloads the
    history it belongs to. The model itself remembers nothing.
    """
    session_id = req.session_id or uuid.uuid4().hex
    t = trace.new_trace(session_id)
    # One span for the whole turn. Every model call and tool call inside
    # becomes a child of this one, so a trace viewer draws the shape of the
    # turn - the same information step_ms and tool_ms give you as numbers.
    with otel.span("chat_turn", {"session.id": session_id,
                                 "turn.id": t["turn_id"]}) as sp:
        try:
            # Guardrails first, before any work is done. Rejecting a request
            # that was never going to be allowed should cost nothing -
            # certainly not a model call.
            g.check_api_key(x_api_key)
            g.check_rate_limit(x_api_key or "anonymous")
            g.check_input_length(req.message)
            g.check_blocked_input(req.message)

            history = memory.load(session_id)
            reply, new_history, t = run_turn(req.message, history, trace=t)
            memory.save(session_id, new_history)
            return {"reply": reply, "session_id": session_id,
                    "turn_id": t["turn_id"]}
        except g.GuardrailError as e:
            # A rule was broken. Expected, and the caller's fault: a clean 4xx.
            t["error"] = str(e)
            raise HTTPException(status_code=e.status, detail=str(e))
        except AgentError as e:
            t["error"] = str(e)
            raise HTTPException(status_code=e.status, detail=str(e))
        except Exception as e:
            # Anything else: a provider outage, a timeout, a bug of ours.
            #
            # This except block is easy to leave out, and leaving it out is the
            # bug that makes your dashboard lie. Without it the exception
            # escapes before the trace is filled, so a total outage is recorded
            # as "error": null - and /metrics cheerfully reports a 0% error
            # rate while every single request is failing.
            t["error"] = f"{type(e).__name__}: {e}"
            raise HTTPException(status_code=500, detail="internal error") from e
        finally:
            # emit() finalises the trace (duration, cost, severity), so it has
            # to run before we copy those numbers onto the span.
            trace.emit(t)
            sp.set("turn.steps", t["steps"])
            sp.set("turn.tokens", t["token_count"])
            sp.set("turn.cost_usd", t["cost_usd"])
            sp.set("turn.duration_ms", t["duration_ms"])
            if t.get("error"):
                sp.failed(t["error"])
            monitor.record(t)   # Week 05: telemetry is only half of monitoring


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest,
                      x_api_key: str | None = Header(default=None)):
    """The same turn, streamed as server-sent events.

    The guardrails run here too, and they run BEFORE the response starts. That
    ordering is the whole trick: once the first frame goes out, HTTP 200 has
    already been sent and there is no status code left to reject with. Check
    first, and a rejected caller still gets an honest 401 or 429.
    """
    session_id = req.session_id or uuid.uuid4().hex
    t = trace.new_trace(session_id)

    try:
        g.check_api_key(x_api_key)
        g.check_rate_limit(x_api_key or "anonymous")
        g.check_input_length(req.message)
        g.check_blocked_input(req.message)
    except g.GuardrailError as e:
        t["error"] = str(e)
        trace.emit(t)
        monitor.record(t)
        raise HTTPException(status_code=e.status, detail=str(e))

    history = memory.load(session_id)

    def run():
        reply, new_history, _ = run_turn(req.message, history, trace=t)
        memory.save(session_id, new_history)
        return reply, new_history

    async def frames():
        # The trace has to be finalised and recorded whatever happens in here,
        # including a client that disconnects halfway through. Without the
        # finally, an abandoned stream leaves no trace at all and /metrics
        # silently under-counts exactly the turns users gave up on.
        try:
            with otel.span("chat_turn_stream",
                           {"session.id": session_id,
                            "turn.id": t["turn_id"]}) as sp:
                try:
                    async for frame in stream.stream_turn(
                            req.message, history, run, t,
                            finalise=trace.emit):
                        yield frame
                except Exception as e:
                    t["error"] = f"{type(e).__name__}: {e}"
                    yield stream.sse("error", {"message": "internal error"})
                finally:
                    trace.emit(t)
                    sp.set("turn.steps", t["steps"])
                    sp.set("turn.cost_usd", t["cost_usd"])
                    if t.get("error"):
                        sp.failed(t["error"])
        finally:
            monitor.record(t)

    return StreamingResponse(
        frames(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # Cloud Run, and most proxies, will happily buffer a response and
            # hand it over in one lump - which defeats the entire point. This
            # header is the standard way to say "do not".
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn
    # PORT comes from the environment because that is how every container
    # platform tells a service where to listen. Hardcode 8080 and you have a
    # service that works locally and fails on deploy.
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
