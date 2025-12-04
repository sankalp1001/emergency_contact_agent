"""
Emergency Dispatcher Module
Contains tools for ambulance, fire, and police emergency services
"""

from .ambulance_tools import (
    # Functions
    get_all_ambulances,
    get_available_ambulances,
    get_nearby_ambulances,
    get_nearest_ambulance,
    dispatch_ambulance,
    dispatch_nearest_ambulance,
    update_ambulance_status,
    complete_dispatch as complete_ambulance_dispatch,
    get_dispatch_history as get_ambulance_dispatch_history,
    assess_ambulance_need,
    # Tool definitions
    AMBULANCE_TOOLS
)

from .fire_tools import (
    # Functions
    get_all_fire_stations,
    get_available_fire_trucks,
    get_nearby_fire_stations,
    get_nearby_fire_trucks,
    dispatch_fire_truck,
    dispatch_nearest_fire_truck,
    dispatch_multiple_units as dispatch_multiple_fire_units,
    update_fire_truck_status,
    complete_fire_dispatch,
    assess_fire_severity,
    # Tool definitions
    FIRE_TOOLS
)

from .police_tools import (
    # Functions
    get_all_police_stations,
    get_available_patrol_units,
    get_nearby_police_stations,
    get_nearby_patrol_units,
    dispatch_patrol_unit,
    dispatch_nearest_patrol_unit,
    dispatch_multiple_units as dispatch_multiple_police_units,
    create_case,
    update_case_status,
    update_patrol_unit_status,
    complete_police_dispatch,
    assess_threat_level,
    get_safety_instructions,
    # Tool definitions
    POLICE_TOOLS
)

from .setup_database import setup_all_databases, setup_ambulance_db, setup_fire_db, setup_police_db

from .state_tools import (
    classify_emergency,
    set_user_location,
    update_medical_info,
    update_fire_info,
    update_police_info,
    STATE_TOOLS
)

# Combined tool definitions for LLM
ALL_TOOLS = AMBULANCE_TOOLS + FIRE_TOOLS + POLICE_TOOLS

# Tool function mapping for executing tool calls
TOOL_FUNCTIONS = {
    # Ambulance tools
    "get_nearby_ambulances": get_nearby_ambulances,
    "dispatch_nearest_ambulance": dispatch_nearest_ambulance,
    "assess_ambulance_need": assess_ambulance_need,
    "get_available_ambulances": get_available_ambulances,
    "update_ambulance_status": update_ambulance_status,
    
    # Fire tools
    "get_nearby_fire_stations": get_nearby_fire_stations,
    "dispatch_nearest_fire_truck": dispatch_nearest_fire_truck,
    "dispatch_multiple_units": dispatch_multiple_fire_units,  # Note: context determines which one
    "assess_fire_severity": assess_fire_severity,
    "get_available_fire_trucks": get_available_fire_trucks,
    "update_fire_truck_status": update_fire_truck_status,
    
    # Police tools
    "get_nearby_patrol_units": get_nearby_patrol_units,
    "dispatch_nearest_patrol_unit": dispatch_nearest_patrol_unit,
    "assess_threat_level": assess_threat_level,
    "create_case": create_case,
    "get_safety_instructions": get_safety_instructions,
    "get_available_patrol_units": get_available_patrol_units,
    "update_case_status": update_case_status,
}

__all__ = [
    # Ambulance
    'get_all_ambulances',
    'get_available_ambulances', 
    'get_nearby_ambulances',
    'get_nearest_ambulance',
    'dispatch_ambulance',
    'dispatch_nearest_ambulance',
    'update_ambulance_status',
    'complete_ambulance_dispatch',
    'get_ambulance_dispatch_history',
    'assess_ambulance_need',
    'AMBULANCE_TOOLS',
    
    # Fire
    'get_all_fire_stations',
    'get_available_fire_trucks',
    'get_nearby_fire_stations',
    'get_nearby_fire_trucks',
    'dispatch_fire_truck',
    'dispatch_nearest_fire_truck',
    'dispatch_multiple_fire_units',
    'update_fire_truck_status',
    'complete_fire_dispatch',
    'assess_fire_severity',
    'FIRE_TOOLS',
    
    # Police
    'get_all_police_stations',
    'get_available_patrol_units',
    'get_nearby_police_stations',
    'get_nearby_patrol_units',
    'dispatch_patrol_unit',
    'dispatch_nearest_patrol_unit',
    'dispatch_multiple_police_units',
    'create_case',
    'update_case_status',
    'update_patrol_unit_status',
    'complete_police_dispatch',
    'assess_threat_level',
    'get_safety_instructions',
    'POLICE_TOOLS',
    
    # Setup
    'setup_all_databases',
    'setup_ambulance_db',
    'setup_fire_db',
    'setup_police_db',
    
    # State tools
    'classify_emergency',
    'set_user_location',
    'update_medical_info',
    'update_fire_info',
    'update_police_info',
    'STATE_TOOLS',
    
    # Combined
    'ALL_TOOLS',
    'TOOL_FUNCTIONS',
]

