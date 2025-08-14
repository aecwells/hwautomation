"""
Backward compatibility module for the legacy boarding_validator.py file.

This module provides a compatibility layer to ensure existing code continues
to work while using the new modular boarding validation system.
"""

import warnings
from typing import Dict, Optional

from ..logging import get_logger
from .boarding import create_boarding_validator, validate_device_boarding

logger = get_logger(__name__)


# Re-export the original classes and enums for backward compatibility
from .boarding.base import BoardingValidation, ValidationResult, ValidationStatus


class BMCBoardingValidator:
    """
    Backward compatibility wrapper for the legacy BMCBoardingValidator class.

    This class provides the same interface as the original monolithic class
    but delegates to the new modular system.
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = get_logger(__name__)

        # Issue deprecation warning
        warnings.warn(
            "BMCBoardingValidator is deprecated. "
            "Use hwautomation.validation.boarding.create_boarding_validator instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        # Create the new coordinator
        self.coordinator = create_boarding_validator(config)

    def validate_complete_boarding(
        self,
        device_id: str,
        device_type: str,
        server_ip: str,
        ipmi_ip: str,
    ) -> BoardingValidation:
        """
        Perform complete boarding validation for a device (legacy interface).

        This method provides backward compatibility for the original interface.
        """
        logger.info(f"Validating boarding via legacy interface for {device_id}")

        return validate_device_boarding(
            device_id=device_id,
            device_type=device_type,
            server_ip=server_ip,
            ipmi_ip=ipmi_ip,
            config=self.config,
        )

    def _load_bios_requirements(self) -> Dict[str, Dict]:
        """Load BIOS requirements (legacy method - returns empty dict)."""
        warnings.warn(
            "_load_bios_requirements is deprecated and no longer used",
            DeprecationWarning,
            stacklevel=2,
        )
        return {}

    def _load_ipmi_requirements(self) -> Dict[str, Dict]:
        """Load IPMI requirements (legacy method - returns empty dict)."""
        warnings.warn(
            "_load_ipmi_requirements is deprecated and no longer used",
            DeprecationWarning,
            stacklevel=2,
        )
        return {}
