# Enhanced Server Commissioning with Database Integration

## Overview

The HWAutomation system has been enhanced with comprehensive database integration and SSH connectivity validation throughout the server commissioning workflow. This ensures complete tracking of the provisioning process and validates that servers are properly accessible before proceeding.

## Key Enhancements

### 🗄️ **Database Integration**

**Automatic Database Management:**
- Server entries are automatically created when commissioning begins
- Status updates throughout the entire provisioning workflow
- Hardware discovery results stored in database
- SSH and IPMI connectivity status tracked
- Vendor-specific information preserved

**Database Fields Enhanced:**
```sql
-- Core server information
server_id TEXT                    -- MaaS system ID
status_name TEXT                  -- Current provisioning status
is_ready TEXT                     -- TRUE/FALSE server readiness
server_model TEXT                 -- Hardware model with vendor info

-- Network connectivity
ip_address TEXT                   -- Server IP address from MaaS
ip_address_works TEXT             -- SSH connectivity status (TRUE/FALSE)

-- IPMI/BMC management  
ipmi_address TEXT                 -- Discovered IPMI IP address
ipmi_address_works TEXT           -- IPMI connectivity status (TRUE/FALSE)
kcs_status TEXT                   -- IPMI KCS interface status
host_inferface_status TEXT        -- Host interface status

-- Metadata and vendor info
currServerModels TEXT             -- Vendor-specific information summary
```

### 🔌 **SSH Connectivity Validation**

**Multi-Attempt SSH Testing:**
- Exponential backoff retry logic (1s, 2s, 4s, 8s, 16s)
- Comprehensive connectivity validation before workflow continues
- Database status updates for successful/failed SSH tests
- Error handling with detailed logging

**SSH Test Implementation:**
```python
def _test_ssh_connectivity(self, ip_address: str, context: WorkflowContext, max_retries: int = 5) -> bool:
    """Test SSH connectivity with retry logic and database updates"""
    # Multiple connection attempts with exponential backoff
    # Updates database with connectivity status
    # Validates workflow can proceed safely
```

### 🔍 **Enhanced Hardware Discovery**

**Vendor-Specific Integration:**
- Automatic vendor tool installation (sumtool, hpssacli, omreport)
- Enhanced hardware information collection
- IPMI address discovery and validation
- Network interface enumeration
- Vendor-specific BMC/firmware details

**Database Storage:**
- System manufacturer and model information
- IPMI configuration and connectivity status
- Vendor-specific tool results
- Hardware discovery error tracking

### 🚀 **Workflow Integration**

**8-Step Enhanced Process:**

1. **Commission Server + Database Entry**
   - Create database record for new server
   - Update status to "Commissioning"
   - Store basic server model information
   - Track commissioning progress and errors

2. **Get Server IP + SSH Validation**
   - Retrieve IP address from MaaS
   - Test SSH connectivity with retry logic
   - Update database with IP and connectivity status
   - Fail workflow if SSH inaccessible

3. **Hardware Discovery + Database Storage**
   - Run comprehensive hardware discovery
   - Store system, IPMI, and vendor information
   - Test IPMI connectivity via ping
   - Update database with discovery results

4. **Pull BIOS Config** (Enhanced with connectivity validation)
5. **Modify BIOS Config** (Device-type specific)
6. **Push BIOS Config** (With verification)
7. **Configure IPMI** (Using discovered or target IP)

8. **Finalize + Database Completion**
   - Apply MaaS tags for tracking
   - Update database with final completion status
   - Store metadata about SSH/IPMI verification
   - Mark server as fully provisioned

## Usage Examples

### **Interactive Device Selection (New)**

**Web-Based Device Selection:**
```bash
# Start the GUI application
cd /home/ubuntu/HWAutomation
python gui/app.py

# Navigate to: http://localhost:5000/device-selection
# - View all available MaaS devices
# - Filter by CPU, memory, status, architecture
# - See detailed hardware specifications
# - Commission devices with guided workflow
```

**Device Selection Features:**
- **Smart Filtering**: Filter by status, hardware specs, architecture, tags
- **Hardware Details**: View CPU, memory, storage, network interfaces
- **Validation**: Automatic commissioning readiness checks
- **Device Type Suggestions**: Automatic suggestions based on hardware specs  
- **Search by Hostname**: Find specific devices quickly
- **Status Summary**: Overview of total, available, commissioned, deployed devices

### **CLI Commissioning with Database Tracking**

```bash
# Show planned workflow (dry-run)
./examples/enhanced_commissioning_demo.py \
  --server-id server-001 \
  --device-type s2.c2.small \
  --ipmi-ip 192.168.100.10 \
  --dry-run

# Execute full commissioning with database integration
./examples/enhanced_commissioning_demo.py \
  --server-id server-001 \
  --device-type s2.c2.small \
  --ipmi-ip 192.168.100.10 \
  --verbose
```

### **Programmatic Usage**

```python
from hwautomation.orchestration.workflow_manager import WorkflowManager
from hwautomation.orchestration.server_provisioning import ServerProvisioningWorkflow

# Initialize with database integration
workflow_manager = WorkflowManager(config)
provisioning = ServerProvisioningWorkflow(workflow_manager)

# Commission with automatic database tracking
result = provisioning.provision_server(
    server_id="server-001",
    device_type="s2.c2.small", 
    target_ipmi_ip="192.168.100.10",
    progress_callback=progress_callback
)

# Database automatically updated throughout process
if result['success']:
    print(f"SSH Verified: {result['context']['ssh_connectivity_verified']}")
    print(f"Database Updated: {result['context']['database_updated']}")
```

### **GUI Integration**

**Enhanced Database API Endpoints:**
- `GET /api/database/servers/status` - Server commissioning status with connectivity
- `POST /api/database/servers/<id>/test-connectivity` - Test SSH/IPMI connectivity
- Enhanced database viewer with commissioning tracking

**Device Selection API Endpoints (New):**
- `GET /api/devices/available` - List available devices with filtering
- `GET /api/devices/<system_id>/details` - Detailed device information
- `GET /api/devices/<system_id>/validate` - Validate device for commissioning
- `GET /api/devices/status-summary` - Device status statistics
- `POST /api/devices/search` - Advanced device search with filters

**Interactive Device Management:**
```javascript
// Get available devices with filters
fetch('/api/devices/available?status=available&min_cpu=8&min_memory_gb=16')
  .then(response => response.json())
  .then(data => {
    console.log(`Found ${data.count} devices matching criteria`);
    data.machines.forEach(machine => {
      console.log(`${machine.hostname}: ${machine.cpu_count} CPUs, ${machine.memory_display}`);
    });
  });

// Get device details for commissioning decision
fetch('/api/devices/abc123/details')
  .then(response => response.json())
  .then(details => {
    console.log(`Hardware: ${details.hardware.cpu_count} CPUs, ${details.hardware.storage_devices.length} drives`);
    console.log(`Network: ${details.hardware.network_interfaces.length} interfaces`);
  });

// Validate and get suggested device type
fetch('/api/devices/abc123/validate')
  .then(response => response.json())
  .then(validation => {
    if (validation.valid) {
      console.log(`Device ready for commissioning`);
      console.log(`Suggested type: ${validation.suggested_device_type}`);
    }
  });
```

**Real-time Status Monitoring:**
```javascript
// Get server commissioning status
fetch('/api/database/servers/status')
  .then(response => response.json())
  .then(data => {
    console.log(`Healthy Servers: ${data.summary.healthy_servers}`);
    console.log(`SSH Connectivity: ${data.summary.ssh_connectivity_rate}`);
    console.log(`IPMI Connectivity: ${data.summary.ipmi_connectivity_rate}`);
  });
```

## Database Schema Integration

### **Status Tracking Throughout Workflow**

| Workflow Step | Database Updates |
|---------------|------------------|
| Commission Server | `status_name='Commissioning'`, `is_ready='FALSE'` |
| Get Server IP | `ip_address='x.x.x.x'`, `ip_address_works='TRUE/FALSE'` |
| Hardware Discovery | `server_model`, `ipmi_address`, `ipmi_address_works` |
| BIOS Configuration | `status_name` updates during BIOS steps |
| IPMI Configuration | `kcs_status='Enabled'`, `host_inferface_status='Active'` |
| Finalize Server | `status_name='Provisioning Complete'`, `is_ready='TRUE'` |

### **Health Status Determination**

```python
# Server health logic
if server['is_ready'] and server['ssh_connectivity'] and server['ipmi_connectivity']:
    health_status = 'healthy'  # Fully operational
elif server['ssh_connectivity'] and server['ip_address']:
    health_status = 'partial'  # SSH works, IPMI issues
elif 'Error' in server['status_name']:
    health_status = 'error'    # Provisioning failed
else:
    health_status = 'pending'  # Still provisioning
```

## Error Handling and Recovery

### **Database Consistency**
- All database updates wrapped in try/catch blocks
- Error states recorded in database for troubleshooting
- Partial completion status preserved for recovery

### **SSH Connectivity Failures**
- Multiple retry attempts with exponential backoff
- Clear error messaging and database status updates
- Workflow fails early if SSH inaccessible (prevents wasted time)

### **IPMI Discovery Issues**
- Non-fatal IPMI discovery failures (workflow continues)
- Database records connectivity status for manual intervention
- Fallback to target IPMI IP if discovery fails

## Monitoring and Maintenance

### **Server Health Dashboard**
- Real-time status of all commissioned servers
- SSH and IPMI connectivity indicators
- Health status summary and statistics
- One-click connectivity testing

### **Database Maintenance**
- Automatic schema migrations
- Backup capabilities before major operations
- Export functionality for reporting
- Historical tracking of commissioning activities

## Benefits

1. **Complete Visibility**: Every server's commissioning status tracked in database
2. **Early Failure Detection**: SSH connectivity validated before proceeding
3. **Vendor Integration**: Hardware-specific tools automatically installed and used
4. **Recovery Capability**: Detailed status allows resuming failed workflows
5. **Monitoring Ready**: Database provides foundation for alerting and dashboards
6. **Audit Trail**: Complete history of commissioning activities and results
7. **Device Discovery**: Browse and select MaaS devices without manual ID entry
8. **Intelligent Filtering**: Advanced search and filtering by hardware specifications
9. **Guided Commissioning**: Interactive workflow with validation and suggestions
10. **Hardware Awareness**: Automatic device type suggestions based on actual specs

## Device Selection Workflow

### **Traditional vs Enhanced Approach**

**Before (Manual Machine ID Entry):**
```bash
# User must know Machine ID in advance
hwautomation provision --server-id abc123def456 --device-type s2.c2.small
```

**After (Interactive Device Selection):**
1. **Browse Available Devices**: View all MaaS devices with rich details
2. **Apply Smart Filters**: Filter by CPU, memory, status, architecture  
3. **Inspect Hardware**: See detailed specs, network interfaces, storage
4. **Validate Readiness**: Automatic commissioning readiness checks
5. **Get Suggestions**: System suggests optimal device type
6. **Commission Interactively**: Guided workflow with progress tracking

### **Device Selection Features**

| Feature | Description | Benefit |
|---------|-------------|---------|
| **Status Summary** | Real-time count of total, available, commissioned, deployed devices | Quick infrastructure overview |
| **Smart Filtering** | Filter by CPU cores, memory, storage, architecture, power type | Find devices matching requirements |
| **Hardware Details** | CPU, memory, storage devices, network interfaces, BIOS info | Make informed commissioning decisions |
| **Hostname Search** | Find devices by hostname pattern | Quick device location |
| **Tag Support** | Filter by MaaS tags (include/exclude) | Organize devices by purpose/location |
| **Validation** | Check commissioning readiness and ownership | Prevent commissioning conflicts |
| **Type Suggestions** | Automatic device type based on hardware specs | Optimal configuration selection |
| **Interactive UI** | Cards, modals, progress tracking | User-friendly experience |

This enhanced system ensures that commissioned devices are properly tracked, validated for connectivity, and have comprehensive hardware information stored for ongoing management and troubleshooting. The new device selection interface eliminates the need for manual Machine ID lookup and provides a rich, interactive commissioning experience.
