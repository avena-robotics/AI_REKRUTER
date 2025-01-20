// Function to refresh table
export async function refreshTable(fetchNewData = false) {
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
            
            // Reapply filters after fetching new data
            if (typeof applyFilters === 'function') {
                applyFilters();
            }
        }
        
        // Update row numbers for visible rows only
        let visibleRowNumber = 1;
        document.querySelectorAll('#candidatesTable tbody tr').forEach(row => {
            if (row.style.display !== 'none') {
                const numberCell = row.querySelector('td.row-number');
                if (numberCell) {
                    numberCell.textContent = visibleRowNumber++;
                }
            }
        });
        
    } catch (error) {
        console.error('Error:', error);
        showToast('Wystąpił błąd podczas odświeżania tabeli', 'error');
    }
}

// Function to get row value for sorting
export function getRowValue(row, sortField) {
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