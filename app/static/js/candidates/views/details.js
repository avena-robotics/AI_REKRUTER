import { initializeCopyLinks, updateTimeRemainingDisplays } from '../components/tokens.js';

// Initialize details view
export function initializeDetailsView() {
    // Initialize copy links
    initializeCopyLinks();
    
    // Initialize time remaining updates
    updateTimeRemainingDisplays();
    setInterval(updateTimeRemainingDisplays, 60000);
}

// Export initialization function
window.initializeDetailsView = initializeDetailsView; 