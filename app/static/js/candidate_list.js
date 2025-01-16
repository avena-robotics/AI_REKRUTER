// Define functions in global scope
window.viewCandidate = async function(candidateId) {
    setButtonLoading(`viewBtn_${candidateId}`, true);
    try {
        const response = await fetch(`/candidates/${candidateId}`);
        const html = await response.text();
        document.getElementById('candidateModalBody').innerHTML = html;
        initializeCopyLinks();
        const modal = new bootstrap.Modal(document.getElementById('candidateModal'));
        document.getElementById('candidateModal').addEventListener('hidden.bs.modal', function () {
            document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
                backdrop.remove();
            });
        });
        modal.show();
    } catch (error) {
        console.error('Error:', error);
        showToast('Błąd podczas ładowania danych kandydata', 'error');
    } finally {
        setButtonLoading(`viewBtn_${candidateId}`, false);
    }
};

async function refreshTable(fetchNewData = false) {
    const tbody = document.querySelector('tbody');
    
    // Fetch new data if requested
    if (fetchNewData) {
        try {
            const response = await fetch('/candidates/');
            const html = await response.text();
            
            // Create a temporary div to parse the HTML
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            
            // Get the new tbody content
            const newTbody = tempDiv.querySelector('tbody');
            if (newTbody) {
                // Update originalRows with new data
                originalRows = Array.from(newTbody.querySelectorAll('tr'));
            }
        } catch (error) {
            console.error('Error fetching updated candidate data:', error);
            showToast('Błąd podczas odświeżania listy kandydatów', 'error');
            return;
        }
    }
    
    // Get current filters
    const searchText = document.getElementById('searchText').value.toLowerCase();
    const selectedCampaigns = Array.from(document.querySelectorAll('.filter-campaign:checked'))
        .map(cb => cb.value);
    const selectedStatuses = Array.from(document.querySelectorAll('.filter-status:checked'))
        .map(cb => cb.value);
    
    // Clone original rows for filtering
    let rows = originalRows.map(row => row.cloneNode(true));
    
    // Apply filters
    rows = rows.filter(row => {
        const text = row.textContent.toLowerCase();
        const campaignCode = row.querySelector('td:nth-child(2)').textContent.trim();
        const statusBadge = row.querySelector('.badge');
        const status = statusBadge ? statusBadge.textContent.trim() : '';
        
        const matchesSearch = !searchText || text.includes(searchText);
        
        // Nowa logika dla kampanii:
        // - Jeśli nic nie jest zaznaczone, pokaż tylko elementy bez kodu kampanii
        // - Jeśli coś jest zaznaczone, pokaż elementy z zaznaczonymi kodami kampanii
        const matchesCampaign = selectedCampaigns.length === 0 ? 
            !campaignCode : // pokaż tylko gdy nie ma kodu kampanii
            selectedCampaigns.includes(campaignCode); // pokaż gdy kod jest w zaznaczonych

        // Nowa logika dla statusów:
        // - Jeśli nic nie jest zaznaczone, pokaż tylko elementy bez statusu
        // - Jeśli coś jest zaznaczone, pokaż elementy z zaznaczonymi statusami
        const matchesStatus = selectedStatuses.length === 0 ?
            !status : // pokaż tylko gdy nie ma statusu
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
        
        return matchesSearch && matchesCampaign && matchesStatus;
    });

    // Apply multiple sorts
    if (currentSorts.length > 0) {
        rows.sort((a, b) => {
            for (const sort of currentSorts) {
                const aValue = getRowValue(a, sort.field);
                const bValue = getRowValue(b, sort.field);
                
                const order = sort.direction === 'asc' ? 1 : -1;
                
                if (aValue < bValue) return -1 * order;
                if (aValue > bValue) return 1 * order;
            }
            return 0;
        });
    }

    // Update table
    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
    
    // Reattach event listeners
    setupActionButtons();
}

async function moveToNextStage(candidateId) {
    if (!confirm('Czy na pewno chcesz przepchnąć kandydata do kolejnego etapu?')) return;
    
    setButtonLoading(`nextStageBtn_${candidateId}`, true);
    try {
        const response = await fetch(`/candidates/${candidateId}/next-stage`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (response.ok && data.success) {
            showToast('Kandydat został przeniesiony do następnego etapu', 'success');
            await refreshTable(true);
        } else {
            throw new Error(data.error || 'Network response was not ok');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Błąd podczas zmiany etapu', 'error');
    } finally {
        setButtonLoading(`nextStageBtn_${candidateId}`, false);
    }
}

async function rejectCandidate(candidateId) {
    if (!confirm('Czy na pewno chcesz odrzucić kandydata?')) return;
    
    setButtonLoading(`rejectBtn_${candidateId}`, true);
    try {
        const response = await fetch(`/candidates/${candidateId}/reject`, {
            method: 'POST'
        });
        if (response.ok) {
            showToast('Kandydat został odrzucony', 'success');
            await refreshTable(true);
        } else {
            throw new Error('Network response was not ok');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Błąd podczas odrzucania kandydata', 'error');
    } finally {
        setButtonLoading(`rejectBtn_${candidateId}`, false);
    }
}

async function acceptCandidate(candidateId) {
    if (!confirm('Czy na pewno chcesz zaakceptować kandydata?')) return;
    
    setButtonLoading(`acceptBtn_${candidateId}`, true);
    try {
        const response = await fetch(`/candidates/${candidateId}/accept`, {
            method: 'POST'
        });
        if (response.ok) {
            showToast('Kandydat został zaakceptowany', 'success');
            await refreshTable(true);
        } else {
            throw new Error('Network response was not ok');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Błąd podczas akceptowania kandydata', 'error');
    } finally {
        setButtonLoading(`acceptBtn_${candidateId}`, false);
    }
}

async function deleteCandidate(candidateId) {
    if (!confirm('Czy na pewno chcesz usunąć tę aplikację? Ta operacja jest nieodwracalna.')) return;
    
    setButtonLoading(`deleteBtn_${candidateId}`, true);
    try {
        const response = await fetch(`/candidates/${candidateId}/delete`, {
            method: 'POST'
        });
        if (response.ok) {
            showToast('Aplikacja została usunięta', 'success');
            await refreshTable(true);
        } else {
            throw new Error('Network response was not ok');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Błąd podczas usuwania aplikacji', 'error');
    } finally {
        setButtonLoading(`deleteBtn_${candidateId}`, false);
    }
}

window.recalculateScores = async function(candidateId) {
    if (!confirm('Czy na pewno chcesz przeliczyć punkty tego kandydata?')) return;
    
    setButtonLoading(`recalculateBtn_${candidateId}`, true);
    try {
        const response = await fetch(`/candidates/${candidateId}/recalculate`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (response.ok) {
            showToast('Punkty zostały przeliczone', 'success');
            if (data.status_changed) {
                showToast('Status kandydata został zmieniony!', 'warning');
            }
            await refreshTable(true);
        } else {
            throw new Error(data.error || 'Network response was not ok');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Błąd podczas przeliczania punktów', 'error');
    } finally {
        setButtonLoading(`recalculateBtn_${candidateId}`, false);
    }
};

window.toggleNewNoteForm = function() {
    const form = document.getElementById('newNoteForm');
    if (form.classList.contains('d-none')) {
        form.classList.remove('d-none');
        document.getElementById('noteType').value = '';
        document.getElementById('noteContent').value = '';
        document.getElementById('noteType').focus();
    } else {
        form.classList.add('d-none');
    }
};

window.saveNote = async function(candidateId) {
    const noteType = document.getElementById('noteType').value.trim();
    const noteContent = document.getElementById('noteContent').value.trim();
    
    if (!noteType || !noteContent) {
        showToast('Wypełnij wszystkie pola', 'error');
        return;
    }
    
    const saveButton = document.querySelector('#newNoteForm .btn-primary');
    setButtonLoading(saveButton, true);
    
    try {
        const response = await fetch(`/candidates/${candidateId}/notes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                note_type: noteType,
                content: noteContent
            })
        });
        
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        showToast('Notatka została zapisana', 'success');
        toggleNewNoteForm();
        await viewCandidate(candidateId);
        
    } catch (error) {
        console.error('Error:', error);
        showToast('Błąd podczas zapisywania notatki', 'error');
    } finally {
        setButtonLoading(saveButton, false);
    }
};

window.deleteNote = async function(candidateId, noteId) {
    if (!confirm('Czy na pewno chcesz usunąć tę notatkę?')) return;
    
    try {
        const response = await fetch(`/candidates/${candidateId}/notes/${noteId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        showToast('Notatka została usunięta', 'success');
        await viewCandidate(candidateId);
        
    } catch (error) {
        console.error('Error:', error);
        showToast('Błąd podczas usuwania notatki', 'error');
    }
};

function initializeCopyLinks() {
    document.querySelectorAll('.copy-link').forEach(button => {
        button.addEventListener('click', function() {
            const link = this.dataset.link;
            const fullLink = link.startsWith('http') ? link : window.location.origin + link;
            
            navigator.clipboard.writeText(fullLink)
                .then(() => {
                    showToast('Link został skopiowany do schowka', 'success');
                })
                .catch(err => {
                    console.error('Failed to copy:', err);
                    showToast('Nie udało się skopiować linku', 'error');
                });
        });
    });
}

function setButtonLoading(buttonId, isLoading) {
    const button = document.getElementById(buttonId);
    if (!button) return;
    
    const spinner = button.querySelector('.spinner-border');
    const buttonText = button.querySelector('.button-text');
    
    button.disabled = isLoading;
    if (isLoading) {
        spinner.classList.remove('d-none');
        buttonText.style.opacity = '0.5';
    } else {
        spinner.classList.add('d-none');
        buttonText.style.opacity = '1';
    }
}

let currentSorts = [];
let originalRows = [];

document.addEventListener('DOMContentLoaded', function() {
    // Store original table rows
    const tbody = document.querySelector('tbody');
    originalRows = Array.from(tbody.querySelectorAll('tr'));
    
    // Initialize filters and event listeners
    initializeFilters();
    initializeEventListeners();
    
    // Initialize sortable headers
    initializeSortableHeaders();

    // Bulk recalculation button
    document.getElementById('bulkRecalculateBtn').addEventListener('click', bulkRecalculateScores);
});

function initializeFilters() {
    // Zaznacz wszystkie checkboxy na starcie
    document.querySelectorAll('.filter-campaign, .filter-status').forEach(checkbox => {
        checkbox.checked = true;
    });
    
    // Zaznacz checkboxy "Zaznacz wszystkie" na starcie
    document.querySelectorAll('.select-all-campaigns, .select-all-statuses').forEach(checkbox => {
        checkbox.checked = true;
    });
    
    // Zaktualizuj tekst w dropdownach na starcie
    document.querySelectorAll('.dropdown').forEach(dropdown => {
        const selectedSpan = dropdown.querySelector('.selected-options');
        const checkboxes = dropdown.querySelectorAll('input[type="checkbox"]:not([class*="select-all"])');
        if (checkboxes.length > 0) {
            updateSelectedOptionsText(checkboxes[0]);
        }
    });
}

function initializeEventListeners() {
    // Initialize filters with instant update
    document.querySelectorAll('.filter-campaign, .filter-status').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            // Aktualizuj stan checkboxa "Zaznacz wszystkie"
            const isFilterCampaign = checkbox.classList.contains('filter-campaign');
            const selectAllCheckbox = isFilterCampaign ? 
                document.querySelector('.select-all-campaigns') : 
                document.querySelector('.select-all-statuses');
            const relatedCheckboxes = isFilterCampaign ? 
                document.querySelectorAll('.filter-campaign') : 
                document.querySelectorAll('.filter-status');
            
            const allChecked = Array.from(relatedCheckboxes).every(cb => cb.checked);
            selectAllCheckbox.checked = allChecked;
            
            updateSelectedOptionsText(this);
            refreshTable(false);
        });
    });

    // Obsługa checkboxów "Zaznacz wszystkie"
    document.querySelector('.select-all-campaigns').addEventListener('change', function() {
        const campaignCheckboxes = document.querySelectorAll('.filter-campaign');
        campaignCheckboxes.forEach(cb => {
            cb.checked = this.checked;
        });
        if (campaignCheckboxes.length > 0) {
            updateSelectedOptionsText(campaignCheckboxes[0]);
        }
        refreshTable(false);
    });

    document.querySelector('.select-all-statuses').addEventListener('change', function() {
        const statusCheckboxes = document.querySelectorAll('.filter-status');
        statusCheckboxes.forEach(cb => {
            cb.checked = this.checked;
        });
        if (statusCheckboxes.length > 0) {
            updateSelectedOptionsText(statusCheckboxes[0]);
        }
        refreshTable(false);
    });

    // Search input with debounce
    const searchInput = document.getElementById('searchText');
    let debounceTimer;
    searchInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            refreshTable(false);
        }, 300);
    });

    // Stop dropdown from closing on click inside
    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        menu.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });

    // Reset filters
    document.getElementById('resetFiltersBtn').addEventListener('click', function() {
        document.getElementById('searchText').value = '';
        
        // Zaznacz wszystkie checkboxy
        document.querySelectorAll('.filter-campaign, .filter-status, .select-all-campaigns, .select-all-statuses').forEach(checkbox => {
            checkbox.checked = true;
        });
        
        // Zaktualizuj tekst w dropdownach
        document.querySelectorAll('.dropdown').forEach(dropdown => {
            const selectedSpan = dropdown.querySelector('.selected-options');
            const checkboxes = dropdown.querySelectorAll('input[type="checkbox"]:not([class*="select-all"])');
            if (checkboxes.length > 0) {
                updateSelectedOptionsText(checkboxes[0]);
            }
        });
        
        // Reset sorting
        document.querySelectorAll('th.sortable').forEach(header => {
            header.classList.remove('asc', 'desc');
            const orderIndicator = header.querySelector('.sort-order');
            if (orderIndicator) {
                orderIndicator.remove();
            }
        });
        currentSorts = [];
        
        refreshTable(false);
    });
}

function updateSelectedOptionsText(checkbox) {
    const dropdownButton = checkbox.closest('.dropdown').querySelector('button');
    const selectedSpan = dropdownButton.querySelector('.selected-options');
    const checkboxes = checkbox.closest('.dropdown-menu').querySelectorAll('input[type="checkbox"]:not([class*="select-all"])');
    const selectedOptions = Array.from(checkboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.nextElementSibling.textContent.trim());
    
    if (selectedOptions.length === checkboxes.length) {
        selectedSpan.textContent = checkbox.classList.contains('filter-campaign') ? 'Wszystkie kampanie' : 'Wszystkie statusy';
    } else if (selectedOptions.length === 0) {
        selectedSpan.textContent = '-';
    } else {
        selectedSpan.textContent = selectedOptions.join(', ');
    }
}

function initializeSortableHeaders() {
    const headers = document.querySelectorAll('th.sortable');
    headers.forEach(header => {
        header.addEventListener('click', function() {
            const sortField = this.dataset.sort;
            const currentDirection = this.classList.contains('asc') ? 'asc' : 
                                   this.classList.contains('desc') ? 'desc' : null;
            
            // Update sort direction
            let newDirection;
            if (!currentDirection) {
                newDirection = 'asc';
            } else if (currentDirection === 'asc') {
                newDirection = 'desc';
            } else {
                // Remove sorting for this column
                this.classList.remove('desc');
                // Remove order indicator
                const orderIndicator = this.querySelector('.sort-order');
                if (orderIndicator) {
                    orderIndicator.remove();
                }
                currentSorts = currentSorts.filter(sort => sort.field !== sortField);
                // Update numbering of remaining sorts
                currentSorts.forEach((sort, index) => {
                    const header = document.querySelector(`th[data-sort="${sort.field}"]`);
                    const indicator = header.querySelector('.sort-order');
                    if (indicator) {
                        indicator.textContent = index + 1;
                    }
                });
                refreshTable(false);
                return;
            }

            // Remove existing sort for this field
            currentSorts = currentSorts.filter(sort => sort.field !== sortField);
            
            // Add new sort
            currentSorts.push({
                field: sortField,
                direction: newDirection,
                order: currentSorts.length + 1
            });

            // Update classes and indicators
            this.classList.remove('asc', 'desc');
            this.classList.add(newDirection);

            // Update or add order indicator
            let orderIndicator = this.querySelector('.sort-order');
            if (!orderIndicator) {
                orderIndicator = document.createElement('span');
                orderIndicator.className = 'sort-order';
                this.appendChild(orderIndicator);
            }
            orderIndicator.textContent = currentSorts.length;

            refreshTable(false);
        });
    });
}

function setupActionButtons() {
    // Przyciski kopiowania linków
    document.querySelectorAll('.copy-link').forEach(btn => {
        btn.addEventListener('click', function() {
            const link = this.dataset.link;
            navigator.clipboard.writeText(link)
                .then(() => showToast('Link został skopiowany do schowka', 'success'))
                .catch(() => showToast('Nie udało się skopiować linku', 'error'));
        });
    });
}

function applyFilters() {
    const campaign = document.getElementById('campaign-filter').value;
    const status = document.getElementById('status-filter').value;
    const search = document.getElementById('search-input').value;
    const sortBy = document.getElementById('sort-by').value;
    const sortOrder = document.getElementById('sort-order').value;

    const params = new URLSearchParams({
        campaign_code: campaign,
        status: status,
        search: search,
        sort_by: sortBy,
        sort_order: sortOrder
    });

    window.location.href = `${window.location.pathname}?${params.toString()}`;
}

window.editNote = function(candidateId, noteId, noteType, noteContent) {
    // Wypełnij formularz danymi notatki
    const form = document.getElementById('newNoteForm');
    const typeInput = document.getElementById('noteType');
    const contentInput = document.getElementById('noteContent');
    const saveButton = form.querySelector('.btn-primary');
    
    // Pokaż formularz i wypełnij danymi
    form.classList.remove('d-none');
    typeInput.value = noteType;
    contentInput.value = noteContent;
    
    // Zmień funkcję przycisku Zapisz
    saveButton.onclick = async function() {
        const updatedType = typeInput.value.trim();
        const updatedContent = contentInput.value.trim();
        
        if (!updatedType || !updatedContent) {
            showToast('Wypełnij wszystkie pola', 'error');
            return;
        }
        
        setButtonLoading(saveButton, true);
        
        try {
            const response = await fetch(`/candidates/${candidateId}/notes/${noteId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    note_type: updatedType,
                    content: updatedContent
                })
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            showToast('Notatka została zaktualizowana', 'success');
            toggleNewNoteForm();
            await viewCandidate(candidateId);
            
        } catch (error) {
            console.error('Error:', error);
            showToast('Błąd podczas aktualizacji notatki', 'error');
        } finally {
            setButtonLoading(saveButton, false);
            // Przywróć oryginalną funkcję przycisku
            saveButton.onclick = () => saveNote(candidateId);
        }
    };
}; 

window.addNote = async function(candidateId) {
    // Clear previous form data
    document.getElementById('noteType').value = '';
    document.getElementById('noteContent').value = '';
    
    // Store candidateId for later use
    document.getElementById('saveNoteBtn').setAttribute('data-candidate-id', candidateId);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('addNoteModal'));
    modal.show();
}; 

function formatDateTime(date) {
    return date.toLocaleDateString('pl-PL', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).replace(',', '');
}

window.regenerateToken = function(candidateId, stage) {
    console.log('Regenerating token for:', {candidateId, stage});
    
    if (!confirm('Czy na pewno chcesz wygenerować nowy token? Stary token przestanie działać.')) {
        console.log('User cancelled');
        return;
    }
    
    fetch(`/candidates/${candidateId}/regenerate-token/${stage}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        console.log('Response data:', data);
        if (data.success) {
            // Aktualizuj wartości w sekcji tokenu
            const tokenSection = document.querySelector(`.token-section[data-stage="${stage}"]`);
            if (tokenSection) {
                // Aktualizuj link
                const linkInput = tokenSection.querySelector('input[type="text"]');
                const copyButton = tokenSection.querySelector('.copy-link');
                const newLink = `${window.location.origin}/test/candidate/${data.token}`;
                
                if (linkInput) linkInput.value = newLink;
                if (copyButton) copyButton.dataset.link = newLink;
                
                // Aktualizuj datę wygaśnięcia
                const expirySpan = tokenSection.querySelector(`#expiryTime${stage}`);
                if (expirySpan) {
                    const expiryDate = new Date(data.new_expiry);
                    expirySpan.textContent = formatDateTime(expiryDate);
                }
                
                // Aktualizuj status
                const statusBadge = tokenSection.querySelector('.badge');
                if (statusBadge) {
                    statusBadge.className = 'badge bg-success ms-2';
                    statusBadge.textContent = 'Niewykorzystany';
                }
            }
            
            showToast(data.message, 'success');
        } else {
            throw new Error(data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast(error.message, 'error');
    });
};

let isRecalculationCancelled = false;
let recalculationModal = null;

async function bulkRecalculateScores() {
    // Get all visible candidate IDs from the table
    const visibleRows = document.querySelectorAll('#candidatesTable tbody tr');
    const candidateIds = Array.from(visibleRows).map(row => {
        const recalculateBtn = row.querySelector('[id^="recalculateBtn_"]');
        return recalculateBtn ? recalculateBtn.id.replace('recalculateBtn_', '') : null;
    }).filter(id => id);

    if (candidateIds.length === 0) {
        showToast('Brak kandydatów do przeliczenia', 'warning');
        return;
    }

    // Reset cancellation flag
    isRecalculationCancelled = false;

    // Initialize and show modal
    recalculationModal = new bootstrap.Modal(document.getElementById('bulkRecalculateModal'));
    document.getElementById('totalCount').textContent = candidateIds.length;
    document.getElementById('processedCount').textContent = '0';
    document.querySelector('#bulkRecalculateModal .progress-bar').style.width = '0%';
    recalculationModal.show();

    // Process candidates sequentially
    let processedCount = 0;
    for (const candidateId of candidateIds) {
        if (isRecalculationCancelled) {
            showToast('Operacja została przerwana', 'warning');
            break;
        }

        try {
            const response = await fetch(`/candidates/${candidateId}/recalculate`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            processedCount++;
            updateRecalculationProgress(processedCount, candidateIds.length);

        } catch (error) {
            console.error('Error:', error);
            showToast('Wystąpił błąd podczas przeliczania punktów', 'error');
            break;
        }
    }

    // After completion
    if (!isRecalculationCancelled) {
        showToast('Przeliczanie punktów zakończone', 'success');
        setTimeout(() => {
            recalculationModal.hide();
            location.reload();
        }, 1000);
    }
}

function updateRecalculationProgress(processed, total) {
    const percentage = (processed / total) * 100;
    document.querySelector('#bulkRecalculateModal .progress-bar').style.width = `${percentage}%`;
    document.getElementById('processedCount').textContent = processed;
}

async function saveNoteFromList() {
    const noteType = document.getElementById('noteType').value.trim();
    const noteContent = document.getElementById('noteContent').value.trim();
    const candidateId = document.getElementById('saveNoteBtn').getAttribute('data-candidate-id');
    
    if (!noteType || !noteContent) {
        showToast('Wypełnij wszystkie pola', 'error');
        return;
    }
    
    const saveButton = document.getElementById('saveNoteBtn');
    setButtonLoading(saveButton, true);
    
    try {
        const response = await fetch(`/candidates/${candidateId}/notes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                note_type: noteType,
                content: noteContent
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Close the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addNoteModal'));
            modal.hide();
            
            // Clear the form
            document.getElementById('noteType').value = '';
            document.getElementById('noteContent').value = '';
            
            showToast('Notatka została zapisana', 'success');
            
            // If we're in candidate view, update the notes list
            const notesList = document.querySelector('.notes-list');
            if (notesList) {
                await updateNotesList(candidateId);
            }
        } else {
            throw new Error(data.error || 'Network response was not ok');
        }
        
    } catch (error) {
        console.error('Error:', error);
        showToast('Błąd podczas zapisywania notatki', 'error');
    } finally {
        setButtonLoading(saveButton, false);
    }
}

function getRowValue(row, sortField) {
    switch (sortField) {
        case 'name':
            return row.querySelector('td:nth-child(1)').textContent.toLowerCase();
        case 'campaign_code':
            return row.querySelector('td:nth-child(2)').textContent.toLowerCase();
        case 'email':
            return row.querySelector('td:nth-child(3)').textContent.toLowerCase();
        case 'phone':
            return row.querySelector('td:nth-child(4)').textContent.toLowerCase();
        case 'recruitment_status':
            const status = row.querySelector('td:nth-child(5) .badge').textContent.trim();
            const statusOrder = {
                'Odrzucony': 1,
                'Ankieta': 2,
                'Test EQ': 3,
                'Ocena EQ': 4,
                'Test IQ': 5,
                'Potencjał': 6,
                'Zaproszono na rozmowę': 7,
                'Oczekuje na decyzję': 8,
                'Zaakceptowany': 9
            };
            return statusOrder[status] || 0;
        case 'po1_score':
            return parseFloat(row.querySelector('td:nth-child(6)').textContent) || -Infinity;
        case 'po2_score':
            return parseFloat(row.querySelector('td:nth-child(7)').textContent) || -Infinity;
        case 'po2_5_score':
            return parseFloat(row.querySelector('td:nth-child(8)').textContent) || -Infinity;
        case 'po3_score':
            return parseFloat(row.querySelector('td:nth-child(9)').textContent) || -Infinity;
        case 'po4_score':
            return parseFloat(row.querySelector('td:nth-child(10)').textContent) || -Infinity;
        case 'total_score':
            return parseFloat(row.querySelector('td:nth-child(11)').textContent) || -Infinity;
        case 'created_at':
            const dateText = row.querySelector('td:nth-child(12)').textContent;
            const [datePart, timePart] = dateText.split(' ');
            const [day, month, year] = datePart.split('.');
            const [hours, minutes] = timePart.split(':');
            return new Date(year, month - 1, day, hours, minutes).getTime();
        default:
            return 0;
    }
}

async function inviteToInterview(candidateId) {
    if (!confirm('Czy na pewno chcesz zaprosić kandydata na rozmowę?')) return;
    
    setButtonLoading(`inviteBtn_${candidateId}`, true);
    try {
        const response = await fetch(`/candidates/${candidateId}/invite-to-interview`, {
            method: 'POST'
        });
        if (response.ok) {
            showToast('Kandydat został zaproszony na rozmowę', 'success');
            await refreshTable(true);
        } else {
            throw new Error('Network response was not ok');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Błąd podczas zapraszania kandydata na rozmowę', 'error');
    } finally {
        setButtonLoading(`inviteBtn_${candidateId}`, false);
    }
}

async function setAwaitingDecision(candidateId) {
    if (!confirm('Czy na pewno chcesz ustawić status oczekiwania na decyzję?')) return;
    
    setButtonLoading(`awaitingBtn_${candidateId}`, true);
    try {
        const response = await fetch(`/candidates/${candidateId}/set-awaiting-decision`, {
            method: 'POST'
        });
        if (response.ok) {
            showToast('Status kandydata został zmieniony na oczekujący', 'success');
            await refreshTable(true);
        } else {
            throw new Error('Network response was not ok');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Błąd podczas zmiany statusu kandydata', 'error');
    } finally {
        setButtonLoading(`awaitingBtn_${candidateId}`, false);
    }
}
