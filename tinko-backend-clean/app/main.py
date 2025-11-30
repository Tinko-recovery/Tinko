# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# ---------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ---------------------------------------------
load_dotenv()

# ---------------------------------------------
# IMPORT ROUTERS
# ---------------------------------------------
from app.routers import (
    health,
    auth,
    customer_api,
    payments,
    payments_razorpay,
    stripe_payments,
    razorpay_webhooks,
    webhooks_stripe,
    recoveries,
    recovery_links,
    retry,
    retry_policies,
    events,
    analytics,
    schedule,
    recon,
    maintenance,
    profile,
    classifier,
    dev,
    admin_db,
    early_access,

    # NEW ONBOARDING ROUTERS
    onboarding,
    onboarding_credentials,
    onboarding_finish,
    gateways,
    pay,
    razorpay_oauth,
)

# ---------------------------------------------
# APP INIT
# ---------------------------------------------
app = FastAPI(
    title="Tinko Backend API",
    version="1.0.0",
)

# ---------------------------------------------
# CORS
# ---------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------------------------------------
# ROUTERS
# ---------------------------------------------

# Health
app.include_router(health.router, prefix="/health", tags=["Health"])

# Auth
app.include_router(auth.router, prefix="/v1/auth", tags=["Auth"])

# Customer API
app.include_router(customer_api.router, prefix="/v1/customer", tags=["Customer"])

# Payments
# Payments
app.include_router(payments.router, prefix="/v1/payments", tags=["Payments"])
app.include_router(payments_razorpay.router, prefix="/v1/payments/razorpay", tags=["Razorpay"])
app.include_router(stripe_payments.router, prefix="/v1/payments/stripe", tags=["Stripe"])

# Webhooks
app.include_router(razorpay_webhooks.router, prefix="/v1/webhooks/razorpay", tags=["Razorpay Webhooks"])
app.include_router(webhooks_stripe.router, prefix="/v1/webhooks/stripe", tags=["Stripe Webhooks"])

# Recovery
app.include_router(recoveries.router, prefix="/v1/recoveries", tags=["Recoveries"])
app.include_router(recovery_links.router, prefix="/v1/recovery-links", tags=["Recovery Links"])

# Retry Engine
app.include_router(retry.router, prefix="/v1/retry", tags=["Retry"])
app.include_router(retry_policies.router, prefix="/v1/retry/policies", tags=["Retry Policies"])

# Events
app.include_router(events.router, prefix="/v1/events", tags=["Events"])

# Analytics
app.include_router(analytics.router, prefix="/v1/analytics", tags=["Analytics"])

# Schedule
app.include_router(schedule.router, prefix="/v1/schedule", tags=["Schedule"])

# Reconciliation
app.include_router(recon.router, prefix="/v1/recon", tags=["Reconciliation"])

# Maintenance
app.include_router(maintenance.router, prefix="/v1/maintenance", tags=["Maintenance"])

# Profile
app.include_router(profile.router, prefix="/v1/profile", tags=["Profile"])

# Classifier
app.include_router(classifier.router, prefix="/v1/classify", tags=["Classifier"])

# Developer Tools
app.include_router(dev.router, prefix="/_dev", tags=["Developer"])

# Admin DB Tools
app.include_router(admin_db.router, prefix="/admin/db", tags=["Admin DB"])

# Early Access
app.include_router(early_access.router, prefix="/v1/early-access", tags=["Early Access"])

# ---------------------------------------------
# ONBOARDING (CLEAN + CORRECT)
# ---------------------------------------------
app.include_router(onboarding, prefix="/v1/onboarding", tags=["Onboarding"])
app.include_router(onboarding_credentials, prefix="/v1/onboarding", tags=["Onboarding"])
app.include_router(onboarding_finish, prefix="/v1/onboarding", tags=["Onboarding"])

# Gateways
app.include_router(gateways.router, prefix="/v1/gateways", tags=["Gateways"])

# Payment Pages (Magic Links)
app.include_router(pay.router, tags=["Payment Pages"])

# Razorpay OAuth
app.include_router(razorpay_oauth.router)

# ---------------------------------------------
# ROOT ENDPOINT
# ---------------------------------------------
@app.get("/")
def root():
    return {"message": "Tinko Backend is running"}
