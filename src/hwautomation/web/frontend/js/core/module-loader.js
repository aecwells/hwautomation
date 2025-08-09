/**
 * Module Loader for HWAutomation Frontend
 *
 * Loads and initializes modular components based on the current page.
 * Provides lazy loading and dependency management for frontend modules.
 */

class ModuleLoader {
  constructor() {
    this.loadedModules = new Map();
    this.loadingModules = new Map();
    this.pageModules = new Map();
    this.isInitialized = false;
  }

  /**
   * Initialize module loader
   */
  async initialize() {
    if (this.isInitialized) {
      return;
    }

    // Register page-specific modules
    this.registerPageModules();

    // Load modules for current page
    await this.loadPageModules();

    this.isInitialized = true;
    console.log("Module Loader initialized");
  }

  /**
   * Register modules for specific pages
   */
  registerPageModules() {
    // Dashboard page
    this.pageModules.set("dashboard", [
      "components/connection-status.js",
      "components/theme-manager.js",
    ]);

    // Device selection page
    this.pageModules.set("device-selection", [
      "components/connection-status.js",
      "components/theme-manager.js",
      "components/device-selection.js",
    ]);

    // Firmware management page
    this.pageModules.set("firmware", [
      "components/connection-status.js",
      "components/theme-manager.js",
    ]);

    // Database management page
    this.pageModules.set("database", [
      "components/connection-status.js",
      "components/theme-manager.js",
    ]);

    // Logs page
    this.pageModules.set("logs", [
      "components/connection-status.js",
      "components/theme-manager.js",
    ]);
  }

  /**
   * Detect current page and load appropriate modules
   */
  async loadPageModules() {
    const currentPage = this.detectCurrentPage();
    const modules = this.pageModules.get(currentPage) || [];

    console.log(`Loading modules for page: ${currentPage}`, modules);

    // Load all modules for the current page
    const loadPromises = modules.map((module) => this.loadModule(module));
    await Promise.all(loadPromises);
  }

  /**
   * Detect current page based on URL or body classes
   */
  detectCurrentPage() {
    const path = window.location.pathname;
    const bodyClasses = document.body.classList;

    // Check body classes first (most reliable)
    if (bodyClasses.contains("page-dashboard")) return "dashboard";
    if (bodyClasses.contains("page-device-selection"))
      return "device-selection";
    if (bodyClasses.contains("page-firmware")) return "firmware";
    if (bodyClasses.contains("page-database")) return "database";
    if (bodyClasses.contains("page-logs")) return "logs";

    // Fallback to URL path detection
    if (path === "/" || path === "/dashboard") return "dashboard";
    if (path.includes("/devices") || path.includes("/maas"))
      return "device-selection";
    if (path.includes("/firmware")) return "firmware";
    if (path.includes("/database")) return "database";
    if (path.includes("/logs")) return "logs";

    // Default to dashboard
    return "dashboard";
  }

  /**
   * Load a specific module
   */
  async loadModule(modulePath) {
    // Check if already loaded
    if (this.loadedModules.has(modulePath)) {
      return this.loadedModules.get(modulePath);
    }

    // Check if currently loading
    if (this.loadingModules.has(modulePath)) {
      return this.loadingModules.get(modulePath);
    }

    // Start loading
    const loadPromise = this.doLoadModule(modulePath);
    this.loadingModules.set(modulePath, loadPromise);

    try {
      const module = await loadPromise;
      this.loadedModules.set(modulePath, module);
      this.loadingModules.delete(modulePath);
      return module;
    } catch (error) {
      this.loadingModules.delete(modulePath);
      throw error;
    }
  }

  /**
   * Actually load the module
   */
  async doLoadModule(modulePath) {
    try {
      // Try to load from built assets first
      let fullPath;
      
      // Check if we have a manifest with built assets
      try {
        const manifestResponse = await fetch('/static/dist/manifest.json');
        if (manifestResponse.ok) {
          const manifest = await manifestResponse.json();
          
          // Convert module path to manifest key format
          const manifestKey = `src/hwautomation/web/frontend/js/${modulePath}`;
          
          if (manifest[manifestKey]) {
            fullPath = `/static/dist/${manifest[manifestKey].file}`;
          }
        }
      } catch (e) {
        console.warn('Could not load manifest, falling back to development paths');
      }
      
      // Fallback to development path if not in manifest
      if (!fullPath) {
        const basePath = "/static/js/frontend/js/";
        fullPath = basePath + modulePath;
      }

      console.log(`Loading module: ${fullPath}`);

      // Dynamic import
      const module = await import(fullPath);

      // Auto-initialize if the module has an initialize function
      if (module.default && typeof module.default.initialize === "function") {
        await module.default.initialize();
      }

      console.log(`Module loaded successfully: ${modulePath}`);
      return module;
    } catch (error) {
      console.error(`Failed to load module ${modulePath}:`, error);

      // Try fallback loading for compatibility
      return this.loadModuleFallback(modulePath);
    }
  }

  /**
   * Fallback module loading for compatibility
   */
  async loadModuleFallback(modulePath) {
    console.log(`Attempting fallback loading for: ${modulePath}`);

    // For now, just return a stub
    return {
      default: {
        initialize: async () => {
          console.log(`Fallback module loaded: ${modulePath}`);
        },
      },
    };
  }

  /**
   * Load module on demand
   */
  async loadOnDemand(modulePath) {
    return this.loadModule(modulePath);
  }

  /**
   * Unload a module
   */
  unloadModule(modulePath) {
    if (this.loadedModules.has(modulePath)) {
      const module = this.loadedModules.get(modulePath);

      // Call destroy method if available
      if (module.default && typeof module.default.destroy === "function") {
        module.default.destroy();
      }

      this.loadedModules.delete(modulePath);
      console.log(`Module unloaded: ${modulePath}`);
    }
  }

  /**
   * Get a loaded module
   */
  getModule(modulePath) {
    return this.loadedModules.get(modulePath);
  }

  /**
   * Check if module is loaded
   */
  isModuleLoaded(modulePath) {
    return this.loadedModules.has(modulePath);
  }

  /**
   * Get all loaded modules
   */
  getLoadedModules() {
    return Array.from(this.loadedModules.keys());
  }

  /**
   * Reload page modules
   */
  async reloadPageModules() {
    // Unload existing modules
    const currentPage = this.detectCurrentPage();
    const modules = this.pageModules.get(currentPage) || [];

    modules.forEach((module) => this.unloadModule(module));

    // Reload modules
    await this.loadPageModules();
  }

  /**
   * Clean up all modules
   */
  destroy() {
    // Unload all modules
    for (const [modulePath] of this.loadedModules) {
      this.unloadModule(modulePath);
    }

    this.loadedModules.clear();
    this.loadingModules.clear();
    this.isInitialized = false;
  }
}

// Create global module loader instance
window.moduleLoader = new ModuleLoader();

// Initialize when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    window.moduleLoader.initialize().catch(console.error);
  });
} else {
  // DOM already loaded
  window.moduleLoader.initialize().catch(console.error);
}

export { ModuleLoader };
