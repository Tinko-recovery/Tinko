# 🧪 Testing Payment Failure & Recovery Flow

## Overview
This guide shows you how to **simulate a failed payment** and test Tinko's **automatic recovery system**.

---

## 📋 The Complete Flow

```
Customer Payment Attempt
         ↓
    ❌ PAYMENT FAILS
         ↓
    Tinko Detects Failure
         ↓
    Creates Recovery Link
         ↓
    Sends to Customer (SMS/Email/WhatsApp)
         ↓
    Customer Clicks Link
         ↓
    ✅ Payment Succeeds
```

---

## 🎯 Method 1: Using the API (Recommended)

### **Step 1: Simulate a Failed Payment**

Use the `/v1/events/payment_failed` endpoint to report a payment failure:

```powershell
# Using PowerShell
$body = @{
    transaction_ref = "ORDER_12345"
    amount = 4999
    currency = "INR"
    gateway = "razorpay"
    failure_reason = "insufficient_funds"
    customer = @{
        email = "customer@example.com"
        phone = "+919876543210"
    }
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://127.0.0.1:8000/v1/events/payment_failed" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

**Or using Python:**

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/v1/events/payment_failed",
    json={
        "transaction_ref": "ORDER_12345",
        "amount": 4999,
        "currency": "INR",
        "gateway": "razorpay",
        "failure_reason": "insufficient_funds",
        "customer": {
            "email": "customer@example.com",
            "phone": "+919876543210"
        }
    }
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

### **Step 2: Create a Recovery Link**

After the payment fails, create a recovery link:

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/_dev/seed/recovery_link?ref=ORDER_12345" `
    -Method POST
```

**Or using Python:**

```python
response = requests.post(
    "http://127.0.0.1:8000/_dev/seed/recovery_link",
    params={"ref": "ORDER_12345"}
)

result = response.json()
print(f"Recovery URL: {result['url']}")
print(f"Token: {result['token']}")
```

### **Step 3: Test the Recovery Link**

Open the recovery URL in your browser:
```
http://127.0.0.1:8000/pay/retry/{token}
```

---

## 🎯 Method 2: Complete End-to-End Test Script

Create a file called `test_payment_failure.py`:

```python
import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_payment_failure_flow():
    print("=" * 60)
    print("🧪 TINKO PAYMENT FAILURE TEST")
    print("=" * 60)
    
    # Step 1: Create a test transaction
    transaction_ref = f"TEST_{int(time.time())}"
    print(f"\n📝 Step 1: Creating transaction ({transaction_ref})...")
    
    transaction_response = requests.post(
        f"{BASE_URL}/_dev/seed/transaction",
        params={
            "ref": transaction_ref,
            "amount": 2999,
            "currency": "INR"
        }
    )
    
    if transaction_response.status_code == 200:
        print("✅ Transaction created successfully")
        print(f"   Transaction ID: {transaction_response.json()['id']}")
    else:
        print(f"❌ Failed to create transaction: {transaction_response.text}")
        return
    
    # Step 2: Simulate payment failure
    print(f"\n❌ Step 2: Simulating payment failure...")
    
    failure_response = requests.post(
        f"{BASE_URL}/v1/events/payment_failed",
        json={
            "transaction_ref": transaction_ref,
            "amount": 2999,
            "currency": "INR",
            "gateway": "razorpay",
            "failure_reason": "Card declined - insufficient funds",
            "customer": {
                "email": "test.customer@example.com",
                "phone": "+919876543210"
            },
            "metadata": {
                "order_id": transaction_ref,
                "product": "Premium Subscription"
            }
        }
    )
    
    if failure_response.status_code == 201:
        failure_data = failure_response.json()
        print("✅ Payment failure recorded")
        print(f"   Failure Event ID: {failure_data['id']}")
        print(f"   Transaction ID: {failure_data['transaction_id']}")
    else:
        print(f"❌ Failed to record failure: {failure_response.text}")
        return
    
    # Step 3: Generate recovery link
    print(f"\n🔗 Step 3: Generating recovery link...")
    
    recovery_response = requests.post(
        f"{BASE_URL}/_dev/seed/recovery_link",
        params={
            "ref": transaction_ref,
            "ttl_hours": 24.0
        }
    )
    
    if recovery_response.status_code == 200:
        recovery_data = recovery_response.json()
        print("✅ Recovery link generated")
        print(f"   Recovery URL: {recovery_data['url']}")
        print(f"   Token: {recovery_data['token']}")
        print(f"   Expires: {recovery_data['expires_at']}")
    else:
        print(f"❌ Failed to generate recovery link: {recovery_response.text}")
        return
    
    # Step 4: Verify events
    print(f"\n📊 Step 4: Verifying failure events...")
    
    events_response = requests.get(
        f"{BASE_URL}/v1/events/by_ref/{transaction_ref}"
    )
    
    if events_response.status_code == 200:
        events = events_response.json()
        print(f"✅ Found {len(events)} failure event(s)")
        for event in events:
            print(f"   - Event #{event['id']}: {event['reason']}")
            print(f"     Gateway: {event['gateway']}")
            print(f"     Occurred: {event['occurred_at'] or 'N/A'}")
    else:
        print(f"❌ Failed to retrieve events: {events_response.text}")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETE!")
    print("=" * 60)
    print(f"\n📋 Summary:")
    print(f"   Transaction Ref: {transaction_ref}")
    print(f"   Recovery URL: {recovery_data['url']}")
    print(f"\n💡 Next steps:")
    print(f"   1. Open the recovery URL in your browser")
    print(f"   2. Customer completes payment")
    print(f"   3. Revenue recovered! 🎉")
    print("=" * 60)

if __name__ == "__main__":
    test_payment_failure_flow()
```

**Run it:**
```powershell
cd "C:\Users\sadis\OneDrive\Desktop\Tinko full\tinko-backend-clean"
python test_payment_failure.py
```

---

## 🎯 Method 3: Using cURL (Quick Test)

### Create a transaction and simulate failure:

```bash
# 1. Create transaction
curl -X POST "http://127.0.0.1:8000/_dev/seed/transaction?ref=QUICK_TEST&amount=1999"

# 2. Report failure
curl -X POST "http://127.0.0.1:8000/v1/events/payment_failed" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_ref": "QUICK_TEST",
    "amount": 1999,
    "currency": "INR",
    "gateway": "razorpay",
    "failure_reason": "3D Secure authentication failed"
  }'

# 3. Generate recovery link
curl -X POST "http://127.0.0.1:8000/_dev/seed/recovery_link?ref=QUICK_TEST"

# 4. View events
curl "http://127.0.0.1:8000/v1/events/by_ref/QUICK_TEST"
```

---

## 📊 What to Check in Dashboard

After simulating failures, you should see in your dashboard:
- ✅ **Failed Payments** count increases
- ✅ **Recovery attempts** created
- ✅ **Recovery links** generated
- ✅ **Stats updated** (when you implement analytics endpoints)

---

## 🔍 Common Failure Reasons to Test

Try different failure scenarios:

```python
failure_reasons = [
    "insufficient_funds",
    "card_declined",
    "3ds_failed",
    "network_error",
    "gateway_timeout",
    "invalid_card",
    "card_expired",
    "otp_timeout"
]
```

---

## 🎨 Testing with Real Payment Gateways

### **Razorpay Test Cards:**
- **Success:** `4111 1111 1111 1111`
- **Failure (Insufficient Funds):** `4000 0000 0000 0002`
- **Failure (Card Declined):** `4000 0000 0000 0069`

### **Stripe Test Cards:**
- **Success:** `4242 4242 4242 4242`
- **Failure (Insufficient Funds):** `4000 0000 0000 9995`
- **Failure (Declined):** `4000 0000 0000 0002`

---

## 🚀 Next Steps

1. **Run the test** using any method above
2. **Check the dashboard** to see failed payments
3. **Open the recovery link** to simulate customer retry
4. **Verify the flow** works end-to-end

---

## 💡 Pro Tips

- Use **unique transaction refs** for each test (e.g., with timestamps)
- Test with different **failure reasons** to see classification
- Try different **amounts and currencies**
- Test **expired recovery links** (set ttl_hours to a small value)
- Simulate **multiple failures** for the same transaction

---

**Happy Testing! 🎉**
