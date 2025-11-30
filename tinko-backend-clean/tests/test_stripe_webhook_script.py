import requests
import json
import time
from unittest.mock import MagicMock
import sys

# Mock stripe before importing app
sys.modules["stripe"] = MagicMock()

API_BASE = "http://127.0.0.1:8000"

def test_stripe_webhook():
    print("Starting Stripe Webhook Verification...")

    # 1. Create a dummy transaction to match against
    # We need to login first to create a transaction via API, or just insert into DB if we had direct access.
    # Since we don't have direct DB access easily here without setting up the whole app context, 
    # let's try to use the API to create a transaction if possible.
    # But wait, creating a transaction usually requires a valid user/org.
    
    # Let's assume we can use the same user from previous tests or create a new one.
    # Actually, the webhook looks up by `transaction_ref`.
    # We can try to hit the `events` endpoint to create a transaction if it doesn't exist?
    # No, `webhooks_stripe` looks up `Transaction` by `transaction_ref` extracted from description.
    # `_extract_txn_ref_from_description` looks for "Recovery for {ref}".
    
    # So if we send a webhook with description "Recovery for REF123", it will look for REF123.
    # If REF123 doesn't exist, `txn` will be None, and `RecoveryAttempt` creation will fail (foreign key).
    
    # We need a valid Transaction in the DB.
    # Let's use the `onboarding` flow to get a valid user/org, then create a transaction.
    
    # LOGIN
    email = "test_stripe@tinko.in"
    password = "password123"
    
    # Signup/Login
    try:
        requests.post(f"{API_BASE}/v1/auth/signup", json={
            "email": email,
            "password": password,
            "full_name": "Stripe Test User",
            "phone": "8888888888"
        })
    except: pass

    res = requests.post(f"{API_BASE}/v1/auth/login", data={"username": email, "password": password})
    if res.status_code != 200:
        print(f"Login failed: {res.text}")
        return
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Ensure Org
    requests.post(f"{API_BASE}/v1/customer/onboarding", json={
        "business_name": "Stripe Org",
        "phone": "8888888888"
    }, headers=headers)
    
    # Create Transaction (Merchant API)
    # We need an API key for merchant transactions, or we can use the customer API if available?
    # `customer_api.py` has `create_transaction` but it requires `require_api_key_scopes`.
    # Let's generate an API key first.
    # Is there an endpoint to generate API keys? 
    # Usually in `dev.py` or `profile.py`.
    # Let's check `app/routers/dev.py` or just assume we can't easily create one.
    
    # ALTERNATIVE: Use `events.py` -> `/payment_failed` to upsert a transaction!
    # `events.py` line 28: Upsert transaction by external reference.
    # This is perfect.
    
    txn_ref = f"REF_STRIPE_{int(time.time())}"
    print(f"Creating Transaction {txn_ref} via events endpoint...")
    
    res = requests.post(f"{API_BASE}/v1/events/payment_failed", json={
        "transaction_ref": txn_ref,
        "amount": 5000,
        "currency": "INR",
        "gateway": "stripe",
        "failure_reason": "initial_setup"
    }, headers=headers) # Auth header assigns org
    
    if res.status_code != 201:
        print(f"Failed to create transaction: {res.text}")
        return
    
    print("Transaction created.")
    
    # 2. Simulate Stripe Webhook
    # We need to mock the signature verification in the backend.
    # Since we can't easily mock the backend process from here (it's running separately),
    # we have a problem: `webhooks_stripe.py` will reject our request because of invalid signature.
    
    # WORKAROUND:
    # We can temporarily disable signature verification in `webhooks_stripe.py` for this test?
    # OR we can use the `client` from `fastapi.testclient` if we run the test *inside* the app context.
    # Running as a separate script against a running server makes mocking hard.
    
    # Let's try to run this test using `TestClient` by importing the app.
    # This requires installing `httpx` and `stripe` (mocked).
    pass

if __name__ == "__main__":
    # We will run this logic using a proper pytest/TestClient approach in a separate file
    # that imports the app, so we can mock stripe.
    pass
