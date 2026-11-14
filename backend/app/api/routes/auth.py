"""
Cyber Raksha AI - User Registration, Authentication & Verification Routes
Supports mobile OTP verification, email confirmation, secure PBKDF2 hashing, and profile management.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    MobileOtpRequest,
    MobileOtpVerifyRequest,
    TokenResponse,
    UserProfileResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest
)
from app.core.auth_utils import (
    hash_password,
    verify_password,
    create_access_token,
    verify_access_token,
    generate_verification_token
)
from app.services.otp_service import otp_service, normalize_indian_mobile
from app.services.email_service import email_service

router = APIRouter(prefix="/auth", tags=["User Authentication & Verification"])


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency that extracts and validates Bearer token to return the current authenticated User."""
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    elif request.headers.get("X-User-Token"):
        token = request.headers.get("X-User-Token").strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required. Provide 'Authorization: Bearer <token>'."
        )

    payload = verify_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token."
        )

    user_id = payload["sub"]
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or deactivated."
        )

    return user


def get_optional_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    try:
        return get_current_user(request, db)
    except HTTPException:
        return None


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(req: UserRegisterRequest, db: Session = Depends(get_db)):
    """Registers a new user account with hashed password and initial unverified state."""
    # Check if email exists
    if db.query(User).filter(User.email == req.email.lower()).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )
    # Check if username exists
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken."
        )

    normalized_mobile = None
    if req.mobile_number:
        normalized_mobile = normalize_indian_mobile(req.mobile_number)
        if not normalized_mobile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid mobile number format. Must be a valid 10-digit Indian number (+91)."
            )

    email_token = generate_verification_token()
    now = datetime.now(timezone.utc)

    user = User(
        email=req.email.lower(),
        username=req.username,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        mobile_number=normalized_mobile,
        is_mobile_verified=False,
        is_email_verified=False,
        email_verification_token=email_token,
        email_token_expires_at=now + timedelta(days=2),
        consent_given=req.consent_given,
        consent_timestamp=now if req.consent_given else None,
        role="citizen",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Dispatch verification email
    email_service.send_verification_email(user.email, email_token, user.full_name)

    token = create_access_token({"sub": user.id, "username": user.username, "role": user.role})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        email=user.email,
        mobile_number=user.mobile_number,
        is_mobile_verified=user.is_mobile_verified,
        is_email_verified=user.is_email_verified,
        role=user.role
    )


@router.post("/login", response_model=TokenResponse)
def login_user(req: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticates using email, username, or mobile number + password."""
    ident = req.identifier.strip()
    user = None

    # Try email
    if "@" in ident:
        user = db.query(User).filter(User.email == ident.lower()).first()
    # Try normalized mobile
    if not user:
        norm_mobile = normalize_indian_mobile(ident)
        if norm_mobile:
            user = db.query(User).filter(User.mobile_number == norm_mobile).first()
    # Try username
    if not user:
        user = db.query(User).filter(User.username == ident).first()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Check username/email/mobile and password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact Cyber Raksha support."
        )

    token = create_access_token({"sub": user.id, "username": user.username, "role": user.role})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        email=user.email,
        mobile_number=user.mobile_number,
        is_mobile_verified=user.is_mobile_verified,
        is_email_verified=user.is_email_verified,
        role=user.role
    )


@router.post("/send-mobile-otp")
def send_mobile_otp(
    req: MobileOtpRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generates and delivers a 6-digit cryptographic OTP to verify the user's Indian mobile number."""
    result = otp_service.request_otp(db, current_user, req.mobile_number)
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])
    return {
        "status": "SUCCESS",
        "message": result["message"],
        "masked_mobile": result["masked_mobile"],
        "telecom_delivered": result["telecom_delivered"],
        "delivery_channel": result["delivery_channel"],
        "delivery_detail": result["delivery_detail"]
    }


@router.post("/verify-mobile-otp")
def verify_mobile_otp(
    req: MobileOtpVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verifies the 6-digit mobile OTP."""
    success, message = otp_service.verify_otp(db, current_user, req.otp)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return {"status": "VERIFIED", "message": message, "is_mobile_verified": True}


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    """Verifies user email address via token link."""
    user = db.query(User).filter(User.email_verification_token == token).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token.")

    now = datetime.now(timezone.utc)
    if user.email_token_expires_at:
        exp = user.email_token_expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if now > exp:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification link has expired.")

    user.is_email_verified = True
    user.email_verification_token = None
    user.email_token_expires_at = None
    db.commit()

    return {"status": "VERIFIED", "message": "Email address successfully verified. Your account is fully active."}


@router.get("/me", response_model=UserProfileResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    """Returns the authenticated user profile."""
    return UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        mobile_number=current_user.mobile_number,
        is_mobile_verified=current_user.is_mobile_verified,
        is_email_verified=current_user.is_email_verified,
        consent_given=current_user.consent_given,
        role=current_user.role,
        created_at=current_user.created_at.isoformat()
    )


@router.delete("/account")
def delete_user_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Data governance: User-initiated complete account and private data deletion."""
    db.delete(current_user)
    db.commit()
    return {"status": "DELETED", "message": "Your account and associated profile records have been permanently removed."}

