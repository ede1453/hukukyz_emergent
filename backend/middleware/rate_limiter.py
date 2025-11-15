"""Rate limiting middleware"""

from fastapi import HTTPException, Request
from datetime import datetime, timedelta
import logging
from typing import Dict, Tuple
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        # Store: {user_id: [(timestamp, count), ...]}
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = asyncio.Lock()
        
        # Rate limits (requests per time window)
        self.limits = {
            "admin": {
                "requests_per_minute": 100,
                "requests_per_hour": 1000
            },
            "avukat": {
                "requests_per_minute": 20,
                "requests_per_hour": 100
            },
            "anonymous": {
                "requests_per_minute": 5,
                "requests_per_hour": 20
            }
        }
    
    async def check_rate_limit(self, user_id: str, user_role: str = "avukat") -> Tuple[bool, str]:
        """
        Check if user has exceeded rate limit
        Returns: (allowed: bool, message: str)
        """
        async with self.lock:
            now = datetime.utcnow()
            
            # Get user's request history
            user_requests = self.requests[user_id]
            
            # Clean old requests (older than 1 hour)
            cutoff_time = now - timedelta(hours=1)
            user_requests = [(ts, count) for ts, count in user_requests if ts > cutoff_time]
            self.requests[user_id] = user_requests
            
            # Count requests in last minute and hour
            minute_ago = now - timedelta(minutes=1)
            requests_last_minute = sum(count for ts, count in user_requests if ts > minute_ago)
            requests_last_hour = sum(count for ts, count in user_requests)
            
            # Get limits for user role
            limits = self.limits.get(user_role, self.limits["avukat"])
            
            # Check limits
            if requests_last_minute >= limits["requests_per_minute"]:
                return False, f"Dakikalık limit aşıldı ({limits['requests_per_minute']} istek/dakika)"
            
            if requests_last_hour >= limits["requests_per_hour"]:
                return False, f"Saatlik limit aşıldı ({limits['requests_per_hour']} istek/saat)"
            
            # Add current request
            user_requests.append((now, 1))
            
            return True, "OK"
    
    async def get_rate_limit_info(self, user_id: str, user_role: str = "avukat") -> dict:
        """Get current rate limit status"""
        async with self.lock:
            now = datetime.utcnow()
            user_requests = self.requests.get(user_id, [])
            
            # Count requests
            minute_ago = now - timedelta(minutes=1)
            hour_ago = now - timedelta(hours=1)
            
            requests_last_minute = sum(count for ts, count in user_requests if ts > minute_ago)
            requests_last_hour = sum(count for ts, count in user_requests if ts > hour_ago)
            
            limits = self.limits.get(user_role, self.limits["avukat"])
            
            return {
                "requests_last_minute": requests_last_minute,
                "requests_last_hour": requests_last_hour,
                "limit_per_minute": limits["requests_per_minute"],
                "limit_per_hour": limits["requests_per_hour"],
                "remaining_minute": max(0, limits["requests_per_minute"] - requests_last_minute),
                "remaining_hour": max(0, limits["requests_per_hour"] - requests_last_hour)
            }


# Global rate limiter instance
rate_limiter = RateLimiter()


async def check_rate_limit(request: Request, user_email: str, user_role: str = "avukat"):
    """Middleware to check rate limits"""
    
    # Admin users are exempt from rate limiting
    if user_role == "admin":
        return
    
    allowed, message = await rate_limiter.check_rate_limit(user_email, user_role)
    
    if not allowed:
        logger.warning(f"Rate limit exceeded for {user_email}: {message}")
        raise HTTPException(
            status_code=429,
            detail=f"Çok fazla istek. {message}. Lütfen biraz bekleyin."
        )
