from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
import uvicorn
import json
#import requests
import os
from datetime import date, timedelta

MAKERSPACE_DB_USERNAME = os.environ.get('MAKERSPACE_DB_USERNAME')
MAKERSPACE_DB_PASSWORD = os.environ.get('MAKERSPACE_DB_PASSWORD')
MAKERSPACE_DB_HOST = os.environ.get('MAKERSPACE_DB_HOST')

UNI_CONFIG = {
    'host': '',
    'port': 1,
    'database': 'Museum',
    'user': MAKERSPACE_DB_USERNAME, #sql user
    'password': MAKERSPACE_DB_PASSWORD #passwrod user
}
try:
    print(f"testing connection")
    conn = mysql.connector.connect(**UNI_CONFIG)
    print(f"hello")
    if conn.is_connected():
        print(f"Connected to MakerSpace DB")
        conn.close()
    
    print(f"failed to connect")
    
except Error as e:
    print(f"Failed again: {e}")