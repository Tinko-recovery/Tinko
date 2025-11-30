# app/routers/profile.py
from fastapi import APIRouter, Depends
from app.supabase_jwt import get_current_user_email

router = APIRouter(tags=["Profile"])


@router.get("/me")
async def get_me(email: str = Depends(get_current_user_email)):
    """
    Simple test endpoint to verify Supabase JWT integration.
    Requires Authorization: Bearer <access_token>.
    """
    return {
        "email": email,
        "message": "Supabase JWT verified. This is the logged-in user.",
    }
