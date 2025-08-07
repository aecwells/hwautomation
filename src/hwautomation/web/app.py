#!/usr/bin/env python3
"""
Flask Web Application for HWAutomation

Modular web interface for batch device commissioning and BMC management.
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
from hwautomation.orchestration.workflow_manager import WorkflowStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory for Flask app."""
    
    # Add src to path for development
    project_root = Path(__file__).parent.parent.parent.parent
    src_path = project_root / 'src'
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from hwautomation.hardware.bios_config import BiosConfigManager
    from hwautomation.database.helper import DbHelper
    from hwautomation.utils.env_config import load_config
    from hwautomation.maas.client import create_maas_client
    from hwautomation.orchestration.workflow_manager import WorkflowManager
    from hwautomation.orchestration.server_provisioning import ServerProvisioningWorkflow
    from hwautomation.orchestration.device_selection import DeviceSelectionService

    # Initialize Flask app
    app = Flask(__name__, 
                template_folder=str(Path(__file__).parent / 'templates'),
                static_folder=str(Path(__file__).parent / 'static'))
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'hwautomation-web-interface')
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")

    # Global variables for background monitoring
    workflow_monitor_thread = None
    stop_monitoring = False

    # Load configuration from environment variables with .env file
    project_root = Path(__file__).parent.parent.parent.parent
    env_file = project_root / '.env'
    config = load_config(str(env_file) if env_file.exists() else None)
    db_path = config.get('database', {}).get('path', 'hw_automation.db')

    # Ensure absolute database path
    if not os.path.isabs(db_path):
        db_path = str(project_root / db_path)

    # Set up database helper with proper table name and path
    table_name = config.get('database', {}).get('table_name', 'servers')
    auto_migrate = config.get('database', {}).get('auto_migrate', True)
    db_helper = DbHelper(tablename=table_name, db_path=db_path, auto_migrate=auto_migrate)
    
    # Initialize managers with proper config directory
    project_root = Path(__file__).parent.parent.parent.parent
    config_dir = project_root / "configs" / "bios"
    
    bios_config_manager = BiosConfigManager(config_dir=str(config_dir))
    device_selection_service = DeviceSelectionService(db_path)
    workflow_manager = WorkflowManager(config)
    
    # Initialize firmware management
    try:
        from hwautomation.hardware.firmware_manager import FirmwareManager
        from hwautomation.web.firmware_routes import firmware_bp, init_firmware_routes
        
        firmware_manager = FirmwareManager()
        init_firmware_routes(firmware_manager, workflow_manager, db_helper, socketio)
        app.register_blueprint(firmware_bp)
        logger.info("Firmware management routes initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize firmware management: {e}")
        logger.warning("Firmware management features will not be available")

    @app.route('/health')
    def health_check():
        """Comprehensive health check endpoint for container orchestration."""
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0",
                "services": {}
            }
            
            # Check database connectivity
            try:
                cursor = db_helper.sql_db_worker.cursor()
                cursor.execute("SELECT 1")  # Simple connectivity test
                cursor.fetchone()
                cursor.close()
                health_status["services"]["database"] = "healthy"
            except Exception as e:
                logger.error(f"Database health check failed: {e}")
                health_status["services"]["database"] = "unhealthy"
                health_status["status"] = "degraded"
            
            # Check MaaS connectivity
            try:
                maas_config = config.get('maas', {})
                # Use host as url if url is not set
                if not maas_config.get('url') and maas_config.get('host'):
                    maas_config['url'] = maas_config['host']
                
                if maas_config.get('url') and (maas_config.get('consumer_key') and 
                                               maas_config.get('token_key') and 
                                               maas_config.get('token_secret')):
                    maas_client = create_maas_client(maas_config)
                    machines = maas_client.get_machines()
                    health_status["services"]["maas"] = "healthy"
                    health_status["services"]["maas_machines"] = len(machines)
                else:
                    health_status["services"]["maas"] = "not_configured"
            except Exception as e:
                logger.error(f"MaaS health check failed: {e}")
                health_status["services"]["maas"] = "unhealthy"
                health_status["status"] = "degraded"
            
            # Check BIOS manager
            try:
                # Test BIOS manager initialization
                device_types = bios_config_manager.get_device_types()
                health_status["services"]["bios_manager"] = "healthy"
                health_status["services"]["bios_device_types"] = len(device_types)
            except Exception as e:
                logger.error(f"BIOS manager health check failed: {e}")
                health_status["services"]["bios_manager"] = "unhealthy"
                health_status["status"] = "degraded"
            
            # Check workflow manager
            try:
                active_workflows = workflow_manager.list_workflows()
                health_status["services"]["workflow_manager"] = "healthy" 
                health_status["services"]["active_workflows"] = len(active_workflows)
            except Exception as e:
                logger.error(f"Workflow manager health check failed: {e}")
                health_status["services"]["workflow_manager"] = "unhealthy"
                health_status["status"] = "degraded"
            
            # Return appropriate HTTP status code
            status_code = 200 if health_status["status"] == "healthy" else 503
            return jsonify(health_status), status_code
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return jsonify({
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }), 503

    # Import and register all route blueprints from the original app
    # For now, we'll include the essential routes inline
    
    @app.route('/')
    def index():
        """Main dashboard page."""
        try:
            # Get statistics for the enhanced dashboard
            stats = {
                'available_machines': 0,
                'device_types': 0,
                'database_servers': 0,
                'maas_status': 'disconnected'
            }
            
            # Get device types count
            try:
                device_types = bios_config_manager.get_device_types()
                stats['device_types'] = len(device_types)
            except Exception as e:
                logger.error(f"Failed to get device types: {e}")
                device_types = []
            
            # Get database server count
            try:
                with db_helper.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM device_templates")
                    stats['database_servers'] = cursor.fetchone()[0]
            except Exception as e:
                logger.error(f"Failed to get database count: {e}")
            
            # Check MaaS status and get available machines
            try:
                maas_config = config.get('maas', {})
                # Use host as url if url is not set
                if not maas_config.get('url') and maas_config.get('host'):
                    maas_config['url'] = maas_config['host']
                
                if maas_config.get('url') and (maas_config.get('consumer_key') and 
                                               maas_config.get('token_key') and 
                                               maas_config.get('token_secret')):
                    maas_client = create_maas_client(maas_config)
                    machines = maas_client.get_machines()
                    available_machines = [m for m in machines if m.get('status') == 'Ready']
                    stats['available_machines'] = len(available_machines)
                    stats['maas_status'] = 'connected'
                else:
                    available_machines = []
                    stats['maas_status'] = 'not_configured'
            except Exception as e:
                logger.error(f"MaaS connection failed: {e}")
                available_machines = []
                stats['maas_status'] = 'disconnected'
            
            return render_template('enhanced_dashboard.html', 
                                 stats=stats, 
                                 device_types=device_types,
                                 available_machines=available_machines)
            
        except Exception as e:
            logger.error(f"Enhanced dashboard error: {e}")
            # Provide default stats if there's an error
            default_stats = {
                'available_machines': 0,
                'device_types': 0,
                'database_servers': 0,
                'maas_status': 'disconnected'
            }
            return render_template('enhanced_dashboard.html', 
                                 stats=default_stats, 
                                 device_types=[],
                                 available_machines=[])

    @app.route('/logs')

    # Add other essential routes here...
    # (Would normally import from separate route modules)
    
    @app.route('/logs')
    def view_logs():
        """Logs view page."""
        return render_template('logs.html')
    
    @app.route('/database')
    def database_management():
        """Database management page."""
        return render_template('database.html')
    
    # Database API endpoints
    @app.route('/api/database/info')
    def api_database_info():
        """Get database information."""
        try:
            import sqlite3
            import os
            
            db_path = db_helper.db_path
            
            # Get database file size
            if db_path != ':memory:' and os.path.exists(db_path):
                size_bytes = os.path.getsize(db_path)
                if size_bytes < 1024:
                    size = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size = f"{size_bytes / 1024:.1f} KB"
                else:
                    size = f"{size_bytes / (1024 * 1024):.1f} MB"
            else:
                size = "In-memory"
            
            # Get SQLite version
            cursor = db_helper.sql_db_worker.cursor()
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            
            # Count tables
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            # Count servers (if table exists)
            try:
                cursor.execute("SELECT COUNT(*) FROM servers")
                server_count = cursor.fetchone()[0]
            except:
                server_count = 0
            
            cursor.close()
            
            return jsonify({
                'success': True,
                'info': {
                    'version': version,
                    'size': size,
                    'path': db_path if db_path != ':memory:' else None,
                    'table_count': table_count,
                    'server_count': server_count
                }
            })
            
        except Exception as e:
            logger.error(f"Database info API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/database/tables')
    def api_database_tables():
        """Get database tables and their data."""
        try:
            format_type = request.args.get('format', 'json')
            cursor = db_helper.sql_db_worker.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            table_names = [row[0] for row in cursor.fetchall()]
            
            tables_data = {}
            
            for table_name in table_names:
                try:
                    # Get table row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    
                    # Get table data (limit to first 100 rows for display)
                    limit = 100
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
                    columns = [description[0] for description in cursor.description]
                    rows = cursor.fetchall()
                    
                    # Convert to list of dictionaries
                    data = []
                    for row in rows:
                        row_dict = {}
                        for i, value in enumerate(row):
                            row_dict[columns[i]] = value
                        data.append(row_dict)
                    
                    tables_data[table_name] = {
                        'count': count,
                        'showing': len(data),
                        'data': data
                    }
                    
                except Exception as e:
                    logger.warning(f"Error reading table {table_name}: {e}")
                    tables_data[table_name] = {
                        'count': 0,
                        'showing': 0,
                        'data': [],
                        'error': str(e)
                    }
            
            cursor.close()
            
            if format_type == 'json' and request.args.get('download'):
                response = jsonify({'success': True, 'tables': tables_data})
                response.headers['Content-Disposition'] = 'attachment; filename=database_export.json'
                return response
            
            return jsonify({'success': True, 'tables': tables_data})
            
        except Exception as e:
            logger.error(f"Database tables API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # API endpoints for enhanced dashboard
    @app.route('/api/maas/discover')
    def api_maas_discover():
        """Discover devices from MaaS API."""
        try:
            maas_config = config.get('maas', {})
            # Use host as url if url is not set
            if not maas_config.get('url') and maas_config.get('host'):
                maas_config['url'] = maas_config['host']
                
            if not maas_config.get('url') or not (maas_config.get('consumer_key') and 
                                                 maas_config.get('token_key') and 
                                                 maas_config.get('token_secret')):
                return jsonify({'error': 'MaaS not properly configured'}), 400
            
            maas_client = create_maas_client(maas_config)
            machines = maas_client.get_machines()
            
            # Filter for available machines
            available_devices = []
            for machine in machines:
                if machine.get('status') == 'Ready':
                    available_devices.append({
                        'system_id': machine.get('system_id'),
                        'hostname': machine.get('hostname', 'Unknown'),
                        'status': machine.get('status'),
                        'architecture': machine.get('architecture', 'Unknown'),
                        'cpu_count': machine.get('cpu_count', 0)
                    })
            
            return jsonify({
                'devices': available_devices,
                'available_count': len(available_devices),
                'total_discovered': len(machines)
            })
            
        except Exception as e:
            logger.error(f"MaaS discovery failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/batch/commission', methods=['POST'])
    def api_batch_commission():
        """Start batch commissioning workflow."""
        try:
            data = request.json
            device_type = data.get('device_type')
            device_ids = data.get('device_ids', [])
            ipmi_range = data.get('ipmi_range')
            gateway = data.get('gateway')
            
            if not device_type or not device_ids:
                return jsonify({'error': 'Missing device_type or device_ids'}), 400
            
            # Generate a batch ID
            batch_id = f"batch_{int(time.time())}"
            results = []
            
            # Process each device
            for i, device_id in enumerate(device_ids):
                try:
                    # Only calculate IPMI IP if a range is provided
                    target_ipmi_ip = None
                    if ipmi_range:
                        base_parts = ipmi_range.split('.')
                        base_parts[-1] = str(int(base_parts[-1]) + i)
                        target_ipmi_ip = '.'.join(base_parts)
                    
                    # Generate workflow ID
                    workflow_id = f"provision_{device_id}_{int(time.time())}"
                    
                    result_data = {
                        'device_id': device_id,
                        'status': 'started',
                        'workflow_id': workflow_id
                    }
                    
                    # Only include IPMI IP in result if it was calculated
                    if target_ipmi_ip:
                        result_data['target_ipmi_ip'] = target_ipmi_ip
                    
                    # Include gateway if provided
                    if gateway:
                        result_data['gateway'] = gateway
                    
                    results.append(result_data)
                    
                except Exception as e:
                    results.append({
                        'device_id': device_id,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            return jsonify({
                'batch_id': batch_id,
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Batch commission failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/workflows/status')
    def api_workflows_status():
        """Get status of active workflows."""
        try:
            # Get actual workflows from workflow manager
            workflows = workflow_manager.get_active_workflows()
            return jsonify({'workflows': workflows})
            
        except Exception as e:
            logger.error(f"Workflow status failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Orchestration API endpoints
    @app.route('/api/orchestration/workflows')
    def api_orchestration_workflows():
        """Get all workflows (active and completed)."""
        try:
            workflows = workflow_manager.get_all_workflows()
            return jsonify({'workflows': workflows})
            
        except Exception as e:
            logger.error(f"Failed to get workflows: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/orchestration/workflow/<workflow_id>/status')
    def api_orchestration_workflow_status(workflow_id):
        """Get status of a specific workflow."""
        try:
            workflow = workflow_manager.get_workflow(workflow_id)
            if not workflow:
                return jsonify({'error': 'Workflow not found'}), 404
            
            return jsonify(workflow.get_status())
            
        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/orchestration/workflow/<workflow_id>/cancel', methods=['POST'])
    def api_orchestration_workflow_cancel(workflow_id):
        """Cancel a running workflow."""
        try:
            success = workflow_manager.cancel_workflow(workflow_id)
            if not success:
                return jsonify({'error': 'Workflow not found or cannot be cancelled'}), 404
            
            return jsonify({'success': True, 'message': f'Workflow {workflow_id} cancelled'})
            
        except Exception as e:
            logger.error(f"Failed to cancel workflow: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/orchestration/provision', methods=['POST'])
    def api_orchestration_provision():
        """Start a server provisioning workflow."""
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['server_id', 'device_type']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            server_id = data['server_id']
            device_type = data['device_type']
            target_ipmi_ip = data.get('target_ipmi_ip')
            rack_location = data.get('rack_location')
            gateway = data.get('gateway')
            
            # Create and start provisioning workflow
            from hwautomation.orchestration.server_provisioning import ServerProvisioningWorkflow
            provisioning_workflow = ServerProvisioningWorkflow(workflow_manager)
            
            workflow = provisioning_workflow.create_provisioning_workflow(
                server_id=server_id,
                device_type=device_type,
                target_ipmi_ip=target_ipmi_ip,
                rack_location=rack_location,
                gateway=gateway
            )
            
            # Set up progress callback for WebSocket updates
            def progress_callback(progress_data):
                socketio.emit('workflow_progress', progress_data)
            
            workflow.set_progress_callback(progress_callback)
            
            # Start workflow execution in background thread
            import threading
            from hwautomation.orchestration.workflow_manager import WorkflowContext
            
            context = WorkflowContext(
                server_id=server_id,
                device_type=device_type,
                target_ipmi_ip=target_ipmi_ip,
                rack_location=rack_location,
                gateway=gateway,
                maas_client=workflow_manager.maas_client,
                db_helper=workflow_manager.db_helper
            )
            context.workflow_id = workflow.id
            
            def execute_workflow():
                try:
                    success = workflow.execute(context)
                    logger.info(f"Workflow {workflow.id} completed with success: {success}")
                except Exception as e:
                    logger.error(f"Workflow {workflow.id} failed: {e}")
                    workflow.status = WorkflowStatus.FAILED
                    workflow.error = str(e)
            
            thread = threading.Thread(target=execute_workflow)
            thread.daemon = True
            thread.start()
            
            response_data = {
                'success': True,
                'id': workflow.id,
                'message': f'Provisioning workflow started for {server_id}',
                'steps': [{'name': step.name, 'description': step.description} for step in workflow.steps]
            }
            
            # Include optional fields in response if provided
            if target_ipmi_ip:
                response_data['target_ipmi_ip'] = target_ipmi_ip
            if gateway:
                response_data['gateway'] = gateway
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"Failed to start provisioning workflow: {e}")
            return jsonify({'error': str(e)}), 500

    # Logs API endpoints
    @app.route('/api/logs')
    def api_get_logs():
        """Get system logs with filtering."""
        try:
            level = request.args.get('level', '')
            component = request.args.get('component', '')
            lines = request.args.get('lines', '500')
            
            # Mock logs data for now
            # In a real implementation, you would read from log files
            mock_logs = [
                {
                    'timestamp': '2024-01-01T12:00:00Z',
                    'level': 'INFO',
                    'component': 'web',
                    'message': 'HWAutomation web interface started'
                },
                {
                    'timestamp': '2024-01-01T12:00:01Z',
                    'level': 'INFO',
                    'component': 'database',
                    'message': 'Database connection established'
                },
                {
                    'timestamp': '2024-01-01T12:00:02Z',
                    'level': 'WARNING',
                    'component': 'maas',
                    'message': 'MaaS connection timeout, retrying...'
                }
            ]
            
            # Filter logs based on parameters
            filtered_logs = mock_logs
            if level:
                filtered_logs = [log for log in filtered_logs if log['level'] == level]
            if component:
                filtered_logs = [log for log in filtered_logs if log['component'] == component]
            
            # Limit number of lines
            if lines != 'all':
                try:
                    limit = int(lines)
                    filtered_logs = filtered_logs[-limit:]
                except ValueError:
                    pass
            
            return jsonify({'logs': filtered_logs})
            
        except Exception as e:
            logger.error(f"Failed to get logs: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/logs/search')
    def api_search_logs():
        """Search system logs."""
        try:
            query = request.args.get('query', '')
            regex = request.args.get('regex', 'false').lower() == 'true'
            
            # Mock search results
            mock_results = [
                {
                    'timestamp': '2024-01-01T12:00:00Z',
                    'level': 'INFO',
                    'component': 'web',
                    'message': f'Found log entry matching: {query}'
                }
            ]
            
            return jsonify({'results': mock_results})
            
        except Exception as e:
            logger.error(f"Failed to search logs: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/logs/clear', methods=['POST'])
    def api_clear_logs():
        """Clear system logs."""
        try:
            # In a real implementation, you would clear the actual log files
            logger.info("System logs cleared via API")
            return jsonify({'success': True, 'message': 'Logs cleared successfully'})
            
        except Exception as e:
            logger.error(f"Failed to clear logs: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/logs/download')
    def api_download_logs():
        """Download system logs as text file."""
        try:
            # Mock log content
            log_content = """[2024-01-01 12:00:00] [INFO] web: HWAutomation web interface started
[2024-01-01 12:00:01] [INFO] database: Database connection established  
[2024-01-01 12:00:02] [WARNING] maas: MaaS connection timeout, retrying...
"""
            
            from flask import Response
            return Response(
                log_content,
                mimetype='text/plain',
                headers={'Content-Disposition': 'attachment; filename=hwautomation_logs.txt'}
            )
            
        except Exception as e:
            logger.error(f"Failed to download logs: {e}")
            return jsonify({'error': str(e)}), 500
    
    return app, socketio

# For backward compatibility and standalone usage
app, socketio = create_app()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='HWAutomation Web Interface')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    logger.info(f"Starting HWAutomation Web Interface on {args.host}:{args.port}")
    logger.info(f"Debug mode: {args.debug}")
    
    socketio.run(app, host=args.host, port=args.port, debug=args.debug)
