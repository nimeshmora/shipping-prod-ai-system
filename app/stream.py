"""Week 01: streaming, because 8 seconds of nothing feels broken.

The agent's answer takes as long as it takes. What you control is whether the
user watches a spinner for all of it, or sees words appear after 400ms. Same
total duration, completely different product - which is why every assistant
you have ever used streams.

The metric this is about is TTFB - time to first byte. p95 duration (Week 05)
tells you how long the whole turn took. TTFB tells you how long the user
stared at nothing. They are different numbers and they need different fixes:
a slow turn is a model or tool problem, a slow TTFB is an architecture one.

Why this is a separate module
-----------------------------
The blocking loop in agent.py stays exactly as it is, and /chat keeps
returning one JSON object. That is deliberate:

  - the eval gate (Week 08) grades a complete answer, not a token stream
  - the trace (Week 05) is finalised once, at the end, in one place
  - every test keeps working

So streaming is an additional way to READ the same turn, not a rewrite of it.
When you add a capability to a system that already has budgets, traces and a
gate wired through it, the cheap move is usually a new surface over the old
engine rather than a new engine.

The honest limitation
---------------------
This streams the SHAPE of the turn - each step, each tool call, then the
answer text in chunks - rather than tokens straight off the provider socket.
True token streaming means passing stream=True down to the provider and
threading partial deltas back up through the loop, the budget and the trace.
That is a genuinely bigger change, and the sequence of events a client has to
handle is identical either way, which is why this is the right shape to teach
first. `guide/week-01.md` says what changes if you go the rest of the way.
"""
import asyncio
import json


CHUNK_WORDS = 8          # words per text frame; small enough to look alive


def sse(event, data):
    """One server-sent event. The blank line at the end is not optional -
    it is what tells the client the frame is complete."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def stream_turn(message, history, run, trace, finalise=None):
    """Yield SSE frames for one turn.

    `run` is a zero-argument callable that performs the blocking turn. It is
    handed in rather than imported so the caller stays in charge of guardrails
    and memory, and so tests can pass a fake.

    `finalise` closes the trace (duration, cost) before the `done` frame is
    built, so the summary the client receives carries real numbers.

    Frame sequence, which a client can rely on:

        start   -> the turn was accepted; session and turn ids
        status  -> something happened (a tool ran, a step finished)
        token   -> a piece of the answer
        done    -> the turn is finished, with steps / tokens / cost
        error   -> the turn failed; always the last frame if present
    """
    yield sse("start", {"session_id": trace["session_id"],
                        "turn_id": trace["turn_id"]})

    loop = asyncio.get_running_loop()
    try:
        # The loop is synchronous and does network I/O, so it must not run on
        # the event loop thread - that would block every other request in this
        # container. run_in_executor hands it to a worker thread.
        reply, history_out = await loop.run_in_executor(None, run)
    except Exception as e:
        # Streaming responses have already sent HTTP 200 by the time this
        # happens, so there is no status code left to fail with. The error has
        # to travel as a frame, and the client has to actually read it.
        # Forgetting this is how a streamed agent "succeeds" while showing the
        # user half an answer.
        #
        # Record it on the trace TOO. This is the same trap /chat has in
        # main.py: catch the exception but forget the trace, and a total
        # outage is logged as "error": null while /metrics reports a 0% error
        # rate. The streaming path has its own copy of that trap, and one
        # `except` that only writes a frame is how you fall into it.
        trace["error"] = f"{type(e).__name__}: {e}"
        if finalise is not None:
            finalise(trace)
        yield sse("error", {"message": f"{type(e).__name__}: {e}"})
        return

    for tool in trace.get("tools_used", []):
        yield sse("status", {"tool": tool})

    words = reply.split(" ")
    for i in range(0, len(words), CHUNK_WORDS):
        yield sse("token", {"text": " ".join(words[i:i + CHUNK_WORDS]) + " "})
        await asyncio.sleep(0)        # let the server actually flush

    # Finalise before the summary frame, or `done` reports the zeros the trace
    # was born with: duration_ms and cost_usd are computed by emit(), and the
    # caller's finally block runs AFTER this generator is exhausted.
    if finalise is not None:
        finalise(trace)

    yield sse("done", {"steps": trace.get("steps", 0),
                       "tokens": trace.get("token_count", 0),
                       "cost_usd": trace.get("cost_usd", 0.0),
                       "duration_ms": trace.get("duration_ms", 0)})
    return
