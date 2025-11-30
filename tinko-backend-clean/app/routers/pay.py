from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.deps import get_db
from app import models
import os

router = APIRouter()

@router.get("/pay/retry/{token}", response_class=HTMLResponse)
def recovery_page(token: str, db: Session = Depends(get_db)):
    # 1. Validate Token
    attempt = db.query(models.RecoveryAttempt).filter(models.RecoveryAttempt.token == token).first()
    if not attempt:
        return "<h1>Invalid or Expired Link</h1>"
        
    txn = attempt.transaction
    if not txn:
        return "<h1>Transaction Not Found</h1>"
        
    org = txn.organization
    
    # 2. Prepare Data
    merchant_name = org.name if org else "Merchant"
    amount = txn.amount / 100 # Assuming cents/paise
    currency = txn.currency.upper()
    
    customer_email = txn.customer_email or ""
    customer_phone = txn.customer_phone or ""
    
    # 3. Render HTML
    # In a real app, use Jinja2 templates. Here we use f-string for simplicity.
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pay {merchant_name}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f9fafb; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .card {{ background: white; padding: 2rem; border-radius: 1rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); width: 100%; max-width: 400px; text-align: center; }}
            .amount {{ font-size: 2.5rem; font-weight: 800; color: #111827; margin: 1rem 0; }}
            .merchant {{ color: #6b7280; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; }}
            .btn {{ background: #DE6B06; color: white; border: none; padding: 1rem; width: 100%; border-radius: 0.5rem; font-size: 1rem; font-weight: 600; cursor: pointer; margin-top: 1rem; }}
            .btn:hover {{ background: #c25e05; }}
            .upi-options {{ display: flex; gap: 1rem; justify-content: center; margin-top: 1.5rem; }}
            .upi-icon {{ width: 48px; height: 48px; border-radius: 12px; border: 1px solid #e5e7eb; padding: 8px; cursor: pointer; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="merchant">Paying {merchant_name}</div>
            <div class="amount">{currency} {amount:.2f}</div>
            <p style="color: #374151; font-size: 0.9rem;">Complete your payment securely.</p>
            
            <button id="rzp-button1" class="btn">Pay Now</button>
            
            <div id="upi-section" style="display: none;">
                <p style="margin-top: 1.5rem; font-size: 0.8rem; color: #6b7280;">OR PAY VIA UPI APP</p>
                <div class="upi-options">
                    <a href="upi://pay?pa=merchant@upi&pn={merchant_name}&am={amount}&tr={txn.transaction_ref}&cu={currency}"><img src="https://cdn.iconscout.com/icon/free/png-256/free-google-pay-2038779-1721670.png" class="upi-icon" alt="GPay"></a>
                    <a href="upi://pay?pa=merchant@upi&pn={merchant_name}&am={amount}&tr={txn.transaction_ref}&cu={currency}"><img src="https://cdn.iconscout.com/icon/free/png-256/free-phonepe-2709167-2249157.png" class="upi-icon" alt="PhonePe"></a>
                    <a href="upi://pay?pa=merchant@upi&pn={merchant_name}&am={amount}&tr={txn.transaction_ref}&cu={currency}"><img src="https://cdn.iconscout.com/icon/free/png-256/free-paytm-226448.png" class="upi-icon" alt="Paytm"></a>
                </div>
            </div>
        </div>

        <script>
            // Auto-detect mobile for UPI
            if (/Android|iPhone/i.test(navigator.userAgent)) {{
                document.getElementById('upi-section').style.display = 'block';
            }}

            document.getElementById('rzp-button1').onclick = function(e){{
                var options = {{
                    "key": "{org.gateway_credentials.get('razorpay', {}).get('key_id', 'rzp_test_123456789') if org.gateway_credentials else 'rzp_test_123456789'}",
                    "amount": "{int(txn.amount)}", 
                    "currency": "{currency}",
                    "name": "{merchant_name}",
                    "description": "Payment Recovery",
                    "image": "{org.logo_url or 'https://example.com/logo.png'}",
                    "order_id": "{txn.razorpay_order_id or ''}", // If we have one
                    "handler": function (response){{
                        alert("Payment Successful: " + response.razorpay_payment_id);
                        // Call backend to mark as paid
                    }},
                    "prefill": {{
                        "name": "{customer_email.split('@')[0] if customer_email else 'Customer'}",
                        "email": "{customer_email}",
                        "contact": "{customer_phone}"
                    }},
                    "theme": {{
                        "color": "#DE6B06"
                    }}
                }};
                var rzp1 = new Razorpay(options);
                rzp1.open();
                e.preventDefault();
            }}
        </script>
    </body>
    </html>
    """
    return html
