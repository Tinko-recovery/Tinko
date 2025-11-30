from __future__ import annotations

from typing import Any, Dict, Optional

from .. import rules


def classify_event(code: Optional[str], message: Optional[str]) -> Dict[str, Any]:
    """
    Contract:
    - Inputs: gateway failure code (string|None), message (string|None)
    - Output: { category: str, recommendation: str, alt: list[str], cooldown_seconds?: int }
    - Errors: never raises; unknown maps to sensible defaults
    """
    category = rules.classify_failure(code, message)
    options = rules.next_retry_options(category)

    # Map hardness per spec
    # - insufficient_funds -> soft
    # - issuer_declined -> hard
    # - auth_timeout -> soft
    # - 3ds_timeout -> soft (maps to auth_timeout in rules)
    # - unknown -> soft by default
    hardness = "soft"
    if category in ("issuer_decline",):
        hardness = "hard"

    # Explicit code overrides for clarity
    if code == "insufficient_funds":
        hardness = "soft"
    elif code == "issuer_declined":
        hardness = "hard"
    elif code in ("auth_timeout", "3ds_timeout"):
        hardness = "soft"

    payload: Dict[str, Any] = {
        "category": category,
        **options,
        "hardness": hardness,
    }
    return payload
