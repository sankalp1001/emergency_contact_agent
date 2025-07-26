from connect_LLM import run_agent_conversation
from state_manager import CONTEXT

while True:
    user_input = input("User: ")
    if user_input.lower() in {"exit", "quit"}:
        break

    result = run_agent_conversation(user_input, CONTEXT)
    print("Agent:", result)
