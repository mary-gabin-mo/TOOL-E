from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
# import mysql.connector
# from mysql.connector import Error
from sqlalchemy import create_engine, Connection, Column, Integer, String, DateTime, Date, Numeric, func, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import uvicorn
import json
#import requests
import os
from dotenv import load_dotenv
from datetime import date, timedelta

load_dotenv('.env.local')

TOOL_E_DB_USERNAME = os.getenv('TOOL_E_DB_USERNAME')
TOOL_E_DB_PASSWORD = os.getenv('TOOL_E_DB_PASSWORD')

MAKERSPACE_DB_USERNAME = os.getenv('MAKERSPACE_DB_USERNAME')
MAKERSPACE_DB_PASSWORD = os.getenv('MAKERSPACE_DB_PASSWORD')
MAKERSPACE_DB_HOST = os.getenv('MAKERSPACE_DB_HOST')
MAKERSPACE_DB_PORT = os.getenv('MAKERSPACE_DB_PORT')

DATABASE_URL = f"mysql+pymysql://{MAKERSPACE_DB_USERNAME}:{MAKERSPACE_DB_PASSWORD}@{MAKERSPACE_DB_HOST}:{MAKERSPACE_DB_PORT}/{'Museum'}"



app = FastAPI(title="Pi Data Ingestion Server")

# --- MySQL Configs ---
TOOLE_CONFIG = {
    'host': 'localhost',
    'database': 'tool_e_db',
    'user': '{TOOL_E_DB_USERNAME}',
    'password': '{TOOL_E_DB_PASSWORD}'
}

UNI_CONFIG = {
    'host': MAKERSPACE_DB_HOST,
    'port': MAKERSPACE_DB_PORT,
    'database': 'Museum',
    'user': MAKERSPACE_DB_USERNAME, #sql user
    'password': MAKERSPACE_DB_PASSWORD #passwrod user
}

#--- Pydantic Model for Incoming Data ---
class UserRequest(BaseModel):
    UCID: Optional[int] = None   
    barcode: Optional[str] = None

class ServerResponse(BaseModel):
    success: bool
    message: str


#--- Database Helper Functions ---
# def save_data_to_toole(data: UserRequest):
#     conn = None
#     try:
#         conn = mysql.connector.connect(**TOOLE_CONFIG)
#         cursor = conn.cursor()

#         sql_insert = """
#         INSERT INTO sensor_readings (temperature, humidity, reading_timestamp)
#         VALUES (%s, %s, %s)
#         """
#         record = (data.temperature, data.humidity, data.timestamp)

#         cursor.execute(sql_insert, record)
#         conn.commit()
#         print(f"Data saved to TOOLE Datebase (ID: {cursor.lastrowid})")

#     except Error as e:
#         print(f"TOOLE database Error: {e}")
#         raise HTTPException(status_code=500, detail="Database insertion failed at TOOLE Database")
    
#     finally:
#         if conn and conn.is_connected():
#             cursor.close()
#             conn.close()

# def compare_and_verify() -> bool:
#     toole_conn = None
#     uni_conn = None

#     try:
#         #connect to db
#         toole_conn = mysql.connector.connect(**TOOLE_CONFIG)
#         uni_conn = mysql.connector.connect(**UNI_CONFIG)
#         toole_cursor = toole_conn.cursor(dictionary=True)
#         uni_cursor = uni_conn.cursor(dictionary=True)

#     #Will need to change the DB search string
#         #fetching latest data from TOOLE DB
#         toole_cursor.execute("SELECT UCID FROM student_id ORDER BY id DESC LIMIT 1")
#         latest_reading = toole_cursor.fetchone()

#         if not latest_reading:
#             print("No data in TOOLE DB to verify")
#             return False
        
#         # Fetch verification values from Uni DB
#         uni_cursor.execute("SELECT UCID FROM student_id WHERE UCID=(student_ucid)")
#         thresholds = uni_cursor.fechone()

#         if not thresholds:
#             print("No thresholds found in Uni DB")
#             return False

#         # Comparing IDs
#         ucid_ok = (latest_reading['UCID'] >= thresholds['UCID'] and 
#                    latest_reading['UCID'] <= thresholds['UCID'])
        
#         is_valid = ucid_ok
        
#         print(f" UCID is Valid")
#         return is_valid

#     except Error as e:
#         print(f"Error verifiying UCID")
#         return False
    
#     finally:
#         if toole_conn and toole_conn.is_connected():
#             toole_conn.close()
#         if uni_conn and uni_conn.is_connected():
#             uni_conn.close()


# # Receives JSON from the Pi, saves it to TOOLE DB and checks it with the uni DB
# @app.post("/api/ingest")
# async def ingest_data(data: UserRequest):
#     print(f"\n--- API Received Data: UCID={data.UCID} @ {data.timestamp} ---")

    

#     verification_passed = compare_and_verify()

#     if (verification_passed == True):
#         save_data_to_toole(data)

#     return {
#         "status": "success",
#         "message": "Data received, saved, and verified",
#         "verification_result": verification_passed
#     }

def get_db_connection():
    # try: 
    #     conn = mysql.connector.connect(**UNI_CONFIG)
    #     print(f"CONNECTED TO DATABASE")
    #     return conn
    # except Error as e:
    #     print(f"Database Connection Error: {e}")
    #     raise HTTPException(status_code=500, detail="Could not connect to database")

    engine = create_engine(DATABASE_URL)

    conn = engine.connect()
    try:
        yield conn
    finally: 
        conn.close()

@app.post("/validate_user", response_model=ServerResponse)
async def validate_user_route(request: UserRequest):
    # Receives a user ID, checks the database for existence and status, and returns validation status, and returns validation status
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        print(f"CONNECTED TO DATABASE")

        if request.UCID:
            print(f"[SERVER] Validating UserID: {request.UCID}")
            # conn = get_db_connection()
            # user = db.query(UserRequest).filter(UserRequest.UCID == request.user_id).first() 
        
            sql_query = text(f"SELECT FirstName, UCID, UNICARDBarcode, recordDate FROM MakerspaceCapstone WHERE UCID = :ucid ")
        
            user = conn.execute(sql_query,{"ucid": int(request.UCID)}).fetchone()
        
        elif request.barcode:
            print(f"[SERVER] Validating UserID: {request.barcode}")

            # Keep the SQL simple (no extra semicolon needed inside the quotes)
            sql_query = text("SELECT FirstName, UCID, UNICARDBarcode, recordDate FROM MakerspaceCapstone WHERE UNICARDBarcode = :barcode")
            
            # ADD THE SEMICOLON HERE to the input data
            barcode_input = f"{request.barcode};" 

            user = conn.execute(sql_query, {"barcode": barcode_input}).fetchone()

        if not user:
            return ServerResponse(
                success=False,
                message="User not found in database"
            )
        
        #Variable declaration 0=FirstName 1=UCID 2=UNICARDBarode 3=WaiverDate
        first_name = user[0]                
        waiver_date = user[3]        

        # checker for waiver (recordDate)
        one_year_ago = date.today() - timedelta(days=365)
            
        if waiver_date is None or waiver_date < one_year_ago:
            return ServerResponse(
                success=False,
                message="Waiver is expired, please renew"
            )
        
        return ServerResponse(
            success=True,
            message=f"Access Granted, {first_name}"
        )
    # try:
    #     # sql_query = """SELECT UCID, recordDate FROM MakerspaceCapstone WHERE UCID = %s """

    #     # cursor.execute(sql_query, (request.UCID))
    #     # user = cursor.fetchone()

    #     # checker for UCID
    #     if not user:
    #         return ServerResponse(
    #             success=False,
    #             message="User not found in database"
    #         )
        
    #     # checker for waiver (recordDate)

    #     waiver_date = user['recordDate']
    #     one_year_ago = date.today() - timedelta(days=365)
        
    #     if waiver_date is None or waiver_date < one_year_ago:
    #         return ServerResponse(
    #             success=False,
    #             message="Waiver is expired, please renew"
    #         )
        
    #     return ServerResponse(
    #         valid=True,
    #         message="Access Granted"
    #     )
    
    # except Error as e:
    #     print(f"SQL Query Error: {e}")
    #     raise HTTPException(status_code=500, detail="Databse query failed")
    
    # finally:
    #     if conn and conn.is_connected():
    #         cursor.close()
    #         conn.close()


if __name__ == '__main__':
    
    uvicorn.run(app, host="0.0.0.0", port=5000) #uses port 0.0.0.0 to be accessible from Pi on local network

    