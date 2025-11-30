import os
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from dotenv import load_dotenv

load_dotenv()

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

if not SUPABASE_JWT_SECRET:
    raise RuntimeError("SUPABASE_JWT_SECRET missing in .env")

security = HTTPBearer()


def verify_jwt(token: str):
    """
    Validates a Supabase JWT token using the project's JWT secret.
    """
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(payload: dict = Depends(security)):
    """
    Extracts user information from validated JWT token.
    """
    token = payload.credentials
    decoded = verify_jwt(token)

    user_id = decoded.get("sub")
    email = decoded.get("email")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: missing sub")

    return {"user_id": user_id, "email": email}


def get_current_user_id(user=Depends(get_current_user)):
    return user["user_id"]


def get_current_user_email(user=Depends(get_current_user)):
    return user["email"]
