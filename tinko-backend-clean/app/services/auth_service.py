import os
import random
import time
from fastapi import HTTPException
from jose import jwt, JWTError

# ===============================
# JWT CONFIG
# ===============================
JWT_SECRET = os.getenv("JWT_SECRET", "localdevsecret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# ===============================
# IN-MEMORY OTP STORE (LOCAL TESTING)
# ===============================
# For production you will replace this with DB or Redis
OTP_STORE = {}  # { email: { "otp": "1234", "expires": 1234567890 } }


# ===============================
# JWT VERIFY
# ===============================
def verify_access_token(token: str):
    """
    Decodes JWT access token and returns payload.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ===============================
# OTP GENERATION
# ===============================
def generate_otp():
    """Generate 6-digit numeric OTP."""
    return str(random.randint(100000, 999999))


# ===============================
# SAVE OTP
# ===============================
def save_otp(email: str, otp: str):
    """Save OTP to in-memory store with 5-minute expiry."""
    OTP_STORE[email] = {
        "otp": otp,
        "expires": time.time() + 300  # 5 minutes
    }


# ===============================
# VALIDATE OTP
# ===============================
def validate_otp(email: str, otp: str):
    """
    Validates OTP entered by user.
    """
    if email not in OTP_STORE:
        raise HTTPException(status_code=400, detail="OTP not found")

    record = OTP_STORE[email]

    if time.time() > record["expires"]:
        raise HTTPException(status_code=400, detail="OTP expired")

    if otp != record["otp"]:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # OTP is valid → cleanup
    del OTP_STORE[email]
    return True
