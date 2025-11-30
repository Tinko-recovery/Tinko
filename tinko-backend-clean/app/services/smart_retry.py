from datetime import datetime, timedelta

def calculate_smart_delays(strategy: str, configured_delays: list[int]) -> list[int]:
    """
    Calculate delay minutes based on strategy.
    """
    if strategy == "payday":
        return [_minutes_until_next_payday()]
    
    # Default to configured delays (e.g. [0, 5] for network)
    return configured_delays or [0]

def _minutes_until_next_payday() -> int:
    now = datetime.utcnow()
    year = now.year
    month = now.month
    
    # Candidates: 5th and 15th of current month
    candidates = [
        datetime(year, month, 5),
        datetime(year, month, 15)
    ]
    
    # Candidates: 5th and 15th of next month
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
        
    candidates.append(datetime(next_year, next_month, 5))
    candidates.append(datetime(next_year, next_month, 15))
    
    # Find first candidate in the future
    for cand in candidates:
        if cand > now:
            diff = cand - now
            return int(diff.total_seconds() / 60)
            
    # Fallback (shouldn't happen)
    return 24 * 60 # 1 day
