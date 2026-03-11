
import sys
import os

# Add the server directory to python path
sys.path.append(os.path.join(os.getcwd(), "Server"))

from app.main import app
from fastapi.routing import APIRoute

print("Registered Routes:")
for route in app.routes:
    if isinstance(route, APIRoute):
        print(f"{route.methods} {route.path}")
