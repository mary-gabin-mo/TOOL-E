from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, tools, transactions, ml, analytics
from app.services import ml_service, image_service

app = FastAPI(title="TOOL-E Backend Server (Modular)")

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
