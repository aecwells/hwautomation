"""
Redfish Power Management

Specialized manager for power operations (on, off, restart, status).
"""

from typing import Dict, Optional, Union

from hwautomation.logging import get_logger

from ..base import PowerAction, PowerState, RedfishCredentials
from ..operations import RedfishPowerOperation
from .base import BaseRedfishManager, RedfishManagerError

logger = get_logger(__name__)


class RedfishPowerManager(BaseRedfishManager):
    """Specialized manager for power operations."""

    def __init__(self, credentials: RedfishCredentials):
        super().__init__(credentials)
        self.power_ops = RedfishPowerOperation(credentials)

    def get_supported_operations(self) -> Dict[str, bool]:
        """Get supported power operations."""
        return {
            "get_power_state": True,
            "set_power_state": True,
            "power_on": True,
            "power_off": True,
            "restart": True,
            "power_cycle": True,
            "graceful_shutdown": True,
            "force_power_off": True,
        }

    def get_power_state(self, system_id: str = "1") -> Optional[PowerState]:
        """Get current power state.

        Args:
            system_id: System identifier

        Returns:
            Current power state
        """
        try:
            result = self.power_ops.get_power_state(system_id)
            if result.success:
                return result.result
            else:
                self.logger.error(f"Failed to get power state: {result.error_message}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting power state: {e}")
            return None

    def set_power_state(
        self,
        action: Union[PowerAction, str],
        system_id: str = "1",
        wait: bool = True,
    ) -> bool:
        """Set power state.

        Args:
            action: Power action to perform
            system_id: System identifier
            wait: Wait for operation to complete

        Returns:
            True if successful
        """
        try:
            # Convert string to PowerAction if needed
            if isinstance(action, str):
                try:
                    action = PowerAction(action.lower())
                except ValueError:
                    self.logger.error(f"Invalid power action: {action}")
                    return False

            with self.create_session() as session:
                result = self.power_ops.set_power_state(
                    session, action, system_id, wait
                )
                if not result.success:
                    self.logger.error(
                        f"Failed to set power state: {result.error_message}"
                    )
                return result.success

        except Exception as e:
            self.logger.error(f"Error setting power state: {e}")
            return False

    def power_on(self, system_id: str = "1", wait: bool = True) -> bool:
        """Power on the system.

        Args:
            system_id: System identifier
            wait: Wait for power on to complete

        Returns:
            True if successful
        """
        return self.set_power_state(PowerAction.ON, system_id, wait)

    def power_off(
        self, system_id: str = "1", wait: bool = True, force: bool = False
    ) -> bool:
        """Power off the system.

        Args:
            system_id: System identifier
            wait: Wait for power off to complete
            force: Force immediate power off

        Returns:
            True if successful
        """
        action = PowerAction.FORCE_OFF if force else PowerAction.OFF
        return self.set_power_state(action, system_id, wait)

    def restart(
        self, system_id: str = "1", wait: bool = True, force: bool = False
    ) -> bool:
        """Restart the system.

        Args:
            system_id: System identifier
            wait: Wait for restart to complete
            force: Force immediate restart

        Returns:
            True if successful
        """
        action = PowerAction.FORCE_RESTART if force else PowerAction.GRACEFUL_RESTART
        return self.set_power_state(action, system_id, wait)

    def power_cycle(self, system_id: str = "1", wait: bool = True) -> bool:
        """Power cycle the system.

        Args:
            system_id: System identifier
            wait: Wait for power cycle to complete

        Returns:
            True if successful
        """
        return self.set_power_state(PowerAction.RESTART, system_id, wait)

    def get_system_power_state(self, system_id: str = "1") -> Optional[str]:
        """Get system power state as string (legacy compatibility).

        Args:
            system_id: System identifier

        Returns:
            Power state as string
        """
        power_state = self.get_power_state(system_id)
        return power_state.value if power_state else None

    def is_powered_on(self, system_id: str = "1") -> bool:
        """Check if system is powered on.

        Args:
            system_id: System identifier

        Returns:
            True if powered on
        """
        power_state = self.get_power_state(system_id)
        return power_state == PowerState.ON if power_state else False

    def is_powered_off(self, system_id: str = "1") -> bool:
        """Check if system is powered off.

        Args:
            system_id: System identifier

        Returns:
            True if powered off
        """
        power_state = self.get_power_state(system_id)
        return power_state == PowerState.OFF if power_state else False

    def wait_for_power_state(
        self,
        target_state: PowerState,
        system_id: str = "1",
        timeout: int = 300,
        poll_interval: int = 5,
    ) -> bool:
        """Wait for system to reach target power state.

        Args:
            target_state: Target power state
            system_id: System identifier
            timeout: Maximum wait time in seconds
            poll_interval: Polling interval in seconds

        Returns:
            True if target state reached
        """
        import time

        start_time = time.time()
        while time.time() - start_time < timeout:
            current_state = self.get_power_state(system_id)
            if current_state == target_state:
                return True
            time.sleep(poll_interval)

        self.logger.warning(
            f"Timeout waiting for power state {target_state.value} on system {system_id}"
        )
        return False
