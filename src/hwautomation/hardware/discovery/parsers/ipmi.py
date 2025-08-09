"""IPMI configuration parser for BMC network settings."""

import re
from typing import Any, Dict

from ..base import BaseParser, IPMIInfo


class IpmiParser(BaseParser):
    """Parser for IPMI tool command outputs."""

    def parse_lan_config(self, output: str) -> IPMIInfo:
        """Parse ipmitool lan print output."""
        ipmi_info = IPMIInfo()

        for line in output.split("\n"):
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                if key == "IP Address":
                    ipmi_info.ip_address = value if value != "0.0.0.0" else None
                elif key == "MAC Address":
                    ipmi_info.mac_address = value
                elif key == "Default Gateway IP":
                    ipmi_info.gateway = value if value != "0.0.0.0" else None
                elif key == "Subnet Mask":
                    ipmi_info.netmask = value if value != "0.0.0.0" else None
                elif key == "802.1q VLAN ID":
                    try:
                        if value.lower() != "disabled":
                            ipmi_info.vlan_id = int(value)
                    except ValueError:
                        pass

        # Mark as enabled if we have a valid IP
        ipmi_info.enabled = ipmi_info.ip_address is not None
        return ipmi_info

    def parse_channel_info(self, output: str) -> Dict[str, Any]:
        """Parse IPMI channel information."""
        channel_info = {}

        for line in output.split("\n"):
            line = line.strip()
            if "Channel" in line and ":" in line:
                try:
                    # Extract channel number
                    match = re.search(r"Channel\s+(\d+)", line)
                    if match:
                        channel_info["channel"] = int(match.group(1))
                except ValueError:
                    pass

        return channel_info

    def parse_bmc_info(self, output: str) -> Dict[str, Any]:
        """Parse BMC device information."""
        bmc_info = {}

        for line in output.split("\n"):
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()

                if key in ["device_id", "device_revision", "firmware_revision"]:
                    bmc_info[key] = value

        return bmc_info

    def parse(self, output: str) -> Dict[str, Any]:
        """Parse IPMI output and determine content type automatically."""
        # Try to detect what type of IPMI output this is
        if "IP Address" in output and "MAC Address" in output:
            ipmi_info = self.parse_lan_config(output)
            return {
                "ip_address": ipmi_info.ip_address,
                "mac_address": ipmi_info.mac_address,
                "gateway": ipmi_info.gateway,
                "netmask": ipmi_info.netmask,
                "vlan_id": ipmi_info.vlan_id,
                "enabled": ipmi_info.enabled,
            }
        elif "Channel" in output:
            return self.parse_channel_info(output)
        elif "Device ID" in output:
            return self.parse_bmc_info(output)
        else:
            self.logger.warning("Unknown IPMI output format")
            return {}
