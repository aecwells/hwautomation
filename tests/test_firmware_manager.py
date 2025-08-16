"""
Unit tests for Firmware Manager - Phase 4 Implementation
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hwautomation.hardware.firmware import (
    FirmwareInfo,
    FirmwareManager,
    FirmwareRepository,
    FirmwareType,
    FirmwareUpdateException,
    FirmwareUpdateResult,
    Priority,
    UpdatePolicy,
)


class TestFirmwareManager:
    """Test suite for FirmwareManager"""

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary firmware configuration file"""
        config_content = """firmware_repository:
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
            f.flush()
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
        assert vendor_info["model"] == "ProLiant RL300 Gen11"

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
        assert priority == Priority.CRITICAL

        # BIOS updates should be high
        priority = firmware_manager._determine_update_priority(
            FirmwareType.BIOS, "1.0.0", "1.1.0"
        )
        assert priority == Priority.HIGH

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
                priority=Priority.NORMAL,
            ),
            FirmwareInfo(
                firmware_type=FirmwareType.BMC,
                current_version="1.0.0",
                latest_version="1.1.0",
                update_required=True,
                priority=Priority.CRITICAL,
            ),
        ]

        sorted_firmware = firmware_manager._sort_firmware_updates(firmware_list)

        # Critical BMC should come before normal BIOS
        assert sorted_firmware[0].firmware_type == FirmwareType.BMC
        assert sorted_firmware[0].priority == Priority.CRITICAL
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
            priority=Priority.NORMAL,
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
            priority=Priority.NORMAL,
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
                priority=Priority.CRITICAL,
                estimated_time=5,
            ),
            FirmwareInfo(
                firmware_type=FirmwareType.BIOS,
                current_version="1.0.0",
                latest_version="1.1.0",
                update_required=True,
                priority=Priority.HIGH,
                estimated_time=5,
            ),
        ]

        # Mock the firmware update methods to return successful results
        with (
            patch.object(firmware_manager, "_update_bmc_firmware", return_value=True),
            patch.object(firmware_manager, "_update_bios_firmware", return_value=True),
            patch.object(
                firmware_manager, "_validate_firmware_file", return_value=True
            ),
        ):

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
            priority=Priority.HIGH,
            vendor="test_vendor",
        )

        assert firmware_info.firmware_type == FirmwareType.BIOS
        assert firmware_info.update_required == True
        assert firmware_info.priority == Priority.HIGH

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
@pytest.mark.performance
class TestFirmwareManagerIntegration:
    """Integration tests for FirmwareManager"""

    @pytest.mark.asyncio
    async def test_full_firmware_check_workflow(self):
        """Test complete firmware check workflow"""
        import time

        start_time = time.time()
        firmware_manager = FirmwareManager()

        # Test with mock data
        firmware_info = await firmware_manager.check_firmware_versions(
            "a1.c5.large", "192.168.1.100", "admin", "password"
        )

        check_time = time.time() - start_time

        # Should return firmware info for BIOS and BMC
        assert len(firmware_info) >= 2
        assert FirmwareType.BIOS in firmware_info
        assert FirmwareType.BMC in firmware_info

        # Performance assertion: firmware check should complete within 5 seconds
        assert (
            check_time < 5.0
        ), f"Firmware check took {check_time:.2f}s, expected < 5.0s"

        # Check if any updates are needed
        updates_needed = [fw for fw in firmware_info.values() if fw.update_required]

        if updates_needed:
            # Test batch update timing
            update_start = time.time()
            results = await firmware_manager.update_firmware_batch(
                "a1.c5.large", "192.168.1.100", "admin", "password", updates_needed
            )
            update_time = time.time() - update_start

            assert len(results) == len(updates_needed)
            assert all(isinstance(r, FirmwareUpdateResult) for r in results)

            # Performance assertion: batch update should complete within reasonable time
            expected_time = len(updates_needed) * 10  # 10 seconds per update max
            assert (
                update_time < expected_time
            ), f"Batch update took {update_time:.2f}s, expected < {expected_time}s"


@pytest.mark.performance
class TestFirmwareManagerPerformance:
    """Performance-focused tests for FirmwareManager"""

    @pytest.fixture
    def firmware_manager(self, temp_config_file):
        """Create a FirmwareManager instance for testing"""
        return FirmwareManager(config_file=temp_config_file)

    def test_firmware_info_creation_performance(self):
        """Test performance of creating FirmwareInfo objects"""
        import time

        start_time = time.time()

        # Create many FirmwareInfo objects to test performance
        firmware_objects = []
        for i in range(1000):
            firmware_info = FirmwareInfo(
                firmware_type=FirmwareType.BIOS,
                current_version=f"1.0.{i}",
                latest_version=f"1.1.{i}",
                update_required=True,
                priority=Priority.NORMAL,  # Use NORMAL instead of RECOMMENDED
                file_path=f"/path/to/firmware_{i}.bin",
                checksum=f"sha256_{i}",
                release_notes=f"Release notes {i}",
                estimated_time=300,
                requires_reboot=True,
            )
            firmware_objects.append(firmware_info)

        creation_time = time.time() - start_time

        # Performance assertion: should create 1000 objects in under 1 second
        assert (
            creation_time < 1.0
        ), f"Creating 1000 FirmwareInfo objects took {creation_time:.2f}s, expected < 1.0s"
        assert len(firmware_objects) == 1000

    def test_repository_scan_performance(self):
        """Test performance of repository scanning operations"""
        import os
        import tempfile
        import time

        # Create a temporary directory with firmware files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock firmware files
            start_time = time.time()

            for vendor in ["supermicro", "dell", "hp"]:
                vendor_dir = os.path.join(temp_dir, vendor)
                os.makedirs(vendor_dir, exist_ok=True)
                for fw_type in ["bios", "bmc"]:
                    for i in range(10):  # 10 files per type
                        fw_file = os.path.join(
                            vendor_dir, f"{fw_type}_firmware_{i}.bin"
                        )
                        with open(fw_file, "w") as f:
                            f.write(f"Mock firmware data {i}")

            # Simulate repository scanning by walking the directory
            file_count = 0
            for root, dirs, files in os.walk(temp_dir):
                file_count += len(files)

            scan_time = time.time() - start_time

            # Performance assertion: scanning should complete within 2 seconds
            assert (
                scan_time < 2.0
            ), f"Repository scan took {scan_time:.2f}s, expected < 2.0s"

            # Verify results
            assert file_count == 60  # 3 vendors * 2 types * 10 files = 60 files

    def test_firmware_update_result_serialization_performance(self):
        """Test performance of FirmwareUpdateResult serialization"""
        import time

        # Create a FirmwareUpdateResult object with correct API
        result = FirmwareUpdateResult(
            firmware_type=FirmwareType.BIOS,
            success=True,
            old_version="1.0.0",  # Use old_version instead of version_before
            new_version="1.1.0",  # Use new_version instead of version_after
            execution_time=45.5,
            requires_reboot=True,
            error_message=None,
            warnings=[],
        )

        start_time = time.time()

        # Serialize many times to test performance
        serialized_results = []
        for i in range(10000):
            serialized = result.to_dict()
            serialized_results.append(serialized)

        serialization_time = time.time() - start_time

        # Performance assertion: should serialize 10000 objects in under 1 second
        assert (
            serialization_time < 1.0
        ), f"Serializing 10000 results took {serialization_time:.2f}s, expected < 1.0s"
        assert len(serialized_results) == 10000

        # Verify serialization correctness
        sample = serialized_results[0]
        assert sample["firmware_type"] == "bios"  # Should be serialized to string
        assert sample["success"] == True
        assert sample["execution_time"] == 45.5


if __name__ == "__main__":
    pytest.main([__file__])
