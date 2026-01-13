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

    