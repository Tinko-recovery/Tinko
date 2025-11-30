import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_payment_failure_flow():
    print("=" * 60)
    print("TINKO PAYMENT FAILURE TEST")
    print("=" * 60)
    
    # Step 1: Create a test transaction
    transaction_ref = f"TEST_{int(time.time())}"
    print(f"\nStep 1: Creating transaction ({transaction_ref})...")
    
    transaction_response = requests.post(
        f"{BASE_URL}/_dev/seed/transaction",
        params={
            "ref": transaction_ref,
            "amount": 2999,
            "currency": "INR"
        }
    )
    
    if transaction_response.status_code == 200:
        print("SUCCESS: Transaction created")
        txn_data = transaction_response.json()
        print(f"  Transaction ID: {txn_data['id']}")
        print(f"  Amount: Rs.{txn_data['amount']}/100 = Rs.{txn_data['amount']/100}")
    else:
        print(f"FAILED: {transaction_response.text}")
        return
    
    # Step 2: Simulate payment failure
    print(f"\nStep 2: Simulating payment failure...")
    
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
            }
        }
    )
    
    if failure_response.status_code == 201:
        failure_data = failure_response.json()
        print("SUCCESS: Payment failure recorded")
        print(f"  Failure Event ID: {failure_data['id']}")
    else:
        print(f"FAILED: {failure_response.text}")
        return
    
    # Step 3: Generate recovery link
    print(f"\nStep 3: Generating recovery link...")
    
    recovery_response = requests.post(
        f"{BASE_URL}/_dev/seed/recovery_link",
        params={
            "ref": transaction_ref,
            "ttl_hours": 24.0
        }
    )
    
    if recovery_response.status_code == 200:
        recovery_data = recovery_response.json()
        print("SUCCESS: Recovery link generated")
        print(f"  Recovery URL: {recovery_data['url']}")
        print(f"  Token: {recovery_data['token']}")
        print(f"  Expires: {recovery_data['expires_at']}")
    else:
        print(f"FAILED: {recovery_response.text}")
        return
    
    # Step 4: Verify events
    print(f"\nStep 4: Verifying failure events...")
    
    events_response = requests.get(
        f"{BASE_URL}/v1/events/by_ref/{transaction_ref}"
    )
    
    if events_response.status_code == 200:
        events = events_response.json()
        print(f"SUCCESS: Found {len(events)} failure event(s)")
        for event in events:
            print(f"  - Event #{event['id']}: {event['reason']}")
            print(f"    Gateway: {event['gateway']}")
    else:
        print(f"FAILED: {events_response.text}")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST COMPLETE!")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  Transaction Ref: {transaction_ref}")
    print(f"  Recovery URL: {recovery_data['url']}")
    print(f"\nNext steps:")
    print(f"  1. Open the recovery URL in your browser")
    print(f"  2. Customer completes payment")
    print(f"  3. Revenue recovered!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_payment_failure_flow()
    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to backend server!")
        print("  Make sure the server is running at http://127.0.0.1:8000")
    except Exception as e:
        print(f"\nERROR: {str(e)}")
