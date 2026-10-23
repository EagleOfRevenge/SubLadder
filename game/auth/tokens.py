"""
game/auth/tokens.py — Token management for online profiles
Store, load, and validate JWT tokens.
"""

import json
import os
import time


class TokenManager:
    """Manage JWT tokens for online profiles."""
    
    def __init__(self, data_dict):
        """
        Initialize with reference to the game data dict.
        data_dict should have structure: {"auth": {"tokens": {}, "sessions": {}}}
        """
        self.data = data_dict
        self._ensure_auth_structure()
    
    def _ensure_auth_structure(self):
        """Ensure auth structure exists in data dict."""
        if "auth" not in self.data:
            self.data["auth"] = {"tokens": {}, "sessions": {}}
        if "tokens" not in self.data["auth"]:
            self.data["auth"]["tokens"] = {}
        if "sessions" not in self.data["auth"]:
            self.data["auth"]["sessions"] = {}
    
    def store_token(self, profile_name: str, token: str, expires_at: int = None):
        """Store JWT token for a profile."""
        self._ensure_auth_structure()
        self.data["auth"]["tokens"][profile_name] = token
        
        if expires_at:
            self.data["auth"]["sessions"][profile_name] = {
                "token": token,
                "expires_at": expires_at,
            }
    
    def get_token(self, profile_name: str) -> str:
        """Get stored JWT token for a profile."""
        self._ensure_auth_structure()
        token = self.data["auth"]["tokens"].get(profile_name)
        
        # Check if token is expired
        session = self.data["auth"]["sessions"].get(profile_name, {})
        if session.get("expires_at") and session["expires_at"] < time.time():
            self.delete_token(profile_name)
            return None
        
        return token
    
    def delete_token(self, profile_name: str):
        """Delete stored token for a profile."""
        self._ensure_auth_structure()
        self.data["auth"]["tokens"].pop(profile_name, None)
        self.data["auth"]["sessions"].pop(profile_name, None)
    
    def has_token(self, profile_name: str) -> bool:
        """Check if profile has a valid token."""
        return self.get_token(profile_name) is not None
    
    def clear_all(self):
        """Clear all tokens (for logout)."""
        self.data["auth"]["tokens"] = {}
        self.data["auth"]["sessions"] = {}
