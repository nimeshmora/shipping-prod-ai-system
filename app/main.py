"""The web service: the agent's front door.

Two ways to read the same turn:

    POST /chat          the whole reply, as one JSON object
    POST /chat/stream   the same reply, streamed as server-sent events
    GET  /health        is this process up? the deploy pipeline asks this

One engine, two surfaces. Every later week adds a layer here - auth and rate
limits in Week 03, budgets in Week 04, tracing in Week 05 - and they all attach
to the one loop in app/agent.py.
"""
import os
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app import memory, stream
from app.agent import AgentError, run_turn

app = FastAPI(title="Ship Production AI agent")


class ChatRequest(BaseModel):
    """The request body. Pydantic validates this for you, so a request with a
    missing or wrong-typed `message` is rejected with a 422 before your code
    runs. That is a guardrail you get for free by declaring the shape."""
    message: str
    session_id: str | None = None


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
def chat(req: ChatRequest):
    """One turn of conversation.

    The session id is how a stateless HTTP service holds a conversation: the
    caller sends it back on the next request, and this handler reloads the
    history it belongs to. The model itself remembers nothing.
    """
    session_id = req.session_id or uuid.uuid4().hex
    try:
        history = memory.load(session_id)
        reply, new_history = run_turn(req.message, history)
        memory.save(session_id, new_history)
        return {"reply": reply, "session_id": session_id}
    except AgentError as e:
        # Something the caller can understand and act on.
        raise HTTPException(status_code=e.status, detail=str(e))
    except Exception as e:
        # Anything else: a provider outage, a timeout, a bug of ours. Never
        # let the raw exception reach the client - it can carry internals, and
        # sometimes secrets, straight into someone else's browser.
        raise HTTPException(status_code=500, detail="internal error") from e


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """The same turn, streamed as server-sent events.

    Note where the work happens: `run` closes over the request, and
    stream.stream_turn calls it on a worker thread. Everything before the
    first frame is identical to /chat, because a streaming endpoint is not a
    side door - in Week 03, when auth arrives, it has to guard both.
    """
    session_id = req.session_id or uuid.uuid4().hex
    history = memory.load(session_id)

    def run():
        reply, new_history = run_turn(req.message, history)
        memory.save(session_id, new_history)
        return reply, new_history

    return StreamingResponse(
        stream.stream_turn(req.message, history, run),
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
    # platform tells a service where to listen. Hardcode 7000 and you have a
    # service that works locally and fails on deploy.
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 7000)))
