from tools.tools_definations import TOOL_REGISTRY
# context.py
context = {
    "user_lat": 12.933,
    "user_lon": 77.6105,
    "last_booking_id": None,
    "preferred_specialization": "emergency"
}


def call_tool(tool_name, params):
    tool = TOOL_REGISTRY[tool_name]
    print(f"\nCalling tool: {tool_name} with params: {params}")
    output = tool["function"](**params)
    print(f" Output: {output}")
    return output

def simulate_run():
    print("=== Test Run: Ambulance Emergency Scenario ===")

    # Step 1: User says something urgent
    user_input = "My dad collapsed. Please send help."
    print(f"\nUser: {user_input}")

    # Mock LLM reasoning — output step-by-step tool plan:
    print("\n Mock LLM reasoning...")

    ## Step 1: Get nearby ambulances
    step1 = {
        "tool_name": "get_nearby_ambulances",
        "parameters": {
            "user_lat": context["user_lat"],
            "user_lon": context["user_lon"],
            "max_distance_km": 5
        }
    }
    ambulances = call_tool(step1["tool_name"], step1["parameters"])
    selected_amb = ambulances[0] if ambulances else None
    if not selected_amb:
        print("No ambulances found.")
        return

    ## Step 2: Book ambulance
    step2 = {
        "tool_name": "book_ambulance",
        "parameters": {
            "user_lat": context["user_lat"],
            "user_lon": context["user_lon"],
            "ambulance_id": selected_amb["id"]
        }
    }
    booking_id = call_tool(step2["tool_name"], step2["parameters"])
    context["last_booking_id"] = booking_id

    # Step 3: Estimate ETA 
    from tools.ambulance_utils import haversine
    # For demonstration, use ambulance location as destination
    distance = haversine(
        context["user_lat"], context["user_lon"],
        selected_amb["lat"], selected_amb["lon"]
    )
    step3 = {
        "tool_name": "estimate_eta_km",
        "parameters": {
            "speed_kmph": 40,
            "distance_km": distance
        }
    }
    eta = call_tool(step3["tool_name"], step3["parameters"])

    #  Final Summary
    print("\n===  Final Agent Summary ===")
    print(f" Ambulance: {selected_amb['driver']} (ID {selected_amb['id']})")
    print(f" ETA: {eta:.2f} minutes")
    print(f"Booking ID: {booking_id}")

if __name__ == "__main__":
    simulate_run()
    print("\n===Test Run Completed ===")