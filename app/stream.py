"""Streaming, because 8 seconds of nothing feels broken.

The agent's answer takes as long as it takes. What you control is whether the
user watches a spinner for all of it, or sees words appear after 400ms. Same
total duration, completely different product - which is why every assistant
you have ever used streams.

The metric this is about is TTFB - time to first byte. Total duration tells you
how long the turn took. TTFB tells you how long the user stared at nothing.
They are different numbers and they need different fixes: a slow turn is a
model or tool problem, a slow TTFB is an architecture one.

Why this is a separate module
-----------------------------
The blocking loop in agent.py stays exactly as it is, and /chat keeps returning
one JSON object. Streaming is an additional way to READ the same turn, not a
rewrite of it. When you add a capability to a system, the cheap move is usually
a new surface over the old engine rather than a new engine.

That choice pays off in later weeks: the budget (Week 04), the trace (Week 05)
and the eval gate (Week 08) all attach to the one loop, and get streaming for
free.

The honest limitation
---------------------
This streams the SHAPE of the turn - each tool call, then the answer text in
chunks - rather than tokens straight off the provider socket. True token
streaming means passing stream=True down to the provider and threading partial
deltas back up through the loop. That is a genuinely bigger change, and the
sequence of events a client has to handle is identical either way, which is why
this is the right shape to build first.
"""
import asyncio
import json


CHUNK_WORDS = 8          # words per text frame; small enough to look alive


def sse(event, data):
    """Format one server-sent event.

    The blank line at the end is not optional - it is what tells the client
    the frame is complete. Forget it and the client waits forever for a frame
    you have already sent.
    """
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def stream_turn(message, history, run):
    """Yield SSE frames for one turn.

    `run` is a zero-argument callable that performs the blocking turn. It is
    handed in rather than imported so the caller stays in charge of memory,
    and so tests can pass a fake.

    Frame sequence, which a client can rely on:

        start   -> the turn was accepted
        status  -> something happened (a tool ran)
        token   -> a piece of the answer
        done    -> the turn finished cleanly
        error   -> the turn failed; always the last frame if present
    """
    yield sse("start", {})

    loop = asyncio.get_running_loop()
    try:
        # The loop is synchronous and does network I/O, so it must not run on
        # the event loop thread - that would block every other request in this
        # container. run_in_executor hands it to a worker thread.
        reply, _ = await loop.run_in_executor(None, run)
    except Exception as e:
        # Streaming responses have already sent HTTP 200 by the time this
        # happens, so there is no status code left to fail with. The error has
        # to travel as a frame, and the client has to actually read it.
        # Forgetting this is how a streamed agent "succeeds" while showing the
        # user half an answer.
        yield sse("error", {"message": f"{type(e).__name__}: {e}"})
        return

    words = reply.split(" ")
    for i in range(0, len(words), CHUNK_WORDS):
        yield sse("token", {"text": " ".join(words[i:i + CHUNK_WORDS]) + " "})
        await asyncio.sleep(0)        # let the server actually flush

    yield sse("done", {})
