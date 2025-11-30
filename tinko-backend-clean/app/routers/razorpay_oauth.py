from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse, JSONResponse
import httpx
import secrets
from app.config.settings import settings
from typing import Optional

router = APIRouter(
    prefix="/v1/razorpay",
    tags=["razorpay"]
)

# Razorpay OAuth Endpoints
AUTHORIZE_URL = "https://auth.razorpay.com/authorize"
TOKEN_URL = "https://auth.razorpay.com/token"

@router.get("/authorize")
async def authorize_razorpay(request: Request):
    """
    Redirects the user to Razorpay's OAuth authorization page.
    """
    if not settings.RAZORPAY_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Razorpay Client ID is not configured."
        )

    # Generate a random state string for security (CSRF protection)
    # In a production app, store this in a secure cookie or session
    state = secrets.token_urlsafe(16)
    
    # Construct the authorization URL
    params = {
        "response_type": "code",
        "client_id": settings.RAZORPAY_CLIENT_ID,
        "redirect_uri": settings.RAZORPAY_REDIRECT_URI,
        "scope": "read_write", # Adjust scope as needed
        "state": state
    }
    
    # Build query string
    query_string = "&".join([f"{key}={value}" for key, value in params.items()])
    redirect_url = f"{AUTHORIZE_URL}?{query_string}"
    
    return RedirectResponse(url=redirect_url)


@router.get("/callback")
async def razorpay_callback(request: Request, code: str, state: str, error: Optional[str] = None):
    """
    Handles the callback from Razorpay after user authorization.
    Exchanges the authorization code for an access token.
    """
    if error:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": error, "detail": "Authorization failed or was denied by user."}
        )
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code missing."
        )

    # In a real app, verify the 'state' parameter here against what was stored

    if not settings.RAZORPAY_CLIENT_ID or not settings.RAZORPAY_CLIENT_SECRET:
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Razorpay credentials are not configured."
        )

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.RAZORPAY_REDIRECT_URI,
                    "client_id": settings.RAZORPAY_CLIENT_ID,
                    "client_secret": settings.RAZORPAY_CLIENT_SECRET
                }
            )
            response.raise_for_status()
            token_data = response.json()
            
            # Here you would typically:
            # 1. Identify the user (e.g., via session or a temporary token passed in state)
            # 2. Store the access_token, refresh_token, and razorpay_account_id in your DB
            # 3. Link it to the user's organization
            
            # For now, we'll just redirect to the dashboard with a success parameter
            # In a real flow, you might redirect to a specific onboarding step
            
            # Mocking success redirect to dashboard
            dashboard_url = "http://localhost:8000/dashboard/dashboard-preview.html?razorpay_connected=true" 
            # Note: In production, this should point to the actual frontend URL
            
            return RedirectResponse(url=dashboard_url)

        except httpx.HTTPStatusError as e:
            return JSONResponse(
                status_code=e.response.status_code,
                content={"detail": "Failed to exchange token with Razorpay", "error": e.response.text}
            )
        except Exception as e:
             return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "An error occurred during token exchange", "error": str(e)}
            )
