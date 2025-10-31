"""
Tests for the logging_config module.
"""

import logging

from azure_pipelines.logging_config import configure_logging, get_logger


def test_configure_logging_default():
    """Test configure_logging with default parameters."""
    logger = configure_logging(logger_name="test_logger")
    assert logger.name == "test_logger"
    assert logger.level == logging.INFO
    assert len(logger.handlers) > 0

    # Clean up handlers to avoid affecting other tests
    logger.handlers.clear()


def test_configure_logging_custom_level():
    """Test configure_logging with custom log level."""
    logger = configure_logging(logger_name="test_logger", log_level=logging.DEBUG)
    assert logger.level == logging.DEBUG

    # Clean up handlers to avoid affecting other tests
    logger.handlers.clear()


def test_configure_logging_no_file_output():
    """Test configure_logging with file output disabled."""
    logger = configure_logging(logger_name="test_logger", file_output=False)

    # Check that no RotatingFileHandler is present
    assert not any(
        isinstance(h, logging.handlers.RotatingFileHandler) for h in logger.handlers
    )

    # Clean up handlers to avoid affecting other tests
    logger.handlers.clear()


def test_get_logger_default():
    """Test get_logger with default parameters."""
    logger = get_logger("test_module")
    assert logger.name == "test_module"
    assert logger.level == logging.INFO

    # Clean up handlers to avoid affecting other tests
    logger.handlers.clear()


def test_get_logger_env_override(mock_env):
    """Test get_logger with environment variable override."""
    with mock_env(AZURE_PIPELINES_LOG_LEVEL="DEBUG"):
        logger = get_logger("test_module")
        assert logger.level == logging.DEBUG

    # Clean up handlers to avoid affecting other tests
    logger.handlers.clear()


def test_get_logger_param_override(mock_env):
    """Test that log_level parameter overrides environment variable."""
    with mock_env(AZURE_PIPELINES_LOG_LEVEL="DEBUG"):
        logger = get_logger("test_module", log_level=logging.ERROR)
        assert logger.level == logging.ERROR

    # Clean up handlers to avoid affecting other tests
    logger.handlers.clear()
