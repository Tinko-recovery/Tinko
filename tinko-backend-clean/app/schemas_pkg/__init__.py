# app/schemas_pkg/__init__.py

# OTP-related schemas
from .auth import (
    SendOTPRequest,
    VerifyOTPRequest,
    OTPResponse,
)

# Recovery schemas
from .recoveries import (
    RecoveryLinkRequest,
    RecoveryLinkOut,
    RecoveryAttemptOut,
    RecoveryAttemptsResponse,
)

# Onboarding schemas (ALL)
from .onboarding import (
    GatewaySelectRequest,
    GatewaySelectResponse,
    OnboardingStartRequest,
    OnboardingStartResponse,
    OnboardingCompleteRequest,
    OnboardingCompleteResponse,
)

__all__ = [
    # OTP
    "SendOTPRequest",
    "VerifyOTPRequest",
    "OTPResponse",

    # Recoveries
    "RecoveryLinkRequest",
    "RecoveryLinkOut",
    "RecoveryAttemptOut",
    "RecoveryAttemptsResponse",

    # Onboarding
    "GatewaySelectRequest",
    "GatewaySelectResponse",
    "OnboardingStartRequest",
    "OnboardingStartResponse",
    "OnboardingCompleteRequest",
    "OnboardingCompleteResponse",
]
