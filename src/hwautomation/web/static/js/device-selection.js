/**
 * Device Selection JavaScript (Vanilla JS - No jQuery)
 * Handles device listing, filtering, and commissioning functionality
 */

let currentDevices = [];
let selectedDevice = null;
let deviceDetailsModal = null;
let commissionModal = null;
let currentView = 'cards'; // 'cards' or 'list'
let masonryInstance = null;

// Initialize page when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing device selection...');
    
    // Wait a bit more to ensure all elements are rendered
    setTimeout(function() {
        initializeDeviceSelection();
    }, 100);
});

function initializeDeviceSelection() {
    // Verify all required elements exist
    const requiredElements = [
        'deviceDetailsModal',
        'commissionModal',
        'device-filter-form',
        'clear-filters',
        'refresh-devices',
        'commission-form',
        'device-cards-container',
        'device-list-container',
        'device-list-tbody'
    ];
    
    const missingElements = requiredElements.filter(id => !document.getElementById(id));
    if (missingElements.length > 0) {
        console.error('Missing required elements:', missingElements);
        // Still try to initialize what we can
    }
    
    // Initialize Bootstrap modals
    const deviceDetailsModalEl = document.getElementById('deviceDetailsModal');
    const commissionModalEl = document.getElementById('commissionModal');
    
    if (deviceDetailsModalEl && commissionModalEl) {
        deviceDetailsModal = new bootstrap.Modal(deviceDetailsModalEl);
        commissionModal = new bootstrap.Modal(commissionModalEl);
        
        // Fix aria-hidden accessibility issue
        commissionModalEl.addEventListener('show.bs.modal', function() {
            this.removeAttribute('aria-hidden');
        });
        
        commissionModalEl.addEventListener('hide.bs.modal', function() {
            this.setAttribute('aria-hidden', 'true');
        });
        
        deviceDetailsModalEl.addEventListener('show.bs.modal', function() {
            this.removeAttribute('aria-hidden');
        });
        
        deviceDetailsModalEl.addEventListener('hide.bs.modal', function() {
            this.setAttribute('aria-hidden', 'true');
        });
    } else {
        console.error('Modal elements not found');
    }
    
    // Load initial data
    loadDeviceStatusSummary();
    loadDevices();
    
    // Event handlers
    const filterForm = document.getElementById('device-filter-form');
    const clearFiltersBtn = document.getElementById('clear-filters');
    const refreshBtn = document.getElementById('refresh-devices');
    const commissionForm = document.getElementById('commission-form');
    
    if (filterForm) filterForm.addEventListener('submit', handleFilterSubmit);
    if (clearFiltersBtn) clearFiltersBtn.addEventListener('click', clearFilters);
    if (refreshBtn) refreshBtn.addEventListener('click', loadDevices);
    if (commissionForm) commissionForm.addEventListener('submit', handleCommissionSubmit);
    
    // Modal event handlers
    if (deviceDetailsModalEl) {
        deviceDetailsModalEl.addEventListener('hidden.bs.modal', function() {
            selectedDevice = null;
        });
    }
    
    console.log('Device selection initialized successfully');
}

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
            currentDevices = data.machines || [];
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
 * Display devices in the current view (cards or list)
 */
function displayDevices(devices) {
    if (devices.length === 0) {
        document.getElementById('no-devices').style.display = 'block';
        document.getElementById('device-cards-container').style.display = 'none';
        document.getElementById('device-list-container').style.display = 'none';
        return;
    }
    
    document.getElementById('no-devices').style.display = 'none';
    
    if (currentView === 'cards') {
        displayDevicesAsCards(devices);
    } else {
        displayDevicesAsList(devices);
    }
}

/**
 * Display devices as masonry cards
 */
function displayDevicesAsCards(devices) {
    const container = document.getElementById('device-cards-container');
    
    // Check if container exists
    if (!container) {
        console.error('device-cards-container element not found in DOM');
        // Fallback to old container if it exists
        const fallbackContainer = document.getElementById('device-list');
        if (fallbackContainer) {
            console.log('Using fallback container');
            fallbackContainer.innerHTML = '';
            devices.forEach(device => {
                const deviceCard = createDeviceCard(device);
                fallbackContainer.appendChild(deviceCard);
            });
        }
        return;
    }
    
    container.innerHTML = '';
    container.style.display = 'block';
    
    const listContainer = document.getElementById('device-list-container');
    if (listContainer) {
        listContainer.style.display = 'none';
    }
    
    // Destroy existing masonry instance
    if (masonryInstance) {
        masonryInstance.destroy();
    }
    
    devices.forEach(device => {
        const deviceCard = createDeviceCard(device);
        container.appendChild(deviceCard);
    });
    
    // Initialize masonry layout
    setTimeout(() => {
        masonryInstance = new Masonry(container, {
            itemSelector: '.col-lg-4',
            columnWidth: '.col-lg-4',
            percentPosition: true
        });
    }, 100);
}

/**
 * Display devices as a list/table
 */
function displayDevicesAsList(devices) {
    const tableBody = document.getElementById('device-list-tbody');
    const cardsContainer = document.getElementById('device-cards-container');
    const listContainer = document.getElementById('device-list-container');
    
    // Check if required elements exist
    if (!tableBody || !listContainer) {
        console.error('Required list view elements not found in DOM');
        return;
    }
    
    tableBody.innerHTML = '';
    
    if (cardsContainer) {
        cardsContainer.style.display = 'none';
    }
    listContainer.style.display = 'block';
    
    devices.forEach(device => {
        const row = createDeviceListRow(device);
        tableBody.appendChild(row);
    });
}

/**
 * Create a device list row for table view
 */
function createDeviceListRow(device) {
    const row = document.createElement('tr');
    row.setAttribute('data-system-id', device.system_id);
    
    const statusClass = getStatusClass(device.status);
    const ipAddressDisplay = device.ip_addresses && device.ip_addresses.length > 0 
        ? device.ip_addresses[0] 
        : 'Not assigned';
    
    // Check if this device is currently being commissioned
    const isCommissioning = commissioningWorkflows.has(device.system_id);
    const workflowInfo = isCommissioning ? commissioningWorkflows.get(device.system_id) : null;
    
    row.innerHTML = `
        <td>
            <div class="d-flex align-items-center">
                <div class="me-3">
                    <i class="bi bi-server fs-4 text-muted"></i>
                </div>
                <div>
                    <div class="fw-bold">${device.hostname}</div>
                    <small class="text-muted">${device.system_id}</small>
                </div>
            </div>
        </td>
        <td>
            <span class="badge ${isCommissioning ? 'bg-warning' : statusClass} status-badge">${isCommissioning ? 'Commissioning' : device.status}</span>
            ${isCommissioning && workflowInfo ? `
            <div class="commissioning-progress mt-1">
                <div class="progress" style="height: 4px;">
                    <div class="progress-bar progress-bar-striped progress-bar-animated bg-warning" 
                         style="width: ${workflowInfo.progress}%"></div>
                </div>
                <small class="text-muted d-block">${workflowInfo.currentStep}</small>
            </div>
            ` : ''}
        </td>
        <td>${device.cpu_count || 'Unknown'}</td>
        <td>${device.memory_display || 'Unknown'}</td>
        <td>${device.storage_display || 'Unknown'}</td>
        <td>
            <span class="text-muted">${ipAddressDisplay}</span>
        </td>
        <td>
            <small class="text-muted">${device.architecture || 'Unknown'}</small>
        </td>
        <td>
            <div class="btn-group" role="group">
                <button class="btn btn-outline-primary btn-sm" onclick="showDeviceDetails('${device.system_id}')" title="View Details">
                    <i class="bi bi-eye"></i>
                </button>
                <button class="btn btn-outline-success btn-sm" onclick="commissionDevice('${device.system_id}')" title="Commission" ${isCommissioning ? 'disabled' : ''}>
                    <i class="bi bi-play-circle"></i>
                </button>
            </div>
        </td>
    `;
    
    return row;
}

/**
 * Create a device card element for masonry layout
 */
function createDeviceCard(device) {
    const cardDiv = document.createElement('div');
    cardDiv.className = 'col-md-6 col-lg-4';
    
    const statusClass = getStatusClass(device.status);
    const ipAddressDisplay = device.ip_addresses && device.ip_addresses.length > 0 
        ? device.ip_addresses[0] 
        : 'Not assigned';
    
    // Check if this device is currently being commissioned
    const isCommissioning = commissioningWorkflows.has(device.system_id);
    const workflowInfo = isCommissioning ? commissioningWorkflows.get(device.system_id) : null;
    
    cardDiv.innerHTML = `
        <div class="card device-card" data-system-id="${device.system_id}">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h6 class="mb-0">${device.hostname}</h6>
                <span class="badge ${isCommissioning ? 'bg-warning' : statusClass}">${isCommissioning ? 'Commissioning' : device.status}</span>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-6">
                        <small class="text-muted">CPU Cores</small>
                        <div class="fw-bold">${device.cpu_count || 'Unknown'}</div>
                    </div>
                    <div class="col-6">
                        <small class="text-muted">Memory</small>
                        <div class="fw-bold">${device.memory_display || 'Unknown'}</div>
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-6">
                        <small class="text-muted">Storage</small>
                        <div class="fw-bold">${device.storage_display || 'Unknown'}</div>
                    </div>
                    <div class="col-6">
                        <small class="text-muted">Architecture</small>
                        <div class="fw-bold">${device.architecture || 'Unknown'}</div>
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-12">
                        <small class="text-muted">IP Address</small>
                        <div class="fw-bold">${ipAddressDisplay}</div>
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-12">
                        <small class="text-muted">Power Type</small>
                        <div class="fw-bold">${device.power_type || 'Unknown'}</div>
                    </div>
                </div>
                ${device.tags && device.tags.length > 0 ? `
                <div class="row mt-2">
                    <div class="col-12">
                        <small class="text-muted">Tags</small>
                        <div>${device.tags.map(tag => `<span class="badge bg-secondary badge-sm me-1">${tag}</span>`).join('')}</div>
                    </div>
                </div>
                ` : ''}
                ${isCommissioning && workflowInfo ? `
                <div class="commissioning-progress mt-2">
                    <div class="progress mb-1" style="height: 6px;">
                        <div class="progress-bar progress-bar-striped progress-bar-animated bg-warning" 
                             style="width: ${workflowInfo.progress}%"></div>
                    </div>
                    <small class="text-muted">${workflowInfo.currentStep}</small>
                </div>
                ` : ''}
            </div>
            <div class="card-footer">
                <div class="d-grid gap-2">
                    <button class="btn btn-primary btn-sm" onclick="showDeviceDetails('${device.system_id}')">
                        <i class="bi bi-eye"></i> View Details
                    </button>
                    <button class="btn btn-success btn-sm" onclick="commissionDevice('${device.system_id}')" ${isCommissioning ? 'disabled' : ''}>
                        <i class="bi bi-play-circle"></i> ${isCommissioning ? 'Commissioning...' : 'Commission'}
                    </button>
                </div>
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
        case 'ready': return 'bg-success';
        case 'new': return 'bg-info';
        case 'failed testing': return 'bg-warning';
        case 'failed commissioning': return 'bg-danger';
        case 'deployed': return 'bg-primary';
        default: return 'bg-secondary';
    }
}

/**
 * Switch to card/masonry view
 */
function switchToCardView() {
    currentView = 'cards';
    document.getElementById('card-view-btn').classList.add('active');
    document.getElementById('list-view-btn').classList.remove('active');
    
    if (currentDevices.length > 0) {
        displayDevicesAsCards(currentDevices);
    }
}

/**
 * Switch to list/table view
 */
function switchToListView() {
    currentView = 'list';
    document.getElementById('list-view-btn').classList.add('active');
    document.getElementById('card-view-btn').classList.remove('active');
    
    if (currentDevices.length > 0) {
        displayDevicesAsList(currentDevices);
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
    
    console.log('Commission data:', commissionData);
    
    // Show progress in modal briefly
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
            const message = data.message || 'Device commissioning started successfully';
            showAlert(message, 'success');
            
            // Close modal immediately
            commissionModal.hide();
            
            // Start tracking progress for this device only if we have a valid workflow_id
            if (data.workflow_id && data.workflow_id !== null && data.workflow_id !== 'null') {
                startCommissioningProgressTracking(commissionData.system_id, data.workflow_id);
            } else {
                console.warn('No valid workflow_id returned from commissioning request:', data);
                // Still show that commissioning started, but without progress tracking
                updateDeviceCommissioningStatus(commissionData.system_id, 'Commissioning', 'Started...', 0);
            }
            
            // Refresh device list to show updated status
            loadDevices();
        } else {
            showAlert(`Failed to start commissioning: ${data.message}`, 'error');
            document.getElementById('commission-status').style.display = 'none';
            document.getElementById('start-commission').disabled = false;
        }
    })
    .catch(error => {
        console.error('Failed to commission device:', error);
        showAlert('Failed to start commissioning', 'error');
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

// Track commissioning workflows in progress
let commissioningWorkflows = new Map();

/**
 * Start tracking commissioning progress for a device
 */
function startCommissioningProgressTracking(systemId, workflowId) {
    // Validate inputs
    if (!systemId || !workflowId || workflowId === 'null' || workflowId === null) {
        console.error('Invalid parameters for progress tracking:', { systemId, workflowId });
        return;
    }
    
    console.log(`Starting progress tracking for device ${systemId}, workflow ${workflowId}`);
    
    // Store the workflow info
    commissioningWorkflows.set(systemId, {
        workflowId: workflowId,
        startTime: Date.now(),
        currentStep: 'Starting...',
        progress: 0
    });
    
    // Update device display immediately
    updateDeviceCommissioningStatus(systemId, 'Commissioning', 'Starting...', 0);
    
    // Start polling for progress
    pollWorkflowProgress(systemId, workflowId);
}

/**
 * Poll workflow progress
 */
function pollWorkflowProgress(systemId, workflowId) {
    // Validate inputs
    if (!workflowId || workflowId === 'null' || workflowId === null) {
        console.error('Cannot poll progress for invalid workflow ID:', workflowId);
        return;
    }
    
    fetch(`/api/orchestration/workflow/${workflowId}/status`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log(`Workflow ${workflowId} status:`, data);
            
            // Check for error response
            if (data.error) {
                console.error(`Workflow ${workflowId} error:`, data.error);
                updateDeviceCommissioningStatus(systemId, 'Error', data.error, 0);
                commissioningWorkflows.delete(systemId);
                return;
            }
            
            const workflowInfo = commissioningWorkflows.get(systemId);
            if (!workflowInfo) {
                console.log(`No tracking info found for system ${systemId}, stopping poll`);
                return;
            }
            
            // Calculate progress based on completed steps
            const totalSteps = data.steps ? data.steps.length : 8; // Default expected steps
            const completedSteps = data.steps ? data.steps.filter(step => 
                step.status === 'completed' || step.status === 'skipped'
            ).length : 0;
            const progress = Math.round((completedSteps / totalSteps) * 100);
            
            // Get current step info
            let currentStep = 'Processing...';
            let stepStatus = data.status || 'running';
            
            if (data.steps) {
                const runningStep = data.steps.find(step => step.status === 'running');
                const failedStep = data.steps.find(step => step.status === 'failed');
                
                if (failedStep) {
                    currentStep = `Failed: ${failedStep.name}`;
                    stepStatus = 'failed';
                } else if (runningStep) {
                    // Include sub-task information if available
                    if (data.current_sub_task) {
                        currentStep = `${runningStep.description || runningStep.name}: ${data.current_sub_task}`;
                    } else {
                        currentStep = runningStep.description || runningStep.name;
                    }
                } else if (completedSteps === totalSteps) {
                    currentStep = 'Completed';
                    stepStatus = 'completed';
                }
            } else if (data.current_sub_task) {
                // Fallback to sub-task if no step info
                currentStep = data.current_sub_task;
            }
            
            // Update workflow info
            workflowInfo.currentStep = currentStep;
            workflowInfo.progress = progress;
            
            // Update device display
            updateDeviceCommissioningStatus(systemId, 'Commissioning', currentStep, progress);
            
            // Check if workflow is complete
            if (stepStatus === 'completed' || stepStatus === 'failed' || stepStatus === 'cancelled') {
                console.log(`Workflow ${workflowId} finished with status: ${stepStatus}`);
                commissioningWorkflows.delete(systemId);
                
                // Refresh device list to get final status
                setTimeout(() => {
                    loadDevices();
                }, 2000);
                
                if (stepStatus === 'completed') {
                    showAlert(`Device ${systemId} commissioned successfully!`, 'success');
                } else if (stepStatus === 'failed') {
                    showAlert(`Device ${systemId} commissioning failed: ${currentStep}`, 'error');
                }
            } else {
                // Continue polling
                setTimeout(() => {
                    if (commissioningWorkflows.has(systemId)) {
                        pollWorkflowProgress(systemId, workflowId);
                    }
                }, 3000); // Poll every 3 seconds
            }
        })
        .catch(error => {
            console.error(`Error polling workflow ${workflowId}:`, error);
            
            // Update device status to show error
            const workflowInfo = commissioningWorkflows.get(systemId);
            if (workflowInfo) {
                updateDeviceCommissioningStatus(systemId, 'Error', `Polling failed: ${error.message}`, 0);
                
                // Stop tracking this workflow after several failed attempts
                if (!workflowInfo.errorCount) {
                    workflowInfo.errorCount = 0;
                }
                workflowInfo.errorCount++;
                
                if (workflowInfo.errorCount >= 3) {
                    console.log(`Stopping progress tracking for ${systemId} after ${workflowInfo.errorCount} failed attempts`);
                    commissioningWorkflows.delete(systemId);
                    showAlert(`Lost connection to workflow for device ${systemId}`, 'warning');
                    return;
                }
            }
            
            // Continue polling with longer interval on error (only if still tracking)
            setTimeout(() => {
                if (commissioningWorkflows.has(systemId)) {
                    pollWorkflowProgress(systemId, workflowId);
                }
            }, 10000); // Poll every 10 seconds on error
        });
}

/**
 * Update device commissioning status in the UI
 */
function updateDeviceCommissioningStatus(systemId, status, step, progress) {
    // Update card view
    const deviceCard = document.querySelector(`[data-system-id="${systemId}"] .card`);
    if (deviceCard) {
        const statusBadge = deviceCard.querySelector('.badge');
        const cardBody = deviceCard.querySelector('.card-body');
        
        if (statusBadge) {
            statusBadge.className = 'badge bg-warning';
            statusBadge.textContent = status;
        }
        
        // Add/update progress section
        let progressSection = cardBody.querySelector('.commissioning-progress');
        if (!progressSection) {
            progressSection = document.createElement('div');
            progressSection.className = 'commissioning-progress mt-2';
            cardBody.appendChild(progressSection);
        }
        
        progressSection.innerHTML = `
            <div class="progress mb-1" style="height: 6px;">
                <div class="progress-bar progress-bar-striped progress-bar-animated bg-warning" 
                     style="width: ${progress}%"></div>
            </div>
            <small class="text-muted">${step}</small>
        `;
    }
    
    // Update list view
    const listRow = document.querySelector(`tr[data-system-id="${systemId}"]`);
    if (listRow) {
        const statusBadge = listRow.querySelector('.status-badge');
        if (statusBadge) {
            statusBadge.className = 'badge bg-warning status-badge';
            statusBadge.textContent = status;
        }
        
        // Add progress to the status cell
        const statusCell = statusBadge.parentElement;
        let progressDiv = statusCell.querySelector('.commissioning-progress');
        if (!progressDiv) {
            progressDiv = document.createElement('div');
            progressDiv.className = 'commissioning-progress mt-1';
            statusCell.appendChild(progressDiv);
        }
        
        progressDiv.innerHTML = `
            <div class="progress" style="height: 4px;">
                <div class="progress-bar progress-bar-striped progress-bar-animated bg-warning" 
                     style="width: ${progress}%"></div>
            </div>
            <small class="text-muted d-block">${step}</small>
        `;
    }
}
