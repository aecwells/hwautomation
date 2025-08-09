/**
 * API Service for HWAutomation Frontend
 *
 * Centralized HTTP client for all API interactions.
 * Provides consistent error handling and request/response processing.
 */

class ApiService {
  constructor(baseUrl = "") {
    this.baseUrl = baseUrl;
    this.defaultHeaders = {
      "Content-Type": "application/json",
      "X-Requested-With": "XMLHttpRequest",
    };
  }

  /**
   * Make a GET request
   */
  async get(url, options = {}) {
    return this.request("GET", url, null, options);
  }

  /**
   * Make a POST request
   */
  async post(url, data = null, options = {}) {
    return this.request("POST", url, data, options);
  }

  /**
   * Make a PUT request
   */
  async put(url, data = null, options = {}) {
    return this.request("PUT", url, data, options);
  }

  /**
   * Make a DELETE request
   */
  async delete(url, options = {}) {
    return this.request("DELETE", url, null, options);
  }

  /**
   * Make a PATCH request
   */
  async patch(url, data = null, options = {}) {
    return this.request("PATCH", url, data, options);
  }

  /**
   * Generic request method
   */
  async request(method, url, data = null, options = {}) {
    const fullUrl = this.buildUrl(url);
    const headers = { ...this.defaultHeaders, ...(options.headers || {}) };

    const config = {
      method,
      headers,
      ...options,
    };

    if (data) {
      if (headers["Content-Type"] === "application/json") {
        config.body = JSON.stringify(data);
      } else {
        config.body = data;
      }
    }

    try {
      const response = await fetch(fullUrl, config);
      return await this.handleResponse(response);
    } catch (error) {
      console.error(`API request failed: ${method} ${fullUrl}`, error);
      throw new ApiError(`Request failed: ${error.message}`, null, error);
    }
  }

  /**
   * Handle API response
   */
  async handleResponse(response) {
    const contentType = response.headers.get("content-type");
    const isJson = contentType && contentType.includes("application/json");

    let data;
    try {
      data = isJson ? await response.json() : await response.text();
    } catch (error) {
      data = null;
    }

    if (!response.ok) {
      const message =
        data?.error ||
        data?.message ||
        `HTTP ${response.status}: ${response.statusText}`;
      throw new ApiError(message, response.status, data);
    }

    return data;
  }

  /**
   * Build full URL from relative path
   */
  buildUrl(path) {
    if (path.startsWith("http://") || path.startsWith("https://")) {
      return path;
    }

    const base = this.baseUrl || window.location.origin;
    const cleanBase = base.replace(/\/$/, "");
    const cleanPath = path.replace(/^\//, "");

    return `${cleanBase}/${cleanPath}`;
  }

  /**
   * Set default header
   */
  setHeader(name, value) {
    this.defaultHeaders[name] = value;
  }

  /**
   * Remove default header
   */
  removeHeader(name) {
    delete this.defaultHeaders[name];
  }

  /**
   * Set correlation ID for requests
   */
  setCorrelationId(correlationId) {
    this.setHeader("X-Correlation-ID", correlationId);
  }
}

/**
 * Custom API Error class
 */
class ApiError extends Error {
  constructor(message, status = null, data = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }

  /**
   * Check if error is a specific HTTP status
   */
  isStatus(status) {
    return this.status === status;
  }

  /**
   * Check if error is a client error (4xx)
   */
  isClientError() {
    return this.status >= 400 && this.status < 500;
  }

  /**
   * Check if error is a server error (5xx)
   */
  isServerError() {
    return this.status >= 500;
  }
}

export { ApiService, ApiError };
