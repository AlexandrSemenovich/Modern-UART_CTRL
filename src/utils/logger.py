"""
Enhanced logging configuration for Modern UART Control.

This module provides centralized logging configuration with:
- Console and file output
- Log rotation
- Environment-specific configurations
- Module-level log level control
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime

from src.styles.constants import LoggingConfig


def _get_environment() -> str:
    """Get the current environment from environment variable or default."""
    env = os.environ.get('APP_ENV', '').lower()
    if env in LoggingConfig.ENV_LEVELS:
        return env
    return LoggingConfig.DEFAULT_ENV


def setup_logging(
    env: str | None = None,
    log_file: str | None = None,
    level: int | None = None,
    console: bool | None = None,
    file_output: bool | None = None,
) -> logging.Logger:
    """
    Configure application logging.
    
    Args:
        env: Environment name (development, testing, production, staging)
        log_file: Optional log file name
        level: Optional explicit log level
        console: Enable console output (default: True for dev/test, False for prod)
        file_output: Enable file output (default: True)
        
    Returns:
        Configured root logger
    """
    # Determine environment
    if env is None:
        env = _get_environment()
    
    # Determine log level
    if level is None:
        level = LoggingConfig.ENV_LEVELS.get(env, logging.DEBUG)
    
    # Determine console and file settings based on environment
    if console is None:
        console = env in ('development', 'testing')
    if file_output is None:
        file_output = True
    
    # Create logs directory
    LoggingConfig.LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create formatters
    formatter = logging.Formatter(LoggingConfig.LOG_FORMAT, LoggingConfig.DATE_FORMAT)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if file_output:
        if log_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = f'app_{timestamp}.log'
        
        file_path = LoggingConfig.LOG_DIR / log_file
        
        # Rotating file handler
        rotating_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=LoggingConfig.MAX_BYTES,
            backupCount=LoggingConfig.BACKUP_COUNT,
            encoding='utf-8'
        )
        rotating_handler.setLevel(level)
        rotating_handler.setFormatter(formatter)
        root_logger.addHandler(rotating_handler)
        
        # Error log file (always ERROR level)
        error_file_path = LoggingConfig.LOG_DIR / f'errors_{timestamp}.log'
        error_handler = logging.handlers.RotatingFileHandler(
            error_file_path,
            maxBytes=LoggingConfig.MAX_BYTES,
            backupCount=LoggingConfig.BACKUP_COUNT,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
    
    return root_logger


def get_logger(name: str, level: int | None = None) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name: Logger name (typically __name__)
        level: Optional specific level for this logger
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level)
    return logger


def set_module_level(module_name: str, level: int) -> None:
    """
    Set log level for a specific module.
    
    Args:
        module_name: Module name prefix (e.g., 'src.models')
        level: Log level (e.g., logging.DEBUG)
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(level)


def get_log_file_path(name: str = 'app') -> Path | None:
    """
    Get the path to a log file.
    
    Args:
        name: Log file name prefix
        
    Returns:
        Path to the log file, or None if it doesn't exist
    """
    # Find the most recent log file with the given prefix
    if not LoggingConfig.LOG_DIR.exists():
        return None
    
    pattern = f'{name}_*.log'
    log_files = list(LoggingConfig.LOG_DIR.glob(pattern))
    
    if not log_files:
        return None
    
    # Return the most recent file
    return max(log_files, key=lambda p: p.stat().st_mtime)


def cleanup_old_logs(days: int = 30) -> int:
    """
    Remove log files older than specified days.
    
    Args:
        days: Number of days to keep logs
        
    Returns:
        Number of files removed
    """
    if not LoggingConfig.LOG_DIR.exists():
        return 0
    
    import time
    cutoff = time.time() - (days * 24 * 60 * 60)
    removed = 0
    
    for log_file in LoggingConfig.LOG_DIR.glob('*.log'):
        if log_file.stat().st_mtime < cutoff:
            try:
                log_file.unlink()
                removed += 1
            except OSError:
                pass
    
    return removed
