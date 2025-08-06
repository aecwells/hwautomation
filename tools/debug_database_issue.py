#!/usr/bin/env python3
"""
Debug the database table issue in the commissioning workflow
"""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

from hwautomation.utils.config import load_config
from hwautomation.orchestration.workflow_manager import WorkflowManager
from hwautomation.database.helper import DbHelper

def debug_database_issue():
    print("=" * 60)
    print("DEBUGGING DATABASE TABLE ISSUE")
    print("=" * 60)
    
    try:
        # 1. Load configuration
        print("1. Loading configuration...")
        config = load_config('config.yaml')
        db_config = config.get('database', {})
        print(f"   Database config: {db_config}")
        
        # 2. Test direct database connection
        print("\n2. Testing direct database connection...")
        db_path = db_config.get('path', 'hw_automation.db')
        print(f"   Database path: {db_path}")
        
        # Ensure absolute path
        if not os.path.isabs(db_path):
            db_path = str(project_root / db_path)
        print(f"   Absolute path: {db_path}")
        
        # Check if file exists
        if os.path.exists(db_path):
            print(f"   ✅ Database file exists")
            file_size = os.path.getsize(db_path)
            print(f"   File size: {file_size} bytes")
        else:
            print(f"   ❌ Database file does not exist")
            return
        
        # 3. Test DbHelper initialization
        print("\n3. Testing DbHelper initialization...")
        try:
            db_helper = DbHelper(
                tablename='servers',
                db_path=db_path,
                auto_migrate=True
            )
            print("   ✅ DbHelper initialized successfully")
            print(f"   Table name: {db_helper.tablename}")
            print(f"   Database path: {db_helper.db_path}")
            
            # Test table access
            print("\n4. Testing table access...")
            result = db_helper.checkifserveridexists('test123')
            print(f"   ✅ Table access working: {result}")
            
        except Exception as e:
            print(f"   ❌ DbHelper initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # 4. Test WorkflowManager initialization  
        print("\n5. Testing WorkflowManager initialization...")
        try:
            workflow_manager = WorkflowManager(config)
            print("   ✅ WorkflowManager initialized successfully")
            print(f"   WM Database path: {workflow_manager.db_helper.db_path}")
            print(f"   WM Table name: {workflow_manager.db_helper.tablename}")
            
            # Test database access through workflow manager
            print("\n6. Testing database access through WorkflowManager...")
            result = workflow_manager.db_helper.checkifserveridexists('test123')
            print(f"   ✅ WorkflowManager database access working: {result}")
            
        except Exception as e:
            print(f"   ❌ WorkflowManager initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # 5. Test database schema
        print("\n7. Testing database schema...")
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # List tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"   Tables: {[t[0] for t in tables]}")
            
            # Check servers table schema
            if 'servers' in [t[0] for t in tables]:
                cursor.execute("PRAGMA table_info(servers)")
                columns = cursor.fetchall()
                print(f"   Servers table columns: {[c[1] for c in columns]}")
                
                # Count records
                cursor.execute("SELECT COUNT(*) FROM servers")
                count = cursor.fetchone()[0]
                print(f"   Servers table record count: {count}")
            else:
                print("   ❌ 'servers' table not found!")
            
            conn.close()
            
        except Exception as e:
            print(f"   ❌ Database schema test failed: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("DATABASE DEBUG COMPLETE")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Debug script failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_database_issue()
