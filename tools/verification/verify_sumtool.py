#!/usr/bin/env python3
"""
Verify sumtool package in tools directory
"""

import os
import subprocess
import tarfile
from pathlib import Path


def verify_sumtool_package():
    """Verify the local sumtool package is valid"""

    tools_dir = Path("/home/ubuntu/HWAutomation/tools")
    sumtool_file = tools_dir / "sum_2.14.0_Linux_x86_64_20240215.tar.gz"

    print("🔍 Verifying sumtool package...")
    print(f"📁 Tools directory: {tools_dir}")
    print(f"📦 Sumtool package: {sumtool_file}")

    # Check if file exists
    if not sumtool_file.exists():
        print("❌ Sumtool package not found!")
        print(f"   Expected: {sumtool_file}")
        return False

    # Check file size
    file_size = sumtool_file.stat().st_size
    print(f"📏 File size: {file_size:,} bytes ({file_size / 1024 / 1024:.1f} MB)")

    if file_size < 1024 * 1024:  # Less than 1MB
        print("⚠️  File seems too small for sumtool package")
        return False

    # Test archive extraction
    print("🗜️  Testing archive extraction...")
    try:
        with tarfile.open(sumtool_file, "r:gz") as tar:
            members = tar.getnames()
            print(f"📋 Archive contains {len(members)} files:")

            # Show first few files
            for member in members[:5]:
                print(f"   • {member}")

            if len(members) > 5:
                print(f"   ... and {len(members) - 5} more files")

            # Look for sum binary
            sum_binary = None
            for member in members:
                if member.endswith("/sum") or member == "sum":
                    sum_binary = member
                    break

            if sum_binary:
                print(f"✅ Found sum binary: {sum_binary}")
            else:
                print("❌ Sum binary not found in archive!")
                return False

    except Exception as e:
        print(f"❌ Archive extraction test failed: {e}")
        return False

    # Test with tar command (simulates remote server behavior)
    print("🧪 Testing with tar command...")
    try:
        result = subprocess.run(
            ["tar", "-tzf", str(sumtool_file)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print("✅ Archive validates with tar command")
        else:
            print(f"❌ tar validation failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("⏰ tar command timed out")
        return False
    except Exception as e:
        print(f"❌ tar command failed: {e}")
        return False

    print("\n🎉 Sumtool package verification successful!")
    print("✅ File exists and has reasonable size")
    print("✅ Archive extracts properly")
    print("✅ Sum binary found in archive")
    print("✅ tar command validation passed")
    print("\n📋 Ready for deployment to remote servers")

    return True


def show_deployment_info():
    """Show information about how the package will be deployed"""
    print("\n📖 Deployment Information:")
    print(
        "   Local path:  /home/ubuntu/HWAutomation/tools/sum_2.14.0_Linux_x86_64_20240215.tar.gz"
    )
    print("   Remote path: /tmp/sumtool.tar.gz")
    print("   Install path: /usr/local/bin/sumtool -> /usr/bin/sumtool")
    print("   Method: SSH upload + remote extraction")
    print("   Validation: Archive integrity check before installation")


if __name__ == "__main__":
    print("🛠️  Sumtool Package Verification Tool")
    print("=" * 50)

    success = verify_sumtool_package()

    if success:
        show_deployment_info()
        exit(0)
    else:
        print("\n❌ Verification failed!")
        print("   Please check the sumtool package and try again.")
        exit(1)
