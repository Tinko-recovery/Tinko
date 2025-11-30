"""
Twilio Verify Service for OTP functionality
Uses Twilio Verify API for enhanced security and delivery rates
"""
import logging
from typing import Dict, Any
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioException
from ..config import settings

logger = logging.getLogger(__name__)


class TwilioVerifyService:
    """Enhanced OTP service using Twilio Verify API"""
    
    def __init__(self):
        self.twilio_client = None
        self.verify_service_sid = None
        self.is_available = False
        self._initialize()
    
    def _initialize(self):
        """Initialize Twilio Verify service"""
        try:
            if not all([
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN,
                settings.TWILIO_VERIFY_SERVICE_SID
            ]):
                logger.warning("Twilio Verify not configured. Missing credentials or service SID.")
                return
            
            self.twilio_client = TwilioClient(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
            self.verify_service_sid = settings.TWILIO_VERIFY_SERVICE_SID
            self.is_available = True
            
            logger.info(f"Twilio Verify service initialized successfully with SID: {self.verify_service_sid}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Twilio Verify service: {e}")
            self.is_available = False
    
    async def send_verification(self, mobile_number: str, channel: str = "sms") -> Dict[str, Any]:
        """
        Send verification code via Twilio Verify
        
        Args:
            mobile_number: Phone number in E.164 format (+1234567890)
            channel: Verification channel ('sms', 'call', 'email')
            
        Returns:
            Dict with success status and verification details
        """
        if not self.is_available:
            return {
                "success": False,
                "error": "Twilio Verify service not available",
                "provider": "twilio_verify"
            }
        
        try:
            # Format mobile number to E.164 if needed
            formatted_number = self._format_mobile_number(mobile_number)
            if not formatted_number:
                return {
                    "success": False,
                    "error": "Invalid mobile number format",
                    "provider": "twilio_verify"
                }
            
            # Send verification via Twilio Verify API
            verification = self.twilio_client.verify.v2.services(
                self.verify_service_sid
            ).verifications.create(
                to=formatted_number,
                channel=channel
            )
            
            logger.info(f"Verification sent successfully via Twilio Verify: {verification.sid}")
            
            return {
                "success": True,
                "provider": "twilio_verify",
                "verification_sid": verification.sid,
                "status": verification.status,
                "to": formatted_number,
                "channel": channel,
                "valid": verification.valid,
                "lookup": verification.lookup
            }
            
        except TwilioException as e:
            logger.error(f"Twilio Verify send failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "twilio_verify",
                "to": mobile_number
            }
        except Exception as e:
            logger.error(f"Unexpected error sending verification: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "provider": "twilio_verify"
            }
    
    async def check_verification(self, mobile_number: str, code: str) -> Dict[str, Any]:
        """
        Verify OTP code via Twilio Verify
        
        Args:
            mobile_number: Phone number in E.164 format (+1234567890)
            code: 6-digit verification code
            
        Returns:
            Dict with verification status and details
        """
        if not self.is_available:
            return {
                "success": False,
                "error": "Twilio Verify service not available",
                "provider": "twilio_verify"
            }
        
        try:
            # Format mobile number to E.164 if needed
            formatted_number = self._format_mobile_number(mobile_number)
            if not formatted_number:
                return {
                    "success": False,
                    "error": "Invalid mobile number format",
                    "provider": "twilio_verify"
                }
            
            # Check verification via Twilio Verify API
            verification_check = self.twilio_client.verify.v2.services(
                self.verify_service_sid
            ).verification_checks.create(
                to=formatted_number,
                code=code
            )
            
            is_valid = verification_check.status == 'approved'
            
            logger.info(f"Verification check completed: {verification_check.sid}, Valid: {is_valid}")
            
            return {
                "success": True,
                "valid": is_valid,
                "provider": "twilio_verify",
                "verification_sid": verification_check.sid,
                "status": verification_check.status,
                "to": formatted_number,
                "channel": verification_check.channel
            }
            
        except TwilioException as e:
            logger.error(f"Twilio Verify check failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "twilio_verify",
                "to": mobile_number,
                "valid": False
            }
        except Exception as e:
            logger.error(f"Unexpected error checking verification: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "provider": "twilio_verify",
                "valid": False
            }
    
    def _format_mobile_number(self, mobile_number: str) -> str:
        """
        Format mobile number to E.164 format
        
        Args:
            mobile_number: Raw mobile number
            
        Returns:
            Formatted mobile number or empty string if invalid
        """
        # Remove all non-digit characters
        cleaned = ''.join(filter(str.isdigit, mobile_number))
        
        # If already has country code (starts with +)
        if mobile_number.startswith('+'):
            return mobile_number
        
        # If 10 digits, assume US number
        if len(cleaned) == 10:
            return f"+1{cleaned}"
        
        # If 11 digits and starts with 1, it's US
        if len(cleaned) == 11 and cleaned.startswith('1'):
            return f"+{cleaned}"
        
        # If starts with common country codes, add +
        if cleaned.startswith(('91', '44', '61', '33', '49')):
            return f"+{cleaned}"
        
        # Return as-is with + prefix if it looks like international format
        if len(cleaned) >= 10:
            return f"+{cleaned}"
        
        logger.warning(f"Could not format mobile number: {mobile_number}")
        return ""


# Global instance
twilio_verify_service = TwilioVerifyService()


# Convenience functions
async def send_otp_verification(mobile_number: str, channel: str = "sms") -> Dict[str, Any]:
    """Send OTP verification via Twilio Verify"""
    return await twilio_verify_service.send_verification(mobile_number, channel)


async def verify_otp_code(mobile_number: str, code: str) -> Dict[str, Any]:
    """Verify OTP code via Twilio Verify"""
    return await twilio_verify_service.check_verification(mobile_number, code)


def is_verify_available() -> bool:
    """Check if Twilio Verify service is available"""
    return twilio_verify_service.is_available