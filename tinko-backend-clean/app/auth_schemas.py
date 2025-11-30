# app/auth_schemas.py

from pydantic import BaseModel, EmailStr, constr
from typing import Optional, List


class UserCreateWithPassword(BaseModel):
    email: EmailStr
    password: constr(min_length=6)
    full_name: Optional[str] = None
    org_name: Optional[str] = None
    org_slug: Optional[str] = None
    account_type: Optional[str] = "user"


class UserLogin(BaseModel):
    email: EmailStr
    password: constr(min_length=6)


class SendOTPRequest(BaseModel):
    email: EmailStr


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: constr(min_length=6, max_length=6)


class OTPResponse(BaseModel):
    message: str
    success: bool
    details: Optional[dict] = None


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    role: Optional[str]
    org_id: Optional[int]
    account_type: Optional[str]
    is_active: bool
    is_email_verified: bool

    class Config:
        from_attributes = True  # Updated for Pydantic v2 (use orm_mode = True for v1)


class OrganizationResponse(BaseModel):
    id: int
    name: str
    slug: str
    is_active: bool

    class Config:
        from_attributes = True  # Updated for Pydantic v2 (use orm_mode = True for v1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
    organization: Optional[OrganizationResponse] = None


class ApiKeyCreate(BaseModel):
    key_name: str
    scopes: List[str]
    expires_in_days: Optional[int] = None


class ApiKeyResponse(BaseModel):
    id: int
    key_name: str
    key_prefix: str
    scopes: List[str]
    expires_at: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class ApiKeyCreateResponse(BaseModel):
    api_key: str
    key_info: ApiKeyResponse
