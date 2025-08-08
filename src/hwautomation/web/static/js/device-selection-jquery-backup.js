/**
 * Device Selection JavaScript
 * Handles device listing, filtering, and commissioning functionality
 */

let currentDevices = [];
let selectedDevice = null;

// Initialize page
$(document).ready(function() {
    loadDeviceStatusSummary();
    loadDevices();

    // Event handlers
    $('#device-filter-form').on('submit', handleFilterSubmit);
    $('#clear-filters').on('click', clearFilters);
    $('#refresh-devices').on('click', loadDevices);
    $('#commission-form').on('submit', handleCommissionSubmit);
    $('#deviceDetailsModal').on('hidden.bs.modal', function() {
        selectedDevice = null;
    });
});

/**
 * Load device status summary
 */
function loadDeviceStatusSummary() {
    $.get('/api/devices/status-summary')
        .done(function(data) {
            $('#total-count').text(data.total || 0);
            $('#available-count').text(data.available || 0);
            $('#commissioned-count').text(data.commissioned || 0);
            $('#deployed-count').text(data.deployed || 0);
        })
        .fail(function(xhr) {
            console.error('Failed to load device status summary:', xhr.responseJSON);
            showAlert('Failed to load device status summary', 'error');
        });
}

/**
 * Load devices with current filters
 */
function loadDevices() {
    showLoading(true);

    // Build query parameters from form
    const params = new URLSearchParams();
    const form = $('#device-filter-form')[0];

    if (form.elements['hostname-search'].value) {
        params.append('hostname_pattern', form.elements['hostname-search'].value);
    }
    if (form.elements['status-filter'].value) {
        params.append('status', form.elements['status-filter'].value);
    }
    if (form.elements['min-cpu'].value) {
        params.append('min_cpu', form.elements['min-cpu'].value);
    }
    if (form.elements['min-memory'].value) {
        params.append('min_memory_gb', form.elements['min-memory'].value);
    }
    if (form.elements['architecture'].value) {
        params.append('architecture', form.elements['architecture'].value);
    }

    const url = '/api/devices/available' + (params.toString() ? '?' + params.toString() : '');

    $.get(url)
        .done(function(data) {
            currentDevices = data.machines || [];
            renderDeviceList(currentDevices);
            updateDeviceCount(data.count || 0);
        })
        .fail(function(xhr) {
            console.error('Failed to load devices:', xhr.responseJSON);
            showAlert('Failed to load devices: ' + (xhr.responseJSON?.error || 'Unknown error'), 'error');
            renderDeviceList([]);
            updateDeviceCount(0);
        })
        .always(function() {
            showLoading(false);
        });
}

/**
 * Render device list
 */
function renderDeviceList(devices) {
    const container = $('#device-list');
    container.empty();

    if (devices.length === 0) {
        $('#no-devices').show();
        return;
    }

    $('#no-devices').hide();

    devices.forEach(function(device) {
        const deviceCard = createDeviceCard(device);
        container.append(deviceCard);
    });
}

/**
 * Create device card HTML
 */
function createDeviceCard(device) {
    const statusClass = getStatusClass(device.status);
    const storageDisplay = device.storage_display || 'Unknown';
    const memoryDisplay = device.memory_display || 'Unknown';

    return $(`
        <div class="card mb-3 device-card" data-system-id="${device.system_id}">
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <h6 class="card-title">
                            ${device.hostname || 'Unknown'}
                            <span class="badge badge-${statusClass} ml-2">${device.status}</span>
                        </h6>
                        <p class="card-text">
                            <strong>System ID:</strong> ${device.system_id}<br>
                            <strong>Architecture:</strong> ${device.architecture || 'Unknown'}<br>
                            <strong>Power Type:</strong> ${device.power_type || 'Unknown'}
                        </p>
                    </div>
                    <div class="col-md-4">
                        <p class="card-text">
                            <strong>CPU:</strong> ${device.cpu_count || 0} cores<br>
                            <strong>Memory:</strong> ${memoryDisplay}<br>
                            <strong>Storage:</strong> ${storageDisplay}
                        </p>
                        ${device.ip_addresses && device.ip_addresses.length > 0 ?
                            `<p class="card-text"><strong>IPs:</strong> ${device.ip_addresses.join(', ')}</p>` : ''}
                    </div>
                    <div class="col-md-2 text-right">
                        <button type="button" class="btn btn-info btn-sm mb-2" onclick="showDeviceDetails('${device.system_id}')">
                            Details
                        </button>
                        ${device.status === 'Ready' || device.status === 'New' || device.status.includes('Failed') ?
                            `<button type="button" class="btn btn-success btn-sm" onclick="startCommissioning('${device.system_id}')">
                                Commission
                            </button>` : ''}
                    </div>
                </div>
            </div>
        </div>
    `);
}

/**
 * Get CSS class for device status
 */
function getStatusClass(status) {
    const statusLower = status.toLowerCase();
    if (statusLower === 'ready' || statusLower === 'new') {
        return 'success';
    } else if (statusLower.includes('commissioning') || statusLower.includes('testing')) {
        return 'warning';
    } else if (statusLower === 'deployed') {
        return 'info';
    } else if (statusLower.includes('failed') || statusLower === 'broken') {
        return 'danger';
    } else {
        return 'secondary';
    }
}

/**
 * Show device details modal
 */
function showDeviceDetails(systemId) {
    selectedDevice = currentDevices.find(d => d.system_id === systemId);
    if (!selectedDevice) {
        showAlert('Device not found', 'error');
        return;
    }

    // Load detailed information
    $('#device-details-content').html('<div class="text-center"><div class="spinner-border" role="status"></div></div>');
    $('#commission-device').hide();
    $('#deviceDetailsModal').modal('show');

    $.get(`/api/devices/${systemId}/details`)
        .done(function(details) {
            renderDeviceDetails(details);

            // Show commission button if device is available
            if (selectedDevice.status === 'Ready' || selectedDevice.status === 'New' ||
                selectedDevice.status.includes('Failed')) {
                $('#commission-device').show().off('click').on('click', function() {
                    $('#deviceDetailsModal').modal('hide');
                    startCommissioning(systemId);
                });
            }
        })
        .fail(function(xhr) {
            $('#device-details-content').html(`
                <div class="alert alert-danger">
                    Failed to load device details: ${xhr.responseJSON?.error || 'Unknown error'}
                </div>
            `);
        });
}

/**
 * Render device details
 */
function renderDeviceDetails(details) {
    const basicInfo = details.basic_info || {};
    const hardware = details.hardware || {};
    const network = details.network || {};

    let html = `
        <div class="row">
            <div class="col-md-6">
                <h6>Basic Information</h6>
                <table class="table table-sm">
                    <tr><td><strong>System ID:</strong></td><td>${basicInfo.system_id || 'Unknown'}</td></tr>
                    <tr><td><strong>Hostname:</strong></td><td>${basicInfo.hostname || 'Unknown'}</td></tr>
                    <tr><td><strong>Status:</strong></td><td><span class="badge badge-${getStatusClass(basicInfo.status || '')}">${basicInfo.status || 'Unknown'}</span></td></tr>
                    <tr><td><strong>Architecture:</strong></td><td>${basicInfo.architecture || 'Unknown'}</td></tr>
                    <tr><td><strong>Owner:</strong></td><td>${basicInfo.owner || 'None'}</td></tr>
                    <tr><td><strong>Created:</strong></td><td>${formatDate(basicInfo.created)}</td></tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6>Hardware Specifications</h6>
                <table class="table table-sm">
                    <tr><td><strong>CPU Cores:</strong></td><td>${hardware.cpu_count || 0}</td></tr>
                    <tr><td><strong>Memory:</strong></td><td>${formatBytes(hardware.memory * 1024 * 1024) || 'Unknown'}</td></tr>
                    <tr><td><strong>Power Type:</strong></td><td>${hardware.power_type || 'Unknown'}</td></tr>
                    <tr><td><strong>Boot Method:</strong></td><td>${hardware.bios_boot_method || 'Unknown'}</td></tr>
                    <tr><td><strong>Boot Interface:</strong></td><td>${network.boot_interface || 'Unknown'}</td></tr>
                </table>
            </div>
        </div>
    `;

    // Storage devices
    if (hardware.storage_devices && hardware.storage_devices.length > 0) {
        html += `
            <div class="row mt-3">
                <div class="col-md-12">
                    <h6>Storage Devices</h6>
                    <table class="table table-sm">
                        <thead>
                            <tr><th>Name</th><th>Model</th><th>Size</th><th>Type</th></tr>
                        </thead>
                        <tbody>
        `;

        hardware.storage_devices.forEach(function(device) {
            html += `
                <tr>
                    <td>${device.name || 'Unknown'}</td>
                    <td>${device.model || 'Unknown'}</td>
                    <td>${device.size_display || 'Unknown'}</td>
                    <td>${device.type || 'Unknown'}</td>
                </tr>
            `;
        });

        html += '</tbody></table></div></div>';
    }

    // Network interfaces
    if (hardware.network_interfaces && hardware.network_interfaces.length > 0) {
        html += `
            <div class="row mt-3">
                <div class="col-md-12">
                    <h6>Network Interfaces</h6>
                    <table class="table table-sm">
                        <thead>
                            <tr><th>Name</th><th>Type</th><th>MAC Address</th><th>IP Addresses</th><th>Enabled</th></tr>
                        </thead>
                        <tbody>
        `;

        hardware.network_interfaces.forEach(function(iface) {
            const ipAddresses = iface.ip_addresses.map(ip => `${ip.ip} (${ip.type})`).join(', ') || 'None';
            html += `
                <tr>
                    <td>${iface.name || 'Unknown'}</td>
                    <td>${iface.type || 'Unknown'}</td>
                    <td>${iface.mac_address || 'Unknown'}</td>
                    <td>${ipAddresses}</td>
                    <td>${iface.enabled ? 'Yes' : 'No'}</td>
                </tr>
            `;
        });

        html += '</tbody></table></div></div>';
    }

    // Tags
    if (details.tags && details.tags.length > 0) {
        html += `
            <div class="row mt-3">
                <div class="col-md-12">
                    <h6>Tags</h6>
                    <p>
        `;
        details.tags.forEach(function(tag) {
            html += `<span class="badge badge-secondary mr-1">${tag}</span>`;
        });
        html += '</p></div></div>';
    }

    $('#device-details-content').html(html);
}

/**
 * Start commissioning workflow
 */
function startCommissioning(systemId) {
    selectedDevice = currentDevices.find(d => d.system_id === systemId);
    if (!selectedDevice) {
        showAlert('Device not found', 'error');
        return;
    }

    // Reset form
    $('#commission-form')[0].reset();
    $('#commission-system-id').val(systemId);
    $('#commission-device-info').text(`${selectedDevice.hostname} (${systemId})`);
    $('#commission-status').hide();
    $('#commission-form').show();
    $('#start-commission').show();

    // Get validation and suggested device type
    $.get(`/api/devices/${systemId}/validate`)
        .done(function(data) {
            if (!data.valid) {
                showAlert(`Device cannot be commissioned: ${data.reason}`, 'error');
                return;
            }

            $('#suggested-device-type').text(data.suggested_device_type || 'Unknown');

            // Pre-select suggested device type
            if (data.suggested_device_type) {
                $('#commission-device-type').val(data.suggested_device_type);
            }
        })
        .fail(function(xhr) {
            console.error('Failed to validate device:', xhr.responseJSON);
            $('#suggested-device-type').text('Unknown');
        });

    $('#commissionModal').modal('show');
}

/**
 * Handle filter form submission
 */
function handleFilterSubmit(e) {
    e.preventDefault();
    loadDevices();
}

/**
 * Clear all filters
 */
function clearFilters() {
    $('#device-filter-form')[0].reset();
    loadDevices();
}

/**
 * Handle commission form submission
 */
function handleCommissionSubmit(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = {
        server_id: formData.get('system_id'),
        device_type: formData.get('device_type')
    };

    if (formData.get('target_ipmi_ip')) {
        data.target_ipmi_ip = formData.get('target_ipmi_ip');
    }

    if (formData.get('rack_location')) {
        data.rack_location = formData.get('rack_location');
    }

    // Show progress
    $('#commission-form').hide();
    $('#start-commission').hide();
    $('#commission-status').show();
    updateCommissionProgress(0, 'Starting commissioning...');

    // Start commissioning
    $.ajax({
        url: '/api/orchestration/provision',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(data)
    })
    .done(function(result) {
        if (result.success) {
            updateCommissionProgress(100, 'Commissioning completed successfully!');
            setTimeout(function() {
                $('#commissionModal').modal('hide');
                loadDevices(); // Refresh device list
                showAlert('Device commissioned successfully!', 'success');
            }, 2000);
        } else {
            showAlert(`Commissioning failed: ${result.error || 'Unknown error'}`, 'error');
            resetCommissionForm();
        }
    })
    .fail(function(xhr) {
        showAlert(`Commissioning failed: ${xhr.responseJSON?.error || 'Unknown error'}`, 'error');
        resetCommissionForm();
    });
}

/**
 * Reset commission form
 */
function resetCommissionForm() {
    $('#commission-status').hide();
    $('#commission-form').show();
    $('#start-commission').show();
}

/**
 * Update commission progress
 */
function updateCommissionProgress(percent, message) {
    $('#commission-progress').css('width', percent + '%').attr('aria-valuenow', percent);
    $('#commission-step').text(message);
}

/**
 * Update device count display
 */
function updateDeviceCount(count) {
    $('#device-count').text(`${count} device${count !== 1 ? 's' : ''}`);
}

/**
 * Show loading state
 */
function showLoading(show) {
    if (show) {
        $('#device-loading').show();
        $('#device-list').hide();
        $('#no-devices').hide();
    } else {
        $('#device-loading').hide();
        $('#device-list').show();
    }
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    const alertClass = type === 'error' ? 'alert-danger' : `alert-${type}`;
    const alert = $(`
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="close" data-dismiss="alert">
                <span>&times;</span>
            </button>
        </div>
    `);

    // Insert at top of page
    $('.container-fluid').prepend(alert);

    // Auto-dismiss after 5 seconds
    setTimeout(function() {
        alert.alert('close');
    }, 5000);
}

/**
 * Format date string
 */
function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    try {
        return new Date(dateString).toLocaleString();
    } catch (e) {
        return dateString;
    }
}

/**
 * Format bytes to human readable
 */
function formatBytes(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}
