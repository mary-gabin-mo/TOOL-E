from sqlalchemy import create_engine, text
import sys
import os
from dotenv import load_dotenv

load_dotenv('.env.local')

MAKERSPACE_DB_USERNAME = os.getenv('MAKERSPACE_DB_USERNAME')
MAKERSPACE_DB_PASSWORD = os.getenv('MAKERSPACE_DB_PASSWORD')
MAKERSPACE_DB_HOST = os.getenv('MAKERSPACE_DB_HOST')
MAKERSPACE_DB_PORT = os.getenv('MAKERSPACE_DB_PORT')

DATABASE_URL = f"mysql+pymysql://{MAKERSPACE_DB_USERNAME}:{MAKERSPACE_DB_PASSWORD}@{MAKERSPACE_DB_HOST}:{MAKERSPACE_DB_PORT}/{'Museum'}"

print(f"1. Attempting to connect to: {MAKERSPACE_DB_HOST}...")
print(f"{MAKERSPACE_DB_USERNAME=}, {MAKERSPACE_DB_PASSWORD=}, {MAKERSPACE_DB_HOST=}, {MAKERSPACE_DB_PORT=}")

try:
    # Create Engine
    engine = create_engine(DATABASE_URL)

    userid = 30113779
    # Try to actually connect
    with engine.connect() as connection:

        sql_query = text(f"SELECT UCID, recordDate FROM MakerspaceCapstone WHERE UCID = :ucid ")
        print("2. Connection object created successfully.")

        # Run a simpl query to verify
        result = connection.execute(sql_query, {"ucid": userid}).fetchone()
        print(result)
        print("3. Query executed successfully!")
        print(result.UCID)
        print(result.recordDate)
        print("\nSUCCESS: Your database connection works perfectly.")

except ImportError:
    print("\nERROR")
    print("install pymysql.")

except Exception as e:
    print("\nERROR: Connection Failed.")
    print("-" * 30)
    print(e)
    print("-" * 30)
    print("\nCheck the following:")