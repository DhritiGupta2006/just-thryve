from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.business_profile import BusinessProfile
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserResponse, ProfileUpdateRequest
from app.services.auth_service import AuthService, get_current_user

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


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        user_id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        kyc_verified=current_user.kyc_verified,
        created_at=current_user.created_at,
    )


@router.put("/profile", response_model=UserResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.name is not None:
        current_user.name = payload.name

    if payload.business_name is not None or payload.sector is not None:
        profile = (
            db.query(BusinessProfile)
            .filter(BusinessProfile.user_id == current_user.id)
            .first()
        )
        if profile:
            if payload.business_name is not None:
                profile.business_name = payload.business_name
            if payload.sector is not None:
                if payload.sector not in VALID_SECTORS:
                    raise HTTPException(
                        status_code=400,
                        detail=f"sector must be one of {VALID_SECTORS}",
                    )
                profile.sector = payload.sector

    db.commit()
    db.refresh(current_user)

    return UserResponse(
        user_id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        kyc_verified=current_user.kyc_verified,
        created_at=current_user.created_at,
    )


@router.post("/kyc/verify", response_model=UserResponse)
def verify_kyc(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark the current user's KYC as verified.

    In production this would integrate with a KYC provider (e.g. DigiLocker/Aadhaar).
    Here it simulates a successful KYC verification for the authenticated user.
    """
    if current_user.kyc_verified:
        raise HTTPException(status_code=400, detail="KYC is already verified")

    current_user.kyc_verified = True
    db.commit()
    db.refresh(current_user)

    return UserResponse(
        user_id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        kyc_verified=current_user.kyc_verified,
        created_at=current_user.created_at,
    )

