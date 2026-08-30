"""Week 06: plant a bug for students to find from the traces, and remove it again.

    python -m checks.plant_bug plant     # break something, quietly
    python -m checks.plant_bug fix       # put it back

The instructor runs `plant` before the session. Students then hunt the bug by
reading traces, not by guessing - which is the actual skill of Week 06.

The bug is chosen on purpose: the agent still answers every question, returns
200 every time, and never crashes. Only the *content* is wrong. That is exactly
how AI systems fail in production, and why you need the recording.
"""
import re
import sys
from pathlib import Path

ORDERS = Path(__file__).resolve().parent.parent / "app" / "orders.py"

# The bug: the ETA is dropped from the reply the tool hands back.
#
# Chosen because the unit tests do not assert on it, so `make test` stays green
# and does not hand students the answer. The agent still answers politely, still
# returns 200, still finds the order - it just quietly stops telling anyone when
# their parcel arrives. Only reading a trace, or a customer complaining, reveals
# it. That is the whole lesson of Week 06.
GOOD = """    return (f"{key}: {order['item']}, ${order['total_usd']:.2f}, "
            f"status {order['status']}, {order['eta']}. "
            f"Note: {order['note']}")"""
BAD = """    return (f"{key}: {order['item']}, ${order['total_usd']:.2f}, "
            f"status {order['status']}. "
            f"Note: {order['note']}")"""


def plant():
    src = ORDERS.read_text()
    if BAD in src and GOOD not in src:
        print("A bug is already planted. Run `fix` first.")
        return 1
    if GOOD not in src:
        print(f"Could not find the line to change in {ORDERS}.")
        return 1
    ORDERS.write_text(src.replace(GOOD, BAD, 1))
    print("Bug planted.\n")
    print("It is subtle on purpose:")
    print("  - every request still returns 200")
    print("  - nothing crashes, no error appears anywhere")
    print("  - the order IS found, and the reply looks perfectly normal")
    print("\nTell the students only this: 'a customer complained that the agent")
    print("could not find their order, but the order definitely exists.'")
    print("\nThey should find it by reading traces. Put it back with:")
    print("  python -m checks.plant_bug fix")
    return 0


def fix():
    src = ORDERS.read_text()
    if GOOD in src:
        print("No bug planted - nothing to fix.")
        return 0
    ORDERS.write_text(re.sub(re.escape(BAD), GOOD, src, count=1))
    print("Bug removed. Run `make check-week-00` to confirm.")
    return 0


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else ""
    if what == "plant":
        raise SystemExit(plant())
    if what == "fix":
        raise SystemExit(fix())
    print("usage: python -m checks.plant_bug [plant|fix]")
    raise SystemExit(2)
