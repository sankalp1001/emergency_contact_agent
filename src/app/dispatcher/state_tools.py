"""
State Management Tools
Tools that allow the LLM to update conversation state
"""

from typing import Dict, Any, Optional


# These functions will be called by the orchestrator with state context
# They return instructions for state updates

def classify_emergency(
    emergency_type: str,
    confidence: str = "high"
) -> Dict[str, Any]:
    """
    Classify the type of emergency based on conversation
    
    Args:
        emergency_type: Type of emergency ('medical', 'fire', 'police')
        confidence: Confidence level ('high', 'medium', 'low')
    
    Returns:
        Dict containing classification result
    """
    valid_types = ['medical', 'fire', 'police']
    
    if emergency_type.lower() not in valid_types:
        return {
            "success": False,
            "error": f"Invalid emergency type. Must be one of: {valid_types}"
        }
    
    return {
        "success": True,
        "emergency_type": emergency_type.lower(),
        "confidence": confidence,
        "message": f"Emergency classified as {emergency_type.upper()}"
    }


def set_user_location(
    latitude: float,
    longitude: float,
    address: Optional[str] = None
) -> Dict[str, Any]:
    """
    Set or update the user's location
    
    Args:
        latitude: User's latitude
        longitude: User's longitude
        address: Optional address description
    
    Returns:
        Dict containing location update result
    """
    # Basic validation
    if not (-90 <= latitude <= 90):
        return {"success": False, "error": "Invalid latitude"}
    if not (-180 <= longitude <= 180):
        return {"success": False, "error": "Invalid longitude"}
    
    return {
        "success": True,
        "location": {
            "latitude": latitude,
            "longitude": longitude,
            "address": address
        },
        "message": f"Location set to ({latitude}, {longitude})"
    }


import random

# Known areas in Bangalore with approximate coordinates
BANGALORE_AREAS = {
    "koramangala": (12.9352, 77.6245),
    "indiranagar": (12.9784, 77.6408),
    "whitefield": (12.9698, 77.7500),
    "jayanagar": (12.9250, 77.5897),
    "electronic city": (12.8456, 77.6603),
    "hsr layout": (12.9116, 77.6389),
    "hsr": (12.9116, 77.6389),
    "marathahalli": (12.9591, 77.6971),
    "btm layout": (12.9166, 77.6101),
    "btm": (12.9166, 77.6101),
    "mg road": (12.9758, 77.6045),
    "brigade road": (12.9716, 77.6077),
    "ulsoor": (12.9830, 77.6200),
    "cubbon park": (12.9763, 77.5929),
    "majestic": (12.9767, 77.5713),
    "bangalore central": (12.9716, 77.5946),
    "bangalore": (12.9716, 77.5946),
    "bengaluru": (12.9716, 77.5946),
}


def lookup_location_by_area(area_name: str) -> Dict[str, Any]:
    """
    Look up approximate coordinates for a known area name
    Adds small random offset for realistic variation
    
    Args:
        area_name: Name of the area (e.g., "Koramangala", "HSR Layout")
    
    Returns:
        Dict containing coordinates or error
    """
    area_lower = area_name.lower().strip()
    
    # Try exact match first
    if area_lower in BANGALORE_AREAS:
        base_lat, base_lon = BANGALORE_AREAS[area_lower]
    else:
        # Try partial match
        matched = None
        for key in BANGALORE_AREAS:
            if key in area_lower or area_lower in key:
                matched = key
                break
        
        if matched:
            base_lat, base_lon = BANGALORE_AREAS[matched]
        else:
            # Default to Bangalore center with larger random offset
            base_lat, base_lon = 12.9716, 77.5946
    
    # Add small random offset (approx 100-500m)
    lat = base_lat + (random.random() - 0.5) * 0.005
    lon = base_lon + (random.random() - 0.5) * 0.005
    
    return {
        "success": True,
        "location": {
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "address": area_name
        },
        "message": f"Location set to {area_name} ({round(lat, 4)}, {round(lon, 4)})"
    }


def update_medical_info(
    patient_count: Optional[int] = None,
    symptoms: Optional[list] = None,
    patient_conscious: Optional[bool] = None,
    patient_breathing: Optional[bool] = None,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update medical emergency information
    
    Args:
        patient_count: Number of patients
        symptoms: List of symptoms
        patient_conscious: Is patient conscious
        patient_breathing: Is patient breathing
        notes: Additional notes
    
    Returns:
        Dict containing the update info
    """
    update = {}
    if patient_count is not None:
        update["patient_count"] = patient_count
    if symptoms is not None:
        update["symptoms"] = symptoms
    if patient_conscious is not None:
        update["patient_conscious"] = patient_conscious
    if patient_breathing is not None:
        update["patient_breathing"] = patient_breathing
    if notes is not None:
        update["notes"] = notes
    
    return {
        "success": True,
        "medical_info_update": update,
        "message": "Medical information updated"
    }


def update_fire_info(
    smoke_visible: Optional[bool] = None,
    flames_visible: Optional[bool] = None,
    building_type: Optional[str] = None,
    people_trapped: Optional[int] = None,
    floor_count: Optional[int] = None,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update fire emergency information
    
    Args:
        smoke_visible: Is smoke visible
        flames_visible: Are flames visible
        building_type: Type of building
        people_trapped: Number of people trapped
        floor_count: Number of floors
        notes: Additional notes
    
    Returns:
        Dict containing the update info
    """
    update = {}
    if smoke_visible is not None:
        update["smoke_visible"] = smoke_visible
    if flames_visible is not None:
        update["flames_visible"] = flames_visible
    if building_type is not None:
        update["building_type"] = building_type
    if people_trapped is not None:
        update["people_trapped"] = people_trapped
    if floor_count is not None:
        update["floor_count"] = floor_count
    if notes is not None:
        update["notes"] = notes
    
    return {
        "success": True,
        "fire_info_update": update,
        "message": "Fire information updated"
    }


def update_police_info(
    emergency_subtype: Optional[str] = None,
    weapons_involved: Optional[bool] = None,
    hostage_situation: Optional[bool] = None,
    suspect_count: Optional[int] = None,
    victim_count: Optional[int] = None,
    suspect_present: Optional[bool] = None,
    victim_safe: Optional[bool] = None,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update police emergency information
    
    Args:
        emergency_subtype: Subtype (kidnap, extortion, robbery, assault, threat)
        weapons_involved: Are weapons involved
        hostage_situation: Is this a hostage situation
        suspect_count: Number of suspects
        victim_count: Number of victims
        suspect_present: Is suspect still present
        victim_safe: Is victim currently safe
        notes: Additional notes
    
    Returns:
        Dict containing the update info
    """
    update = {}
    if emergency_subtype is not None:
        update["emergency_subtype"] = emergency_subtype
    if weapons_involved is not None:
        update["weapons_involved"] = weapons_involved
    if hostage_situation is not None:
        update["hostage_situation"] = hostage_situation
    if suspect_count is not None:
        update["suspect_count"] = suspect_count
    if victim_count is not None:
        update["victim_count"] = victim_count
    if suspect_present is not None:
        update["suspect_present"] = suspect_present
    if victim_safe is not None:
        update["victim_safe"] = victim_safe
    if notes is not None:
        update["notes"] = notes
    
    return {
        "success": True,
        "police_info_update": update,
        "message": "Police emergency information updated"
    }


# Tool definitions for LLM
STATE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "classify_emergency",
            "description": "Classify the type of emergency based on the user's description. Call this once you understand what kind of emergency it is.",
            "parameters": {
                "type": "object",
                "properties": {
                    "emergency_type": {
                        "type": "string",
                        "enum": ["medical", "fire", "police"],
                        "description": "The type of emergency: medical (injuries, illness, accidents), fire (fires, smoke, explosions), police (kidnap, extortion, robbery, assault, threats)"
                    },
                    "confidence": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "How confident you are in this classification"
                    }
                },
                "required": ["emergency_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_user_location",
            "description": "Set user's location when they provide exact coordinates",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Latitude coordinate"
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude coordinate"
                    },
                    "address": {
                        "type": "string",
                        "description": "Optional address description"
                    }
                },
                "required": ["latitude", "longitude"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_location_by_area",
            "description": "Convert an area/neighborhood name to coordinates. Use this when user provides a location like 'Koramangala', 'HSR Layout', 'Indiranagar' etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "area_name": {
                        "type": "string",
                        "description": "Name of the area/neighborhood (e.g., 'Koramangala', 'HSR Layout', 'Indiranagar')"
                    }
                },
                "required": ["area_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_medical_info",
            "description": "Update medical emergency details as you gather information from the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_count": {
                        "type": "integer",
                        "description": "Number of patients/injured people"
                    },
                    "symptoms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of symptoms or conditions"
                    },
                    "patient_conscious": {
                        "type": "boolean",
                        "description": "Is the patient conscious"
                    },
                    "patient_breathing": {
                        "type": "boolean",
                        "description": "Is the patient breathing normally"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_fire_info",
            "description": "Update fire emergency details as you gather information from the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "smoke_visible": {
                        "type": "boolean",
                        "description": "Is smoke visible"
                    },
                    "flames_visible": {
                        "type": "boolean",
                        "description": "Are flames visible"
                    },
                    "building_type": {
                        "type": "string",
                        "enum": ["residential", "commercial", "industrial", "vehicle", "forest"],
                        "description": "Type of building/area"
                    },
                    "people_trapped": {
                        "type": "integer",
                        "description": "Number of people trapped"
                    },
                    "floor_count": {
                        "type": "integer",
                        "description": "Number of floors"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_police_info",
            "description": "Update police emergency details as you gather information from the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "emergency_subtype": {
                        "type": "string",
                        "enum": ["kidnap", "extortion", "robbery", "assault", "threat", "suspicious_activity"],
                        "description": "Specific type of police emergency"
                    },
                    "weapons_involved": {
                        "type": "boolean",
                        "description": "Are weapons involved"
                    },
                    "hostage_situation": {
                        "type": "boolean",
                        "description": "Is this a hostage situation"
                    },
                    "suspect_count": {
                        "type": "integer",
                        "description": "Number of suspects"
                    },
                    "victim_count": {
                        "type": "integer",
                        "description": "Number of victims"
                    },
                    "suspect_present": {
                        "type": "boolean",
                        "description": "Is the suspect still present"
                    },
                    "victim_safe": {
                        "type": "boolean",
                        "description": "Is the victim currently safe"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes"
                    }
                }
            }
        }
    }
]

