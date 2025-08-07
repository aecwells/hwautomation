#!/usr/bin/env python3
"""
Firmware Management Routes for HWAutomation Web Interface

Provides web endpoints for firmware inventory, scheduling, and monitoring.
Integrates with FirmwareManager and FirmwareProvisioningWorkflow.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_socketio import emit
from pathlib import Path
import threading

logger = logging.getLogger(__name__)

# Create blueprint for firmware routes
firmware_bp = Blueprint('firmware', __name__, url_prefix='/firmware')

class FirmwareWebManager:
    """Manages firmware operations for web interface."""
    
    def __init__(self, firmware_manager, workflow_manager, db_helper, socketio=None):
        """Initialize firmware web manager.
        
        Args:
            firmware_manager: FirmwareManager instance
            workflow_manager: WorkflowManager instance
            db_helper: Database helper instance
            socketio: SocketIO instance for real-time updates
        """
        self.firmware_manager = firmware_manager
        self.workflow_manager = workflow_manager
        self.db_helper = db_helper
        self.socketio = socketio
        self._active_updates = {}  # Track active firmware updates
        
    def get_firmware_inventory(self) -> Dict[str, Any]:
        """Get comprehensive firmware inventory across all servers.
        
        Returns:
            Dict containing firmware status, versions, and update availability
        """
        try:
            inventory = {
                'servers': [],
                'update_summary': {
                    'total_servers': 0,
                    'updates_available': 0,
                    'up_to_date': 0,
                    'unknown_status': 0
                },
                'firmware_repository': {
                    'total_files': 0,
                    'vendors': [],
                    'latest_versions': {}
                }
            }
            
            # Get all servers from database
            with self.db_helper.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, hostname, status_name, device_type, ipmi_ip 
                    FROM servers 
                    WHERE status_name != 'Deleted'
                    ORDER BY id
                """)
                servers = cursor.fetchall()
                
            inventory['update_summary']['total_servers'] = len(servers)
            
            # Check firmware status for each server
            for server in servers:
                server_id, hostname, status, device_type, ipmi_ip = server
                
                server_info = {
                    'id': server_id,
                    'hostname': hostname or f'Server-{server_id}',
                    'status': status,
                    'device_type': device_type,
                    'ipmi_ip': ipmi_ip,
                    'firmware_status': 'unknown',
                    'bios_version': 'Unknown',
                    'bmc_version': 'Unknown',
                    'updates_available': False,
                    'last_checked': None
                }
                
                # Try to get current firmware versions if server is accessible
                if ipmi_ip and status in ['Ready', 'Deployed']:
                    try:
                        # This would integrate with actual firmware detection
                        # For now, simulate firmware version detection
                        server_info['firmware_status'] = 'detected'
                        server_info['bios_version'] = 'Simulated-v1.0'
                        server_info['bmc_version'] = 'Simulated-BMC-v2.0'
                        server_info['last_checked'] = datetime.now().isoformat()
                        
                        # Check for available updates
                        available_updates = self._check_available_updates(device_type)
                        if available_updates:
                            server_info['updates_available'] = True
                            server_info['available_updates'] = available_updates
                            inventory['update_summary']['updates_available'] += 1
                        else:
                            inventory['update_summary']['up_to_date'] += 1
                            
                    except Exception as e:
                        logger.warning(f"Failed to check firmware for server {server_id}: {e}")
                        inventory['update_summary']['unknown_status'] += 1
                else:
                    inventory['update_summary']['unknown_status'] += 1
                    
                inventory['servers'].append(server_info)
            
            # Get firmware repository information
            try:
                firmware_files = self.firmware_manager.discover_firmware_files('.')
                inventory['firmware_repository']['total_files'] = len(firmware_files)
                
                # Group by vendor
                vendors = set()
                for file_info in firmware_files:
                    if 'vendor' in file_info:
                        vendors.add(file_info['vendor'])
                
                inventory['firmware_repository']['vendors'] = list(vendors)
                
            except Exception as e:
                logger.warning(f"Failed to get firmware repository info: {e}")
            
            return inventory
            
        except Exception as e:
            logger.error(f"Failed to get firmware inventory: {e}")
            return {
                'servers': [],
                'update_summary': {'total_servers': 0, 'updates_available': 0, 'up_to_date': 0, 'unknown_status': 0},
                'firmware_repository': {'total_files': 0, 'vendors': [], 'latest_versions': {}}
            }
    
    def _check_available_updates(self, device_type: str) -> List[Dict]:
        """Check for available firmware updates for device type.
        
        Args:
            device_type: Device type to check updates for
            
        Returns:
            List of available updates
        """
        try:
            # This would integrate with actual firmware version comparison
            # For now, simulate available updates
            if device_type and 'large' in device_type:
                return [
                    {
                        'component': 'BIOS',
                        'current': 'v1.0',
                        'available': 'v1.2',
                        'priority': 'recommended'
                    },
                    {
                        'component': 'BMC',
                        'current': 'v2.0',
                        'available': 'v2.1',
                        'priority': 'optional'
                    }
                ]
            return []
            
        except Exception as e:
            logger.warning(f"Failed to check updates for {device_type}: {e}")
            return []
    
    def schedule_firmware_update(self, server_ids: List[str], update_config: Dict) -> Dict[str, Any]:
        """Schedule firmware updates for specified servers.
        
        Args:
            server_ids: List of server IDs to update
            update_config: Update configuration (components, scheduling, etc.)
            
        Returns:
            Dict with scheduling results
        """
        try:
            scheduled_updates = []
            failed_schedules = []
            
            for server_id in server_ids:
                try:
                    # Create firmware update workflow
                    workflow_data = {
                        'server_id': server_id,
                        'firmware_components': update_config.get('components', ['bios', 'bmc']),
                        'scheduled_time': update_config.get('scheduled_time'),
                        'maintenance_window': update_config.get('maintenance_window', 60),
                        'rollback_enabled': update_config.get('rollback_enabled', True)
                    }
                    
                    # For now, simulate workflow creation
                    # This would integrate with actual FirmwareProvisioningWorkflow
                    workflow_id = f"fw-update-{server_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    
                    scheduled_updates.append({
                        'server_id': server_id,
                        'workflow_id': workflow_id,
                        'scheduled_time': update_config.get('scheduled_time'),
                        'status': 'scheduled'
                    })
                    
                    logger.info(f"Scheduled firmware update for server {server_id}: {workflow_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to schedule firmware update for server {server_id}: {e}")
                    failed_schedules.append({
                        'server_id': server_id,
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'scheduled_updates': scheduled_updates,
                'failed_schedules': failed_schedules,
                'total_scheduled': len(scheduled_updates)
            }
            
        except Exception as e:
            logger.error(f"Failed to schedule firmware updates: {e}")
            return {
                'success': False,
                'error': str(e),
                'scheduled_updates': [],
                'failed_schedules': []
            }
    
    def get_update_progress(self, workflow_id: str) -> Dict[str, Any]:
        """Get real-time progress for firmware update workflow.
        
        Args:
            workflow_id: Workflow ID to check progress for
            
        Returns:
            Dict with current progress information
        """
        try:
            # This would integrate with actual workflow progress tracking
            # For now, simulate progress data
            if workflow_id in self._active_updates:
                progress = self._active_updates[workflow_id]
            else:
                # Simulate initial progress
                progress = {
                    'workflow_id': workflow_id,
                    'status': 'running',
                    'current_phase': 'firmware_analysis',
                    'progress_percentage': 25,
                    'steps_completed': 2,
                    'total_steps': 8,
                    'current_step': 'Analyzing current firmware versions',
                    'estimated_remaining': '15 minutes',
                    'started_at': datetime.now().isoformat(),
                    'phases': {
                        'hardware_discovery': {'status': 'completed', 'duration': 120},
                        'firmware_analysis': {'status': 'running', 'duration': None},
                        'bios_configuration': {'status': 'pending', 'duration': None},
                        'firmware_updates': {'status': 'pending', 'duration': None},
                        'validation': {'status': 'pending', 'duration': None},
                        'documentation': {'status': 'pending', 'duration': None}
                    }
                }
                self._active_updates[workflow_id] = progress
            
            return progress
            
        except Exception as e:
            logger.error(f"Failed to get update progress for {workflow_id}: {e}")
            return {
                'workflow_id': workflow_id,
                'status': 'error',
                'error': str(e)
            }

# Global firmware web manager instance
firmware_web_manager = None

def init_firmware_routes(firmware_manager, workflow_manager, db_helper, socketio=None):
    """Initialize firmware routes with dependencies.
    
    Args:
        firmware_manager: FirmwareManager instance
        workflow_manager: WorkflowManager instance  
        db_helper: Database helper instance
        socketio: SocketIO instance for real-time updates
    """
    global firmware_web_manager
    firmware_web_manager = FirmwareWebManager(
        firmware_manager, workflow_manager, db_helper, socketio
    )

@firmware_bp.route('/dashboard')
def firmware_dashboard():
    """Firmware management dashboard."""
    try:
        if not firmware_web_manager:
            flash('Firmware management not initialized', 'error')
            return redirect(url_for('index'))
        
        inventory = firmware_web_manager.get_firmware_inventory()
        
        return render_template('firmware/dashboard.html',
                             title='Firmware Management',
                             inventory=inventory)
                             
    except Exception as e:
        logger.error(f"Error loading firmware dashboard: {e}")
        flash(f'Error loading firmware dashboard: {e}', 'error')
        return redirect(url_for('index'))

# API Endpoints

@firmware_bp.route('/api/inventory')
def api_firmware_inventory():
    """API endpoint for firmware inventory data."""
    try:
        if not firmware_web_manager:
            return jsonify({'error': 'Firmware management not initialized'}), 500
        
        inventory = firmware_web_manager.get_firmware_inventory()
        return jsonify(inventory)
        
    except Exception as e:
        logger.error(f"API error getting firmware inventory: {e}")
        return jsonify({'error': str(e)}), 500

@firmware_bp.route('/api/schedule', methods=['POST'])
def api_schedule_firmware_update():
    """API endpoint to schedule firmware updates."""
    try:
        if not firmware_web_manager:
            return jsonify({'error': 'Firmware management not initialized'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        server_ids = data.get('server_ids', [])
        if not server_ids:
            return jsonify({'error': 'No servers specified'}), 400
        
        update_config = {
            'components': data.get('components', ['bios', 'bmc']),
            'scheduled_time': data.get('scheduled_time'),
            'maintenance_window': data.get('maintenance_window', 60),
            'rollback_enabled': data.get('rollback_enabled', True)
        }
        
        result = firmware_web_manager.schedule_firmware_update(server_ids, update_config)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"API error scheduling firmware update: {e}")
        return jsonify({'error': str(e)}), 500

@firmware_bp.route('/api/progress/<workflow_id>')
def api_firmware_update_progress(workflow_id):
    """API endpoint to get firmware update progress."""
    try:
        if not firmware_web_manager:
            return jsonify({'error': 'Firmware management not initialized'}), 500
        
        progress = firmware_web_manager.get_update_progress(workflow_id)
        return jsonify(progress)
        
    except Exception as e:
        logger.error(f"API error getting firmware update progress: {e}")
        return jsonify({'error': str(e)}), 500

@firmware_bp.route('/api/cancel/<workflow_id>', methods=['POST'])
def api_cancel_firmware_update(workflow_id):
    """API endpoint to cancel firmware update."""
    try:
        if not firmware_web_manager:
            return jsonify({'error': 'Firmware management not initialized'}), 500
        
        # This would integrate with actual workflow cancellation
        # For now, simulate cancellation
        result = {
            'success': True,
            'workflow_id': workflow_id,
            'status': 'cancelled',
            'message': 'Firmware update cancelled successfully'
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"API error cancelling firmware update: {e}")
        return jsonify({'error': str(e)}), 500
