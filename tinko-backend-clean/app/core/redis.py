"""
Redis configuration for OTP storage and caching
"""
import redis.asyncio as redis
from ..config import settings
import logging

logger = logging.getLogger(__name__)

class RedisManager:
    def __init__(self):
        self.redis_client = None
        self.is_available = False
    
    async def connect(self):
        """Initialize Redis connection"""
        try:
            if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
            else:
                # Default local Redis configuration
                self.redis_client = redis.Redis(
                    host=getattr(settings, 'REDIS_HOST', 'localhost'),
                    port=getattr(settings, 'REDIS_PORT', 6379),
                    db=getattr(settings, 'REDIS_DB', 0),
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
            
            # Test connection
            await self.redis_client.ping()
            self.is_available = True
            logger.info("Redis connection established successfully")
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Falling back to database storage.")
            self.is_available = False
            self.redis_client = None
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    async def set_otp(self, key: str, value: str, expire_seconds: int = 300):
        """Store OTP with expiration"""
        try:
            if self.is_available and self.redis_client:
                await self.redis_client.setex(key, expire_seconds, value)
                logger.debug(f"OTP stored in Redis: {key}")
                return True
        except Exception as e:
            logger.warning(f"Failed to store OTP in Redis: {e}")
            self.is_available = False
        
        return False
    
    async def get_otp(self, key: str) -> str:
        """Retrieve OTP from Redis"""
        try:
            if self.is_available and self.redis_client:
                value = await self.redis_client.get(key)
                if value:
                    logger.debug(f"OTP retrieved from Redis: {key}")
                return value
        except Exception as e:
            logger.warning(f"Failed to retrieve OTP from Redis: {e}")
            self.is_available = False
        
        return None
    
    async def delete_otp(self, key: str):
        """Delete OTP from Redis"""
        try:
            if self.is_available and self.redis_client:
                await self.redis_client.delete(key)
                logger.debug(f"OTP deleted from Redis: {key}")
                return True
        except Exception as e:
            logger.warning(f"Failed to delete OTP from Redis: {e}")
        
        return False
    
    async def increment_attempts(self, key: str, expire_seconds: int = 3600) -> int:
        """Increment attempt counter"""
        try:
            if self.is_available and self.redis_client:
                # Use a pipeline for atomic operations
                pipe = self.redis_client.pipeline()
                pipe.incr(f"{key}:attempts")
                pipe.expire(f"{key}:attempts", expire_seconds)
                results = await pipe.execute()
                return results[0]
        except Exception as e:
            logger.warning(f"Failed to increment attempts in Redis: {e}")
        
        return 0

# Global Redis manager instance
redis_manager = RedisManager()

# Convenience functions for backward compatibility
async def get_redis():
    """Get Redis client instance"""
    if not redis_manager.is_available:
        await redis_manager.connect()
    return redis_manager.redis_client

async def set_otp(key: str, value: str, expire_seconds: int = 300):
    """Store OTP with expiration"""
    return await redis_manager.set_otp(key, value, expire_seconds)

async def get_otp(key: str):
    """Retrieve OTP"""
    return await redis_manager.get_otp(key)

async def delete_otp(key: str):
    """Delete OTP"""
    return await redis_manager.delete_otp(key)