"""Network interface parser for system network configuration."""

import re
from typing import Any, Dict, List

from ..base import BaseParser, NetworkInterface


class NetworkParser(BaseParser):
    """Parser for network interface command outputs."""

    def parse_ip_addr(self, output: str) -> List[NetworkInterface]:
        """Parse ip addr show output."""
        interfaces = []
        current_interface = None

        for line in output.split("\n"):
            line = line.strip()

            # Interface line (e.g., "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500")
            if re.match(r"^\d+:", line):
                if current_interface:
                    interfaces.append(current_interface)

                parts = line.split()
                if len(parts) >= 2:
                    name = parts[1].rstrip(":")
                    state = "up" if "UP" in line else "down"
                    current_interface = NetworkInterface(
                        name=name, mac_address="", state=state
                    )

            # MAC address line (e.g., "link/ether 00:50:56:xx:xx:xx brd ff:ff:ff:ff:ff:ff")
            elif line.startswith("link/ether") and current_interface:
                parts = line.split()
                if len(parts) >= 2:
                    current_interface.mac_address = parts[1]

            # IP address line (e.g., "inet 192.168.1.100/24 brd 192.168.1.255 scope global eth0")
            elif line.startswith("inet ") and current_interface:
                parts = line.split()
                if len(parts) >= 2:
                    ip_cidr = parts[1]
                    if "/" in ip_cidr:
                        ip, cidr = ip_cidr.split("/")
                        current_interface.ip_address = ip
                        current_interface.netmask = self._cidr_to_netmask(int(cidr))

        # Add the last interface
        if current_interface:
            interfaces.append(current_interface)

        return interfaces

    def parse_ifconfig(self, output: str) -> List[NetworkInterface]:
        """Parse ifconfig output (alternative format)."""
        interfaces = []
        current_interface = None

        for line in output.split("\n"):
            line = line.strip()

            # Interface line (e.g., "eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>")
            if re.match(r"^[a-zA-Z0-9]+:", line):
                if current_interface:
                    interfaces.append(current_interface)

                name = line.split(":")[0]
                state = "up" if "UP" in line else "down"
                current_interface = NetworkInterface(
                    name=name, mac_address="", state=state
                )

            # MAC address line (e.g., "ether 00:50:56:xx:xx:xx")
            elif "ether " in line and current_interface:
                parts = line.split()
                ether_index = parts.index("ether")
                if ether_index + 1 < len(parts):
                    current_interface.mac_address = parts[ether_index + 1]

            # IP address line (e.g., "inet 192.168.1.100  netmask 255.255.255.0")
            elif "inet " in line and current_interface:
                parts = line.split()
                inet_index = parts.index("inet")
                if inet_index + 1 < len(parts):
                    current_interface.ip_address = parts[inet_index + 1]

                # Look for netmask
                if "netmask" in parts:
                    netmask_index = parts.index("netmask")
                    if netmask_index + 1 < len(parts):
                        current_interface.netmask = parts[netmask_index + 1]

        # Add the last interface
        if current_interface:
            interfaces.append(current_interface)

        return interfaces

    def _cidr_to_netmask(self, cidr: int) -> str:
        """Convert CIDR notation to netmask."""
        mask = (0xFFFFFFFF >> (32 - cidr)) << (32 - cidr)
        return f"{(mask >> 24) & 0xff}.{(mask >> 16) & 0xff}.{(mask >> 8) & 0xff}.{mask & 0xff}"

    def parse(self, output: str) -> Dict[str, Any]:
        """Parse network output and determine format automatically."""
        # Try to detect what type of network output this is
        if re.search(r"^\d+:", output, re.MULTILINE):
            # ip addr format
            interfaces = self.parse_ip_addr(output)
        elif re.search(r"^[a-zA-Z0-9]+:", output, re.MULTILINE):
            # ifconfig format
            interfaces = self.parse_ifconfig(output)
        else:
            self.logger.warning("Unknown network output format")
            return {"interfaces": []}

        return {
            "interfaces": [
                {
                    "name": iface.name,
                    "mac_address": iface.mac_address,
                    "ip_address": iface.ip_address,
                    "netmask": iface.netmask,
                    "state": iface.state,
                }
                for iface in interfaces
            ]
        }
