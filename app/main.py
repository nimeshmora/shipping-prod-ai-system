"""The web service: the agent's front door.

    POST /chat          the whole reply, as one JSON object
    POST /chat/stream   the same reply, streamed as server-sent events
    GET  /health        is this process up? the deploy pipeline asks this

Request flow, top to bottom:

    1. api key      (Week 03)
    2. rate limit   (Week 03)
    3. run the turn
    4. return, or a clean 4xx if a rule was broken

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
def chat(req: ChatRequest, x_api_key: str | None = Header(default=None)):
    """One turn of conversation.

    The session id is how a stateless HTTP service holds a conversation: the
    caller sends it back on the next request, and this handler reloads the
    history it belongs to. The model itself remembers nothing.
    """
    session_id = req.session_id or uuid.uuid4().hex
    try:
        # Guardrails first, before any work is done. Rejecting a request that
        # was never going to be allowed should cost nothing - certainly not a
        # model call.
        g.check_api_key(x_api_key)
        g.check_rate_limit(x_api_key or "anonymous")

        history = memory.load(session_id)
        reply, new_history = run_turn(req.message, history)
        memory.save(session_id, new_history)
        return {"reply": reply, "session_id": session_id}
    except g.GuardrailError as e:
        # A rule was broken. Expected, and the caller's fault: a clean 4xx.
        raise HTTPException(status_code=e.status, detail=str(e))
    except AgentError as e:
        # Something the caller can understand and act on.
        raise HTTPException(status_code=e.status, detail=str(e))
    except Exception as e:
        # Anything else: a provider outage, a timeout, a bug of ours. Never
        # let the raw exception reach the client - it can carry internals, and
        # sometimes secrets, straight into someone else's browser.
        raise HTTPException(status_code=500, detail="internal error") from e


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

    try:
        g.check_api_key(x_api_key)
        g.check_rate_limit(x_api_key or "anonymous")
    except g.GuardrailError as e:
        raise HTTPException(status_code=e.status, detail=str(e))

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
