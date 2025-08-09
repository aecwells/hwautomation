/**
 * Device Selection Component
 *
 * Manages device listing, filtering, and selection functionality.
 * Modular replacement for the monolithic device-selection.js file.
 */

class DeviceSelectionComponent {
  constructor() {
    this.currentDevices = [];
    this.selectedDevice = null;
    this.deviceDetailsModal = null;
    this.commissionModal = null;
    this.currentView = "cards";
    this.masonryInstance = null;
    this.isInitialized = false;

    // Services
    this.apiService = null;
    this.stateManager = null;
    this.notificationService = null;

    // DOM elements
    this.elements = {};
  }

  /**
   * Initialize device selection component
   */
  async initialize() {
    if (this.isInitialized) {
      return;
    }

    // Get services
    const app = window.HWAutomationApp;
    this.apiService = app.getService("api");
    this.stateManager = app.getService("state");
    this.notificationService = app.getService("notifications");

    // Find DOM elements
    this.findElements();

    // Initialize modals
    this.initializeModals();

    // Setup event listeners
    this.setupEventListeners();

    // Initialize view from state
    this.currentView = this.stateManager.getState(
      "devices.currentView",
      "cards",
    );
    this.applyView();

    // Load initial devices
    await this.loadDevices();

    this.isInitialized = true;
    console.log("Device Selection Component initialized");
  }

  /**
   * Find required DOM elements
   */
  findElements() {
    const elementIds = [
      "deviceDetailsModal",
      "commissionModal",
      "device-filter-form",
      "clear-filters",
      "refresh-devices",
      "commission-form",
      "device-cards-container",
      "device-list-container",
      "device-list-tbody",
      "view-toggle-cards",
      "view-toggle-list",
    ];

    elementIds.forEach((id) => {
      this.elements[id] = document.getElementById(id);
    });

    // Log missing elements for debugging
    const missing = elementIds.filter((id) => !this.elements[id]);
    if (missing.length > 0) {
      console.warn("Missing device selection elements:", missing);
    }
  }

  /**
   * Initialize Bootstrap modals
   */
  initializeModals() {
    if (this.elements.deviceDetailsModal && this.elements.commissionModal) {
      if (typeof bootstrap !== "undefined") {
        this.deviceDetailsModal = new bootstrap.Modal(
          this.elements.deviceDetailsModal,
        );
        this.commissionModal = new bootstrap.Modal(
          this.elements.commissionModal,
        );
      } else {
        console.warn("Bootstrap not available for modals");
      }
    }
  }

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Refresh devices button
    if (this.elements["refresh-devices"]) {
      this.elements["refresh-devices"].addEventListener("click", () => {
        this.loadDevices();
      });
    }

    // Clear filters button
    if (this.elements["clear-filters"]) {
      this.elements["clear-filters"].addEventListener("click", () => {
        this.clearFilters();
      });
    }

    // Filter form
    if (this.elements["device-filter-form"]) {
      this.elements["device-filter-form"].addEventListener("submit", (e) => {
        e.preventDefault();
        this.applyFilters();
      });
    }

    // View toggle buttons
    if (this.elements["view-toggle-cards"]) {
      this.elements["view-toggle-cards"].addEventListener("click", () => {
        this.setView("cards");
      });
    }

    if (this.elements["view-toggle-list"]) {
      this.elements["view-toggle-list"].addEventListener("click", () => {
        this.setView("list");
      });
    }

    // Commission form
    if (this.elements["commission-form"]) {
      this.elements["commission-form"].addEventListener("submit", (e) => {
        e.preventDefault();
        this.submitCommission();
      });
    }
  }

  /**
   * Load devices from API
   */
  async loadDevices() {
    try {
      this.showLoading(true);

      const response = await this.apiService.get("/api/maas/machines");

      if (response && response.machines) {
        this.currentDevices = response.machines;
        this.renderDevices();
        this.notificationService.success(
          `Loaded ${this.currentDevices.length} devices`,
        );
      } else {
        this.currentDevices = [];
        this.renderDevices();
        this.notificationService.warning("No devices found");
      }
    } catch (error) {
      console.error("Failed to load devices:", error);
      this.notificationService.error(
        "Failed to load devices: " + error.message,
      );
      this.currentDevices = [];
      this.renderDevices();
    } finally {
      this.showLoading(false);
    }
  }

  /**
   * Render devices in current view
   */
  renderDevices() {
    if (this.currentView === "cards") {
      this.renderCardsView();
    } else {
      this.renderListView();
    }

    // Update state
    this.stateManager.setState("devices.list", this.currentDevices);
  }

  /**
   * Render devices in cards view
   */
  renderCardsView() {
    const container = this.elements["device-cards-container"];
    if (!container) return;

    container.innerHTML = "";

    if (this.currentDevices.length === 0) {
      container.innerHTML =
        '<div class="col-12"><div class="alert alert-info">No devices found</div></div>';
      return;
    }

    this.currentDevices.forEach((device) => {
      const deviceCard = this.createDeviceCard(device);
      container.appendChild(deviceCard);
    });

    // Initialize masonry if available
    this.initializeMasonry();
  }

  /**
   * Render devices in list view
   */
  renderListView() {
    const tbody = this.elements["device-list-tbody"];
    if (!tbody) return;

    tbody.innerHTML = "";

    if (this.currentDevices.length === 0) {
      tbody.innerHTML =
        '<tr><td colspan="8" class="text-center">No devices found</td></tr>';
      return;
    }

    this.currentDevices.forEach((device) => {
      const row = this.createDeviceRow(device);
      tbody.appendChild(row);
    });
  }

  /**
   * Create device card element
   */
  createDeviceCard(device) {
    const col = document.createElement("div");
    col.className = "col-md-6 col-lg-4 mb-3";

    const statusClass = this.getStatusClass(device.status);
    const statusIcon = this.getStatusIcon(device.status);

    col.innerHTML = `
            <div class="card device-card h-100" data-device-id="${device.system_id}">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="card-title mb-0">${this.escapeHtml(device.hostname || "Unknown")}</h6>
                    <span class="badge ${statusClass}">
                        <i class="${statusIcon}"></i> ${device.status}
                    </span>
                </div>
                <div class="card-body">
                    <div class="device-info">
                        <div class="row">
                            <div class="col-6"><strong>Architecture:</strong></div>
                            <div class="col-6">${device.architecture || "Unknown"}</div>
                        </div>
                        <div class="row">
                            <div class="col-6"><strong>CPU:</strong></div>
                            <div class="col-6">${device.cpu_count || "Unknown"} cores</div>
                        </div>
                        <div class="row">
                            <div class="col-6"><strong>Memory:</strong></div>
                            <div class="col-6">${this.formatMemory(device.memory)}</div>
                        </div>
                        <div class="row">
                            <div class="col-6"><strong>Storage:</strong></div>
                            <div class="col-6">${this.formatStorage(device.storage)}</div>
                        </div>
                    </div>
                </div>
                <div class="card-footer">
                    <div class="btn-group w-100" role="group">
                        <button class="btn btn-outline-primary btn-sm" onclick="deviceSelection.showDeviceDetails('${device.system_id}')">
                            <i class="fas fa-info-circle"></i> Details
                        </button>
                        ${
                          device.status === "Ready"
                            ? `
                            <button class="btn btn-primary btn-sm" onclick="deviceSelection.selectForCommissioning('${device.system_id}')">
                                <i class="fas fa-cogs"></i> Commission
                            </button>
                        `
                            : ""
                        }
                    </div>
                </div>
            </div>
        `;

    return col;
  }

  /**
   * Create device table row
   */
  createDeviceRow(device) {
    const row = document.createElement("tr");
    row.setAttribute("data-device-id", device.system_id);

    const statusClass = this.getStatusClass(device.status);
    const statusIcon = this.getStatusIcon(device.status);

    row.innerHTML = `
            <td>
                <input type="checkbox" class="device-checkbox" value="${device.system_id}"
                       ${device.status !== "Ready" ? "disabled" : ""}>
            </td>
            <td>${this.escapeHtml(device.hostname || "Unknown")}</td>
            <td>
                <span class="badge ${statusClass}">
                    <i class="${statusIcon}"></i> ${device.status}
                </span>
            </td>
            <td>${device.architecture || "Unknown"}</td>
            <td>${device.cpu_count || "Unknown"}</td>
            <td>${this.formatMemory(device.memory)}</td>
            <td>${this.formatStorage(device.storage)}</td>
            <td>
                <div class="btn-group btn-group-sm" role="group">
                    <button class="btn btn-outline-primary" onclick="deviceSelection.showDeviceDetails('${device.system_id}')">
                        <i class="fas fa-info-circle"></i>
                    </button>
                    ${
                      device.status === "Ready"
                        ? `
                        <button class="btn btn-primary" onclick="deviceSelection.selectForCommissioning('${device.system_id}')">
                            <i class="fas fa-cogs"></i>
                        </button>
                    `
                        : ""
                    }
                </div>
            </td>
        `;

    return row;
  }

  /**
   * Show device details modal
   */
  async showDeviceDetails(deviceId) {
    const device = this.currentDevices.find((d) => d.system_id === deviceId);
    if (!device || !this.deviceDetailsModal) return;

    try {
      // Load detailed device information
      const details = await this.apiService.get(
        `/api/maas/machines/${deviceId}`,
      );

      // Populate modal with device details
      this.populateDeviceDetailsModal(details);

      // Show modal
      this.deviceDetailsModal.show();
    } catch (error) {
      console.error("Failed to load device details:", error);
      this.notificationService.error("Failed to load device details");
    }
  }

  /**
   * Select device for commissioning
   */
  selectForCommissioning(deviceId) {
    const device = this.currentDevices.find((d) => d.system_id === deviceId);
    if (!device || !this.commissionModal) return;

    this.selectedDevice = device;
    this.stateManager.setState("devices.selectedDevice", device);

    // Populate commission modal
    this.populateCommissionModal(device);

    // Show modal
    this.commissionModal.show();
  }

  /**
   * Set current view (cards or list)
   */
  setView(view) {
    if (view !== "cards" && view !== "list") return;

    this.currentView = view;
    this.stateManager.setState("devices.currentView", view);
    this.applyView();
    this.renderDevices();
  }

  /**
   * Apply current view to UI
   */
  applyView() {
    // Update view toggle buttons
    const cardsBtn = this.elements["view-toggle-cards"];
    const listBtn = this.elements["view-toggle-list"];

    if (cardsBtn && listBtn) {
      cardsBtn.classList.toggle("active", this.currentView === "cards");
      listBtn.classList.toggle("active", this.currentView === "list");
    }

    // Show/hide view containers
    const cardsContainer = this.elements["device-cards-container"]?.closest(
      ".devices-cards-view",
    );
    const listContainer =
      this.elements["device-list-container"]?.closest(".devices-list-view");

    if (cardsContainer) {
      cardsContainer.style.display =
        this.currentView === "cards" ? "block" : "none";
    }

    if (listContainer) {
      listContainer.style.display =
        this.currentView === "list" ? "block" : "none";
    }
  }

  /**
   * Apply filters to device list
   */
  applyFilters() {
    // Implementation for filtering logic
    // This would read form values and filter this.currentDevices
    console.log("Applying filters...");
    // TODO: Implement filtering logic
  }

  /**
   * Clear all filters
   */
  clearFilters() {
    const form = this.elements["device-filter-form"];
    if (form) {
      form.reset();
      this.applyFilters();
    }
  }

  /**
   * Show/hide loading indicator
   */
  showLoading(show) {
    const indicators = document.querySelectorAll(".device-loading");
    indicators.forEach((indicator) => {
      indicator.style.display = show ? "block" : "none";
    });
  }

  /**
   * Utility methods
   */
  getStatusClass(status) {
    const statusClasses = {
      Ready: "bg-success",
      Commissioning: "bg-warning",
      Failed: "bg-danger",
      Deploying: "bg-info",
      Deployed: "bg-primary",
    };
    return statusClasses[status] || "bg-secondary";
  }

  getStatusIcon(status) {
    const statusIcons = {
      Ready: "fas fa-check",
      Commissioning: "fas fa-spinner fa-spin",
      Failed: "fas fa-exclamation-triangle",
      Deploying: "fas fa-download",
      Deployed: "fas fa-server",
    };
    return statusIcons[status] || "fas fa-question";
  }

  formatMemory(memory) {
    if (!memory) return "Unknown";
    return `${(memory / 1024).toFixed(1)} GB`;
  }

  formatStorage(storage) {
    if (!storage) return "Unknown";
    return `${(storage / 1000000000).toFixed(0)} GB`;
  }

  escapeHtml(text) {
    if (!text) return "";
    const map = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    };
    return text.replace(/[&<>"']/g, (m) => map[m]);
  }

  initializeMasonry() {
    // Placeholder for masonry initialization if needed
  }

  populateDeviceDetailsModal(device) {
    // Implementation for populating device details modal
    console.log("Populating device details modal for:", device);
  }

  populateCommissionModal(device) {
    // Implementation for populating commission modal
    console.log("Populating commission modal for:", device);
  }

  async submitCommission() {
    // Implementation for commission submission
    console.log("Submitting commission request...");
  }

  /**
   * Clean up component
   */
  destroy() {
    if (this.masonryInstance) {
      this.masonryInstance.destroy();
    }
    this.isInitialized = false;
  }
}

// Make available globally for backward compatibility
window.deviceSelection = new DeviceSelectionComponent();

export { DeviceSelectionComponent };
