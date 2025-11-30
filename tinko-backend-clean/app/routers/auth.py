# app/routers/auth.py

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta
from jose import jwt
import os

from sqlalchemy.orm import Session

from app.schemas_pkg.auth import SendOTPRequest, VerifyOTPRequest, OTPResponse
from app.services.auth_service import generate_otp, save_otp, validate_otp
from app.services.email_service import send_email_otp
from app.deps import get_db
from app.models import User

# ⚠ main.py already mounts this with prefix="/v1/auth"
router = APIRouter(tags=["Auth"])

JWT_SECRET = os.getenv("JWT_SECRET", "localdevsecret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", 1440))  # 24 hrs


# -------------------------------------------
# Send OTP
# -------------------------------------------
@router.post("/email/send-otp", response_model=OTPResponse)
async def send_otp_route(
    request: SendOTPRequest,
    db: Session = Depends(get_db)
):
    # Check if user exists
    user = db.query(User).filter(User.email == request.email).first()

    if request.intent == "signup":
        if user:
            raise HTTPException(status_code=409, detail="Account already exists. Please login.")
    elif request.intent == "login":
        if not user:
            raise HTTPException(status_code=404, detail="Account not found. Please sign up.")
    
    otp = generate_otp()
    save_otp(request.email, otp)

    await send_email_otp(request.email, otp)

    return OTPResponse(
        message="OTP sent successfully",
        email=request.email,
        verified=False,
    )


# -------------------------------------------
# Verify OTP + Generate JWT + Detect New User
# -------------------------------------------
@router.post("/email/verify-otp")
async def verify_otp_route(
    request: VerifyOTPRequest,
    db: Session = Depends(get_db),
):
    # 1) OTP check
    if not validate_otp(request.email, request.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    # 2) Check if user already exists
    user = db.query(User).filter(User.email == request.email).first()
    is_new_user = False

    if not user:
        # First-time login → create minimal user
        is_new_user = True
        user = User(email=request.email)
        db.add(user)
        db.commit()
        db.refresh(user)

        # 🔜 Next step: here we can trigger:
        # - admin notification email
        # - user welcome email

    # 3) Generate JWT
    payload = {
        "sub": request.email,
        "email": request.email,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRY_MINUTES),
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # 4) Return token + new_user flag
    return {
        "access_token": token,
        "token_type": "bearer",
        "email": request.email,
        "new_user": is_new_user,
    }
