// Custom JavaScript for HWAutomation Documentation

// Add "Back to App" functionality
document.addEventListener('DOMContentLoaded', function() {
    // Create a clickable overlay for the "Back to App" button
    const navTop = document.querySelector('.wy-nav-top');
    if (navTop) {
        // Create the clickable link
        const backLink = document.createElement('a');
        backLink.href = '/';
        backLink.className = 'back-to-app-link';
        backLink.title = 'Return to HWAutomation Application';
        backLink.setAttribute('aria-label', 'Back to HWAutomation Application');

        // Add the link to the nav header
        navTop.appendChild(backLink);

        // Optional: Add click handler for analytics or custom behavior
        backLink.addEventListener('click', function(e) {
            // Could add analytics tracking here if needed
            console.log('Navigating back to HWAutomation app');
        });
    }
});
