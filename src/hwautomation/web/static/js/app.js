/**
 * HWAutomation GUI JavaScript
 * Main application JavaScript for the web interface
 */

// Global variables
let socket;
let currentOperation = null;

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize the main application
 */
function initializeApp() {
    console.log('Initializing HWAutomation GUI...');
    
    // Initialize Socket.IO connection
    initializeSocket();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize event listeners
    initializeEventListeners();
    
    // Check connection status
    checkConnectionStatus();
    
    console.log('HWAutomation GUI initialized successfully');
}

/**
 * Initialize Socket.IO connection
 */
function initializeSocket() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to server');
        updateConnectionStatus(true);
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        updateConnectionStatus(false);
    });
    
    socket.on('config_progress', function(data) {
        handleProgressUpdate(data);
    });
    
    socket.on('connection_test', function(data) {
        handleConnectionTest(data);
    });
    
    socket.on('error', function(error) {
        console.error('Socket error:', error);
        showNotification('Connection error: ' + error, 'error');
    });
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize global event listeners
 */
function initializeEventListeners() {
    // Handle form submissions
    document.addEventListener('submit', function(e) {
        if (e.target.tagName === 'FORM') {
            e.preventDefault();
        }
    });
    
    // Handle escape key to close modals
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeActiveModals();
        }
    });
    
    // Handle window beforeunload
    window.addEventListener('beforeunload', function(e) {
        if (currentOperation) {
            e.preventDefault();
            e.returnValue = 'An operation is in progress. Are you sure you want to leave?';
            return e.returnValue;
        }
    });
}

/**
 * Update connection status indicator
 */
function updateConnectionStatus(connected) {
    const statusElement = document.getElementById('connection-status');
    if (statusElement) {
        if (connected) {
            statusElement.className = 'bi bi-circle-fill text-success';
            statusElement.parentElement.innerHTML = 
                '<i class="bi bi-circle-fill text-success" id="connection-status"></i> Connected';
        } else {
            statusElement.className = 'bi bi-circle-fill text-danger';
            statusElement.parentElement.innerHTML = 
                '<i class="bi bi-circle-fill text-danger" id="connection-status"></i> Disconnected';
        }
    }
}

/**
 * Check connection status periodically
 */
function checkConnectionStatus() {
    setInterval(function() {
        if (socket && socket.connected) {
            updateConnectionStatus(true);
        } else {
            updateConnectionStatus(false);
        }
    }, 5000);
}

/**
 * Handle progress updates from WebSocket
 */
function handleProgressUpdate(data) {
    console.log('Progress update:', data);
    
    const progressCard = document.getElementById('progressCard');
    const progressMessage = document.getElementById('progressMessage');
    const progressBar = document.getElementById('progressBar');
    
    if (!progressCard || !progressMessage || !progressBar) {
        return;
    }
    
    progressCard.style.display = 'block';
    progressMessage.textContent = data.message;
    
    // Update progress bar based on stage
    const stages = {
        'connecting': 20,
        'starting': 25,
        'pulling': 40,
        'applying': 60,
        'validating': 80,
        'pushing': 90,
        'complete': 100,
        'error': 100
    };
    
    const progress = stages[data.stage] || 50;
    progressBar.style.width = progress + '%';
    
    // Update progress bar color based on stage
    progressBar.className = 'progress-bar progress-bar-striped';
    if (data.stage === 'error') {
        progressBar.classList.add('bg-danger');
        progressCard.classList.remove('border-info');
        progressCard.classList.add('border-danger');
    } else if (data.stage === 'complete') {
        progressBar.classList.add('bg-success');
        progressBar.classList.remove('progress-bar-animated');
        progressCard.classList.remove('border-info');
        progressCard.classList.add('border-success');
    } else {
        progressBar.classList.add('bg-info', 'progress-bar-animated');
    }
}

/**
 * Handle connection test updates
 */
function handleConnectionTest(data) {
    handleProgressUpdate(data);
    
    if (data.stage === 'complete' || data.stage === 'error') {
        setTimeout(() => {
            hideProgress();
        }, 2000);
    }
}

/**
 * Show progress indicator
 */
function showProgress(message) {
    currentOperation = message;
    const progressCard = document.getElementById('progressCard');
    const progressMessage = document.getElementById('progressMessage');
    const progressBar = document.getElementById('progressBar');
    const resultsCard = document.getElementById('resultsCard');
    
    if (progressCard) {
        progressCard.style.display = 'block';
        progressCard.className = 'card border-info';
    }
    
    if (resultsCard) {
        resultsCard.style.display = 'none';
    }
    
    if (progressMessage) {
        progressMessage.textContent = message;
    }
    
    if (progressBar) {
        progressBar.style.width = '25%';
        progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-info';
    }
    
    // Scroll to progress card
    if (progressCard) {
        progressCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

/**
 * Hide progress indicator
 */
function hideProgress() {
    currentOperation = null;
    const progressCard = document.getElementById('progressCard');
    if (progressCard) {
        progressCard.style.display = 'none';
    }
}

/**
 * Show results
 */
function showResults(type, message, data) {
    const resultsCard = document.getElementById('resultsCard');
    const resultsContent = document.getElementById('resultsContent');
    
    if (!resultsCard || !resultsContent) {
        return;
    }
    
    let html = `<div class="alert alert-${type === 'success' ? 'success' : 'danger'} fade-in">
        <strong><i class="bi bi-${type === 'success' ? 'check-circle' : 'exclamation-triangle'}"></i> ${message}</strong>
    </div>`;
    
    // Add changes made
    if (data.changes_made && data.changes_made.length > 0) {
        html += '<div class="mt-3"><h6><i class="bi bi-list-check"></i> Changes Made:</h6><ul class="list-group">';
        data.changes_made.forEach(change => {
            html += `<li class="list-group-item d-flex align-items-center">
                <i class="bi bi-arrow-right text-success me-2"></i>${escapeHtml(change)}
            </li>`;
        });
        html += '</ul></div>';
    }
    
    // Add validation errors
    if (data.validation_errors && data.validation_errors.length > 0) {
        html += '<div class="mt-3"><h6><i class="bi bi-exclamation-triangle text-danger"></i> Validation Errors:</h6><ul class="list-group">';
        data.validation_errors.forEach(error => {
            html += `<li class="list-group-item list-group-item-danger d-flex align-items-center">
                <i class="bi bi-x-circle text-danger me-2"></i>${escapeHtml(error)}
            </li>`;
        });
        html += '</ul></div>';
    }
    
    // Add XML content
    if (data.xml) {
        html += `<div class="mt-3">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <h6><i class="bi bi-file-code"></i> Configuration XML:</h6>
                <button class="btn btn-sm btn-outline-secondary" onclick="copyToClipboard('xml-content-${Date.now()}')">
                    <i class="bi bi-clipboard"></i> Copy XML
                </button>
            </div>
            <pre id="xml-content-${Date.now()}" class="bg-light p-3" style="max-height: 300px; overflow-y: auto;">${escapeHtml(data.xml)}</pre>
        </div>`;
    }
    
    // Add error details
    if (data.error) {
        html += `<div class="mt-3">
            <h6><i class="bi bi-bug text-danger"></i> Error Details:</h6>
            <div class="alert alert-danger">${escapeHtml(data.error)}</div>
        </div>`;
    }
    
    // Add additional info
    if (data.target_ip) {
        html += `<div class="mt-3">
            <small class="text-muted">
                <i class="bi bi-info-circle"></i> Target: ${escapeHtml(data.target_ip)}
                ${data.device_type ? ` | Device Type: ${escapeHtml(data.device_type)}` : ''}
                ${data.dry_run ? ' | <strong>Dry Run Mode</strong>' : ''}
            </small>
        </div>`;
    }
    
    resultsContent.innerHTML = html;
    resultsCard.style.display = 'block';
    resultsCard.classList.add('fade-in');
    
    // Scroll to results
    resultsCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

/**
 * Show notification toast
 */
function showNotification(message, type = 'info', duration = 5000) {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
                ${escapeHtml(message)}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    // Add to toast container
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1200';
        document.body.appendChild(container);
    }
    
    container.appendChild(toast);
    
    // Show toast
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: duration
    });
    bsToast.show();
    
    // Remove from DOM after hiding
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    if (!element) {
        showNotification('Element not found', 'error');
        return;
    }
    
    const text = element.textContent || element.value;
    
    navigator.clipboard.writeText(text).then(function() {
        showNotification('Copied to clipboard!', 'success', 2000);
    }).catch(function(err) {
        console.error('Could not copy text: ', err);
        showNotification('Failed to copy to clipboard', 'error');
        
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showNotification('Copied to clipboard!', 'success', 2000);
        } catch (err) {
            showNotification('Copy not supported by browser', 'error');
        }
        document.body.removeChild(textArea);
    });
}

/**
 * Download text as file
 */
function downloadAsFile(content, filename, contentType = 'text/plain') {
    const blob = new Blob([content], { type: contentType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    showNotification(`Downloaded ${filename}`, 'success', 2000);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/**
 * Close all active modals
 */
function closeActiveModals() {
    const modals = document.querySelectorAll('.modal.show');
    modals.forEach(modal => {
        const bsModal = bootstrap.Modal.getInstance(modal);
        if (bsModal) {
            bsModal.hide();
        }
    });
}

/**
 * Format timestamp
 */
function formatTimestamp(isoString) {
    const date = new Date(isoString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

/**
 * Validate IP address
 */
function isValidIP(ip) {
    const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    return ipRegex.test(ip);
}

/**
 * Validate form before submission
 */
function validateForm(formElement) {
    const requiredFields = formElement.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
            
            // Additional validation for IP addresses
            if (field.type === 'text' && field.id.toLowerCase().includes('ip')) {
                if (!isValidIP(field.value.trim())) {
                    field.classList.add('is-invalid');
                    isValid = false;
                }
            }
        }
    });
    
    return isValid;
}

/**
 * Auto-resize textarea elements
 */
function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

/**
 * Initialize auto-resize for all textareas
 */
function initializeAutoResize() {
    const textareas = document.querySelectorAll('textarea[data-auto-resize]');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            autoResizeTextarea(this);
        });
        autoResizeTextarea(textarea);
    });
}

// Initialize auto-resize when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeAutoResize);

/**
 * Enhanced theme management functions
 */
function initializeThemeSupport() {
    // Initialize theme-aware elements on page load
    updateThemeAwareElements();
    
    // Listen for theme changes
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'data-bs-theme') {
                updateThemeAwareElements();
                handleThemeChange();
            }
        });
    });
    
    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-bs-theme']
    });
}

function updateThemeAwareElements() {
    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    
    // Update spinners
    const spinners = document.querySelectorAll('.spinner-border');
    spinners.forEach(spinner => {
        if (spinner.classList.contains('text-primary')) {
            spinner.className = isDark ? 'spinner-border text-light' : 'spinner-border text-primary';
        }
    });
    
    // Update status indicators
    const statusElements = document.querySelectorAll('[data-theme-aware="true"]');
    statusElements.forEach(element => {
        if (element.hasAttribute('data-theme-light-class')) {
            const lightClass = element.getAttribute('data-theme-light-class');
            const darkClass = element.getAttribute('data-theme-dark-class');
            element.className = isDark ? darkClass : lightClass;
        }
    });
    
    // Update table striping
    const tables = document.querySelectorAll('.table-striped');
    tables.forEach(table => {
        // Force re-render of striped tables
        table.classList.remove('table-striped');
        setTimeout(() => table.classList.add('table-striped'), 10);
    });
}

function handleThemeChange() {
    // Emit custom event for components that need to respond to theme changes
    const themeChangeEvent = new CustomEvent('themeChanged', {
        detail: {
            theme: document.documentElement.getAttribute('data-bs-theme')
        }
    });
    document.dispatchEvent(themeChangeEvent);
    
    // Update any charts or visualizations
    if (typeof updateChartsTheme === 'function') {
        updateChartsTheme();
    }
    
    // Update any code syntax highlighting
    if (typeof updateSyntaxHighlighting === 'function') {
        updateSyntaxHighlighting();
    }
}

function applyThemeToElement(element, theme) {
    // Apply theme-specific classes to dynamically created elements
    if (theme === 'dark') {
        element.classList.add('theme-dark');
        element.classList.remove('theme-light');
    } else {
        element.classList.add('theme-light');
        element.classList.remove('theme-dark');
    }
}

function createThemeAwareElement(tagName, options = {}) {
    const element = document.createElement(tagName);
    const currentTheme = document.documentElement.getAttribute('data-bs-theme');
    
    // Apply base classes
    if (options.classes) {
        element.className = options.classes;
    }
    
    // Apply theme-aware styling
    applyThemeToElement(element, currentTheme);
    
    // Set content if provided
    if (options.content) {
        element.textContent = options.content;
    }
    
    if (options.html) {
        element.innerHTML = options.html;
    }
    
    return element;
}

// Initialize theme support when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeThemeSupport);

// Export functions for global use
window.hwautomation = {
    showProgress,
    hideProgress,
    showResults,
    showNotification,
    copyToClipboard,
    downloadAsFile,
    escapeHtml,
    isValidIP,
    validateForm,
    formatTimestamp,
    // Theme support functions
    updateThemeAwareElements,
    handleThemeChange,
    applyThemeToElement,
    createThemeAwareElement
};
