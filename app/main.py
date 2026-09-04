"""The web service, with every guardrail wired in.

Request flow, top to bottom:
  1. api key      (Week 03)
  2. rate limit   (Week 03)
  3. input size   (Week 07)
  4. blocked input(Week 07)
  5. run the turn: budget + trace + retry + fallback  (Weeks 04, 05, 06)
  6. record the turn for monitoring                  (Week 05)
A broken rule returns a clean 4xx. Everything else is a 200 with the reply.

Two ways to read the same turn: /chat returns it whole, /chat/stream sends it
as server-sent events. One engine, two surfaces (Week 01).
"""
import os
import uuid

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app import guardrails as g
from app import memory, monitor, otel, stream, trace
from app.agent import run_turn

app = FastAPI(title="Ship Production AI agent")


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


@app.get("/health")
def health():
    """Liveness: is the process up? Used by the deploy pipeline."""
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    """Week 05: is the agent HEALTHY, not just alive?

    A broken agent still returns 200 on /health. These numbers are how you see
    it going wrong: turns failing, the slow tail growing, the fallback carrying
    traffic, the loop taking more steps, the bill creeping up.
    """
    current = monitor.alerts()
    return {
        "status": "degraded" if current else "ok",
        "alerts": current,
        **monitor.stats(),
    }


@app.post("/chat")
def chat(req: ChatRequest, x_api_key: str | None = Header(default=None)):
    session_id = req.session_id or uuid.uuid4().hex
    t = trace.new_trace(session_id)
    # One span for the whole turn. Every model call and tool call above
    # becomes a child of this one, so a trace viewer draws the shape of the
    # turn - which is exactly the picture step_ms and tool_ms give you as
    # numbers. Same information, industry-standard format.
    with otel.span("chat_turn", {"session.id": session_id,
                                 "turn.id": t["turn_id"]}) as sp:
      try:
          g.check_api_key(x_api_key)
          g.check_rate_limit(x_api_key or "anonymous")
          g.check_input_length(req.message)
          g.check_blocked_input(req.message)

          history = memory.load(session_id)
          reply, new_history, t = run_turn(req.message, history, trace=t)
          memory.save(session_id, new_history)
          return {"reply": reply, "session_id": session_id, "turn_id": t["turn_id"]}
      except g.GuardrailError as e:
          # A rule was broken. Expected, and the caller's fault: a clean 4xx.
          t["error"] = str(e)
          raise HTTPException(status_code=e.status, detail=str(e))
      except Exception as e:
          # Anything else: a provider outage, a timeout, a bug of ours.
          #
          # This except block is easy to leave out, and leaving it out is the
          # bug that makes your dashboard lie. Without it the exception escapes
          # before the trace is filled, so a total outage is recorded as
          # "error": null - and /metrics cheerfully reports a 0% error rate
          # while every single request is failing.
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
          monitor.record(t)    # Week 05: telemetry is only half of monitoring


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, x_api_key: str | None = Header(default=None)):
    """Week 01: the same turn, streamed as server-sent events.

    Everything before the first byte is identical to /chat - same key check,
    same rate limit, same input guards - because a streaming endpoint is not a
    side door. Skipping the guards on the "convenience" endpoint is a classic
    way to leave an unauthenticated, unlimited path into a paid model.

    The guards run BEFORE the response starts, so a rejected request can still
    be an honest 401/429. Once streaming begins the status code is already
    sent, and any later failure has to arrive as an `error` frame instead.
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
            with otel.span("chat_turn_stream", {"session.id": session_id,
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
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 7000)))
