from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Organization, User
from app.deps import get_current_user
from app.services.oauth_service import oauth_service
from pydantic import BaseModel

router = APIRouter(tags=["Gateways"])

class ManualGatewayConfig(BaseModel):
    gateway: str
    key_id: str
    key_secret: str

@router.get("/connect/{provider}")
def connect_gateway(provider: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Initiates the OAuth flow for a provider (e.g., razorpay).
    Redirects the user to the provider's authorization page.
    """
    if provider != "razorpay":
        raise HTTPException(status_code=400, detail="Only Razorpay is supported for OAuth currently.")
    
    # Ensure user has an organization
    if not current_user.org_id:
        raise HTTPException(status_code=400, detail="User does not belong to an organization.")

    auth_url = oauth_service.get_razorpay_auth_url(current_user.org_id)
    return {"redirect_url": auth_url}

@router.get("/callback/{provider}")
def gateway_callback(provider: str, code: str, state: str, db: Session = Depends(get_db)):
    """
    Handles the OAuth callback.
    Exchanges the code for an access token and updates the organization.
    """
    if provider != "razorpay":
        raise HTTPException(status_code=400, detail="Invalid provider.")

    # Extract org_id from state (format: org_id_randomstring)
    try:
        org_id = int(state.split("_")[0])
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="Invalid state parameter.")

    # Exchange token
    try:
        token_data = oauth_service.exchange_razorpay_token(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {str(e)}")

    # 3. Create Webhook (Automated)
    try:
        if provider == "razorpay":
            oauth_service.create_razorpay_webhook(org_id, token_data["access_token"])
        elif provider == "stripe":
            oauth_service.create_stripe_webhook(org_id, token_data["access_token"])
    except Exception as e:
        print(f"Warning: Failed to auto-create webhook: {e}")

    # Update Organization
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found.")

    # Update credentials
    creds = org.gateway_credentials or {}
    creds[provider] = {
        "auth_type": "oauth",
        "access_token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "expires_in": token_data.get("expires_in"),
        "token_type": token_data.get("token_type")
    }
    
    # Add to payment_gateways list if not present
    gateways = org.payment_gateways or []
    if provider not in gateways:
        gateways.append(provider)
        org.payment_gateways = gateways

    org.gateway_credentials = creds
    db.commit()

    # Redirect to frontend success page (or close popup)
    # For now, we return a simple HTML success message
    return {"status": "success", "message": f"Connected to {provider} successfully!"}

@router.post("/verify")
def verify_manual_gateway(config: ManualGatewayConfig, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Verifies and saves manually entered API keys.
    """
    if not current_user.org_id:
        raise HTTPException(status_code=400, detail="User does not belong to an organization.")

    # TODO: Implement actual ping/verification logic here based on gateway type
    # For now, we assume keys are valid if they are not empty
    if not config.key_id or not config.key_secret:
        raise HTTPException(status_code=400, detail="Invalid credentials.")

    org = db.query(Organization).filter(Organization.id == current_user.org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found.")

    creds = org.gateway_credentials or {}
    creds[config.gateway.lower()] = {
        "auth_type": "manual",
        "key_id": config.key_id,
        "key_secret": config.key_secret # In prod, encrypt this!
    }

    gateways = org.payment_gateways or []
    gw_name = config.gateway.lower()
    if gw_name not in gateways:
        gateways.append(gw_name)
        org.payment_gateways = gateways

    org.gateway_credentials = creds
    db.commit()

    return {"status": "success", "message": f"Connected to {config.gateway} successfully!"}
