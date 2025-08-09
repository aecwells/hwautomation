/**
 * HWAutomation Frontend Application Core
 *
 * Main application entry point and initialization logic.
 * Manages global state, socket connections, and component coordination.
 */

class HWAutomationApp {
  constructor() {
    this.socket = null;
    this.currentOperation = null;
    this.components = new Map();
    this.services = new Map();
    this.isInitialized = false;

    // Bind methods to preserve context
    this.handleConnect = this.handleConnect.bind(this);
    this.handleDisconnect = this.handleDisconnect.bind(this);
    this.handleSubscribeWorkflow = this.handleSubscribeWorkflow.bind(this);
  }

  /**
   * Initialize the application
   */
  async initialize() {
    if (this.isInitialized) {
      console.warn("Application already initialized");
      return;
    }

    console.log("Initializing HWAutomation Frontend...");

    try {
      // Initialize core services
      await this.initializeServices();

      // Initialize Socket.IO connection
      this.initializeSocket();

      // Initialize UI components
      await this.initializeComponents();

      // Initialize global event listeners
      this.initializeEventListeners();

      // Check initial connection status
      this.checkConnectionStatus();

      this.isInitialized = true;
      console.log("HWAutomation Frontend initialized successfully");

      // Emit initialization complete event
      this.emit("app:initialized");
    } catch (error) {
      console.error("Failed to initialize application:", error);
      throw error;
    }
  }

  /**
   * Initialize core services
   */
  async initializeServices() {
    const { ApiService } = await import("../services/api.js");
    const { StateManager } = await import("../services/state.js");
    const { NotificationService } = await import(
      "../services/notifications.js"
    );

    // Initialize services
    this.services.set("api", new ApiService());
    this.services.set("state", new StateManager());
    this.services.set("notifications", new NotificationService());

    // Initialize services
    await this.services.get("state").initialize();
    await this.services.get("notifications").initialize();
  }

  /**
   * Initialize UI components
   */
  async initializeComponents() {
    // Initialize tooltips
    this.initializeTooltips();

    // Initialize theme manager
    const { ThemeManager } = await import("../components/theme-manager.js");
    const themeManager = new ThemeManager();
    await themeManager.initialize();
    this.components.set("theme", themeManager);

    // Initialize connection status component
    const { ConnectionStatus } = await import(
      "../components/connection-status.js"
    );
    const connectionStatus = new ConnectionStatus(this.services.get("state"));
    await connectionStatus.initialize();
    this.components.set("connectionStatus", connectionStatus);
  }

  /**
   * Initialize Socket.IO connection
   */
  initializeSocket() {
    if (!window.io) {
      console.error("Socket.IO not available");
      return;
    }

    this.socket = io();

    this.socket.on("connect", this.handleConnect);
    this.socket.on("disconnect", this.handleDisconnect);
    this.socket.on("subscribe_workflow", this.handleSubscribeWorkflow);

    // Store socket in services for other components
    this.services.set("socket", this.socket);
  }

  /**
   * Initialize global event listeners
   */
  initializeEventListeners() {
    // Global error handler
    window.addEventListener("error", (event) => {
      console.error("Global error:", event.error);
      this.services
        .get("notifications")
        .error(
          "An unexpected error occurred. Please refresh the page if issues persist.",
        );
    });

    // Unhandled promise rejection handler
    window.addEventListener("unhandledrejection", (event) => {
      console.error("Unhandled promise rejection:", event.reason);
      this.services
        .get("notifications")
        .error(
          "An unexpected error occurred. Please refresh the page if issues persist.",
        );
    });
  }

  /**
   * Initialize Bootstrap tooltips
   */
  initializeTooltips() {
    if (typeof bootstrap !== "undefined" && bootstrap.Tooltip) {
      const tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]'),
      );
      tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
      });
    }
  }

  /**
   * Handle socket connection
   */
  handleConnect() {
    console.log("Connected to server");
    this.services.get("state").setState("socket.connected", true);
    this.emit("socket:connected");
  }

  /**
   * Handle socket disconnection
   */
  handleDisconnect() {
    console.log("Disconnected from server");
    this.services.get("state").setState("socket.connected", false);
    this.emit("socket:disconnected");
  }

  /**
   * Handle workflow subscription
   */
  handleSubscribeWorkflow(data) {
    const workflowId = data.workflow_id;
    console.log(`Client subscribed to workflow ${workflowId}`);
    this.emit("workflow:subscribed", { workflowId });
  }

  /**
   * Check connection status
   */
  async checkConnectionStatus() {
    try {
      const response = await this.services.get("api").get("/health");
      const isHealthy = response.status === "healthy";
      this.services.get("state").setState("api.healthy", isHealthy);
    } catch (error) {
      console.error("Health check failed:", error);
      this.services.get("state").setState("api.healthy", false);
    }
  }

  /**
   * Get a service by name
   */
  getService(name) {
    return this.services.get(name);
  }

  /**
   * Get a component by name
   */
  getComponent(name) {
    return this.components.get(name);
  }

  /**
   * Register a component
   */
  registerComponent(name, component) {
    this.components.set(name, component);
  }

  /**
   * Emit an event to all registered components
   */
  emit(eventName, data = {}) {
    const event = new CustomEvent(eventName, { detail: data });
    document.dispatchEvent(event);
  }

  /**
   * Clean up resources
   */
  destroy() {
    if (this.socket) {
      this.socket.disconnect();
    }

    // Destroy all components
    for (const [name, component] of this.components) {
      if (component.destroy) {
        component.destroy();
      }
    }

    // Clear collections
    this.components.clear();
    this.services.clear();

    this.isInitialized = false;
  }
}

// Create global app instance
window.HWAutomationApp = new HWAutomationApp();

// Initialize when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    window.HWAutomationApp.initialize().catch(console.error);
  });
} else {
  // DOM already loaded
  window.HWAutomationApp.initialize().catch(console.error);
}

export { HWAutomationApp };
