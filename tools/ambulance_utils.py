# tools/ambulance_db.py
import sqlite3
from math import radians, cos, sin, sqrt, atan2

def haversine(lat1, lon1, lat2, lon2):
    # Calculate the distance between 2 lat/lon points (km)
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def get_nearby_ambulances(user_lat, user_lon, max_distance_km=10000.0):

    conn = sqlite3.connect("ambulance.db")
    c = conn.cursor()

    c.execute("SELECT id, driver_name, latitude, longitude FROM ambulances WHERE is_available = 1")
    rows = c.fetchall()

    if not rows:
        print("[DEBUG] No available ambulances found in DB.")
    
    nearby = []
    seen_drivers = set()
    for row in rows:
        amb_id, driver_name, lat, lon = row
        dist = haversine(user_lat, user_lon, lat, lon)
        print(f"[DEBUG] Amb: {amb_id}, Dist: {dist}")

        if dist is None:
            continue

        if dist <= max_distance_km:
            driver_key = (driver_name, round(dist, 2))
            if driver_key not in seen_drivers:
                seen_drivers.add(driver_key)
                nearby.append({
                    "id": amb_id,
                    "driver": driver_name,
                    "lat": lat,
                    "lon": lon,
                    "distance_km": round(dist, 2)
                })

    conn.close()
    print(f"[DEBUG] Nearby ambulances found: {len(nearby)}")
    return sorted(nearby, key=lambda x: x["distance_km"])


def book_ambulance(user_lat, user_lon, ambulance_id):
    conn = sqlite3.connect("ambulance.db")
    c = conn.cursor()

    try:
        # Check if ambulance exists and is available
        c.execute("SELECT is_available FROM ambulances WHERE id = ?", (ambulance_id,))
        result = c.fetchone()
        
        if not result:
            conn.close()
            raise ValueError(f"Ambulance with ID {ambulance_id} not found")
        
        if not result[0]:
            conn.close()
            raise ValueError(f"Ambulance with ID {ambulance_id} is not available")

        # Insert into bookings
        c.execute("""
            INSERT INTO bookings (user_latitude, user_longitude, ambulance_id, status)
            VALUES (?, ?, ?, 'pending')
        """, (user_lat, user_lon, ambulance_id))

        # Mark ambulance as unavailable
        c.execute("UPDATE ambulances SET is_available = 0 WHERE id = ?", (ambulance_id,))
        conn.commit()

        booking_id = c.lastrowid
        conn.close()
        return booking_id
    except Exception as e:
        conn.rollback()
        conn.close()
        raise e

def update_booking_status(booking_id, status):
    conn = sqlite3.connect("ambulance.db")
    c = conn.cursor()
    c.execute("UPDATE bookings SET status = ? WHERE id = ?", (status, booking_id))
    conn.commit()
    conn.close()

def reset_all():
    """Reset ambulance availability, clear bookings, and reset booking IDs."""
    conn = sqlite3.connect("ambulance.db")
    c = conn.cursor()

    # Set all ambulances to available
    c.execute("UPDATE ambulances SET is_available = 1")

    # Delete all existing bookings
    c.execute("DELETE FROM bookings")

    # Reset the auto-increment counter for the bookings table
    c.execute("DELETE FROM sqlite_sequence WHERE name='bookings'")

    conn.commit()
    conn.close()
    print("Reset completed: Ambulances available, bookings cleared, booking IDs reset.")


def get_booking_status(booking_id):
    conn = sqlite3.connect("ambulance.db")
    c = conn.cursor()
    c.execute("SELECT status FROM bookings WHERE id = ?", (booking_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def cancel_booking(booking_id):
    conn = sqlite3.connect("ambulance.db")
    c = conn.cursor()

    # Set status
    c.execute("UPDATE bookings SET status = 'cancelled' WHERE id = ?", (booking_id,))

    # Make ambulance available again
    c.execute("""
        UPDATE ambulances SET is_available = 1
        WHERE id = (SELECT ambulance_id FROM bookings WHERE id = ?)
    """, (booking_id,))

    conn.commit()
    conn.close()

def estimate_eta_km(speed_kmph, distance_km):
    if speed_kmph <= 0:
        return None
    time_hr = distance_km / speed_kmph
    return round(time_hr * 60)  # return ETA in minutes

def get_user_booking_history(limit=10):
    conn = sqlite3.connect("ambulance.db")
    c = conn.cursor()
    c.execute("""
        SELECT b.id, a.driver_name, b.status, b.user_latitude, b.user_longitude
        FROM bookings b
        JOIN ambulances a ON b.ambulance_id = a.id
        ORDER BY b.id DESC LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    # reset_all()
    user_lat, user_lon = 12.9335, 77.6105
    # Find ambulance
    options = get_nearby_ambulances(user_lat, user_lon)
    if not options:
        print("No ambulances available nearby.")
        exit()

    selected_amb = options[0]
    print(f"Booking ambulance: {selected_amb['driver']}")

    booking_id = book_ambulance(user_lat, user_lon, selected_amb["id"])
    print(f"Booking ID: {booking_id}")

    # Simulate confirmation
    update_booking_status(booking_id, "confirmed")

    # Estimate ETA
    eta = estimate_eta_km(speed_kmph=40, distance_km=selected_amb['distance_km'])
    print(f"ETA: {eta} minutes")
