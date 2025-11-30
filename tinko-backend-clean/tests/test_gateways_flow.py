import requests
import json
import time

API_BASE = "http://127.0.0.1:8000"
TEST_EMAIL = "test@tinko.in"
TEST_OTP = "123456"

def test_gateway_flow():
    print("Starting Gateway Verification...")
    
    # 1. Login (Get Token via OTP Flow)
    print(f"Sending OTP to {TEST_EMAIL}...")
    try:
        # Try signup intent first
        res = requests.post(f"{API_BASE}/v1/auth/email/send-otp", json={
            "email": TEST_EMAIL,
            "intent": "signup"
        })
        
        if res.status_code == 409: # Already exists
            print("User exists, trying login intent...")
            res = requests.post(f"{API_BASE}/v1/auth/email/send-otp", json={
                "email": TEST_EMAIL,
                "intent": "login"
            })
        
        if res.status_code != 200:
            print(f"[FAILURE] Send OTP failed: {res.text}")
            return

        print("OTP Sent. Verifying...")
        res = requests.post(f"{API_BASE}/v1/auth/email/verify-otp", json={
            "email": TEST_EMAIL,
            "otp": TEST_OTP
        })

        if res.status_code != 200:
            print(f"[FAILURE] Verify OTP failed: {res.text}")
            return

        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("[SUCCESS] Logged in successfully.")

    except Exception as e:
        print(f"[FAILURE] Auth failed: {e}")
        return

    # 2. Ensure Org Exists
    print("\nChecking Organization...")
    res = requests.get(f"{API_BASE}/v1/auth/me", headers=headers) 
    
    print("Creating/Updating Org...")
    res = requests.post(f"{API_BASE}/v1/customer/onboarding", json={
        "business_name": "Test Org",
        "phone": "9999999999",
        "payment_gateways": [], 
        "gateway_credentials": {}
    }, headers=headers)
    
    if res.status_code == 200:
         print("[SUCCESS] Org created/updated.")
         pass
    else:
        print(f"[WARNING] Onboarding step warning: {res.text}")

    # 3. Test OAuth Connect (Razorpay)
    print("\nTesting OAuth Connect (Razorpay)...")
    res = requests.get(f"{API_BASE}/v1/gateways/connect/razorpay", headers=headers)
    if res.status_code == 200:
        print(f"[SUCCESS] Connect URL received: {res.json()['redirect_url']}")
    else:
        print(f"[FAILURE] Connect failed: {res.text}")

    # 4. Test OAuth Callback (Razorpay)
    print("\nTesting OAuth Callback (Razorpay)...")
    org_id = 1 
    state = f"{org_id}_randomstate"
    
    res = requests.get(f"{API_BASE}/v1/gateways/callback/razorpay?code=mock_code&state={state}", headers=headers)
    if res.status_code == 200:
        print(f"[SUCCESS] Callback success: {res.json()}")
    else:
        print(f"[FAILURE] Callback failed: {res.text}")

    # 5. Test Manual Verification (Cashfree)
    print("\nTesting Manual Verification (Cashfree)...")
    res = requests.post(f"{API_BASE}/v1/gateways/verify", json={
        "gateway": "Cashfree",
        "key_id": "test_app_id",
        "key_secret": "test_secret_key"
    }, headers=headers)
    
    if res.status_code == 200:
        print(f"[SUCCESS] Manual verification success: {res.json()}")
    else:
        print(f"[FAILURE] Manual verification failed: {res.text}")

if __name__ == "__main__":
    test_gateway_flow()
