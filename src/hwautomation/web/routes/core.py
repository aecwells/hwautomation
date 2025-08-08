#!/usr/bin/env python3
"""
Core routes for HWAutomation Web Interface

Handles main dashboard, health checks, and core application routes.
"""

import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify

logger = logging.getLogger(__name__)

# Create blueprint for core routes
core_bp = Blueprint('core', __name__)

def init_core_routes(app, db_helper, maas_client, config):
    """Initialize core routes with dependencies."""
    
    @core_bp.route('/health')
    def health_check():
        """Health check endpoint for load balancers."""
        return jsonify({
            'status': 'healthy',
            'service': 'hwautomation-web',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @core_bp.route('/')
    def dashboard():
        """Main dashboard with device overview and quick actions."""
        try:
            # Get dashboard statistics
            stats = {
                'available_machines': 0,
                'device_types': 0,
                'database_servers': 0,
                'ready_servers': 0
            }
            
            # Get server count from database if available
            try:
                cursor = db_helper.sql_db_worker.cursor()
                cursor.execute("SELECT COUNT(*) FROM servers")
                stats['database_servers'] = cursor.fetchone()[0]
                
                # Count ready servers
                cursor.execute("SELECT COUNT(*) FROM servers WHERE status_name = 'Ready'")
                stats['ready_servers'] = cursor.fetchone()[0]
                cursor.close()
            except Exception as e:
                logger.warning(f"Could not get database stats: {e}")
            
            # Get MaaS machines count if configured
            try:
                maas_config = config.get('maas', {})
                if maas_config.get('url') and maas_config.get('consumer_key'):
                    from hwautomation.maas.client import create_maas_client
                    maas_client_instance = create_maas_client(maas_config)
                    machines = maas_client_instance.get_machines()
                    stats['available_machines'] = len([m for m in machines if m.get('status') == 'Ready'])
            except Exception as e:
                logger.warning(f"Could not get MaaS stats: {e}")
            
            # Get available device types
            device_types = ['a1.c5.large', 'd1.c1.small', 'd1.c2.medium', 'd1.c2.large']
            stats['device_types'] = len(device_types)
            
            return render_template('dashboard.html',
                                 stats=stats,
                                 device_types=device_types)
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
            return render_template('dashboard.html', error=str(e))
