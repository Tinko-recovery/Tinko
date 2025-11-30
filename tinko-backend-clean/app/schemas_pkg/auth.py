from pydantic import BaseModel, EmailStr

class SendOTPRequest(BaseModel):
    email: EmailStr
    intent: str = "login"  # "login" or "signup"

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class OTPResponse(BaseModel):
    message: str
    email: EmailStr
    verified: bool = False
