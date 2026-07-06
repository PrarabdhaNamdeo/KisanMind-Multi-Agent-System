"""
Adds suppliers + inventory for the remaining districts
(Vidisha, Narsinghpur, Jabalpur, Sagar, Gwalior, Ujjain)
without touching your existing Bhopal/Indore data.

HOW TO RUN:
    python add_more_suppliers.py
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

# (name, address, phone, district, distance_km, [medicines to stock])
NEW_SUPPLIERS = [
    ("Vidisha Krishi Kendra", "Bus Stand Road, Vidisha", "9876500001", "Vidisha", 3.2,
     ["Mancozeb 75% WP", "Copper Oxychloride 50% WP"]),
    ("Narsinghpur Agro Store", "Civil Lines, Narsinghpur", "9876500002", "Narsinghpur", 2.8,
     ["Chlorothalonil 75% WP", "Imidacloprid 17.8% SL"]),
    ("Jabalpur Farm Supplies", "Napier Town, Jabalpur", "9876500003", "Jabalpur", 4.5,
     ["Metalaxyl + Mancozeb (Ridomil Gold)", "Azoxystrobin 23% SC"]),
    ("Sagar Kisan Bhandar", "Makronia Road, Sagar", "9876500004", "Sagar", 3.9,
     ["Mancozeb 75% WP", "Abamectin 1.8% EC (Vertimec)"]),
    ("Gwalior Agro Center", "City Center, Gwalior", "9876500005", "Gwalior", 2.1,
     ["Copper Oxychloride 50% WP", "Imidacloprid 17.8% SL"]),
    ("Ujjain Farmers Store", "Freeganj, Ujjain", "9876500006", "Ujjain", 3.4,
     ["Chlorothalonil 75% WP", "Azoxystrobin 23% SC"]),
]


def main():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"❌ Connection failed: {e}")
        return

    cursor = conn.cursor()
    print("✅ Connected.\n")

    added_suppliers = 0
    added_inventory = 0

    for name, address, phone, district, distance_km, medicines in NEW_SUPPLIERS:
        cursor.execute("SELECT supplier_id FROM suppliers WHERE name = %s", (name,))
        existing = cursor.fetchone()

        if existing:
            supplier_id = existing[0]
            print(f"ℹ️  '{name}' already exists (id={supplier_id}) - skipping supplier insert.")
        else:
            cursor.execute(
                "INSERT INTO suppliers (name, address, phone, district, distance_km) VALUES (%s, %s, %s, %s, %s)",
                (name, address, phone, district, distance_km)
            )
            supplier_id = cursor.lastrowid
            conn.commit()
            added_suppliers += 1
            print(f"✅ Added supplier '{name}' in {district} (id={supplier_id})")

        for medicine in medicines:
            cursor.execute(
                "SELECT id FROM supplier_inventory WHERE supplier_id = %s AND medicine_name = %s",
                (supplier_id, medicine)
            )
            if cursor.fetchone():
                continue
            cursor.execute(
                "INSERT INTO supplier_inventory (supplier_id, medicine_name, in_stock) VALUES (%s, %s, TRUE)",
                (supplier_id, medicine)
            )
            added_inventory += 1
        conn.commit()

    cursor.close()
    conn.close()

    print(f"\n🎉 Done. Added {added_suppliers} new suppliers and {added_inventory} new inventory rows.")


if __name__ == "__main__":
    main()
