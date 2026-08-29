"""The web service, with every guardrail wired in.

Request flow, top to bottom:
  1. api key      (Week 03)
  2. rate limit   (Week 03)
  3. input size   (Week 07)
  4. blocked input(Week 07)
  5. run the turn: budget + trace + fallback  (Weeks 04, 05, 06)
  6. record the turn for monitoring           (Week 05)
A broken rule returns a clean 4xx. Everything else is a 200 with the reply.
"""
import os
import uuid

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from app import guardrails as g
from app import memory, monitor, otel, trace
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
