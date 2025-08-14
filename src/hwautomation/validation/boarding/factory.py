"""
Factory functions for creating boarding validators.

Provides backward-compatible interface for creating boarding validators.
"""

from typing import Dict, Optional

from ...logging import get_logger
from .base import BoardingValidation
from .coordinator import BoardingValidationCoordinator

logger = get_logger(__name__)


def create_boarding_validator(
    config: Optional[Dict] = None,
) -> BoardingValidationCoordinator:
    """
    Factory function to create a boarding validation coordinator.

    This function provides a backward-compatible interface for creating
    boarding validators while using the new modular system.

    Args:
        config: Optional configuration dictionary

    Returns:
        BoardingValidationCoordinator: Configured coordinator ready for use
    """
    logger.info("Creating boarding validation coordinator")
    return BoardingValidationCoordinator(config)


def validate_device_boarding(
    device_id: str,
    device_type: str,
    server_ip: str,
    ipmi_ip: str,
    ipmi_username: str = "ADMIN",
    ipmi_password: str = "ADMIN",
    ssh_username: str = "root",
    config: Optional[Dict] = None,
    **kwargs,
) -> BoardingValidation:
    """
    Convenience function to perform complete boarding validation.

    This function creates a coordinator and performs validation in one call.

    Args:
        device_id: Device identifier
        device_type: BMC device type
        server_ip: Server IP address
        ipmi_ip: IPMI IP address
        ipmi_username: IPMI username
        ipmi_password: IPMI password
        ssh_username: SSH username
        config: Optional configuration dictionary
        **kwargs: Additional configuration parameters

    Returns:
        BoardingValidation: Complete validation results
    """
    logger.info(f"Performing boarding validation for device {device_id}")

    coordinator = create_boarding_validator(config)

    return coordinator.validate_complete_boarding(
        device_id=device_id,
        device_type=device_type,
        server_ip=server_ip,
        ipmi_ip=ipmi_ip,
        ipmi_username=ipmi_username,
        ipmi_password=ipmi_password,
        ssh_username=ssh_username,
        **kwargs,
    )
