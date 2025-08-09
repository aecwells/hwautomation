/**
 * Notification Service for HWAutomation Frontend
 *
 * Manages user notifications with different types and persistence.
 * Provides toast notifications and persistent message management.
 */

class NotificationService {
    constructor() {
        this.notifications = [];
        this.container = null;
        this.maxNotifications = 5;
        this.defaultDuration = 5000; // 5 seconds
        this.isInitialized = false;
    }

    /**
     * Initialize notification service
     */
    async initialize() {
        if (this.isInitialized) {
            return;
        }

        this.createContainer();
        this.setupStyles();
        this.isInitialized = true;
    }

    /**
     * Show success notification
     */
    success(message, options = {}) {
        return this.show(message, 'success', options);
    }

    /**
     * Show error notification
     */
    error(message, options = {}) {
        return this.show(message, 'error', { duration: 0, ...options }); // Errors don't auto-dismiss
    }

    /**
     * Show warning notification
     */
    warning(message, options = {}) {
        return this.show(message, 'warning', options);
    }

    /**
     * Show info notification
     */
    info(message, options = {}) {
        return this.show(message, 'info', options);
    }

    /**
     * Show notification
     */
    show(message, type = 'info', options = {}) {
        const notification = {
            id: this.generateId(),
            message,
            type,
            timestamp: new Date(),
            duration: options.duration !== undefined ? options.duration : this.defaultDuration,
            persistent: options.persistent || false,
            dismissible: options.dismissible !== false
        };

        this.notifications.push(notification);
        this.renderNotification(notification);

        // Auto-dismiss if duration is set
        if (notification.duration > 0) {
            setTimeout(() => {
                this.dismiss(notification.id);
            }, notification.duration);
        }

        // Limit number of notifications
        if (this.notifications.length > this.maxNotifications) {
            const oldest = this.notifications.shift();
            this.removeFromDOM(oldest.id);
        }

        return notification.id;
    }

    /**
     * Dismiss notification by ID
     */
    dismiss(id) {
        const index = this.notifications.findIndex(n => n.id === id);
        if (index !== -1) {
            this.notifications.splice(index, 1);
            this.removeFromDOM(id);
        }
    }

    /**
     * Clear all notifications
     */
    clear() {
        this.notifications = [];
        if (this.container) {
            this.container.innerHTML = '';
        }
    }

    /**
     * Get all notifications
     */
    getAll() {
        return [...this.notifications];
    }

    /**
     * Create notification container
     */
    createContainer() {
        this.container = document.createElement('div');
        this.container.id = 'notification-container';
        this.container.className = 'notification-container';
        document.body.appendChild(this.container);
    }

    /**
     * Render notification in DOM
     */
    renderNotification(notification) {
        const element = document.createElement('div');
        element.id = `notification-${notification.id}`;
        element.className = `notification notification-${notification.type}`;

        const iconClass = this.getIconClass(notification.type);

        element.innerHTML = `
            <div class="notification-content">
                <i class="${iconClass}" aria-hidden="true"></i>
                <span class="notification-message">${this.escapeHtml(notification.message)}</span>
                ${notification.dismissible ? '<button class="notification-close" aria-label="Close">&times;</button>' : ''}
            </div>
        `;

        // Add click handlers
        if (notification.dismissible) {
            const closeBtn = element.querySelector('.notification-close');
            closeBtn.addEventListener('click', () => {
                this.dismiss(notification.id);
            });
        }

        // Add to container with animation
        this.container.appendChild(element);

        // Trigger animation
        requestAnimationFrame(() => {
            element.classList.add('notification-show');
        });
    }

    /**
     * Remove notification from DOM
     */
    removeFromDOM(id) {
        const element = document.getElementById(`notification-${id}`);
        if (element) {
            element.classList.add('notification-hide');
            setTimeout(() => {
                if (element.parentNode) {
                    element.parentNode.removeChild(element);
                }
            }, 300); // Match CSS transition duration
        }
    }

    /**
     * Get icon class for notification type
     */
    getIconClass(type) {
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        return icons[type] || icons.info;
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    /**
     * Generate unique ID
     */
    generateId() {
        return `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Setup notification styles
     */
    setupStyles() {
        const styleId = 'notification-service-styles';
        if (document.getElementById(styleId)) {
            return; // Styles already added
        }

        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            .notification-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                pointer-events: none;
            }

            .notification {
                background: white;
                border-left: 4px solid #007bff;
                border-radius: 6px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                margin-bottom: 10px;
                max-width: 400px;
                opacity: 0;
                pointer-events: auto;
                transform: translateX(100%);
                transition: all 0.3s ease;
            }

            .notification-show {
                opacity: 1;
                transform: translateX(0);
            }

            .notification-hide {
                opacity: 0;
                transform: translateX(100%);
            }

            .notification-content {
                align-items: center;
                display: flex;
                padding: 16px;
            }

            .notification-content i {
                font-size: 18px;
                margin-right: 12px;
                min-width: 18px;
            }

            .notification-message {
                flex: 1;
                font-size: 14px;
                line-height: 1.4;
            }

            .notification-close {
                background: none;
                border: none;
                color: #6c757d;
                cursor: pointer;
                font-size: 20px;
                line-height: 1;
                margin-left: 12px;
                opacity: 0.7;
                padding: 0;
            }

            .notification-close:hover {
                opacity: 1;
            }

            .notification-success {
                border-left-color: #198754;
            }

            .notification-success i {
                color: #198754;
            }

            .notification-error {
                border-left-color: #dc3545;
            }

            .notification-error i {
                color: #dc3545;
            }

            .notification-warning {
                border-left-color: #ffc107;
            }

            .notification-warning i {
                color: #ffc107;
            }

            .notification-info {
                border-left-color: #0dcaf0;
            }

            .notification-info i {
                color: #0dcaf0;
            }

            /* Dark theme support */
            [data-bs-theme="dark"] .notification {
                background: #2d3748;
                color: #e2e8f0;
            }

            [data-bs-theme="dark"] .notification-close {
                color: #a0aec0;
            }
        `;

        document.head.appendChild(style);
    }
}

export { NotificationService };
