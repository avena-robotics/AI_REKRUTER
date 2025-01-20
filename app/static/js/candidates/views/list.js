import { refreshTable } from '../utils/table.js';

// Initialize list view
export function initializeListView() {
    // Initialize filters
    initializeFilters();
    
    // Initialize sortable headers
    initializeSortableHeaders();
    
    // Initialize bulk recalculate button
    const bulkRecalculateBtn = document.getElementById('bulkRecalculateBtn');
    if (bulkRecalculateBtn) {
        bulkRecalculateBtn.addEventListener('click', bulkRecalculateScores);
    }
    
    // Initial table refresh
    refreshTable(false);
}

// Export initialization function
window.initializeListView = initializeListView; 