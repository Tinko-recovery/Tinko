# app/supabase_http.py

import httpx
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

AUTH_URL = f"{SUPABASE_URL}/auth/v1"

headers = {
    "apikey": SUPABASE_ANON_KEY,
    "Content-Type": "application/json"
}


async def send_otp(email: str):
    """
    Send OTP using Supabase email OTP flow.
    """
    payload = {
        "email": email,
        "create_user": True   # Auto-create user on first login
    }

    async with httpx.AsyncClient() as client:
        res = await client.post(f"{AUTH_URL}/otp", json=payload, headers=headers)

    if res.status_code != 200:
        raise Exception(f"Send OTP failed: {res.text}")

    return {"message": "OTP sent to email", "email": email}


async def verify_otp(email: str, otp: str):
    """
    Verify OTP and return access token from Supabase.
    """
    payload = {
        "email": email,
        "token": otp,
        "type": "email"
    }

    async with httpx.AsyncClient() as client:
        res = await client.post(f"{AUTH_URL}/verify", json=payload, headers=headers)

    if res.status_code != 200:
        raise Exception(f"Verify OTP failed: {res.text}")

    data = res.json()

    # Return tokens so frontend can store session
    return {
        "access_token": data.get("access_token"),
        "refresh_token": data.get("refresh_token"),
        "expires_in": data.get("expires_in"),
        "token_type": data.get("token_type", "bearer")
    }
