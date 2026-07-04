import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "kisanmind")
}


def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            return conn
    except Error as e:
        raise ConnectionError(f"MySQL connection failed: {e}")


def extract_medicine_name(treatment: dict) -> str:
    medicine = treatment.get("chemical_treatment", {}).get("medicine", "")

    if not medicine or medicine in ["No treatment needed", "Consult local agronomist before applying chemicals"]:
        return None

    medicine_clean = medicine.split("(")[0].strip()
    return medicine_clean


def find_nearest_supplier(district: str, medicine_name: str) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    district_clean = district.split(",")[0].strip()
    medicine_keyword = medicine_name.split("+")[0].strip().split()[0]

    print(f"🔍 Searching suppliers in: {district_clean}")
    print(f"   For medicine containing: {medicine_keyword}")

    query = """
        SELECT 
            s.name,
            s.address,
            s.phone,
            s.district,
            s.distance_km,
            si.medicine_name
        FROM suppliers s
        JOIN supplier_inventory si 
            ON s.supplier_id = si.supplier_id
        WHERE 
            s.district = %s
            AND si.medicine_name LIKE %s
            AND si.in_stock = TRUE
        ORDER BY s.distance_km ASC
        LIMIT 3
    """

    cursor.execute(query, (district_clean, f"%{medicine_keyword}%"))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    if results:
        nearest = results[0]
        return {
            "found": True,
            "supplier_name": nearest["name"],
            "address": nearest["address"],
            "phone": nearest["phone"],
            "distance_km": nearest["distance_km"],
            "medicine_available": nearest["medicine_name"],
            "all_nearby": results
        }
    else:
        return find_fallback_supplier(medicine_keyword)


def find_fallback_supplier(medicine_keyword: str) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT s.name, s.address, s.phone, s.district, s.distance_km
        FROM suppliers s
        JOIN supplier_inventory si ON s.supplier_id = si.supplier_id
        WHERE si.medicine_name LIKE %s AND si.in_stock = TRUE
        ORDER BY s.distance_km ASC
        LIMIT 1
    """

    cursor.execute(query, (f"%{medicine_keyword}%",))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result:
        return {
            "found": True,
            "supplier_name": result["name"],
            "address": result["address"],
            "phone": result["phone"],
            "distance_km": result["distance_km"],
            "medicine_available": medicine_keyword,
            "note": "Supplier found in nearby district"
        }
    else:
        return {
            "found": False,
            "supplier_name": "No supplier found",
            "address": "Contact Krishi Vigyan Kendra",
            "phone": "1800-180-1551",
            "distance_km": 0,
            "note": "Call national Kisan helpline"
        }


def get_supplier_for_treatment(treatment: dict, farmer_location: str) -> dict:
    medicine_name = extract_medicine_name(treatment)

    if not medicine_name:
        return {
            "found": False,
            "supplier_name": "No medicine needed",
            "address": "Your crop is healthy!",
            "phone": "N/A",
            "distance_km": 0
        }

    return find_nearest_supplier(farmer_location, medicine_name)


def format_supplier_for_voice(supplier: dict) -> str:
    if not supplier["found"] or supplier["distance_km"] == 0:
        return "आपकी फसल स्वस्थ है, कोई दवाई की जरूरत नहीं है।"

    return f"""
    नजदीकी दुकान: {supplier['supplier_name']}।
    पता: {supplier['address']}।
    दूरी: {supplier['distance_km']} किलोमीटर।
    फोन नंबर: {supplier['phone']}।
    """.strip()