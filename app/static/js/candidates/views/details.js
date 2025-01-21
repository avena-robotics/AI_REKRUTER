import { initializeCopyLinks, updateTimeRemainingDisplays } from '../components/tokens.js';

// Initialize details view
function initializeDetailsView() {
    // Initialize copy links
    initializeCopyLinks();
    
    // Initialize time remaining updates
    updateTimeRemainingDisplays();
    setInterval(updateTimeRemainingDisplays, 60000);
}

// Export initialization function
export { initializeDetailsView };

// Also expose to window for non-module scripts
window.initializeDetailsView = initializeDetailsView; 