CONTEXT = {
    "user_lat": 12.9335,
    "user_lon": 77.6105,
    "last_booking_id": None,
    "preferred_specialization": "cardiology"
}

business_state = {
    "location": None,
    "ambulance_booked": False,
    "hospital_assigned": False,
}

execution_state = {
    "steps_taken": [],
    "last_tool": None,
    "last_result": None,
    "errors": [],
}

def summarize_state(business_state, execution_state):
    return f"""BUSINESS STATE:
- Location: {business_state['location']}
- Ambulance Booked: {business_state['ambulance_booked']}
- Hospital Assigned: {business_state['hospital_assigned']}

EXECUTION STATE:
- Steps Taken: {', '.join(execution_state['steps_taken'])}
- Last Tool Used: {execution_state['last_tool']}
- Last Tool Result: {execution_state['last_result']}
- Errors: {', '.join(execution_state['errors']) if execution_state['errors'] else 'None'}
"""
