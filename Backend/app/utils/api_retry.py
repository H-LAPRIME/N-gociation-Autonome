"""
API Retry Utility with Exponential Backoff
-------------------------------------------
Provides retry logic for API calls that may hit rate limits.
"""
import asyncio
import logging
from typing import Any, Callable, TypeVar, Optional
from functools import wraps
import time

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RateLimitError(Exception):
    """Exception raised when API rate limit is exceeded."""
    pass


async def retry_with_exponential_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    on_retry: Optional[Callable] = None
) -> Any:
    """
    Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Add randomization to delay
        on_retry: Callback function to call on each retry
        
    Returns:
        Result of the function call
        
    Raises:
        Last exception if all retries fail
    """
    import random
    
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            # Try to execute the function
            result = await func()
            
            # Success! Reset rate limit tracking if needed
            if attempt > 0:
                logger.info(f"✅ Success after {attempt} retries")
            
            return result
            
        except Exception as e:
            last_exception = e
            error_msg = str(e).lower()
            
            # Check if it's a rate limit error
            is_rate_limit = (
                "rate limit" in error_msg or 
                "429" in error_msg or
                "too many requests" in error_msg or
                "rate_limited" in error_msg
            )
            
            # If it's not a rate limit error, don't retry
            if not is_rate_limit and attempt == 0:
                logger.error(f"❌ Non-retryable error: {e}")
                raise
            
            # If we've exhausted retries
            if attempt >= max_retries:
                logger.error(f"❌ Max retries ({max_retries}) exceeded. Last error: {e}")
                raise
            
            # Calculate delay with exponential backoff
            current_delay = min(delay * (exponential_base ** attempt), max_delay)
            
            # Add jitter to prevent thundering herd
            if jitter:
                current_delay = current_delay * (0.5 + random.random())
            
            # Log the retry
            logger.warning(
                f"⚠️ Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                f"Retrying in {current_delay:.2f}s..."
            )
            
            # Call retry callback if provided
            if on_retry:
                try:
                    await on_retry(attempt, e, current_delay)
                except Exception as callback_error:
                    logger.error(f"Error in retry callback: {callback_error}")
            
            # Wait before retrying
            await asyncio.sleep(current_delay)
    
    # This should never be reached, but just in case
    raise last_exception


def async_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
):
    """
    Decorator for async functions to add retry logic with exponential backoff.
    
    Usage:
        @async_retry(max_retries=3, initial_delay=2.0)
        async def my_api_call():
            # Your API call here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async def _execute():
                return await func(*args, **kwargs)
            
            return await retry_with_exponential_backoff(
                _execute,
                max_retries=max_retries,
                initial_delay=initial_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                jitter=jitter
            )
        
        return wrapper
    return decorator


class RateLimiter:
    """
    Simple rate limiter to prevent exceeding API limits.
    Uses token bucket algorithm.
    """
    def __init__(self, rate: float, capacity: int):
        """
        Args:
            rate: Number of tokens added per second
            capacity: Maximum number of tokens in bucket
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens from the bucket.
        Waits if not enough tokens available.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            True when tokens are acquired
        """
        async with self._lock:
            # Refill tokens based on time elapsed
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(
                self.capacity,
                self.tokens + (elapsed * self.rate)
            )
            self.last_update = now
            
            # If we don't have enough tokens, wait
            if self.tokens < tokens:
                wait_time = (tokens - self.tokens) / self.rate
                logger.info(f"⏳ Rate limiter: waiting {wait_time:.2f}s for tokens")
                await asyncio.sleep(wait_time)
                self.tokens = 0
                self.last_update = time.time()
            else:
                self.tokens -= tokens
            
            return True


# Global rate limiter for Mistral API
# Increased to 2 requests per second with capacity of 10 for better throughput
mistral_rate_limiter = RateLimiter(rate=2.0, capacity=10)
