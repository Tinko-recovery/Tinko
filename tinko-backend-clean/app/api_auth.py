"""
API Key authentication middleware and dependency
Allows customers to authenticate using API keys for programmatic access
"""
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional, List

from .deps import get_db
from .models import User, ApiKey
from .security import verify_password


async def get_api_key_user(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Authenticate user via API key from Authorization header or X-API-Key header
    
    Supports:
    - Authorization: Bearer sk_your_api_key_here
    - X-API-Key: sk_your_api_key_here
    """
    api_key = None
    
    # Try Authorization header first (Bearer format)
    if authorization and authorization.startswith("Bearer sk_"):
        api_key = authorization.replace("Bearer ", "")
    
    # Fallback to X-API-Key header
    elif x_api_key and x_api_key.startswith("sk_"):
        api_key = x_api_key
    
    if not api_key:
        return None
    
    # Find API key in database
    api_key_record = db.query(ApiKey).filter(
        ApiKey.is_active == True
    ).all()
    
    # Check each active API key (hash comparison)
    for record in api_key_record:
        if verify_password(api_key, record.key_hash):
            # Check if key is expired
            if record.expires_at:
                from datetime import datetime
                if datetime.utcnow() > record.expires_at:
                    continue
            
            # Update usage statistics
            record.usage_count += 1
            record.last_used_at = datetime.utcnow()
            db.commit()
            
            # Return the associated user
            return record.user
    
    return None


async def require_api_key(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Require valid API key authentication
    Raises 401 if no valid API key is provided
    """
    user = await get_api_key_user(authorization, x_api_key, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    return user


def require_api_key_scopes(required_scopes: List[str]):
    """
    Dependency factory to require specific API key scopes
    
    Usage:
    @router.post("/sensitive-endpoint")
    def protected_endpoint(
        user: User = Depends(require_api_key_scopes(["write", "admin"]))
    ):
        # Only API keys with 'write' AND 'admin' scopes can access
    """
    async def check_scopes(
        authorization: Optional[str] = Header(None),
        x_api_key: Optional[str] = Header(None),
        db: Session = Depends(get_db)
    ) -> User:
        # First authenticate the API key
        user = await require_api_key(authorization, x_api_key, db)
        
        # Find the API key record to check scopes
        api_key = None
        if authorization and authorization.startswith("Bearer sk_"):
            api_key = authorization.replace("Bearer ", "")
        elif x_api_key and x_api_key.startswith("sk_"):
            api_key = x_api_key
        
        # Find the API key record
        api_key_records = db.query(ApiKey).filter(
            ApiKey.user_id == user.id,
            ApiKey.is_active == True
        ).all()
        
        api_key_record = None
        for record in api_key_records:
            if verify_password(api_key, record.key_hash):
                api_key_record = record
                break
        
        if not api_key_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key not found"
            )
        
        # Check if API key has required scopes
        user_scopes = api_key_record.scopes or []
        missing_scopes = [scope for scope in required_scopes if scope not in user_scopes]
        
        if missing_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API key missing required scopes: {missing_scopes}",
                headers={"X-Required-Scopes": ", ".join(required_scopes)}
            )
        
        return user
    
    return check_scopes


# Utility function to check current user's API key capabilities
def get_current_api_key_info(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[dict]:
    """
    Get information about the current API key being used
    Returns None if not using API key authentication
    """
    api_key = None
    if authorization and authorization.startswith("Bearer sk_"):
        api_key = authorization.replace("Bearer ", "")
    elif x_api_key and x_api_key.startswith("sk_"):
        api_key = x_api_key
    
    if not api_key:
        return None
    
    # Find API key record
    api_key_records = db.query(ApiKey).filter(ApiKey.is_active == True).all()
    
    for record in api_key_records:
        if verify_password(api_key, record.key_hash):
            return {
                "key_name": record.key_name,
                "scopes": record.scopes,
                "usage_count": record.usage_count,
                "last_used_at": record.last_used_at,
                "expires_at": record.expires_at
            }
    
    return None