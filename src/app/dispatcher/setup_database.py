"""
Database Setup Module for Emergency Contact Agent
Creates and initializes SQLite databases for ambulance, fire, and police services
"""

import sqlite3
import os
import random

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "../../../database")

def get_db_connection(db_name: str):
    """Get a connection to the specified database"""
    db_path = os.path.join(DATABASE_PATH, f"{db_name}.db")
    os.makedirs(DATABASE_PATH, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def setup_ambulance_db():
    """Create and populate the ambulance database"""
    conn = get_db_connection("ambulance")
    cursor = conn.cursor()
    
    # Drop existing tables to reset IDs
    cursor.execute("DROP TABLE IF EXISTS ambulance_dispatches")
    cursor.execute("DROP TABLE IF EXISTS ambulances")
    
    # Create ambulances table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ambulances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_number TEXT UNIQUE NOT NULL,
            station_name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            status TEXT DEFAULT 'available',
            ambulance_type TEXT DEFAULT 'basic',
            contact_number TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create dispatches table to track dispatch history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ambulance_dispatches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ambulance_id INTEGER,
            user_location_lat REAL,
            user_location_lon REAL,
            emergency_type TEXT,
            patient_count INTEGER DEFAULT 1,
            status TEXT DEFAULT 'dispatched',
            dispatch_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            arrival_time TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (ambulance_id) REFERENCES ambulances(id)
        )
    """)
    
    # Sample ambulance data (Bangalore coordinates)
    sample_ambulances = [
        ("KA-01-AM-1001", "City Hospital Ambulance", 12.9716, 77.5946, "available", "advanced", "080-1001"),
        ("KA-01-AM-1002", "Apollo Emergency", 12.9352, 77.6245, "available", "basic", "080-1002"),
        ("KA-01-AM-1003", "Manipal Ambulance", 12.9165, 77.6019, "busy", "advanced", "080-1003"),
        ("KA-01-AM-1004", "Fortis Emergency", 12.9698, 77.7500, "available", "icu", "080-1004"),
        ("KA-01-AM-1005", "Government Hospital", 12.9783, 77.5713, "available", "basic", "080-1005"),
        ("KA-01-AM-1006", "Red Cross Ambulance", 12.9250, 77.5897, "maintenance", "basic", "080-1006"),
        ("KA-01-AM-1007", "St. Johns Ambulance", 12.9300, 77.6200, "available", "advanced", "080-1007"),
        ("KA-01-AM-1008", "Narayana Health", 12.9100, 77.6500, "available", "icu", "080-1008"),
    ]
    
    cursor.executemany("""
        INSERT INTO ambulances (vehicle_number, station_name, latitude, longitude, status, ambulance_type, contact_number)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, sample_ambulances)
    
    conn.commit()
    conn.close()
    print("[OK] Ambulance database setup complete")

def setup_fire_db():
    """Create and populate the fire brigade database"""
    conn = get_db_connection("fire")
    cursor = conn.cursor()
    
    # Drop existing tables to reset IDs
    cursor.execute("DROP TABLE IF EXISTS fire_dispatches")
    cursor.execute("DROP TABLE IF EXISTS fire_trucks")
    cursor.execute("DROP TABLE IF EXISTS fire_stations")
    
    # Create fire stations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fire_stations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_name TEXT NOT NULL,
            station_code TEXT UNIQUE NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            contact_number TEXT,
            available_units INTEGER DEFAULT 2,
            total_units INTEGER DEFAULT 3,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create fire trucks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fire_trucks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_number TEXT UNIQUE NOT NULL,
            station_id INTEGER,
            truck_type TEXT DEFAULT 'standard',
            status TEXT DEFAULT 'available',
            water_capacity INTEGER DEFAULT 5000,
            FOREIGN KEY (station_id) REFERENCES fire_stations(id)
        )
    """)
    
    # Create fire dispatches table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fire_dispatches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fire_truck_id INTEGER,
            user_location_lat REAL,
            user_location_lon REAL,
            fire_type TEXT,
            severity TEXT DEFAULT 'medium',
            people_trapped INTEGER DEFAULT 0,
            status TEXT DEFAULT 'dispatched',
            dispatch_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_time TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (fire_truck_id) REFERENCES fire_trucks(id)
        )
    """)
    
    # Sample fire station data
    sample_stations = [
        ("Central Fire Station", "FS-001", 12.9716, 77.5946, "101", 3, 4),
        ("Koramangala Fire Station", "FS-002", 12.9352, 77.6245, "101", 2, 3),
        ("Whitefield Fire Station", "FS-003", 12.9698, 77.7500, "101", 2, 2),
        ("Jayanagar Fire Station", "FS-004", 12.9250, 77.5897, "101", 1, 3),
        ("Electronic City Fire Station", "FS-005", 12.8456, 77.6603, "101", 2, 2),
    ]
    
    cursor.executemany("""
        INSERT INTO fire_stations (station_name, station_code, latitude, longitude, contact_number, available_units, total_units)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, sample_stations)
    
    # Sample fire trucks
    sample_trucks = [
        ("KA-01-FT-101", 1, "water_tender", "available", 8000),
        ("KA-01-FT-102", 1, "ladder", "available", 3000),
        ("KA-01-FT-103", 1, "rescue", "busy", 2000),
        ("KA-01-FT-201", 2, "water_tender", "available", 6000),
        ("KA-01-FT-202", 2, "standard", "available", 5000),
        ("KA-01-FT-301", 3, "water_tender", "available", 7000),
        ("KA-01-FT-302", 3, "standard", "maintenance", 5000),
        ("KA-01-FT-401", 4, "water_tender", "available", 5000),
        ("KA-01-FT-501", 5, "standard", "available", 5000),
        ("KA-01-FT-502", 5, "rescue", "available", 2000),
    ]
    
    cursor.executemany("""
        INSERT INTO fire_trucks (vehicle_number, station_id, truck_type, status, water_capacity)
        VALUES (?, ?, ?, ?, ?)
    """, sample_trucks)
    
    conn.commit()
    conn.close()
    print("[OK] Fire brigade database setup complete")

def setup_police_db():
    """Create and populate the police database"""
    conn = get_db_connection("police")
    cursor = conn.cursor()
    
    # Drop existing tables to reset IDs
    cursor.execute("DROP TABLE IF EXISTS police_dispatches")
    cursor.execute("DROP TABLE IF EXISTS cases")
    cursor.execute("DROP TABLE IF EXISTS patrol_units")
    cursor.execute("DROP TABLE IF EXISTS police_stations")
    
    # Create police stations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS police_stations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_name TEXT NOT NULL,
            station_code TEXT UNIQUE NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            contact_number TEXT,
            jurisdiction_area TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create patrol units table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patrol_units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_code TEXT UNIQUE NOT NULL,
            station_id INTEGER,
            vehicle_number TEXT,
            unit_type TEXT DEFAULT 'patrol',
            status TEXT DEFAULT 'available',
            officers_count INTEGER DEFAULT 2,
            latitude REAL,
            longitude REAL,
            FOREIGN KEY (station_id) REFERENCES police_stations(id)
        )
    """)
    
    # Create police dispatches table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS police_dispatches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patrol_unit_id INTEGER,
            user_location_lat REAL,
            user_location_lon REAL,
            emergency_type TEXT,
            threat_level TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'dispatched',
            dispatch_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_time TIMESTAMP,
            case_number TEXT,
            notes TEXT,
            FOREIGN KEY (patrol_unit_id) REFERENCES patrol_units(id)
        )
    """)
    
    # Create cases table for tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_number TEXT UNIQUE NOT NULL,
            case_type TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            reported_lat REAL,
            reported_lon REAL,
            description TEXT,
            victim_safe INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)
    
    # Sample police stations
    sample_stations = [
        ("Cubbon Park Police Station", "PS-001", 12.9763, 77.5929, "100", "Central Bangalore"),
        ("Koramangala Police Station", "PS-002", 12.9279, 77.6271, "100", "Koramangala"),
        ("Whitefield Police Station", "PS-003", 12.9698, 77.7500, "100", "Whitefield"),
        ("Jayanagar Police Station", "PS-004", 12.9299, 77.5838, "100", "Jayanagar"),
        ("Electronic City Police Station", "PS-005", 12.8456, 77.6603, "100", "Electronic City"),
        ("HSR Layout Police Station", "PS-006", 12.9116, 77.6389, "100", "HSR Layout"),
    ]
    
    cursor.executemany("""
        INSERT INTO police_stations (station_name, station_code, latitude, longitude, contact_number, jurisdiction_area)
        VALUES (?, ?, ?, ?, ?, ?)
    """, sample_stations)
    
    # Sample patrol units with varying locations
    sample_units = [
        ("PATROL-001", 1, "KA-01-PC-001", "patrol", "available", 2, 12.9750, 77.5900),
        ("PATROL-002", 1, "KA-01-PC-002", "rapid_response", "available", 4, 12.9780, 77.6000),
        ("PATROL-003", 2, "KA-01-PC-003", "patrol", "busy", 2, 12.9300, 77.6300),
        ("PATROL-004", 2, "KA-01-PC-004", "patrol", "available", 2, 12.9250, 77.6200),
        ("PATROL-005", 3, "KA-01-PC-005", "patrol", "available", 2, 12.9700, 77.7450),
        ("PATROL-006", 4, "KA-01-PC-006", "patrol", "available", 2, 12.9320, 77.5850),
        ("PATROL-007", 5, "KA-01-PC-007", "rapid_response", "available", 4, 12.8500, 77.6600),
        ("PATROL-008", 6, "KA-01-PC-008", "patrol", "available", 2, 12.9100, 77.6400),
    ]
    
    cursor.executemany("""
        INSERT INTO patrol_units (unit_code, station_id, vehicle_number, unit_type, status, officers_count, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_units)
    
    conn.commit()
    conn.close()
    print("[OK] Police database setup complete")

def setup_all_databases():
    """Setup all emergency service databases"""
    print("\nSetting up Emergency Services Databases...\n")
    setup_ambulance_db()
    setup_fire_db()
    setup_police_db()
    print("\nAll databases setup complete!\n")

if __name__ == "__main__":
    setup_all_databases()

