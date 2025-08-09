/**
 * Format Utilities for HWAutomation Frontend
 *
 * Common formatting functions for data display.
 */

/**
 * Format bytes to human readable format
 */
export function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    if (!bytes || isNaN(bytes)) return 'Unknown';

    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Format memory size (MB to human readable)
 */
export function formatMemory(memory) {
    if (!memory || isNaN(memory)) return 'Unknown';

    // Assume memory is in MB
    const bytes = memory * 1024 * 1024;
    return formatBytes(bytes);
}

/**
 * Format storage size (bytes to human readable)
 */
export function formatStorage(storage) {
    if (!storage || isNaN(storage)) return 'Unknown';
    return formatBytes(storage);
}

/**
 * Format duration in milliseconds to human readable
 */
export function formatDuration(ms) {
    if (!ms || isNaN(ms)) return 'Unknown';

    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) {
        return `${days}d ${hours % 24}h ${minutes % 60}m`;
    } else if (hours > 0) {
        return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
        return `${minutes}m ${seconds % 60}s`;
    } else {
        return `${seconds}s`;
    }
}

/**
 * Format timestamp to locale string
 */
export function formatTimestamp(timestamp, options = {}) {
    if (!timestamp) return 'Unknown';

    const date = new Date(timestamp);
    if (isNaN(date.getTime())) return 'Invalid Date';

    const defaultOptions = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };

    return date.toLocaleString(undefined, { ...defaultOptions, ...options });
}

/**
 * Format relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(timestamp) {
    if (!timestamp) return 'Unknown';

    const date = new Date(timestamp);
    if (isNaN(date.getTime())) return 'Invalid Date';

    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSeconds = Math.floor(diffMs / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSeconds < 60) {
        return 'Just now';
    } else if (diffMinutes < 60) {
        return `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
        return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else if (diffDays < 7) {
        return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    } else {
        return formatTimestamp(timestamp, { year: 'numeric', month: 'short', day: 'numeric' });
    }
}

/**
 * Format percentage
 */
export function formatPercentage(value, decimals = 1) {
    if (value === null || value === undefined || isNaN(value)) return 'Unknown';
    return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format number with thousand separators
 */
export function formatNumber(number, decimals = 0) {
    if (number === null || number === undefined || isNaN(number)) return 'Unknown';

    return number.toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

/**
 * Format IP address with validation
 */
export function formatIPAddress(ip) {
    if (!ip) return 'Unknown';

    // Basic IP validation
    const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/;
    const ipv6Regex = /^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/;

    if (ipv4Regex.test(ip) || ipv6Regex.test(ip)) {
        return ip;
    }

    return 'Invalid IP';
}

/**
 * Format MAC address
 */
export function formatMACAddress(mac) {
    if (!mac) return 'Unknown';

    // Remove any existing separators and convert to uppercase
    const cleanMac = mac.replace(/[:-]/g, '').toUpperCase();

    // Validate MAC address (12 hex characters)
    if (!/^[0-9A-F]{12}$/.test(cleanMac)) {
        return 'Invalid MAC';
    }

    // Format as XX:XX:XX:XX:XX:XX
    return cleanMac.match(/.{2}/g).join(':');
}

/**
 * Format CPU information
 */
export function formatCPU(cpuInfo) {
    if (!cpuInfo) return 'Unknown';

    if (typeof cpuInfo === 'number') {
        return `${cpuInfo} core${cpuInfo !== 1 ? 's' : ''}`;
    }

    if (typeof cpuInfo === 'object') {
        const cores = cpuInfo.cores || cpuInfo.count;
        const model = cpuInfo.model || cpuInfo.name;

        if (cores && model) {
            return `${cores}x ${model}`;
        } else if (cores) {
            return `${cores} core${cores !== 1 ? 's' : ''}`;
        } else if (model) {
            return model;
        }
    }

    return String(cpuInfo);
}

/**
 * Format status with appropriate styling
 */
export function formatStatus(status) {
    if (!status) return { text: 'Unknown', class: 'secondary' };

    const statusMap = {
        'ready': { text: 'Ready', class: 'success' },
        'commissioning': { text: 'Commissioning', class: 'warning' },
        'failed': { text: 'Failed', class: 'danger' },
        'deploying': { text: 'Deploying', class: 'info' },
        'deployed': { text: 'Deployed', class: 'primary' },
        'broken': { text: 'Broken', class: 'danger' },
        'retired': { text: 'Retired', class: 'secondary' },
        'allocated': { text: 'Allocated', class: 'primary' },
        'releasing': { text: 'Releasing', class: 'warning' }
    };

    const normalizedStatus = status.toLowerCase();
    return statusMap[normalizedStatus] || { text: status, class: 'secondary' };
}

/**
 * Format device type/architecture
 */
export function formatArchitecture(arch) {
    if (!arch) return 'Unknown';

    const archMap = {
        'amd64': 'x86_64',
        'i386': 'x86',
        'arm64': 'ARM64',
        'armhf': 'ARM',
        'ppc64el': 'PowerPC 64-bit',
        's390x': 'IBM Z'
    };

    return archMap[arch] || arch;
}

/**
 * Format JSON for display
 */
export function formatJSON(obj, indent = 2) {
    if (obj === null || obj === undefined) return 'null';

    try {
        return JSON.stringify(obj, null, indent);
    } catch (error) {
        return 'Invalid JSON';
    }
}

/**
 * Truncate text with ellipsis
 */
export function truncateText(text, maxLength = 50, suffix = '...') {
    if (!text || typeof text !== 'string') return text;

    if (text.length <= maxLength) return text;

    return text.substring(0, maxLength - suffix.length) + suffix;
}

/**
 * Capitalize first letter
 */
export function capitalize(text) {
    if (!text || typeof text !== 'string') return text;

    return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
}

/**
 * Convert camelCase to Title Case
 */
export function camelToTitle(camelCase) {
    if (!camelCase || typeof camelCase !== 'string') return camelCase;

    return camelCase
        .replace(/([A-Z])/g, ' $1')
        .replace(/^./, str => str.toUpperCase())
        .trim();
}

/**
 * Format error message for user display
 */
export function formatError(error) {
    if (!error) return 'Unknown error';

    if (typeof error === 'string') return error;

    if (error.message) return error.message;

    if (error.error) return error.error;

    return 'An unexpected error occurred';
}
