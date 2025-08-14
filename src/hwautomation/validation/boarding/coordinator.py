"""
Boarding validation coordinator.

Orchestrates the complete boarding validation process using modular handlers.
"""

from typing import Dict, List, Optional

from ...logging import get_logger
from .base import (
    BoardingValidation,
    ValidationCategory,
    ValidationConfig,
    ValidationHandler,
    ValidationStatus,
)
from .connectivity import ConnectivityValidationHandler
from .hardware import HardwareValidationHandler
from .ipmi import IpmiValidationHandler

logger = get_logger(__name__)


class BoardingValidationCoordinator:
    """Coordinates the complete boarding validation process."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = get_logger(__name__)

        # Initialize validation handlers
        self.handlers: Dict[ValidationCategory, ValidationHandler] = {
            ValidationCategory.CONNECTIVITY: ConnectivityValidationHandler(),
            ValidationCategory.HARDWARE: HardwareValidationHandler(),
            ValidationCategory.IPMI: IpmiValidationHandler(),
            # TODO: Add remaining handlers
            # ValidationCategory.BIOS: BiosValidationHandler(),
            # ValidationCategory.NETWORK: NetworkValidationHandler(),
            # ValidationCategory.CONFIGURATION: ConfigurationValidationHandler(),
        }

    def validate_complete_boarding(
        self,
        device_id: str,
        device_type: str,
        server_ip: str,
        ipmi_ip: str,
        ipmi_username: str = "ADMIN",
        ipmi_password: str = "ADMIN",
        ssh_username: str = "root",
        **kwargs,
    ) -> BoardingValidation:
        """
        Perform complete boarding validation for a device.

        Args:
            device_id: Device identifier
            device_type: BMC device type
            server_ip: Server IP address
            ipmi_ip: IPMI IP address
            ipmi_username: IPMI username
            ipmi_password: IPMI password
            ssh_username: SSH username
            **kwargs: Additional configuration parameters

        Returns:
            Complete validation results
        """
        logger.info(
            f"Starting complete boarding validation for {device_id} ({device_type})"
        )

        # Create validation configuration
        config = ValidationConfig(
            device_id=device_id,
            device_type=device_type,
            server_ip=server_ip,
            ipmi_ip=ipmi_ip,
            ipmi_username=ipmi_username,
            ipmi_password=ipmi_password,
            ssh_username=ssh_username,
            **kwargs,
        )

        # Initialize validation results
        validation = BoardingValidation(
            device_id=device_id,
            device_type=device_type,
            overall_status=ValidationStatus.PASS,
        )

        # Execute validation in order of dependencies
        validation_order = self._get_validation_order()

        for category in validation_order:
            handler = self.handlers.get(category)
            if handler is None:
                logger.warning(
                    f"No handler available for category {category.value}, skipping"
                )
                continue

            # Check if prerequisites are met
            if not self._check_prerequisites(handler, validation):
                logger.warning(f"Prerequisites not met for {category.value}, skipping")
                continue

            try:
                logger.info(f"Executing {category.value} validation")
                results = handler.validate(config)

                for result in results:
                    validation.add_result(result)

                logger.info(
                    f"Completed {category.value} validation: {len(results)} checks"
                )

            except Exception as e:
                logger.error(f"Error in {category.value} validation: {e}")
                from .base import ValidationResult

                error_result = ValidationResult(
                    check_name=f"{category.value}_validation_error",
                    status=ValidationStatus.FAIL,
                    message=f"Validation error in {category.value}: {e}",
                    category=category,
                )
                validation.add_result(error_result)

        # Final summary update
        validation.update_summary()

        logger.info(
            f"Boarding validation complete for {device_id}: {validation.overall_status.value} "
            f"({validation.summary['passed']}/{validation.summary['total']} passed)"
        )

        return validation

    def _get_validation_order(self) -> List[ValidationCategory]:
        """Get the order in which validations should be executed."""
        return [
            ValidationCategory.CONNECTIVITY,
            ValidationCategory.HARDWARE,
            ValidationCategory.IPMI,
            ValidationCategory.BIOS,
            ValidationCategory.NETWORK,
            ValidationCategory.CONFIGURATION,
        ]

    def _check_prerequisites(
        self, handler: ValidationHandler, validation: BoardingValidation
    ) -> bool:
        """Check if prerequisites for a handler are met."""
        required_categories = handler.get_required_prerequisites()

        for required_category in required_categories:
            # Check if any validation in this category passed
            category_results = validation.get_results_by_category(required_category)
            if not category_results:
                logger.warning(
                    f"No results found for prerequisite category {required_category.value}"
                )
                return False

            # Check if at least one critical check passed
            passed_results = [
                r for r in category_results if r.status == ValidationStatus.PASS
            ]
            if not passed_results:
                logger.warning(
                    f"No passing results in prerequisite category {required_category.value}"
                )
                return False

        return True

    def get_validation_summary(self, validation: BoardingValidation) -> Dict:
        """Get a detailed summary of validation results."""
        summary = {
            "device_id": validation.device_id,
            "device_type": validation.device_type,
            "overall_status": validation.overall_status.value,
            "summary": validation.summary,
            "categories": {},
        }

        # Group results by category
        for category in ValidationCategory:
            category_results = validation.get_results_by_category(category)
            if category_results:
                category_summary = {
                    "total": len(category_results),
                    "passed": len(
                        [
                            r
                            for r in category_results
                            if r.status == ValidationStatus.PASS
                        ]
                    ),
                    "failed": len(
                        [
                            r
                            for r in category_results
                            if r.status == ValidationStatus.FAIL
                        ]
                    ),
                    "warnings": len(
                        [
                            r
                            for r in category_results
                            if r.status == ValidationStatus.WARNING
                        ]
                    ),
                    "skipped": len(
                        [
                            r
                            for r in category_results
                            if r.status == ValidationStatus.SKIP
                        ]
                    ),
                    "checks": [
                        {
                            "name": r.check_name,
                            "status": r.status.value,
                            "message": r.message,
                            "remediation": r.remediation,
                        }
                        for r in category_results
                    ],
                }
                summary["categories"][category.value] = category_summary

        return summary

    def get_failed_validations(self, validation: BoardingValidation) -> List[Dict]:
        """Get all failed validations with remediation suggestions."""
        failed_results = validation.get_failed_results()

        return [
            {
                "category": result.category.value,
                "check": result.check_name,
                "message": result.message,
                "remediation": result.remediation,
                "details": result.details,
            }
            for result in failed_results
        ]
