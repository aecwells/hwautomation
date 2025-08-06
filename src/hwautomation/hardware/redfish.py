"""
RedFish API management module for hardware automation.
"""

import requests
import json
from typing import Dict, List, Optional, Any
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings for RedFish (common with self-signed certs)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class RedFishManager:
    """Manages RedFish API operations for servers"""
    
    def __init__(self, username: str = "ADMIN", timeout: int = 30, verify_ssl: bool = False):
        """
        Initialize RedFish manager.
        
        Args:
            username: RedFish username
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.username = username
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.sessions = {}  # Cache authentication tokens
    
    def authenticate(self, ipmi_ip: str, password: str) -> Optional[str]:
        """
        Authenticate with RedFish API and get session token.
        
        Args:
            ipmi_ip: IPMI/BMC IP address
            password: Authentication password
            
        Returns:
            Authentication token or None if failed
        """
        try:
            headers = {'Content-Type': 'application/json'}
            data = {
                "UserName": self.username,
                "Password": password
            }
            
            response = requests.post(
                f'https://{ipmi_ip}/redfish/v1/SessionService/Sessions',
                headers=headers,
                json=data,
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            
            if response.status_code == 201:
                # Extract token from response headers
                token = response.headers.get('X-Auth-Token')
                if token:
                    self.sessions[ipmi_ip] = token
                    print(f"Successfully authenticated to {ipmi_ip}")
                    return token
                else:
                    print(f"No authentication token received from {ipmi_ip}")
                    return None
            else:
                print(f"Failed to authenticate to {ipmi_ip}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error authenticating to {ipmi_ip}: {e}")
            return None
    
    def get_token(self, ipmi_ip: str, password: str) -> Optional[str]:
        """Get authentication token, using cached token if available"""
        if ipmi_ip in self.sessions:
            return self.sessions[ipmi_ip]
        return self.authenticate(ipmi_ip, password)
    
    def make_request(self, ipmi_ip: str, password: str, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """
        Make authenticated RedFish API request.
        
        Args:
            ipmi_ip: IPMI/BMC IP address
            password: Authentication password
            method: HTTP method (GET, POST, PATCH, etc.)
            endpoint: API endpoint (e.g., '/redfish/v1/Systems')
            data: Request data for POST/PATCH requests
            
        Returns:
            Response JSON data or None if failed
        """
        token = self.get_token(ipmi_ip, password)
        if not token:
            return None
        
        try:
            headers = {'X-Auth-Token': token}
            if data:
                headers['Content-Type'] = 'application/json'
            
            url = f'https://{ipmi_ip}{endpoint}'
            
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                json=data,
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            
            if response.status_code in [200, 201, 204]:
                return response.json() if response.content else {}
            else:
                print(f"RedFish request failed: HTTP {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error making RedFish request to {ipmi_ip}: {e}")
            return None
    
    def get_system_info(self, ipmi_ip: str, password: str) -> Optional[Dict]:
        """Get system information via RedFish"""
        return self.make_request(ipmi_ip, password, 'GET', '/redfish/v1/Systems/1')
    
    def get_power_state(self, ipmi_ip: str, password: str) -> Optional[str]:
        """Get system power state via RedFish"""
        system_info = self.get_system_info(ipmi_ip, password)
        if system_info:
            return system_info.get('PowerState')
        return None
    
    def set_power_state(self, ipmi_ip: str, password: str, action: str) -> bool:
        """
        Set system power state via RedFish.
        
        Args:
            ipmi_ip: IPMI/BMC IP address
            password: Authentication password
            action: Power action ('On', 'ForceOff', 'ForceRestart', 'GracefulShutdown', 'GracefulRestart')
            
        Returns:
            True if successful, False otherwise
        """
        valid_actions = ['On', 'ForceOff', 'ForceRestart', 'GracefulShutdown', 'GracefulRestart']
        if action not in valid_actions:
            print(f"Invalid power action: {action}. Valid actions: {valid_actions}")
            return False
        
        data = {"ResetType": action}
        response = self.make_request(ipmi_ip, password, 'POST', '/redfish/v1/Systems/1/Actions/ComputerSystem.Reset', data)
        
        if response is not None:
            print(f"Successfully executed power action '{action}' on {ipmi_ip}")
            return True
        else:
            print(f"Failed to execute power action '{action}' on {ipmi_ip}")
            return False
    
    def get_kcs_status(self, ipmi_ip: str, password: str) -> Optional[Dict]:
        """Get KCS interface status (Supermicro specific)"""
        return self.make_request(ipmi_ip, password, 'GET', '/redfish/v1/Managers/1/Oem/Supermicro/KCSInterface')
    
    def set_kcs_privilege(self, ipmi_ip: str, password: str, privilege: str) -> bool:
        """
        Set KCS privilege level (Supermicro specific).
        
        Args:
            ipmi_ip: IPMI/BMC IP address
            password: Authentication password
            privilege: Privilege level ('User', 'Operator', 'Administrator')
            
        Returns:
            True if successful, False otherwise
        """
        data = {"Privilege": privilege}
        response = self.make_request(ipmi_ip, password, 'PATCH', '/redfish/v1/Managers/1/Oem/Supermicro/KCSInterface', data)
        
        if response is not None:
            print(f"Successfully set KCS privilege to '{privilege}' on {ipmi_ip}")
            return True
        else:
            print(f"Failed to set KCS privilege on {ipmi_ip}")
            return False
    
    def get_host_interface_config(self, ipmi_ip: str, password: str) -> Optional[Dict]:
        """Get host interface configuration"""
        return self.make_request(ipmi_ip, password, 'GET', '/redfish/v1/Managers/1/HostInterfaces/1')
    
    def set_host_interface_enabled(self, ipmi_ip: str, password: str, enabled: bool) -> bool:
        """
        Enable or disable host interface.
        
        Args:
            ipmi_ip: IPMI/BMC IP address
            password: Authentication password
            enabled: Whether to enable the interface
            
        Returns:
            True if successful, False otherwise
        """
        data = {"InterfaceEnabled": enabled}
        response = self.make_request(ipmi_ip, password, 'PATCH', '/redfish/v1/Managers/1/HostInterfaces/1', data)
        
        if response is not None:
            print(f"Successfully set host interface enabled={enabled} on {ipmi_ip}")
            return True
        else:
            print(f"Failed to set host interface configuration on {ipmi_ip}")
            return False
    
    def get_thermal_info(self, ipmi_ip: str, password: str) -> Optional[Dict]:
        """Get thermal information (temperatures, fans)"""
        return self.make_request(ipmi_ip, password, 'GET', '/redfish/v1/Chassis/1/Thermal')
    
    def get_power_info(self, ipmi_ip: str, password: str) -> Optional[Dict]:
        """Get power consumption information"""
        return self.make_request(ipmi_ip, password, 'GET', '/redfish/v1/Chassis/1/Power')
    
    def get_firmware_inventory(self, ipmi_ip: str, password: str) -> Optional[Dict]:
        """Get firmware inventory"""
        return self.make_request(ipmi_ip, password, 'GET', '/redfish/v1/UpdateService/FirmwareInventory')
    
    def logout(self, ipmi_ip: str, password: str) -> bool:
        """Logout and invalidate session token"""
        token = self.sessions.get(ipmi_ip)
        if not token:
            return True
        
        try:
            headers = {'X-Auth-Token': token}
            response = requests.delete(
                f'https://{ipmi_ip}/redfish/v1/SessionService/Sessions/{token}',
                headers=headers,
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            
            # Remove from cache regardless of response
            self.sessions.pop(ipmi_ip, None)
            
            if response.status_code == 204:
                print(f"Successfully logged out from {ipmi_ip}")
                return True
            else:
                print(f"Logout may have failed from {ipmi_ip}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error logging out from {ipmi_ip}: {e}")
            # Still remove from cache
            self.sessions.pop(ipmi_ip, None)
            return False
    
    def logout_all(self):
        """Logout from all active sessions"""
        for ipmi_ip in list(self.sessions.keys()):
            self.logout(ipmi_ip, "")  # Password not needed for logout
