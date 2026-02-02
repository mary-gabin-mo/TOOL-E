from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.models import UserRequest, ServerResponse, LoginPayload, LoginResponse, LoginUser
from app.database import engine_users, engine_tools
import secrets
from datetime import date, timedelta

router = APIRouter()

@router.post("/validate_user", response_model=ServerResponse)
async def validate_user_route(request: UserRequest):
    with engine_users.connect() as conn:
        print(f"[SERVER] Checking User Database...")

        if request.UCID:
            print(f"[SERVER] Validating UserID: {request.UCID}")
            sql_query = text(f"SELECT FirstName, UCID, UNICARDBarcode, recordDate FROM MakerspaceCapstone WHERE UCID = :ucid ")
            user = conn.execute(sql_query,{"ucid": int(request.UCID)}).fetchone()
        
        elif request.barcode:
            print(f"[SERVER] Validating UserID: {request.barcode}")
            sql_query = text("SELECT FirstName, UCID, UNICARDBarcode, recordDate FROM MakerspaceCapstone WHERE UNICARDBarcode = :barcode")
            barcode_input = f"{request.barcode};" 
            user = conn.execute(sql_query, {"barcode": barcode_input}).fetchone()
        
        else:
             return ServerResponse(success=False, message="No ID provided")

        if not user:
            return ServerResponse(success=False, message="User not found in database")
        
        first_name = user[0]                
        waiver_date = user[3]        

        # Check waiver (recordDate) - must be within 365 days
        one_year_ago = date.today() - timedelta(days=365)
            
        if waiver_date is None or waiver_date < one_year_ago:
            return ServerResponse(success=False, message="Waiver is expired, please renew")
        
        return ServerResponse(success=True, message=f"Access Granted, {first_name}")

@router.post("/api/auth/login", response_model=LoginResponse)
async def login(payload: LoginPayload):
    with engine_tools.connect() as conn:
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
