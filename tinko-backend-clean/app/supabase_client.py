import os
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

AUTH_URL = f"{SUPABASE_URL}/auth/v1"


def send_otp(email: str):
    """
    Sends a 6-digit email OTP using Supabase native auth.
    """
    url = f"{AUTH_URL}/otp"

    payload = {
        "email": email,
        "create_user": True,
        "type": "email"
    }

    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json"
    }

    r = requests.post(url, json=payload, headers=headers)

    if r.status_code >= 400:
        raise Exception(f"Send OTP failed: {r.text}")

    return {"message": "OTP sent"}


def verify_otp(email: str, otp: str):
    """
    Verifies the OTP and returns Supabase access token.
    """
    url = f"{AUTH_URL}/token?grant_type=otp"

    payload = {
        "email": email,
        "token": otp,
        "type": "email"
    }

    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json"
    }

    r = requests.post(url, json=payload, headers=headers)

    if r.status_code >= 400:
        raise Exception(f"Verify OTP failed: {r.text}")

    return r.json()   # contains access_token, refresh_token, user
