"""
IPMI management module for hardware automation.
"""

import subprocess
from typing import Dict, List, Optional
from ..utils.network import get_ipmi_ip_via_ssh


class IpmiManager:
    """Manages IPMI operations for servers"""
    
    def __init__(self, username: str = "ADMIN", timeout: int = 30):
        """
        Initialize IPMI manager.
        
        Args:
            username: IPMI username
            timeout: Command timeout in seconds
        """
        self.username = username
        self.timeout = timeout
    
    def get_ipmi_ips_from_servers(self, server_ips: List[str], ssh_username: str = "ubuntu") -> List[str]:
        """
        Get IPMI IPs from a list of server IPs via SSH.
        
        Args:
            server_ips: List of server IP addresses
            ssh_username: SSH username for connecting to servers
            
        Returns:
            List of discovered IPMI IP addresses
        """
        ipmi_ips = []
        
        for server_ip in server_ips:
            if server_ip and server_ip != 'Unreachable':
                ipmi_ip = get_ipmi_ip_via_ssh(server_ip, ssh_username, self.timeout)
                if ipmi_ip:
                    ipmi_ips.append(ipmi_ip)
                    print(f"Found IPMI IP {ipmi_ip} for server {server_ip}")
                else:
                    print(f"Could not get IPMI IP from {server_ip}")
        
        return ipmi_ips
    
    def set_ipmi_password(self, server_ip: str, new_password: str, user_id: int = 2, ssh_username: str = "ubuntu") -> bool:
        """
        Set IPMI password via SSH to the server OS.
        
        Args:
            server_ip: Server IP address to SSH to
            new_password: New IPMI password
            user_id: IPMI user ID (default 2)
            ssh_username: SSH username
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = [
                'ssh', '-q', '-o', 'StrictHostKeyChecking=no',
                f'{ssh_username}@{server_ip}',
                f'sudo ipmitool user set password {user_id} {new_password}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            
            if result.returncode == 0:
                print(f"Successfully set IPMI password for {server_ip}")
                return True
            else:
                print(f"Failed to set IPMI password for {server_ip}: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error setting IPMI password for {server_ip}: {e}")
            return False
    
    def set_ipmi_passwords_bulk(self, server_ips: List[str], password: str, ssh_username: str = "ubuntu") -> Dict[str, bool]:
        """
        Set IPMI passwords for multiple servers.
        
        Args:
            server_ips: List of server IP addresses
            password: IPMI password to set
            ssh_username: SSH username
            
        Returns:
            Dictionary mapping server IPs to success status
        """
        results = {}
        
        for server_ip in server_ips:
            results[server_ip] = self.set_ipmi_password(server_ip, password, ssh_username=ssh_username)
        
        return results
    
    def get_power_status(self, ipmi_ip: str, password: str) -> Optional[str]:
        """
        Get power status via IPMI.
        
        Args:
            ipmi_ip: IPMI IP address
            password: IPMI password
            
        Returns:
            Power status string or None if failed
        """
        try:
            cmd = [
                'ipmitool', '-I', 'lanplus', '-H', ipmi_ip,
                '-U', self.username, '-P', password,
                'chassis', 'power', 'status'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            
            if result.returncode == 0:
                # Parse output like "Chassis Power is on"
                output = result.stdout.strip()
                if 'on' in output.lower():
                    return 'ON'
                elif 'off' in output.lower():
                    return 'OFF'
                else:
                    return output
            else:
                print(f"Failed to get power status from {ipmi_ip}: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"Error getting power status from {ipmi_ip}: {e}")
            return None
    
    def set_power_state(self, ipmi_ip: str, password: str, action: str) -> bool:
        """
        Set power state via IPMI.
        
        Args:
            ipmi_ip: IPMI IP address
            password: IPMI password
            action: Power action ('on', 'off', 'cycle', 'reset')
            
        Returns:
            True if successful, False otherwise
        """
        valid_actions = ['on', 'off', 'cycle', 'reset']
        if action.lower() not in valid_actions:
            print(f"Invalid power action: {action}. Valid actions: {valid_actions}")
            return False
        
        try:
            cmd = [
                'ipmitool', '-I', 'lanplus', '-H', ipmi_ip,
                '-U', self.username, '-P', password,
                'chassis', 'power', action.lower()
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            
            if result.returncode == 0:
                print(f"Successfully executed power {action} on {ipmi_ip}")
                return True
            else:
                print(f"Failed to execute power {action} on {ipmi_ip}: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error executing power {action} on {ipmi_ip}: {e}")
            return False
    
    def get_sensor_data(self, ipmi_ip: str, password: str) -> Optional[Dict]:
        """
        Get sensor data via IPMI.
        
        Args:
            ipmi_ip: IPMI IP address
            password: IPMI password
            
        Returns:
            Dictionary of sensor data or None if failed
        """
        try:
            cmd = [
                'ipmitool', '-I', 'lanplus', '-H', ipmi_ip,
                '-U', self.username, '-P', password,
                'sdr', 'list'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            
            if result.returncode == 0:
                # Parse sensor data (simplified)
                sensors = {}
                for line in result.stdout.split('\n'):
                    if '|' in line:
                        parts = [p.strip() for p in line.split('|')]
                        if len(parts) >= 3:
                            sensor_name = parts[0]
                            sensor_value = parts[1]
                            sensor_status = parts[2]
                            sensors[sensor_name] = {
                                'value': sensor_value,
                                'status': sensor_status
                            }
                return sensors
            else:
                print(f"Failed to get sensor data from {ipmi_ip}: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"Error getting sensor data from {ipmi_ip}: {e}")
            return None
