"""Utility functions for the apartment search application."""
import time
import functools
import logging
from typing import TypeVar, Callable, Any, List, Dict, Tuple, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Type variables for generics
T = TypeVar('T')
R = TypeVar('R')

def retry(max_retries: int = 3, delay: float = 1.0, 
          exception_types: Tuple = (Exception,), 
          logger_func: Optional[Callable[[str], Any]] = None):
    """
    Decorator for retrying a function if it raises specified exceptions.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        exception_types: Tuple of exception types to catch and retry
        logger_func: Optional function to log retry attempts
    
    Returns:
        The decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            log = logger_func or logger.warning
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        log(f"Retry attempt {attempt}/{max_retries} for {func.__name__}")
                    return func(*args, **kwargs)
                except exception_types as e:
                    last_exception = e
                    if attempt < max_retries:
                        log(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        log(f"All {max_retries} retries failed for {func.__name__}")
            
            # If we reach here, all retries have failed
            raise last_exception
        
        return wrapper
    return decorator

def extract_number(text: str) -> Optional[float]:
    """
    Extract a number from a string.
    
    Args:
        text: Text that may contain a number
    
    Returns:
        Float value if found, None otherwise
    """
    import re
    if not text:
        return None
    
    # Try to extract a numeric value
    match = re.search(r'(\d+[.,]?\d*)', text)
    if match:
        return float(match.group(1).replace(',', '.'))
    return None

def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds to a human-readable string.
    
    Args:
        seconds: Time duration in seconds
    
    Returns:
        Formatted duration string (e.g., "2h 30m 15s")
    """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{int(hours)}h")
    if minutes > 0 or (hours > 0 and seconds > 0):
        parts.append(f"{int(minutes)}m")
    if seconds > 0 or not parts:
        parts.append(f"{int(seconds)}s")
    
    return " ".join(parts)