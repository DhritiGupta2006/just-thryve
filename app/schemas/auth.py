from typing import Optional
from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str  # borrower | lender
    business_name: Optional[str] = None
    sector: Optional[str] = None  # renewable_energy, agriculture, commerce


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    user_id: str
    token: str
    role: str
