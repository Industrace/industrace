# backend/services/rate_limiter.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from typing import Optional
from app.config import settings
import time
import logging

logger = logging.getLogger(__name__)

# Initialize the rate limiter
limiter = Limiter(key_func=get_remote_address)

# Redis client (lazy initialization)
_redis_client = None
_redis_available = False


def get_redis_client():
    """Get or create Redis client with lazy initialization"""
    global _redis_client, _redis_available
    
    if not settings.REDIS_ENABLED or not settings.RATE_LIMIT_ENABLED:
        return None
    
    if _redis_client is not None:
        return _redis_client if _redis_available else None
    
    try:
        from redis import Redis
        from redis.exceptions import ConnectionError as RedisConnectionError
        
        _redis_client = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=False,  # We need bytes for incr operations
            socket_connect_timeout=2,
            socket_timeout=2,
            retry_on_timeout=True,
        )
        # Test connection
        _redis_client.ping()
        _redis_available = True
        logger.info("Redis connected successfully for rate limiting")
        return _redis_client
    except (RedisConnectionError, ImportError, Exception) as e:
        logger.warning(f"Redis not available for rate limiting: {e}. Using in-memory fallback.")
        _redis_available = False
        _redis_client = None
        return None


def get_rate_limit_for_api_key(api_key) -> str:
    """Determines the rate limit for a specific API Key"""
    if api_key and hasattr(api_key, "rate_limit"):
        return api_key.rate_limit
    return settings.RATE_LIMIT_DEFAULT


def rate_limit_by_api_key(api_key=None):
    """
    Decorator to apply rate limiting based on API Key.
    If there's no API Key, uses the default limit.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Determine the rate limit
            rate_limit = get_rate_limit_for_api_key(api_key)

            # Apply the rate limiting
            return limiter.limit(rate_limit)(func)(*args, **kwargs)

        return wrapper

    return decorator


def get_client_identifier(request: Request, api_key=None) -> str:
    """
    Generates a unique identifier for the client.
    If there's an API Key, uses that, otherwise uses the IP.
    """
    if api_key:
        return f"api_key:{api_key.id}"
    return f"ip:{get_remote_address(request)}"


def check_rate_limit_strict(request: Request, rate_limit_str: str) -> bool:
    """
    Checks rate limit with a specific limit (for login, etc.)
    """
    if not settings.RATE_LIMIT_ENABLED:
        return True
    
    identifier = f"ip:{get_remote_address(request)}"
    
    # Parse rate limit
    try:
        limit_str, period = rate_limit_str.split("/")
        limit = int(limit_str)
    except (ValueError, AttributeError):
        logger.warning(f"Invalid rate limit format: {rate_limit_str}. Using default.")
        limit = 10
        period = "minute"
    
    period_seconds = 3600 if period == "hour" else 60 if period == "minute" else 1
    
    redis_client = get_redis_client()
    
    if redis_client:
        try:
            key = f"rate_limit_strict:{identifier}"
            current = redis_client.incr(key)
            
            if current == 1:
                redis_client.expire(key, period_seconds)
            
            if current > limit:
                logger.warning(f"Strict rate limit exceeded for {identifier}: {current}/{limit} {period}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Redis error in strict rate limiting: {e}. Falling back to in-memory.")
    
    # In-memory fallback
    if not hasattr(check_rate_limit_strict, '_memory_store'):
        check_rate_limit_strict._memory_store = {}
        check_rate_limit_strict._memory_timestamps = {}
    
    current_time = time.time()
    store = check_rate_limit_strict._memory_store
    timestamps = check_rate_limit_strict._memory_timestamps
    
    if identifier in timestamps:
        if current_time - timestamps[identifier] > period_seconds:
            store[identifier] = 0
            timestamps[identifier] = current_time
    
    if identifier not in store:
        store[identifier] = 0
        timestamps[identifier] = current_time
    
    store[identifier] += 1
    
    if store[identifier] > limit:
        logger.warning(f"Strict rate limit exceeded (in-memory) for {identifier}: {store[identifier]}/{limit} {period}")
        return False
    
    return True


def check_rate_limit(request: Request, api_key=None) -> bool:
    """
    Checks if the client has exceeded the rate limit.
    Returns True if the limit has not been exceeded.
    """
    if not settings.RATE_LIMIT_ENABLED:
        return True
    
    identifier = get_client_identifier(request, api_key)
    rate_limit = get_rate_limit_for_api_key(api_key)
    
    # Parse rate limit (e.g., "100/hour", "10/minute")
    try:
        limit_str, period = rate_limit.split("/")
        limit = int(limit_str)
    except (ValueError, AttributeError):
        logger.warning(f"Invalid rate limit format: {rate_limit}. Using default.")
        limit = 100
        period = "hour"
    
    # Convert period to seconds
    period_seconds = 3600 if period == "hour" else 60 if period == "minute" else 1
    
    redis_client = get_redis_client()
    
    if redis_client:
        # Use Redis for distributed rate limiting
        try:
            key = f"rate_limit:{identifier}"
            current = redis_client.incr(key)
            
            # Set expiration on first request
            if current == 1:
                redis_client.expire(key, period_seconds)
            
            # Check if limit exceeded
            if current > limit:
                logger.warning(f"Rate limit exceeded for {identifier}: {current}/{limit} {period}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Redis error in rate limiting: {e}. Falling back to in-memory.")
            # Fall through to in-memory fallback
    
    # In-memory fallback (per-process, not distributed)
    # This is a simple implementation for when Redis is not available
    if not hasattr(check_rate_limit, '_memory_store'):
        check_rate_limit._memory_store = {}
        check_rate_limit._memory_timestamps = {}
    
    current_time = time.time()
    store = check_rate_limit._memory_store
    timestamps = check_rate_limit._memory_timestamps
    
    # Clean old entries
    if identifier in timestamps:
        if current_time - timestamps[identifier] > period_seconds:
            store[identifier] = 0
            timestamps[identifier] = current_time
    
    # Increment counter
    if identifier not in store:
        store[identifier] = 0
        timestamps[identifier] = current_time
    
    store[identifier] += 1
    
    # Check limit
    if store[identifier] > limit:
        logger.warning(f"Rate limit exceeded (in-memory) for {identifier}: {store[identifier]}/{limit} {period}")
        return False
    
    return True


def get_remaining_requests(request: Request, api_key=None) -> dict:
    """
    Returns information about remaining rate limits.
    """
    identifier = get_client_identifier(request, api_key)
    rate_limit = get_rate_limit_for_api_key(api_key)
    
    # Parse rate limit
    try:
        limit_str, period = rate_limit.split("/")
        limit = int(limit_str)
    except (ValueError, AttributeError):
        limit = 100
        period = "hour"
    
    period_seconds = 3600 if period == "hour" else 60 if period == "minute" else 1
    
    redis_client = get_redis_client()
    
    if redis_client:
        try:
            key = f"rate_limit:{identifier}"
            current = redis_client.get(key)
            current = int(current) if current else 0
            
            # Get TTL to calculate reset time
            ttl = redis_client.ttl(key)
            reset_time = int(time.time()) + (ttl if ttl > 0 else period_seconds)
            
            remaining = max(0, limit - current)
            
            return {
                "limit": limit,
                "period": period,
                "remaining": remaining,
                "reset_time": reset_time,
            }
        except Exception as e:
            logger.error(f"Redis error getting remaining requests: {e}")
            # Fall through to in-memory fallback
    
    # In-memory fallback
    if not hasattr(check_rate_limit, '_memory_store'):
        current = 0
        reset_time = int(time.time()) + period_seconds
    else:
        store = check_rate_limit._memory_store
        timestamps = check_rate_limit._memory_timestamps
        current = store.get(identifier, 0)
        reset_time = int(timestamps.get(identifier, time.time()) + period_seconds)
    
    remaining = max(0, limit - current)
    
    return {
        "limit": limit,
        "period": period,
        "remaining": remaining,
        "reset_time": reset_time,
    }


def add_rate_limit_headers(response: Response, request: Request, api_key=None):
    """Adds rate limiting headers to the response"""
    info = get_remaining_requests(request, api_key)

    response.headers["X-RateLimit-Limit"] = str(info["limit"])
    response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
    response.headers["X-RateLimit-Reset"] = str(info["reset_time"])

    return response


def add_rate_limit_headers_strict(response: Response, request: Request, rate_limit_str: str):
    """Adds rate limiting headers with a specific limit (for login, etc.)"""
    identifier = f"ip:{get_remote_address(request)}"
    
    # Parse rate limit
    try:
        limit_str, period = rate_limit_str.split("/")
        limit = int(limit_str)
    except (ValueError, AttributeError):
        limit = 10
        period = "minute"
    
    period_seconds = 3600 if period == "hour" else 60 if period == "minute" else 1
    
    redis_client = get_redis_client()
    
    if redis_client:
        try:
            key = f"rate_limit_strict:{identifier}"
            current = redis_client.get(key)
            current = int(current) if current else 0
            
            ttl = redis_client.ttl(key)
            reset_time = int(time.time()) + (ttl if ttl > 0 else period_seconds)
            
            remaining = max(0, limit - current)
            
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_time)
            return response
        except Exception:
            pass
    
    # In-memory fallback
    if hasattr(check_rate_limit_strict, '_memory_store'):
        store = check_rate_limit_strict._memory_store
        timestamps = check_rate_limit_strict._memory_timestamps
        current = store.get(identifier, 0)
        reset_time = int(timestamps.get(identifier, time.time()) + period_seconds)
    else:
        current = 0
        reset_time = int(time.time()) + period_seconds
    
    remaining = max(0, limit - current)
    
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset_time)
    
    return response
