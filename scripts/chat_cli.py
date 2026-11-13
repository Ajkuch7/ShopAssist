"""Interactive terminal chat for the guided ShopAssist agent."""

import argparse
import sys
import uuid
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agent.graph import reset_session, run_turn


GREY = "\033[90m"
RESET = "\033[0m"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--customer", type=int, required=True)
    args = parser.parse_args()
    session_id = str(uuid.uuid4())
    print("ShopAssist is ready. Type /reset to start over or /quit to exit.")
    while True:
        try:
            message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if message == "/quit":
            break
        if message == "/reset":
            reset_session(session_id)
            session_id = str(uuid.uuid4())
            print("Session reset.")
            continue
        if not message:
            continue
        result = run_turn(message, session_id, args.customer, use_llm=True)
        if result["tools_used"]:
            print(f"{GREY}Tools: {', '.join(result['tools_used'])}{RESET}")
        print(f"ShopAssist: {result['reply']}")
        if result["conversation_ended"]:
            break


if __name__ == "__main__":
    main()
