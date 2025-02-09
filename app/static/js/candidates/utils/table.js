// Function to refresh table
export async function refreshTable() {
    try {
        const currentUrl = new URL(window.location.href);
        // Dodaj parametry filtrowania do URL
        const selectedCampaigns = Array.from(document.querySelectorAll('.filter-campaign:checked'))
            .map(cb => cb.value);
        const selectedStatuses = Array.from(document.querySelectorAll('.filter-status:checked'))
            .map(cb => cb.value);
        const searchText = document.getElementById('searchText')?.value || '';

        currentUrl.searchParams.set('campaigns', selectedCampaigns.join(','));
        currentUrl.searchParams.set('statuses', selectedStatuses.join(','));
        currentUrl.searchParams.set('search', searchText);

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

const statusOrder = {
    'Odrzucony k': 1,          // REJECTED_CRITICAL - najpierw krytyczne odrzucenie
    'Odrzucony': 2,            // REJECTED - potem zwykłe odrzucenie
    'Ankieta': 3,              // PO1
    'Test EQ': 4,              // PO2
    'Ocena EQ': 5,             // PO2_5
    'Test IQ': 6,              // PO3
    'Potencjał': 7,            // PO4
    'Zaproszono na rozmowę': 8,// INVITED_TO_INTERVIEW
    'Oczekuje na decyzję': 9,  // AWAITING_DECISION
    'Zaakceptowany': 10        // ACCEPTED
};

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
    } else if (sortField === 'recruitment_status') {
        // Pobierz tekst ze spana wewnątrz komórki (pomijając białe znaki)
        const statusText = cell.querySelector('.badge')?.textContent.trim() || '';
        // Zwróć wartość numeryczną ze słownika lub maksymalną wartość jeśli status nie jest znany
        return statusOrder[statusText] || 999;
    }
    
    return value.toLowerCase();
} 