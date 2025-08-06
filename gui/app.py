#!/usr/bin/env python3
"""
Web GUI for Hardware Automation

Flask-based web interface for managing BIOS configurations and hardware automation tasks.
Provides a user-friendly interface for the HWAutomation package.
"""

import sys
import os
import logging
from pathlib import Path
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_socketio import SocketIO, emit
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Any

# Add src to path
project_root = Path(__file__).parent.parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

from hwautomation.hardware.bios_config import BiosConfigManager
from hwautomation.database.helper import DbHelper
from hwautomation.utils.env_config import load_config
from hwautomation.hardware.ipmi import IpmiManager
from hwautomation.hardware.redfish import RedFishManager
from hwautomation.maas.client import create_maas_client
from hwautomation.orchestration.workflow_manager import WorkflowManager
from hwautomation.orchestration.server_provisioning import ServerProvisioningWorkflow
from hwautomation.orchestration.device_selection import DeviceSelectionService, MachineFilter, MachineStatus

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'hwautomation-gui-secret-key-change-in-production'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize managers
bios_manager = BiosConfigManager()

# Load configuration and use the database path from config
config = load_config()
db_path = config.get('database', {}).get('path', 'hw_automation.db')

# Ensure database path is relative to project root, not GUI directory
if not os.path.isabs(db_path):
    db_path = str(project_root / db_path)

db_helper = DbHelper(tablename="servers", db_path=db_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize orchestration system
try:
    # Update config to use absolute database path for orchestration system
    config_for_orchestration = config.copy()
    if 'database' not in config_for_orchestration:
        config_for_orchestration['database'] = {}
    config_for_orchestration['database']['path'] = db_path
    
    workflow_manager = WorkflowManager(config_for_orchestration)
    provisioning_workflow = ServerProvisioningWorkflow(workflow_manager)
    device_selection_service = DeviceSelectionService(config=config.get('maas', {}))
    logger.info("Orchestration system initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize orchestration system: {e}")
    workflow_manager = None
    provisioning_workflow = None
    device_selection_service = None
    device_selection_service = None
    provisioning_workflow = None


@app.route('/')
def index():
    """Main dashboard page."""
    try:
        device_types = bios_manager.get_device_types()
        stats = {
            'device_types_count': len(device_types),
            'preserve_settings_count': len(bios_manager.preserve_settings),
            'template_rules_count': len(bios_manager.template_rules.get('template_rules', {}))
        }
        return render_template('index.html', stats=stats, device_types=device_types)
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash(f"Error loading dashboard: {e}", 'error')
        return render_template('error.html', error=str(e))


@app.route('/bios')
def bios_management():
    """BIOS configuration management page."""
    try:
        device_types = bios_manager.get_device_types()
        return render_template('bios_management.html', device_types=device_types)
    except Exception as e:
        logger.error(f"Error loading BIOS management: {e}")
        flash(f"Error loading BIOS management: {e}", 'error')
        return render_template('error.html', error=str(e))


@app.route('/api/device-types')
def api_device_types():
    """API endpoint to get device types."""
    try:
        device_types = bios_manager.get_device_types()
        data = []
        for device_type in device_types:
            config = bios_manager.get_device_config(device_type)
            data.append({
                'name': device_type,
                'description': config.get('description', 'No description') if config else 'No description',
                'motherboards': config.get('motherboards', []) if config else []
            })
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error getting device types: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/device-config/<device_type>')
def api_device_config(device_type):
    """API endpoint to get device configuration."""
    try:
        config = bios_manager.get_device_config(device_type)
        if config:
            return jsonify({'success': True, 'data': config})
        else:
            return jsonify({'success': False, 'error': f'Device type {device_type} not found'})
    except Exception as e:
        logger.error(f"Error getting device config: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/generate-xml', methods=['POST'])
def api_generate_xml():
    """API endpoint to generate XML configuration."""
    try:
        data = request.get_json()
        device_type = data.get('device_type')
        motherboard = data.get('motherboard')
        
        if not device_type:
            return jsonify({'success': False, 'error': 'Device type is required'})
        
        xml_config = bios_manager.generate_xml_config(device_type, motherboard)
        if xml_config:
            return jsonify({'success': True, 'data': {'xml': xml_config}})
        else:
            return jsonify({'success': False, 'error': 'Failed to generate XML configuration'})
    except Exception as e:
        logger.error(f"Error generating XML: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/pull-config', methods=['POST'])
def api_pull_config():
    """API endpoint to pull current BIOS configuration."""
    try:
        data = request.get_json()
        target_ip = data.get('target_ip')
        username = data.get('username', 'ADMIN')
        password = data.get('password')
        
        if not target_ip:
            return jsonify({'success': False, 'error': 'Target IP is required'})
        
        # Emit progress update
        socketio.emit('config_progress', {
            'stage': 'connecting',
            'message': f'Connecting to {target_ip}...'
        })
        
        current_config = bios_manager.pull_current_bios_config(target_ip, username, password)
        
        if current_config is not None:
            # Pretty print the XML
            bios_manager._indent_xml(current_config)
            xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n'
            xml_str += ET.tostring(current_config, encoding='unicode')
            
            socketio.emit('config_progress', {
                'stage': 'complete',
                'message': 'Configuration pulled successfully'
            })
            
            return jsonify({'success': True, 'data': {'xml': xml_str, 'target_ip': target_ip}})
        else:
            socketio.emit('config_progress', {
                'stage': 'error',
                'message': f'Failed to retrieve configuration from {target_ip}'
            })
            return jsonify({'success': False, 'error': f'Failed to retrieve configuration from {target_ip}'})
            
    except Exception as e:
        logger.error(f"Error pulling config: {e}")
        socketio.emit('config_progress', {
            'stage': 'error',
            'message': f'Error: {str(e)}'
        })
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/apply-config', methods=['POST'])
def api_apply_config():
    """API endpoint to apply BIOS configuration using smart approach."""
    try:
        data = request.get_json()
        device_type = data.get('device_type')
        target_ip = data.get('target_ip')
        username = data.get('username', 'ADMIN')
        password = data.get('password')
        dry_run = data.get('dry_run', False)
        
        if not device_type or not target_ip:
            return jsonify({'success': False, 'error': 'Device type and target IP are required'})
        
        # Emit progress updates
        socketio.emit('config_progress', {
            'stage': 'starting',
            'message': f'Starting smart configuration for {device_type} on {target_ip}...'
        })
        
        socketio.emit('config_progress', {
            'stage': 'pulling',
            'message': 'Step 1: Pulling current configuration...'
        })
        
        result = bios_manager.apply_bios_config_smart(
            device_type=device_type,
            target_ip=target_ip,
            username=username,
            password=password,
            dry_run=dry_run
        )
        
        if result['success']:
            socketio.emit('config_progress', {
                'stage': 'complete',
                'message': 'Configuration applied successfully!' if not dry_run else 'Dry run completed successfully!'
            })
        else:
            socketio.emit('config_progress', {
                'stage': 'error',
                'message': f"Error: {result.get('error', 'Unknown error')}"
            })
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error applying config: {e}")
        socketio.emit('config_progress', {
            'stage': 'error',
            'message': f'Error: {str(e)}'
        })
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/validate-connection', methods=['POST'])
def api_validate_connection():
    """API endpoint to validate BMC connection."""
    try:
        data = request.get_json()
        target_ip = data.get('target_ip')
        username = data.get('username', 'ADMIN')
        password = data.get('password')
        
        if not target_ip:
            return jsonify({'success': False, 'error': 'Target IP is required'})
        
        # Emit progress update
        socketio.emit('connection_test', {
            'stage': 'testing',
            'message': f'Testing connection to {target_ip}...'
        })
        
        # Mock connection test - in real implementation, use IPMI/RedFish
        import time
        time.sleep(1)  # Simulate connection test
        
        # Mock result - replace with actual connection test
        success = True
        message = f"Successfully connected to BMC at {target_ip}"
        
        socketio.emit('connection_test', {
            'stage': 'complete' if success else 'error',
            'message': message
        })
        
        return jsonify({
            'success': success,
            'message': message,
            'target_ip': target_ip
        })
        
    except Exception as e:
        logger.error(f"Error validating connection: {e}")
        socketio.emit('connection_test', {
            'stage': 'error',
            'message': f'Connection test failed: {str(e)}'
        })
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/maas/connection', methods=['GET'])
def api_maas_connection():
    """API endpoint to check MaaS connection status."""
    try:
        # Try to load configuration and create MaaS client
        config = load_config()
        if 'maas' not in config:
            return jsonify({
                'success': False, 
                'error': 'MaaS configuration not found',
                'configured': False
            })
        
        maas_client = create_maas_client(config['maas'])
        
        # Test connection by getting machines
        machines = maas_client.get_machines()
        
        return jsonify({
            'success': True,
            'configured': True,
            'host': config['maas'].get('host', 'Unknown'),
            'machine_count': len(machines)
        })
        
    except Exception as e:
        logger.error(f"Error checking MaaS connection: {e}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'configured': False
        })


@app.route('/api/maas/machines', methods=['GET'])
def api_maas_machines():
    """API endpoint to get machines from MaaS."""
    try:
        config = load_config()
        if 'maas' not in config:
            return jsonify({'success': False, 'error': 'MaaS configuration not found'})
        
        maas_client = create_maas_client(config['maas'])
        machines = maas_client.get_machines()
        
        # Enhance machine data with additional info
        enhanced_machines = []
        for machine in machines:
            enhanced_machine = {
                'system_id': machine.get('system_id'),
                'hostname': machine.get('hostname'),
                'status_name': machine.get('status_name'),
                'power_state': machine.get('power_state'),
                'architecture': machine.get('architecture'),
                'ip_address': '',  # Would be populated from MaaS API
                'memory': machine.get('memory', 0),
                'cpu_count': machine.get('cpu_count', 0),
                'storage': machine.get('storage', 0),
                'owner': machine.get('owner'),
                'tags': machine.get('tag_names', [])
            }
            
            # Try to get IP address
            try:
                ip = maas_client.get_machine_ip(machine.get('system_id'))
                enhanced_machine['ip_address'] = ip or 'N/A'
            except:
                enhanced_machine['ip_address'] = 'N/A'
            
            enhanced_machines.append(enhanced_machine)
        
        return jsonify({'success': True, 'data': enhanced_machines})
        
    except Exception as e:
        logger.error(f"Error getting MaaS machines: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/maas/machines/<system_id>/action', methods=['POST'])
def api_maas_machine_action(system_id):
    """API endpoint to perform actions on MaaS machines."""
    try:
        data = request.get_json()
        action = data.get('action')
        
        if not action:
            return jsonify({'success': False, 'error': 'Action is required'})
        
        config = load_config()
        if 'maas' not in config:
            return jsonify({'success': False, 'error': 'MaaS configuration not found'})
        
        # Redirect commissioning operations to use orchestration workflow
        if action in ['commission', 'force_commission']:
            logger.info(f"Redirecting {action} operation to orchestration workflow for {system_id}")
            
            if not provisioning_workflow:
                return jsonify({'success': False, 'error': 'Orchestration system not available'}), 503
            
            # Use a default device type for manual commissioning
            # In a real scenario, this could be determined from machine specs
            default_device_type = 's2.c2.medium' 
            
            try:
                # Start provisioning workflow via orchestration system
                result = provisioning_workflow.provision_server(
                    server_id=system_id,
                    device_type=default_device_type,
                    progress_callback=lambda progress: socketio.emit('workflow_progress', progress)
                )
                
                if result.get('success', False):
                    action_name = 'force commission' if action == 'force_commission' else 'commission'
                    return jsonify({
                        'success': True, 
                        'message': f'Action {action_name} started via orchestration workflow (auto-detecting force recommission needs)',
                        'workflow_id': result.get('workflow_id'),
                        'note': 'This commissioning uses the enhanced workflow system with proper database tracking'
                    })
                else:
                    error_msg = result.get('message', f'Failed to start {action}')
                    return jsonify({'success': False, 'error': error_msg})
                    
            except Exception as e:
                logger.error(f"Error starting orchestration workflow for {action}: {e}")
                return jsonify({'success': False, 'error': f'Orchestration workflow failed: {str(e)}'})
        
        # For non-commissioning actions, use direct MaaS operations
        maas_client = create_maas_client(config['maas'])
        
        result = False
        if action == 'deploy':
            os_name = data.get('os_name')
            result = maas_client.deploy_machine(system_id, os_name)
        elif action == 'release':
            result = maas_client.release_machine(system_id)
        elif action == 'abort':
            result = maas_client.abort_machine_operation(system_id)
        else:
            return jsonify({'success': False, 'error': f'Unknown action: {action}'})
        
        if result:
            return jsonify({'success': True, 'message': f'Action {action} completed successfully'})
        else:
            return jsonify({'success': False, 'error': f'Action {action} failed'})
            
    except Exception as e:
        logger.error(f"Error performing MaaS machine action: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/maas/statistics', methods=['GET'])
def api_maas_statistics():
    """API endpoint to get MaaS statistics."""
    try:
        config = load_config()
        if 'maas' not in config:
            return jsonify({'success': False, 'error': 'MaaS configuration not found'})
        
        maas_client = create_maas_client(config['maas'])
        
        # Get machines and calculate statistics
        all_machines = maas_client.get_machines()
        ready_machines = maas_client.get_ready_machines()
        deployed_machines = maas_client.get_deployed_machines()
        
        # Count by status
        status_counts = {}
        for machine in all_machines:
            status = machine.get('status_name', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        statistics = {
            'total': len(all_machines),
            'ready': len(ready_machines),
            'deployed': len(deployed_machines),
            'commissioning': status_counts.get('Commissioning', 0),
            'failed': status_counts.get('Failed', 0),
            'broken': status_counts.get('Broken', 0),
            'status_breakdown': status_counts
        }
        
        return jsonify({'success': True, 'data': statistics})
        
    except Exception as e:
        logger.error(f"Error getting MaaS statistics: {e}")
        return jsonify({'success': False, 'error': str(e)})


# Database API Endpoints
@app.route('/api/database/info', methods=['GET'])
def api_database_info():
    """Get database information and statistics."""
    try:
        from hwautomation.database.migrations import DatabaseMigrator
        import sqlite3
        
        # Get database file path
        db_path = db_helper.db_path if db_helper.db_path != ":memory:" else None
        
        # Calculate database size
        db_size = "In-memory"
        if db_path and Path(db_path).exists():
            size_bytes = Path(db_path).stat().st_size
            if size_bytes < 1024:
                db_size = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                db_size = f"{size_bytes / 1024:.1f} KB"
            else:
                db_size = f"{size_bytes / (1024 * 1024):.1f} MB"
        
        # Create a new connection for this request to avoid threading issues
        conn = sqlite3.connect(db_helper.db_path)
        cursor = conn.cursor()
        
        # Get table count
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        table_count = cursor.fetchone()[0]
        
        # Get server count
        try:
            cursor.execute("SELECT COUNT(*) FROM servers")
            server_count = cursor.fetchone()[0]
        except:
            server_count = 0
        
        # Get power events count
        try:
            cursor.execute("SELECT COUNT(*) FROM power_state_history")
            power_events = cursor.fetchone()[0]
        except:
            power_events = 0
        
        conn.close()
        
        # Get schema version
        migrator = DatabaseMigrator(db_helper.db_path)
        schema_version = migrator.get_current_version()
        migrator.close()
        
        info = {
            'version': '3.x',  # SQLite version
            'size': db_size,
            'table_count': table_count,
            'server_count': server_count,
            'power_events': power_events,
            'schema_version': schema_version
        }
        
        return jsonify({'success': True, 'info': info})
        
    except Exception as e:
        logger.error(f"Error getting database info: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/database/migrations', methods=['GET'])
def api_database_migrations():
    """Get migration history."""
    try:
        import sqlite3
        
        # Create a new connection for this request
        conn = sqlite3.connect(db_helper.db_path)
        cursor = conn.cursor()
        
        # Check if migrations table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='schema_migrations'
        """)
        
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': True, 'migrations': []})
        
        cursor.execute("""
            SELECT version, name, applied_at, checksum 
            FROM schema_migrations 
            ORDER BY version
        """)
        
        migrations = []
        for row in cursor.fetchall():
            migrations.append({
                'version': row[0],
                'name': row[1],
                'applied_at': row[2],
                'checksum': row[3]
            })
        
        conn.close()
        return jsonify({'success': True, 'migrations': migrations})
        
    except Exception as e:
        logger.error(f"Error getting migrations: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/database/table/<table_name>', methods=['GET'])
def api_get_table_data(table_name):
    """Get data from a specific table."""
    try:
        import sqlite3
        
        # Validate table name to prevent SQL injection
        valid_tables = ['servers', 'power_state_history', 'schema_migrations']
        if table_name not in valid_tables:
            return jsonify({'success': False, 'error': 'Invalid table name'})
        
        # Create a new connection for this request
        conn = sqlite3.connect(db_helper.db_path)
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for row in cursor.fetchall():
            columns.append({
                'cid': row[0],
                'name': row[1],
                'type': row[2],
                'notnull': row[3],
                'dflt_value': row[4],
                'pk': row[5]
            })
        
        # Get table data
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1000")  # Limit for performance
        
        data = []
        for row in cursor.fetchall():
            record = {}
            for i, column in enumerate(columns):
                record[column['name']] = row[i]
            data.append(record)
        
        conn.close()
        return jsonify({'success': True, 'data': data, 'columns': columns})
        
    except Exception as e:
        logger.error(f"Error getting table data: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/database/table/<table_name>', methods=['POST'])
def api_add_record(table_name):
    """Add a new record to a table."""
    try:
        import sqlite3
        
        # Validate table name
        valid_tables = ['servers', 'power_state_history']  # No adding to schema_migrations
        if table_name not in valid_tables:
            return jsonify({'success': False, 'error': 'Invalid table name'})
        
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'})
        
        # Create a new connection for this request
        conn = sqlite3.connect(db_helper.db_path)
        cursor = conn.cursor()
        
        # Filter out None/empty values and timestamp fields
        filtered_data = {}
        for key, value in data.items():
            if value and not key.endswith('_at') and key != 'id':
                filtered_data[key] = value
        
        if not filtered_data:
            conn.close()
            return jsonify({'success': False, 'error': 'No valid data to insert'})
        
        # Build INSERT query
        columns = ', '.join(filtered_data.keys())
        placeholders = ', '.join(['?' for _ in filtered_data])
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        cursor.execute(query, list(filtered_data.values()))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Record added successfully'})
        
    except Exception as e:
        logger.error(f"Error adding record: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/database/table/<table_name>/<record_id>', methods=['PUT'])
def api_update_record(table_name, record_id):
    """Update a record in a table."""
    try:
        import sqlite3
        
        # Validate table name
        valid_tables = ['servers', 'power_state_history']
        if table_name not in valid_tables:
            return jsonify({'success': False, 'error': 'Invalid table name'})
        
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'})
        
        # Create a new connection for this request
        conn = sqlite3.connect(db_helper.db_path)
        cursor = conn.cursor()
        
        # Filter out timestamp fields and None values for update
        filtered_data = {}
        for key, value in data.items():
            if not key.endswith('_at') and key != 'id' and value is not None:
                filtered_data[key] = value
        
        if not filtered_data:
            conn.close()
            return jsonify({'success': False, 'error': 'No valid data to update'})
        
        # Build UPDATE query
        set_clause = ', '.join([f"{key} = ?" for key in filtered_data.keys()])
        primary_key = 'server_id' if table_name == 'servers' else 'id'
        query = f"UPDATE {table_name} SET {set_clause} WHERE {primary_key} = ?"
        
        values = list(filtered_data.values()) + [record_id]
        cursor.execute(query, values)
        conn.commit()
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Record not found'})
        
        conn.close()
        return jsonify({'success': True, 'message': 'Record updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating record: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/database/table/<table_name>/<record_id>', methods=['DELETE'])
def api_delete_record(table_name, record_id):
    """Delete a record from a table."""
    try:
        import sqlite3
        
        # Validate table name
        valid_tables = ['servers', 'power_state_history']
        if table_name not in valid_tables:
            return jsonify({'success': False, 'error': 'Invalid table name'})
        
        # Create a new connection for this request
        conn = sqlite3.connect(db_helper.db_path)
        cursor = conn.cursor()
        
        primary_key = 'server_id' if table_name == 'servers' else 'id'
        
        cursor.execute(f"DELETE FROM {table_name} WHERE {primary_key} = ?", (record_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Record not found'})
        
        conn.close()
        return jsonify({'success': True, 'message': 'Record deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting record: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/database/table/<table_name>/data', methods=['GET'])
def api_get_enhanced_table_data(table_name):
    """Get data for a specific table with enhanced functionality."""
    try:
        import sqlite3
        
        # Validate table name
        valid_tables = ['servers', 'workflow_history', 'power_state_history', 'schema_migrations']
        if table_name not in valid_tables:
            return jsonify({'success': False, 'error': 'Invalid table name'})
        
        # Create a new connection for this request
        conn = sqlite3.connect(db_helper.db_path)
        conn.row_factory = sqlite3.Row  # Enable dictionary-like access
        cursor = conn.cursor()
        
        # Get data with limit
        limit = request.args.get('limit', 1000, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        query = f"SELECT * FROM {table_name} ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        if table_name == 'schema_migrations':
            query = f"SELECT * FROM {table_name} ORDER BY version DESC LIMIT ? OFFSET ?"
        
        cursor.execute(query, (limit, offset))
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        data = [dict(row) for row in rows]
        
        # Get total count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': data,
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Error getting table data: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/database/stats', methods=['GET'])
def api_get_database_stats():
    """Get database statistics."""
    try:
        import sqlite3
        
        conn = sqlite3.connect(db_helper.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Server statistics
        cursor.execute("SELECT COUNT(*) FROM servers")
        stats['total_servers'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM servers WHERE status_name = 'Ready'")
        stats['ready_servers'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM servers WHERE status_name = 'Commissioning'")
        stats['commissioning_servers'] = cursor.fetchone()[0]
        
        # Get schema version
        cursor.execute("SELECT MAX(version) FROM schema_migrations")
        result = cursor.fetchone()
        stats['schema_version'] = result[0] if result[0] else 0
        
        # Get device types
        cursor.execute("SELECT DISTINCT device_type FROM servers WHERE device_type IS NOT NULL")
        stats['device_types'] = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/database/migrate', methods=['POST'])
def api_run_migrations():
    """Run database migrations."""
    try:
        from hwautomation.database.migrations import DatabaseMigrator
        
        migrator = DatabaseMigrator(db_helper.db_path)
        migrator.migrate_to_latest()
        migrator.close()
        
        # Refresh database connection
        db_helper.migrate_database()
        
        return jsonify({'success': True, 'message': 'Migrations completed successfully'})
        
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/database/backup', methods=['POST'])
def api_create_backup():
    """Create a database backup."""
    try:
        from hwautomation.database.migrations import DatabaseMigrator
        
        migrator = DatabaseMigrator(db_helper.db_path)
        backup_file = migrator.backup_database()
        migrator.close()
        
        if backup_file:
            return jsonify({'success': True, 'backup_file': backup_file})
        else:
            return jsonify({'success': False, 'error': 'Cannot backup in-memory database'})
        
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/database/export', methods=['GET'])
def api_export_database():
    """Export database data."""
    try:
        export_format = request.args.get('format', 'json')
        
        cursor = db_helper.sql_database.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        export_data = {
            'exported_at': datetime.now().isoformat(),
            'format': export_format,
            'tables': {}
        }
        
        for table in tables:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            # Get column names
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Convert to list of dicts
            table_data = []
            for row in rows:
                record = {}
                for i, column in enumerate(columns):
                    record[column] = row[i]
                table_data.append(record)
            
            export_data['tables'][table] = {
                'columns': columns,
                'data': table_data,
                'count': len(table_data)
            }
        
        return jsonify(export_data)
        
    except Exception as e:
        logger.error(f"Error exporting database: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/database/servers/status', methods=['GET'])
def api_servers_status():
    """Get enhanced server commissioning status with SSH and discovery information."""
    try:
        conn = sqlite3.connect(db_helper.db_path)
        cursor = conn.cursor()
        
        # Get all server records with enhanced information
        cursor.execute(f"""
            SELECT server_id, status_name, is_ready, server_model, ip_address, 
                   ip_address_works, ipmi_address, ipmi_address_works, 
                   kcs_status, host_inferface_status, currServerModels
            FROM {db_helper.tablename}
            ORDER BY server_id
        """)
        
        servers = []
        for row in cursor.fetchall():
            server = {
                'server_id': row[0],
                'status_name': row[1] or 'Unknown',
                'is_ready': row[2] == 'TRUE',
                'server_model': row[3] or 'Unknown',
                'ip_address': row[4],
                'ssh_connectivity': row[5] == 'TRUE',
                'ipmi_address': row[6],
                'ipmi_connectivity': row[7] == 'TRUE',
                'kcs_status': row[8] or 'Unknown',
                'host_interface_status': row[9] or 'Unknown',
                'vendor_info': row[10] or 'Not Available'
            }
            
            # Determine overall health status
            if server['is_ready'] and server['ssh_connectivity'] and server['ipmi_connectivity']:
                server['health_status'] = 'healthy'
                server['health_color'] = 'success'
            elif server['ssh_connectivity'] and server['ip_address']:
                server['health_status'] = 'partial'
                server['health_color'] = 'warning'
            elif 'Error' in server['status_name'] or 'Failed' in server['status_name']:
                server['health_status'] = 'error'
                server['health_color'] = 'danger'
            else:
                server['health_status'] = 'pending'
                server['health_color'] = 'info'
            
            servers.append(server)
        
        conn.close()
        
        # Calculate summary statistics
        total_servers = len(servers)
        healthy_servers = len([s for s in servers if s['health_status'] == 'healthy'])
        servers_with_ssh = len([s for s in servers if s['ssh_connectivity']])
        servers_with_ipmi = len([s for s in servers if s['ipmi_connectivity']])
        
        return jsonify({
            'success': True,
            'servers': servers,
            'summary': {
                'total_servers': total_servers,
                'healthy_servers': healthy_servers,
                'ssh_connectivity_rate': f"{servers_with_ssh}/{total_servers}" if total_servers > 0 else "0/0",
                'ipmi_connectivity_rate': f"{servers_with_ipmi}/{total_servers}" if total_servers > 0 else "0/0",
                'health_rate': f"{healthy_servers}/{total_servers}" if total_servers > 0 else "0/0"
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting server status: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/database/servers/<server_id>/test-connectivity', methods=['POST'])
def api_test_server_connectivity(server_id):
    """Test SSH and IPMI connectivity for a specific server."""
    try:
        # Get server information from database
        conn = sqlite3.connect(db_helper.db_path)
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT ip_address, ipmi_address FROM {db_helper.tablename} 
            WHERE server_id = ?
        """, (server_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'success': False, 'error': f'Server {server_id} not found'})
        
        ip_address, ipmi_address = result
        connectivity_results = {}
        
        # Test SSH connectivity
        if ip_address:
            ssh_result = test_ssh_connectivity(ip_address)
            connectivity_results['ssh'] = ssh_result
            
            # Update database with SSH test result
            db_helper.updateserverinfo(server_id, 'ip_address_works', 'TRUE' if ssh_result['success'] else 'FALSE')
        
        # Test IPMI connectivity
        if ipmi_address:
            ipmi_result = test_ipmi_connectivity(ipmi_address)
            connectivity_results['ipmi'] = ipmi_result
            
            # Update database with IPMI test result
            db_helper.updateserverinfo(server_id, 'ipmi_address_works', 'TRUE' if ipmi_result['success'] else 'FALSE')
        
        return jsonify({
            'success': True,
            'server_id': server_id,
            'connectivity': connectivity_results
        })
        
    except Exception as e:
        logger.error(f"Error testing connectivity for {server_id}: {e}")
        return jsonify({'success': False, 'error': str(e)})

def test_ssh_connectivity(ip_address: str) -> dict:
    """Test SSH connectivity to an IP address"""
    try:
        ssh_config = config.get('ssh', {})
        username = ssh_config.get('username', 'ubuntu')
        
        with ssh_manager.get_client(ip_address, username) as ssh_client:
            result = ssh_client.execute_command("echo 'SSH test successful'", timeout=10)
            
            return {
                'success': result.exit_code == 0,
                'response_time': '< 10s',
                'details': result.stdout if result.exit_code == 0 else result.stderr
            }
            
    except Exception as e:
        return {
            'success': False,
            'response_time': 'timeout',
            'details': str(e)
        }

def test_ipmi_connectivity(ipmi_address: str) -> dict:
    """Test IPMI connectivity via ping"""
    try:
        import subprocess
        import time
        
        start_time = time.time()
        result = subprocess.run(['ping', '-c', '3', '-W', '5', ipmi_address], 
                              capture_output=True, text=True, timeout=30)
        response_time = time.time() - start_time
        
        return {
            'success': result.returncode == 0,
            'response_time': f"{response_time:.2f}s",
            'details': 'Ping successful' if result.returncode == 0 else 'Ping failed'
        }
        
    except Exception as e:
        return {
            'success': False,
            'response_time': 'timeout',
            'details': str(e)
        }


@app.route('/database')
def database_management():
    """Database management page."""
    try:
        # Get database status and stats
        status = "Connected"  # Mock status
        return render_template('database_enhanced.html', status=status)
    except Exception as e:
        logger.error(f"Error loading database management: {e}")
        flash(f"Error loading database management: {e}", 'error')
        return render_template('error.html', error=str(e))


@app.route('/maas')
def maas_management():
    """MaaS management page."""
    try:
        return render_template('maas_management.html')
    except Exception as e:
        logger.error(f"Error loading MaaS management: {e}")
        flash(f"Error loading MaaS management: {e}", 'error')
        return render_template('error.html', error=str(e))


@app.route('/hardware')
def hardware_management():
    """Hardware management page."""
    try:
        return render_template('hardware.html')
    except Exception as e:
        logger.error(f"Error loading hardware management: {e}")
        flash(f"Error loading hardware management: {e}", 'error')
        return render_template('error.html', error=str(e))


@app.route('/device-selection')
def device_selection():
    """Device selection interface for commissioning"""
    try:
        return render_template('device_selection.html')
    except Exception as e:
        logger.error(f"Error loading device selection: {e}")
        flash(f"Error loading device selection: {e}", 'error')
        return render_template('error.html', error=str(e))


@app.route('/logs')
def view_logs():
    """View application logs."""
    try:
        # In a real implementation, read from log files
        logs = [
            {'timestamp': datetime.now().isoformat(), 'level': 'INFO', 'message': 'GUI application started'},
            {'timestamp': datetime.now().isoformat(), 'level': 'INFO', 'message': 'BIOS manager initialized'},
        ]
        return render_template('logs.html', logs=logs)
    except Exception as e:
        logger.error(f"Error loading logs: {e}")
        flash(f"Error loading logs: {e}", 'error')
        return render_template('error.html', error=str(e))


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    logger.info('Client connected to WebSocket')
    emit('connected', {'message': 'Connected to HWAutomation GUI'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    logger.info('Client disconnected from WebSocket')


# ============================================================================
# Orchestration API Endpoints
# ============================================================================

@app.route('/api/orchestration/provision', methods=['POST'])
def api_provision_server():
    """Start server provisioning workflow"""
    if not provisioning_workflow:
        return jsonify({'error': 'Orchestration system not available'}), 503
    
    try:
        data = request.get_json()
        
        # Validate required fields - only server_id and device_type are required now
        required_fields = ['server_id', 'device_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Start provisioning workflow with optional IPMI and rack location
        result = provisioning_workflow.provision_server(
            server_id=data['server_id'],
            device_type=data['device_type'],
            target_ipmi_ip=data.get('target_ipmi_ip'),  # Now optional
            rack_location=data.get('rack_location'),
            progress_callback=lambda progress: socketio.emit('workflow_progress', progress)
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error starting provisioning workflow: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/orchestration/configure-ipmi', methods=['POST'])
def api_configure_server_ipmi():
    """Configure IPMI for a commissioned server"""
    if not provisioning_workflow:
        return jsonify({'error': 'Orchestration system not available'}), 503
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['server_id', 'target_ipmi_ip']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Configure IPMI for the server
        result = provisioning_workflow.configure_server_ipmi(
            server_id=data['server_id'],
            target_ipmi_ip=data['target_ipmi_ip'],
            rack_location=data.get('rack_location')
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error configuring server IPMI: {e}")
        return jsonify({'error': str(e)}), 500

# Device Selection API Endpoints
@app.route('/api/devices/available', methods=['GET'])
def api_get_available_devices():
    """Get list of available devices from MaaS"""
    if not device_selection_service:
        return jsonify({'error': 'Device selection service not available'}), 503
    
    try:
        # Parse query parameters for filtering
        args = request.args
        machine_filter = MachineFilter()
        
        # Status filter
        if 'status' in args:
            status_map = {
                'available': MachineStatus.AVAILABLE,
                'commissioned': MachineStatus.COMMISSIONED,
                'deployed': MachineStatus.DEPLOYED,
                'other': MachineStatus.OTHER
            }
            if args['status'] in status_map:
                machine_filter.status_category = status_map[args['status']]
        
        # Hardware filters
        if 'min_cpu' in args:
            machine_filter.min_cpu_count = int(args['min_cpu'])
        if 'min_memory_gb' in args:
            machine_filter.min_memory_gb = float(args['min_memory_gb'])
        if 'min_storage_gb' in args:
            machine_filter.min_storage_gb = float(args['min_storage_gb'])
        if 'architecture' in args:
            machine_filter.architecture = args['architecture']
        if 'power_type' in args:
            machine_filter.power_type = args['power_type']
        if 'hostname_pattern' in args:
            machine_filter.hostname_pattern = args['hostname_pattern']
        
        # Tag filters
        if 'has_tags' in args:
            machine_filter.has_tags = args['has_tags'].split(',')
        if 'exclude_tags' in args:
            machine_filter.exclude_tags = args['exclude_tags'].split(',')
        
        machines = device_selection_service.list_available_machines(machine_filter)
        
        return jsonify({
            'machines': machines,
            'count': len(machines)
        })
        
    except Exception as e:
        logger.error(f"Error getting available devices: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<system_id>/details', methods=['GET'])
def api_get_device_details(system_id):
    """Get detailed information about a specific device"""
    logger.info(f"Device details requested for system_id: {system_id}")
    
    if not device_selection_service:
        logger.error("Device selection service not available")
        return jsonify({'success': False, 'error': 'Device selection service not available'}), 503
    
    try:
        # First try to get basic machine info from the available machines list
        # This is more reliable than the detailed API call
        machines = device_selection_service.list_available_machines()
        selected_machine = None
        
        for machine in machines:
            if machine.get('system_id') == system_id:
                selected_machine = machine
                break
        
        if not selected_machine:
            logger.warning(f"Device {system_id} not found in available machines")
            return jsonify({'success': False, 'error': 'Device not found'}), 404
        
        # Try to get detailed info, but fall back to basic info if it fails
        try:
            detailed_info = device_selection_service.get_machine_details(system_id)
            logger.info(f"Got detailed info for {system_id}: {bool(detailed_info)}")
        except Exception as e:
            logger.warning(f"Failed to get detailed info for {system_id}: {e}")
            detailed_info = None
        
        # Build response using available data
        device_data = {
            'hostname': selected_machine.get('hostname', 'Unknown'),
            'system_id': system_id,
            'status': selected_machine.get('status', 'Unknown'),
            'owner': selected_machine.get('owner', 'None'),
            'architecture': selected_machine.get('architecture', 'Unknown'),
            'power_type': selected_machine.get('power_type', 'Unknown'),
            'cpu_count': selected_machine.get('cpu_count', 0),
            'memory_display': selected_machine.get('memory_display', 'Unknown'),
            'storage_display': selected_machine.get('storage_display', 'Unknown'),
            'bios_boot_method': selected_machine.get('bios_boot_method', 'Unknown'),
            'ip_addresses': selected_machine.get('ip_addresses', []),
            'tags': selected_machine.get('tags', [])
        }
        
        # If we have detailed info, enhance the response
        if detailed_info and isinstance(detailed_info, dict):
            basic_info = detailed_info.get('basic_info', {})
            hardware = detailed_info.get('hardware', {})
            network = detailed_info.get('network', {})
            
            # Update with more detailed information where available
            if basic_info.get('hostname'):
                device_data['hostname'] = basic_info['hostname']
            if basic_info.get('owner'):
                device_data['owner'] = basic_info['owner']
            if hardware.get('cpu_count'):
                device_data['cpu_count'] = hardware['cpu_count']
            if network.get('ip_addresses'):
                device_data['ip_addresses'] = network['ip_addresses']
            if detailed_info.get('tags'):
                device_data['tags'] = detailed_info['tags']
        
        logger.info(f"Returning device data for {system_id}")
        return jsonify({
            'success': True,
            'device': device_data
        })
        
    except Exception as e:
        logger.error(f"Error getting device details for {system_id}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/devices/<system_id>/validate', methods=['GET'])
def api_validate_device(system_id):
    """Validate if a device is suitable for commissioning"""
    if not device_selection_service:
        return jsonify({'error': 'Device selection service not available'}), 503
    
    try:
        is_valid, reason = device_selection_service.validate_machine_for_commissioning(system_id)
        
        # Also suggest device type
        suggested_device_type = device_selection_service.suggest_device_type(system_id)
        
        return jsonify({
            'valid': is_valid,
            'reason': reason,
            'suggested_device_type': suggested_device_type
        })
        
    except Exception as e:
        logger.error(f"Error validating device {system_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/status-summary', methods=['GET'])
def api_get_device_status_summary():
    """Get summary of device statuses"""
    if not device_selection_service:
        return jsonify({'error': 'Device selection service not available'}), 503
    
    try:
        summary = device_selection_service.get_status_summary()
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Error getting device status summary: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/search', methods=['POST'])
def api_search_devices():
    """Search for devices by hostname or other criteria"""
    if not device_selection_service:
        return jsonify({'error': 'Device selection service not available'}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No search criteria provided'}), 400
        
        results = []
        
        # Search by hostname
        if 'hostname' in data:
            machine = device_selection_service.get_machine_by_hostname(data['hostname'])
            if machine:
                results.append(machine)
        
        # Search with filters
        if 'filter' in data:
            filter_data = data['filter']
            machine_filter = MachineFilter()
            
            # Apply filter criteria from request
            if 'status_category' in filter_data:
                status_map = {
                    'available': MachineStatus.AVAILABLE,
                    'commissioned': MachineStatus.COMMISSIONED,
                    'deployed': MachineStatus.DEPLOYED,
                    'other': MachineStatus.OTHER
                }
                if filter_data['status_category'] in status_map:
                    machine_filter.status_category = status_map[filter_data['status_category']]
            
            for field in ['min_cpu_count', 'min_memory_gb', 'min_storage_gb', 
                         'architecture', 'power_type', 'hostname_pattern']:
                if field in filter_data:
                    setattr(machine_filter, field, filter_data[field])
            
            if 'has_tags' in filter_data:
                machine_filter.has_tags = filter_data['has_tags']
            if 'exclude_tags' in filter_data:
                machine_filter.exclude_tags = filter_data['exclude_tags']
            
            filtered_machines = device_selection_service.list_available_machines(machine_filter)
            results.extend(filtered_machines)
        
        # Remove duplicates
        seen_ids = set()
        unique_results = []
        for machine in results:
            if machine['system_id'] not in seen_ids:
                unique_results.append(machine)
                seen_ids.add(machine['system_id'])
        
        return jsonify({
            'results': unique_results,
            'count': len(unique_results)
        })
        
    except Exception as e:
        logger.error(f"Error searching devices: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/commission', methods=['POST'])
def api_commission_device():
    """Commission a device using the orchestration system"""
    logger.info("Commission device endpoint called")
    
    if not provisioning_workflow:
        logger.error("Provisioning workflow not available")
        return jsonify({'success': False, 'message': 'Orchestration system not available'}), 503
    
    try:
        data = request.get_json()
        logger.info(f"Commission request data: {data}")
        
        if not data:
            return jsonify({'success': False, 'message': 'No commission data provided'}), 400
        
        # Validate required fields
        required_fields = ['system_id', 'device_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
        
        logger.info(f"Starting commissioning for system_id: {data['system_id']}, device_type: {data['device_type']} (auto-detecting force recommission needs)")
        
        # Start provisioning workflow via orchestration system
        # The workflow will automatically detect if force recommissioning is needed
        result = provisioning_workflow.provision_server(
            server_id=data['system_id'],  # Use system_id as server_id
            device_type=data['device_type'],
            target_ipmi_ip=data.get('target_ipmi_ip'),  # Optional
            rack_location=data.get('rack_location'),    # Optional
            progress_callback=lambda progress: socketio.emit('workflow_progress', progress)
        )
        
        logger.info(f"Provisioning workflow result: {result}")
        
        if result.get('success', False):
            return jsonify({
                'success': True,
                'message': 'Device commissioning started successfully (auto-detecting force recommission needs)',
                'workflow_id': result.get('workflow_id'),
                'server_id': data['system_id'],
                'device_type': data['device_type']
            })
        else:
            error_msg = result.get('message', 'Failed to start commissioning')
            logger.error(f"Commissioning failed: {error_msg}")
            return jsonify({
                'success': False,
                'message': error_msg
            })
        
    except Exception as e:
        logger.error(f"Error commissioning device: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/orchestration/workflow/<workflow_id>/status', methods=['GET'])
def api_get_workflow_status(workflow_id):
    """Get detailed workflow status"""
    if not workflow_manager:
        return jsonify({'error': 'Orchestration system not available'}), 503
    
    try:
        workflow = workflow_manager.get_workflow(workflow_id)
        if not workflow:
            return jsonify({'error': 'Workflow not found'}), 404
        
        status = workflow.get_status()
        
        # Add additional debugging information to logs
        logger.info(f"Workflow {workflow_id} status: {status.get('status', 'unknown')}")
        if status.get('steps'):
            for i, step in enumerate(status['steps']):
                step_status = step.get('status', 'unknown')
                step_name = step.get('name', f'step_{i}')
                logger.info(f"  Step {i+1}: {step_name} - {step_status}")
                if step.get('error'):
                    logger.error(f"    Error: {step['error']}")
                if step.get('result'):
                    logger.info(f"    Result: {step['result']}")
        
        # Add current step information
        if hasattr(workflow, 'current_step_index'):
            status['current_step_index'] = workflow.current_step_index
            logger.info(f"  Current step index: {workflow.current_step_index}")
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/orchestration/workflow/<workflow_id>/cancel', methods=['POST'])
def api_cancel_workflow(workflow_id):
    """Cancel a running workflow"""
    if not workflow_manager:
        return jsonify({'error': 'Orchestration system not available'}), 503
    
    try:
        workflow = workflow_manager.get_workflow(workflow_id)
        if not workflow:
            return jsonify({'error': 'Workflow not found'}), 404
        
        workflow.cancel()
        return jsonify({'message': 'Workflow cancelled successfully'})
        
    except Exception as e:
        logger.error(f"Error cancelling workflow: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/orchestration/workflow/<workflow_id>/debug', methods=['GET'])
def api_debug_workflow(workflow_id):
    """Get detailed workflow debug information"""
    if not workflow_manager:
        return jsonify({'error': 'Orchestration system not available'}), 503
    
    try:
        workflow = workflow_manager.get_workflow(workflow_id)
        if not workflow:
            return jsonify({'error': 'Workflow not found'}), 404
        
        # Get basic status
        status = workflow.get_status()
        
        # Add detailed debug information
        debug_info = {
            'workflow_id': workflow_id,
            'status': status,
            'workflow_type': type(workflow).__name__,
            'is_running': workflow.is_running() if hasattr(workflow, 'is_running') else 'unknown',
            'thread_alive': workflow.execution_thread.is_alive() if hasattr(workflow, 'execution_thread') else 'no_thread',
            'current_step': getattr(workflow, 'current_step_index', 'unknown'),
            'total_steps': len(workflow.steps) if hasattr(workflow, 'steps') else 'unknown'
        }
        
        # Add step details
        if hasattr(workflow, 'steps'):
            debug_info['step_details'] = []
            for i, step in enumerate(workflow.steps):
                step_info = {
                    'index': i,
                    'name': step.get('name', f'step_{i}'),
                    'function': step.get('function', 'unknown'),
                    'status': 'completed' if i < getattr(workflow, 'current_step_index', 0) else 'pending'
                }
                debug_info['step_details'].append(step_info)
        
        # Log debug information
        logger.info(f"Debug info for workflow {workflow_id}: {debug_info}")
        
        return jsonify(debug_info)
        
    except Exception as e:
        logger.error(f"Error getting workflow debug info: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/orchestration/workflows', methods=['GET'])
def api_list_workflows():
    """List all workflows"""
    if not workflow_manager:
        return jsonify({'error': 'Orchestration system not available'}), 503
    
    try:
        workflow_ids = workflow_manager.list_workflows()
        workflows = []
        
        for workflow_id in workflow_ids:
            workflow = workflow_manager.get_workflow(workflow_id)
            if workflow:
                workflows.append(workflow.get_status())
        
        return jsonify({'workflows': workflows})
        
    except Exception as e:
        logger.error(f"Error listing workflows: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/hardware/discover', methods=['POST'])
def api_discover_hardware():
    """Discover hardware information from a remote host"""
    if not workflow_manager:
        return jsonify({'error': 'Orchestration system not available'}), 503
    
    try:
        data = request.get_json()
        if not data or 'host' not in data:
            return jsonify({'error': 'Host address is required'}), 400
        
        host = data['host']
        username = data.get('username', 'ubuntu')
        key_file = data.get('key_file')
        
        logger.info(f"Starting hardware discovery for {host}")
        
        # Perform hardware discovery
        hardware_info = workflow_manager.discovery_manager.discover_hardware(
            host=host,
            username=username,
            key_file=key_file
        )
        
        return jsonify({
            'success': True,
            'hardware_info': hardware_info.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Hardware discovery failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/hardware/scan-network', methods=['POST'])
def api_scan_network():
    """Scan network range for IPMI addresses"""
    if not workflow_manager:
        return jsonify({'error': 'Orchestration system not available'}), 503
    
    try:
        data = request.get_json()
        if not data or 'network_range' not in data:
            return jsonify({'error': 'Network range is required'}), 400
        
        network_range = data['network_range']
        username = data.get('username', 'ubuntu')
        key_file = data.get('key_file')
        
        logger.info(f"Starting network scan for {network_range}")
        
        # Perform network scan for IPMI addresses
        ipmi_addresses = workflow_manager.discovery_manager.discover_ipmi_from_network_scan(
            network_range=network_range
        )
        
        return jsonify({
            'success': True,
            'ipmi_addresses': ipmi_addresses,
            'count': len(ipmi_addresses)
        })
        
    except Exception as e:
        logger.error(f"Network scan failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/orchestration')
def orchestration_page():
    """Server orchestration management page"""
    return render_template('orchestration.html')


def create_app(debug=False):
    """Create and configure the Flask application."""
    app.debug = debug
    return app


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='HWAutomation Web GUI')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    logger.info(f"Starting HWAutomation Web GUI on {args.host}:{args.port}")
    socketio.run(app, host=args.host, port=args.port, debug=args.debug, allow_unsafe_werkzeug=True)
