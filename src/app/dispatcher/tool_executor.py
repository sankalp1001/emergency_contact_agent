"""
Tool Executor Module
Handles execution of tool calls from the LLM
"""

import json
from typing import Dict, Any, Callable

from .ambulance_tools import (
    get_nearby_ambulances,
    dispatch_nearest_ambulance,
    assess_ambulance_need,
    get_available_ambulances,
    update_ambulance_status,
)

from .fire_tools import (
    get_nearby_fire_stations,
    get_nearby_fire_trucks,
    dispatch_nearest_fire_truck,
    dispatch_multiple_units as dispatch_multiple_fire_units,
    assess_fire_severity,
    get_available_fire_trucks,
    update_fire_truck_status,
)

from .police_tools import (
    get_nearby_patrol_units,
    dispatch_nearest_patrol_unit,
    dispatch_multiple_units as dispatch_multiple_police_units,
    assess_threat_level,
    create_case,
    get_safety_instructions,
    get_available_patrol_units,
    update_case_status,
)

from .state_tools import (
    classify_emergency,
    set_user_location,
    lookup_location_by_area,
    update_medical_info,
    update_fire_info,
    update_police_info,
)


# Complete mapping of tool names to their functions
TOOL_REGISTRY: Dict[str, Callable] = {
    # ========== STATE MANAGEMENT TOOLS ==========
    "classify_emergency": classify_emergency,
    "set_user_location": set_user_location,
    "lookup_location_by_area": lookup_location_by_area,
    "update_medical_info": update_medical_info,
    "update_fire_info": update_fire_info,
    "update_police_info": update_police_info,
    
    # ========== AMBULANCE TOOLS ==========
    "get_nearby_ambulances": get_nearby_ambulances,
    "dispatch_nearest_ambulance": dispatch_nearest_ambulance,
    "assess_ambulance_need": assess_ambulance_need,
    "get_available_ambulances": get_available_ambulances,
    "update_ambulance_status": update_ambulance_status,
    
    # ========== FIRE TOOLS ==========
    "get_nearby_fire_stations": get_nearby_fire_stations,
    "get_nearby_fire_trucks": get_nearby_fire_trucks,
    "dispatch_nearest_fire_truck": dispatch_nearest_fire_truck,
    "dispatch_multiple_fire_units": dispatch_multiple_fire_units,
    "assess_fire_severity": assess_fire_severity,
    "get_available_fire_trucks": get_available_fire_trucks,
    "update_fire_truck_status": update_fire_truck_status,
    
    # ========== POLICE TOOLS ==========
    "get_nearby_patrol_units": get_nearby_patrol_units,
    "dispatch_nearest_patrol_unit": dispatch_nearest_patrol_unit,
    "dispatch_multiple_police_units": dispatch_multiple_police_units,
    "assess_threat_level": assess_threat_level,
    "create_case": create_case,
    "get_safety_instructions": get_safety_instructions,
    "get_available_patrol_units": get_available_patrol_units,
    "update_case_status": update_case_status,
}


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool by name with given arguments
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Dictionary of arguments for the tool
    
    Returns:
        Result of the tool execution
    """
    if tool_name not in TOOL_REGISTRY:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}",
            "available_tools": list(TOOL_REGISTRY.keys())
        }
    
    try:
        tool_function = TOOL_REGISTRY[tool_name]
        # Filter out None/null values - let function defaults handle them
        filtered_args = {k: v for k, v in arguments.items() if v is not None}
        result = tool_function(**filtered_args)
        return result
    except TypeError as e:
        return {
            "success": False,
            "error": f"Invalid arguments for {tool_name}: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Tool execution failed: {str(e)}"
        }


def execute_tool_call(tool_call) -> Dict[str, Any]:
    """
    Execute a tool call object from the LLM response
    
    Args:
        tool_call: Tool call object with name and arguments
    
    Returns:
        Result of the tool execution
    """
    tool_name = tool_call.function.name
    
    try:
        arguments = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Failed to parse tool arguments"
        }
    
    return execute_tool(tool_name, arguments)


def get_tool_description(tool_name: str) -> str:
    """Get a description of what a tool does"""
    descriptions = {
        "get_nearby_ambulances": "Find available ambulances near a location",
        "dispatch_nearest_ambulance": "Dispatch the nearest ambulance to an emergency",
        "assess_ambulance_need": "Assess medical situation severity and ambulance type needed",
        "get_available_ambulances": "List all available ambulances in the system",
        "update_ambulance_status": "Update an ambulance's status",
        
        "get_nearby_fire_stations": "Find fire stations near a location",
        "get_nearby_fire_trucks": "Find available fire trucks near a location",
        "dispatch_nearest_fire_truck": "Dispatch the nearest fire truck",
        "dispatch_multiple_fire_units": "Dispatch multiple fire units for large emergencies",
        "assess_fire_severity": "Assess fire severity and recommended response",
        "get_available_fire_trucks": "List all available fire trucks",
        "update_fire_truck_status": "Update a fire truck's status",
        
        "get_nearby_patrol_units": "Find police patrol units near a location",
        "dispatch_nearest_patrol_unit": "Dispatch the nearest patrol unit",
        "dispatch_multiple_police_units": "Dispatch multiple units for high-threat situations",
        "assess_threat_level": "Assess threat level and get recommendations",
        "create_case": "Create a new case in the police system",
        "get_safety_instructions": "Get safety instructions for emergency types",
        "get_available_patrol_units": "List all available patrol units",
        "update_case_status": "Update case status",
    }
    return descriptions.get(tool_name, "No description available")


def list_available_tools() -> Dict[str, str]:
    """List all available tools with descriptions"""
    return {name: get_tool_description(name) for name in TOOL_REGISTRY.keys()}


if __name__ == "__main__":
    print("\n=== Available Emergency Tools ===\n")
    for name, desc in list_available_tools().items():
        print(f"  • {name}: {desc}")
    
    print("\n=== Testing Tool Execution ===\n")
    
    # Test ambulance tool
    result = execute_tool("get_nearby_ambulances", {
        "user_lat": 12.9716,
        "user_lon": 77.5946,
        "radius_km": 5
    })
    print(f"Nearby Ambulances: Found {result.get('count', 0)} ambulances")
    
    # Test fire tool
    result = execute_tool("assess_fire_severity", {
        "smoke_visible": True,
        "flames_visible": True,
        "building_type": "residential",
        "people_trapped": 2
    })
    print(f"Fire Severity: {result.get('assessment', {}).get('severity_level', 'N/A')}")
    
    # Test police tool
    result = execute_tool("assess_threat_level", {
        "emergency_type": "kidnap",
        "weapons_involved": True
    })
    print(f"Threat Level: {result.get('assessment', {}).get('threat_level', 'N/A')}")

