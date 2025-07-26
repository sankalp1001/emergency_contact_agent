# agent.py
import re
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
You are an emergency response agent that can take actions using tools.
Based on user input and state, decide what to do.

TOOLS:
{tools}

You must always return the following fields:
THOUGHT: What you're thinking
ACTION: One of [{tool_names}]
PARAMS: JSON dict with required keys
STATE_UPDATE: JSON of keys to update in state

Example:
THOUGHT: I need user's location
ACTION: get_current_location
PARAMS: {{"user_lat": 12.9, "user_lon": 77.6}}
STATE_UPDATE: {{}}

If task is complete, return:
THOUGHT: The task is complete.
ACTION: inform_user
PARAMS: {{"message": "Your ambulance is arriving in 3 minutes."}}
STATE_UPDATE: {{}}
"""

THOUGHT_RE = re.compile(r"THOUGHT:\s*(.*)")
ACTION_RE = re.compile(r"ACTION:\s*(.*)")
PARAMS_RE = re.compile(r"PARAMS:\s*(\{.*?\})")
STATE_UPDATE_RE = re.compile(r"STATE_UPDATE:\s*(\{.*?\})")


def render_system_prompt():
    tool_descriptions = "\n".join(
        [f"- {k}: {v['description']} (inputs: {', '.join(v.get('inputs', []))})" for k, v in TOOL_REGISTRY.items()]
    )
    return SYSTEM_PROMPT.format(tools=tool_descriptions, tool_names=", ".join(TOOL_REGISTRY))


def parse_response(response: str) -> Tuple[str, str, Dict[str, Any], Dict[str, Any]]:
    thought = THOUGHT_RE.search(response).group(1).strip()
    action = ACTION_RE.search(response).group(1).strip()
    params = eval(PARAMS_RE.search(response).group(1))
    state_update = eval(STATE_UPDATE_RE.search(response).group(1))
    return thought, action, params, state_update


def apply_state_update(update: Dict[str, Any]):
    for k, v in update.items():
        key = k.lower().replace(" ", "_")
        if key in business_state:
            business_state[key] = v
        if key in execution_state:
            execution_state[key] = v


def run_agent(user_message: str):
    print("\nUser:", user_message)

    while True:
        prompt = render_system_prompt()
        full_prompt = f"{prompt}\n\nUser message: {user_message}\n\nCurrent State:\nBusiness: {business_state}\nExecution: {execution_state}"

        # Call the LLM
        response = call_llm(full_prompt)
        print("\nAgent Response:\n", response)

        # Parse
        thought, action, params, state_update = parse_response(response)
        print(f"\nThought: {thought}\nAction: {action}\nParams: {params}\nState Update: {state_update}")

        apply_state_update(state_update)

        if action == "inform_user":
            print("\nFinal Message to User:", params.get("message"))
            break

        if action not in TOOL_REGISTRY:
            print("\nUnknown tool:", action)
            break

        tool_func = TOOL_REGISTRY[action]["function"]
        result = tool_func(**params)
        print("\nTool Result:", result)

        # If ETA has been estimated, inform user and exit
        if action == "estimate_eta_km":
            print(f"\n Final Message to User: Your ambulance is arriving in {result} minutes.")
            break

        user_message = result   # Pass tool result to next loop


if __name__ == "__main__":
    run_agent("I need an ambulance at my location")
