from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.business_profile import BusinessProfile
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

VALID_ROLES = {"borrower", "lender"}
VALID_SECTORS = {"renewable_energy", "agriculture", "commerce"}


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    if payload.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"role must be one of {VALID_ROLES}")

    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=payload.email,
        password_hash=AuthService.hash_password(payload.password),
        name=payload.name,
        role=payload.role,
        kyc_verified=False,
    )
    db.add(user)
    db.flush()  # get user.id before creating business profile

    if payload.role == "borrower" and payload.business_name:
        sector = payload.sector or "commerce"
        if sector not in VALID_SECTORS:
            raise HTTPException(status_code=400, detail=f"sector must be one of {VALID_SECTORS}")
        profile = BusinessProfile(
            user_id=user.id,
            business_name=payload.business_name,
            sector=sector,
        )
        db.add(profile)

    db.commit()
    db.refresh(user)

    token = AuthService.create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(user_id=str(user.id), token=token, role=user.role)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not AuthService.verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = AuthService.create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(user_id=str(user.id), token=token, role=user.role)
