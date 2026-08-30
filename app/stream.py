"""app/stream.py - Week 01. BUILD THIS FILE.

Streaming, because 8 seconds of nothing feels broken. 8 seconds with words
appearing after 400ms feels fast. Same total duration, completely different
product - which is why every assistant you have ever used streams.

The number this is about is TTFB, time to first byte: how long the user stared
at nothing. Total duration tells you how long the turn took. They are different
numbers needing different fixes - a slow turn is a model or tool problem, a slow
TTFB is an architecture one.

The wire format
---------------
Server-sent events. Each frame is exactly:

    event: <name>\\ndata: <json>\\n\\n

The trailing blank line is NOT optional - it is what tells the client the frame
is complete. Leave it out and the client waits forever for something you have
already sent.

The sequence a client can rely on:

    event: start      the turn was accepted
    data: {}

    event: token      a piece of the answer (many of these)
    data: {"text": "Your standing desk "}

    event: done       finished cleanly
    data: {}

    event: error      it failed; always the last frame if it appears
    data: {"message": "..."}

What to build
-------------
1. `sse(event, data)` -> the formatted frame string. json.dumps the data.

2. `async def stream_turn(message, history, run)` - an async generator that
   yields frames.

   `run` is a zero-argument callable from main.py that performs the blocking
   turn and returns (reply, new_history).

   The order of business:

     a. yield a `start` frame immediately. This is what makes the UI feel
        alive before the model has said anything.

     b. run the turn - but NOT on the event loop thread:

            loop = asyncio.get_running_loop()
            reply, _ = await loop.run_in_executor(None, run)

        run_turn is synchronous and does network I/O. Call it directly in an
        async handler and it blocks every other request in this container.
        This is the single most common way a streaming endpoint makes overall
        latency worse instead of better.

     c. if that raised, yield an `error` frame and return.

        This is the subtle one. By the time the model fails, you have already
        sent HTTP 200 - the status line went out with the first frame. There
        is no status code left to fail with, so the error has to travel as a
        frame. Miss it and a streamed agent "succeeds" while showing the user
        half an answer.

     d. split the reply and yield `token` frames. Chunk it - a module-level
        CHUNK_WORDS of about 8 reads well. After each frame:

            await asyncio.sleep(0)

        which yields control so the server actually flushes rather than
        buffering your whole loop.

     e. yield a `done` frame.

Why this is a separate module
-----------------------------
The blocking loop in agent.py does not change, and /chat keeps returning one
JSON object. Streaming is an additional way to READ the same turn, not a
rewrite of it. That choice is what lets the budget (Week 04), the trace
(Week 05) and the eval gate (Week 08) attach to one loop and get streaming for
free.

The honest limitation
---------------------
This streams the SHAPE of the turn, not tokens straight off the provider
socket. True token streaming means passing stream=True down to the provider and
threading partial deltas back up through the loop - a genuinely bigger change.
The frame sequence a client handles is identical either way, which is why this
is the right shape to build first.

Done when
---------
    make check-week-01

Stuck? git diff week-01-package..week-01-solution -- app/stream.py
"""

# your code here
