import { initializeCopyLinks, updateTimeRemainingDisplays } from '../components/tokens.js';

// Initialize details view
function initializeDetailsView() {
    console.log('Initializing details view...');
    
    // Initialize copy links
    console.log('Calling initializeCopyLinks...');
    initializeCopyLinks();
    
    // Initialize time remaining updates
    console.log('Setting up time remaining updates...');
    updateTimeRemainingDisplays();
    setInterval(updateTimeRemainingDisplays, 60000);
    
    console.log('Details view initialization complete');
}

// Export initialization function
export { initializeDetailsView };

// Also expose to window for non-module scripts
window.initializeDetailsView = initializeDetailsView; 