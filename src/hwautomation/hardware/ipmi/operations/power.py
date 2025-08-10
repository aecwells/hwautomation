"""Power management operations for IPMI.

This module handles all power-related IPMI operations including
status checking, power state changes, and power cycling.
"""

import subprocess
import time
from typing import Optional

from hwautomation.logging import get_logger

from ..base import (
    BaseIPMIHandler,
    IPMICommand,
    IPMICommandError,
    IPMICredentials,
    PowerState,
    PowerStatus,
)

logger = get_logger(__name__)


class PowerManager:
    """Manages IPMI power operations."""

    def __init__(self, timeout: int = 30):
        """Initialize power manager.

        Args:
            timeout: Command timeout in seconds
        """
        self.timeout = timeout

    def get_power_status(self, credentials: IPMICredentials) -> PowerStatus:
        """Get current power status.

        Args:
            credentials: IPMI connection credentials

        Returns:
            Power status information

        Raises:
            IPMICommandError: If command execution fails
        """
        try:
            result = self._execute_power_command(credentials, IPMICommand.POWER_STATUS)

            # Parse power status from output
            output = result.stdout.strip()

            # Common power status patterns
            if "Chassis Power is on" in output or "Power is on" in output:
                state = "on"
            elif "Chassis Power is off" in output or "Power is off" in output:
                state = "off"
            else:
                # Try to extract state from output
                state = self._parse_power_state(output)

            return PowerStatus(
                state=state,
                raw_output=output,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            )

        except subprocess.TimeoutExpired:
            raise IPMICommandError(
                f"Power status check timed out after {self.timeout}s", "power status"
            )
        except Exception as e:
            raise IPMICommandError(f"Failed to get power status: {e}", "power status")

    def set_power_state(
        self,
        credentials: IPMICredentials,
        state: PowerState,
        wait_for_completion: bool = True,
    ) -> bool:
        """Set power state.

        Args:
            credentials: IPMI connection credentials
            state: Target power state
            wait_for_completion: Wait for power state change to complete

        Returns:
            True if successful, False otherwise
        """
        try:
            # Map PowerState to IPMI command
            command_map = {
                PowerState.ON: IPMICommand.POWER_ON,
                PowerState.OFF: IPMICommand.POWER_OFF,
                PowerState.RESET: IPMICommand.POWER_RESET,
                PowerState.CYCLE: IPMICommand.POWER_CYCLE,
                PowerState.SOFT: IPMICommand.POWER_SOFT,
            }

            command = command_map.get(state)
            if not command:
                logger.error(f"Unsupported power state: {state}")
                return False

            logger.info(
                f"Setting power state to {state.value} for {credentials.ip_address}"
            )

            result = self._execute_power_command(credentials, command)

            if result.returncode == 0:
                logger.info(f"Power command successful: {command.value}")

                if wait_for_completion:
                    return self._wait_for_power_state(credentials, state)
                return True
            else:
                logger.error(f"Power command failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to set power state {state.value}: {e}")
            return False

    def power_cycle_with_delay(
        self,
        credentials: IPMICredentials,
        off_delay: int = 10,
        on_delay: int = 5,
    ) -> bool:
        """Perform controlled power cycle with configurable delays.

        Args:
            credentials: IPMI connection credentials
            off_delay: Seconds to wait after power off
            on_delay: Seconds to wait after power on

        Returns:
            True if successful, False otherwise
        """
        try:
            # Power off
            if not self.set_power_state(
                credentials, PowerState.OFF, wait_for_completion=True
            ):
                logger.error("Failed to power off system")
                return False

            logger.info(f"Waiting {off_delay} seconds before power on")
            time.sleep(off_delay)

            # Power on
            if not self.set_power_state(
                credentials, PowerState.ON, wait_for_completion=True
            ):
                logger.error("Failed to power on system")
                return False

            logger.info(f"Waiting {on_delay} seconds for system stabilization")
            time.sleep(on_delay)

            return True

        except Exception as e:
            logger.error(f"Power cycle failed: {e}")
            return False

    def _execute_power_command(
        self,
        credentials: IPMICredentials,
        command: IPMICommand,
    ) -> subprocess.CompletedProcess:
        """Execute a power-related IPMI command.

        Args:
            credentials: IPMI connection credentials
            command: IPMI command to execute

        Returns:
            Completed process result
        """
        cmd_args = [
            "ipmitool",
            "-I",
            credentials.interface,
            "-H",
            credentials.ip_address,
            "-U",
            credentials.username,
            "-P",
            credentials.password,
        ]

        cmd_args.extend(command.value.split())

        return subprocess.run(
            cmd_args,
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )

    def _parse_power_state(self, output: str) -> str:
        """Parse power state from IPMI output.

        Args:
            output: Raw IPMI command output

        Returns:
            Parsed power state
        """
        output_lower = output.lower()

        if "on" in output_lower:
            return "on"
        elif "off" in output_lower:
            return "off"
        else:
            logger.warning(f"Could not parse power state from: {output}")
            return "unknown"

    def _wait_for_power_state(
        self,
        credentials: IPMICredentials,
        target_state: PowerState,
        max_wait: int = 60,
        check_interval: int = 2,
    ) -> bool:
        """Wait for power state to reach target.

        Args:
            credentials: IPMI connection credentials
            target_state: Target power state to wait for
            max_wait: Maximum wait time in seconds
            check_interval: Check interval in seconds

        Returns:
            True if target state reached, False if timeout
        """
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                current_status = self.get_power_status(credentials)

                # Check if we've reached the target state
                if target_state == PowerState.ON and current_status.state == "on":
                    return True
                elif target_state == PowerState.OFF and current_status.state == "off":
                    return True

                time.sleep(check_interval)

            except Exception as e:
                logger.warning(f"Error checking power state: {e}")
                time.sleep(check_interval)

        logger.warning(f"Timeout waiting for power state {target_state.value}")
        return False
