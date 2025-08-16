# Phase 5 User Manual: API/Web Interface Modularization

## Overview

Phase 5 introduces a comprehensive modularization of the HWAutomation web interface, providing reusable components for building clean, maintainable API endpoints and web routes. This modularization enhances code organization, reduces duplication, and improves overall system architecture.

## Architecture

The Phase 5 modularization consists of six main component categories:

1. **Base Classes**: Foundation classes for API views and resources
2. **Middleware**: Request/response processing components
3. **Response Handlers**: Standardized response formatting
4. **Serializers**: Data formatting and transformation
5. **WebSocket Managers**: Real-time communication components
6. **Template Helpers**: Utilities for web interface rendering

## Component Reference

### 1. Base Classes (`base_classes.py`)

#### BaseAPIView
Foundation class for all API views with common functionality.

```python
from hwautomation.web.core import BaseAPIView

class MyAPIView(BaseAPIView):
    def get(self):
        return self.success_response({"message": "Hello World"})
```

**Features:**
- Standard response formatting
- Error handling
- Request logging
- Performance tracking

#### BaseResourceView
RESTful resource base class with CRUD operations.

```python
from hwautomation.web.core import BaseResource

class ServerResource(BaseResource):
    resource_name = "server"

    def get_single(self, resource_id):
        # Implement single resource retrieval
        pass

    def get_list(self):
        # Implement resource listing with pagination
        pass

    def create(self):
        # Implement resource creation
        pass
```

#### Mixins
Reusable functionality mixins:

- **DatabaseMixin**: Database operations and connection management
- **ValidationMixin**: Common validation patterns
- **CacheMixin**: Memory caching functionality
- **TimestampMixin**: Timestamp utilities

### 2. Middleware (`middleware.py`)

#### RequestMiddleware
Centralized request processing with correlation tracking.

```python
from hwautomation.web.core import RequestMiddleware

# Initialize with Flask app
middleware = RequestMiddleware(app)
```

**Features:**
- Correlation ID tracking
- Request timing
- Rate limiting
- Request logging

#### ValidationMiddleware
Request validation with decorators.

```python
from hwautomation.web.core import ValidationMiddleware

@ValidationMiddleware.validate_json_request(['hostname', 'ip_address'])
def create_server(json_data):
    # json_data is validated and available
    pass

@ValidationMiddleware.validate_query_params(
    required_params=['page'],
    optional_params={'per_page': 20, 'status': 'all'}
)
def list_servers(query_params):
    # query_params contains validated parameters
    pass
```

#### AuthenticationMiddleware
API authentication and authorization.

```python
from hwautomation.web.core import AuthenticationMiddleware

auth = AuthenticationMiddleware(app)

@auth.require_authentication(roles=['admin'])
def admin_endpoint(current_user):
    # current_user contains authenticated user info
    pass
```

### 3. Response Handlers (`response_handlers.py`)

#### APIResponseHandler
Standardized API response formatting.

```python
from hwautomation.web.core import APIResponseHandler

handler = APIResponseHandler()

# Success response
return handler.success(
    data={"server_id": "srv-123"},
    message="Server created successfully"
)

# Error response
return handler.error(
    message="Server not found",
    error_code="SERVER_NOT_FOUND",
    status_code=404
)

# Paginated response
return handler.paginated(
    items=servers,
    pagination_info={
        'page': 1,
        'per_page': 20,
        'total': 100,
        'total_pages': 5
    }
)
```

#### StreamingResponseHandler
Real-time data streaming.

```python
from hwautomation.web.core import StreamingResponseHandler

def progress_task():
    for i in range(100):
        yield {
            "progress": i,
            "message": f"Processing step {i}"
        }

# Create streaming response
return StreamingResponseHandler.create_progress_stream(progress_task)
```

### 4. Serializers (`serializers.py`)

#### ServerSerializer
Specialized server data formatting.

```python
from hwautomation.web.core import ServerSerializer

serializer = ServerSerializer(fields=['id', 'hostname', 'status'])
formatted_data = serializer.serialize(server_data)
```

#### WorkflowSerializer
Workflow progress and status formatting.

```python
from hwautomation.web.core import WorkflowSerializer

workflow_serializer = WorkflowSerializer()
formatted_workflow = workflow_serializer.serialize(workflow_data)
```

#### Custom Serializers
Create custom serializers for specific data types.

```python
from hwautomation.web.core import BaseSerializer

class CustomSerializer(BaseSerializer):
    def serialize_item(self, item):
        data = super().serialize_item(item)
        # Add custom formatting
        data['custom_field'] = self.format_custom_data(item)
        return data
```

### 5. WebSocket Managers (`websocket_managers.py`)

#### WebSocketManagerFactory
Centralized WebSocket manager creation.

```python
from flask_socketio import SocketIO
from hwautomation.web.core import WebSocketManagerFactory

socketio = SocketIO(app)
ws_factory = WebSocketManagerFactory(socketio)

# Initialize all managers
managers = ws_factory.initialize_all()
```

#### ServerStatusManager
Real-time server status updates.

```python
# Get manager
server_manager = ws_factory.get_manager('server_status')

# Broadcast server status
server_manager.broadcast_server_status('srv-123', {
    'status': 'online',
    'cpu_usage': 45.2,
    'memory_usage': 68.1
})

# Client-side JavaScript
socket.emit('subscribe_server_status', {server_id: 'srv-123'});
socket.on('server_status_update', (data) => {
    updateServerDisplay(data);
});
```

#### WorkflowManager
Workflow progress tracking.

```python
workflow_manager = ws_factory.get_manager('workflow')

# Broadcast progress update
workflow_manager.broadcast_workflow_progress('wf-456', {
    'progress': 75,
    'current_step': 'Installing BIOS configuration',
    'message': 'Configuration in progress...'
})
```

### 6. Template Helpers (`template_helpers.py`)

#### Registration
Register all helpers with Flask app.

```python
from hwautomation.web.core import register_all_helpers

register_all_helpers(app)
```

#### Template Filters
Use in Jinja2 templates.

```html
<!-- Format timestamps -->
<span>{{ server.created_at | format_timestamp('human') }}</span>
<span>{{ server.updated_at | format_timestamp('relative') }}</span>

<!-- Format file sizes -->
<span>{{ disk_usage | format_bytes }}</span>

<!-- Status badges -->
<span>{{ server.status | status_badge }}</span>

<!-- Duration formatting -->
<span>{{ workflow.duration | format_duration }}</span>
```

#### Global Functions
Available in all templates.

```html
<!-- Build URLs with parameters -->
<a href="{{ build_url('servers.list', page=2, status='online') }}">Next Page</a>

<!-- Navigation helpers -->
{% for item in NavigationHelper.get_navigation_menu() %}
    <li class="{{ 'active' if item.active }}">
        <a href="{{ url_for(item.endpoint) }}">{{ item.title }}</a>
    </li>
{% endfor %}

<!-- Pagination -->
{% set pagination = PaginationHelper(current_page, total_pages, per_page, total_items) %}
{% for page_num in pagination.get_page_numbers() %}
    <a href="{{ build_url('servers.list', page=page_num) }}">{{ page_num }}</a>
{% endfor %}
```

## Integration Guide

### Step 1: Initialize Core Components

```python
from flask import Flask
from flask_socketio import SocketIO
from hwautomation.web.core import create_web_core

app = Flask(__name__)
socketio = SocketIO(app)

# Initialize all components
components = create_web_core(app=app, socketio=socketio)
```

### Step 2: Create Resource Classes

```python
from hwautomation.web.core import BaseResource

class ServerResource(BaseResource):
    resource_name = "server"

    def get_single(self, server_id):
        # Use built-in database and caching mixins
        cache_key = f"server_{server_id}"
        cached_data = self.cache_get(cache_key)

        if cached_data:
            return self.success_response(data=cached_data)

        # Fetch from database
        query = "SELECT * FROM servers WHERE id = ?"
        server_data = self.execute_query(query, (server_id,), fetch_one=True)

        if not server_data:
            return self.error_response("Server not found", "NOT_FOUND", 404)

        # Cache and return
        self.cache_set(cache_key, server_data)
        return self.success_response(data=server_data)
```

### Step 3: Register Routes

```python
server_resource = ServerResource()

@app.route('/api/servers/<server_id>')
def get_server(server_id):
    return server_resource.get_single(server_id)

@app.route('/api/servers', methods=['POST'])
@ValidationMiddleware.validate_json_request(['hostname', 'ip_address'])
def create_server(json_data):
    return server_resource.create()
```

### Step 4: Add Real-time Features

```python
# Get WebSocket manager
server_manager = components['websocket_managers']['server_status']

# In your server creation logic
def create_server_with_notifications(server_data):
    # Create server in database
    server_id = create_server_in_db(server_data)

    # Notify WebSocket clients
    server_manager.broadcast_server_status(server_id, {
        'status': 'created',
        'hostname': server_data['hostname']
    })

    return server_id
```

## Best Practices

### 1. Resource Organization

- Use `BaseResource` for RESTful endpoints
- Implement all CRUD methods consistently
- Use mixins for common functionality
- Keep resources focused on single entities

### 2. Validation

- Use middleware decorators for request validation
- Validate at the API boundary
- Provide clear error messages
- Use consistent error codes

### 3. Response Formatting

- Use response handlers for consistent formatting
- Include appropriate HTTP status codes
- Provide correlation IDs for tracking
- Use serializers for data transformation

### 4. Real-time Features

- Use WebSocket managers for live updates
- Organize clients into logical rooms
- Handle connection/disconnection gracefully
- Provide fallback for non-WebSocket clients

### 5. Template Development

- Register all helpers during app initialization
- Use filters for data formatting
- Use globals for utility functions
- Keep template logic minimal

## Migration from Existing Code

### Converting Existing Routes

**Before (traditional Flask route):**
```python
@app.route('/api/servers/<server_id>')
def get_server(server_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM servers WHERE id = ?", (server_id,))
        server = cursor.fetchone()

        if not server:
            return jsonify({"error": "Server not found"}), 404

        return jsonify({"data": server})

    except Exception as e:
        return jsonify({"error": "Database error"}), 500
    finally:
        conn.close()
```

**After (using Phase 5 components):**
```python
class ServerResource(BaseResource):
    def get_single(self, server_id):
        query = "SELECT * FROM servers WHERE id = ?"
        server_data = self.execute_query(query, (server_id,), fetch_one=True)

        if not server_data:
            return self.error_response("Server not found", "NOT_FOUND", 404)

        return self.success_response(data=server_data)

server_resource = ServerResource()

@app.route('/api/servers/<server_id>')
def get_server(server_id):
    return server_resource.get_single(server_id)
```

## Performance Considerations

### Caching Strategy

```python
# Built-in cache with TTL
cache_key = f"servers_page_{page}"
cached_result = self.cache_get(cache_key, ttl=300)  # 5 minutes

if not cached_result:
    result = expensive_database_query()
    self.cache_set(cache_key, result)
    return result

return cached_result
```

### Database Optimization

```python
# Use connection context managers
def get_servers_optimized(self):
    def _query(conn):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM servers ORDER BY updated_at DESC LIMIT 100")
        return cursor.fetchall()

    return self.with_connection(_query)
```

### WebSocket Resource Management

```python
# Monitor connection counts
stats = websocket_manager.get_connection_stats()
if stats['total_connections'] > 1000:
    # Implement connection throttling
    pass
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure Phase 5 components are properly installed
2. **Database Connection Issues**: Verify DbHelper configuration
3. **WebSocket Connection Problems**: Check CORS settings and port configuration
4. **Template Rendering Errors**: Verify all helpers are registered

### Debug Mode

```python
# Enable debug logging for Phase 5 components
import logging
logging.getLogger('hwautomation.web.core').setLevel(logging.DEBUG)
```

### Testing

```python
# Test resource endpoints
def test_server_resource():
    resource = ServerResource()
    response = resource.get_single('test-server-id')
    assert response[1] == 200  # HTTP status code
```

## Conclusion

Phase 5 modularization provides a solid foundation for building maintainable, scalable web interfaces. The modular architecture promotes code reuse, consistency, and easier testing while maintaining full backward compatibility with existing HWAutomation components.

For additional examples and advanced usage patterns, see the `examples/phase5_api_web_modularization_example.py` file.
