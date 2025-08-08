"""
Unit tests for Firmware Manager - Phase 4 Implementation
"""

import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.hwautomation.hardware.firmware_manager import (
    FirmwareInfo,
    FirmwareManager,
    FirmwareRepository,
    FirmwareType,
    FirmwareUpdateException,
    FirmwareUpdateResult,
    UpdatePolicy,
    UpdatePriority,
)


class TestFirmwareManager:
    """Test suite for FirmwareManager"""

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary firmware configuration file"""
        config_content = """
firmware_repository:
  base_path: "/tmp/test_firmware"
  download_enabled: true
  auto_verify: true
  vendors:
    supermicro:
      display_name: "Super Micro Computer Inc."
      bios:
        update_method: "redfish"
        estimated_time: 480
      bmc:
        update_method: "redfish"
        estimated_time: 360
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            yield f.name
        os.unlink(f.name)

    @pytest.fixture
    def firmware_manager(self, temp_config_file):
        """Create FirmwareManager instance with test configuration"""
        return FirmwareManager(config_path=temp_config_file)

    def test_initialization(self, firmware_manager):
        """Test FirmwareManager initialization"""
        assert firmware_manager is not None
        assert firmware_manager.repository is not None
        assert firmware_manager.vendor_tools is not None
        assert isinstance(firmware_manager.repository, FirmwareRepository)

    def test_get_vendor_info(self, firmware_manager):
        """Test vendor information retrieval"""
        # Test known device type
        vendor_info = firmware_manager._get_vendor_info("a1.c5.large")
        assert vendor_info["vendor"] == "hpe"
        assert vendor_info["model"] == "Gen10"

        # Test unknown device type
        vendor_info = firmware_manager._get_vendor_info("unknown.device")
        assert vendor_info["vendor"] == "unknown"

    def test_compare_versions(self, firmware_manager):
        """Test firmware version comparison"""
        # Different versions should require update
        assert firmware_manager._compare_versions("1.0.0", "1.1.0") == True

        # Same versions should not require update
        assert firmware_manager._compare_versions("1.0.0", "1.0.0") == False

        # Unknown versions should not require update
        assert firmware_manager._compare_versions("unknown", "1.0.0") == False

    def test_determine_update_priority(self, firmware_manager):
        """Test update priority determination"""
        # BMC updates should be critical
        priority = firmware_manager._determine_update_priority(
            FirmwareType.BMC, "1.0.0", "1.1.0"
        )
        assert priority == UpdatePriority.CRITICAL

        # BIOS updates should be high
        priority = firmware_manager._determine_update_priority(
            FirmwareType.BIOS, "1.0.0", "1.1.0"
        )
        assert priority == UpdatePriority.HIGH

    def test_estimate_update_time(self, firmware_manager):
        """Test update time estimation"""
        # BIOS should have longer estimate
        bios_time = firmware_manager._estimate_update_time(FirmwareType.BIOS)
        assert bios_time == 480

        # BMC should be shorter
        bmc_time = firmware_manager._estimate_update_time(FirmwareType.BMC)
        assert bmc_time == 360

    def test_sort_firmware_updates(self, firmware_manager):
        """Test firmware update sorting"""
        firmware_list = [
            FirmwareInfo(
                firmware_type=FirmwareType.BIOS,
                current_version="1.0.0",
                latest_version="1.1.0",
                update_required=True,
                priority=UpdatePriority.NORMAL,
            ),
            FirmwareInfo(
                firmware_type=FirmwareType.BMC,
                current_version="1.0.0",
                latest_version="1.1.0",
                update_required=True,
                priority=UpdatePriority.CRITICAL,
            ),
        ]

        sorted_firmware = firmware_manager._sort_firmware_updates(firmware_list)

        # Critical BMC should come before normal BIOS
        assert sorted_firmware[0].firmware_type == FirmwareType.BMC
        assert sorted_firmware[0].priority == UpdatePriority.CRITICAL
        assert sorted_firmware[1].firmware_type == FirmwareType.BIOS

    @pytest.mark.asyncio
    async def test_get_mock_firmware_versions(self, firmware_manager):
        """Test mock firmware version retrieval"""
        # Test HPE vendor
        versions = await firmware_manager._get_mock_firmware_versions(
            "192.168.1.100", {"vendor": "hpe"}
        )
        assert FirmwareType.BIOS in versions
        assert FirmwareType.BMC in versions
        assert versions[FirmwareType.BIOS] == "U30_v2.50"

        # Test Supermicro vendor
        versions = await firmware_manager._get_mock_firmware_versions(
            "192.168.1.100", {"vendor": "supermicro"}
        )
        assert versions[FirmwareType.BIOS] == "3.4"

    @pytest.mark.asyncio
    async def test_check_firmware_versions(self, firmware_manager):
        """Test firmware version checking"""
        device_type = "a1.c5.large"
        target_ip = "192.168.1.100"
        username = "admin"
        password = "password"

        firmware_info = await firmware_manager.check_firmware_versions(
            device_type, target_ip, username, password
        )

        assert isinstance(firmware_info, dict)
        assert FirmwareType.BIOS in firmware_info
        assert FirmwareType.BMC in firmware_info

        # Check firmware info structure
        bios_info = firmware_info[FirmwareType.BIOS]
        assert isinstance(bios_info, FirmwareInfo)
        assert bios_info.firmware_type == FirmwareType.BIOS
        assert bios_info.vendor == "hpe"

    @pytest.mark.asyncio
    async def test_validate_firmware_file(self, firmware_manager):
        """Test firmware file validation"""
        # Test with non-existent file
        firmware_info = FirmwareInfo(
            firmware_type=FirmwareType.BIOS,
            current_version="1.0.0",
            latest_version="1.1.0",
            update_required=True,
            priority=UpdatePriority.NORMAL,
            file_path="/nonexistent/file.bin",
        )

        result = await firmware_manager._validate_firmware_file(firmware_info)
        assert result == False

        # Test with valid file (create temporary file)
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(b"test firmware content")
            firmware_info.file_path = tmp_file.name

        try:
            result = await firmware_manager._validate_firmware_file(firmware_info)
            assert result == True
        finally:
            os.unlink(tmp_file.name)

    @pytest.mark.asyncio
    async def test_update_firmware_component(self, firmware_manager):
        """Test single firmware component update"""
        firmware_info = FirmwareInfo(
            firmware_type=FirmwareType.BIOS,
            current_version="1.0.0",
            latest_version="1.1.0",
            update_required=True,
            priority=UpdatePriority.NORMAL,
            estimated_time=10,  # Short time for testing
        )

        result = await firmware_manager.update_firmware_component(
            firmware_info, "192.168.1.100", "admin", "password"
        )

        assert isinstance(result, FirmwareUpdateResult)
        assert result.firmware_type == FirmwareType.BIOS
        assert result.old_version == "1.0.0"
        assert result.execution_time > 0

    @pytest.mark.asyncio
    async def test_update_firmware_batch(self, firmware_manager):
        """Test batch firmware update"""
        firmware_list = [
            FirmwareInfo(
                firmware_type=FirmwareType.BMC,
                current_version="1.0.0",
                latest_version="1.1.0",
                update_required=True,
                priority=UpdatePriority.CRITICAL,
                estimated_time=5,
            ),
            FirmwareInfo(
                firmware_type=FirmwareType.BIOS,
                current_version="1.0.0",
                latest_version="1.1.0",
                update_required=True,
                priority=UpdatePriority.HIGH,
                estimated_time=5,
            ),
        ]

        results = await firmware_manager.update_firmware_batch(
            "a1.c5.large", "192.168.1.100", "admin", "password", firmware_list
        )

        assert len(results) == 2
        assert all(isinstance(r, FirmwareUpdateResult) for r in results)

        # Check that BMC was updated first (higher priority)
        assert results[0].firmware_type == FirmwareType.BMC
        assert results[1].firmware_type == FirmwareType.BIOS

    @pytest.mark.asyncio
    async def test_empty_firmware_batch(self, firmware_manager):
        """Test batch update with empty firmware list"""
        results = await firmware_manager.update_firmware_batch(
            "a1.c5.large", "192.168.1.100", "admin", "password", []
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_calculate_file_checksum(self, firmware_manager):
        """Test file checksum calculation"""
        content = b"test firmware content"

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(content)
            tmp_file.flush()

            checksum = await firmware_manager._calculate_file_checksum(tmp_file.name)

        os.unlink(tmp_file.name)

        # Verify checksum format (should be 64 character hex string for SHA256)
        assert len(checksum) == 64
        assert all(c in "0123456789abcdef" for c in checksum)


class TestFirmwareRepository:
    """Test suite for FirmwareRepository"""

    def test_from_config_valid_file(self):
        """Test repository creation from valid config file"""
        config_content = """
firmware_repository:
  base_path: "/opt/firmware"
  vendors:
    test_vendor:
      display_name: "Test Vendor"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            repo = FirmwareRepository.from_config(config_path)
            assert repo.base_path == "/opt/firmware"
            assert "test_vendor" in repo.vendors
        finally:
            os.unlink(config_path)

    def test_from_config_invalid_file(self):
        """Test repository creation from invalid config file"""
        repo = FirmwareRepository.from_config("/nonexistent/config.yaml")

        # Should return default repository
        assert repo.base_path == "/opt/firmware"
        assert repo.vendors == {}


class TestFirmwareDataStructures:
    """Test suite for firmware data structures"""

    def test_firmware_info_creation(self):
        """Test FirmwareInfo creation and serialization"""
        firmware_info = FirmwareInfo(
            firmware_type=FirmwareType.BIOS,
            current_version="1.0.0",
            latest_version="1.1.0",
            update_required=True,
            priority=UpdatePriority.HIGH,
            vendor="test_vendor",
        )

        assert firmware_info.firmware_type == FirmwareType.BIOS
        assert firmware_info.update_required == True
        assert firmware_info.priority == UpdatePriority.HIGH

        # Test serialization
        data = firmware_info.to_dict()
        assert isinstance(data, dict)
        assert data["firmware_type"] == FirmwareType.BIOS
        assert data["vendor"] == "test_vendor"

    def test_firmware_update_result_creation(self):
        """Test FirmwareUpdateResult creation and serialization"""
        result = FirmwareUpdateResult(
            firmware_type=FirmwareType.BMC,
            success=True,
            old_version="1.0.0",
            new_version="1.1.0",
            execution_time=45.5,
            requires_reboot=True,
        )

        assert result.success == True
        assert result.execution_time == 45.5
        assert result.warnings == []  # Should be initialized

        # Test serialization
        data = result.to_dict()
        assert isinstance(data, dict)
        assert data["firmware_type"] == "bmc"  # Should be string value
        assert data["success"] == True


class TestFirmwareExceptions:
    """Test suite for firmware exceptions"""

    def test_firmware_update_exception(self):
        """Test FirmwareUpdateException"""
        with pytest.raises(FirmwareUpdateException) as exc_info:
            raise FirmwareUpdateException("Test firmware update error")

        assert "Test firmware update error" in str(exc_info.value)


@pytest.mark.integration
class TestFirmwareManagerIntegration:
    """Integration tests for FirmwareManager"""

    @pytest.mark.asyncio
    async def test_full_firmware_check_workflow(self):
        """Test complete firmware check workflow"""
        firmware_manager = FirmwareManager()

        # Test with mock data
        firmware_info = await firmware_manager.check_firmware_versions(
            "a1.c5.large", "192.168.1.100", "admin", "password"
        )

        # Should return firmware info for BIOS and BMC
        assert len(firmware_info) >= 2
        assert FirmwareType.BIOS in firmware_info
        assert FirmwareType.BMC in firmware_info

        # Check if any updates are needed
        updates_needed = [fw for fw in firmware_info.values() if fw.update_required]

        if updates_needed:
            # Test batch update
            results = await firmware_manager.update_firmware_batch(
                "a1.c5.large", "192.168.1.100", "admin", "password", updates_needed
            )

            assert len(results) == len(updates_needed)
            assert all(isinstance(r, FirmwareUpdateResult) for r in results)


if __name__ == "__main__":
    pytest.main([__file__])
