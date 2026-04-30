"""
Price Cache - In-memory caching with TTL

Provides simple in-memory caching for pricing data to avoid repeated API calls.
Cache entries expire after a configurable TTL (default: 12 hours).
"""

import logging
import time
from typing import Optional, Any, Dict

logger = logging.getLogger(__name__)


class PriceCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, ttl_seconds: int = 43200):
        """
        Initialize cache.
        
        Args:
            ttl_seconds: Time-to-live for cache entries in seconds (default: 12 hours)
        """
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        logger.info(f"PriceCache initialized with TTL={ttl_seconds}s ({ttl_seconds/3600:.1f}h)")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        current_time = time.time()
        
        # Check if expired
        if current_time - entry["timestamp"] > self.ttl_seconds:
            logger.debug(f"Cache miss (expired): {key}")
            del self.cache[key]
            return None
        
        logger.debug(f"Cache hit: {key}")
        return entry["value"]
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self.cache[key] = {
            "value": value,
            "timestamp": time.time()
        }
        logger.debug(f"Cache set: {key}")
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def size(self) -> int:
        """Get number of cached entries"""
        return len(self.cache)
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time - entry["timestamp"] > self.ttl_seconds
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
