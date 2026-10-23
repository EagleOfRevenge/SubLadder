"""
game/auth/cache.py — Profile data caching with timestamp management
Caches online profile data to reduce server requests and enable offline display.
"""

import time
from typing import Optional


class ProfileCache:
    """Cache for online profile data with timestamp-based refresh."""
    
    def __init__(self, cache_duration: int = 300):
        """
        Initialize profile cache.
        
        Args:
            cache_duration: How long to cache profile data (seconds, default: 5 min)
        """
        self.cache_duration = cache_duration
        self.cache = {}  # {user_id: {"data": {...}, "timestamp": time.time()}}
        self.syncing = set()  # Track profiles currently being synced
    
    def get(self, user_id: str) -> Optional[dict]:
        """
        Get cached profile data if valid (not expired).
        
        Args:
            user_id: Online user ID
            
        Returns:
            Profile dict if valid, None if expired or not cached
        """
        if user_id not in self.cache:
            return None
        
        cached = self.cache[user_id]
        age = time.time() - cached["timestamp"]
        
        if age > self.cache_duration:
            # Cache expired, keep data but return None to signal refresh needed
            return None
        
        return cached["data"]
    
    def get_stale(self, user_id: str) -> Optional[dict]:
        """
        Get cached profile data even if expired (for fallback display).
        
        Args:
            user_id: Online user ID
            
        Returns:
            Profile dict if cached (any age), None if not cached
        """
        if user_id not in self.cache:
            return None
        
        return self.cache[user_id]["data"]
    
    def set(self, user_id: str, profile_data: dict) -> None:
        """
        Store profile data in cache with current timestamp.
        
        Args:
            user_id: Online user ID
            profile_data: Profile dict to cache
        """
        self.cache[user_id] = {
            "data": profile_data,
            "timestamp": time.time()
        }
    
    def is_expired(self, user_id: str) -> bool:
        """Check if cache entry is expired."""
        if user_id not in self.cache:
            return True
        
        age = time.time() - self.cache[user_id]["timestamp"]
        return age > self.cache_duration
    
    def is_syncing(self, user_id: str) -> bool:
        """Check if profile is currently being synced."""
        return user_id in self.syncing
    
    def start_sync(self, user_id: str) -> None:
        """Mark profile as syncing to prevent concurrent fetches."""
        self.syncing.add(user_id)
    
    def end_sync(self, user_id: str) -> None:
        """Mark profile as done syncing."""
        self.syncing.discard(user_id)
    
    def clear(self, user_id: Optional[str] = None) -> None:
        """
        Clear cache entry or all cache.
        
        Args:
            user_id: Specific user to clear, or None to clear all
        """
        if user_id:
            self.cache.pop(user_id, None)
            self.syncing.discard(user_id)
        else:
            self.cache.clear()
            self.syncing.clear()
    
    def get_last_updated(self, user_id: str) -> Optional[float]:
        """Get timestamp of last cache update."""
        if user_id not in self.cache:
            return None
        
        return self.cache[user_id]["timestamp"]
