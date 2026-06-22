"""Error handling and monitoring utilities."""
import functools
import time
from typing import Callable, Any, Optional
from fastapi import HTTPException
from pydantic import ValidationError

from logger import get_logger

logger = get_logger("error_handler")


class APIError(HTTPException):
    """Base API error class."""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        **extra_info
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.extra_info = extra_info


class ValidationAPIError(APIError):
    """Validation error for API."""
    
    def __init__(self, detail: str, **extra_info):
        super().__init__(status_code=422, detail=detail, error_code="VALIDATION_ERROR", **extra_info)


class NotFoundAPIError(APIError):
    """Not found error for API."""
    
    def __init__(self, resource: str, **extra_info):
        detail = f"{resource} not found"
        super().__init__(status_code=404, detail=detail, error_code="NOT_FOUND", **extra_info)


class ConflictAPIError(APIError):
    """Conflict error for API."""
    
    def __init__(self, detail: str, **extra_info):
        super().__init__(status_code=409, detail=detail, error_code="CONFLICT", **extra_info)


def handle_errors(func: Callable) -> Callable:
    """
    Decorator to handle common errors in API routes.
    
    Catches and logs errors, returns appropriate HTTP responses.
    """
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error in {func.__name__}: {str(e)}")
            raise ValidationAPIError(
                detail="Invalid input data",
                errors=e.errors()
            )
        except APIError:
            raise  # Re-raise API errors as-is
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            raise APIError(
                status_code=500,
                detail="Internal server error",
                error_code="INTERNAL_ERROR"
            )
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error in {func.__name__}: {str(e)}")
            raise ValidationAPIError(
                detail="Invalid input data",
                errors=e.errors()
            )
        except APIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            raise APIError(
                status_code=500,
                detail="Internal server error",
                error_code="INTERNAL_ERROR"
            )
    
    # Return async or sync wrapper based on function
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def monitor_performance(threshold_ms: float = 1000):
    """
    Decorator to monitor and log execution time.
    
    Args:
        threshold_ms: Log warning if execution exceeds this time (milliseconds)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                execution_time_ms = (time.time() - start_time) * 1000
                if execution_time_ms > threshold_ms:
                    logger.warning(
                        f"{func.__name__} took {execution_time_ms:.2f}ms (threshold: {threshold_ms}ms)"
                    )
                else:
                    logger.debug(f"{func.__name__} took {execution_time_ms:.2f}ms")
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time_ms = (time.time() - start_time) * 1000
                if execution_time_ms > threshold_ms:
                    logger.warning(
                        f"{func.__name__} took {execution_time_ms:.2f}ms (threshold: {threshold_ms}ms)"
                    )
                else:
                    logger.debug(f"{func.__name__} took {execution_time_ms:.2f}ms")
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Import asyncio at module level for iscoroutinefunction check
import asyncio
