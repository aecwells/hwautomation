/**
 * HWAutomation Frontend Application Core
 *
 * Main application entry point and initialization logic.
 * Manages global state, socket connections, and component coordination.
 */

// Import Bootstrap for bundling and global availability
import * as bootstrap from "bootstrap/dist/js/bootstrap.bundle.min.js";

// Make Bootstrap available globally for template JavaScript
// Do this immediately when the module loads
if (typeof window !== "undefined") {
  window.bootstrap = bootstrap;

  // Also ensure it's available in the global scope
  globalThis.bootstrap = bootstrap;

  console.log("✅ Bootstrap loaded and exposed globally");
}

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
    this.handleConnectError = this.handleConnectError.bind(this);
    this.handleReconnect = this.handleReconnect.bind(this);
    this.handleReconnectError = this.handleReconnectError.bind(this);
    this.handleReconnectFailed = this.handleReconnectFailed.bind(this);
    this.handleSubscribeWorkflow = this.handleSubscribeWorkflow.bind(this);
    this.handleWorkflowProgress = this.handleWorkflowProgress.bind(this);
    this.handleWorkflowStep = this.handleWorkflowStep.bind(this);
    this.handleWorkflowComplete = this.handleWorkflowComplete.bind(this);
    this.handleWorkflowUpdates = this.handleWorkflowUpdates.bind(this);
    this.handleActivityUpdate = this.handleActivityUpdate.bind(this);
    this.handleServerStatusUpdate = this.handleServerStatusUpdate.bind(this);
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

    this.socket = io({
      // Add connection options for better reliability
      transports: ["websocket", "polling"],
      upgrade: true,
      rememberUpgrade: true,
      timeout: 20000,
      forceNew: false,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      maxReconnectionAttempts: 5,
      randomizationFactor: 0.5,
    });

    // Connection events
    this.socket.on("connect", this.handleConnect);
    this.socket.on("disconnect", this.handleDisconnect);
    this.socket.on("connect_error", this.handleConnectError);
    this.socket.on("reconnect", this.handleReconnect);
    this.socket.on("reconnect_error", this.handleReconnectError);
    this.socket.on("reconnect_failed", this.handleReconnectFailed);

    // Workflow events
    this.socket.on("subscribe_workflow", this.handleSubscribeWorkflow);
    this.socket.on("workflow_progress_update", this.handleWorkflowProgress);
    this.socket.on("workflow_step_update", this.handleWorkflowStep);
    this.socket.on("workflow_complete", this.handleWorkflowComplete);
    this.socket.on("workflow_updates", this.handleWorkflowUpdates);

    // Activity and log events
    this.socket.on("activity_update", this.handleActivityUpdate);
    this.socket.on("server_status_update", this.handleServerStatusUpdate);

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
    this.services
      .get("notifications")
      .success("Connected to real-time updates");
    this.emit("socket:connected");
  }

  /**
   * Handle socket disconnection
   */
  handleDisconnect() {
    console.log("Disconnected from server");
    this.services.get("state").setState("socket.connected", false);
    this.services
      .get("notifications")
      .warning("Lost connection to real-time updates");
    this.emit("socket:disconnected");
  }

  /**
   * Handle socket connection error
   */
  handleConnectError(error) {
    console.error("Socket connection error:", error);
    this.services
      .get("notifications")
      .error("Failed to connect to real-time updates");
    this.emit("socket:connection-error", { error });
  }

  /**
   * Handle socket reconnection
   */
  handleReconnect(attemptNumber) {
    console.log(`Reconnected to server after ${attemptNumber} attempts`);
    this.services
      .get("notifications")
      .success("Reconnected to real-time updates");
    this.emit("socket:reconnected", { attemptNumber });
  }

  /**
   * Handle socket reconnection error
   */
  handleReconnectError(error) {
    console.error("Socket reconnection error:", error);
    this.emit("socket:reconnection-error", { error });
  }

  /**
   * Handle socket reconnection failure
   */
  handleReconnectFailed() {
    console.error("Socket reconnection failed permanently");
    this.services
      .get("notifications")
      .error(
        "Unable to restore real-time connection. Please refresh the page.",
      );
    this.emit("socket:reconnection-failed");
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
   * Handle workflow progress updates
   */
  handleWorkflowProgress(data) {
    console.log(`Workflow ${data.workflow_id} progress:`, data.progress);
    this.emit("workflow:progress", data);
  }

  /**
   * Handle workflow step updates
   */
  handleWorkflowStep(data) {
    console.log(`Workflow ${data.workflow_id} step:`, data.step);
    this.emit("workflow:step", data);
  }

  /**
   * Handle workflow completion
   */
  handleWorkflowComplete(data) {
    console.log(`Workflow ${data.workflow_id} completed:`, data.result);
    this.emit("workflow:complete", data);
  }

  /**
   * Handle workflow list updates
   */
  handleWorkflowUpdates(data) {
    console.log("Workflow list updated:", data);
    this.emit("workflows:updated", data);
  }

  /**
   * Handle activity updates
   */
  handleActivityUpdate(data) {
    console.log("Activity update:", data);
    this.emit("activity:update", data);
  }

  /**
   * Handle server status updates
   */
  handleServerStatusUpdate(data) {
    console.log("Server status update:", data);
    this.emit("server:status-update", data);
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
    for (const [, component] of this.components) {
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
