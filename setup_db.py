"""
One-time setup script: creates tables and inserts sample data
into your Aiven MySQL database.

HOW TO RUN:
1. Make sure your .env file has the correct MYSQL_HOST, MYSQL_PORT,
   MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE values from Aiven.
2. Place this file in the root of your project (same level as requirements.txt).
3. From your terminal, with your venv activated, run:
       python setup_db.py
4. You should see confirmation messages printed for each step.
   Safe to run more than once - it checks before creating/inserting.
"""

import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "kisanmind"),
    "ssl_disabled": os.getenv("MYSQL_SSL_DISABLED", "false").lower() == "true"
}

CREATE_TABLES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS suppliers (
        supplier_id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(100),
        address VARCHAR(200),
        phone VARCHAR(20),
        district VARCHAR(50),
        distance_km FLOAT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS supplier_inventory (
        id INT PRIMARY KEY AUTO_INCREMENT,
        supplier_id INT,
        medicine_name VARCHAR(100),
        in_stock BOOLEAN,
        FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS farmer_queries (
        id INT PRIMARY KEY AUTO_INCREMENT,
        farmer_phone VARCHAR(20),
        disease VARCHAR(100),
        confidence FLOAT,
        location VARCHAR(100),
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
]

SAMPLE_SUPPLIERS = [
    ("Kisan Agro Center", "Main Road, Bhopal", "9876543210", "Bhopal", 2.5),
    ("Green Field Agro Store", "Station Road, Bhopal", "9876543211", "Bhopal", 4.1),
    ("Farmer Friend Agro", "MG Road, Indore", "9876543212", "Indore", 3.0),
]

SAMPLE_INVENTORY = [
    # (supplier index starting at 1, medicine_name, in_stock)
    (1, "Mancozeb 75% WP", True),
    (1, "Copper Oxychloride 50% WP", True),
    (1, "Imidacloprid 17.8% SL", True),
    (2, "Chlorothalonil 75% WP", True),
    (2, "Metalaxyl + Mancozeb (Ridomil Gold)", True),
    (3, "Abamectin 1.8% EC (Vertimec)", True),
    (3, "Azoxystrobin 23% SC", True),
]


def main():
    print(f"Connecting to {DB_CONFIG['host']}:{DB_CONFIG['port']} ...")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"❌ Connection failed: {e}")
        return

    print("✅ Connected successfully.\n")
    cursor = conn.cursor()

    print("Creating tables (if they don't already exist)...")
    for stmt in CREATE_TABLES_SQL:
        cursor.execute(stmt)
    conn.commit()
    print("✅ Tables ready.\n")

    cursor.execute("SELECT COUNT(*) FROM suppliers")
    existing_count = cursor.fetchone()[0]

    if existing_count > 0:
        print(f"ℹ️  suppliers table already has {existing_count} row(s) - skipping sample data insert.")
        print("   (Delete rows manually first if you want to re-seed.)")
    else:
        print("Inserting sample suppliers...")
        cursor.executemany(
            "INSERT INTO suppliers (name, address, phone, district, distance_km) VALUES (%s, %s, %s, %s, %s)",
            SAMPLE_SUPPLIERS
        )
        conn.commit()
        print(f"✅ Inserted {len(SAMPLE_SUPPLIERS)} suppliers.\n")

        print("Inserting sample inventory...")
        cursor.executemany(
            "INSERT INTO supplier_inventory (supplier_id, medicine_name, in_stock) VALUES (%s, %s, %s)",
            SAMPLE_INVENTORY
        )
        conn.commit()
        print(f"✅ Inserted {len(SAMPLE_INVENTORY)} inventory rows.\n")

    cursor.close()
    conn.close()
    print("🎉 Setup complete. Your Aiven MySQL database is ready to use.")


if __name__ == "__main__":
    main()
