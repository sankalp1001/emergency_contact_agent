"""
Fire Brigade Tools Module
Tools for fire emergency dispatch, retrieval, and management
"""

import sqlite3
import math
from typing import Optional, List, Dict, Any
from datetime import datetime
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "../../../database/fire.db")

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

def estimate_arrival_time(distance_km: float, avg_speed_kmh: float = 50) -> int:
    """Estimate arrival time in minutes (fire trucks often faster due to sirens)"""
    return max(1, int((distance_km / avg_speed_kmh) * 60))


# ============== TOOL FUNCTIONS FOR LLM ==============

def get_all_fire_stations() -> Dict[str, Any]:
    """
    Retrieve all fire stations from the database
    
    Returns:
        Dict containing status and list of all fire stations
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, station_name, station_code, latitude, longitude, 
                   contact_number, available_units, total_units
            FROM fire_stations
        """)
        stations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            "success": True,
            "count": len(stations),
            "fire_stations": stations
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_available_fire_trucks() -> Dict[str, Any]:
    """
    Retrieve all available fire trucks
    
    Returns:
        Dict containing available fire trucks with station info
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, t.vehicle_number, t.truck_type, t.water_capacity,
                   s.station_name, s.latitude, s.longitude, s.contact_number
            FROM fire_trucks t
            JOIN fire_stations s ON t.station_id = s.id
            WHERE t.status = 'available'
        """)
        trucks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            "success": True,
            "count": len(trucks),
            "fire_trucks": trucks
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_nearby_fire_stations(
    user_lat: float,
    user_lon: float,
    radius_km: float = 15.0
) -> Dict[str, Any]:
    """
    Find fire stations near a given location with available units
    
    Args:
        user_lat: User's latitude
        user_lon: User's longitude
        radius_km: Search radius in kilometers (default: 15km)
    
    Returns:
        Dict containing nearby fire stations sorted by distance
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, station_name, station_code, latitude, longitude, 
                   contact_number, available_units, total_units
            FROM fire_stations
            WHERE available_units > 0
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
            "fire_stations": nearby
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_nearby_fire_trucks(
    user_lat: float,
    user_lon: float,
    radius_km: float = 15.0,
    truck_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Find available fire trucks near a given location
    
    Args:
        user_lat: User's latitude
        user_lon: User's longitude
        radius_km: Search radius in kilometers
        truck_type: Filter by type ('water_tender', 'ladder', 'rescue', 'standard')
    
    Returns:
        Dict containing nearby fire trucks sorted by distance
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT t.id, t.vehicle_number, t.truck_type, t.water_capacity,
                   s.station_name, s.latitude, s.longitude, s.contact_number
            FROM fire_trucks t
            JOIN fire_stations s ON t.station_id = s.id
            WHERE t.status = 'available'
        """
        params = []
        
        if truck_type:
            query += " AND t.truck_type = ?"
            params.append(truck_type)
        
        cursor.execute(query, params)
        trucks = cursor.fetchall()
        conn.close()
        
        nearby = []
        for truck in trucks:
            distance = calculate_distance(user_lat, user_lon, truck['latitude'], truck['longitude'])
            if distance <= radius_km:
                truck_dict = dict(truck)
                truck_dict['distance_km'] = round(distance, 2)
                truck_dict['estimated_arrival_minutes'] = estimate_arrival_time(distance)
                nearby.append(truck_dict)
        
        nearby.sort(key=lambda x: x['distance_km'])
        
        return {
            "success": True,
            "user_location": {"latitude": user_lat, "longitude": user_lon},
            "count": len(nearby),
            "fire_trucks": nearby
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def dispatch_fire_truck(
    fire_truck_id: int,
    user_lat: float,
    user_lon: float,
    fire_type: str,
    severity: str = "medium",
    people_trapped: int = 0,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Dispatch a fire truck to a location
    
    Args:
        fire_truck_id: ID of the fire truck to dispatch
        user_lat: Destination latitude
        user_lon: Destination longitude
        fire_type: Type of fire ('building', 'vehicle', 'forest', 'electrical', 'gas', 'other')
        severity: Fire severity ('low', 'medium', 'high', 'critical')
        people_trapped: Number of people trapped
        notes: Additional notes
    
    Returns:
        Dict containing dispatch confirmation
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get fire truck info
        cursor.execute("""
            SELECT t.*, s.station_name, s.latitude, s.longitude, s.contact_number, s.id as station_id
            FROM fire_trucks t
            JOIN fire_stations s ON t.station_id = s.id
            WHERE t.id = ?
        """, (fire_truck_id,))
        truck = cursor.fetchone()
        
        if not truck:
            conn.close()
            return {"success": False, "error": "Fire truck not found"}
        
        if truck['status'] != 'available':
            conn.close()
            return {"success": False, "error": f"Fire truck is currently {truck['status']}"}
        
        distance = calculate_distance(user_lat, user_lon, truck['latitude'], truck['longitude'])
        eta_minutes = estimate_arrival_time(distance)
        
        # Update truck status
        cursor.execute("UPDATE fire_trucks SET status = 'dispatched' WHERE id = ?", (fire_truck_id,))
        
        # Update station available units
        cursor.execute("""
            UPDATE fire_stations 
            SET available_units = available_units - 1 
            WHERE id = ?
        """, (truck['station_id'],))
        
        # Create dispatch record
        cursor.execute("""
            INSERT INTO fire_dispatches 
            (fire_truck_id, user_location_lat, user_location_lon, fire_type, severity, people_trapped, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'dispatched')
        """, (fire_truck_id, user_lat, user_lon, fire_type, severity, people_trapped, notes))
        
        dispatch_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "dispatch_id": dispatch_id,
            "fire_truck": {
                "id": truck['id'],
                "vehicle_number": truck['vehicle_number'],
                "truck_type": truck['truck_type'],
                "water_capacity": truck['water_capacity'],
                "station_name": truck['station_name'],
                "contact": truck['contact_number']
            },
            "destination": {"latitude": user_lat, "longitude": user_lon},
            "distance_km": round(distance, 2),
            "estimated_arrival_minutes": eta_minutes,
            "fire_type": fire_type,
            "severity": severity,
            "people_trapped": people_trapped,
            "message": f"Fire truck {truck['vehicle_number']} dispatched. ETA: {eta_minutes} minutes"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def dispatch_nearest_fire_truck(
    user_lat: float,
    user_lon: float,
    fire_type: str,
    severity: str = "medium",
    people_trapped: int = 0,
    truck_type: Optional[str] = None,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Automatically find and dispatch the nearest available fire truck
    
    Args:
        user_lat: Destination latitude
        user_lon: Destination longitude
        fire_type: Type of fire emergency
        severity: Fire severity level
        people_trapped: Number of people trapped
        truck_type: Preferred truck type (optional)
        notes: Additional notes
    
    Returns:
        Dict containing dispatch confirmation
    """
    # Find nearby trucks
    result = get_nearby_fire_trucks(user_lat, user_lon, radius_km=30, truck_type=truck_type)
    
    if not result["success"]:
        return result
    
    if result["count"] == 0:
        return {
            "success": False,
            "error": "No available fire trucks found nearby",
            "suggestion": "Call emergency services directly at 101"
        }
    
    nearest_truck = result["fire_trucks"][0]
    
    return dispatch_fire_truck(
        fire_truck_id=nearest_truck["id"],
        user_lat=user_lat,
        user_lon=user_lon,
        fire_type=fire_type,
        severity=severity,
        people_trapped=people_trapped,
        notes=notes
    )

def dispatch_multiple_units(
    user_lat: float,
    user_lon: float,
    fire_type: str,
    severity: str,
    units_needed: int = 2,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Dispatch multiple fire units for large-scale emergencies
    
    Args:
        user_lat: Destination latitude
        user_lon: Destination longitude
        fire_type: Type of fire
        severity: Fire severity
        units_needed: Number of units to dispatch
        notes: Additional notes
    
    Returns:
        Dict containing dispatch confirmations for all units
    """
    dispatched = []
    failed = []
    
    result = get_nearby_fire_trucks(user_lat, user_lon, radius_km=50)
    
    if not result["success"]:
        return result
    
    available_trucks = result["fire_trucks"]
    
    for i, truck in enumerate(available_trucks[:units_needed]):
        dispatch_result = dispatch_fire_truck(
            fire_truck_id=truck["id"],
            user_lat=user_lat,
            user_lon=user_lon,
            fire_type=fire_type,
            severity=severity,
            notes=f"Multi-unit dispatch #{i+1}. {notes or ''}"
        )
        
        if dispatch_result["success"]:
            dispatched.append(dispatch_result)
        else:
            failed.append({"truck_id": truck["id"], "error": dispatch_result["error"]})
    
    return {
        "success": len(dispatched) > 0,
        "units_requested": units_needed,
        "units_dispatched": len(dispatched),
        "dispatches": dispatched,
        "failed": failed,
        "message": f"{len(dispatched)} fire units dispatched to location"
    }

def update_fire_truck_status(fire_truck_id: int, new_status: str) -> Dict[str, Any]:
    """
    Update the status of a fire truck
    
    Args:
        fire_truck_id: ID of the fire truck
        new_status: New status ('available', 'busy', 'dispatched', 'maintenance')
    
    Returns:
        Dict containing update confirmation
    """
    valid_statuses = ['available', 'busy', 'dispatched', 'maintenance']
    
    if new_status not in valid_statuses:
        return {"success": False, "error": f"Invalid status. Must be one of: {valid_statuses}"}
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current status and station
        cursor.execute("""
            SELECT t.status, t.station_id FROM fire_trucks t WHERE t.id = ?
        """, (fire_truck_id,))
        truck = cursor.fetchone()
        
        if not truck:
            conn.close()
            return {"success": False, "error": "Fire truck not found"}
        
        old_status = truck['status']
        
        # Update truck status
        cursor.execute("UPDATE fire_trucks SET status = ? WHERE id = ?", (new_status, fire_truck_id))
        
        # Update station available units if status changed to/from available
        if old_status != 'available' and new_status == 'available':
            cursor.execute("""
                UPDATE fire_stations SET available_units = available_units + 1 WHERE id = ?
            """, (truck['station_id'],))
        elif old_status == 'available' and new_status != 'available':
            cursor.execute("""
                UPDATE fire_stations SET available_units = available_units - 1 WHERE id = ?
            """, (truck['station_id'],))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "fire_truck_id": fire_truck_id,
            "old_status": old_status,
            "new_status": new_status,
            "message": f"Fire truck status updated to '{new_status}'"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def complete_fire_dispatch(dispatch_id: int, notes: Optional[str] = None) -> Dict[str, Any]:
    """
    Mark a fire dispatch as resolved and make truck available again
    
    Args:
        dispatch_id: ID of the dispatch to complete
        notes: Resolution notes
    
    Returns:
        Dict containing completion confirmation
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM fire_dispatches WHERE id = ?", (dispatch_id,))
        dispatch = cursor.fetchone()
        
        if not dispatch:
            conn.close()
            return {"success": False, "error": "Dispatch not found"}
        
        # Update dispatch status
        cursor.execute("""
            UPDATE fire_dispatches 
            SET status = 'resolved', resolved_time = CURRENT_TIMESTAMP, notes = ?
            WHERE id = ?
        """, (notes, dispatch_id))
        
        # Make truck available
        cursor.execute("""
            UPDATE fire_trucks SET status = 'available' WHERE id = ?
        """, (dispatch['fire_truck_id'],))
        
        # Update station available units
        cursor.execute("""
            SELECT station_id FROM fire_trucks WHERE id = ?
        """, (dispatch['fire_truck_id'],))
        truck = cursor.fetchone()
        
        cursor.execute("""
            UPDATE fire_stations SET available_units = available_units + 1 WHERE id = ?
        """, (truck['station_id'],))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "dispatch_id": dispatch_id,
            "message": "Fire emergency resolved. Unit is now available."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def assess_fire_severity(
    smoke_visible: bool,
    flames_visible: bool,
    building_type: str,
    people_trapped: int = 0,
    floor_count: int = 1,
    spread_rate: str = "unknown"
) -> Dict[str, Any]:
    """
    Assess fire severity and recommend appropriate response
    
    Args:
        smoke_visible: Is smoke visible?
        flames_visible: Are flames visible?
        building_type: Type of building ('residential', 'commercial', 'industrial', 'vehicle', 'forest')
        people_trapped: Number of people trapped
        floor_count: Number of floors in building
        spread_rate: How fast is fire spreading ('slow', 'moderate', 'fast', 'unknown')
    
    Returns:
        Dict containing severity assessment and recommendations
    """
    severity_score = 0
    
    # Smoke and flames
    if smoke_visible:
        severity_score += 1
    if flames_visible:
        severity_score += 2
    
    # People trapped
    if people_trapped > 0:
        severity_score += 3
    if people_trapped > 5:
        severity_score += 2
    
    # Building type risk
    high_risk_buildings = ['industrial', 'commercial', 'forest']
    if building_type.lower() in high_risk_buildings:
        severity_score += 2
    
    # Multi-story
    if floor_count > 3:
        severity_score += 2
    elif floor_count > 1:
        severity_score += 1
    
    # Spread rate
    if spread_rate == 'fast':
        severity_score += 3
    elif spread_rate == 'moderate':
        severity_score += 1
    
    # Determine severity level
    if severity_score >= 8:
        severity = "CRITICAL"
        units_recommended = 4
        truck_types = ["water_tender", "ladder", "rescue"]
        recommendation = "Multiple units with rescue capability needed. Evacuate immediately."
    elif severity_score >= 5:
        severity = "HIGH"
        units_recommended = 2
        truck_types = ["water_tender", "rescue"]
        recommendation = "Multiple fire units recommended. Begin evacuation."
    elif severity_score >= 3:
        severity = "MEDIUM"
        units_recommended = 1
        truck_types = ["water_tender"]
        recommendation = "Standard fire response. Stay low and evacuate."
    else:
        severity = "LOW"
        units_recommended = 1
        truck_types = ["standard"]
        recommendation = "Single unit response. Monitor for changes."
    
    return {
        "success": True,
        "assessment": {
            "severity_level": severity,
            "severity_score": severity_score,
            "units_recommended": units_recommended,
            "recommended_truck_types": truck_types,
            "recommendation": recommendation,
            "evacuation_priority": "HIGH" if people_trapped > 0 else "NORMAL",
            "factors": {
                "smoke_visible": smoke_visible,
                "flames_visible": flames_visible,
                "building_type": building_type,
                "people_trapped": people_trapped,
                "floor_count": floor_count,
                "spread_rate": spread_rate
            }
        },
        "safety_instructions": [
            "Stay low to avoid smoke inhalation",
            "Do not use elevators",
            "Close doors behind you to slow fire spread",
            "Feel doors before opening - if hot, use another exit",
            "If trapped, seal door gaps and signal from window"
        ]
    }


# ============== TOOL DEFINITIONS FOR LLM ==============

FIRE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_nearby_fire_stations",
            "description": "Find fire stations near a location that have available units",
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
                        "description": "Search radius in kilometers (default: 15)"
                    }
                },
                "required": ["user_lat", "user_lon"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "dispatch_nearest_fire_truck",
            "description": "Automatically find and dispatch the nearest available fire truck to a fire emergency",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_lat": {
                        "type": "number",
                        "description": "Fire location latitude"
                    },
                    "user_lon": {
                        "type": "number",
                        "description": "Fire location longitude"
                    },
                    "fire_type": {
                        "type": "string",
                        "enum": ["building", "residential", "commercial", "industrial", "vehicle", "forest", "electrical", "gas", "kitchen", "other"],
                        "description": "Type of fire emergency"
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Severity of the fire"
                    },
                    "people_trapped": {
                        "type": "integer",
                        "description": "Number of people trapped"
                    },
                    "truck_type": {
                        "type": "string",
                        "enum": ["water_tender", "ladder", "rescue", "standard"],
                        "description": "Preferred truck type"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional emergency details"
                    }
                },
                "required": ["user_lat", "user_lon", "fire_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "dispatch_multiple_fire_units",
            "description": "Dispatch multiple fire units for large-scale fire emergencies",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_lat": {
                        "type": "number",
                        "description": "Fire location latitude"
                    },
                    "user_lon": {
                        "type": "number",
                        "description": "Fire location longitude"
                    },
                    "fire_type": {
                        "type": "string",
                        "description": "Type of fire"
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Fire severity"
                    },
                    "units_needed": {
                        "type": "integer",
                        "description": "Number of fire units needed"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional details"
                    }
                },
                "required": ["user_lat", "user_lon", "fire_type", "severity", "units_needed"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "assess_fire_severity",
            "description": "Assess fire severity and get recommendations for appropriate response",
            "parameters": {
                "type": "object",
                "properties": {
                    "smoke_visible": {
                        "type": "boolean",
                        "description": "Is smoke visible?"
                    },
                    "flames_visible": {
                        "type": "boolean",
                        "description": "Are flames visible?"
                    },
                    "building_type": {
                        "type": "string",
                        "description": "Type of building/area (residential, commercial, industrial, vehicle, forest)"
                    },
                    "people_trapped": {
                        "type": "integer",
                        "description": "Number of people trapped (default 0)"
                    },
                    "floor_count": {
                        "type": "integer",
                        "description": "Number of floors in building (default 1)"
                    },
                    "spread_rate": {
                        "type": "string",
                        "description": "How fast is fire spreading (slow, moderate, fast, unknown)"
                    }
                },
                "required": ["smoke_visible", "flames_visible", "building_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_available_fire_trucks",
            "description": "Get all currently available fire trucks in the system",
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
            "name": "update_fire_truck_status",
            "description": "Update the status of a fire truck",
            "parameters": {
                "type": "object",
                "properties": {
                    "fire_truck_id": {
                        "type": "integer",
                        "description": "ID of the fire truck"
                    },
                    "new_status": {
                        "type": "string",
                        "enum": ["available", "busy", "dispatched", "maintenance"],
                        "description": "New status"
                    }
                },
                "required": ["fire_truck_id", "new_status"]
            }
        }
    }
]


if __name__ == "__main__":
    # Test the tools
    print("\n=== Testing Fire Brigade Tools ===\n")
    
    # Test getting all stations
    print("1. All Fire Stations:")
    result = get_all_fire_stations()
    print(f"   Found {result['count']} fire stations")
    
    # Test nearby stations
    print("\n2. Nearby Fire Stations (Bangalore center):")
    result = get_nearby_fire_stations(12.9716, 77.5946, radius_km=10)
    print(f"   Found {result['count']} stations with available units")
    
    # Test fire assessment
    print("\n3. Fire Severity Assessment:")
    result = assess_fire_severity(
        smoke_visible=True,
        flames_visible=True,
        building_type="commercial",
        people_trapped=3,
        floor_count=5,
        spread_rate="moderate"
    )
    print(f"   Severity: {result['assessment']['severity_level']}")
    print(f"   Units recommended: {result['assessment']['units_recommended']}")
    print(f"   Recommendation: {result['assessment']['recommendation']}")

