"""
PSP Adapter Base Class and Interface.
Provides uniform interface for multiple payment gateways (Stripe, Razorpay, etc.).
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum


class PSPProvider(str, Enum):
    """Supported PSP providers."""
    STRIPE = "stripe"
    RAZORPAY = "razorpay"
    PAYPAL = "paypal"


class PSPAdapter(ABC):
    """
    Base adapter for Payment Service Providers.
    All PSP implementations must inherit from this class.
    """
    
    def __init__(self, api_key: str, api_secret: Optional[str] = None, **kwargs):
        """
        Initialize PSP adapter with credentials.
        
        Args:
            api_key: Primary API key
            api_secret: Secondary secret/webhook secret
            **kwargs: Provider-specific configuration
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.config = kwargs
    
    @abstractmethod
    def create_payment_intent(
        self,
        amount: int,
        currency: str,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a payment intent.
        
        Args:
            amount: Amount in smallest currency unit (e.g., cents)
            currency: ISO currency code (e.g., "usd", "inr")
            metadata: Additional metadata to attach
            **kwargs: Provider-specific parameters
            
        Returns:
            Dict containing:
                - intent_id: Unique payment intent ID
                - status: Payment status
                - client_secret: Client secret for frontend
                - any provider-specific fields
        """
        pass
    
    @abstractmethod
    def retrieve_payment_intent(self, intent_id: str) -> Dict[str, Any]:
        """
        Retrieve payment intent details.
        
        Args:
            intent_id: Payment intent ID
            
        Returns:
            Dict with payment intent details including status
        """
        pass
    
    @abstractmethod
    def create_checkout_session(
        self,
        amount: int,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a hosted checkout session.
        
        Args:
            amount: Amount in smallest currency unit
            currency: ISO currency code
            success_url: Redirect URL on success
            cancel_url: Redirect URL on cancel
            metadata: Additional metadata
            **kwargs: Provider-specific parameters
            
        Returns:
            Dict containing:
                - session_id: Checkout session ID
                - url: Hosted checkout URL
                - any provider-specific fields
        """
        pass

    @abstractmethod
    def create_payment_link(
        self,
        amount: int,
        currency: str,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a payment link (if supported by provider).

        Args:
            amount: Amount in smallest currency unit
            currency: ISO currency code
            metadata: Additional metadata
            **kwargs: Provider-specific parameters

        Returns:
            Dict containing:
                - payment_link_id
                - url
                - any provider-specific fields
        """
        pass
    
    @abstractmethod
    def verify_webhook(
        self,
        payload: bytes,
        signature: str,
        secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify and parse webhook payload.
        
        Args:
            payload: Raw webhook payload bytes
            signature: Webhook signature from headers
            secret: Webhook secret (uses self.api_secret if not provided)
            
        Returns:
            Parsed webhook event data
            
        Raises:
            ValueError: If signature verification fails
        """
        pass
    
    @abstractmethod
    def refund_payment(
        self,
        payment_id: str,
        amount: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Refund a payment.
        
        Args:
            payment_id: Payment/intent ID to refund
            amount: Amount to refund (None for full refund)
            reason: Refund reason
            
        Returns:
            Dict with refund details
        """
        pass
    
    def normalize_status(self, provider_status: str) -> str:
        """
        Normalize provider-specific status to standard status.
        
        Args:
            provider_status: Status from PSP
            
        Returns:
            One of: pending, succeeded, failed, cancelled, requires_action
        """
        # Default implementation - override in subclasses for provider-specific mapping
        status_map = {
            "requires_payment_method": "pending",
            "requires_confirmation": "pending",
            "requires_action": "requires_action",
            "processing": "pending",
            "succeeded": "succeeded",
            "canceled": "cancelled",
            "failed": "failed",
        }
        return status_map.get(provider_status.lower(), "pending")

    @abstractmethod
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve hosted checkout session status/details if supported.

        Args:
            session_id: Provider checkout session identifier

        Returns:
            Dict with at least: {"session_id": str, "status": str, ...}
        """
        pass
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(provider={getattr(self, 'provider', 'unknown')})>"
