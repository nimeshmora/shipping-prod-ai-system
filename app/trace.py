"""app/trace.py - Week 05. BUILD THIS FILE.

One JSON trace per turn, so you can see what happened.

THE PREMISE OF THIS WEEK
------------------------
A broken agent still returns 200 OK. Nothing crashes - no exception, no 500, no
red graph. The answers just quietly get worse: the loop takes more steps, tools
start failing and the model apologises instead, the bill creeps up, the slow
tail grows. None of that appears in an HTTP status code.

So you write down what happened on every turn, as one JSON line on stdout.
Cloud Run and every log platform read stdout, so printing IS shipping telemetry.

What to build
-------------
1. `new_trace(session_id)` -> a dict with these keys, zeroed:

       turn_id           uuid4().hex - one turn, findable in the logs
       session_id
       started_at        time.time()
       steps             filled by the agent loop
       token_count
       input_tokens      kept apart from output: they are BILLED apart
       output_tokens
       tools_used        [] - which tools ran
       tool_errors       [] - which of them broke
       step_ms           [] - how long each trip round the loop took
       tool_ms           [] - how long each tool call took
       model_calls       []
       error             None
       cost_usd          0.0

   Two of these are worth pausing on.

   step_ms AND tool_ms, separately. "This turn took 8 seconds" is useless on
   its own - you need to know whether the MODEL was slow or YOUR TOOL was slow,
   because those have completely different fixes.

   tool_errors, at all. A tool that fails hands its error text back to the
   model, which apologises politely, and the turn returns 200. This is the only
   place that breakage is visible.

2. `cost_of(input_tokens, output_tokens)` using two rates from the env:

       COST_PER_1M_INPUT   default 3.00
       COST_PER_1M_OUTPUT  default 15.00

   Priced separately because output costs 3-5x input. A long-context agent is
   mostly input tokens, so a blended average overstates it several times over -
   and then nobody trusts the number. Keep an `estimate_cost(total)` blended
   fallback for gateways that only report a total.

3. `_redact(value)` walking dicts and lists, replacing anything whose key looks
   like a secret ("api_key", "token", "secret", "password", "authorization")
   with "[redacted]".

   THE TRAP: that match is on SUBSTRING, so `input_tokens` and `token_count`
   are caught by a rule meant for `api_token`. Failing safe is the right
   default - so keep an explicit allow-set for the counters, or your trace
   lies about its own inputs.

4. `emit(trace)` which finalises and prints:

       duration_ms   from started_at
       cost_usd      from the input/output split, falling back to the blended
                     estimate when there is no split
       severity      "ERROR" if trace["error"] else "INFO"
       message       a short human line

   severity is NOT for you - it is for the log platform. Cloud Logging reads
   that exact field to decide whether a line is routine. Without it every line
   lands as INFO, a failed turn looks identical to a successful one, and
   nothing ever pages anybody.

   Make emit() IDEMPOTENT: set a private flag and return early if it has
   already run. The streaming path finalises early so its `done` frame can
   report real numbers, and the request's finally block calls emit() again to
   guarantee it happens at all. Without the guard, every streamed turn is
   logged twice and /metrics counts it twice. Do not print keys starting "_".

Then wire it in
---------------
app/agent.py: run_turn takes `trace=None` and returns
(reply, history, trace). Time each step, record tools, tokens and tool errors.
Pass the trace to model_fn only if it accepts one - the fakes in the tests take
a single argument, so inspect the signature rather than making every fake grow
a parameter it does not use.

app/main.py: build a trace per request, and in a `finally` block call
trace.emit(t) then monitor.record(t).

Done when
---------
    make check-week-05

Stuck? git diff week-05-see..week-05-solution -- app/trace.py
"""

# your code here
