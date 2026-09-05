import asyncio
import time
import logging
from collections import deque
from typing import Optional, Dict, Any, Callable
from app.core.config import settings

logger = logging.getLogger("truthlens.gemini")

class GeminiApiException(Exception):
    """Base exception for Gemini API errors."""
    def __init__(self, code: str, message: str, status_code: int = 500, details: Optional[str] = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or message
        super().__init__(self.message)

class GeminiRateLimitException(GeminiApiException):
    def __init__(self, message: str = "Gemini rate limit reached. Please wait a moment before trying again.", details: Optional[str] = None):
        super().__init__(code="API_RATE_LIMIT", message=message, status_code=429, details=details)

class GeminiNotFoundException(GeminiApiException):
    def __init__(self, message: str = "Gemini model or resource endpoint not found.", details: Optional[str] = None):
        super().__init__(code="API_NOT_FOUND", message=message, status_code=404, details=details)

class GeminiAuthException(GeminiApiException):
    def __init__(self, message: str = "Invalid Google API key or permission denied.", details: Optional[str] = None):
        super().__init__(code="API_AUTH_ERROR", message=message, status_code=401, details=details)

class GeminiRateLimiter:
    """
    In-memory rate limiter and concurrency controller for Google Gemini API calls.
    Enforces safe free-tier RPM limits, serializes concurrent calls, and provides
    exponential backoff for transient 429s.
    """
    _timestamps: deque = deque()
    _lock: asyncio.Lock = asyncio.Lock()
    _last_call_time: float = 0.0

    @classmethod
    async def acquire(cls):
        """Ensures request spacing and sliding-window RPM limit adherence."""
        now = time.time()
        
        # 1. Purge timestamps older than 60 seconds
        while cls._timestamps and cls._timestamps[0] <= now - 60.0:
            cls._timestamps.popleft()

        # 2. Check if sliding window is full
        if len(cls._timestamps) >= settings.GEMINI_MAX_RPM:
            oldest = cls._timestamps[0]
            wait_time = max(0.1, 60.0 - (now - oldest) + 0.1)
            if wait_time <= 4.0:
                logger.warning(f"[Gemini RateLimiter] Approaching RPM limit ({len(cls._timestamps)}/{settings.GEMINI_MAX_RPM}). Waiting {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                # Re-purge
                now = time.time()
                while cls._timestamps and cls._timestamps[0] <= now - 60.0:
                    cls._timestamps.popleft()
            else:
                raise GeminiRateLimitException(
                    message="Verification service is currently rate-limited by upstream API. Please retry in a few seconds.",
                    details=f"Local client rate limiter blocked request: {len(cls._timestamps)} calls in past 60s (limit: {settings.GEMINI_MAX_RPM} RPM)."
                )

        # 3. Enforce minimum inter-call delay spacing (e.g. 500ms)
        elapsed_since_last = now - cls._last_call_time
        if elapsed_since_last < settings.GEMINI_MIN_INTER_CALL_DELAY_SEC:
            spacing_wait = settings.GEMINI_MIN_INTER_CALL_DELAY_SEC - elapsed_since_last
            await asyncio.sleep(spacing_wait)

        # Record this timestamp
        current_time = time.time()
        cls._timestamps.append(current_time)
        cls._last_call_time = current_time

    @classmethod
    async def execute_with_retry(cls, call_fn: Callable, *args, **kwargs) -> Any:
        """
        Executes a Gemini API call with strict concurrency serialization,
        rate-limiting, and exponential backoff for 429 errors only.
        """
        async with cls._lock:
            await cls.acquire()

            retries = settings.GEMINI_MAX_RETRIES
            backoff = settings.GEMINI_INITIAL_BACKOFF_SEC

            for attempt in range(retries + 1):
                try:
                    # Run the sync generate_content in a threadpool so it doesn't block the event loop
                    result = await asyncio.to_thread(call_fn, *args, **kwargs)
                    return result
                except Exception as e:
                    err_str = str(e)
                    err_lower = err_str.lower()
                    logger.error(f"[Gemini API Call Error] Attempt {attempt+1}/{retries+1}: {err_str}")

                    # 1. Check for 404 Not Found (Invalid Model / Resource) -> Fail fast!
                    if "404" in err_str or "not found" in err_lower:
                        raise GeminiNotFoundException(
                            message=f"Gemini model or endpoint not found ({settings.GEMINI_MODEL}).",
                            details=err_str
                        )

                    # 2. Check for 401 / 403 (Auth / Invalid Key) -> Fail fast!
                    if "401" in err_str or "403" in err_str or "api_key_invalid" in err_lower or "permission_denied" in err_lower:
                        raise GeminiAuthException(
                            message="Google API key is invalid or lacks necessary Gemini permissions.",
                            details=err_str
                        )

                    # 3. Check for 429 Too Many Requests / Resource Exhausted -> Backoff & Retry
                    if "429" in err_str or "resource_exhausted" in err_lower or "too many requests" in err_lower or "quota" in err_lower:
                        if attempt < retries:
                            # Try to extract retry-after if present
                            retry_match = None
                            logger.warning(f"[Gemini 429 RateLimit] Backing off for {backoff:.1f}s before retry {attempt+1}/{retries}...")
                            await asyncio.sleep(backoff)
                            backoff *= 2.0
                            continue
                        else:
                            raise GeminiRateLimitException(
                                message="Gemini API rate limit exceeded. Please wait a moment before trying again.",
                                details=f"Upstream 429 Too Many Requests after {retries} retries: {err_str}"
                            )

                    # 4. Check for transient 503 / 500 server errors -> Backoff & Retry
                    if "503" in err_str or "unavailable" in err_lower or "deadline" in err_lower:
                        if attempt < retries:
                            logger.warning(f"[Gemini 503/Timeout] Backing off for {backoff:.1f}s before retry {attempt+1}/{retries}...")
                            await asyncio.sleep(backoff)
                            backoff *= 2.0
                            continue
                        else:
                            raise GeminiApiException(
                                code="API_SERVICE_UNAVAILABLE",
                                message="Google Gemini service is temporarily unavailable. Please retry in a moment.",
                                status_code=503,
                                details=err_str
                            )

                    # For any other unhandled exception, raise directly
                    raise GeminiApiException(
                        code="API_ERROR",
                        message="Error communicating with Google Gemini API.",
                        status_code=500,
                        details=err_str
                    )
