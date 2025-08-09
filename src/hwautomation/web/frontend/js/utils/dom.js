/**
 * DOM Utilities for HWAutomation Frontend
 *
 * Common DOM manipulation and query utilities.
 */

/**
 * Safely query a single element
 */
export function querySelector(selector, context = document) {
  try {
    return context.querySelector(selector);
  } catch (error) {
    console.warn(`Invalid selector: ${selector}`, error);
    return null;
  }
}

/**
 * Safely query multiple elements
 */
export function querySelectorAll(selector, context = document) {
  try {
    return Array.from(context.querySelectorAll(selector));
  } catch (error) {
    console.warn(`Invalid selector: ${selector}`, error);
    return [];
  }
}

/**
 * Get element by ID with null safety
 */
export function getElementById(id) {
  return document.getElementById(id);
}

/**
 * Create element with attributes and content
 */
export function createElement(tag, attributes = {}, content = "") {
  const element = document.createElement(tag);

  // Set attributes
  Object.entries(attributes).forEach(([key, value]) => {
    if (key === "className") {
      element.className = value;
    } else if (key === "dataset") {
      Object.entries(value).forEach(([dataKey, dataValue]) => {
        element.dataset[dataKey] = dataValue;
      });
    } else {
      element.setAttribute(key, value);
    }
  });

  // Set content
  if (typeof content === "string") {
    element.innerHTML = content;
  } else if (content instanceof Node) {
    element.appendChild(content);
  } else if (Array.isArray(content)) {
    content.forEach((child) => {
      if (child instanceof Node) {
        element.appendChild(child);
      }
    });
  }

  return element;
}

/**
 * Add event listener with automatic cleanup
 */
export function addEventListener(element, event, handler, options = {}) {
  if (!element) return null;

  element.addEventListener(event, handler, options);

  // Return cleanup function
  return () => {
    element.removeEventListener(event, handler, options);
  };
}

/**
 * Add multiple event listeners
 */
export function addEventListeners(element, events) {
  if (!element) return [];

  const cleanupFunctions = [];

  Object.entries(events).forEach(([event, handler]) => {
    const cleanup = addEventListener(element, event, handler);
    if (cleanup) {
      cleanupFunctions.push(cleanup);
    }
  });

  // Return cleanup function for all listeners
  return () => {
    cleanupFunctions.forEach((cleanup) => cleanup());
  };
}

/**
 * Toggle class on element
 */
export function toggleClass(element, className, force = undefined) {
  if (!element) return false;
  return element.classList.toggle(className, force);
}

/**
 * Add class to element
 */
export function addClass(element, className) {
  if (!element) return;
  element.classList.add(className);
}

/**
 * Remove class from element
 */
export function removeClass(element, className) {
  if (!element) return;
  element.classList.remove(className);
}

/**
 * Check if element has class
 */
export function hasClass(element, className) {
  return element ? element.classList.contains(className) : false;
}

/**
 * Show element
 */
export function show(element, display = "block") {
  if (element) {
    element.style.display = display;
  }
}

/**
 * Hide element
 */
export function hide(element) {
  if (element) {
    element.style.display = "none";
  }
}

/**
 * Toggle element visibility
 */
export function toggle(element, display = "block") {
  if (!element) return;

  if (element.style.display === "none") {
    show(element, display);
  } else {
    hide(element);
  }
}

/**
 * Check if element is visible
 */
export function isVisible(element) {
  if (!element) return false;

  const style = window.getComputedStyle(element);
  return (
    style.display !== "none" &&
    style.visibility !== "hidden" &&
    style.opacity !== "0"
  );
}

/**
 * Get element dimensions
 */
export function getDimensions(element) {
  if (!element) return null;

  const rect = element.getBoundingClientRect();
  return {
    width: rect.width,
    height: rect.height,
    top: rect.top,
    left: rect.left,
    bottom: rect.bottom,
    right: rect.right,
  };
}

/**
 * Scroll element into view smoothly
 */
export function scrollIntoView(element, options = {}) {
  if (!element) return;

  const defaultOptions = {
    behavior: "smooth",
    block: "nearest",
    inline: "nearest",
  };

  element.scrollIntoView({ ...defaultOptions, ...options });
}

/**
 * Wait for element to appear in DOM
 */
export function waitForElement(selector, timeout = 5000, context = document) {
  return new Promise((resolve, reject) => {
    const element = querySelector(selector, context);

    if (element) {
      resolve(element);
      return;
    }

    const observer = new MutationObserver((mutations, obs) => {
      const element = querySelector(selector, context);
      if (element) {
        obs.disconnect();
        resolve(element);
      }
    });

    observer.observe(context, {
      childList: true,
      subtree: true,
    });

    // Timeout fallback
    setTimeout(() => {
      observer.disconnect();
      reject(new Error(`Element ${selector} not found within ${timeout}ms`));
    }, timeout);
  });
}

/**
 * Debounce function calls
 */
export function debounce(func, delay = 300) {
  let timeoutId;

  return function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(this, args), delay);
  };
}

/**
 * Throttle function calls
 */
export function throttle(func, limit = 300) {
  let inThrottle;

  return function (...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * Escape HTML to prevent XSS
 */
export function escapeHtml(text) {
  if (typeof text !== "string") return text;

  const map = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  };

  return text.replace(/[&<>"']/g, (m) => map[m]);
}

/**
 * Parse HTML string into DOM elements
 */
export function parseHTML(html) {
  const template = document.createElement("template");
  template.innerHTML = html.trim();
  return template.content;
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (error) {
    // Fallback for older browsers
    const textArea = createElement("textarea", {
      value: text,
      style: "position: fixed; top: -9999px; left: -9999px;",
    });

    document.body.appendChild(textArea);
    textArea.select();

    try {
      document.execCommand("copy");
      return true;
    } catch (fallbackError) {
      console.error("Failed to copy text:", fallbackError);
      return false;
    } finally {
      document.body.removeChild(textArea);
    }
  }
}
