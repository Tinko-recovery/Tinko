def calculate_fee(amount: int, percent: float, fixed: int) -> int:
    """
    Calculate service fee based on amount, percentage, and fixed fee.
    
    Args:
        amount: Total transaction amount in smallest currency unit (e.g., paise)
        percent: Percentage fee (e.g., 2.0 for 2%)
        fixed: Fixed fee in smallest currency unit (e.g., 30 for ₹0.30)
        
    Returns:
        Total fee in smallest currency unit (integer)
    """
    if amount is None or amount < 0:
        return 0
        
    percent_fee = int(amount * (percent / 100.0))
    total_fee = percent_fee + fixed
    
    # Cap fee at amount? Usually not, but good to be safe against negative net
    if total_fee > amount:
        # In reality, we might charge more than amount if fixed fee is high, 
        # but for net calculation we can't pay out negative.
        # For now, just return the calculated fee.
        pass
        
    return total_fee
