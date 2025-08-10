"""Redfish power management operations.

This module provides power control operations for computer systems
through the Redfish API.
"""

from __future__ import annotations
import time
from typing import Optional

from hwautomation.logging import get_logger
from ..base import (
    BaseRedfishOperation,
    PowerAction,
    PowerState,
    RedfishCredentials,
    RedfishError,
    RedfishNotSupportedError,
    RedfishOperation,
    RedfishResponse,
)
from ..client import RedfishSession

logger = get_logger(__name__)


class RedfishPowerOperation(BaseRedfishOperation):
    """Redfish power management operations."""

    def __init__(self, credentials: RedfishCredentials):
        """Initialize power operations.
        
        Args:
            credentials: Redfish connection credentials
        """
        super().__init__(credentials)

    def get_power_state(self, system_id: str = "1") -> RedfishOperation[PowerState]:
        """Get current power state of the system.

        Args:
            system_id: System identifier (default: "1")

        Returns:
            Operation result with power state
        """
        try:
            with RedfishSession(self.credentials) as session:
                system_uri = f"/redfish/v1/Systems/{system_id}"
                response = session.get(system_uri)

                if not response.success:
                    return RedfishOperation(
                        success=False,
                        error_message=f"Failed to get system info: {response.error_message}",
                        response=response,
                    )

                if not response.data:
                    return RedfishOperation(
                        success=False,
                        error_message="No system data received",
                        response=response,
                    )

                power_state_str = response.data.get("PowerState", "Unknown")
                
                # Map Redfish power states to our enum
                try:
                    power_state = PowerState(power_state_str)
                except ValueError:
                    logger.warning(f"Unknown power state: {power_state_str}")
                    power_state = PowerState.UNKNOWN

                return RedfishOperation(
                    success=True,
                    result=power_state,
                    response=response,
                )

        except Exception as e:
            logger.error(f"Failed to get power state: {e}")
            return RedfishOperation(
                success=False,
                error_message=str(e),
            )

    def set_power_state(
        self, 
        action: PowerAction, 
        system_id: str = "1",
        wait_for_completion: bool = True,
        timeout: int = 300
    ) -> RedfishOperation[bool]:
        """Set power state of the system.

        Args:
            action: Power action to perform
            system_id: System identifier (default: "1")
            wait_for_completion: Wait for action to complete
            timeout: Timeout in seconds for completion

        Returns:
            Operation result with success status
        """
        try:
            with RedfishSession(self.credentials) as session:
                # Get system info and reset action URI
                system_uri = f"/redfish/v1/Systems/{system_id}"
                response = session.get(system_uri)

                if not response.success:
                    return RedfishOperation(
                        success=False,
                        error_message=f"Failed to get system info: {response.error_message}",
                        response=response,
                    )

                if not response.data:
                    return RedfishOperation(
                        success=False,
                        error_message="No system data received",
                        response=response,
                    )

                # Find reset action
                actions = response.data.get("Actions", {})
                reset_action = actions.get("#ComputerSystem.Reset")
                
                if not reset_action:
                    return RedfishOperation(
                        success=False,
                        error_message="Reset action not supported",
                        response=response,
                    )

                reset_uri = reset_action.get("target")
                if not reset_uri:
                    return RedfishOperation(
                        success=False,
                        error_message="Reset target URI not found",
                        response=response,
                    )

                # Get allowed reset types
                allowed_values = reset_action.get("ResetType@Redfish.AllowableValues", [])
                
                # Map our action to Redfish reset type
                reset_type = self._map_power_action(action, allowed_values)
                if not reset_type:
                    return RedfishOperation(
                        success=False,
                        error_message=f"Power action {action.value} not supported. "
                                    f"Available: {allowed_values}",
                        response=response,
                    )

                # Perform the reset action
                reset_data = {"ResetType": reset_type}
                reset_response = session.post(reset_uri, reset_data)

                if not reset_response.success:
                    return RedfishOperation(
                        success=False,
                        error_message=f"Power action failed: {reset_response.error_message}",
                        response=reset_response,
                    )

                logger.info(f"Power action {action.value} initiated successfully")

                # Wait for completion if requested
                if wait_for_completion:
                    success = self._wait_for_power_state_change(
                        session, system_uri, action, timeout
                    )
                    
                    return RedfishOperation(
                        success=success,
                        result=success,
                        response=reset_response,
                        error_message=None if success else "Power state change timeout",
                    )

                return RedfishOperation(
                    success=True,
                    result=True,
                    response=reset_response,
                )

        except Exception as e:
            logger.error(f"Failed to set power state: {e}")
            return RedfishOperation(
                success=False,
                error_message=str(e),
            )

    def power_on(self, system_id: str = "1", wait: bool = True) -> RedfishOperation[bool]:
        """Power on the system.

        Args:
            system_id: System identifier
            wait: Wait for power on to complete

        Returns:
            Operation result
        """
        return self.set_power_state(PowerAction.ON, system_id, wait)

    def power_off(self, system_id: str = "1", wait: bool = True, force: bool = False) -> RedfishOperation[bool]:
        """Power off the system.

        Args:
            system_id: System identifier
            wait: Wait for power off to complete
            force: Force immediate power off

        Returns:
            Operation result
        """
        action = PowerAction.FORCE_OFF if force else PowerAction.GRACEFUL_SHUTDOWN
        return self.set_power_state(action, system_id, wait)

    def restart(self, system_id: str = "1", wait: bool = True, force: bool = False) -> RedfishOperation[bool]:
        """Restart the system.

        Args:
            system_id: System identifier
            wait: Wait for restart to complete
            force: Force immediate restart

        Returns:
            Operation result
        """
        action = PowerAction.FORCE_RESTART if force else PowerAction.GRACEFUL_RESTART
        return self.set_power_state(action, system_id, wait)

    def _map_power_action(self, action: PowerAction, allowed_values: list) -> Optional[str]:
        """Map power action to Redfish reset type.

        Args:
            action: Power action
            allowed_values: Allowed reset types from Redfish

        Returns:
            Redfish reset type if supported
        """
        # Mapping from our actions to Redfish reset types
        action_mapping = {
            PowerAction.ON: ["On", "PowerOn"],
            PowerAction.GRACEFUL_SHUTDOWN: ["GracefulShutdown", "Nmi"],
            PowerAction.FORCE_OFF: ["ForceOff", "ImmediateOff"],
            PowerAction.GRACEFUL_RESTART: ["GracefulRestart", "PowerCycle"],
            PowerAction.FORCE_RESTART: ["ForceRestart", "ForceReset"],
        }

        possible_types = action_mapping.get(action, [])
        
        # Find first supported type
        for reset_type in possible_types:
            if reset_type in allowed_values:
                return reset_type

        return None

    def _wait_for_power_state_change(
        self, 
        session: RedfishSession, 
        system_uri: str, 
        action: PowerAction,
        timeout: int
    ) -> bool:
        """Wait for power state to change after action.

        Args:
            session: Redfish session
            system_uri: System URI
            action: Power action performed
            timeout: Timeout in seconds

        Returns:
            True if expected state reached
        """
        # Determine expected final state
        expected_states = {
            PowerAction.ON: [PowerState.ON],
            PowerAction.GRACEFUL_SHUTDOWN: [PowerState.OFF],
            PowerAction.FORCE_OFF: [PowerState.OFF],
            PowerAction.GRACEFUL_RESTART: [PowerState.ON],
            PowerAction.FORCE_RESTART: [PowerState.ON],
        }

        target_states = expected_states.get(action, [])
        if not target_states:
            return True  # No specific state to wait for

        start_time = time.time()
        check_interval = 5  # seconds

        logger.info(f"Waiting for power state change to {target_states}")

        while time.time() - start_time < timeout:
            try:
                response = session.get(system_uri)
                if response.success and response.data:
                    power_state_str = response.data.get("PowerState", "Unknown")
                    
                    try:
                        current_state = PowerState(power_state_str)
                        if current_state in target_states:
                            logger.info(f"Power state reached: {current_state.value}")
                            return True
                    except ValueError:
                        pass  # Unknown state, continue waiting

                time.sleep(check_interval)

            except Exception as e:
                logger.warning(f"Error checking power state: {e}")
                time.sleep(check_interval)

        logger.warning(f"Timeout waiting for power state change after {timeout}s")
        return False
