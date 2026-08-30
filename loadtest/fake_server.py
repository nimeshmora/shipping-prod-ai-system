"""A real app instance with a fake model, for load testing without an API key.

The whole point of a load test is to exercise YOUR code - the rate limiter, the
trace, the monitor window, the streaming plumbing - under concurrency. None of
that needs a real model, and paying a provider to answer 500 identical
questions teaches you nothing. So the model is faked and everything else is
exactly the app you deploy.

    PYTHONPATH=. python -m loadtest.fake_server --port 8099
"""
import argparse
from types import SimpleNamespace as NS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8099)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()

    import app.agent as agent
    import app.main as main_mod

    def fake(messages, trace=None):
        return NS(content=[NS(type="text",
                              text="Order ORD-1002 is a standing desk, arriving Thursday.")],
                  stop_reason="end_turn",
                  usage=NS(input_tokens=140, output_tokens=25))

    real_run_turn = agent.run_turn
    main_mod.run_turn = lambda m, history=None, trace=None: real_run_turn(
        m, history, model_fn=fake, trace=trace)

    import uvicorn
    uvicorn.run(main_mod.app, host=args.host, port=args.port, log_level="error")


if __name__ == "__main__":
    main()
