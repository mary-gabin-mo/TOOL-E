from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import uvicorn
import os
from dotenv import load_dotenv
from datetime import date, timedelta

load_dotenv('.env.local')

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
                 "trained": bool(row.trained)
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

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=5000)
        
    