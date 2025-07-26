import sqlite3

def create_tables():
    conn = sqlite3.connect("ambulance.db")
    c = conn.cursor()

    # Ambulance table
    c.execute("""
        CREATE TABLE IF NOT EXISTS ambulances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_name TEXT,
            latitude REAL,
            longitude REAL,
            is_available INTEGER
        )
    """)

    # Bookings table
    c.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_latitude REAL,
            user_longitude REAL,
            ambulance_id INTEGER,
            status TEXT
        )
    """)

   
    conn.commit()
    conn.close()

def populate_dummy_ambulances():
    conn = sqlite3.connect("ambulance.db")
    c = conn.cursor()

    ambulances = [
        ("Alice", 12.9330, 77.6100, 1),
        ("Bob", 12.9350, 77.6120, 1),
        ("Charlie", 12.9200, 77.6000, 0),
        ("David", 12.9400, 77.6200, 1)
    ]

    c.executemany("""
        INSERT INTO ambulances (driver_name, latitude, longitude, is_available)
        VALUES (?, ?, ?, ?)
    """, ambulances)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_tables()
    populate_dummy_ambulances()
    print("Database, tables created, and dummy data populated.")
