"""DMI decode output parser for system hardware information."""

import re
from typing import Any, Dict

from ..base import BaseParser, SystemInfo


class DmidecodeParser(BaseParser):
    """Parser for dmidecode command output."""

    def parse_system_info(self, output: str) -> SystemInfo:
        """Parse dmidecode system output."""
        system_info = SystemInfo()

        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("Manufacturer:"):
                system_info.manufacturer = line.split(":", 1)[1].strip()
            elif line.startswith("Product Name:"):
                system_info.product_name = line.split(":", 1)[1].strip()
            elif line.startswith("Serial Number:"):
                system_info.serial_number = line.split(":", 1)[1].strip()
            elif line.startswith("UUID:"):
                system_info.uuid = line.split(":", 1)[1].strip()

        return system_info

    def parse_bios_info(self, output: str) -> Dict[str, str]:
        """Parse dmidecode BIOS output."""
        bios_info = {}

        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("Version:"):
                bios_info["version"] = line.split(":", 1)[1].strip()
            elif line.startswith("Release Date:"):
                bios_info["date"] = line.split(":", 1)[1].strip()

        return bios_info

    def parse_cpu_info(self, output: str) -> Dict[str, Any]:
        """Parse lscpu output."""
        cpu_info: Dict[str, Any] = {}

        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("Model name:"):
                cpu_info["model"] = line.split(":", 1)[1].strip()
            elif line.startswith("CPU(s):"):
                try:
                    cpu_info["cores"] = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass

        return cpu_info

    def parse_memory_info(self, output: str) -> Dict[str, Any]:
        """Parse free command output for total memory."""
        memory_info = {}

        for line in output.split("\n"):
            if line.startswith("Mem:"):
                parts = line.split()
                if len(parts) >= 2:
                    memory_info["total"] = parts[1]  # Total memory in KB
                    break

        return memory_info

    def parse(self, output: str) -> Dict[str, Any]:
        """Parse dmidecode output and determine content type automatically."""
        # Try to detect what type of dmidecode output this is
        if "System Information" in output:
            system_info = self.parse_system_info(output)
            return {
                "manufacturer": system_info.manufacturer,
                "product_name": system_info.product_name,
                "serial_number": system_info.serial_number,
                "uuid": system_info.uuid,
            }
        elif "BIOS Information" in output:
            return self.parse_bios_info(output)
        elif "Model name:" in output:
            return self.parse_cpu_info(output)
        elif "Mem:" in output:
            return self.parse_memory_info(output)
        else:
            self.logger.warning("Unknown dmidecode output format")
            return {}
