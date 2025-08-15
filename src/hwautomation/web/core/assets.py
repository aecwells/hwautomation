"""
Asset management for Vite-built frontend assets.

Handles loading and serving of built frontend assets with manifest integration.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional

from flask import current_app, url_for

logger = logging.getLogger(__name__)


class AssetManager:
    """Manages Vite-built frontend assets with manifest integration."""

    def __init__(self, app=None):
        self.manifest_cache: Optional[Dict] = None
        self.manifest_path: Optional[Path] = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the asset manager with Flask app."""
        # Configure asset paths
        static_folder = Path(app.static_folder)
        self.manifest_path = static_folder / "dist" / "manifest.json"

        # Add template functions - always register these to avoid template errors
        app.jinja_env.globals["asset_url"] = self.asset_url
        app.jinja_env.globals["asset_exists"] = self.asset_exists
        app.jinja_env.globals["get_css_assets"] = self.get_css_assets
        app.jinja_env.globals["get_js_assets"] = self.get_js_assets
        app.jinja_env.globals["get_preload_assets"] = self.get_preload_assets

        # Store reference
        app.extensions = getattr(app, "extensions", {})
        app.extensions["asset_manager"] = self

        # Try to load manifest, but don't fail if it's missing
        try:
            manifest = self._load_manifest()
            if manifest:
                logger.info(
                    f"Asset manager initialized with Vite manifest ({len(manifest)} entries)"
                )
            else:
                logger.warning(
                    "Asset manager initialized without Vite manifest - using CDN fallbacks"
                )
        except Exception as e:
            logger.warning(
                f"Asset manager initialized with manifest error: {e} - using CDN fallbacks"
            )

    def _load_manifest(self) -> Dict:
        """Load and cache the Vite manifest."""
        if self.manifest_cache is not None and not current_app.debug:
            return self.manifest_cache

        if not self.manifest_path or not self.manifest_path.exists():
            logger.warning(f"Vite manifest not found at {self.manifest_path}")
            return {}

        try:
            with open(self.manifest_path, "r") as f:
                manifest = json.load(f)

            self.manifest_cache = manifest
            logger.debug(f"Loaded Vite manifest with {len(manifest)} entries")
            return manifest

        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load Vite manifest: {e}")
            return {}

    def asset_url(self, entry_name: str) -> str:
        """
        Get the URL for a built asset from the manifest.

        Args:
            entry_name: Entry name from vite.config.js (e.g., 'app', 'main')

        Returns:
            URL to the built asset or fallback URL
        """
        manifest = self._load_manifest()

        # Try to find the entry in manifest
        entry_key = f"src/hwautomation/web/frontend/js/core/{entry_name}.js"
        if entry_name == "main":
            entry_key = "src/hwautomation/web/frontend/css/main.css"

        if entry_key in manifest:
            asset_path = manifest[entry_key]["file"]
            return url_for("static", filename=f"dist/{asset_path}")

        # Fallback for development or missing assets
        logger.warning(f"Asset '{entry_name}' not found in manifest")
        if entry_name == "main":
            return url_for("static", filename="css/main.css")
        return url_for("static", filename=f"js/{entry_name}.js")

    def asset_exists(self, entry_name: str) -> bool:
        """Check if an asset exists in the manifest."""
        manifest = self._load_manifest()
        entry_key = f"src/hwautomation/web/frontend/js/core/{entry_name}.js"
        if entry_name == "main":
            entry_key = "src/hwautomation/web/frontend/css/main.css"

        return entry_key in manifest

    def get_css_assets(self) -> list:
        """Get all CSS assets from the manifest."""
        manifest = self._load_manifest()
        css_assets = []

        for entry_key, entry_data in manifest.items():
            if entry_data.get("isEntry") and entry_data["file"].endswith(".css"):
                css_assets.append(
                    url_for("static", filename=f'dist/{entry_data["file"]}')
                )

        return css_assets

    def get_js_assets(self, entry_names: list = None) -> list:
        """
        Get JavaScript assets from the manifest.

        Args:
            entry_names: List of entry names to include (None for all)

        Returns:
            List of JavaScript asset URLs
        """
        manifest = self._load_manifest()
        js_assets = []

        if entry_names is None:
            # Get all entry JavaScript files
            for entry_key, entry_data in manifest.items():
                if entry_data.get("isEntry") and entry_data["file"].endswith(".js"):
                    js_assets.append(
                        url_for("static", filename=f'dist/{entry_data["file"]}')
                    )
        else:
            # Get specific entries
            for entry_name in entry_names:
                entry_key = f"src/hwautomation/web/frontend/js/core/{entry_name}.js"
                if entry_key in manifest:
                    asset_path = manifest[entry_key]["file"]
                    js_assets.append(url_for("static", filename=f"dist/{asset_path}"))

        return js_assets

    def get_preload_assets(self, entry_name: str) -> list:
        """Get assets that should be preloaded for an entry."""
        manifest = self._load_manifest()
        entry_key = f"src/hwautomation/web/frontend/js/core/{entry_name}.js"

        if entry_key not in manifest:
            return []

        entry_data = manifest[entry_key]
        preload_assets = []

        # Add imports (dependencies)
        for import_path in entry_data.get("imports", []):
            if import_path in manifest:
                asset_path = manifest[import_path]["file"]
                preload_assets.append(url_for("static", filename=f"dist/{asset_path}"))

        return preload_assets


# Global instance
asset_manager = AssetManager()


def init_assets(app):
    """Initialize asset management for the Flask app."""
    asset_manager.init_app(app)
    return asset_manager
