"""app/main.py - Week 01. BUILD THIS FILE.

The agent's front door. Three endpoints, and the shapes below are a contract:
`make check-week-01` asserts on them, and so would any real client.

    GET  /health        -> {"status": "ok"}
    POST /chat          -> {"reply": "<text>", "session_id": "<id>"}
    POST /chat/stream   -> text/event-stream  (see app/stream.py)

Work down the TODOs in order. Each is a few lines, and the slides walk through
every line. Run `make check-week-01` whenever you want to see how far you got.

Stuck on one? Compare with the answer key:
    git diff week-01-package..week-01-solution -- app/main.py
"""

# TODO 1 - bring in the tools.
#
#   from fastapi import FastAPI, HTTPException
#   from fastapi.responses import StreamingResponse
#   from pydantic import BaseModel
#   from app import memory, stream
#   from app.agent import AgentError, run_turn
#   import os, uuid


# TODO 2 - create the application, and call it exactly `app`.
#
#   app = FastAPI(title="Ship Production AI agent")
#
# The name is not optional: uvicorn is told to look for `app.main:app`, so
# anything else and nothing starts. This is the line check-week-01 complains
# about first.


# TODO 3 - describe what an incoming question looks like.
#
#   class ChatRequest(BaseModel):
#       message: str
#       session_id: str | None = None
#
# Declaring the shape is a guardrail you get for free: FastAPI rejects a
# request with no `message` as a 422 before your handler ever runs.


# TODO 4 - GET /health, returning {"status": "ok"}.
#
# Keep it trivial. No model call, no memory read, no database. A health check
# that depends on your dependencies fails during someone else's outage and
# gets your container restarted for no reason. Week 02's deploy pipeline polls
# this to decide whether a release worked.


# TODO 5 - POST /chat.
#
# The session id is the whole trick to holding a conversation over a protocol
# that forgets you between requests:
#
#   session_id = req.session_id or uuid.uuid4().hex
#   history = memory.load(session_id)
#   reply, new_history = run_turn(req.message, history)
#   memory.save(session_id, new_history)
#   return {"reply": reply, "session_id": session_id}
#
# Load, ask, save. The model itself remembers nothing - every turn re-sends
# the whole conversation, which is why Week 04 has to bound how long it gets.


# TODO 6 - make /chat safe.
#
# Two failure paths, and they are different:
#
#   except AgentError as e     something the caller can understand and act on.
#                              Raise HTTPException(e.status, str(e)).
#   except Exception as e      a provider outage, a timeout, a bug of yours.
#                              Raise HTTPException(500, "internal error").
#
# Never let the raw exception text reach the client: it carries file paths,
# internal addresses, sometimes secrets. A stack trace in someone's browser
# is a security bug, not a debugging aid.


# TODO 7 - POST /chat/stream.
#
# Same session handling as /chat. The difference is what you return:
#
#   return StreamingResponse(
#       stream.stream_turn(req.message, history, run),
#       media_type="text/event-stream",
#       headers={"Cache-Control": "no-cache",
#                "Connection": "keep-alive",
#                "X-Accel-Buffering": "no"})
#
# `run` is a zero-argument function you define inside the handler. It calls
# run_turn, saves the memory, and returns (reply, new_history) - closing over
# the request. stream.py runs it on a worker thread, which is why it is handed
# in rather than imported.
#
# That last header matters: proxies buffer a streamed response and deliver it
# in one lump, which destroys the point silently. It tells them not to.


# TODO 8 - let `python3 -m app.main` start the service.
#
#   if __name__ == "__main__":
#       import uvicorn
#       uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 7000)))
#
# PORT comes from the environment because that is how every container platform
# tells a service where to listen. Hardcode it and you have a service that
# works locally and fails on deploy.
