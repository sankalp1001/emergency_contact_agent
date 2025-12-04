"""
Ambulance Tools Module
Tools for ambulance dispatch, retrieval, and management
"""

import sqlite3
import math
from typing import Optional, List, Dict, Any
from datetime import datetime
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "../../../database/ambulance.db")

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula
    Returns distance in kilometers
    """
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def estimate_arrival_time(distance_km: float, avg_speed_kmh: float = 40) -> int:
    """Estimate arrival time in minutes based on distance"""
    return max(1, int((distance_km / avg_speed_kmh) * 60))

# ============== TOOL FUNCTIONS FOR LLM ==============

def get_all_ambulances() -> Dict[str, Any]:
    """
    Retrieve all ambulances from the database
    
    Returns:
        Dict containing status and list of all ambulances with their details
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, vehicle_number, station_name, latitude, longitude, 
                   status, ambulance_type, contact_number
            FROM ambulances
        """)
        ambulances = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            "success": True,
            "count": len(ambulances),
            "ambulances": ambulances
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_available_ambulances() -> Dict[str, Any]:
    """
    Retrieve only available ambulances
    
    Returns:
        Dict containing status and list of available ambulances
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, vehicle_number, station_name, latitude, longitude, 
                   ambulance_type, contact_number
            FROM ambulances
            WHERE status = 'available'
        """)
        ambulances = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            "success": True,
            "count": len(ambulances),
            "ambulances": ambulances
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_nearby_ambulances(
    user_lat: float, 
    user_lon: float, 
    radius_km: float = 10.0,
    ambulance_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Find available ambulances near a given location
    
    Args:
        user_lat: User's latitude
        user_lon: User's longitude
        radius_km: Search radius in kilometers (default: 10km)
        ambulance_type: Filter by type ('basic', 'advanced', 'icu') - optional
    
    Returns:
        Dict containing nearby ambulances sorted by distance with ETA
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT id, vehicle_number, station_name, latitude, longitude, 
                   ambulance_type, contact_number
            FROM ambulances
            WHERE status = 'available'
        """
        params = []
        
        if ambulance_type:
            query += " AND ambulance_type = ?"
            params.append(ambulance_type)
        
        cursor.execute(query, params)
        ambulances = cursor.fetchall()
        conn.close()
        
        # Calculate distances and filter by radius
        nearby = []
        for amb in ambulances:
            distance = calculate_distance(user_lat, user_lon, amb['latitude'], amb['longitude'])
            if distance <= radius_km:
                amb_dict = dict(amb)
                amb_dict['distance_km'] = round(distance, 2)
                amb_dict['estimated_arrival_minutes'] = estimate_arrival_time(distance)
                nearby.append(amb_dict)
        
        # Sort by distance
        nearby.sort(key=lambda x: x['distance_km'])
        
        return {
            "success": True,
            "user_location": {"latitude": user_lat, "longitude": user_lon},
            "search_radius_km": radius_km,
            "count": len(nearby),
            "ambulances": nearby
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_nearest_ambulance(
    user_lat: float, 
    user_lon: float,
    ambulance_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Find the single nearest available ambulance to a location
    
    Args:
        user_lat: User's latitude
        user_lon: User's longitude
        ambulance_type: Required ambulance type ('basic', 'advanced', 'icu') - optional
    
    Returns:
        Dict containing the nearest ambulance details with distance and ETA
    """
    result = get_nearby_ambulances(user_lat, user_lon, radius_km=50, ambulance_type=ambulance_type)
    
    if not result["success"]:
        return result
    
    if result["count"] == 0:
        return {
            "success": False,
            "error": "No available ambulances found nearby",
            "suggestion": "Try expanding search or contact emergency services directly"
        }
    
    nearest = result["ambulances"][0]
    return {
        "success": True,
        "ambulance": nearest,
        "message": f"Nearest ambulance is {nearest['distance_km']} km away, ETA: {nearest['estimated_arrival_minutes']} minutes"
    }

def dispatch_ambulance(
    ambulance_id: int,
    user_lat: float,
    user_lon: float,
    emergency_type: str,
    patient_count: int = 1,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Dispatch an ambulance to a location
    
    Args:
        ambulance_id: ID of the ambulance to dispatch
        user_lat: Destination latitude
        user_lon: Destination longitude
        emergency_type: Type of medical emergency
        patient_count: Number of patients (default: 1)
        notes: Additional notes about the emergency
    
    Returns:
        Dict containing dispatch confirmation and details
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if ambulance is available
        cursor.execute("SELECT * FROM ambulances WHERE id = ?", (ambulance_id,))
        ambulance = cursor.fetchone()
        
        if not ambulance:
            conn.close()
            return {"success": False, "error": "Ambulance not found"}
        
        if ambulance['status'] != 'available':
            conn.close()
            return {"success": False, "error": f"Ambulance is currently {ambulance['status']}"}
        
        # Calculate ETA
        distance = calculate_distance(user_lat, user_lon, ambulance['latitude'], ambulance['longitude'])
        eta_minutes = estimate_arrival_time(distance)
        
        # Update ambulance status
        cursor.execute("UPDATE ambulances SET status = 'dispatched' WHERE id = ?", (ambulance_id,))
        
        # Create dispatch record
        cursor.execute("""
            INSERT INTO ambulance_dispatches 
            (ambulance_id, user_location_lat, user_location_lon, emergency_type, patient_count, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, 'dispatched')
        """, (ambulance_id, user_lat, user_lon, emergency_type, patient_count, notes))
        
        dispatch_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "dispatch_id": dispatch_id,
            "ambulance": {
                "id": ambulance['id'],
                "vehicle_number": ambulance['vehicle_number'],
                "station_name": ambulance['station_name'],
                "type": ambulance['ambulance_type'],
                "contact": ambulance['contact_number']
            },
            "destination": {"latitude": user_lat, "longitude": user_lon},
            "distance_km": round(distance, 2),
            "estimated_arrival_minutes": eta_minutes,
            "emergency_type": emergency_type,
            "patient_count": patient_count,
            "message": f"Ambulance {ambulance['vehicle_number']} dispatched. ETA: {eta_minutes} minutes"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def dispatch_nearest_ambulance(
    user_lat: float,
    user_lon: float,
    emergency_type: str,
    patient_count: int = 1,
    ambulance_type: Optional[str] = None,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Automatically find and dispatch the nearest available ambulance
    
    Args:
        user_lat: User's latitude
        user_lon: User's longitude
        emergency_type: Type of medical emergency
        patient_count: Number of patients
        ambulance_type: Required ambulance type (optional)
        notes: Additional notes
    
    Returns:
        Dict containing dispatch confirmation
    """
    # Find nearest ambulance
    nearest_result = get_nearest_ambulance(user_lat, user_lon, ambulance_type)
    
    if not nearest_result["success"]:
        return nearest_result
    
    # Dispatch it
    return dispatch_ambulance(
        ambulance_id=nearest_result["ambulance"]["id"],
        user_lat=user_lat,
        user_lon=user_lon,
        emergency_type=emergency_type,
        patient_count=patient_count,
        notes=notes
    )

def update_ambulance_status(ambulance_id: int, new_status: str) -> Dict[str, Any]:
    """
    Update the status of an ambulance
    
    Args:
        ambulance_id: ID of the ambulance
        new_status: New status ('available', 'busy', 'dispatched', 'maintenance')
    
    Returns:
        Dict containing update confirmation
    """
    valid_statuses = ['available', 'busy', 'dispatched', 'maintenance']
    
    if new_status not in valid_statuses:
        return {
            "success": False,
            "error": f"Invalid status. Must be one of: {valid_statuses}"
        }
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE ambulances SET status = ? WHERE id = ?", (new_status, ambulance_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return {"success": False, "error": "Ambulance not found"}
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "ambulance_id": ambulance_id,
            "new_status": new_status,
            "message": f"Ambulance status updated to '{new_status}'"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def complete_dispatch(dispatch_id: int, notes: Optional[str] = None) -> Dict[str, Any]:
    """
    Mark a dispatch as completed and make ambulance available again
    
    Args:
        dispatch_id: ID of the dispatch to complete
        notes: Completion notes
    
    Returns:
        Dict containing completion confirmation
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get dispatch info
        cursor.execute("SELECT * FROM ambulance_dispatches WHERE id = ?", (dispatch_id,))
        dispatch = cursor.fetchone()
        
        if not dispatch:
            conn.close()
            return {"success": False, "error": "Dispatch not found"}
        
        # Update dispatch status
        cursor.execute("""
            UPDATE ambulance_dispatches 
            SET status = 'completed', arrival_time = CURRENT_TIMESTAMP, notes = ?
            WHERE id = ?
        """, (notes, dispatch_id))
        
        # Make ambulance available again
        cursor.execute("""
            UPDATE ambulances SET status = 'available' WHERE id = ?
        """, (dispatch['ambulance_id'],))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "dispatch_id": dispatch_id,
            "message": "Dispatch completed. Ambulance is now available."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_dispatch_history(limit: int = 10) -> Dict[str, Any]:
    """
    Get recent dispatch history
    
    Args:
        limit: Number of records to retrieve (default: 10)
    
    Returns:
        Dict containing recent dispatch records
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT d.*, a.vehicle_number, a.station_name
            FROM ambulance_dispatches d
            JOIN ambulances a ON d.ambulance_id = a.id
            ORDER BY d.dispatch_time DESC
            LIMIT ?
        """, (limit,))
        
        dispatches = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            "success": True,
            "count": len(dispatches),
            "dispatches": dispatches
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def assess_ambulance_need(
    symptoms: List[str],
    patient_count: int = 1,
    patient_conscious: bool = True,
    patient_breathing: bool = True
) -> Dict[str, Any]:
    """
    Assess the urgency and type of ambulance needed based on symptoms
    
    Args:
        symptoms: List of symptoms or conditions
        patient_count: Number of patients
        patient_conscious: Is the patient conscious?
        patient_breathing: Is the patient breathing?
    
    Returns:
        Dict containing assessment and recommended ambulance type
    """
    critical_symptoms = [
        'chest pain', 'heart attack', 'stroke', 'severe bleeding',
        'not breathing', 'unconscious', 'seizure', 'severe burn',
        'head injury', 'spinal injury', 'drowning', 'poisoning'
    ]
    
    moderate_symptoms = [
        'broken bone', 'fracture', 'deep cut', 'difficulty breathing',
        'allergic reaction', 'high fever', 'severe pain', 'fainting'
    ]
    
    # Check symptom severity
    symptoms_lower = [s.lower() for s in symptoms]
    has_critical = any(cs in ' '.join(symptoms_lower) for cs in critical_symptoms)
    has_moderate = any(ms in ' '.join(symptoms_lower) for ms in moderate_symptoms)
    
    # Determine urgency and ambulance type
    if not patient_breathing or not patient_conscious or has_critical:
        urgency = "CRITICAL"
        ambulance_type = "icu"
        recommendation = "ICU ambulance with advanced life support needed immediately"
    elif has_moderate or patient_count > 2:
        urgency = "HIGH"
        ambulance_type = "advanced"
        recommendation = "Advanced ambulance with paramedics recommended"
    else:
        urgency = "MODERATE"
        ambulance_type = "basic"
        recommendation = "Basic ambulance suitable for this situation"
    
    return {
        "success": True,
        "assessment": {
            "urgency_level": urgency,
            "recommended_ambulance_type": ambulance_type,
            "recommendation": recommendation,
            "patient_count": patient_count,
            "patient_conscious": patient_conscious,
            "patient_breathing": patient_breathing,
            "symptoms_analyzed": symptoms
        }
    }


# ============== TOOL DEFINITIONS FOR LLM ==============

AMBULANCE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_nearby_ambulances",
            "description": "Find available ambulances near a given location within a specified radius. Returns ambulances sorted by distance with estimated arrival times.",
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
                    "ambulance_type": {
                        "type": "string",
                        "enum": ["basic", "advanced", "icu"],
                        "description": "Filter by ambulance type"
                    }
                },
                "required": ["user_lat", "user_lon"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "dispatch_nearest_ambulance",
            "description": "Automatically find and dispatch the nearest available ambulance to the user's location",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_lat": {
                        "type": "number",
                        "description": "Destination latitude coordinate"
                    },
                    "user_lon": {
                        "type": "number",
                        "description": "Destination longitude coordinate"
                    },
                    "emergency_type": {
                        "type": "string",
                        "description": "Type of medical emergency (e.g., 'cardiac', 'accident', 'breathing difficulty')"
                    },
                    "patient_count": {
                        "type": "integer",
                        "description": "Number of patients needing assistance"
                    },
                    "ambulance_type": {
                        "type": "string",
                        "enum": ["basic", "advanced", "icu"],
                        "description": "Required ambulance type based on emergency severity"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes about the emergency"
                    }
                },
                "required": ["user_lat", "user_lon", "emergency_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "assess_ambulance_need",
            "description": "Assess the urgency and type of ambulance needed based on patient symptoms and condition",
            "parameters": {
                "type": "object",
                "properties": {
                    "symptoms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of symptoms or conditions"
                    },
                    "patient_count": {
                        "type": "integer",
                        "description": "Number of patients"
                    },
                    "patient_conscious": {
                        "type": "boolean",
                        "description": "Is the patient conscious?"
                    },
                    "patient_breathing": {
                        "type": "boolean",
                        "description": "Is the patient breathing normally?"
                    }
                },
                "required": ["symptoms"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "get_available_ambulances",
            "description": "Get a list of all currently available ambulances in the system",
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
            "name": "update_ambulance_status",
            "description": "Update the status of an ambulance (available, busy, dispatched, maintenance)",
            "parameters": {
                "type": "object",
                "properties": {
                    "ambulance_id": {
                        "type": "integer",
                        "description": "ID of the ambulance"
                    },
                    "new_status": {
                        "type": "string",
                        "enum": ["available", "busy", "dispatched", "maintenance"],
                        "description": "New status for the ambulance"
                    }
                },
                "required": ["ambulance_id", "new_status"]
            }
        }
    }
]


if __name__ == "__main__":
    # Test the tools
    print("\n=== Testing Ambulance Tools ===\n")
    
    # Test getting all ambulances
    print("1. All Ambulances:")
    result = get_all_ambulances()
    print(f"   Found {result['count']} ambulances")
    
    # Test getting nearby ambulances
    print("\n2. Nearby Ambulances (Bangalore center):")
    result = get_nearby_ambulances(12.9716, 77.5946, radius_km=5)
    print(f"   Found {result['count']} nearby ambulances")
    for amb in result['ambulances'][:3]:
        print(f"   - {amb['vehicle_number']}: {amb['distance_km']}km, ETA: {amb['estimated_arrival_minutes']}min")
    
    # Test assessment
    print("\n3. Symptom Assessment:")
    result = assess_ambulance_need(
        symptoms=["chest pain", "difficulty breathing"],
        patient_conscious=True,
        patient_breathing=True
    )
    print(f"   Urgency: {result['assessment']['urgency_level']}")
    print(f"   Recommended: {result['assessment']['recommended_ambulance_type']} ambulance")

