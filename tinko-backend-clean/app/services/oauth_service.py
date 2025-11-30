import os
import secrets
import requests
from urllib.parse import urlencode

# Placeholder for Razorpay OAuth URLs (Mocked for now)
RAZORPAY_AUTH_URL = "https://auth.razorpay.com/authorize"
RAZORPAY_TOKEN_URL = "https://auth.razorpay.com/token"

class OAuthService:
    def __init__(self):
        # In a real scenario, these would come from os.environ
        # For now, we use placeholders or expect them to be set later
        self.client_id = os.getenv("RAZORPAY_CLIENT_ID", "rzp_test_partner_mock")
        self.client_secret = os.getenv("RAZORPAY_CLIENT_SECRET", "mock_secret")
        self.redirect_uri = os.getenv("RAZORPAY_REDIRECT_URI", "http://localhost:8000/gateways/callback/razorpay")

    def get_razorpay_auth_url(self, org_id: int) -> str:
        """
        Generates the Razorpay OAuth redirect URL.
        State parameter is used to pass the org_id securely.
        """
        state = f"{org_id}_{secrets.token_urlsafe(8)}"
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "read_only", # Adjust scope as needed
            "state": state
        }
        return f"{RAZORPAY_AUTH_URL}?{urlencode(params)}"

    def exchange_razorpay_token(self, code: str) -> dict:
        """
        Exchanges the authorization code for an access token.
        """
        # MOCK IMPLEMENTATION FOR DEVELOPMENT
        if self.client_id == "rzp_test_partner_mock":
            return {
                "access_token": f"mock_access_token_{secrets.token_urlsafe(16)}",
                "refresh_token": f"mock_refresh_token_{secrets.token_urlsafe(16)}",
                "expires_in": 31536000, # 1 year
                "token_type": "Bearer"
            }

        # Real Implementation
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        response = requests.post(RAZORPAY_TOKEN_URL, data=payload)
        response.raise_for_status()
        return response.json()

    def create_razorpay_webhook(self, org_id: str, access_token: str):
        """
        MOCK: Creates a webhook on Razorpay for the connected account.
        In production, this would POST to https://api.razorpay.com/v1/webhooks
        """
        print(f"[Mock] Creating Razorpay Webhook for Org {org_id} using token {access_token[:5]}...")
        # Simulate API call
        return {"id": "wh_mock_123", "url": "https://api.tinko.in/webhook/wh_123456789"}

    def create_stripe_webhook(self, org_id: str, access_token: str):
        """
        MOCK: Creates a webhook on Stripe for the connected account.
        In production, this would POST to https://api.stripe.com/v1/webhook_endpoints
        """
        print(f"[Mock] Creating Stripe Webhook for Org {org_id} using token {access_token[:5]}...")
        # Simulate API call
        return {"id": "we_mock_456", "url": "https://api.tinko.in/webhook/wh_123456789"}

oauth_service = OAuthService()
