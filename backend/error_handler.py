"""
Error Handling and Retry Logic Module
Provides robust error handling and retry mechanisms
"""

import logging
import time
from typing import Callable, Any, Optional, TypeVar
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')

class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        timeout: Optional[float] = None
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.timeout = timeout

def retry_with_backoff(config: Optional[RetryConfig] = None) -> Callable:
    """
    Decorator for retrying operations with exponential backoff.
    
    Args:
        config: RetryConfig instance with retry parameters
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = config.initial_delay
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    logger.debug(f"Attempt {attempt + 1}/{config.max_retries + 1} for {func.__name__}")
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < config.max_retries:
                        logger.warning(f"⚠️ {func.__name__} failed (attempt {attempt + 1}): {e}")
                        logger.info(f"  Retrying in {delay:.1f}s...")
                        time.sleep(delay)
                        delay = min(delay * config.backoff_factor, config.max_delay)
                    else:
                        logger.error(f"❌ {func.__name__} failed after {config.max_retries + 1} attempts")
            
            raise last_exception
        
        return wrapper
    return decorator

class ErrorHandler:
    """Centralized error handling."""
    
    @staticmethod
    def handle_extraction_error(filename: str, error: Exception) -> str:
        """Handle text extraction errors with fallback."""
        logger.error(f"❌ Extraction failed for {filename}: {error}")
        return f"[Error extracting text from {filename}: {str(error)}]"
    
    @staticmethod
    def handle_embedding_error(text: str, error: Exception) -> Optional[Any]:
        """Handle embedding generation errors."""
        logger.error(f"❌ Embedding failed: {error}")
        return None
    
    @staticmethod
    def handle_llm_error(query: str, error: Exception) -> str:
        """Handle LLM request errors."""
        logger.error(f"❌ LLM request failed for query '{query}': {error}")
        return "I apologize, but I encountered an error processing your request. Please try again."
    
    @staticmethod
    def handle_index_error(chat_id: str, error: Exception) -> bool:
        """Handle FAISS index errors."""
        logger.error(f"❌ Index error for session {chat_id}: {error}")
        return False

class TimeoutHandler:
    """Handle timeout scenarios."""
    
    @staticmethod
    def with_timeout(func: Callable, timeout: float, *args, **kwargs) -> Any:
        """Execute function with timeout."""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Operation timed out after {timeout} seconds")
        
        # Set signal handler
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(timeout))
        
        try:
            result = func(*args, **kwargs)
            signal.alarm(0)  # Cancel alarm
            return result
        finally:
            signal.signal(signal.SIGALRM, old_handler)
            signal.alarm(0)

# Predefined retry configs
FAST_RETRY = RetryConfig(max_retries=2, initial_delay=0.5, max_delay=5.0)
STANDARD_RETRY = RetryConfig(max_retries=3, initial_delay=1.0, max_delay=30.0)
SLOW_RETRY = RetryConfig(max_retries=5, initial_delay=2.0, max_delay=60.0)
