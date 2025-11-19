from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
import uvicorn
import json
import requests

app = FastAPI(title="Pi Data Ingestion Server")

# --- MySQL Configs ---
TOOLE_CONFIG = {
    'host': 'localhost',
    'database': 'pi_data',
    'user': '', #sql user
    'password': '' #passwrod user
}

UNI_CONFIG = {
    'host': 'localhost',
    'database': 'verification_db',
    'user': '', #sql user
    'password': '' #passwrod user
}

#--- Pydantic Model for Incoming Data ---
class SensorData(BaseModel):
    UCID: int
    first_name: str
    last_name: str


#--- Database Helper Functions ---
def save_data_to_toole(data: SensorData):
    conn = None
    try:
        conn = mysql.connector.connect(**TOOLE_CONFIG)
        cursor = conn.cursor()

        sql_insert = """
        INSERT INTO sensor_readings (temperature, humidity, reading_timestamp)
        VALUES (%s, %s, %s)
        """
        record = (data.temperature, data.humidity, data.timestamp)

        cursor.execute(sql_insert, record)
        conn.commit()
        print(f"Data saved to TOOLE Datebase (ID: {cursor.lastrowid})")

    except Error as e:
        print(f"TOOLE database Error: {e}")
        raise HTTPException(status_code=500, detail="Database insertion failed at TOOLE Database")
    
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def compare_and_verify() -> bool:
    toole_conn = None
    uni_conn = None

    try:
        #connect to db
        toole_conn = mysql.connector.connect(**TOOLE_CONFIG)
        uni_conn = mysql.connector.connect(**UNI_CONFIG)
        toole_cursor = toole_conn.cursor(dictionary=True)
        uni_cursor = uni_conn.cursor(dictionary=True)

    #Will need to change the DB search string
        #fetching latest data from TOOLE DB
        toole_cursor.execute("SELECT UCID FROM student_id ORDER BY id DESC LIMIT 1")
        latest_reading = toole_cursor.fetchone()

        if not latest_reading:
            print("No data in TOOLE DB to verify")
            return False
        
        # Fetch verification values from Uni DB
        uni_cursor.execute("SELECT UCID FROM student_id WHERE UCID=(student_ucid)")
        thresholds = uni_cursor.fechone()

        if not thresholds:
            print("No thresholds found in Uni DB")
            return False

        # Comparing IDs
        ucid_ok = (latest_reading['UCID'] >= thresholds['UCID'] and 
                   latest_reading['UCID'] <= thresholds['UCID'])
        
        is_valid = ucid_ok
        
        print(f" UCID is Valid")
        return is_valid

    except Error as e:
        print(f"Error verifiying UCID")
        return False
    
    finally:
        if toole_conn and toole_conn.is_connected():
            toole_conn.close()
        if uni_conn and uni_conn.is_connected():
            uni_conn.close()


# Receives JSON from the Pi, saves it to TOOLE DB and checks it with the uni DB
@app.post("/api/ingest")
async def ingest_data(data: SensorData):
    print(f"\n--- API Received Data: UCID={data.UCID} @ {data.timestamp} ---")

    save_data_to_toole(data)

    verification_passed = compare_and_verify()

    return {
        "status": "success",
        "message": "Data received, saved, and verified",
        "verification_result": verification_passed
    }


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=5000) #uses port 0.0.0.0 to be accessible from Pi on local network