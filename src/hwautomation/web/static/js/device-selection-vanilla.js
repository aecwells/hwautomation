/**
 * Device Selection JavaScript (Vanilla JS - No jQuery)
 * Handles device listing, filtering, and commissioning functionality
 */

let currentDevices = [];
let selectedDevice = null;
let deviceDetailsModal = null;
let commissionModal = null;

// Initialize page when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap modals
    deviceDetailsModal = new bootstrap.Modal(document.getElementById('deviceDetailsModal'));
    commissionModal = new bootstrap.Modal(document.getElementById('commissionModal'));

    // Load initial data
    loadDeviceStatusSummary();
    loadDevices();

    // Event handlers
    document.getElementById('device-filter-form').addEventListener('submit', handleFilterSubmit);
    document.getElementById('clear-filters').addEventListener('click', clearFilters);
    document.getElementById('refresh-devices').addEventListener('click', loadDevices);
    document.getElementById('commission-form').addEventListener('submit', handleCommissionSubmit);

    // Modal event handlers
    document.getElementById('deviceDetailsModal').addEventListener('hidden.bs.modal', function() {
        selectedDevice = null;
    });
});

/**
 * Load device status summary
 */
function loadDeviceStatusSummary() {
    fetch('/api/devices/status-summary')
        .then(response => response.json())
        .then(data => {
            document.getElementById('total-count').textContent = data.total || 0;
            document.getElementById('available-count').textContent = data.available || 0;
            document.getElementById('commissioned-count').textContent = data.commissioned || 0;
            document.getElementById('deployed-count').textContent = data.deployed || 0;
        })
        .catch(error => {
            console.error('Failed to load device status summary:', error);
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
    const form = document.getElementById('device-filter-form');
    const formData = new FormData(form);

    // Add form data to URLSearchParams
    for (let [key, value] of formData.entries()) {
        if (value.trim()) {
            params.append(key, value);
        }
    }

    // Add individual filter inputs
    const hostnameSearch = document.getElementById('hostname-search').value;
    const statusFilter = document.getElementById('status-filter').value;
    const minCpu = document.getElementById('min-cpu').value;
    const minMemory = document.getElementById('min-memory').value;
    const architecture = document.getElementById('architecture').value;

    if (hostnameSearch) params.append('hostname', hostnameSearch);
    if (statusFilter) params.append('status', statusFilter);
    if (minCpu) params.append('min_cpu', minCpu);
    if (minMemory) params.append('min_memory', minMemory);
    if (architecture) params.append('architecture', architecture);

    const url = `/api/devices/available?${params.toString()}`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            currentDevices = data.devices || [];
            displayDevices(currentDevices);
            updateDeviceCount(currentDevices.length);
            showLoading(false);
        })
        .catch(error => {
            console.error('Failed to load devices:', error);
            showAlert('Failed to load devices', 'error');
            showLoading(false);
        });
}

/**
 * Display devices in the device list
 */
function displayDevices(devices) {
    const container = document.getElementById('device-list');
    container.innerHTML = '';

    if (devices.length === 0) {
        document.getElementById('no-devices').style.display = 'block';
        return;
    }

    document.getElementById('no-devices').style.display = 'none';

    devices.forEach(device => {
        const deviceCard = createDeviceCard(device);
        container.appendChild(deviceCard);
    });
}

/**
 * Create a device card element
 */
function createDeviceCard(device) {
    const cardDiv = document.createElement('div');
    cardDiv.className = 'col-md-6 col-lg-4 mb-3';

    const statusClass = getStatusClass(device.status);
    const ipAddressDisplay = device.ip_addresses && device.ip_addresses.length > 0
        ? device.ip_addresses[0]
        : 'Not assigned';

    cardDiv.innerHTML = `
        <div class="card device-card" data-system-id="${device.system_id}">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h6 class="mb-0">${device.hostname}</h6>
                <span class="badge ${statusClass}">${device.status}</span>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-6">
                        <small class="text-muted">CPU Cores</small>
                        <div>${device.cpu_count || 'Unknown'}</div>
                    </div>
                    <div class="col-6">
                        <small class="text-muted">Memory</small>
                        <div>${device.memory_display || 'Unknown'}</div>
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-6">
                        <small class="text-muted">Storage</small>
                        <div>${device.storage_display || 'Unknown'}</div>
                    </div>
                    <div class="col-6">
                        <small class="text-muted">Architecture</small>
                        <div>${device.architecture || 'Unknown'}</div>
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-12">
                        <small class="text-muted">IP Address</small>
                        <div>${ipAddressDisplay}</div>
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-12">
                        <small class="text-muted">Power Type</small>
                        <div>${device.power_type || 'Unknown'}</div>
                    </div>
                </div>
                ${device.tags && device.tags.length > 0 ? `
                <div class="row mt-2">
                    <div class="col-12">
                        <small class="text-muted">Tags</small>
                        <div>${device.tags.map(tag => `<span class="badge badge-secondary badge-sm">${tag}</span>`).join(' ')}</div>
                    </div>
                </div>
                ` : ''}
            </div>
            <div class="card-footer">
                <button class="btn btn-primary btn-sm" onclick="showDeviceDetails('${device.system_id}')">
                    View Details
                </button>
                <button class="btn btn-success btn-sm" onclick="commissionDevice('${device.system_id}')">
                    Commission
                </button>
            </div>
        </div>
    `;

    return cardDiv;
}

/**
 * Get Bootstrap status class for device status
 */
function getStatusClass(status) {
    switch (status.toLowerCase()) {
        case 'ready': return 'badge-success';
        case 'new': return 'badge-info';
        case 'failed testing': return 'badge-warning';
        case 'failed commissioning': return 'badge-danger';
        case 'deployed': return 'badge-primary';
        default: return 'badge-secondary';
    }
}

/**
 * Show device details modal
 */
function showDeviceDetails(systemId) {
    selectedDevice = currentDevices.find(d => d.system_id === systemId);
    if (!selectedDevice) return;

    // Show loading in modal
    document.getElementById('device-details-content').innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';
    document.getElementById('commission-device').style.display = 'none';
    deviceDetailsModal.show();

    // Load detailed information
    fetch(`/api/devices/${systemId}/details`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('commission-device').style.display = 'inline-block';

                // Remove any existing event listeners and add new one
                const commissionBtn = document.getElementById('commission-device');
                commissionBtn.replaceWith(commissionBtn.cloneNode(true));
                document.getElementById('commission-device').addEventListener('click', function() {
                    deviceDetailsModal.hide();
                    commissionDevice(systemId);
                });

                // Display detailed information
                document.getElementById('device-details-content').innerHTML = `
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Basic Information</h6>
                            <table class="table table-sm">
                                <tr><td><strong>Hostname:</strong></td><td>${data.device.hostname}</td></tr>
                                <tr><td><strong>System ID:</strong></td><td>${data.device.system_id}</td></tr>
                                <tr><td><strong>Status:</strong></td><td><span class="badge ${getStatusClass(data.device.status)}">${data.device.status}</span></td></tr>
                                <tr><td><strong>Owner:</strong></td><td>${data.device.owner || 'None'}</td></tr>
                                <tr><td><strong>Architecture:</strong></td><td>${data.device.architecture}</td></tr>
                                <tr><td><strong>Power Type:</strong></td><td>${data.device.power_type}</td></tr>
                            </table>
                        </div>
                        <div class="col-md-6">
                            <h6>Hardware Specifications</h6>
                            <table class="table table-sm">
                                <tr><td><strong>CPU Cores:</strong></td><td>${data.device.cpu_count}</td></tr>
                                <tr><td><strong>Memory:</strong></td><td>${data.device.memory_display}</td></tr>
                                <tr><td><strong>Storage:</strong></td><td>${data.device.storage_display}</td></tr>
                                <tr><td><strong>BIOS Boot Method:</strong></td><td>${data.device.bios_boot_method}</td></tr>
                            </table>
                        </div>
                    </div>
                    ${data.device.ip_addresses && data.device.ip_addresses.length > 0 ? `
                    <div class="row mt-3">
                        <div class="col-12">
                            <h6>Network Information</h6>
                            <table class="table table-sm">
                                <tr><td><strong>IP Addresses:</strong></td><td>${data.device.ip_addresses.join(', ')}</td></tr>
                            </table>
                        </div>
                    </div>
                    ` : ''}
                    ${data.device.tags && data.device.tags.length > 0 ? `
                    <div class="row mt-3">
                        <div class="col-12">
                            <h6>Tags</h6>
                            <p>${data.device.tags.map(tag => `<span class="badge badge-secondary">${tag}</span>`).join(' ')}</p>
                        </div>
                    </div>
                    ` : ''}
                `;
            } else {
                document.getElementById('device-details-content').innerHTML = `
                    <div class="alert alert-danger">
                        <strong>Error:</strong> ${data.message || 'Failed to load device details'}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Failed to load device details:', error);
            document.getElementById('device-details-content').innerHTML = `
                <div class="alert alert-danger">
                    <strong>Error:</strong> Failed to load device details
                </div>
            `;
        });
}

/**
 * Show commission device modal
 */
function commissionDevice(systemId) {
    selectedDevice = currentDevices.find(d => d.system_id === systemId);
    if (!selectedDevice) return;

    // Populate commission form
    document.getElementById('commission-system-id').value = systemId;
    document.getElementById('commission-device-info').textContent = `${selectedDevice.hostname} (${systemId})`;

    // Load validation and suggestions
    fetch(`/api/devices/${systemId}/validate`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const suggestion = data.suggestions.device_type || 'Based on specifications';
                document.getElementById('suggested-device-type').textContent = suggestion;

                // Auto-select suggested device type if available
                if (data.suggestions.device_type) {
                    const deviceTypeSelect = document.getElementById('commission-device-type');
                    const suggestion = data.suggestions.device_type.toLowerCase();

                    if (suggestion.includes('small')) {
                        deviceTypeSelect.value = 's2.c2.small';
                    } else if (suggestion.includes('large')) {
                        deviceTypeSelect.value = 's2.c2.large';
                    } else if (suggestion.includes('medium')) {
                        deviceTypeSelect.value = 's2.c2.medium';
                    }
                }
            }
        })
        .catch(error => {
            console.error('Failed to validate device:', error);
            document.getElementById('suggested-device-type').textContent = 'Unable to determine';
        });

    // Show modal
    commissionModal.show();
}

/**
 * Handle filter form submission
 */
function handleFilterSubmit(event) {
    event.preventDefault();
    loadDevices();
}

/**
 * Clear all filters
 */
function clearFilters() {
    document.getElementById('device-filter-form').reset();
    loadDevices();
}

/**
 * Handle commission form submission
 */
function handleCommissionSubmit(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const commissionData = Object.fromEntries(formData.entries());

    // Show progress
    document.getElementById('commission-status').style.display = 'block';
    document.getElementById('start-commission').disabled = true;

    // Start commissioning
    fetch('/api/devices/commission', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(commissionData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Device commissioning started successfully', 'success');
            commissionModal.hide();
            loadDevices(); // Refresh device list
        } else {
            showAlert(`Failed to start commissioning: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        console.error('Failed to commission device:', error);
        showAlert('Failed to start commissioning', 'error');
    })
    .finally(() => {
        document.getElementById('commission-status').style.display = 'none';
        document.getElementById('start-commission').disabled = false;
    });
}

/**
 * Show loading indicator
 */
function showLoading(show) {
    const loadingElement = document.getElementById('device-loading');
    if (show) {
        loadingElement.style.display = 'block';
    } else {
        loadingElement.style.display = 'none';
    }
}

/**
 * Update device count display
 */
function updateDeviceCount(count) {
    document.getElementById('device-count').textContent = `${count} device${count !== 1 ? 's' : ''}`;
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // Insert at top of container
    const container = document.querySelector('.container-fluid');
    container.insertBefore(alertDiv, container.firstChild);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}
