import { refreshTable, getRowValue } from '../utils/table.js';

// Function to initialize sortable headers
export function initializeSortableHeaders() {
    const headers = document.querySelectorAll('#candidatesTable th.sortable');
    let currentSortField = null;
    let currentSortOrder = 'asc';
    let sortOrderLabels = {};
    
    headers.forEach(header => {
        header.addEventListener('click', () => {
            const sortField = header.dataset.sort;
            
            // Update sort order
            if (sortField === currentSortField) {
                currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
            } else {
                currentSortField = sortField;
                currentSortOrder = 'asc';
            }
            
            // Update header classes
            headers.forEach(h => {
                h.classList.remove('asc', 'desc');
                const orderLabel = h.querySelector('.sort-order');
                if (orderLabel) orderLabel.remove();
            });
            
            header.classList.add(currentSortOrder);
            
            // Sort the table
            const tbody = document.querySelector('#candidatesTable tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            rows.sort((a, b) => {
                const aValue = getRowValue(a, sortField);
                const bValue = getRowValue(b, sortField);
                
                if (aValue === bValue) return 0;
                if (aValue === -Infinity) return 1;
                if (bValue === -Infinity) return -1;
                
                const comparison = aValue < bValue ? -1 : 1;
                return currentSortOrder === 'asc' ? comparison : -comparison;
            });
            
            // Clear and re-append rows
            tbody.innerHTML = '';
            rows.forEach(row => tbody.appendChild(row));
            
            // Update row numbers
            rows.forEach((row, index) => {
                const numberCell = row.querySelector('td.row-number');
                if (numberCell) {
                    numberCell.textContent = index + 1;
                }
            });
            
            // Update sort order labels
            if (sortOrderLabels[sortField]) {
                delete sortOrderLabels[sortField];
            }
            
            const orderLabel = document.createElement('span');
            orderLabel.className = 'sort-order';
            orderLabel.textContent = Object.keys(sortOrderLabels).length + 1;
            header.appendChild(orderLabel);
            
            sortOrderLabels[sortField] = currentSortOrder;
        });
    });
}

// Function to apply filters
export function applyFilters() {
    const searchText = document.getElementById('searchText')?.value.toLowerCase() || '';
    const selectedCampaigns = Array.from(document.querySelectorAll('.filter-campaign:checked'))
        .map(cb => cb.value);
    const selectedStatuses = Array.from(document.querySelectorAll('.filter-status:checked'))
        .map(cb => cb.value);
    
    document.querySelectorAll('#candidatesTable tbody tr').forEach(row => {
        const name = row.children[1].textContent.toLowerCase();
        const email = row.children[3].textContent.toLowerCase();
        const phone = row.children[4].textContent.toLowerCase();
        const campaign = row.children[2].textContent.trim();
        const statusBadge = row.querySelector('.badge');
        const status = statusBadge ? statusBadge.textContent.trim() : '';
        
        const matchesSearch = !searchText || 
            name.includes(searchText) || 
            email.includes(searchText) || 
            phone.includes(searchText);
            
        const matchesCampaign = selectedCampaigns.length === 0 ? 
            !campaign : // jeśli nie wybrano żadnej kampanii, pokaż tylko wiersze bez kampanii
            selectedCampaigns.includes(campaign);
            
        const matchesStatus = selectedStatuses.length === 0 ?
            !status : // jeśli nie wybrano żadnego statusu, pokaż tylko wiersze bez statusu
            selectedStatuses.some(s => {
                switch(s) {
                    case 'PO1': return status === 'Ankieta';
                    case 'PO2': return status === 'Test EQ';
                    case 'PO2_5': return status === 'Ocena EQ';
                    case 'PO3': return status === 'Test IQ';
                    case 'PO4': return status === 'Potencjał';
                    case 'INVITED_TO_INTERVIEW': return status === 'Zaproszono na rozmowę';
                    case 'AWAITING_DECISION': return status === 'Oczekuje na decyzję';
                    case 'REJECTED': return status === 'Odrzucony';
                    case 'ACCEPTED': return status === 'Zaakceptowany';
                    default: return false;
                }
            });
        
        row.style.display = matchesSearch && matchesCampaign && matchesStatus ? '' : 'none';
    });
    
    // Update row numbers for visible rows
    let visibleRowNumber = 1;
    document.querySelectorAll('#candidatesTable tbody tr').forEach(row => {
        if (row.style.display !== 'none') {
            const numberCell = row.querySelector('td.row-number');
            if (numberCell) {
                numberCell.textContent = visibleRowNumber++;
            }
        }
    });
}

// Function to update selected options text
export function updateSelectedOptionsText(checkbox) {
    const dropdown = checkbox.closest('.dropdown');
    const selectedOptionsSpan = dropdown.querySelector('.selected-options');
    const checkboxes = dropdown.querySelectorAll('.form-check-input:not(.select-all-campaigns):not(.select-all-statuses)');
    const selectAllCheckbox = dropdown.querySelector('.select-all-campaigns, .select-all-statuses');
    
    const selectedOptions = Array.from(checkboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.nextElementSibling.textContent.trim());
    
    const isCampaignFilter = checkbox.classList.contains('filter-campaign') || 
                            checkbox.classList.contains('select-all-campaigns');
    
    if (selectedOptions.length === 0) {
        selectedOptionsSpan.textContent = isCampaignFilter ? 'Brak kampanii' : 'Brak statusów';
        if (selectAllCheckbox) selectAllCheckbox.checked = false;
    } else if (selectedOptions.length === checkboxes.length) {
        selectedOptionsSpan.textContent = isCampaignFilter ? 'Wszystkie kampanie' : 'Wszystkie statusy';
        if (selectAllCheckbox) selectAllCheckbox.checked = true;
    } else {
        selectedOptionsSpan.textContent = selectedOptions.join(', ');
        if (selectAllCheckbox) selectAllCheckbox.checked = false;
    }
}

// Function to initialize filters
export function initializeFilters() {
    const searchInput = document.getElementById('searchText');
    const selectAllCampaigns = document.querySelector('.select-all-campaigns');
    const selectAllStatuses = document.querySelector('.select-all-statuses');
    const campaignCheckboxes = document.querySelectorAll('.filter-campaign:not(.select-all-campaigns)');
    const statusCheckboxes = document.querySelectorAll('.filter-status:not(.select-all-statuses)');
    
    // Initialize bulk recalculate button
    const bulkRecalculateBtn = document.getElementById('bulkRecalculateBtn');
    if (bulkRecalculateBtn) {
        bulkRecalculateBtn.addEventListener('click', bulkRecalculateScores);
    }

    // Set initial state - all checkboxes checked
    if (selectAllCampaigns) {
        selectAllCampaigns.checked = true;
    }
    if (selectAllStatuses) {
        selectAllStatuses.checked = true;
    }
    campaignCheckboxes.forEach(checkbox => {
        checkbox.checked = true;
    });
    statusCheckboxes.forEach(checkbox => {
        checkbox.checked = true;
    });
    
    // Initialize select all checkboxes
    if (selectAllCampaigns) {
        selectAllCampaigns.addEventListener('change', function() {
            const isChecked = this.checked;
            campaignCheckboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
            });
            updateSelectedOptionsText(this);
            applyFilters();
        });
    }
    
    if (selectAllStatuses) {
        selectAllStatuses.addEventListener('change', function() {
            const isChecked = this.checked;
            statusCheckboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
            });
            updateSelectedOptionsText(this);
            applyFilters();
        });
    }
    
    // Initialize individual checkboxes
    campaignCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const allChecked = Array.from(campaignCheckboxes).every(cb => cb.checked);
            if (selectAllCampaigns) {
                selectAllCampaigns.checked = allChecked;
            }
            updateSelectedOptionsText(this);
            applyFilters();
        });
    });
    
    statusCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const allChecked = Array.from(statusCheckboxes).every(cb => cb.checked);
            if (selectAllStatuses) {
                selectAllStatuses.checked = allChecked;
            }
            updateSelectedOptionsText(this);
            applyFilters();
        });
    });
    
    // Stop dropdown from closing on click inside
    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        menu.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });
    
    // Initialize search input with immediate filtering
    if (searchInput) {
        let debounceTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(() => {
                applyFilters();
            }, 300);
        });
    }
    
    // Initialize reset button
    const resetButton = document.getElementById('resetFiltersBtn');
    if (resetButton) {
        resetButton.addEventListener('click', function() {
            // Reset search
            if (searchInput) {
                searchInput.value = '';
            }
            
            // Reset campaign filters
            if (selectAllCampaigns) {
                selectAllCampaigns.checked = true;
            }
            campaignCheckboxes.forEach(checkbox => {
                checkbox.checked = true;
            });
            
            // Reset status filters
            if (selectAllStatuses) {
                selectAllStatuses.checked = true;
            }
            statusCheckboxes.forEach(checkbox => {
                checkbox.checked = true;
            });
            
            // Update dropdown texts
            document.querySelectorAll('.dropdown .selected-options').forEach(span => {
                if (span.closest('.dropdown').querySelector('.select-all-campaigns')) {
                    span.textContent = 'Wszystkie kampanie';
                } else if (span.closest('.dropdown').querySelector('.select-all-statuses')) {
                    span.textContent = 'Wszystkie statusy';
                }
            });
            
            // Apply filters
            applyFilters();
        });
    }
}

// Export functions to global scope for HTML event handlers
Object.assign(window, {
    initializeSortableHeaders,
    applyFilters,
    updateSelectedOptionsText,
    initializeFilters
});

// Initialize table functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeSortableHeaders();
    initializeFilters();
    refreshTable();
}); 