import re
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from typing import Dict, Any, Tuple
from tools.tools_definations import TOOL_REGISTRY
from connect_LLM import call_llm

# Initial states
business_state = {
    "ambulance_booked": False,
}
execution_state = {
    "user_lat": None,
    "user_lon": None,
    "ambulance_id": None,
    "ETA": None
}

# Prompt template
SYSTEM_PROMPT = """
You are an emergency response agent helping people in emergencies. You can take actions using tools, but you must always communicate with the user in a natural, empathetic, and helpful way, like a real 911 operator.

TOOLS:
{tools}

You must always return the following fields:
THOUGHT: What you're thinking (not shown to user)
ACTION: One of [{tool_names}]
PARAMS: JSON dict with required keys
STATE_UPDATE: JSON of keys to update in state
USER_MESSAGE: What you say to the user (question, update, reassurance, etc.)

Example:
THOUGHT: I need user's location
ACTION: get_current_location
PARAMS: {{}}
STATE_UPDATE: {{}}
USER_MESSAGE: Can you please share your current location so I can send help?

If task is complete, return:
THOUGHT: The task is complete.
ACTION: inform_user
PARAMS: {{"message": "Your ambulance is arriving in 3 minutes."}}
STATE_UPDATE: {{}}
USER_MESSAGE: Your ambulance is on the way and will arrive in 3 minutes. Please stay calm and let me know if you need anything else.
"""


THOUGHT_RE = re.compile(r"THOUGHT:\s*(.*)")
ACTION_RE = re.compile(r"ACTION:\s*(.*)")
PARAMS_RE = re.compile(r"PARAMS:\s*(\{.*?\})")
STATE_UPDATE_RE = re.compile(r"STATE_UPDATE:\s*(\{.*?\})")
USER_MESSAGE_RE = re.compile(r"USER_MESSAGE:\s*(.*)")


def render_system_prompt():
    tool_descriptions = "\n".join(
        [f"- {k}: {v['description']} (inputs: {', '.join(v.get('inputs', []))})" for k, v in TOOL_REGISTRY.items()]
    )
    return SYSTEM_PROMPT.format(tools=tool_descriptions, tool_names=", ".join(TOOL_REGISTRY))


def parse_response(response: str) -> Tuple[str, str, Dict[str, Any], Dict[str, Any], str]:
    thought = THOUGHT_RE.search(response).group(1).strip() if THOUGHT_RE.search(response) else ""
    action = ACTION_RE.search(response).group(1).strip() if ACTION_RE.search(response) else ""
    params = eval(PARAMS_RE.search(response).group(1)) if PARAMS_RE.search(response) else {}
    state_update = eval(STATE_UPDATE_RE.search(response).group(1)) if STATE_UPDATE_RE.search(response) else {}
    user_message = USER_MESSAGE_RE.search(response).group(1).strip() if USER_MESSAGE_RE.search(response) else ""
    return thought, action, params, state_update, user_message


def apply_state_update(update: Dict[str, Any]):
    for k, v in update.items():
        key = k.lower().replace(" ", "_")
        if key in business_state:
            business_state[key] = v
        if key in execution_state:
            execution_state[key] = v


def run_agent(user_message: str, conversation=None):
    # conversation: list of (sender, message) tuples
    chat_turns = []
    if conversation is None:
        conversation = [("user", user_message)]
    else:
        chat_turns = conversation.copy()

    # Build conversation string for LLM
    conversation_str = "\n".join([
        ("User: " if sender == "user" else "Agent: ") + msg for sender, msg in conversation
    ])

    while True:
        prompt = render_system_prompt()
        full_prompt = f"{prompt}\n\nConversation so far:\n{conversation_str}\n\nCurrent State:\nBusiness: {business_state}\nExecution: {execution_state}"

        # Call the LLM
        response = call_llm(full_prompt)

        # Parse
        thought, action, params, state_update, user_message_out = parse_response(response)

        apply_state_update(state_update)

        if user_message_out:
            chat_turns.append(("agent", user_message_out))
            conversation_str += f"\nAgent: {user_message_out}"

        if action == "inform_user":
            break

        if action not in TOOL_REGISTRY:
            chat_turns.append(("agent", f"Unknown tool: {action}"))
            break

        tool_func = TOOL_REGISTRY[action]["function"]
        result = tool_func(**params)

        # If the tool result is a user-facing update, show it (optional, fallback)
        if action == "estimate_eta_km" and not user_message_out:
            chat_turns.append(("agent", f"Your ambulance is arriving in {result} minutes."))
            conversation_str += f"\nAgent: Your ambulance is arriving in {result} minutes."
            break

        # Add the tool result as the next user message (if needed)
        conversation_str += f"\nUser: {result}"

    return chat_turns


if __name__ == "__main__":
    run_agent("I need an ambulance at my location")