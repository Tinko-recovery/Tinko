"""
TINKO – Production-Grade SQLAlchemy Models (Recreated & Cleaned)

This file defines the full data model for:
- Organizations
- Users & Sessions
- API Keys
- Transactions
- Payment Failure Events
- Recovery Attempts
- Notification Logs
- Retry Policies
- Recon Logs
- PSP Events
- Email OTP
- Mobile OTP
- OTP Security Logs
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey,
    JSON, func, UniqueConstraint, Index, Float
)
from sqlalchemy.orm import relationship
from .db import Base


# =====================================================
# ORANIZATION MODEL
# =====================================================

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    slug = Column(String(64), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Extended Profile Fields
    website = Column(String(255), nullable=True)
    industry = Column(String(64), nullable=True)
    gst_number = Column(String(32), nullable=True)
    
    # Pricing / Fees
    service_fee_percent = Column(Float, nullable=False, default=2.0)   # 2.0%
    service_fee_fixed = Column(Integer, nullable=False, default=30)    # 30 paise
    
    payment_gateways = Column(JSON, nullable=True, default=list)  # ["stripe", "razorpay"]
    monthly_volume = Column(String(32), nullable=True)            # "< 100", "100-1000"
    recovery_channels = Column(JSON, nullable=True, default=list) # ["whatsapp", "email"]

    # Smart Onboarding - Phase 2 Fields
    business_size = Column(String(32), nullable=True)             # "Solo", "2-10", "10-50", "50+"
    monthly_gmv = Column(String(32), nullable=True)               # "< 1L", "1-10L"
    
    recovery_destination = Column(String(32), default="customer") # "customer", "internal", "both"
    
    # Technical & Credentials (Encrypted/JSON)
    # Structure: { "razorpay": { "auth_type": "oauth", "access_token": "...", "refresh_token": "...", "expires_at": ... }, "cashfree": { "auth_type": "manual", "app_id": "...", "secret_key": "..." } }
    gateway_credentials = Column(JSON, nullable=True, default=dict)

    # Branding & Notifications
    brand_name = Column(String(128), nullable=True)
    support_email = Column(String(255), nullable=True)
    reply_to_email = Column(String(255), nullable=True)
    logo_url = Column(String(512), nullable=True)
    
    # Contacts & Compliance
    team_contacts = Column(JSON, nullable=True, default=dict)     # { "tech": "...", "finance": "..." }
    billing_email = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                        onupdate=func.now(), nullable=False)

    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete")
    transactions = relationship("Transaction", back_populates="organization")



# =====================================================
# USER MODEL
# =====================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    # Primary identity fields
    email = Column(String(255), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=True)
    full_name = Column(String(128), nullable=True)

    # Role & Access
    role = Column(String(32), nullable=False, default="operator")  # admin/operator/analyst
    account_type = Column(String(32), nullable=False, default="user")
    auth_provider = Column(String(50), nullable=False, default="email")
    auth_providers = Column(JSON, nullable=False, default=list)    # ["email", "google", "mobile_otp"]

    # Organization
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"),
                    nullable=True, index=True)

    # Mobile Auth
    mobile_number = Column(String(20), unique=True, nullable=True, index=True)
    country_code = Column(String(5), nullable=True)
    mobile_verified = Column(Boolean, default=False, nullable=False)

    # OAuth / Social
    google_id = Column(String(128), unique=True, nullable=True, index=True)
    google_email = Column(String(255), nullable=True, index=True)
    avatar_url = Column(String(500), nullable=True)

    # Verification
    is_email_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    mobile_verified_at = Column(DateTime(timezone=True), nullable=True)

    # Login Tracking
    last_login = Column(DateTime(timezone=True), nullable=True)
    login_count = Column(Integer, default=0, nullable=False)

    # Preferences
    preferred_language = Column(String(5), default="en", nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                        onupdate=func.now(), nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="users")
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, mobile={self.mobile_number})>"



# =====================================================
# API KEY MODEL
# =====================================================

class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False, index=True)

    key_name = Column(String(128), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    key_prefix = Column(String(16), nullable=False)

    scopes = Column(JSON, nullable=False, default=list)
    is_active = Column(Boolean, default=True, nullable=False)

    last_used_at = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                        onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="api_keys")

    @classmethod
    def generate_key(cls):
        import secrets
        return f"sk_{secrets.token_urlsafe(32)}"

    def mask_key(self):
        return f"{self.key_prefix}...{self.key_hash[-4:]}"



# =====================================================
# TRANSACTION MODEL
# =====================================================

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    transaction_ref = Column(String(64), unique=True, nullable=False, index=True)

    amount = Column(Integer, nullable=True)
    currency = Column(String(8), nullable=True)
    
    # Fee breakdown (stored at creation/capture)
    service_fee = Column(Integer, nullable=True)  # in paise
    net_amount = Column(Integer, nullable=True)   # amount - service_fee
    
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"),
                    nullable=True, index=True)

    # Stripe
    stripe_payment_intent_id = Column(String(128), index=True, nullable=True)
    stripe_checkout_session_id = Column(String(128), index=True, nullable=True)
    stripe_customer_id = Column(String(128), index=True, nullable=True)
    payment_link_url = Column(String(512), nullable=True)
    customer_email = Column(String(255), nullable=True)
    customer_phone = Column(String(32), nullable=True)

    # Razorpay
    razorpay_order_id = Column(String(128), index=True, nullable=True)
    razorpay_payment_id = Column(String(128), index=True, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                        onupdate=func.now(), nullable=False)

    organization = relationship("Organization", back_populates="transactions")
    failure_events = relationship("FailureEvent", back_populates="transaction",
                                  cascade="all, delete")



# =====================================================
# FAILURE EVENT MODEL
# =====================================================

class FailureEvent(Base):
    __tablename__ = "failure_events"

    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"),
                            nullable=False, index=True)

    gateway = Column(String(32), nullable=True)
    reason = Column(String(128), nullable=False)
    meta = Column("metadata", JSON, nullable=True)

    occurred_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    transaction = relationship("Transaction", back_populates="failure_events")



# =====================================================
# RECOVERY ATTEMPT MODEL
# =====================================================

class RecoveryAttempt(Base):
    __tablename__ = "recovery_attempts"

    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"),
                            nullable=True, index=True)
    transaction_ref = Column(String(64), nullable=True, index=True)

    channel = Column(String(16), nullable=True)  # email/sms/link/whatsapp
    token = Column(String(64), unique=True, nullable=False, index=True)

    status = Column(String(24), nullable=False, default="created")
    expires_at = Column(DateTime(timezone=True), nullable=False)

    opened_at = Column(DateTime(timezone=True), nullable=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    retry_count = Column(Integer, default=0, nullable=False)
    last_retry_at = Column(DateTime(timezone=True), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    max_retries = Column(Integer, default=3, nullable=False)

    transaction = relationship("Transaction")
    notifications = relationship("NotificationLog", back_populates="recovery_attempt",
                                 cascade="all, delete")



# =====================================================
# NOTIFICATION LOG MODEL
# =====================================================

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True)
    recovery_attempt_id = Column(Integer, ForeignKey("recovery_attempts.id",
                                                     ondelete="CASCADE"),
                                 nullable=False, index=True)

    channel = Column(String(16), nullable=False)
    recipient = Column(String(255), nullable=False)
    status = Column(String(24), default="pending", nullable=False)

    provider = Column(String(32), nullable=True)
    provider_message_id = Column(String(128), nullable=True)
    error_message = Column(String(512), nullable=True)

    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    recovery_attempt = relationship("RecoveryAttempt", back_populates="notifications")



# =====================================================
# RETRY POLICY MODEL
# =====================================================

class RetryPolicy(Base):
    __tablename__ = "retry_policies"

    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"),
                    nullable=False, index=True)

    name = Column(String(128), nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)

    initial_delay_minutes = Column(Integer, default=60, nullable=False)
    backoff_multiplier = Column(Integer, default=2, nullable=False)
    max_delay_minutes = Column(Integer, default=1440, nullable=False)

    enabled_channels = Column(JSON, nullable=False, default=list)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                        onupdate=func.now(), nullable=False)

    organization = relationship("Organization")



# =====================================================
# RECON LOG MODEL
# =====================================================

class ReconLog(Base):
    __tablename__ = "recon_logs"

    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"),
                            index=True, nullable=False)

    stripe_checkout_session_id = Column(String(128), nullable=True)
    stripe_payment_intent_id = Column(String(128), nullable=True)

    internal_status = Column(String(32), nullable=False)
    external_status = Column(String(32), nullable=True)
    result = Column(String(16), nullable=False)   # ok | mismatch
    details = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)



# =====================================================
# PSP EVENT MODEL
# =====================================================

class PspEvent(Base):
    __tablename__ = "psp_events"

    id = Column(Integer, primary_key=True)
    provider = Column(String(32), nullable=False)
    event_type = Column(String(64), nullable=False)

    psp_event_id = Column(String(160), nullable=False, unique=True, index=True)
    payload = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)



# =====================================================
# EMAIL OTP MODEL (Production)
# =====================================================

class EmailOTP(Base):
    __tablename__ = "email_otps"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=False)
    otp_hash = Column(String(64), nullable=False)      # SHA256 hashed
    channel = Column(String(16), default="email")

    expires_at = Column(DateTime(timezone=True), nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=5, nullable=False)

    status = Column(String(16), default="pending", nullable=False)
    consumed_at = Column(DateTime(timezone=True), nullable=True)

    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_email_otp_email", "email"),
    )



# =====================================================
# OTP SECURITY LOG MODEL
# =====================================================

class OTPSecurityLog(Base):
    __tablename__ = "otp_security_logs"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    action = Column(String(50), nullable=False)  # request_otp / verify_otp / block
    success = Column(Boolean, nullable=False)
    attempt_count = Column(Integer, default=1, nullable=False)

    blocked_until = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)



# =====================================================
# MOBILE OTP MODEL
# =====================================================

class MobileOTP(Base):
    __tablename__ = "mobile_otps"

    id = Column(Integer, primary_key=True, index=True)
    mobile_number = Column(String(20), index=True, nullable=False)
    otp_hash = Column(String(64), nullable=False)

    expires_at = Column(DateTime(timezone=True), nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=5, nullable=False)

    status = Column(String(16), default="pending", nullable=False)
    consumed_at = Column(DateTime(timezone=True), nullable=True)

    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_mobile_otp_mobile", "mobile_number"),
    )



# =====================================================
# USER SESSION MODEL
# =====================================================

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False, index=True)

    session_token = Column(String(255), unique=True, nullable=False, index=True)

    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_info = Column(JSON, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<UserSession(user_id={self.user_id}, active={self.is_active})>"


# =====================================================
# JOB QUEUE MODEL
# =====================================================

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(128), nullable=False, index=True)
    arguments = Column(JSON, nullable=False, default=dict)
    
    status = Column(String(32), default="pending", nullable=False, index=True) # pending, running, completed, failed
    
    scheduled_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    error = Column(String, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)

    def __repr__(self):
        return f"<Job(id={self.id}, task={self.task_name}, status={self.status})>"


# =====================================================
# WEBHOOK EVENT LOG (Dead Letter Queue)
# =====================================================

class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(32), nullable=False, index=True) # razorpay, stripe
    
    headers = Column(JSON, nullable=True)
    payload = Column(JSON, nullable=False)
    
    status = Column(String(32), default="received", nullable=False, index=True) # received, processed, failed
    error = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<WebhookEvent(id={self.id}, provider={self.provider}, status={self.status})>"


# =====================================================
# AUDIT LOG MODEL (Enterprise Security)
# =====================================================

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    action = Column(String(64), nullable=False)  # e.g., "update_profile", "change_gateway"
    resource_type = Column(String(64), nullable=False) # e.g., "organization", "user"
    resource_id = Column(String(64), nullable=True)
    
    changes = Column(JSON, nullable=True) # { "field": { "old": "val", "new": "val" } }
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    organization = relationship("Organization")
    user = relationship("User")

    def __repr__(self):
        return f"<AuditLog(action={self.action}, user={self.user_id})>"
