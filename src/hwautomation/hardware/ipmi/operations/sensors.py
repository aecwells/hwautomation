"""Sensor management operations for IPMI.

This module handles all sensor-related IPMI operations including
sensor data collection, monitoring, and threshold management.
"""

import subprocess
from typing import Dict, List, Optional

from hwautomation.logging import get_logger

from ..base import (
    IPMICommand,
    IPMICommandError,
    IPMICredentials,
    SensorReading,
)

logger = get_logger(__name__)


class SensorManager:
    """Manages IPMI sensor operations."""

    def __init__(self, timeout: int = 30):
        """Initialize sensor manager.

        Args:
            timeout: Command timeout in seconds
        """
        self.timeout = timeout

    def get_sensor_data(self, credentials: IPMICredentials) -> List[SensorReading]:
        """Get all sensor readings.

        Args:
            credentials: IPMI connection credentials

        Returns:
            List of sensor readings

        Raises:
            IPMICommandError: If command execution fails
        """
        try:
            result = self._execute_sensor_command(credentials, IPMICommand.SENSOR_LIST)

            if result.returncode != 0:
                raise IPMICommandError(
                    f"Sensor command failed: {result.stderr}",
                    "sensor list",
                    result.returncode,
                )

            return self._parse_sensor_output(result.stdout)

        except subprocess.TimeoutExpired:
            raise IPMICommandError(
                f"Sensor data collection timed out after {self.timeout}s", "sensor list"
            )
        except Exception as e:
            raise IPMICommandError(f"Failed to get sensor data: {e}", "sensor list")

    def get_sensor_by_name(
        self,
        credentials: IPMICredentials,
        sensor_name: str,
    ) -> Optional[SensorReading]:
        """Get specific sensor reading by name.

        Args:
            credentials: IPMI connection credentials
            sensor_name: Name of sensor to retrieve

        Returns:
            Sensor reading or None if not found
        """
        try:
            sensors = self.get_sensor_data(credentials)

            for sensor in sensors:
                if sensor.name.lower() == sensor_name.lower():
                    return sensor

            logger.warning(f"Sensor '{sensor_name}' not found")
            return None

        except Exception as e:
            logger.error(f"Failed to get sensor '{sensor_name}': {e}")
            return None

    def get_temperature_sensors(
        self, credentials: IPMICredentials
    ) -> List[SensorReading]:
        """Get all temperature sensors.

        Args:
            credentials: IPMI connection credentials

        Returns:
            List of temperature sensor readings
        """
        try:
            sensors = self.get_sensor_data(credentials)

            temperature_sensors = []
            for sensor in sensors:
                # Look for temperature indicators in name or unit
                if (
                    "temp" in sensor.name.lower()
                    or (sensor.unit and "degrees" in sensor.unit.lower())
                    or (sensor.unit and "c" in sensor.unit.lower())
                ):
                    temperature_sensors.append(sensor)

            return temperature_sensors

        except Exception as e:
            logger.error(f"Failed to get temperature sensors: {e}")
            return []

    def get_fan_sensors(self, credentials: IPMICredentials) -> List[SensorReading]:
        """Get all fan sensors.

        Args:
            credentials: IPMI connection credentials

        Returns:
            List of fan sensor readings
        """
        try:
            sensors = self.get_sensor_data(credentials)

            fan_sensors = []
            for sensor in sensors:
                # Look for fan indicators in name or unit
                if "fan" in sensor.name.lower() or (
                    sensor.unit and "rpm" in sensor.unit.lower()
                ):
                    fan_sensors.append(sensor)

            return fan_sensors

        except Exception as e:
            logger.error(f"Failed to get fan sensors: {e}")
            return []

    def get_power_sensors(self, credentials: IPMICredentials) -> List[SensorReading]:
        """Get all power-related sensors.

        Args:
            credentials: IPMI connection credentials

        Returns:
            List of power sensor readings
        """
        try:
            sensors = self.get_sensor_data(credentials)

            power_sensors = []
            for sensor in sensors:
                # Look for power indicators in name or unit
                if any(
                    keyword in sensor.name.lower()
                    for keyword in ["power", "watt", "volt", "amp"]
                ) or (
                    sensor.unit
                    and any(unit in sensor.unit.lower() for unit in ["w", "v", "a"])
                ):
                    power_sensors.append(sensor)

            return power_sensors

        except Exception as e:
            logger.error(f"Failed to get power sensors: {e}")
            return []

    def check_sensor_thresholds(
        self, credentials: IPMICredentials
    ) -> Dict[str, List[str]]:
        """Check for sensors exceeding thresholds.

        Args:
            credentials: IPMI connection credentials

        Returns:
            Dictionary with warning and critical sensor lists
        """
        result = {"warnings": [], "critical": []}

        try:
            sensors = self.get_sensor_data(credentials)

            for sensor in sensors:
                if sensor.status:
                    status_lower = sensor.status.lower()

                    if any(keyword in status_lower for keyword in ["warn", "caution"]):
                        result["warnings"].append(sensor.name)
                    elif any(
                        keyword in status_lower for keyword in ["crit", "fail", "error"]
                    ):
                        result["critical"].append(sensor.name)

        except Exception as e:
            logger.error(f"Failed to check sensor thresholds: {e}")

        return result

    def _execute_sensor_command(
        self,
        credentials: IPMICredentials,
        command: IPMICommand,
    ) -> subprocess.CompletedProcess:
        """Execute a sensor-related IPMI command.

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

    def _parse_sensor_output(self, output: str) -> List[SensorReading]:
        """Parse sensor data from IPMI output.

        Args:
            output: Raw IPMI sensor list output

        Returns:
            List of parsed sensor readings
        """
        sensors = []

        for line in output.strip().split("\n"):
            if not line.strip():
                continue

            try:
                sensor = self._parse_sensor_line(line)
                if sensor:
                    sensors.append(sensor)
            except Exception as e:
                logger.debug(f"Failed to parse sensor line '{line}': {e}")
                continue

        logger.info(f"Parsed {len(sensors)} sensor readings")
        return sensors

    def _parse_sensor_line(self, line: str) -> Optional[SensorReading]:
        """Parse a single sensor line from IPMI output.

        Args:
            line: Single line of sensor output

        Returns:
            Parsed sensor reading or None if parsing failed
        """
        # IPMI sensor output format is typically:
        # Sensor Name | Value | Units | Status | Lower Threshold | Upper Threshold

        parts = [part.strip() for part in line.split("|")]

        if len(parts) < 2:
            return None

        name = parts[0]
        value = parts[1] if len(parts) > 1 and parts[1] else None
        unit = parts[2] if len(parts) > 2 and parts[2] else None
        status = parts[3] if len(parts) > 3 and parts[3] else None
        lower_threshold = parts[4] if len(parts) > 4 and parts[4] else None
        upper_threshold = parts[5] if len(parts) > 5 and parts[5] else None

        # Clean up values
        if value and value.lower() in ["na", "n/a", "disabled", "no reading"]:
            value = None

        if unit and unit.lower() in ["na", "n/a", "unspecified"]:
            unit = None

        if status and status.lower() in ["na", "n/a"]:
            status = None

        return SensorReading(
            name=name,
            value=value,
            unit=unit,
            status=status,
            lower_threshold=lower_threshold,
            upper_threshold=upper_threshold,
        )
