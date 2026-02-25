from pydantic import BaseModel
from typing import Optional, Dict

# --- Auth Models ---
class UserRequest(BaseModel):
    UCID: Optional[int] = None   
    barcode: Optional[str] = None

class ServerResponse(BaseModel):
    success: bool
    message: str

class UserDetails(BaseModel):
    first_name: str
    last_name: str
    ucid: int
    email: str

class ValidateUserResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    user: Optional[UserDetails] = None

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

class TransactionBatchInput(BaseModel):
    transactions: list[TransactionInput]
