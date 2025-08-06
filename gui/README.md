# HWAutomation Web GUI

A modern web-based interface for managing BIOS configurations and hardware automation tasks.

## Features

🖥️ **Web-Based Interface** - Access from any device with a web browser  
⚡ **Real-Time Updates** - WebSocket integration for live progress updates  
🔧 **BIOS Management** - Smart pull-edit-push configuration approach  
📊 **Dashboard** - Overview of system status and quick actions  
🔍 **Advanced Filtering** - Search and filter configurations and logs  
📱 **Responsive Design** - Works on desktop, tablet, and mobile devices  

## Quick Start

### 1. Prerequisites

- Python 3.8 or higher
- Core HWAutomation dependencies installed:
  ```bash
  pip install pyyaml requests requests-oauthlib
  ```

### 2. Install GUI Dependencies

**Option A: Automatic Setup (Recommended)**
```bash
# Windows
gui\launch_gui.bat

# Linux/macOS
python gui/setup_gui.py
```

**Option B: Manual Installation**
```bash
cd gui
pip install -r requirements.txt
python app.py
```

### 3. Access the GUI

Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

## Usage

### BIOS Configuration Management

1. **Pull Current Configuration**
   - Navigate to "BIOS Management"
   - Enter target IP address and credentials
   - Click "Pull Configuration" to retrieve current settings

2. **Apply Smart Configuration**
   - Select device type (s2_c2_small, s2_c2_medium, s2_c2_large)
   - Enter target system details
   - Use "Dry Run" mode to preview changes
   - Apply configuration with smart pull-edit-push approach

3. **Generate XML Templates**
   - View device configurations
   - Generate XML templates for device types
   - Download configurations for offline use

### Real-Time Monitoring

The GUI provides real-time updates for:
- Configuration pull/push operations
- Connection testing
- Progress tracking
- Error notifications

### Dashboard Features

- **System Statistics** - Device types, templates, settings counts
- **Quick Actions** - Fast access to common operations  
- **Device Overview** - Summary of available device types
- **Status Indicators** - Connection and system status

## Configuration

### Environment Variables

- `FLASK_ENV` - Set to `development` for debug mode
- `FLASK_APP` - Path to the GUI application (auto-configured)

### Host and Port Configuration

```bash
# Default: localhost:5000
python setup_gui.py

# Custom host and port
python setup_gui.py --host 0.0.0.0 --port 8080

# Debug mode
python setup_gui.py --debug
```

### Security Considerations

⚠️ **Important**: The GUI is designed for internal network use. For production deployments:

1. Change the default secret key in `app.py`
2. Use HTTPS with proper SSL certificates
3. Implement authentication/authorization
4. Restrict network access with firewalls
5. Use environment variables for sensitive configuration

## API Endpoints

The GUI provides REST API endpoints:

- `GET /api/device-types` - List available device types
- `GET /api/device-config/<type>` - Get device configuration  
- `POST /api/generate-xml` - Generate XML configuration
- `POST /api/pull-config` - Pull current BIOS configuration
- `POST /api/apply-config` - Apply BIOS configuration
- `POST /api/validate-connection` - Test BMC connection

## WebSocket Events

Real-time updates via WebSocket:

- `config_progress` - Configuration operation progress
- `connection_test` - Connection test results
- `connected` - Client connection confirmation

## Development

### Project Structure

```
gui/
├── app.py                 # Main Flask application
├── setup_gui.py          # Setup and launcher script
├── launch_gui.bat        # Windows launcher
├── requirements.txt      # GUI dependencies
├── static/
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/
│       └── app.js        # JavaScript functionality
└── templates/
    ├── base.html         # Base template
    ├── index.html        # Dashboard
    ├── bios_management.html
    ├── hardware.html
    ├── database.html
    ├── logs.html
    ├── error.html
    └── modals/           # Modal dialogs
```

### Running in Development Mode

```bash
python setup_gui.py --debug
```

This enables:
- Auto-reload on file changes
- Detailed error pages
- Debug logging
- Flask development server

### Adding New Features

1. Add routes in `app.py`
2. Create templates in `templates/`
3. Add CSS/JS in `static/`
4. Update navigation in `base.html`

## Technology Stack

- **Backend**: Flask, Flask-SocketIO
- **Frontend**: Bootstrap 5, JavaScript ES6
- **Real-time**: Socket.IO WebSockets
- **Icons**: Bootstrap Icons
- **Styling**: Custom CSS with Bootstrap

## Browser Support

Tested and supported browsers:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Troubleshooting

### Common Issues

**GUI won't start:**
```bash
# Check Python version
python --version

# Install dependencies
pip install -r gui/requirements.txt

# Check core dependencies
pip install pyyaml requests requests-oauthlib
```

**Connection errors:**
- Verify target IP addresses are reachable
- Check firewall settings
- Ensure BMC interfaces are enabled

**WebSocket issues:**
- Check browser console for errors
- Verify no proxy/firewall blocking WebSocket connections
- Try refreshing the page

### Debug Mode

Enable debug mode for detailed error information:
```bash
python setup_gui.py --debug
```

### Log Files

The GUI logs to:
- Console output (when running in terminal)
- Browser developer tools console
- Application logs (if configured)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This GUI is part of the HWAutomation project. See the main project README for license information.

## Support

For support and issues:
1. Check this README for common solutions
2. Review the main HWAutomation documentation
3. Check browser developer console for errors
4. Verify all dependencies are installed correctly
