"""
Network utility functions for hardware automation.
."""

import logging
import platform
import subprocess
from pathlib import Path
from typing import Optional, Tuple

import paramiko

logger = logging.getLogger(__name__)


def ping_host(ip_address: str, timeout: int = 5) -> bool:
    """
    Test if an IP address is reachable via ping.

    Args:
        ip_address: IP address to ping
        timeout: Timeout in seconds

    Returns:
        True if host is reachable, False otherwise
    ."""
    try:
        # Determine ping command based on OS
        system = platform.system().lower()

        if system == "windows":
            cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), ip_address]
        else:
            cmd = ["ping", "-c", "1", "-W", str(timeout), ip_address]

        result = subprocess.run(cmd, capture_output=True, timeout=timeout + 2)
        return result.returncode == 0

    except subprocess.TimeoutExpired:
        return False
    except Exception as e:
        print(f"Error pinging {ip_address}: {e}")
        return False


def get_ipmi_ip_via_ssh(
    server_ip: str, username: str = "ubuntu", timeout: int = 30
) -> Optional[str]:
    """
    SSH to server and get IPMI IP using ipmitool.

    Args:
        server_ip: IP address of the server to SSH to
        username: SSH username
        timeout: SSH timeout in seconds

    Returns:
        IPMI IP address if found, None otherwise
    ."""
    try:
        cmd = [
            "ssh",
            "-q",
            "-o",
            "StrictHostKeyChecking=no",
            f"{username}@{server_ip}",
            'sudo ipmitool lan print 1 | grep "IP Address" | grep "192" | cut -b 27-40',
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

        if result.returncode == 0:
            ipmi_ip = result.stdout.strip()
            return ipmi_ip if ipmi_ip else None
        else:
            print(f"SSH command failed for {server_ip}: {result.stderr}")
            return None

    except subprocess.TimeoutExpired:
        print(f"Timeout getting IPMI IP from {server_ip}")
        return None
    except Exception as e:
        print(f"Error getting IPMI IP from {server_ip}: {e}")
        return None


def test_port_connectivity(host: str, port: int, timeout: int = 5) -> bool:
    """
    Test if a TCP port is reachable on a host.

    Args:
        host: Hostname or IP address
        port: Port number
        timeout: Connection timeout in seconds

    Returns:
        True if port is reachable, False otherwise
    ."""
    import socket

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Error testing port {port} on {host}: {e}")
        return False


def resolve_hostname(hostname: str) -> Optional[str]:
    """
    Resolve hostname to IP address.

    Args:
        hostname: Hostname to resolve

    Returns:
        IP address if resolution successful, None otherwise
    ."""
    import socket

    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror as e:
        print(f"Failed to resolve {hostname}: {e}")
        return None


class SSHManager:
    """
    SSH connection manager for remote operations

    Provides a simplified interface for SSH connections with proper
    error handling and resource management.
    ."""

    def __init__(self, config: dict = None):
        """
        Initialize SSH manager

        Args:
            config: SSH configuration dictionary
        ."""
        self.config = config or {}
        self.default_username = self.config.get("default_username", "ubuntu")
        self.default_timeout = self.config.get("timeout", 60)
        self.key_file = self.config.get("key_file")

    def connect(
        self,
        host: str,
        username: str = None,
        password: str = None,
        key_file: str = None,
        timeout: int = None,
    ) -> "SSHClient":
        """
        Create SSH connection to host

        Args:
            host: Target host IP or hostname
            username: SSH username (defaults to config or 'ubuntu')
            password: SSH password (if not using keys)
            key_file: Path to SSH private key file
            timeout: Connection timeout in seconds

        Returns:
            SSHClient instance

        Raises:
            Exception: If connection fails
        ."""
        username = username or self.default_username
        timeout = timeout or self.default_timeout
        key_file = key_file or self.key_file

        client = SSHClient(host, username, password, key_file, timeout)
        client.connect()
        return client


class SSHClient:
    """
    Individual SSH client connection

    Manages a single SSH connection with methods for command execution
    and file transfer operations.
    ."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str = None,
        key_file: str = None,
        timeout: int = 60,
    ):
        """
        Initialize SSH client

        Args:
            host: Target host IP or hostname
            username: SSH username
            password: SSH password (if not using keys)
            key_file: Path to SSH private key file
            timeout: Connection timeout in seconds
        ."""
        self.host = host
        self.username = username
        self.password = password
        self.key_file = key_file
        self.timeout = timeout
        self.client = None
        self.sftp = None

    def connect(self):
        """Establish SSH connection."""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            connect_kwargs = {
                "hostname": self.host,
                "username": self.username,
                "timeout": self.timeout,
            }

            if self.password:
                connect_kwargs["password"] = self.password
            elif self.key_file:
                connect_kwargs["key_filename"] = self.key_file

            self.client.connect(**connect_kwargs)
            logger.info(f"SSH connection established to {self.host}")

        except Exception as e:
            logger.error(f"SSH connection failed to {self.host}: {e}")
            raise

    def exec_command(self, command: str) -> Tuple[str, str, int]:
        """
        Execute command on remote host

        Args:
            command: Command to execute

        Returns:
            Tuple of (stdout, stderr, exit_code)
        ."""
        if not self.client:
            raise Exception("SSH client not connected")

        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()

            stdout_text = stdout.read().decode("utf-8")
            stderr_text = stderr.read().decode("utf-8")

            return stdout_text, stderr_text, exit_code

        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            raise

    def upload_file(self, local_path: str, remote_path: str):
        """
        Upload file to remote host

        Args:
            local_path: Local file path
            remote_path: Remote file path
        ."""
        if not self.client:
            raise Exception("SSH client not connected")

        try:
            if not self.sftp:
                self.sftp = self.client.open_sftp()

            self.sftp.put(local_path, remote_path)
            logger.info(f"File uploaded: {local_path} -> {remote_path}")

        except Exception as e:
            logger.error(f"File upload failed: {e}")
            raise

    def download_file(self, remote_path: str, local_path: str):
        """
        Download file from remote host

        Args:
            remote_path: Remote file path
            local_path: Local file path
        ."""
        if not self.client:
            raise Exception("SSH client not connected")

        try:
            if not self.sftp:
                self.sftp = self.client.open_sftp()

            # Ensure local directory exists
            local_dir = Path(local_path).parent
            local_dir.mkdir(parents=True, exist_ok=True)

            self.sftp.get(remote_path, local_path)
            logger.info(f"File downloaded: {remote_path} -> {local_path}")

        except Exception as e:
            logger.error(f"File download failed: {e}")
            raise

    def close(self):
        """Close SSH connection."""
        try:
            if self.sftp:
                self.sftp.close()
                self.sftp = None

            if self.client:
                self.client.close()
                self.client = None

            logger.info(f"SSH connection closed to {self.host}")

        except Exception as e:
            logger.error(f"Error closing SSH connection: {e}")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
