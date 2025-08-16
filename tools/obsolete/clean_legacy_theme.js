/**
 * Legacy Theme Cleanup Script
 *
 * This script can be run in the browser console to clean up any legacy theme storage
 * and ensure the new ThemeManager system starts with a clean state.
 */

(function cleanLegacyTheme() {
    console.log('🧹 Cleaning up legacy theme storage...');

    // Remove legacy theme storage
    const legacyTheme = localStorage.getItem('theme');
    if (legacyTheme) {
        console.log(`Found legacy theme setting: ${legacyTheme}`);
        localStorage.removeItem('theme');
        console.log('✅ Removed legacy theme storage');

        // Migrate to new format if no new format exists
        try {
            const hwState = localStorage.getItem('hwautomation-state');
            let stateObj = hwState ? JSON.parse(hwState) : {};

            if (!stateObj.ui || !stateObj.ui.theme) {
                if (!stateObj.ui) stateObj.ui = {};
                stateObj.ui.theme = legacyTheme;
                localStorage.setItem('hwautomation-state', JSON.stringify(stateObj));
                console.log(`✅ Migrated theme setting to new format: ${legacyTheme}`);
            }
        } catch (e) {
            console.warn('Failed to migrate theme to new format:', e);
        }
    } else {
        console.log('No legacy theme storage found');
    }

    // Show current theme state
    try {
        const hwState = localStorage.getItem('hwautomation-state');
        if (hwState) {
            const parsed = JSON.parse(hwState);
            console.log('Current theme in new format:', parsed.ui?.theme || 'not set');
        } else {
            console.log('No theme state found in new format');
        }
    } catch (e) {
        console.warn('Could not read new theme format:', e);
    }

    console.log('🎨 Legacy theme cleanup complete!');
    console.log('Refresh the page to ensure the ThemeManager initializes with clean state.');
})();
