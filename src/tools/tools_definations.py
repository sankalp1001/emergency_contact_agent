from tools.ambulance_utils import (
    get_nearby_ambulances,
    book_ambulance,
    update_booking_status,
    cancel_booking,
    get_booking_status,
    estimate_eta_km
)

TOOL_REGISTRY = {

    "get_current_location": {
        "function": lambda: {"user_lat": 12.933,  "user_lon": 77.6105,},
        "description": "Get the current user location",
    },
    "get_nearby_ambulances": {
        "function": get_nearby_ambulances,
        "description": "Get ambulances within a distance from user location",
        "inputs": ["user_lat", "user_lon", "max_distance_km"]
    },
    "book_ambulance": {
    "function": book_ambulance,
    "description": "Book a specific ambulance",
    "inputs": ["user_lat", "user_lon", "ambulance_id"]
},

    "update_booking_status": {
        "function": update_booking_status,
        "description": "Update a booking status to confirmed, cancelled, etc.",
        "inputs": ["booking_id", "status"]
    },
    "estimate_eta_km": {
        "function": estimate_eta_km,
        "description": "Estimate ETA given speed and distance",
        "inputs": ["speed_kmph", "distance_km"]
    },
    "get_booking_status": {
        "function": get_booking_status,
        "description": "Get current status of a booking",
        "inputs": ["booking_id"]
    },
    "cancel_booking": {
        "function": cancel_booking,
        "description": "Cancel a booking and free the ambulance",
        "inputs": ["booking_id"]
    }
}
if __name__ == "__main__":
    print("=== TOOL REGISTRY ===")
    for name, tool in TOOL_REGISTRY.items():
        print(f"{name}: {tool['description']}")
        if "inputs" in tool:
            print(f"  Inputs: {', '.join(tool['inputs'])}")
        print(f"  Function: {tool['function'].__name__}\n")