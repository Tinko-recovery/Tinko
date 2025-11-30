"""
Feature flags for STEALTH-TINKO
"""

def flag(name: str, default: bool = False) -> bool:
    """
    Simple feature flag function
    In development, returns the default value
    """
    return default