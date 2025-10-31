"""Centralized logging configuration for azure_pipelines modules.

This module provides a consistent logging setup across all azure_pipelines modules.
It includes configuration for console and file logging with different log levels,
formatting options, and rotation policies.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Any, Optional


def get_log_directory() -> Path:
    """Get or create the log directory.

    Returns:
        Path: Path to the log directory
    """
    # Always return os.devnull to disable file logging completely
    return Path(os.devnull)


def configure_logging(
    logger_name: Optional[str] = None,
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    log_format: str = "[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
    date_format: str = "%Y-%m-%d %H:%M:%S",
    console_output: bool = True,
    file_output: bool = False,  # Default to False to disable file logging
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    propagate: bool = False,
) -> logging.Logger:
    """Configure logging for a module.

    Args:
        logger_name: Name of the logger (defaults to the calling module name)
        log_level: Logging level (default: INFO)
        log_file: Log file name (default: based on logger_name)
        log_format: Format string for log messages
        date_format: Format string for timestamps
        console_output: Whether to output logs to console
        file_output: Whether to output logs to file
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
        propagate: Whether to propagate logs to parent loggers

    Returns:
        logging.Logger: Configured logger instance
    """
    # If no logger name is provided, use the calling module's name
    if logger_name is None:
        import inspect

        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        logger_name = module.__name__ if module else "azure_pipelines"

    # Get or create the logger
    logger = logging.getLogger(logger_name)

    # Clear any existing handlers to avoid duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    # Set the log level
    logger.setLevel(log_level)
    logger.propagate = propagate

    # Create formatter
    formatter = logging.Formatter(log_format, date_format)

    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        logger.addHandler(console_handler)

    # File logging is disabled
    # The file_output parameter is kept for backward compatibility
    # but no file handlers will be created

    return logger


def get_logger(
    name: Optional[str] = None,
    log_level: Optional[int] = None,
    **kwargs: Any,
) -> logging.Logger:
    """Get a configured logger.

    This is a convenience function for getting a logger with the default configuration.

    Args:
        name: Logger name (defaults to the calling module name)
        log_level: Override default log level
        **kwargs: Additional arguments to pass to configure_logging

    Returns:
        logging.Logger: Configured logger instance
    """
    # Get environment variable for log level, defaulting to INFO
    env_log_level = os.environ.get("AZURE_PIPELINES_LOG_LEVEL", "INFO")

    # Map string log levels to logging constants
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    # Use provided log_level, or get from environment, or default to INFO
    effective_log_level = log_level or log_level_map.get(env_log_level, logging.INFO)

    return configure_logging(
        logger_name=name, log_level=effective_log_level, file_output=False, **kwargs
    )


# Configure root logger for the azure_pipelines package
root_logger = get_logger("azure_pipelines")
