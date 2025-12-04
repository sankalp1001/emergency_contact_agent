"""
Police Tools Module
Tools for police emergency dispatch, retrieval, and case management
Handles kidnap, extortion, and general police emergencies
"""

import sqlite3
import math
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import random
import string

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "../../../database/police.db")

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula (km)"""
    R = 6371
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def estimate_arrival_time(distance_km: float, avg_speed_kmh: float = 45) -> int:
    """Estimate patrol unit arrival time in minutes"""
    return max(1, int((distance_km / avg_speed_kmh) * 60))

def generate_case_number() -> str:
    """Generate a unique case number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"CASE-{timestamp}-{random_suffix}"


# ============== TOOL FUNCTIONS FOR LLM ==============

def get_all_police_stations() -> Dict[str, Any]:
    """
    Retrieve all police stations from the database
    
    Returns:
        Dict containing status and list of all police stations
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, station_name, station_code, latitude, longitude, 
                   contact_number, jurisdiction_area
            FROM police_stations
        """)
        stations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            "success": True,
            "count": len(stations),
            "police_stations": stations
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_available_patrol_units() -> Dict[str, Any]:
    """
    Retrieve all available patrol units
    
    Returns:
        Dict containing available patrol units with station info
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.unit_code, p.vehicle_number, p.unit_type, 
                   p.officers_count, p.latitude, p.longitude,
                   s.station_name, s.contact_number, s.jurisdiction_area
            FROM patrol_units p
            JOIN police_stations s ON p.station_id = s.id
            WHERE p.status = 'available'
        """)
        units = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            "success": True,
            "count": len(units),
            "patrol_units": units
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_nearby_police_stations(
    user_lat: float,
    user_lon: float,
    radius_km: float = 15.0
) -> Dict[str, Any]:
    """
    Find police stations near a given location
    
    Args:
        user_lat: User's latitude
        user_lon: User's longitude
        radius_km: Search radius in kilometers
    
    Returns:
        Dict containing nearby police stations sorted by distance
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, station_name, station_code, latitude, longitude, 
                   contact_number, jurisdiction_area
            FROM police_stations
        """)
        stations = cursor.fetchall()
        conn.close()
        
        nearby = []
        for station in stations:
            distance = calculate_distance(user_lat, user_lon, station['latitude'], station['longitude'])
            if distance <= radius_km:
                station_dict = dict(station)
                station_dict['distance_km'] = round(distance, 2)
                station_dict['estimated_arrival_minutes'] = estimate_arrival_time(distance)
                nearby.append(station_dict)
        
        nearby.sort(key=lambda x: x['distance_km'])
        
        return {
            "success": True,
            "user_location": {"latitude": user_lat, "longitude": user_lon},
            "search_radius_km": radius_km,
            "count": len(nearby),
            "police_stations": nearby
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_nearby_patrol_units(
    user_lat: float,
    user_lon: float,
    radius_km: float = 10.0,
    unit_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Find available patrol units near a given location
    
    Args:
        user_lat: User's latitude
        user_lon: User's longitude
        radius_km: Search radius in kilometers
        unit_type: Filter by type ('patrol', 'rapid_response')
    
    Returns:
        Dict containing nearby patrol units sorted by distance
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT p.id, p.unit_code, p.vehicle_number, p.unit_type, 
                   p.officers_count, p.latitude, p.longitude,
                   s.station_name, s.contact_number
            FROM patrol_units p
            JOIN police_stations s ON p.station_id = s.id
            WHERE p.status = 'available'
        """
        params = []
        
        if unit_type:
            query += " AND p.unit_type = ?"
            params.append(unit_type)
        
        cursor.execute(query, params)
        units = cursor.fetchall()
        conn.close()
        
        nearby = []
        for unit in units:
            distance = calculate_distance(user_lat, user_lon, unit['latitude'], unit['longitude'])
            if distance <= radius_km:
                unit_dict = dict(unit)
                unit_dict['distance_km'] = round(distance, 2)
                unit_dict['estimated_arrival_minutes'] = estimate_arrival_time(distance)
                nearby.append(unit_dict)
        
        nearby.sort(key=lambda x: x['distance_km'])
        
        return {
            "success": True,
            "user_location": {"latitude": user_lat, "longitude": user_lon},
            "count": len(nearby),
            "patrol_units": nearby
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def dispatch_patrol_unit(
    patrol_unit_id: int,
    user_lat: float,
    user_lon: float,
    emergency_type: str,
    threat_level: str = "medium",
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Dispatch a patrol unit to a location
    
    Args:
        patrol_unit_id: ID of the patrol unit to dispatch
        user_lat: Destination latitude
        user_lon: Destination longitude
        emergency_type: Type of emergency ('kidnap', 'extortion', 'robbery', 'assault', 'threat', 'suspicious_activity')
        threat_level: Threat level ('low', 'medium', 'high', 'critical')
        notes: Additional notes
    
    Returns:
        Dict containing dispatch confirmation
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get patrol unit info
        cursor.execute("""
            SELECT p.*, s.station_name, s.contact_number
            FROM patrol_units p
            JOIN police_stations s ON p.station_id = s.id
            WHERE p.id = ?
        """, (patrol_unit_id,))
        unit = cursor.fetchone()
        
        if not unit:
            conn.close()
            return {"success": False, "error": "Patrol unit not found"}
        
        if unit['status'] != 'available':
            conn.close()
            return {"success": False, "error": f"Patrol unit is currently {unit['status']}"}
        
        distance = calculate_distance(user_lat, user_lon, unit['latitude'], unit['longitude'])
        eta_minutes = estimate_arrival_time(distance)
        
        # Generate case number
        case_number = generate_case_number()
        
        # Update unit status
        cursor.execute("UPDATE patrol_units SET status = 'dispatched' WHERE id = ?", (patrol_unit_id,))
        
        # Create dispatch record
        cursor.execute("""
            INSERT INTO police_dispatches 
            (patrol_unit_id, user_location_lat, user_location_lon, emergency_type, threat_level, case_number, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'dispatched')
        """, (patrol_unit_id, user_lat, user_lon, emergency_type, threat_level, case_number, notes))
        
        dispatch_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "dispatch_id": dispatch_id,
            "case_number": case_number,
            "patrol_unit": {
                "id": unit['id'],
                "unit_code": unit['unit_code'],
                "vehicle_number": unit['vehicle_number'],
                "unit_type": unit['unit_type'],
                "officers_count": unit['officers_count'],
                "station_name": unit['station_name'],
                "contact": unit['contact_number']
            },
            "destination": {"latitude": user_lat, "longitude": user_lon},
            "distance_km": round(distance, 2),
            "estimated_arrival_minutes": eta_minutes,
            "emergency_type": emergency_type,
            "threat_level": threat_level,
            "message": f"Police unit {unit['unit_code']} dispatched. ETA: {eta_minutes} minutes. Case #: {case_number}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def dispatch_nearest_patrol_unit(
    user_lat: float,
    user_lon: float,
    emergency_type: str,
    threat_level: str = "medium",
    require_rapid_response: bool = False,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Automatically find and dispatch the nearest available patrol unit
    
    Args:
        user_lat: Destination latitude
        user_lon: Destination longitude
        emergency_type: Type of emergency
        threat_level: Threat level
        require_rapid_response: Whether to prioritize rapid response units
        notes: Additional notes
    
    Returns:
        Dict containing dispatch confirmation
    """
    unit_type = "rapid_response" if require_rapid_response else None
    
    result = get_nearby_patrol_units(user_lat, user_lon, radius_km=20, unit_type=unit_type)
    
    if not result["success"]:
        return result
    
    # If rapid response not found but required, fall back to any unit
    if result["count"] == 0 and require_rapid_response:
        result = get_nearby_patrol_units(user_lat, user_lon, radius_km=20)
    
    if result["count"] == 0:
        return {
            "success": False,
            "error": "No available patrol units found nearby",
            "suggestion": "Call emergency services directly at 100"
        }
    
    nearest_unit = result["patrol_units"][0]
    
    return dispatch_patrol_unit(
        patrol_unit_id=nearest_unit["id"],
        user_lat=user_lat,
        user_lon=user_lon,
        emergency_type=emergency_type,
        threat_level=threat_level,
        notes=notes
    )

def dispatch_multiple_units(
    user_lat: float,
    user_lon: float,
    emergency_type: str,
    threat_level: str,
    units_needed: int = 2,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Dispatch multiple patrol units for high-threat situations
    
    Args:
        user_lat: Destination latitude
        user_lon: Destination longitude
        emergency_type: Type of emergency
        threat_level: Threat level
        units_needed: Number of units to dispatch
        notes: Additional notes
    
    Returns:
        Dict containing dispatch confirmations for all units
    """
    dispatched = []
    failed = []
    
    result = get_nearby_patrol_units(user_lat, user_lon, radius_km=30)
    
    if not result["success"]:
        return result
    
    available_units = result["patrol_units"]
    
    for i, unit in enumerate(available_units[:units_needed]):
        dispatch_result = dispatch_patrol_unit(
            patrol_unit_id=unit["id"],
            user_lat=user_lat,
            user_lon=user_lon,
            emergency_type=emergency_type,
            threat_level=threat_level,
            notes=f"Multi-unit dispatch #{i+1}. {notes or ''}"
        )
        
        if dispatch_result["success"]:
            dispatched.append(dispatch_result)
        else:
            failed.append({"unit_id": unit["id"], "error": dispatch_result["error"]})
    
    return {
        "success": len(dispatched) > 0,
        "units_requested": units_needed,
        "units_dispatched": len(dispatched),
        "dispatches": dispatched,
        "failed": failed,
        "message": f"{len(dispatched)} police units dispatched to location"
    }

def create_case(
    case_type: str,
    location_lat: float,
    location_lon: float,
    description: str,
    victim_safe: bool = False
) -> Dict[str, Any]:
    """
    Create a new case record in the system
    
    Args:
        case_type: Type of case ('kidnap', 'extortion', 'robbery', 'assault', 'missing_person')
        location_lat: Incident location latitude
        location_lon: Incident location longitude
        description: Case description
        victim_safe: Is the victim currently safe?
    
    Returns:
        Dict containing case creation confirmation
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        case_number = generate_case_number()
        
        cursor.execute("""
            INSERT INTO cases 
            (case_number, case_type, reported_lat, reported_lon, description, victim_safe, status)
            VALUES (?, ?, ?, ?, ?, ?, 'open')
        """, (case_number, case_type, location_lat, location_lon, description, 1 if victim_safe else 0))
        
        case_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "case_id": case_id,
            "case_number": case_number,
            "case_type": case_type,
            "status": "open",
            "message": f"Case {case_number} created and logged in the system"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_case_status(
    case_number: str,
    new_status: str,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update the status of a case
    
    Args:
        case_number: The case number
        new_status: New status ('open', 'investigating', 'resolved', 'closed')
        notes: Additional notes
    
    Returns:
        Dict containing update confirmation
    """
    valid_statuses = ['open', 'investigating', 'resolved', 'closed']
    
    if new_status not in valid_statuses:
        return {"success": False, "error": f"Invalid status. Must be one of: {valid_statuses}"}
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE cases 
            SET status = ?, updated_at = CURRENT_TIMESTAMP, description = COALESCE(description || ' | ' || ?, description)
            WHERE case_number = ?
        """, (new_status, notes, case_number))
        
        if cursor.rowcount == 0:
            conn.close()
            return {"success": False, "error": "Case not found"}
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "case_number": case_number,
            "new_status": new_status,
            "message": f"Case {case_number} status updated to '{new_status}'"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_patrol_unit_status(patrol_unit_id: int, new_status: str) -> Dict[str, Any]:
    """
    Update the status of a patrol unit
    
    Args:
        patrol_unit_id: ID of the patrol unit
        new_status: New status ('available', 'busy', 'dispatched')
    
    Returns:
        Dict containing update confirmation
    """
    valid_statuses = ['available', 'busy', 'dispatched']
    
    if new_status not in valid_statuses:
        return {"success": False, "error": f"Invalid status. Must be one of: {valid_statuses}"}
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE patrol_units SET status = ? WHERE id = ?", (new_status, patrol_unit_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return {"success": False, "error": "Patrol unit not found"}
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "patrol_unit_id": patrol_unit_id,
            "new_status": new_status,
            "message": f"Patrol unit status updated to '{new_status}'"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def complete_police_dispatch(dispatch_id: int, victim_safe: bool = True, notes: Optional[str] = None) -> Dict[str, Any]:
    """
    Mark a police dispatch as resolved and make unit available again
    
    Args:
        dispatch_id: ID of the dispatch to complete
        victim_safe: Is the victim safe?
        notes: Resolution notes
    
    Returns:
        Dict containing completion confirmation
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM police_dispatches WHERE id = ?", (dispatch_id,))
        dispatch = cursor.fetchone()
        
        if not dispatch:
            conn.close()
            return {"success": False, "error": "Dispatch not found"}
        
        # Update dispatch status
        cursor.execute("""
            UPDATE police_dispatches 
            SET status = 'resolved', resolved_time = CURRENT_TIMESTAMP, notes = ?
            WHERE id = ?
        """, (notes, dispatch_id))
        
        # Make patrol unit available
        cursor.execute("""
            UPDATE patrol_units SET status = 'available' WHERE id = ?
        """, (dispatch['patrol_unit_id'],))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "dispatch_id": dispatch_id,
            "case_number": dispatch['case_number'],
            "victim_safe": victim_safe,
            "message": "Police dispatch resolved. Unit is now available."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def assess_threat_level(
    emergency_type: str,
    weapons_involved: bool = False,
    hostage_situation: bool = False,
    suspect_count: int = 0,
    victim_count: int = 1,
    suspect_present: bool = False,
    violence_occurred: bool = False
) -> Dict[str, Any]:
    """
    Assess threat level and recommend appropriate response
    
    Args:
        emergency_type: Type of emergency ('kidnap', 'extortion', 'robbery', 'assault', 'threat')
        weapons_involved: Are weapons involved?
        hostage_situation: Is this a hostage situation?
        suspect_count: Number of suspects
        victim_count: Number of victims
        suspect_present: Is suspect still present?
        violence_occurred: Has violence occurred?
    
    Returns:
        Dict containing threat assessment and recommendations
    """
    threat_score = 0
    
    # Emergency type base scores
    type_scores = {
        'kidnap': 4,
        'extortion': 2,
        'robbery': 3,
        'assault': 3,
        'threat': 1,
        'suspicious_activity': 1
    }
    threat_score += type_scores.get(emergency_type.lower(), 2)
    
    # Factors
    if weapons_involved:
        threat_score += 4
    if hostage_situation:
        threat_score += 5
    if suspect_present:
        threat_score += 2
    if violence_occurred:
        threat_score += 3
    if suspect_count > 2:
        threat_score += 2
    if victim_count > 1:
        threat_score += 1
    
    # Determine threat level
    if threat_score >= 10:
        threat_level = "CRITICAL"
        units_recommended = 4
        require_rapid_response = True
        recommendation = "Armed response team required. Multiple units needed immediately."
        user_instructions = [
            "DO NOT confront the suspects",
            "Find a safe hiding place if possible",
            "Stay silent and do not draw attention",
            "Keep phone on silent but stay connected",
            "Wait for police to arrive"
        ]
    elif threat_score >= 7:
        threat_level = "HIGH"
        units_recommended = 2
        require_rapid_response = True
        recommendation = "Rapid response unit recommended. Priority dispatch."
        user_instructions = [
            "Move to a safe location if possible",
            "Stay calm and do not provoke",
            "Note descriptions of suspects if safe to do so",
            "Keep communication open with emergency services"
        ]
    elif threat_score >= 4:
        threat_level = "MEDIUM"
        units_recommended = 1
        require_rapid_response = False
        recommendation = "Standard patrol response. Exercise caution."
        user_instructions = [
            "Stay alert and aware of surroundings",
            "Move to a well-lit, public area if possible",
            "Wait for police to arrive"
        ]
    else:
        threat_level = "LOW"
        units_recommended = 1
        require_rapid_response = False
        recommendation = "Standard patrol response appropriate."
        user_instructions = [
            "Stay calm and observe",
            "Note any useful details",
            "Wait for police to arrive"
        ]
    
    return {
        "success": True,
        "assessment": {
            "threat_level": threat_level,
            "threat_score": threat_score,
            "units_recommended": units_recommended,
            "require_rapid_response": require_rapid_response,
            "recommendation": recommendation,
            "factors_analyzed": {
                "emergency_type": emergency_type,
                "weapons_involved": weapons_involved,
                "hostage_situation": hostage_situation,
                "suspect_count": suspect_count,
                "victim_count": victim_count,
                "suspect_present": suspect_present,
                "violence_occurred": violence_occurred
            }
        },
        "user_instructions": user_instructions
    }

def get_safety_instructions(emergency_type: str) -> Dict[str, Any]:
    """
    Get safety instructions for specific emergency types
    
    Args:
        emergency_type: Type of emergency
    
    Returns:
        Dict containing safety instructions
    """
    instructions = {
        "kidnap": {
            "immediate": [
                "If you can communicate safely, share your location",
                "Try to stay calm and do not resist violently",
                "Observe and remember details about captors and location",
                "Look for opportunities to escape only if safe",
                "If possible, leave small clues for rescuers"
            ],
            "for_family": [
                "Contact police immediately",
                "Do not pay ransom without police guidance",
                "Keep communication lines open",
                "Document all communications from kidnappers"
            ]
        },
        "extortion": {
            "immediate": [
                "Do not make immediate payments",
                "Document all threats and communications",
                "Report to police before responding to demands",
                "Do not delete any messages or evidence",
                "Inform trusted family members or friends"
            ],
            "ongoing": [
                "Keep police informed of all developments",
                "Follow police guidance on responses",
                "Maintain records of all incidents"
            ]
        },
        "robbery": {
            "during": [
                "Do not resist - your safety is priority",
                "Follow instructions calmly",
                "Avoid sudden movements",
                "Do not make eye contact with weapons",
                "Note physical descriptions if possible"
            ],
            "after": [
                "Call police immediately",
                "Do not touch anything at the scene",
                "Note direction suspects fled",
                "Get witness contact information"
            ]
        },
        "assault": {
            "during": [
                "Try to escape to safety if possible",
                "Protect vital areas (head, neck)",
                "Call for help loudly",
                "Fight back only as last resort"
            ],
            "after": [
                "Get to a safe location",
                "Call emergency services",
                "Seek medical attention",
                "Do not wash or change clothes (evidence)"
            ]
        },
        "threat": {
            "immediate": [
                "Move to a safe, public location if possible",
                "Do not engage with the person making threats",
                "Try to note their appearance and any vehicle details",
                "Contact trusted friends or family"
            ],
            "ongoing": [
                "Document all threats (save messages, record times)",
                "Report to police immediately",
                "Consider changing your routine temporarily",
                "Stay in well-lit, populated areas"
            ]
        }
    }
    
    return {
        "success": True,
        "emergency_type": emergency_type,
        "instructions": instructions.get(emergency_type.lower(), {
            "general": [
                "Contact emergency services immediately",
                "Move to a safe location",
                "Stay calm and follow police instructions"
            ]
        })
    }


# ============== TOOL DEFINITIONS FOR LLM ==============

POLICE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_nearby_patrol_units",
            "description": "Find available police patrol units near a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_lat": {
                        "type": "number",
                        "description": "User's latitude coordinate"
                    },
                    "user_lon": {
                        "type": "number",
                        "description": "User's longitude coordinate"
                    },
                    "radius_km": {
                        "type": "number",
                        "description": "Search radius in kilometers (default: 10)"
                    },
                    "unit_type": {
                        "type": "string",
                        "enum": ["patrol", "rapid_response"],
                        "description": "Type of unit needed"
                    }
                },
                "required": ["user_lat", "user_lon"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "dispatch_nearest_patrol_unit",
            "description": "Automatically find and dispatch the nearest available police patrol unit",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_lat": {
                        "type": "number",
                        "description": "Destination latitude"
                    },
                    "user_lon": {
                        "type": "number",
                        "description": "Destination longitude"
                    },
                    "emergency_type": {
                        "type": "string",
                        "enum": ["kidnap", "extortion", "robbery", "assault", "threat", "suspicious_activity"],
                        "description": "Type of police emergency"
                    },
                    "threat_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Assessed threat level"
                    },
                    "require_rapid_response": {
                        "type": "boolean",
                        "description": "Whether rapid response unit is required"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional emergency details"
                    }
                },
                "required": ["user_lat", "user_lon", "emergency_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "dispatch_multiple_police_units",
            "description": "Dispatch multiple police units for high-threat situations like kidnapping",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_lat": {
                        "type": "number",
                        "description": "Destination latitude"
                    },
                    "user_lon": {
                        "type": "number",
                        "description": "Destination longitude"
                    },
                    "emergency_type": {
                        "type": "string",
                        "description": "Type of emergency"
                    },
                    "threat_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Threat level"
                    },
                    "units_needed": {
                        "type": "integer",
                        "description": "Number of units to dispatch"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional details"
                    }
                },
                "required": ["user_lat", "user_lon", "emergency_type", "threat_level", "units_needed"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "assess_threat_level",
            "description": "Assess threat level based on emergency details and get response recommendations",
            "parameters": {
                "type": "object",
                "properties": {
                    "emergency_type": {
                        "type": "string",
                        "enum": ["kidnap", "extortion", "robbery", "assault", "threat", "suspicious_activity"],
                        "description": "Type of emergency"
                    },
                    "weapons_involved": {
                        "type": "boolean",
                        "description": "Are weapons involved?"
                    },
                    "hostage_situation": {
                        "type": "boolean",
                        "description": "Is this a hostage situation?"
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
                        "description": "Is the suspect still present?"
                    },
                    "violence_occurred": {
                        "type": "boolean",
                        "description": "Has violence occurred?"
                    }
                },
                "required": ["emergency_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_case",
            "description": "Create a new case record in the police system",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_type": {
                        "type": "string",
                        "enum": ["kidnap", "extortion", "robbery", "assault", "missing_person"],
                        "description": "Type of case"
                    },
                    "location_lat": {
                        "type": "number",
                        "description": "Incident location latitude"
                    },
                    "location_lon": {
                        "type": "number",
                        "description": "Incident location longitude"
                    },
                    "description": {
                        "type": "string",
                        "description": "Case description"
                    },
                    "victim_safe": {
                        "type": "boolean",
                        "description": "Is the victim currently safe?"
                    }
                },
                "required": ["case_type", "location_lat", "location_lon", "description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_safety_instructions",
            "description": "Get safety instructions for specific emergency types to guide the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "emergency_type": {
                        "type": "string",
                        "enum": ["kidnap", "extortion", "robbery", "assault", "threat"],
                        "description": "Type of emergency"
                    }
                },
                "required": ["emergency_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_available_patrol_units",
            "description": "Get all currently available patrol units",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_case_status",
            "description": "Update the status of an existing case",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_number": {
                        "type": "string",
                        "description": "The case number to update"
                    },
                    "new_status": {
                        "type": "string",
                        "enum": ["open", "investigating", "resolved", "closed"],
                        "description": "New case status"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes"
                    }
                },
                "required": ["case_number", "new_status"]
            }
        }
    }
]


if __name__ == "__main__":
    # Test the tools
    print("\n=== Testing Police Tools ===\n")
    
    # Test getting all stations
    print("1. All Police Stations:")
    result = get_all_police_stations()
    print(f"   Found {result['count']} police stations")
    
    # Test nearby units
    print("\n2. Nearby Patrol Units (Bangalore center):")
    result = get_nearby_patrol_units(12.9716, 77.5946, radius_km=10)
    print(f"   Found {result['count']} available units")
    
    # Test threat assessment
    print("\n3. Threat Assessment (Kidnap scenario):")
    result = assess_threat_level(
        emergency_type="kidnap",
        weapons_involved=True,
        hostage_situation=True,
        suspect_count=2
    )
    print(f"   Threat Level: {result['assessment']['threat_level']}")
    print(f"   Units Recommended: {result['assessment']['units_recommended']}")
    print(f"   Recommendation: {result['assessment']['recommendation']}")
    
    # Test safety instructions
    print("\n4. Safety Instructions (Extortion):")
    result = get_safety_instructions("extortion")
    print(f"   Instructions retrieved for: {result['emergency_type']}")

