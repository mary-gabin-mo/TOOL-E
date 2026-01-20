from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import uvicorn
import os
import io
import json
import torch
import torch.nn as nn
from torchvision import transforms, models
from torchvision.models import EfficientNet_V2_S_Weights
from PIL import Image
from dotenv import load_dotenv
from datetime import date, timedelta

load_dotenv('.env.local')

# ==========================================
# ML CONFIGURATION & SETUP
# ==========================================
# Calculate paths relative to this file so it works regardless of where you run it from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, '..', 'ML', 'efficientnet_finetuned_sprint2.pth')
CLASS_NAMES_PATH = os.path.join(BASE_DIR, '..', 'ML', 'class_names.json')

IMG_SIZE = 384
NORMALIZE_MEAN = [0.485, 0.456, 0.406]
NORMALIZE_STD = [0.229, 0.224, 0.225]

# Load Class Names
CLASS_NAMES = []
if os.path.exists(CLASS_NAMES_PATH):
    try:
        with open(CLASS_NAMES_PATH, 'r') as f:
            CLASS_NAMES = json.load(f)
        print(f"[ML] Loaded {len(CLASS_NAMES)} classes.")
    except Exception as e:
        print(f"[ML] Error loading class names: {e}")
else:
    print(f"[ML] Warning: Class names file not found at {CLASS_NAMES_PATH}")

# Define Transform
inference_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=NORMALIZE_MEAN, std=NORMALIZE_STD)
])

# Load Model Logic
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
ml_model = None

def load_ml_model():
    global ml_model
    if not os.path.exists(MODEL_PATH):
        print(f"[ML] Model file not found at {MODEL_PATH}. ML features disabled.")
        return

    print("[ML] Loading AI Model... (This may take a few seconds)")
    try:
        weights = EfficientNet_V2_S_Weights.DEFAULT
        model = models.efficientnet_v2_s(weights=weights)
        
        # Rebuild Head
        in_features = model.classifier[1].in_features
        # Ensure we have class names to determine output size, default to 15 if missing
        num_classes = len(CLASS_NAMES) if CLASS_NAMES else 15
        model.classifier[1] = nn.Linear(in_features, num_classes)
        
        # Load Weights
        model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
        model.to(device)
        model.eval()
        ml_model = model
        print("[ML] Model Loaded Successfully!")
    except Exception as e:
        print(f"[ML] Failed to load model: {e}")

# Load the model immediately on startup
load_ml_model()

# --- Database 1: User Database (Museum/Makerspace) ---
MAKERSPACE_DB_USERNAME = os.getenv('MAKERSPACE_DB_USERNAME')
MAKERSPACE_DB_PASSWORD = os.getenv('MAKERSPACE_DB_PASSWORD')
MAKERSPACE_DB_HOST = os.getenv('MAKERSPACE_DB_HOST')
MAKERSPACE_DB_PORT = os.getenv('MAKERSPACE_DB_PORT')

USER_DB_URL = f"mysql+pymysql://{MAKERSPACE_DB_USERNAME}:{MAKERSPACE_DB_PASSWORD}@{MAKERSPACE_DB_HOST}:{MAKERSPACE_DB_PORT}/{'Museum'}"

# --- Database 2: Tools Database (Local Tool-E DB) ---
TOOL_E_DB_USERNAME = os.getenv('TOOL_E_DB_USERNAME')
TOOL_E_DB_PASSWORD = os.getenv('TOOL_E_DB_PASSWORD')
TOOLS_DB_URL = f"mysql+pymysql://{TOOL_E_DB_USERNAME}:{TOOL_E_DB_PASSWORD}@localhost:3306/tool_e_db"


app = FastAPI(title="TOOL-E Backend Server")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

#--- Pydantic Model for Incoming Data ---
class UserRequest(BaseModel):
    UCID: Optional[int] = None   
    barcode: Optional[str] = None

class ServerResponse(BaseModel):
    success: bool
    message: str

# --- Tools Models ---
class ToolInput(BaseModel):
    name: str
    type: str
    total_quantity: int
    available_quantity: int

class ToolUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    total_quantity: Optional[int] = None
    available_quantity: Optional[int] = None

# --------------------

@app.post("/validate_user", response_model=ServerResponse)
async def validate_user_route(request: UserRequest):
    # Receives a user ID, checks the database for existence and status, and returns validation status
    engine = create_engine(USER_DB_URL)

    with engine.connect() as conn:
        print(f"CONNECTED TO DATABASE")

        if request.UCID:
            print(f"[SERVER] Validating UserID: {request.UCID}")
            sql_query = text(f"SELECT FirstName, UCID, UNICARDBarcode, recordDate FROM MakerspaceCapstone WHERE UCID = :ucid ")
            user = conn.execute(sql_query,{"ucid": int(request.UCID)}).fetchone()
        
        elif request.barcode:
            print(f"[SERVER] Validating UserID: {request.barcode}")
            sql_query = text("SELECT FirstName, UCID, UNICARDBarcode, recordDate FROM MakerspaceCapstone WHERE UNICARDBarcode = :barcode")
            
            # ADD THE SEMICOLON HERE to the input data
            barcode_input = f"{request.barcode};" 
            user = conn.execute(sql_query, {"barcode": barcode_input}).fetchone()
        
        else:
             return ServerResponse(
                success=False,
                message="No ID provided"
            )

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

# --- ML Prediction Endpoint ---
@app.post("/identify_tool")
async def identify_tool(file: UploadFile = File(...)):
    """
    Receives an image file, runs it through the loaded ML model, 
    and returns the predicted tool class and confidence.
    """
    if ml_model is None:
         raise HTTPException(status_code=503, detail="ML Model is not loaded (check server logs/paths)")

    try:
        # 1. Read the file content
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert('RGB')
        
        # 2. Preprocess
        input_tensor = inference_transform(image)
        input_batch = input_tensor.unsqueeze(0).to(device)

        # 3. Predict
        with torch.no_grad():
            output = ml_model(input_batch)
            probabilities = torch.nn.functional.softmax(output[0], dim=0)
            
            # Get top prediction
            top_prob, top_catid = torch.topk(probabilities, 1)
            class_id = top_catid.item()
            score = top_prob.item()
            
            # Safety check if class_id is valid
            if class_id < len(CLASS_NAMES):
                class_name = CLASS_NAMES[class_id]
            else:
                class_name = f"Unknown_Class_{class_id}"
            
            # Get all probabilities
            all_probs = {CLASS_NAMES[i]: prob.item() for i, prob in enumerate(probabilities) if i < len(CLASS_NAMES)}

        return {
            "success": True,
            "prediction": class_name,
            "confidence": score,
            "all_probabilities": all_probs
        }

    except Exception as e:
        print(f"[ML] Prediction Error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

# --- Tool Management Endpoints ---

@app.get("/tools")
async def get_tools():
    """Get all tools from the database"""
    engine = create_engine(TOOLS_DB_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, name, type, total_quantity, available_quantity FROM tools"))
        tools = []
        for row in result:
             tools.append({
                 "id": row.id,
                 "name": row.name,
                 "type": row.type,
                 "total_quantity": row.total_quantity,
                 "available_quantity": row.available_quantity
             })
        return tools

@app.post("/tools")
async def create_tool(tool: ToolInput):
    """Add a new tool to the inventory"""
    engine = create_engine(TOOLS_DB_URL)
    with engine.connect() as conn:
        query = text("""
            INSERT INTO tools (name, type, total_quantity, available_quantity)
            VALUES (:name, :type, :total, :available)
        """)
        conn.execute(query, {
            "name": tool.name,
            "type": tool.type,
            "total": tool.total_quantity,
            "available": tool.available_quantity
        })
        conn.commit()
    return {"success": True, "message": "Tool created successfully"}

@app.put("/tools/{tool_id}")
async def update_tool(tool_id: int, tool: ToolUpdate):
    """Update fields of an existing tool"""
    engine = create_engine(TOOLS_DB_URL)
    with engine.connect() as conn:
        # Check if tool exists
        check = conn.execute(text("SELECT id FROM tools WHERE id = :id"), {"id": tool_id}).fetchone()
        if not check:
            raise HTTPException(status_code=404, detail="Tool not found")

        updates = []
        params = {"id": tool_id}
        
        if tool.name is not None:
            updates.append("name = :name")
            params["name"] = tool.name
        if tool.type is not None:
             updates.append("type = :type")
             params["type"] = tool.type
        if tool.total_quantity is not None:
             updates.append("total_quantity = :total")
             params["total"] = tool.total_quantity
        if tool.available_quantity is not None:
             updates.append("available_quantity = :available")
             params["available"] = tool.available_quantity
        
        if not updates:
             return {"success": True, "message": "No changes provided"}

        sql = f"UPDATE tools SET {', '.join(updates)} WHERE id = :id"
        conn.execute(text(sql), params)
        conn.commit()
        
    return {"success": True, "message": "Tool updated successfully"}

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=5000)

