# app/routers/early_access.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.services.email_service import send_email
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class EarlyAccessRequest(BaseModel):
    email: EmailStr


@router.post("/signup")
async def early_access_signup(request: EarlyAccessRequest):
    email = request.email

    try:
        # Send confirmation to user
        await send_email(
            to_email=email,
            subject="You're on the Tinko Early Access List 🎉",
            text="Welcome to Tinko Early Access!",
            html=f"""
                <h2>Welcome to Tinko Early Access 🎉</h2>
                <p>You’re officially on the early-access waitlist for Tinko.</p>
                <p>We’ll notify you as soon as beta opens.</p>
                <br>
                <p>— Team Tinko</p>
            """
        )

        # Notify admin
        await send_email(
            to_email="founder@tinko.in",
            subject="New Early Access Signup",
            text=f"New signup: {email}",
            html=f"<h3>New Signup</h3><p>Email: {email}</p>"
        )

        return {"message": "Early access signup successful", "email": email}

    except Exception as e:
        logger.error(f"Early access failed: {e}")
        raise HTTPException(500, f"Early access signup failed: {e}")
