# app/routers/email_auth.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.services.email_service import send_email_otp
from app.services.auth_service import generate_otp
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class OTPRequest(BaseModel):
    email: EmailStr


@router.post("/send-otp")
async def send_otp_email(request: OTPRequest):
    try:
        email = request.email
        otp = generate_otp()

        logger.info(f"🔐 Sending OTP to {email}: {otp}")

        await send_email_otp(email, otp)

        return {"message": "OTP sent successfully", "email": email}

    except Exception as e:
        logger.error(f"❌ OTP sending failed: {e}")
        raise HTTPException(400, str(e))
