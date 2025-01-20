// Function to refresh table
async function refreshTable(fetchNewData = false) {
    try {
        if (fetchNewData) {
            const currentUrl = new URL(window.location.href);
            const response = await fetch(currentUrl);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newTable = doc.querySelector('#candidatesTable tbody');
            if (newTable) {
                document.querySelector('#candidatesTable tbody').innerHTML = newTable.innerHTML;
            }
        }
        
        // Update row numbers
        document.querySelectorAll('#candidatesTable tbody tr').forEach((row, index) => {
            const numberCell = row.querySelector('td.row-number');
            if (numberCell) {
                numberCell.textContent = index + 1;
            }
        });
        
    } catch (error) {
        console.error('Error:', error);
        showToast('Wystąpił błąd podczas odświeżania tabeli', 'error');
    }
}

// Function to get row value for sorting
function getRowValue(row, sortField) {
    const cell = row.querySelector(`td[data-sort="${sortField}"]`);
    if (!cell) return '';
    
    let value = cell.textContent.trim();
    
    // Handle special cases
    if (sortField === 'created_at') {
        return new Date(value).getTime();
    } else if (['po1_score', 'po2_score', 'po2_5_score', 'po3_score', 'po4_score', 'total_score'].includes(sortField)) {
        return value === '-' ? -Infinity : parseFloat(value);
    }
    
    return value.toLowerCase();
}

// Function to initialize sortable headers
function initializeSortableHeaders() {
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

// Function to initialize filters
function initializeFilters() {
    const searchInput = document.getElementById('searchText');
    const campaignCheckboxes = document.querySelectorAll('.filter-campaign');
    const statusCheckboxes = document.querySelectorAll('.filter-status');
    const selectAllCampaigns = document.querySelector('.select-all-campaigns');
    const selectAllStatuses = document.querySelector('.select-all-statuses');
    
    // Initialize select all checkboxes
    if (selectAllCampaigns) {
        selectAllCampaigns.addEventListener('change', function() {
            campaignCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateSelectedOptionsText(this);
            applyFilters();
        });
    }
    
    if (selectAllStatuses) {
        selectAllStatuses.addEventListener('change', function() {
            statusCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateSelectedOptionsText(this);
            applyFilters();
        });
    }
    
    // Initialize individual checkboxes
    campaignCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateSelectedOptionsText(this);
            applyFilters();
            
            // Update select all checkbox
            if (selectAllCampaigns) {
                selectAllCampaigns.checked = Array.from(campaignCheckboxes)
                    .every(cb => cb.checked);
            }
        });
    });
    
    statusCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateSelectedOptionsText(this);
            applyFilters();
            
            // Update select all checkbox
            if (selectAllStatuses) {
                selectAllStatuses.checked = Array.from(statusCheckboxes)
                    .every(cb => cb.checked);
            }
        });
    });
    
    // Initialize search input
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

// Function to update selected options text
function updateSelectedOptionsText(checkbox) {
    const dropdown = checkbox.closest('.dropdown');
    const selectedOptionsSpan = dropdown.querySelector('.selected-options');
    const checkboxes = dropdown.querySelectorAll('.form-check-input:not(.select-all-campaigns):not(.select-all-statuses)');
    
    const selectedOptions = Array.from(checkboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.nextElementSibling.textContent.trim());
    
    if (selectedOptions.length === 0) {
        selectedOptionsSpan.textContent = checkbox.classList.contains('filter-campaign') ? 
            'Brak wybranych kampanii' : 'Brak wybranych statusów';
    } else if (selectedOptions.length === checkboxes.length) {
        selectedOptionsSpan.textContent = checkbox.classList.contains('filter-campaign') ? 
            'Wszystkie kampanie' : 'Wszystkie statusy';
    } else {
        selectedOptionsSpan.textContent = `Wybrano ${selectedOptions.length}`;
    }
}

// Function to apply filters
function applyFilters() {
    const searchText = document.getElementById('searchText')?.value.toLowerCase() || '';
    const selectedCampaigns = Array.from(document.querySelectorAll('.filter-campaign:checked'))
        .map(cb => cb.value);
    const selectedStatuses = Array.from(document.querySelectorAll('.filter-status:checked'))
        .map(cb => cb.value);
    
    document.querySelectorAll('#candidatesTable tbody tr').forEach(row => {
        const name = row.children[1].textContent.toLowerCase();
        const email = row.children[3].textContent.toLowerCase();
        const phone = row.children[4].textContent.toLowerCase();
        const campaign = row.children[2].textContent;
        const status = row.querySelector('td[data-sort="recruitment_status"] .badge').textContent.trim();
        
        const matchesSearch = !searchText || 
            name.includes(searchText) || 
            email.includes(searchText) || 
            phone.includes(searchText);
            
        const matchesCampaign = selectedCampaigns.length === 0 || selectedCampaigns.includes(campaign);
        const matchesStatus = selectedStatuses.length === 0 || selectedStatuses.includes(status);
        
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

// Initialize table functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeSortableHeaders();
    initializeFilters();
    refreshTable();
}); 