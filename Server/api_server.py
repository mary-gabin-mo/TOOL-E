from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import uvicorn
import os
import secrets
import io
import json
import torch
import torch.nn as nn
from torchvision import transforms, models
from torchvision.models import EfficientNet_V2_S_Weights
from PIL import Image
from dotenv import load_dotenv
from datetime import datetime, date, timedelta

load_dotenv('.env.local')

# ==========================================
# ML CONFIGURATION & SETUP
# ==========================================
# Calculate paths relative to this file so it works regardless of where you run it from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'efficientnet_finetuned_v2.pth')
CLASS_NAMES_PATH = os.path.join(BASE_DIR, 'class_names.json')

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
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#--- Pydantic Model for Incoming Data ---
class UserRequest(BaseModel):
    UCID: Optional[int] = None   
    barcode: Optional[str] = None

class ServerResponse(BaseModel):
    success: bool
    message: str

class LoginPayload(BaseModel):
    email: str
    password: str

class LoginUser(BaseModel):
    user_id: int
    user_name: str
    email: str

class LoginResponse(BaseModel):
    token: str
    user: LoginUser

# --- Tools Models ---
class ToolInput(BaseModel):
    tool_name: str
    tool_size: Optional[str] = None
    tool_type: str
    current_status: str = "Available"
    total_quantity: int
    available_quantity: int
    consumed_quantity: int = 0
    trained: bool = False

class ToolUpdate(BaseModel):
    tool_name: Optional[str] = None
    tool_size: Optional[str] = None
    tool_type: Optional[str] = None
    current_status: Optional[str] = None
    total_quantity: Optional[int] = None
    available_quantity: Optional[int] = None
    consumed_quantity: Optional[int] = None
    trained: Optional[bool] = None

# --- Transactions Models ---
class TransactionInput(BaseModel):
    user_id: Optional[int] = None
    tool_id: Optional[int] = None
    desired_return_date: Optional[str] = None
    return_timestamp: Optional[str] = None
    quantity: int = 1
    purpose: Optional[str] = None
    image_path: Optional[str] = None
    classification_correct: Optional[bool] = None
    weight: int = 0

class TransactionUpdate(BaseModel):
    user_id: Optional[int] = None
    tool_id: Optional[int] = None
    desired_return_date: Optional[str] = None
    return_timestamp: Optional[str] = None
    quantity: Optional[int] = None
    purpose: Optional[str] = None
    image_path: Optional[str] = None
    classification_correct: Optional[bool] = None
    weight: Optional[int] = None

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

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(payload: LoginPayload):
    """
    Temporary login for Admin Web using tool_e_db.users.
    Username: email
    Password: user_id (as string)
    """
    engine = create_engine(TOOLS_DB_URL)
    with engine.connect() as conn:
        user = conn.execute(
            text(
                """
                SELECT user_id, user_name, email
                FROM users
                WHERE LOWER(email) = LOWER(:email)
                LIMIT 1
                """
            ),
            {"email": payload.email.strip()},
        ).fetchone()

    if not user or payload.password != str(user.user_id):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = secrets.token_urlsafe(32)

    return LoginResponse(
        token=token,
        user=LoginUser(
            user_id=user.user_id,
            user_name=user.user_name,
            email=user.email,
        ),
    )

# --- ML Prediction Endpoint ---
@app.post("/identify_tool")
async def identify_tool(file: UploadFile = File(...)):
    """
    Receives an image file, runs it through the loaded ML model, 
    and returns the predicted tool class and classification score.
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
            "score": score,
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
        result = conn.execute(text("SELECT tool_id, tool_name, tool_size, tool_type, current_status, total_quantity, available_quantity, consumed_quantity, trained FROM tools"))
        tools = []
        for row in result:
             tools.append({
                 "id": row.tool_id,
                 "name": row.tool_name,
                 "size": row.tool_size,
                 "type": row.tool_type,
                 "status": row.current_status,
                 "total_quantity": row.total_quantity,
                 "available_quantity": row.available_quantity,
                 "consumed_quantity": row.consumed_quantity,
                 "trained": True if (row.trained == 1 or str(row.trained) == '1') else False
             })
        return tools

@app.post("/tools")
async def create_tool(tool: ToolInput):
    """Add a new tool to the inventory"""
    engine = create_engine(TOOLS_DB_URL)
    with engine.connect() as conn:
        query = text("""
            INSERT INTO tools (tool_name, tool_size, tool_type, current_status, total_quantity, available_quantity, consumed_quantity, trained)
            VALUES (:name, :size, :type, :status, :total, :available, :consumed, :trained)
        """)
        conn.execute(query, {
            "name": tool.tool_name,
            "size": tool.tool_size,
            "type": tool.tool_type,
            "status": tool.current_status,
            "total": tool.total_quantity,
            "available": tool.available_quantity,
            "consumed": tool.consumed_quantity,
            "trained": tool.trained
        })
        conn.commit()
    return {"success": True, "message": "Tool created successfully"}

@app.put("/tools/{tool_id}")
async def update_tool(tool_id: int, tool: ToolUpdate):
    """Update fields of an existing tool"""
    engine = create_engine(TOOLS_DB_URL)
    with engine.connect() as conn:
        # Check if tool exists
        check = conn.execute(text("SELECT tool_id FROM tools WHERE tool_id = :id"), {"id": tool_id}).fetchone()
        if not check:
            raise HTTPException(status_code=404, detail="Tool not found")

        updates = []
        params = {"id": tool_id}
        
        if tool.tool_name is not None:
            updates.append("tool_name = :name")
            params["name"] = tool.tool_name
        if tool.tool_size is not None:
            updates.append("tool_size = :size")
            params["size"] = tool.tool_size
        if tool.tool_type is not None:
             updates.append("tool_type = :type")
             params["type"] = tool.tool_type
        if tool.current_status is not None:
             updates.append("current_status = :status")
             params["status"] = tool.current_status
        if tool.total_quantity is not None:
             updates.append("total_quantity = :total")
             params["total"] = tool.total_quantity
        if tool.available_quantity is not None:
             updates.append("available_quantity = :available")
             params["available"] = tool.available_quantity
        if tool.consumed_quantity is not None:
             updates.append("consumed_quantity = :consumed")
             params["consumed"] = tool.consumed_quantity
        if tool.trained is not None:
             updates.append("trained = :trained")
             params["trained"] = tool.trained
        
        if not updates:
             return {"success": True, "message": "No changes provided"}

        sql = f"UPDATE tools SET {', '.join(updates)} WHERE tool_id = :id"
        
        conn.execute(text(sql), params)
        conn.commit()
    
    return {"success": True, "message": "Tool updated successfully"}

# --- Transaction Management Endpoints ---

@app.get("/transactions")
async def get_transactions(
    user_id: Optional[int] = None, 
    page: int = 1, 
    limit: int = 50,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get transactions with pagination and date filtering"""
    offset = (page - 1) * limit
    engine = create_engine(TOOLS_DB_URL)
    with engine.connect() as conn:
        # Build base query conditions
        conditions = []
        params = {}
        
        if user_id is not None:
            conditions.append("t.user_id = :user_id")
            params["user_id"] = user_id
            
        if start_date:
            conditions.append("t.checkout_timestamp >= :start_date")
            params["start_date"] = start_date
            
        if end_date:
            # Add one day to end_date to include the full day
            conditions.append("t.checkout_timestamp < DATE_ADD(:end_date, INTERVAL 1 DAY)")
            params["end_date"] = end_date

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        # 1. Get Total Count
        count_sql = f"SELECT COUNT(*) FROM transactions t {where_clause}"
        total = conn.execute(text(count_sql), params).scalar()

        # 2. Get Data
        # Join with users and tools to get names
        base_sql = f"""
            SELECT t.transaction_id, t.user_id, t.tool_id, t.checkout_timestamp, 
                   t.desired_return_date, t.return_timestamp, t.quantity, t.purpose, 
                   t.image_path, t.classification_correct, t.weight,
                   u.user_name, tl.tool_name
            FROM transactions t
            LEFT JOIN users u ON t.user_id = u.user_id
            LEFT JOIN tools tl ON t.tool_id = tl.tool_id
            {where_clause}
            ORDER BY t.transaction_id DESC
        """
        
        if limit > 0:
            base_sql += " LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset
            
        result = conn.execute(text(base_sql), params)
        
        transactions = []
        for row in result:
            # Determine status
            status = "Borrowed"
            if row.return_timestamp:
                status = "Returned"
            elif row.desired_return_date and row.desired_return_date < datetime.now():
                status = "Overdue"
            
            transactions.append({
                "transaction_id": row.transaction_id,
                "user_id": row.user_id,
                "user_name": row.user_name,
                "tool_id": row.tool_id,
                "tool_name": row.tool_name,
                "checkout_timestamp": row.checkout_timestamp,
                "desired_return_date": row.desired_return_date,
                "return_timestamp": row.return_timestamp,
                "quantity": row.quantity,
                "purpose": row.purpose,
                "status": status
            })
            
        return {
            "items": transactions,
            "total": total,
            "page": page,
            "size": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }

@app.post("/transactions")
async def create_transaction(transaction: TransactionInput):
    """Create a new transaction"""
    engine = create_engine(TOOLS_DB_URL)
    with engine.connect() as conn:
        query = text("""
            INSERT INTO transactions
            (user_id, tool_id, desired_return_date, return_timestamp, quantity, purpose,
             image_path, classification_correct, weight)
            VALUES
            (:user_id, :tool_id, :desired_return_date, :return_timestamp, :quantity, :purpose,
             :image_path, :classification_correct, :weight)
        """)
        conn.execute(query, {
            "user_id": transaction.user_id,
            "tool_id": transaction.tool_id,
            "desired_return_date": transaction.desired_return_date,
            "return_timestamp": transaction.return_timestamp,
            "quantity": transaction.quantity,
            "purpose": transaction.purpose,
            "image_path": transaction.image_path,
            "classification_correct": transaction.classification_correct,
            "weight": transaction.weight,
        })
        conn.commit()

    return {"success": True, "message": "Transaction created successfully"}

@app.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: int):
    """Delete a transaction"""
    engine = create_engine(TOOLS_DB_URL)
    with engine.connect() as conn:
        check = conn.execute(
            text("SELECT transaction_id FROM transactions WHERE transaction_id = :id"),
            {"id": transaction_id},
        ).fetchone()
        if not check:
            raise HTTPException(status_code=404, detail="Transaction not found")

        conn.execute(
            text("DELETE FROM transactions WHERE transaction_id = :id"),
            {"id": transaction_id},
        )
        conn.commit()

    return {"success": True, "message": "Transaction deleted successfully"}

@app.put("/transactions/{transaction_id}")
async def update_transaction(transaction_id: int, transaction: TransactionUpdate):
    """Update fields of a transaction"""
    engine = create_engine(TOOLS_DB_URL)
    with engine.connect() as conn:
        check = conn.execute(
            text("SELECT transaction_id FROM transactions WHERE transaction_id = :id"),
            {"id": transaction_id},
        ).fetchone()
        if not check:
            raise HTTPException(status_code=404, detail="Transaction not found")

        updates = []
        params = {"id": transaction_id}

        if transaction.user_id is not None:
            updates.append("user_id = :user_id")
            params["user_id"] = transaction.user_id
        if transaction.tool_id is not None:
            updates.append("tool_id = :tool_id")
            params["tool_id"] = transaction.tool_id
        if transaction.desired_return_date is not None:
            updates.append("desired_return_date = :desired_return_date")
            params["desired_return_date"] = transaction.desired_return_date
        if transaction.return_timestamp is not None:
            updates.append("return_timestamp = :return_timestamp")
            params["return_timestamp"] = transaction.return_timestamp
        if transaction.quantity is not None:
            updates.append("quantity = :quantity")
            params["quantity"] = transaction.quantity
        if transaction.purpose is not None:
            updates.append("purpose = :purpose")
            params["purpose"] = transaction.purpose
        if transaction.image_path is not None:
            updates.append("image_path = :image_path")
            params["image_path"] = transaction.image_path
        if transaction.classification_correct is not None:
            updates.append("classification_correct = :classification_correct")
            params["classification_correct"] = transaction.classification_correct
        if transaction.weight is not None:
            updates.append("weight = :weight")
            params["weight"] = transaction.weight

        if not updates:
            return {"success": True, "message": "No changes provided"}

        sql = f"UPDATE transactions SET {', '.join(updates)} WHERE transaction_id = :id"
        conn.execute(text(sql), params)
        conn.commit()

    return {"success": True, "message": "Transaction updated successfully"}


# --- Analytics Endpoints ---

@app.get("/analytics/dashboard")
async def get_dashboard_analytics(period: str = "1_month"):
    """
    Get dashboard analytics.
    period options: '1_month', 'winter_2026', 'fall_2025', 'summer_2025', etc.
    """
    engine = create_engine(TOOLS_DB_URL)
    with engine.connect() as conn:
        # 1. Determine Date Range
        now = datetime.now()
        start_date = None
        end_date = now # Default end is now
        
        if period == "1_month":
            start_date = now - timedelta(days=30)
        elif period == "winter_2026":
            start_date = datetime(2026, 1, 1)
            end_date = datetime(2026, 4, 30, 23, 59, 59)
        elif period == "fall_2025":
            start_date = datetime(2025, 9, 1)
            end_date = datetime(2025, 12, 31, 23, 59, 59)
        elif period == "summer_2025":
            start_date = datetime(2025, 5, 1)
            end_date = datetime(2025, 8, 31, 23, 59, 59)
        elif period == "winter_2025":
            start_date = datetime(2025, 1, 1)
            end_date = datetime(2025, 4, 30, 23, 59, 59)
        else:
            # Fallback to 1 month
            start_date = now - timedelta(days=30)

        params = {"start_date": start_date, "end_date": end_date}
        
        # 2. Live Stats (Current State of System)
        total_tools = conn.execute(text("SELECT COUNT(*) FROM tools")).scalar()
        current_borrowed = conn.execute(
            text("SELECT COUNT(*) FROM transactions WHERE return_timestamp IS NULL")
        ).scalar()
        current_overdue = conn.execute(
            text("SELECT COUNT(*) FROM transactions WHERE return_timestamp IS NULL AND desired_return_date < NOW()")
        ).scalar()

        # 3. Period Stats (Activity within range)
        period_checkouts = conn.execute(
            text("SELECT COUNT(*) FROM transactions WHERE checkout_timestamp >= :start_date AND checkout_timestamp <= :end_date"),
            params
        ).scalar()

        # Top Tools in Period
        top_tools_result = conn.execute(
            text("""
                SELECT t.tool_name, COUNT(tr.tool_id) as usage_count
                FROM transactions tr
                JOIN tools t ON tr.tool_id = t.tool_id
                WHERE tr.checkout_timestamp >= :start_date AND tr.checkout_timestamp <= :end_date
                GROUP BY tr.tool_id, t.tool_name
                ORDER BY usage_count DESC
                LIMIT 10
            """),
            params
        ).fetchall()
        
        top_tools = [{"name": row.tool_name, "uses": row.usage_count} for row in top_tools_result]

        return {
            "live_stats": {
                "total_tools": total_tools,
                "current_borrowed": current_borrowed,
                "current_overdue": current_overdue,
            },
            "period_stats": {
                "checkouts": period_checkouts,
                "top_tools": top_tools,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=5000)

