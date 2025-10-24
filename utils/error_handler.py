"""
Error Handling Utilities for Multi-Exchange Trading Platform
Provides comprehensive error handling, logging, and user-friendly error messages
"""

import time
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

class TradingError(Exception):
    """Custom exception for trading-related errors"""
    def __init__(self, message: str, error_type: str = "TRADING_ERROR", details: Dict[str, Any] = None):
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        super().__init__(self.message)

class APIError(TradingError):
    """API-related errors"""
    def __init__(self, message: str, exchange: str = None, endpoint: str = None, status_code: int = None):
        super().__init__(message, "API_ERROR", {
            "exchange": exchange,
            "endpoint": endpoint,
            "status_code": status_code
        })

class ValidationError(TradingError):
    """Validation-related errors"""
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(message, "VALIDATION_ERROR", {
            "field": field,
            "value": value
        })

class InsufficientFundsError(TradingError):
    """Insufficient funds error"""
    def __init__(self, message: str, required: float = None, available: float = None):
        super().__init__(message, "INSUFFICIENT_FUNDS", {
            "required": required,
            "available": available
        })

class OrderError(TradingError):
    """Order-related errors"""
    def __init__(self, message: str, order_id: str = None, symbol: str = None, side: str = None):
        super().__init__(message, "ORDER_ERROR", {
            "order_id": order_id,
            "symbol": symbol,
            "side": side
        })

class ErrorHandler:
    """Centralized error handling and logging"""
    
    def __init__(self):
        self.error_log = []
        self.max_log_size = 1000
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None) -> str:
        """Log an error and return error ID"""
        error_id = f"ERR_{int(time.time() * 1000)}"
        
        error_entry = {
            "id": error_id,
            "timestamp": datetime.now().isoformat(),
            "type": type(error).__name__,
            "message": str(error),
            "context": context or {},
            "traceback": traceback.format_exc()
        }
        
        self.error_log.append(error_entry)
        
        # Keep log size manageable
        if len(self.error_log) > self.max_log_size:
            self.error_log = self.error_log[-self.max_log_size:]
        
        return error_id
    
    def get_user_friendly_message(self, error: Exception) -> str:
        """Convert technical errors to user-friendly messages"""
        if isinstance(error, APIError):
            exchange = error.details.get('exchange', 'Unknown')
            endpoint = error.details.get('endpoint', 'Unknown')
            status_code = error.details.get('status_code')
            
            if status_code == 401:
                return f"❌ Authentication failed for {exchange}. Please check your API keys."
            elif status_code == 403:
                return f"❌ Access denied for {exchange}. Check API permissions."
            elif status_code == 429:
                return f"❌ Rate limit exceeded for {exchange}. Please wait and try again."
            elif status_code == 500:
                return f"❌ {exchange} server error. Please try again later."
            else:
                return f"❌ API error from {exchange}: {error.message}"
        
        elif isinstance(error, ValidationError):
            field = error.details.get('field', 'Unknown field')
            return f"❌ Invalid {field}: {error.message}"
        
        elif isinstance(error, InsufficientFundsError):
            required = error.details.get('required', 0)
            available = error.details.get('available', 0)
            return f"❌ Insufficient funds. Required: ${required:,.2f}, Available: ${available:,.2f}"
        
        elif isinstance(error, OrderError):
            symbol = error.details.get('symbol', 'Unknown')
            side = error.details.get('side', 'Unknown')
            return f"❌ Order error for {symbol} {side}: {error.message}"
        
        elif isinstance(error, TradingError):
            return f"❌ Trading error: {error.message}"
        
        else:
            return f"❌ Unexpected error: {str(error)}"
    
    def get_error_suggestions(self, error: Exception) -> list:
        """Get suggested actions for common errors"""
        suggestions = []
        
        if isinstance(error, APIError):
            status_code = error.details.get('status_code')
            if status_code == 401:
                suggestions.extend([
                    "Check if API keys are correct",
                    "Verify API key permissions",
                    "Ensure API keys are not expired"
                ])
            elif status_code == 403:
                suggestions.extend([
                    "Check API key permissions",
                    "Verify trading permissions are enabled",
                    "Contact exchange support if needed"
                ])
            elif status_code == 429:
                suggestions.extend([
                    "Wait a few minutes before retrying",
                    "Reduce request frequency",
                    "Check if you're hitting rate limits"
                ])
        
        elif isinstance(error, InsufficientFundsError):
            suggestions.extend([
                "Deposit more funds to your account",
                "Reduce position size",
                "Check if funds are locked in other positions"
            ])
        
        elif isinstance(error, OrderError):
            suggestions.extend([
                "Check if symbol is valid",
                "Verify order parameters",
                "Check if market is open"
            ])
        
        return suggestions
    
    def get_recent_errors(self, limit: int = 10) -> list:
        """Get recent errors from log"""
        return self.error_log[-limit:]
    
    def clear_errors(self):
        """Clear error log"""
        self.error_log = []

# Global error handler instance
error_handler = ErrorHandler()

def handle_api_error(func):
    """Decorator for API error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_id = error_handler.log_error(e, {
                "function": func.__name__,
                "args": str(args)[:100],  # Limit args length
                "kwargs": str(kwargs)[:100]
            })
            
            # Re-raise with additional context
            if "API" in str(type(e)) or "HTTP" in str(type(e)):
                raise APIError(
                    f"API call failed: {str(e)}",
                    exchange=getattr(args[0], 'exchange_name', 'Unknown') if args else 'Unknown'
                ) from e
            else:
                raise TradingError(f"Operation failed: {str(e)}") from e
    
    return wrapper

def safe_execute(func, *args, **kwargs):
    """Safely execute a function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_id = error_handler.log_error(e, {
            "function": func.__name__,
            "args": str(args)[:100],
            "kwargs": str(kwargs)[:100]
        })
        return {
            "success": False,
            "error": error_handler.get_user_friendly_message(e),
            "error_id": error_id,
            "suggestions": error_handler.get_error_suggestions(e)
        }
