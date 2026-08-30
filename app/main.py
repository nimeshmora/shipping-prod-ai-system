"""app/main.py - Week 01. BUILD THIS FILE.

The agent's front door. Three routes, and the shapes below are a contract:
`make check-week-01` asserts on them, and so would any client.

    GET  /health        -> {"status": "ok"}
    POST /chat          -> {"reply": "<text>", "session_id": "<id>"}
    POST /chat/stream   -> text/event-stream  (see app/stream.py)

Both POST routes accept a JSON body:

    {"message": "where is my order ORD-1002?", "session_id": "<optional>"}

What you have to work with
--------------------------
    from app.agent import AgentError, run_turn
    from app import memory, stream

    run_turn(message, history)  -> (reply_text, new_history)
    memory.load(session_id)     -> the history so far (a list; [] if new)
    memory.save(session_id, h)  -> store it

    AgentError has a .status you should use as the HTTP status code.

What to build, and the reasoning behind each part
-------------------------------------------------
1. The FastAPI app itself, named `app` at module level. Uvicorn is told to
   look for `app.main:app`, so the name is not optional.

2. A request model. Declare the body as a pydantic BaseModel with
   `message: str` and `session_id: str | None = None`. Do this rather than
   reading a raw dict: FastAPI then rejects a request with no `message` as a
   422 before your handler runs. A guardrail you get for free by declaring
   the shape.

3. GET /health returning {"status": "ok"}.

   Keep it trivial. No model call, no memory read, no database. A health
   check that depends on your dependencies will fail during someone else's
   outage and get your container restarted for no reason. Week 02's deploy
   pipeline polls this to decide whether a release worked, so it has to mean
   "this process is up" and nothing more.

4. POST /chat.

   The session id is the whole trick to holding a conversation over a
   stateless protocol:

       session_id = req.session_id or uuid.uuid4().hex

   ... then load that session's history, run the turn, save the new history,
   and return the reply WITH the session id so the caller can send it back.
   The model itself remembers nothing - every turn re-sends the whole
   conversation, which is why Week 04 has to bound how long it can get.

   Two failure paths, and they are different:

     - AgentError      something the caller can understand and act on.
                       Raise HTTPException with e.status and str(e).
     - anything else   a provider outage, a timeout, a bug of yours.
                       Return a 500 with a generic detail like
                       "internal error". Never let the raw exception text
                       reach the client: it carries internals, sometimes
                       secrets, and a stack trace in someone's browser is a
                       security bug, not a debugging aid.

5. POST /chat/stream.

   Same session handling as /chat. The difference is what you return:

       return StreamingResponse(
           stream.stream_turn(req.message, history, run),
           media_type="text/event-stream",
           headers={...})

   `run` is a zero-argument function you define inside the handler. It calls
   run_turn, saves the memory, and returns (reply, new_history) - closing
   over the request. stream.py calls it on a worker thread, which is why it
   is handed in rather than imported.

   Three headers matter:

       Cache-Control: no-cache
       Connection: keep-alive
       X-Accel-Buffering: no

   That last one is the one people forget. Cloud Run, nginx and most proxies
   will buffer your entire response and deliver it in one lump - which
   defeats the whole feature, silently, because the answer is still correct.

   Note also: everything before the first frame is identical to /chat. A
   streaming endpoint is not a side door. In Week 03, when auth and rate
   limits arrive, they have to guard both.

6. The __main__ block, so `make run` works:

       if __name__ == "__main__":
           import uvicorn
           uvicorn.run(app, host="0.0.0.0",
                       port=int(os.environ.get("PORT", 8080)))

   Read the port from the environment. Every container platform tells your
   service where to listen that way. Hardcode 8080 and you have a service
   that works locally and fails on deploy.

Done when
---------
    make check-week-01

Each failure names the exact thing to fix. Stuck? The answer key is the
`week-01-solution` branch:

    git diff week-01-package..week-01-solution -- app/main.py
"""

# your code here
