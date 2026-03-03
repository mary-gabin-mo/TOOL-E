from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, tools, transactions, ml, analytics
from app.services import ml_service, image_service

app = FastAPI(title="TOOL-E Backend Server (Modular)")

# --- Manually registered endpoint to debug the 404 issue ---
from fastapi import HTTPException
from app.models import KioskTransactionRequest
from app.database import engine_tools
from sqlalchemy import text
from app.services import image_service
from datetime import datetime
import os

@app.post("/transaction") 
async def manual_create_transaction_debug(request: Request):
    print(f"DEBUG: Manual '/transaction' handler reached from {request.client.host}")
    try:
        body = await request.json()
        print(f"DEBUG: Payload received: {body}")
        payload = KioskTransactionRequest(**body)
    except Exception as e:
        print(f"DEBUG: Parsing failed: {e}")
        raise HTTPException(status_code=422, detail=str(e))

    # Re-use the logic from transactions.py roughly
    with engine_tools.begin() as conn:
        try:
            u_id = int(payload.user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user_id")
        
        for item in payload.transactions:
            # Simplified logic for debug
            final_img_path = item.img_filename
            # ... skipping complex logic for brevity in debug ...
            
            desired_return = None
            if payload.return_date:
                 try:
                    desired_return = datetime.strptime(payload.return_date, "%Y-%m-%d %H:%M:%S")
                 except: pass

            conn.execute(
                text("INSERT INTO transactions (user_id, user_name, tool_id, desired_return_date, checkout_timestamp, image_path, purpose) VALUES (:uid, :uname, NULL, :d_return, NOW(), :img, 'Manual Debug Borrow')"),
                {"uid": u_id, "uname": payload.user_name, "d_return": desired_return, "img": final_img_path}
            )
            print(f"DEBUG: Inserted transaction for {u_id}")

    return {"success": True, "message": "Manual Debug Transaction Recorded"}
# -----------------------------------------------------------

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"INCOMING REQUEST: {request.method} {request.url}")
    print(f"PATH HEX: {request.url.path.encode('utf-8').hex()}") # Detect hidden chars
    response = await call_next(request)
    print(f"OUTGOING RESPONSE: {response.status_code}")
    return response

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    # Allow all origins for development/LAN access
    # In production, specify the exact IP of the Kiosk (e.g., "http://192.168.1.6:5173")
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup Events
@app.on_event("startup")
async def startup_event():
    # Load ML Model
    ml_service.load_ml_model()
    
    # Init Paths
    image_service.init_image_dirs()
    
    # Run cleanup
    image_service.cleanup_temp_files(max_age_hours=24)

# Include Routers
app.include_router(auth.router)
app.include_router(tools.router)
app.include_router(transactions.router)
app.include_router(ml.router)
app.include_router(analytics.router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Server is running"}
