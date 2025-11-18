"""Structured logging setup for the bot."""
import logging
import logging.handlers
from typing import Optional
from config import Config


def setup_logger(name: str, log_file: Optional[str] = None, level: str = None) -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        log_file: Optional file path for logging
        level: Log level string (e.g., "INFO", "DEBUG")
    
    Returns:
        Configured logger instance
    """
    if level is None:
        level = Config.LOG_LEVEL

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))

    # Formatter with timestamp, level, module, function, and message
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler with rotation
    if log_file or Config.LOG_FILE:
        file_path = log_file or Config.LOG_FILE
        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=10_485_760,  # 10MB
            backupCount=5,
        )
        file_handler.setLevel(getattr(logging, level))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
