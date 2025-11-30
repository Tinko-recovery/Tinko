"""PSP Adapter Dispatcher - Routes to correct PSP based on gateway."""
import os
from typing import Optional
from .adapter import PSPAdapter, PSPProvider
from .stripe_adapter import StripeAdapter
from .razorpay_adapter import RazorpayAdapter


class PSPDispatcher:
    """
    Dispatcher that selects and initializes the correct PSP adapter.
    Loads credentials from environment variables.
    """
    
    _adapters = {}
    
    @classmethod
    def get_adapter(cls, provider: str) -> PSPAdapter:
        """
        Get PSP adapter for the given provider.
        
        Args:
            provider: PSP provider name (stripe, razorpay, etc.)
            
        Returns:
            Initialized PSP adapter
            
        Raises:
            ValueError: If provider is not supported or credentials missing
        """
        provider = provider.lower()
        
        # Return cached adapter if exists
        if provider in cls._adapters:
            return cls._adapters[provider]
        
        # Initialize adapter based on provider
        if provider == PSPProvider.STRIPE:
            api_key = os.getenv("STRIPE_SECRET_KEY")
            webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
            if not api_key:
                raise ValueError("STRIPE_SECRET_KEY environment variable not set")
            adapter = StripeAdapter(api_key=api_key, api_secret=webhook_secret)
            
        elif provider == PSPProvider.RAZORPAY:
            api_key = os.getenv("RAZORPAY_KEY_ID")
            api_secret = os.getenv("RAZORPAY_KEY_SECRET")
            if not api_key or not api_secret:
                raise ValueError("RAZORPAY_KEY_ID or RAZORPAY_KEY_SECRET not set")
            adapter = RazorpayAdapter(api_key=api_key, api_secret=api_secret)
            
        else:
            raise ValueError(f"Unsupported PSP provider: {provider}")
        
        # Cache adapter
        cls._adapters[provider] = adapter
        return adapter
    
    @classmethod
    def clear_cache(cls):
        """Clear cached adapters (useful for testing)."""
        cls._adapters = {}


# Convenience functions
def get_stripe_adapter() -> StripeAdapter:
    """Get Stripe adapter."""
    return PSPDispatcher.get_adapter(PSPProvider.STRIPE)


def get_razorpay_adapter() -> RazorpayAdapter:
    """Get Razorpay adapter."""
    return PSPDispatcher.get_adapter(PSPProvider.RAZORPAY)
