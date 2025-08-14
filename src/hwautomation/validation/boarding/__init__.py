"""
Validation module initialization.

This module provides the modular boarding validation system that replaces
the monolithic boarding_validator.py file.
"""

from .coordinator import BoardingValidationCoordinator
from .factory import create_boarding_validator, validate_device_boarding

__all__ = [
    "BoardingValidationCoordinator",
    "create_boarding_validator",
    "validate_device_boarding",
]
