#!/usr/bin/env python3
"""
Simple test to verify firmware web interface integration.
"""

import sys
sys.path.append('src')

def test_firmware_web_integration():
    """Test basic firmware web interface integration."""
    print("Testing firmware web interface integration...")
    
    try:
        # Test imports
        from hwautomation.web.firmware_routes import firmware_bp, init_firmware_routes
        print("✅ Firmware routes import successful")
        
        # Test blueprint creation
        assert firmware_bp.name == 'firmware'
        assert firmware_bp.url_prefix == '/firmware'
        print("✅ Firmware blueprint created successfully")
        
        # Test basic web manager creation
        from hwautomation.web.firmware_routes import FirmwareWebManager
        from unittest.mock import Mock
        
        firmware_manager = Mock()
        workflow_manager = Mock()
        db_helper = Mock()
        socketio = Mock()
        
        web_manager = FirmwareWebManager(firmware_manager, workflow_manager, db_helper, socketio)
        print("✅ Firmware web manager created successfully")
        
        # Test route initialization
        init_firmware_routes(firmware_manager, workflow_manager, db_helper, socketio)
        print("✅ Firmware routes initialized successfully")
        
        print("\n🎉 Firmware web interface integration test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_firmware_web_integration()
    sys.exit(0 if success else 1)
