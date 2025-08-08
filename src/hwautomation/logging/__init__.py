"""
HWAutomation Unified Logging Package

This package provides centralized logging configuration and utilities
for the entire HWAutomation system.
"""

from .config import (
    CorrelationContext,
    get_correlation_id,
    get_logger,
    set_correlation_id,
    setup_logging,
    with_correlation,
)

__all__ = [
    "get_logger",
    "setup_logging",
    "set_correlation_id",
    "get_correlation_id",
    "with_correlation",
    "CorrelationContext",
]
