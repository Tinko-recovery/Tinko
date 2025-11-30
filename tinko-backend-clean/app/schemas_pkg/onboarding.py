from pydantic import BaseModel, Field
from typing import Optional



# -------------------------
# 1. User selects gateway
# -------------------------
class GatewaySelectRequest(BaseModel):
    gateway: str = Field(..., pattern="^(razorpay|stripe)$")


class GatewaySelectResponse(BaseModel):
    message: str
    next: str  # next step URL or string identifier


# -------------------------
# 2. Onboarding start
# -------------------------
class OnboardingStartRequest(BaseModel):
    email: str
    business_name: str
    website_url: Optional[str] = None


class OnboardingStartResponse(BaseModel):
    onboarding_id: str
    message: str
    next: str  # e.g. "/v1/onboarding/select-gateway"


# -------------------------
# 3. Onboarding complete
# -------------------------
class OnboardingCompleteRequest(BaseModel):
    onboarding_id: str
    gateway: str
    api_key: str
    api_secret: str


class OnboardingCompleteResponse(BaseModel):
    message: str
    dashboard_url: str
