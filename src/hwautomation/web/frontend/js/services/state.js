/**
 * State Manager for HWAutomation Frontend
 *
 * Centralized state management with reactive updates and persistence.
 * Provides a simple but effective state management solution.
 */

class StateManager {
  constructor() {
    this.state = {};
    this.listeners = new Map();
    this.persistentKeys = new Set();
    this.isInitialized = false;
  }

  /**
   * Initialize state manager
   */
  async initialize() {
    if (this.isInitialized) {
      return;
    }

    // Load persistent state from localStorage
    this.loadPersistentState();

    // Set up default state
    this.initializeDefaultState();

    this.isInitialized = true;
  }

  /**
   * Initialize default state values
   */
  initializeDefaultState() {
    const defaults = {
      "socket.connected": false,
      "api.healthy": false,
      "ui.theme": "light",
      "ui.sidebarCollapsed": false,
      "devices.currentView": "cards",
      "devices.selectedDevice": null,
      "devices.filters": {},
      "workflows.active": [],
      "notifications.items": [],
    };

    for (const [key, value] of Object.entries(defaults)) {
      if (!this.hasState(key)) {
        this.setState(key, value, false); // Don't trigger listeners for defaults
      }
    }

    // Mark some keys as persistent
    this.setPersistent([
      "ui.theme",
      "ui.sidebarCollapsed",
      "devices.currentView",
    ]);
  }

  /**
   * Set state value
   */
  setState(key, value, notify = true) {
    const oldValue = this.getState(key);
    this.setNestedValue(this.state, key, value);

    if (notify) {
      this.notifyListeners(key, value, oldValue);
    }

    // Save to localStorage if persistent
    if (this.persistentKeys.has(key)) {
      this.savePersistentState();
    }
  }

  /**
   * Get state value
   */
  getState(key, defaultValue = undefined) {
    return this.getNestedValue(this.state, key, defaultValue);
  }

  /**
   * Check if state key exists
   */
  hasState(key) {
    return (
      this.getNestedValue(this.state, key, Symbol("not-found")) !==
      Symbol("not-found")
    );
  }

  /**
   * Delete state key
   */
  deleteState(key) {
    const keys = key.split(".");
    const lastKey = keys.pop();
    const parent = keys.reduce((obj, k) => obj?.[k], this.state);

    if (parent && lastKey in parent) {
      const oldValue = parent[lastKey];
      delete parent[lastKey];
      this.notifyListeners(key, undefined, oldValue);

      if (this.persistentKeys.has(key)) {
        this.savePersistentState();
      }
    }
  }

  /**
   * Subscribe to state changes
   */
  subscribe(key, callback) {
    if (!this.listeners.has(key)) {
      this.listeners.set(key, new Set());
    }
    this.listeners.get(key).add(callback);

    // Return unsubscribe function
    return () => {
      const keyListeners = this.listeners.get(key);
      if (keyListeners) {
        keyListeners.delete(callback);
        if (keyListeners.size === 0) {
          this.listeners.delete(key);
        }
      }
    };
  }

  /**
   * Subscribe to multiple state keys
   */
  subscribeMultiple(keys, callback) {
    const unsubscribers = keys.map((key) => this.subscribe(key, callback));

    return () => {
      unsubscribers.forEach((unsub) => unsub());
    };
  }

  /**
   * Mark keys as persistent (saved to localStorage)
   */
  setPersistent(keys) {
    if (Array.isArray(keys)) {
      keys.forEach((key) => this.persistentKeys.add(key));
    } else {
      this.persistentKeys.add(keys);
    }
    this.savePersistentState();
  }

  /**
   * Get current state snapshot
   */
  getSnapshot() {
    return JSON.parse(JSON.stringify(this.state));
  }

  /**
   * Reset state to defaults
   */
  reset() {
    this.state = {};
    this.listeners.clear();
    this.persistentKeys.clear();
    localStorage.removeItem("hwautomation-state");
    this.initializeDefaultState();
  }

  /**
   * Set nested value using dot notation
   */
  setNestedValue(obj, path, value) {
    const keys = path.split(".");
    const lastKey = keys.pop();
    const target = keys.reduce((current, key) => {
      if (current[key] === undefined) {
        current[key] = {};
      }
      return current[key];
    }, obj);
    target[lastKey] = value;
  }

  /**
   * Get nested value using dot notation
   */
  getNestedValue(obj, path, defaultValue) {
    const keys = path.split(".");
    let current = obj;

    for (const key of keys) {
      if (current === null || current === undefined || !(key in current)) {
        return defaultValue;
      }
      current = current[key];
    }

    return current;
  }

  /**
   * Notify listeners of state changes
   */
  notifyListeners(key, newValue, oldValue) {
    // Notify exact key listeners
    const exactListeners = this.listeners.get(key);
    if (exactListeners) {
      exactListeners.forEach((callback) => {
        try {
          callback(newValue, oldValue, key);
        } catch (error) {
          console.error("State listener error:", error);
        }
      });
    }

    // Notify wildcard listeners (for parent keys)
    const keyParts = key.split(".");
    for (let i = 0; i < keyParts.length; i++) {
      const parentKey = keyParts.slice(0, i + 1).join(".") + ".*";
      const wildcardListeners = this.listeners.get(parentKey);
      if (wildcardListeners) {
        wildcardListeners.forEach((callback) => {
          try {
            callback(newValue, oldValue, key);
          } catch (error) {
            console.error("State wildcard listener error:", error);
          }
        });
      }
    }
  }

  /**
   * Load persistent state from localStorage
   */
  loadPersistentState() {
    try {
      const stored = localStorage.getItem("hwautomation-state");
      if (stored) {
        const persistentState = JSON.parse(stored);
        Object.assign(this.state, persistentState);
      }
    } catch (error) {
      console.warn("Failed to load persistent state:", error);
    }
  }

  /**
   * Save persistent state to localStorage
   */
  savePersistentState() {
    try {
      const persistentState = {};
      for (const key of this.persistentKeys) {
        const value = this.getState(key);
        if (value !== undefined) {
          this.setNestedValue(persistentState, key, value);
        }
      }
      localStorage.setItem(
        "hwautomation-state",
        JSON.stringify(persistentState),
      );
    } catch (error) {
      console.warn("Failed to save persistent state:", error);
    }
  }
}

export { StateManager };
