"""
Phase 5 Implementation Example: API/Web Interface Modularization

This example demonstrates how to use the new modular web interface components
to create clean, maintainable API endpoints and web routes.
"""

from flask import Flask, request
from flask_socketio import SocketIO

# Import the new modular components
from hwautomation.web.core import (
    BaseResource,
    APIResponseHandler,
    ServerSerializer,
    ValidationMiddleware,
    WebSocketManagerFactory,
    create_web_core
)


class ServerResource(BaseResource):
    """
    Example server resource using the new base classes.
    
    Demonstrates:
    - RESTful API patterns
    - Database integration
    - Validation
    - Caching
    - Error handling
    """
    
    resource_name = "server"
    
    def get_single(self, server_id: str):
        """Get a single server by ID."""
        # Validate server ID format
        if not self.validate_server_id(server_id):
            return self.error_response(
                "Invalid server ID format",
                "INVALID_SERVER_ID",
                400
            )
        
        # Check cache first
        cache_key = f"server_{server_id}"
        cached_server = self.cache_get(cache_key, ttl=300)  # 5 minutes
        
        if cached_server:
            return self.success_response(
                data=cached_server,
                message=f"Server {server_id} retrieved from cache"
            )
        
        # Fetch from database
        try:
            query = "SELECT * FROM servers WHERE id = ?"
            server_data = self.execute_query(query, (server_id,), fetch_one=True)
            
            if not server_data:
                return self.error_response(
                    f"Server {server_id} not found",
                    "SERVER_NOT_FOUND",
                    404
                )
            
            # Convert tuple to dict (assuming column names)
            server_dict = {
                'id': server_data[0],
                'hostname': server_data[1],
                'ip_address': server_data[2],
                'status': server_data[3],
                'device_type': server_data[4],
                'created_at': server_data[5],
                'updated_at': server_data[6]
            }
            
            # Cache the result
            self.cache_set(cache_key, server_dict)
            
            return self.success_response(
                data=server_dict,
                message=f"Server {server_id} retrieved successfully"
            )
            
        except Exception as e:
            return self.error_response(
                "Database error occurred",
                "DATABASE_ERROR",
                500
            )

    def get_list(self):
        """Get list of servers with pagination."""
        # Get query parameters with defaults
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)  # Max 100
        status_filter = request.args.get('status')
        device_type_filter = request.args.get('device_type')
        
        # Build query with filters
        query = "SELECT * FROM servers WHERE 1=1"
        params = []
        
        if status_filter:
            query += " AND status = ?"
            params.append(status_filter)
        
        if device_type_filter:
            query += " AND device_type = ?"
            params.append(device_type_filter)
        
        # Get total count
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        total_count = self.execute_query(count_query, params, fetch_one=True)[0]
        
        # Add pagination
        query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        
        # Execute query
        try:
            servers_data = self.execute_query(query, params)
            
            # Convert to list of dicts
            servers = []
            for server_data in servers_data:
                servers.append({
                    'id': server_data[0],
                    'hostname': server_data[1],
                    'ip_address': server_data[2],
                    'status': server_data[3],
                    'device_type': server_data[4],
                    'created_at': server_data[5],
                    'updated_at': server_data[6]
                })
            
            # Create pagination info
            pagination_info = self.paginate_response(
                items=servers,
                page=page,
                per_page=per_page,
                total=total_count
            )
            
            return self.success_response(
                data=pagination_info,
                message=f"Retrieved {len(servers)} servers"
            )
            
        except Exception as e:
            return self.error_response(
                "Failed to retrieve servers",
                "DATABASE_ERROR",
                500
            )

    def create(self):
        """Create a new server."""
        # Get and validate request data
        try:
            data = self.get_request_data()
        except ValueError as e:
            return self.error_response(str(e), "INVALID_JSON", 400)
        
        # Validate required fields
        required_fields = ['hostname', 'ip_address', 'device_type']
        missing_fields = self.validate_required_fields(data, required_fields)
        
        if missing_fields:
            return self.error_response(
                f"Missing required fields: {', '.join(missing_fields)}",
                "MISSING_FIELDS",
                400,
                validation_errors=missing_fields
            )
        
        # Validate field types
        field_types = {
            'hostname': str,
            'ip_address': str,
            'device_type': str
        }
        type_errors = self.validate_field_types(data, field_types)
        
        if type_errors:
            return self.error_response(
                "Invalid field types",
                "INVALID_FIELD_TYPES",
                400,
                validation_errors=type_errors
            )
        
        # Validate IP address format
        if not self.validate_ip_address(data['ip_address']):
            return self.error_response(
                "Invalid IP address format",
                "INVALID_IP_ADDRESS",
                400
            )
        
        # Validate device type format
        if not self.validate_device_type(data['device_type']):
            return self.error_response(
                "Invalid device type format",
                "INVALID_DEVICE_TYPE",
                400
            )
        
        # Insert into database
        try:
            current_time = self.current_timestamp()
            server_id = f"srv-{int(current_time)}"
            
            query = """
                INSERT INTO servers (id, hostname, ip_address, status, device_type, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                server_id,
                data['hostname'],
                data['ip_address'],
                'pending',
                data['device_type'],
                current_time,
                current_time
            )
            
            self.execute_query(query, params, fetch_all=False)
            
            # Return created server
            server_dict = {
                'id': server_id,
                'hostname': data['hostname'],
                'ip_address': data['ip_address'],
                'status': 'pending',
                'device_type': data['device_type'],
                'created_at': current_time,
                'updated_at': current_time
            }
            
            return self.success_response(
                data=server_dict,
                message=f"Server {server_id} created successfully",
                status_code=201
            )
            
        except Exception as e:
            return self.error_response(
                "Failed to create server",
                "DATABASE_ERROR",
                500
            )

    def update(self, server_id: str):
        """Update an existing server."""
        # Validate server exists
        if not self.validate_resource_exists(server_id):
            return self.error_response(
                f"Server {server_id} not found",
                "SERVER_NOT_FOUND",
                404
            )
        
        try:
            data = self.get_request_data()
        except ValueError as e:
            return self.error_response(str(e), "INVALID_JSON", 400)
        
        # Build update query dynamically
        update_fields = []
        params = []
        
        allowed_fields = ['hostname', 'ip_address', 'status', 'device_type']
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                params.append(data[field])
        
        if not update_fields:
            return self.error_response(
                "No valid fields to update",
                "NO_UPDATE_FIELDS",
                400
            )
        
        # Add updated timestamp
        update_fields.append("updated_at = ?")
        params.append(self.current_timestamp())
        params.append(server_id)
        
        try:
            query = f"UPDATE servers SET {', '.join(update_fields)} WHERE id = ?"
            self.execute_query(query, params, fetch_all=False)
            
            # Clear cache
            self.cache_delete(f"server_{server_id}")
            
            return self.success_response(
                message=f"Server {server_id} updated successfully"
            )
            
        except Exception as e:
            return self.error_response(
                "Failed to update server",
                "DATABASE_ERROR",
                500
            )

    def delete_resource(self, server_id: str):
        """Delete a server."""
        # Validate server exists
        if not self.validate_resource_exists(server_id):
            return self.error_response(
                f"Server {server_id} not found",
                "SERVER_NOT_FOUND",
                404
            )
        
        try:
            query = "DELETE FROM servers WHERE id = ?"
            self.execute_query(query, (server_id,), fetch_all=False)
            
            # Clear cache
            self.cache_delete(f"server_{server_id}")
            
            return self.success_response(
                message=f"Server {server_id} deleted successfully",
                status_code=204
            )
            
        except Exception as e:
            return self.error_response(
                "Failed to delete server",
                "DATABASE_ERROR",
                500
            )


class EnhancedServerAPI:
    """
    Example API using response handlers and serializers.
    
    Demonstrates:
    - Response handler usage
    - Serialization
    - Middleware integration
    - WebSocket notifications
    """
    
    def __init__(self, app, socketio=None):
        self.app = app
        self.response_handler = APIResponseHandler()
        self.server_serializer = ServerSerializer()
        self.websocket_factory = None
        
        if socketio:
            self.websocket_factory = WebSocketManagerFactory(socketio)
            self.server_status_manager = self.websocket_factory.create_manager('server_status')

    @ValidationMiddleware.validate_json_request(['hostname', 'ip_address'])
    def create_server_enhanced(self, json_data):
        """Enhanced server creation with serialization and WebSocket notifications."""
        try:
            # Create server (simplified for example)
            server_data = {
                'id': f"srv-{int(time.time())}",
                'hostname': json_data['hostname'],
                'ip_address': json_data['ip_address'],
                'status': 'pending',
                'created_at': time.time()
            }
            
            # Serialize response data
            serialized_data = self.server_serializer.serialize(server_data)
            
            # Send WebSocket notification
            if self.server_status_manager:
                self.server_status_manager.broadcast_server_status(
                    server_data['id'],
                    {'status': 'created', 'hostname': server_data['hostname']}
                )
            
            return self.response_handler.created(
                data=serialized_data,
                message="Server created successfully",
                location=f"/api/servers/{server_data['id']}"
            )
            
        except Exception as e:
            return self.response_handler.internal_error(
                "Failed to create server"
            )

    def get_server_status_stream(self, server_id):
        """Stream server status updates."""
        def status_generator():
            import time
            import random
            
            for i in range(10):  # Simulate 10 status updates
                yield {
                    'server_id': server_id,
                    'status': 'running',
                    'cpu_usage': random.uniform(20, 80),
                    'memory_usage': random.uniform(30, 90),
                    'timestamp': time.time()
                }
                time.sleep(2)  # Wait 2 seconds between updates
        
        from hwautomation.web.core import StreamingResponseHandler
        return StreamingResponseHandler.create_sse_response(status_generator)


def create_example_app():
    """Create example Flask app with Phase 5 components."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'development-key'
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Initialize web core components
    components = create_web_core(app=app, socketio=socketio)
    
    # Create resource instance
    server_resource = ServerResource()
    enhanced_api = EnhancedServerAPI(app, socketio)
    
    # Register routes
    @app.route('/api/servers', methods=['GET'])
    def list_servers():
        return server_resource.get_list()
    
    @app.route('/api/servers', methods=['POST'])
    def create_server():
        return enhanced_api.create_server_enhanced()
    
    @app.route('/api/servers/<server_id>', methods=['GET'])
    def get_server(server_id):
        return server_resource.get_single(server_id)
    
    @app.route('/api/servers/<server_id>', methods=['PUT'])
    def update_server(server_id):
        return server_resource.update(server_id)
    
    @app.route('/api/servers/<server_id>', methods=['DELETE'])
    def delete_server(server_id):
        return server_resource.delete_resource(server_id)
    
    @app.route('/api/servers/<server_id>/status-stream')
    def server_status_stream(server_id):
        return enhanced_api.get_server_status_stream(server_id)
    
    # Example web route using template helpers
    @app.route('/')
    def index():
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>HWAutomation Phase 5 Example</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .status-online { color: green; }
                .status-offline { color: red; }
                .api-example { background: #f5f5f5; padding: 20px; margin: 20px 0; }
                pre { background: #000; color: #0f0; padding: 10px; overflow-x: auto; }
            </style>
        </head>
        <body>
            <h1>HWAutomation Phase 5: API/Web Interface Modularization</h1>
            
            <h2>Features Implemented</h2>
            <ul>
                <li><strong>Modular Base Classes:</strong> BaseResource, DatabaseMixin, ValidationMixin</li>
                <li><strong>Middleware Components:</strong> Request processing, validation, authentication</li>
                <li><strong>Response Handlers:</strong> Standardized API responses, streaming, CORS</li>
                <li><strong>Serializers:</strong> Data formatting for servers, workflows, devices</li>
                <li><strong>WebSocket Managers:</strong> Real-time updates, room management</li>
                <li><strong>Template Helpers:</strong> Date formatting, pagination, navigation</li>
            </ul>
            
            <h2>API Examples</h2>
            
            <div class="api-example">
                <h3>Get All Servers</h3>
                <pre>GET /api/servers?page=1&per_page=20&status=online</pre>
                <p>Features: Pagination, filtering, caching, validation</p>
            </div>
            
            <div class="api-example">
                <h3>Create Server</h3>
                <pre>POST /api/servers
Content-Type: application/json

{
    "hostname": "server01.example.com",
    "ip_address": "192.168.1.100",
    "device_type": "a1.c4.large"
}</pre>
                <p>Features: JSON validation, error handling, WebSocket notifications</p>
            </div>
            
            <div class="api-example">
                <h3>Stream Server Status</h3>
                <pre>GET /api/servers/srv-123/status-stream
Accept: text/event-stream</pre>
                <p>Features: Server-sent events, real-time monitoring</p>
            </div>
            
            <h2>WebSocket Example</h2>
            <div class="api-example">
                <pre>// Connect to WebSocket
const socket = io();

// Subscribe to server status updates
socket.emit('subscribe_server_status', {server_id: 'srv-123'});

// Listen for updates
socket.on('server_status_update', (data) => {
    console.log('Server status:', data);
});</pre>
            </div>
            
            <h2>Architecture Benefits</h2>
            <ul>
                <li><strong>Modularity:</strong> Reusable components across different endpoints</li>
                <li><strong>Consistency:</strong> Standardized responses, error handling, validation</li>
                <li><strong>Maintainability:</strong> Clear separation of concerns, easy testing</li>
                <li><strong>Extensibility:</strong> Easy to add new resources and features</li>
                <li><strong>Performance:</strong> Built-in caching, efficient serialization</li>
                <li><strong>Real-time:</strong> WebSocket support for live updates</li>
            </ul>
            
            <h2>Integration with Existing System</h2>
            <p>All Phase 5 components are designed to integrate seamlessly with existing HWAutomation infrastructure:</p>
            <ul>
                <li>Uses existing database layer (DbHelper)</li>
                <li>Integrates with Phase 4 logging system</li>
                <li>Maintains backward compatibility</li>
                <li>Enhances existing Flask routes</li>
            </ul>
        </body>
        </html>
        '''
    
    return app, socketio, components


if __name__ == '__main__':
    app, socketio, components = create_example_app()
    print("Phase 5 Example Server Starting...")
    print("Available endpoints:")
    print("  - GET  /api/servers")
    print("  - POST /api/servers") 
    print("  - GET  /api/servers/<id>")
    print("  - PUT  /api/servers/<id>")
    print("  - DELETE /api/servers/<id>")
    print("  - GET  /api/servers/<id>/status-stream")
    print("  - GET  / (Web interface)")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
