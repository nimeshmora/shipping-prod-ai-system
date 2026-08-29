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
from app import memory, monitor, trace
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
        t["error"] = str(e)
        raise HTTPException(status_code=e.status, detail=str(e))
    finally:
        trace.emit(t)
        monitor.record(t)      # Week 05: telemetry is only half of monitoring


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
