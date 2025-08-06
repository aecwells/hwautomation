#!/usr/bin/env python3
"""
Simplified HWAutomation GUI

Focused web interface for batch device commissioning and BMC management.
Core workflow: MaaS device discovery → Device type selection → Batch commissioning → IPMI/BIOS configuration
"""

import sys
import os  
import logging
import threading
import time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_socketio import SocketIO, emit
import json
from datetime import datetime
from typing import Dict, List, Any

# Add src to path
project_root = Path(__file__).parent.parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

from hwautomation.hardware.bios_config import BiosConfigManager
from hwautomation.database.helper import DbHelper
from hwautomation.utils.env_config import load_config
from hwautomation.maas.client import create_maas_client
from hwautomation.orchestration.workflow_manager import WorkflowManager
from hwautomation.orchestration.server_provisioning import ServerProvisioningWorkflow
from hwautomation.orchestration.device_selection import DeviceSelectionService

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'hwautomation-simplified-gui'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables for background monitoring
workflow_monitor_thread = None
stop_monitoring = False

# Load configuration
config = load_config()
db_path = config.get('database', {}).get('path', 'hw_automation.db')

# Ensure absolute database path
if not os.path.isabs(db_path):
    db_path = str(project_root / db_path)

# Initialize core components
bios_manager = BiosConfigManager()
db_helper = DbHelper(tablename="servers", db_path=db_path)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize orchestration system
try:
    config_for_orchestration = config.copy()
    config_for_orchestration['database'] = {'path': db_path}
    
    workflow_manager = WorkflowManager(config_for_orchestration)
    provisioning_workflow = ServerProvisioningWorkflow(workflow_manager)
    device_selection_service = DeviceSelectionService(config=config.get('maas', {}))
    maas_client = create_maas_client(config.get('maas', {}))
    
    logger.info("✅ Orchestration system initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize orchestration system: {e}")
    workflow_manager = None
    provisioning_workflow = None
    device_selection_service = None
    maas_client = None


# =============================================================================
# MAIN DASHBOARD - Single Page Application
# =============================================================================

@app.route('/')
def dashboard():
    """Main dashboard - Single page for all operations"""
    try:
        # Get device types for selection
        device_types_list = bios_manager.get_device_types()
        device_types_dict = {}
        
        # Get full device configurations for the UI
        for device_type in device_types_list:
            config = bios_manager.get_device_config(device_type)
            if config:
                device_types_dict[device_type] = config
        
        # Get MaaS connection status
        maas_status = 'disconnected'
        available_machines = []
        if maas_client:
            try:
                machines = maas_client.get_machines()
                if machines:
                    maas_status = 'connected'
                    available_machines = [m for m in machines if m.get('status_name') in ['Ready', 'New', 'Failed commissioning']]
            except Exception as e:
                logger.warning(f"MaaS connection check failed: {e}")
        
        # Get current database stats
        database_count = 0
        if db_helper:
            try:
                # Count rows in the servers table
                conn = db_helper.sql_database
                cursor = conn.cursor()
                table_name = db_helper._get_table_name()
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                result = cursor.fetchone()
                database_count = result[0] if result else 0
            except Exception as e:
                logger.warning(f"Failed to get database count: {e}")
                database_count = 0
        
        stats = {
            'device_types': len(device_types_list),
            'maas_status': maas_status,
            'available_machines': len(available_machines),
            'database_servers': database_count
        }
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             device_types=device_types_list,
                             device_types_dict=device_types_dict,
                             available_machines=available_machines[:10])  # Show first 10 for UI
                             
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template('error_simple.html', error=str(e))


# =============================================================================
# ENHANCED SIMPLIFIED GUI ROUTES - Added Database and Theme Support
# =============================================================================

@app.route('/database')
def database_management():
    """Database management page"""
    try:
        return render_template('database_simple.html')
    except Exception as e:
        logger.error(f"Error loading database management: {e}")
        return render_template('error_simple.html', error=str(e))

# =============================================================================
# API ENDPOINTS - Core Functionality Only
# =============================================================================

@app.route('/api/devices/detect-types', methods=['POST'])
def api_detect_device_types():
    """Detect compatible device types for selected machines"""
    try:
        from hwautomation.hardware.enhanced_detection import EnhancedHardwareDetector
        
        data = request.get_json()
        machine_ids = data.get('machine_ids', [])
        
        if not machine_ids:
            return jsonify({'error': 'No machine IDs provided'}), 400
        
        if not maas_client:
            return jsonify({'error': 'MaaS client not available'}), 503
        
        detector = EnhancedHardwareDetector(maas_client)
        results = {}
        
        for machine_id in machine_ids:
            matches = detector.detect_matching_device_types(machine_id)
            results[machine_id] = [
                {
                    'device_type': device_type,
                    'confidence': confidence,
                    'display_name': detector.get_device_type_info(device_type).display_name if detector.get_device_type_info(device_type) else device_type,
                    'description': detector.get_device_type_info(device_type).description if detector.get_device_type_info(device_type) else ''
                }
                for device_type, confidence in matches
            ]
        
        return jsonify({
            'detected_types': results,
            'available_types': [
                {
                    'device_type': dt.device_type,
                    'display_name': dt.display_name,
                    'description': dt.description
                }
                for dt in detector.list_all_device_types()
            ]
        })
        
    except Exception as e:
        logger.error(f"Device type detection failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/validate-ipmi', methods=['POST'])
def api_validate_ipmi():
    """Validate IPMI configuration for a device"""
    try:
        from hwautomation.hardware.ipmi_automation import IPMIAutomationService
        
        data = request.get_json()
        ipmi_ip = data.get('ipmi_ip')
        device_type = data.get('device_type')
        
        if not ipmi_ip or not device_type:
            return jsonify({'error': 'IPMI IP and device type required'}), 400
        
        ipmi_service = IPMIAutomationService(config)
        validation_result = ipmi_service.validate_ipmi_configuration(ipmi_ip, device_type)
        
        return jsonify(validation_result)
        
    except Exception as e:
        logger.error(f"IPMI validation failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/validate-boarding', methods=['POST'])
def api_validate_boarding():
    """Perform complete boarding validation for a device"""
    try:
        from hwautomation.validation.boarding_validator import BMCBoardingValidator
        
        data = request.get_json()
        device_id = data.get('device_id')
        device_type = data.get('device_type')
        server_ip = data.get('server_ip')
        ipmi_ip = data.get('ipmi_ip')
        
        if not all([device_id, device_type, server_ip, ipmi_ip]):
            return jsonify({'error': 'All parameters required: device_id, device_type, server_ip, ipmi_ip'}), 400
        
        validator = BMCBoardingValidator(config)
        validation = validator.validate_complete_boarding(device_id, device_type, server_ip, ipmi_ip)
        
        # Convert to JSON-serializable format
        result = {
            'device_id': validation.device_id,
            'device_type': validation.device_type,
            'overall_status': validation.overall_status.value,
            'summary': validation.summary,
            'validations': [
                {
                    'check_name': v.check_name,
                    'status': v.status.value,
                    'message': v.message,
                    'details': v.details,
                    'remediation': v.remediation
                }
                for v in validation.validations
            ]
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Boarding validation failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/maas/discover', methods=['GET'])
def api_discover_devices():
    """Discover available devices from MaaS"""
    if not maas_client:
        return jsonify({'error': 'MaaS client not available'}), 503
    
    try:
        machines = maas_client.get_machines()
        if not machines:
            return jsonify({'devices': [], 'message': 'No machines found in MaaS'})
        
        # Filter for available machines only
        available_machines = []
        for machine in machines:
            status = machine.get('status_name', 'Unknown')
            if status in ['Ready', 'New', 'Failed commissioning', 'Failed testing']:
                available_machines.append({
                    'system_id': machine.get('system_id'),
                    'hostname': machine.get('hostname', 'Unknown'),
                    'status': status,
                    'architecture': machine.get('architecture', 'Unknown'),
                    'cpu_count': machine.get('cpu_count', 0),
                    'memory': machine.get('memory', 0),
                    'power_type': machine.get('power_type', 'Unknown')
                })
        
        return jsonify({
            'devices': available_machines,
            'total_discovered': len(machines),
            'available_count': len(available_machines)
        })
        
    except Exception as e:
        logger.error(f"Device discovery failed: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/batch/commission', methods=['POST'])
def api_batch_commission():
    """Batch commission devices of the same type"""
    if not workflow_manager or not provisioning_workflow:
        return jsonify({'error': 'Orchestration system not available'}), 503
    
    try:
        data = request.get_json()
        device_type = data.get('device_type')
        device_ids = data.get('device_ids', [])
        target_ipmi_range = data.get('ipmi_range', '192.168.100.50')
        
        if not device_type or not device_ids:
            return jsonify({'error': 'Device type and device IDs are required'}), 400
        
        # Validate IPMI range format
        if not target_ipmi_range or not target_ipmi_range.strip():
            target_ipmi_range = '192.168.100.50'  # Default fallback
        
        # Validate IP format
        try:
            ip_parts = target_ipmi_range.strip().split('.')
            if len(ip_parts) != 4:
                raise ValueError("Invalid IP format")
            # Test that all parts are valid integers
            for part in ip_parts:
                if not part or int(part) < 0 or int(part) > 255:
                    raise ValueError("Invalid IP octet")
        except (ValueError, AttributeError):
            logger.warning(f"Invalid IPMI range '{target_ipmi_range}', using default")
            target_ipmi_range = '192.168.100.50'
        
        logger.info(f"🚀 Starting batch commissioning for {len(device_ids)} devices of type {device_type}")
        
        # Start batch workflow
        batch_results = []
        for i, device_id in enumerate(device_ids):
            try:
                # Calculate IPMI IP (increment from base)
                base_ip_parts = target_ipmi_range.split('.')
                base_ip_parts[-1] = str(int(base_ip_parts[-1]) + i)
                target_ipmi_ip = '.'.join(base_ip_parts)
                
                # Start individual workflow
                workflow_id = provisioning_workflow.provision_server(
                    server_id=device_id,
                    device_type=device_type,
                    target_ipmi_ip=target_ipmi_ip
                )
                
                batch_results.append({
                    'device_id': device_id,
                    'workflow_id': workflow_id,
                    'target_ipmi_ip': target_ipmi_ip,
                    'status': 'started'
                })
                
            except Exception as e:
                logger.error(f"Failed to start workflow for device {device_id}: {e}")
                batch_results.append({
                    'device_id': device_id,
                    'workflow_id': None,
                    'error': str(e),
                    'status': 'failed'
                })
        
        return jsonify({
            'success': True,
            'batch_id': f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'device_type': device_type,
            'total_devices': len(device_ids),
            'results': batch_results
        })
        
    except Exception as e:
        logger.error(f"Batch commissioning failed: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/device-types', methods=['GET'])
def api_get_device_types():
    """Get available BMC device types"""
    try:
        device_types_list = bios_manager.get_device_types()
        
        # Format for UI consumption
        formatted_types = {}
        for device_type in device_types_list:
            config = bios_manager.get_device_config(device_type)
            if config:
                formatted_types[device_type] = {
                    'name': device_type,
                    'description': config.get('description', 'No description'),
                    'vendor': config.get('hardware_specs', {}).get('vendor', 'Unknown'),
                    'cpu_cores': config.get('hardware_specs', {}).get('cpu_cores', 0),
                    'memory_gb': config.get('hardware_specs', {}).get('ram_gb', 0)
                }
            else:
                # Fallback if config not found
                formatted_types[device_type] = {
                    'name': device_type,
                    'description': 'No description available',
                    'vendor': 'Unknown',
                    'cpu_cores': 0,
                    'memory_gb': 0
                }
        
        return jsonify({'device_types': formatted_types})
        
    except Exception as e:
        logger.error(f"Error getting device types: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/workflows/status', methods=['GET'])
def api_workflow_status():
    """Get status of all active workflows"""
    if not workflow_manager:
        return jsonify({'error': 'Orchestration system not available'}), 503
    
    try:
        workflow_ids = workflow_manager.list_workflows()
        workflows = []
        
        for workflow_id in workflow_ids:
            workflow = workflow_manager.get_workflow(workflow_id)
            if workflow:
                status = workflow.get_status()
                workflows.append(status)
        
        return jsonify({'workflows': workflows})
        
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/database/servers', methods=['GET'])
def api_get_servers():
    """Get server information from database"""
    try:
        servers = []
        if db_helper:
            # Get all servers from database
            conn = db_helper.sql_database
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {db_helper.tablename}")
            rows = cursor.fetchall()
            
            # Get column names
            column_names = [description[0] for description in cursor.description]
            
            # Convert to list of dictionaries
            for row in rows:
                server = dict(zip(column_names, row))
                servers.append(server)
        
        return jsonify({'servers': servers})
        
    except Exception as e:
        logger.error(f"Error getting servers: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/database/info', methods=['GET'])
def api_database_info():
    """Get database information and statistics"""
    try:
        import sqlite3
        from pathlib import Path
        
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
        
        # Create a new connection for this request
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
        
        conn.close()
        
        info = {
            'version': '3.x',  # SQLite version
            'size': db_size,
            'table_count': table_count,
            'server_count': server_count,
            'path': db_path
        }
        
        return jsonify({'success': True, 'info': info})
        
    except Exception as e:
        logger.error(f"Error getting database info: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/database/tables', methods=['GET'])
def api_get_database_tables():
    """Get all database tables and their data"""
    try:
        import sqlite3
        
        conn = sqlite3.connect(db_helper.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        table_names = [row[0] for row in cursor.fetchall()]
        
        tables_data = {}
        for table_name in table_names:
            # Get table data
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")  # Limit for performance
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            table_data = [dict(row) for row in rows]
            
            # Get total count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_count = cursor.fetchone()[0]
            
            tables_data[table_name] = {
                'data': table_data,
                'count': total_count,
                'showing': min(len(table_data), 100)
            }
        
        conn.close()
        
        return jsonify({'success': True, 'tables': tables_data})
        
    except Exception as e:
        logger.error(f"Error getting database tables: {e}")
        return jsonify({'success': False, 'error': str(e)})


# =============================================================================
# WEBSOCKET EVENTS - Real-time Updates
# =============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info("Client connected to WebSocket")
    
    # Start workflow monitoring when first client connects
    start_workflow_monitor()
    
    # Send initial workflow status
    handle_workflow_updates()
    emit('status', {'message': 'Connected to HWAutomation'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("Client disconnected from WebSocket")


@socketio.on('request_workflow_updates')
def handle_workflow_updates():
    """Send workflow status updates to connected clients"""
    if workflow_manager:
        try:
            workflow_ids = workflow_manager.list_workflows()
            workflows = []
            
            for workflow_id in workflow_ids:
                workflow = workflow_manager.get_workflow(workflow_id)
                if workflow:
                    workflows.append(workflow.get_status())
            
            emit('workflow_updates', {'workflows': workflows})
            
        except Exception as e:
            logger.error(f"Error sending workflow updates: {e}")
            emit('error', {'message': str(e)})


def workflow_monitor_background():
    """Background thread to monitor workflows and send real-time updates"""
    global stop_monitoring
    
    logger.info("🔄 Starting background workflow monitor")
    previous_workflow_count = 0
    previous_workflow_states = {}
    
    while not stop_monitoring:
        try:
            if workflow_manager:
                # Get current workflows
                workflow_ids = workflow_manager.list_workflows()
                workflows = []
                current_workflow_states = {}
                
                for workflow_id in workflow_ids:
                    workflow = workflow_manager.get_workflow(workflow_id)
                    if workflow:
                        workflow_status = workflow.get_status()
                        workflows.append(workflow_status)
                        
                        # Track state changes for activity logging
                        current_step = workflow_status.get('current_step_name', 'Unknown')
                        current_status = workflow_status.get('status', 'unknown')
                        
                        # Extract server ID from workflow ID
                        server_match = workflow_id.match(r'provision_([^_]+)_') if hasattr(workflow_id, 'match') else None
                        if not server_match:
                            import re
                            server_match = re.match(r'provision_([^_]+)_', workflow_id)
                        server_id = server_match.group(1) if server_match else workflow_id
                        
                        state_key = f"{workflow_id}:{current_step}:{current_status}"
                        current_workflow_states[workflow_id] = state_key
                        
                        # Check if this is a new state we haven't seen before
                        if workflow_id not in previous_workflow_states or previous_workflow_states[workflow_id] != state_key:
                            # Send activity update for step changes
                            activity_message = ""
                            if current_status == 'running':
                                activity_message = f"Server {server_id}: {current_step}"
                            elif current_status == 'completed':
                                activity_message = f"Server {server_id}: Workflow completed successfully"
                            elif current_status == 'failed':
                                activity_message = f"Server {server_id}: Workflow failed at {current_step}"
                            
                            if activity_message:
                                socketio.emit('activity_update', {
                                    'message': activity_message,
                                    'level': 'error' if current_status == 'failed' else 'info',
                                    'workflow_id': workflow_id,
                                    'server_id': server_id,
                                    'step': current_step,
                                    'status': current_status
                                })
                                logger.info(f"🔔 Activity: {activity_message}")
                
                # Always broadcast workflow updates
                current_count = len(workflows)
                if current_count > 0 or current_count != previous_workflow_count:
                    socketio.emit('workflow_updates', {'workflows': workflows})
                    
                    # Log workflow progress for debugging
                    for workflow in workflows:
                        if workflow.get('status') == 'running':
                            current_step = workflow.get('current_step_name', 'Unknown')
                            logger.info(f"📊 Workflow {workflow['id']}: {current_step}")
                
                previous_workflow_count = current_count
                previous_workflow_states = current_workflow_states
                
        except Exception as e:
            logger.error(f"Error in workflow monitor: {e}")
        
        # Sleep for 3 seconds between checks
        time.sleep(3)
    
    logger.info("🛑 Background workflow monitor stopped")


def start_workflow_monitor():
    """Start the background workflow monitoring thread"""
    global workflow_monitor_thread, stop_monitoring
    
    if workflow_monitor_thread is None or not workflow_monitor_thread.is_alive():
        stop_monitoring = False
        workflow_monitor_thread = threading.Thread(target=workflow_monitor_background, daemon=True)
        workflow_monitor_thread.start()
        logger.info("✅ Background workflow monitor started")


def stop_workflow_monitor():
    """Stop the background workflow monitoring thread"""
    global stop_monitoring
    stop_monitoring = True
    if workflow_monitor_thread:
        logger.info("🛑 Stopping background workflow monitor")


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    return render_template('error_simple.html', error="Page not found"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('error_simple.html', error="Internal server error"), 500


# =============================================================================
# APPLICATION FACTORY
# =============================================================================

def create_app(debug=False):
    """Create and configure the Flask application"""
    app.debug = debug
    return app


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='HWAutomation Simplified GUI')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    logger.info(f"🚀 Starting HWAutomation Simplified GUI on {args.host}:{args.port}")
    socketio.run(app, host=args.host, port=args.port, debug=args.debug, allow_unsafe_werkzeug=True)
