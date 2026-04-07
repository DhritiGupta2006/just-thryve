from datetime import datetime
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


class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str
    role: str
    kyc_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    business_name: Optional[str] = None
    sector: Optional[str] = None
