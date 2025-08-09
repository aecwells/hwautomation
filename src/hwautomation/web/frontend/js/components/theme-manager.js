/**
 * Theme Manager Component
 *
 * Manages light/dark theme switching and persistence.
 * Integrates with Bootstrap's data-bs-theme attribute.
 */

class ThemeManager {
  constructor() {
    this.currentTheme = "light";
    this.isInitialized = false;
    this.toggleButton = null;
  }

  /**
   * Initialize theme manager
   */
  async initialize() {
    if (this.isInitialized) {
      return;
    }

    // Get state manager
    const app = window.HWAutomationApp;
    this.stateManager = app.getService("state");

    // Load saved theme
    this.currentTheme = this.stateManager.getState("ui.theme", "light");

    // Apply theme
    this.applyTheme(this.currentTheme, false);

    // Setup theme toggle button
    this.setupThemeToggle();

    // Listen for system theme changes
    this.setupSystemThemeListener();

    this.isInitialized = true;
  }

  /**
   * Get current theme
   */
  getCurrentTheme() {
    return this.currentTheme;
  }

  /**
   * Set theme
   */
  setTheme(theme, save = true) {
    if (theme !== "light" && theme !== "dark") {
      console.warn(`Invalid theme: ${theme}. Using light theme.`);
      theme = "light";
    }

    this.currentTheme = theme;
    this.applyTheme(theme, save);
  }

  /**
   * Toggle between light and dark themes
   */
  toggleTheme() {
    const newTheme = this.currentTheme === "light" ? "dark" : "light";
    this.setTheme(newTheme);
  }

  /**
   * Apply theme to document
   */
  applyTheme(theme, save = true) {
    // Set Bootstrap theme attribute
    document.documentElement.setAttribute("data-bs-theme", theme);

    // Update body class for compatibility
    document.body.classList.remove("theme-light", "theme-dark");
    document.body.classList.add(`theme-${theme}`);

    // Update toggle button if it exists
    this.updateToggleButton();

    // Save to state if requested
    if (save && this.stateManager) {
      this.stateManager.setState("ui.theme", theme);
    }

    // Emit theme change event
    const event = new CustomEvent("theme:changed", {
      detail: { theme, previousTheme: this.currentTheme },
    });
    document.dispatchEvent(event);

    console.log(`Theme applied: ${theme}`);
  }

  /**
   * Setup theme toggle button
   */
  setupThemeToggle() {
    // Look for existing theme toggle button
    this.toggleButton = document.querySelector('[data-bs-toggle="theme"]');

    if (!this.toggleButton) {
      // Create theme toggle button if it doesn't exist
      this.createThemeToggle();
    }

    if (this.toggleButton) {
      this.toggleButton.addEventListener("click", (e) => {
        e.preventDefault();
        this.toggleTheme();
      });

      this.updateToggleButton();
    }
  }

  /**
   * Create theme toggle button
   */
  createThemeToggle() {
    // Look for navbar or header to add the toggle
    const navbar = document.querySelector(".navbar");
    const navbarNav = navbar?.querySelector(".navbar-nav");

    if (navbarNav) {
      const themeToggleItem = document.createElement("li");
      themeToggleItem.className = "nav-item";

      themeToggleItem.innerHTML = `
                <button class="nav-link btn btn-link"
                        data-bs-toggle="theme"
                        title="Toggle theme"
                        aria-label="Toggle theme">
                    <i class="fas fa-sun" data-theme-icon="light"></i>
                    <i class="fas fa-moon" data-theme-icon="dark" style="display: none;"></i>
                </button>
            `;

      this.toggleButton = themeToggleItem.querySelector(
        '[data-bs-toggle="theme"]',
      );
      navbarNav.appendChild(themeToggleItem);
    }
  }

  /**
   * Update toggle button appearance
   */
  updateToggleButton() {
    if (!this.toggleButton) return;

    const lightIcon = this.toggleButton.querySelector(
      '[data-theme-icon="light"]',
    );
    const darkIcon = this.toggleButton.querySelector(
      '[data-theme-icon="dark"]',
    );

    if (lightIcon && darkIcon) {
      if (this.currentTheme === "light") {
        lightIcon.style.display = "inline";
        darkIcon.style.display = "none";
        this.toggleButton.title = "Switch to dark theme";
      } else {
        lightIcon.style.display = "none";
        darkIcon.style.display = "inline";
        this.toggleButton.title = "Switch to light theme";
      }
    }
  }

  /**
   * Setup system theme preference listener
   */
  setupSystemThemeListener() {
    if (window.matchMedia) {
      const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

      // Only auto-apply system theme if user hasn't manually set a preference
      const hasUserPreference = this.stateManager.hasState("ui.theme");

      if (!hasUserPreference) {
        const systemTheme = mediaQuery.matches ? "dark" : "light";
        this.setTheme(systemTheme, false); // Don't save system preference
      }

      // Listen for system theme changes
      mediaQuery.addEventListener("change", (e) => {
        // Only auto-apply if user hasn't set a manual preference
        const hasUserPreference = this.stateManager.hasState("ui.theme");

        if (!hasUserPreference) {
          const systemTheme = e.matches ? "dark" : "light";
          this.setTheme(systemTheme, false);
        }
      });
    }
  }

  /**
   * Get system theme preference
   */
  getSystemTheme() {
    if (
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    ) {
      return "dark";
    }
    return "light";
  }

  /**
   * Reset to system theme
   */
  resetToSystemTheme() {
    this.stateManager.deleteState("ui.theme");
    const systemTheme = this.getSystemTheme();
    this.setTheme(systemTheme, false);
  }

  /**
   * Clean up theme manager
   */
  destroy() {
    if (this.toggleButton) {
      this.toggleButton.removeEventListener("click", this.toggleTheme);
    }
    this.isInitialized = false;
  }
}

export { ThemeManager };
