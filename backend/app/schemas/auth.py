"""
Cyber Raksha AI - Authentication & User Account Schemas
"""
from typing import Optional
from pydantic import BaseModel, Field


class UserRegisterRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", description="Valid email address")
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = None
    mobile_number: Optional[str] = None
    consent_given: bool = True


class UserLoginRequest(BaseModel):
    # Allows login with either username/email OR mobile number
    identifier: str = Field(..., description="Email, username, or Indian mobile number")
    password: str


class MobileOtpRequest(BaseModel):
    mobile_number: str = Field(..., description="10-digit Indian mobile number (+91)")


class MobileOtpVerifyRequest(BaseModel):
    otp: str = Field(..., min_length=4, max_length=10)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    email: str
    mobile_number: Optional[str] = None
    is_mobile_verified: bool
    is_email_verified: bool
    role: str


class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    mobile_number: Optional[str] = None
    is_mobile_verified: bool
    is_email_verified: bool
    consent_given: bool
    role: str
    created_at: str


class ForgotPasswordRequest(BaseModel):
    email_or_mobile: str


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str = Field(..., min_length=8)
