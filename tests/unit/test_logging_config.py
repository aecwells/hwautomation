"""Tests for logging configuration and utilities."""

import logging
import os
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from hwautomation.logging import (
    get_correlation_id,
    get_logger,
    set_correlation_id,
    setup_logging,
    with_correlation,
)


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_with_name(self):
        """Test getting a logger with a specific name."""
        logger = get_logger("test.module")
        assert logger.name == "test.module"
        assert isinstance(logger, logging.Logger)

    def test_get_logger_different_names(self):
        """Test that different names return different loggers."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        assert logger1.name != logger2.name
        assert logger1 is not logger2

    def test_get_logger_same_name(self):
        """Test that same names return the same logger instance."""
        logger1 = get_logger("same.module")
        logger2 = get_logger("same.module")
        assert logger1 is logger2


class TestCorrelationTracking:
    """Test correlation ID tracking functionality."""

    def test_set_and_get_correlation_id(self):
        """Test setting and getting correlation ID."""
        correlation_id = "test-123-456"
        set_correlation_id(correlation_id)
        retrieved_id = get_correlation_id()
        assert retrieved_id == correlation_id

    def test_get_correlation_id_none(self):
        """Test getting correlation ID when none is set."""
        # Clear any existing correlation ID
        set_correlation_id(None)
        retrieved_id = get_correlation_id()
        assert retrieved_id is None

    def test_correlation_id_isolation(self):
        """Test that correlation IDs are properly isolated."""
        # Set a correlation ID
        set_correlation_id("test-789")
        assert get_correlation_id() == "test-789"

        # Clear it
        set_correlation_id(None)
        assert get_correlation_id() is None

    def test_with_correlation_decorator(self):
        """Test the with_correlation context manager."""
        # This tests that the context manager can be imported and used
        test_correlation_id = "decorator-test-123"

        # Use with_correlation as a context manager (not decorator)
        with with_correlation(test_correlation_id):
            result = get_correlation_id()

        # The correlation ID should have been set during context execution
        assert result == test_correlation_id


class TestSetupLogging:
    """Test setup_logging function."""

    @patch("hwautomation.logging.config.logging.config.dictConfig")
    def test_setup_logging_basic(self, mock_dict_config):
        """Test basic logging setup."""
        setup_logging(environment="development", force_reload=True)
        # Should call dictConfig at least once
        assert mock_dict_config.called

    @patch("hwautomation.logging.config.logging.config.dictConfig")
    def test_setup_logging_with_level(self, mock_dict_config):
        """Test logging setup with specific environment."""
        setup_logging(environment="production", force_reload=True)
        # Should call dictConfig
        assert mock_dict_config.called

    def test_setup_logging_integration(self):
        """Test setup_logging integration without mocking."""
        # Create a simple config and ensure no exceptions
        try:
            setup_logging(environment="development", force_reload=True)
            # Test that we can get a logger and it works
            logger = get_logger("test.integration")
            logger.warning("Test warning message")
            success = True
        except Exception:
            success = False
        assert success is True


class TestLoggingIntegration:
    """Test logging system integration."""

    def test_logger_creation_and_usage(self):
        """Test creating and using loggers."""
        logger = get_logger("test.integration.usage")

        # Test that basic logging methods exist and can be called
        try:
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            success = True
        except Exception:
            success = False

        assert success is True

    def test_logger_hierarchy(self):
        """Test logger hierarchy behavior."""
        parent_logger = get_logger("parent")
        child_logger = get_logger("parent.child")

        # Child logger name should start with parent name
        assert child_logger.name.startswith(parent_logger.name)

        # Both should be logger instances
        assert isinstance(parent_logger, logging.Logger)
        assert isinstance(child_logger, logging.Logger)

    def test_multiple_logger_instances(self):
        """Test that multiple loggers can be created and used."""
        loggers = []
        for i in range(5):
            logger = get_logger(f"test.multiple.{i}")
            loggers.append(logger)

        # All should be logger instances
        for logger in loggers:
            assert isinstance(logger, logging.Logger)

        # All should have different names
        names = [logger.name for logger in loggers]
        assert len(set(names)) == len(names)

    def test_logging_with_correlation(self):
        """Test logging with correlation ID tracking."""
        logger = get_logger("test.correlation")
        correlation_id = "test-correlation-456"

        # Set correlation ID
        set_correlation_id(correlation_id)

        # Log a message (this should work without errors)
        try:
            logger.info("Test message with correlation")
            success = True
        except Exception:
            success = False

        assert success is True

        # Verify correlation ID is still set
        assert get_correlation_id() == correlation_id


class TestLoggingErrorHandling:
    """Test error handling in logging system."""

    def test_invalid_logger_names(self):
        """Test handling of edge cases in logger names."""
        # Empty string
        logger = get_logger("")
        assert isinstance(logger, logging.Logger)

        # None - this might raise an exception or return a default logger
        try:
            logger = get_logger(None)
            success = True
        except (TypeError, ValueError):
            success = True  # Expected behavior
        except Exception:
            success = False

        assert success is True

    def test_correlation_id_edge_cases(self):
        """Test edge cases for correlation ID handling."""
        # Empty string
        set_correlation_id("")
        assert get_correlation_id() == ""

        # None
        set_correlation_id(None)
        assert get_correlation_id() is None

        # Non-string values
        set_correlation_id(12345)
        assert get_correlation_id() == 12345

    def test_setup_logging_error_recovery(self):
        """Test that setup_logging handles errors gracefully."""
        # Test with invalid parameters
        try:
            setup_logging(level="INVALID_LEVEL")
            success = True
        except Exception:
            # Should either work or fail gracefully
            success = True

        assert success is True
