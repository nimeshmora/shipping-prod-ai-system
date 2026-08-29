# Guide Week 7 · Attack

**Goal:** attack the agent to see the holes, then close them.

## The idea

Play the attacker first, so the danger is real. Then put up plain fences: limit
input size, block dangerous input, allow tools to reach only trusted sites (never
your private network), and keep secrets out of reach.

## Do this

1. Try to break an un-hardened agent and watch it misbehave.
2. The fences are already in `app/guardrails.py`
   (`check_input_length`, `check_blocked_input`, `check_url`) and wired in
   `app/main.py`.
3. Tune the input cap:

```bash
export MAX_INPUT_CHARS=4000
```

4. Attack again and watch the fences hold. Then ask the agent about
   `ORD-1043`: its note contains an instruction aimed at the model, the way
   real customer-entered data does. Check the trace for
   `tool_output_filtered: true`.

## Check it works

```bash
make check-week-07
```

This sends oversized input, dangerous input, and a bad URL, and proves each is
refused.

## Done when

- Oversized input, dangerous input, and untrusted URLs are all refused.

**Pull request:** `week-07-<your-name>`, `week 07: attack and defend`.
