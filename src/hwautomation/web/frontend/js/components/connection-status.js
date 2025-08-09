/**
 * Connection Status Component
 *
 * Displays and manages connection status indicators for WebSocket and API.
 * Updates UI elements to show current connection state.
 */

class ConnectionStatus {
    constructor(stateManager) {
        this.stateManager = stateManager;
        this.isInitialized = false;
        this.statusIndicators = [];
        this.unsubscribers = [];
    }

    /**
     * Initialize connection status component
     */
    async initialize() {
        if (this.isInitialized) {
            return;
        }

        // Find status indicator elements
        this.findStatusIndicators();

        // Subscribe to connection state changes
        this.setupStateSubscriptions();

        // Initial status update
        this.updateStatus();

        this.isInitialized = true;
    }

    /**
     * Find status indicator elements in the DOM
     */
    findStatusIndicators() {
        // Look for existing status indicators
        this.statusIndicators = [
            ...document.querySelectorAll('[data-connection-status]'),
            ...document.querySelectorAll('.connection-status'),
            ...document.querySelectorAll('.connection-status-small')
        ];

        // If no indicators found, try to create one
        if (this.statusIndicators.length === 0) {
            this.createStatusIndicator();
        }
    }

    /**
     * Create a status indicator if none exists
     */
    createStatusIndicator() {
        // Look for navbar brand to add status
        const navbarBrand = document.querySelector('.navbar-brand-container');

        if (navbarBrand) {
            const statusElement = document.createElement('div');
            statusElement.className = 'connection-status-small';
            statusElement.innerHTML = `
                <i class="fas fa-circle" data-connection-icon></i>
                <span data-connection-text>Connecting...</span>
            `;

            navbarBrand.appendChild(statusElement);
            this.statusIndicators.push(statusElement);
        }
    }

    /**
     * Setup state subscriptions
     */
    setupStateSubscriptions() {
        // Subscribe to socket connection state
        const socketUnsub = this.stateManager.subscribe('socket.connected', () => {
            this.updateStatus();
        });

        // Subscribe to API health state
        const apiUnsub = this.stateManager.subscribe('api.healthy', () => {
            this.updateStatus();
        });

        this.unsubscribers.push(socketUnsub, apiUnsub);
    }

    /**
     * Update status indicators
     */
    updateStatus() {
        const socketConnected = this.stateManager.getState('socket.connected', false);
        const apiHealthy = this.stateManager.getState('api.healthy', false);

        const status = this.determineOverallStatus(socketConnected, apiHealthy);

        this.statusIndicators.forEach(indicator => {
            this.updateIndicator(indicator, status);
        });

        // Emit status change event
        const event = new CustomEvent('connection:status-changed', {
            detail: {
                status,
                socketConnected,
                apiHealthy
            }
        });
        document.dispatchEvent(event);
    }

    /**
     * Determine overall connection status
     */
    determineOverallStatus(socketConnected, apiHealthy) {
        if (socketConnected && apiHealthy) {
            return {
                level: 'connected',
                text: 'Connected',
                icon: 'fas fa-circle text-success',
                color: 'success'
            };
        } else if (apiHealthy) {
            return {
                level: 'api-only',
                text: 'API Connected',
                icon: 'fas fa-circle text-warning',
                color: 'warning'
            };
        } else if (socketConnected) {
            return {
                level: 'socket-only',
                text: 'Limited Connection',
                icon: 'fas fa-circle text-warning',
                color: 'warning'
            };
        } else {
            return {
                level: 'disconnected',
                text: 'Disconnected',
                icon: 'fas fa-circle text-danger',
                color: 'danger'
            };
        }
    }

    /**
     * Update individual status indicator
     */
    updateIndicator(indicator, status) {
        // Update icon
        const iconElement = indicator.querySelector('[data-connection-icon], i');
        if (iconElement) {
            iconElement.className = status.icon;
        }

        // Update text
        const textElement = indicator.querySelector('[data-connection-text], .connection-text');
        if (textElement) {
            textElement.textContent = status.text;
        }

        // Update classes
        indicator.classList.remove(
            'connection-connected',
            'connection-api-only',
            'connection-socket-only',
            'connection-disconnected'
        );
        indicator.classList.add(`connection-${status.level}`);

        // Update data attribute
        indicator.setAttribute('data-connection-status', status.level);

        // Update title for tooltips
        indicator.title = this.getDetailedStatusText(status);
    }

    /**
     * Get detailed status text for tooltips
     */
    getDetailedStatusText(status) {
        const details = {
            connected: 'Full connection established - WebSocket and API are both healthy',
            'api-only': 'API connection established - WebSocket connection unavailable',
            'socket-only': 'WebSocket connected - API health check failed',
            disconnected: 'No connection - Both WebSocket and API are unavailable'
        };

        return details[status.level] || status.text;
    }

    /**
     * Force status refresh
     */
    refresh() {
        this.updateStatus();
    }

    /**
     * Get current connection status
     */
    getCurrentStatus() {
        const socketConnected = this.stateManager.getState('socket.connected', false);
        const apiHealthy = this.stateManager.getState('api.healthy', false);
        return this.determineOverallStatus(socketConnected, apiHealthy);
    }

    /**
     * Check if fully connected
     */
    isConnected() {
        return this.getCurrentStatus().level === 'connected';
    }

    /**
     * Check if API is available
     */
    isApiAvailable() {
        return this.stateManager.getState('api.healthy', false);
    }

    /**
     * Check if WebSocket is connected
     */
    isSocketConnected() {
        return this.stateManager.getState('socket.connected', false);
    }

    /**
     * Clean up component
     */
    destroy() {
        // Unsubscribe from state changes
        this.unsubscribers.forEach(unsub => unsub());
        this.unsubscribers = [];

        this.isInitialized = false;
    }
}

export { ConnectionStatus };
