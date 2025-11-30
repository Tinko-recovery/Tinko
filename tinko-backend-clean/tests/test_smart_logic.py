import unittest
from datetime import datetime
from app.rules import classify_failure, next_retry_options
from app.services.smart_retry import calculate_smart_delays

class TestSmartLogic(unittest.TestCase):
    def test_classification_funds(self):
        # Razorpay insufficient funds
        cat = classify_failure("RZP001_INSUFFICIENT_FUNDS", "Balance low")
        self.assertEqual(cat, "funds")
        
        opts = next_retry_options(cat)
        self.assertEqual(opts["schedule_strategy"], "payday")
        
    def test_classification_network(self):
        # Network error
        cat = classify_failure("network_error", "Timeout")
        self.assertEqual(cat, "network")
        
        opts = next_retry_options(cat)
        self.assertEqual(opts["schedule_strategy"], "network_retry")
        self.assertEqual(opts["delays_minutes"], [0, 5])
        
    def test_smart_delay_payday(self):
        # Strategy: payday
        delays = calculate_smart_delays("payday", [])
        self.assertEqual(len(delays), 1)
        self.assertGreater(delays[0], 0) # Should be in future
        print(f"Payday delay: {delays[0]} minutes")
        
    def test_smart_delay_network(self):
        # Strategy: network_retry
        delays = calculate_smart_delays("network_retry", [0, 5])
        self.assertEqual(delays, [0, 5])

if __name__ == "__main__":
    unittest.main()
