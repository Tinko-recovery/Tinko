"""
PSP-001: Stripe Service for Payment Processing
Handles checkout session creation, payment links, and customer management.
"""
import os
import stripe
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)

# Configure Stripe API key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class StripeService:
    """Service for Stripe payment processing."""
    
    @staticmethod
    def create_checkout_session(
        amount: int,
        currency: str,
        transaction_ref: str,
        customer_email: Optional[str] = None,
        customer_phone: Optional[str] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout Session for payment recovery.
        
        Args:
            amount: Amount in smallest currency unit (e.g., cents)
            currency: Three-letter ISO currency code (e.g., 'usd')
            transaction_ref: Unique transaction reference
            customer_email: Customer's email address
            customer_phone: Customer's phone number
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancelled payment
            metadata: Additional metadata to attach to session
            
        Returns:
            Dict containing session_id, payment_intent_id, and checkout_url
        """
        try:
            # Use unified PUBLIC_BASE_URL for public redirects (fallback to legacy BASE_URL then dev default)
            base_url = os.getenv("PUBLIC_BASE_URL") or os.getenv("BASE_URL") or "http://localhost:3000"
            success_url = success_url or f"{base_url}/pay/success?session_id={{CHECKOUT_SESSION_ID}}"
            cancel_url = cancel_url or f"{base_url}/pay/cancel"
            
            # Prepare session metadata
            session_metadata = {
                "transaction_ref": transaction_ref,
                **(metadata or {})
            }
            
            # Create checkout session
            session_params = {
                "payment_method_types": ["card"],
                "line_items": [{
                    "price_data": {
                        "currency": currency,
                        "unit_amount": amount,
                        "product_data": {
                            "name": f"Payment Recovery - {transaction_ref}",
                            "description": "Failed payment recovery"
                        }
                    },
                    "quantity": 1
                }],
                "mode": "payment",
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": session_metadata,
                "expires_at": int((datetime.utcnow() + timedelta(hours=24)).timestamp())
            }
            
            # Add customer email if provided
            if customer_email:
                session_params["customer_email"] = customer_email
            
            # Create session
            session = stripe.checkout.Session.create(**session_params)
            
            logger.info(
                "stripe_checkout_session_created",
                session_id=session.id,
                payment_intent_id=session.payment_intent,
                transaction_ref=transaction_ref,
                amount=amount,
                currency=currency
            )
            
            return {
                "session_id": session.id,
                "payment_intent_id": session.payment_intent,
                "checkout_url": session.url,
                "expires_at": datetime.fromtimestamp(session.expires_at)
            }
            
        except stripe.error.StripeError as e:
            logger.error(
                "stripe_checkout_session_failed",
                error=str(e),
                transaction_ref=transaction_ref,
                error_type=type(e).__name__
            )
            raise
    
    @staticmethod
    def create_payment_link(
        amount: int,
        currency: str,
        transaction_ref: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a reusable Stripe Payment Link.
        
        Args:
            amount: Amount in smallest currency unit
            currency: Three-letter ISO currency code
            transaction_ref: Unique transaction reference
            metadata: Additional metadata
            
        Returns:
            Dict containing payment_link_id and url
        """
        try:
            # First create a product
            product = stripe.Product.create(
                name=f"Payment Recovery - {transaction_ref}",
                description="Failed payment recovery",
                metadata={"transaction_ref": transaction_ref}
            )
            
            # Create a price for the product
            price = stripe.Price.create(
                product=product.id,
                unit_amount=amount,
                currency=currency
            )
            
            # Create payment link
            payment_link = stripe.PaymentLink.create(
                line_items=[{"price": price.id, "quantity": 1}],
                metadata={
                    "transaction_ref": transaction_ref,
                    **(metadata or {})
                },
                after_completion={
                    "type": "redirect",
                    "redirect": {
                        "url": (os.getenv("PUBLIC_BASE_URL") or os.getenv("BASE_URL") or "http://localhost:3000") + "/pay/success"
                    }
                }
            )
            
            logger.info(
                "stripe_payment_link_created",
                payment_link_id=payment_link.id,
                url=payment_link.url,
                transaction_ref=transaction_ref,
                amount=amount,
                currency=currency
            )
            
            return {
                "payment_link_id": payment_link.id,
                "url": payment_link.url,
                "product_id": product.id,
                "price_id": price.id
            }
            
        except stripe.error.StripeError as e:
            logger.error(
                "stripe_payment_link_failed",
                error=str(e),
                transaction_ref=transaction_ref,
                error_type=type(e).__name__
            )
            raise
    
    @staticmethod
    def retrieve_checkout_session(session_id: str) -> Optional[stripe.checkout.Session]:
        """Retrieve a checkout session by ID."""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            logger.info("stripe_session_retrieved", session_id=session_id, status=session.status)
            return session
        except stripe.error.StripeError as e:
            logger.error(
                "stripe_session_retrieve_failed",
                error=str(e),
                session_id=session_id,
                error_type=type(e).__name__
            )
            return None
    
    @staticmethod
    def retrieve_payment_intent(payment_intent_id: str) -> Optional[stripe.PaymentIntent]:
        """Retrieve a payment intent by ID."""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            logger.info(
                "stripe_payment_intent_retrieved",
                payment_intent_id=payment_intent_id,
                status=intent.status,
                amount=intent.amount
            )
            return intent
        except stripe.error.StripeError as e:
            logger.error(
                "stripe_payment_intent_retrieve_failed",
                error=str(e),
                payment_intent_id=payment_intent_id,
                error_type=type(e).__name__
            )
            return None

    @staticmethod
    def get_session_status(session_id: str) -> Optional[str]:
        """Return a simplified status for a Checkout Session: 'paid', 'open', or None on error."""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            # session.payment_status can be 'paid', 'unpaid', 'no_payment_required'
            status = getattr(session, "payment_status", None)
            # Normalize
            if status == "paid":
                return "paid"
            if status in ("unpaid", "no_payment_required", None):
                return "open"
            return status
        except stripe.error.StripeError as e:
            logger.error("stripe_get_session_status_failed", error=str(e), session_id=session_id)
            return None

    @staticmethod
    def get_payment_intent_status(payment_intent_id: str) -> Optional[str]:
        """Return a simplified status for a Payment Intent: 'succeeded', 'requires_payment_method', etc."""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return getattr(intent, "status", None)
        except stripe.error.StripeError as e:
            logger.error("stripe_get_payment_intent_status_failed", error=str(e), payment_intent_id=payment_intent_id)
            return None
    
    @staticmethod
    def create_customer(
        email: Optional[str] = None,
        phone: Optional[str] = None,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Optional[stripe.Customer]:
        """Create a Stripe customer."""
        try:
            customer_params = {"metadata": metadata or {}}
            if email:
                customer_params["email"] = email
            if phone:
                customer_params["phone"] = phone
            if name:
                customer_params["name"] = name
            
            customer = stripe.Customer.create(**customer_params)
            logger.info("stripe_customer_created", customer_id=customer.id, email=email)
            return customer
        except stripe.error.StripeError as e:
            logger.error(
                "stripe_customer_create_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return None
    
    @staticmethod
    def verify_webhook_signature(payload: bytes, sig_header: str) -> Optional[Dict[str, Any]]:
        """
        Verify Stripe webhook signature and return event.
        
        Args:
            payload: Raw request body
            sig_header: Stripe-Signature header value
            
        Returns:
            Parsed webhook event or None if verification fails
        """
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if not webhook_secret:
            logger.warning("stripe_webhook_secret_missing")
            return None
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            logger.info(
                "stripe_webhook_verified",
                event_type=event["type"],
                event_id=event["id"]
            )
            return event
        except ValueError as e:
            logger.error("stripe_webhook_invalid_payload", error=str(e))
            return None
        except stripe.error.SignatureVerificationError as e:
            logger.error("stripe_webhook_signature_failed", error=str(e))
            return None
