// Define functions in global scope
window.viewCandidate = async function(candidateId) {
    setButtonLoading(`viewBtn_${candidateId}`, true);
    try {
        const response = await fetch(`/candidates/${candidateId}`);
        const html = await response.text();
        document.getElementById('candidateModalBody').innerHTML = html;
        initializeCopyLinks();
        initializeExtendTokens();
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

window.moveToNextStage = async function(candidateId) {
    if (!confirm('Czy na pewno chcesz przepchnąć kandydata do kolejnego etapu?')) return;
    
    setButtonLoading(`nextStageBtn_${candidateId}`, true);
    try {
        const response = await fetch(`/candidates/${candidateId}/next-stage`, {
            method: 'POST'
        });
        if (response.ok) {
            location.reload();
        } else {
            throw new Error('Network response was not ok');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Błąd podczas zmiany etapu', 'error');
        setButtonLoading(`nextStageBtn_${candidateId}`, false);
    }
};

window.rejectCandidate = async function(candidateId) {
    if (!confirm('Czy na pewno chcesz odrzucić kandydata?')) return;
    
    setButtonLoading(`rejectBtn_${candidateId}`, true);
    try {
        const response = await fetch(`/candidates/${candidateId}/reject`, {
            method: 'POST'
        });
        if (response.ok) {
            location.reload();
        } else {
            throw new Error('Network response was not ok');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Błąd podczas odrzucania kandydata', 'error');
        setButtonLoading(`rejectBtn_${candidateId}`, false);
    }
};

window.acceptCandidate = async function(candidateId) {
    if (!confirm('Czy na pewno chcesz zaakceptować kandydata?')) return;
    
    setButtonLoading(`acceptBtn_${candidateId}`, true);
    try {
        const response = await fetch(`/candidates/${candidateId}/accept`, {
            method: 'POST'
        });
        if (response.ok) {
            location.reload();
        } else {
            throw new Error('Network response was not ok');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Błąd podczas akceptowania kandydata', 'error');
        setButtonLoading(`acceptBtn_${candidateId}`, false);
    }
};

window.deleteCandidate = async function(candidateId) {
    if (!confirm('Czy na pewno chcesz usunąć tę aplikację? Ta operacja jest nieodwracalna.')) return;
    
    setButtonLoading(`deleteBtn_${candidateId}`, true);
    try {
        const response = await fetch(`/candidates/${candidateId}/delete`, {
            method: 'POST'
        });
        if (response.ok) {
            location.reload();
        } else {
            throw new Error('Network response was not ok');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Błąd podczas usuwania aplikacji', 'error');
        setButtonLoading(`deleteBtn_${candidateId}`, false);
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

function initializeExtendTokens() {
    document.querySelectorAll('.extend-token').forEach(button => {
        button.addEventListener('click', async function() {
            const candidateId = this.dataset.candidateId;
            const stage = this.dataset.stage;
            
            if (confirm('Czy na pewno chcesz przedłużyć ważność tokenu o tydzień?')) {
                try {
                    const response = await fetch(`/candidates/${candidateId}/extend-token/${stage}`, {
                        method: 'POST'
                    });
                    const data = await response.json();
                    
                    if (data.success) {
                        showToast('Token został przedłużony', 'success');
                        
                        // Fetch updated candidate data
                        const candidateResponse = await fetch(`/candidates/${candidateId}`);
                        const updatedHtml = await candidateResponse.text();
                        
                        // Create a temporary container to parse the HTML
                        const tempDiv = document.createElement('div');
                        tempDiv.innerHTML = updatedHtml;
                        
                        // Find the specific expiry date element to update
                        const currentExpiryDate = document.querySelector(
                            `.token-expiry[data-stage="${stage}"]`
                        );
                        const newExpiryDate = tempDiv.querySelector(
                            `.token-expiry[data-stage="${stage}"]`
                        );
                        
                        if (currentExpiryDate && newExpiryDate) {
                            currentExpiryDate.innerHTML = newExpiryDate.innerHTML;
                        }
                    } else {
                        throw new Error(data.error || 'Wystąpił błąd');
                    }
                } catch (error) {
                    showToast(error.message, 'error');
                }
            }
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

// Store original rows globally
let originalRows = [];

document.addEventListener('DOMContentLoaded', function() {
    // Store original table rows
    const tbody = document.querySelector('tbody');
    originalRows = Array.from(tbody.querySelectorAll('tr'));
    
    // Initialize event listeners
    initializeEventListeners();
    
    // Setup action buttons
    setupActionButtons();
});

function initializeEventListeners() {
    // Store original table rows
    const tbody = document.querySelector('tbody');
    originalRows = Array.from(tbody.querySelectorAll('tr'));
    
    // Initialize filters with instant update
    document.querySelectorAll('.filter-campaign, .filter-status').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateSelectedOptionsText(this);
            updateTable(true);
        });
    });

    // Search input with debounce
    const searchInput = document.getElementById('searchText');
    let debounceTimer;
    searchInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            updateTable(true);
        }, 300);
    });

    // Sort controls with instant update
    document.getElementById('sortBy').addEventListener('change', () => updateTable(true));
    document.getElementById('sortOrder').addEventListener('change', () => updateTable(true));

    // Stop dropdown from closing on click inside
    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        menu.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });

    // Reset filters
    document.getElementById('resetFiltersBtn').addEventListener('click', function() {
        document.getElementById('searchText').value = '';
        document.querySelectorAll('.filter-campaign, .filter-status').forEach(checkbox => {
            checkbox.checked = false;
        });
        document.querySelectorAll('.selected-options').forEach(span => {
            span.textContent = span.closest('.dropdown').querySelector('button').textContent.includes('kampanie') ? 
                'Wszystkie kampanie' : 'Wszystkie statusy';
        });
        document.getElementById('sortBy').value = 'created_at';
        document.getElementById('sortOrder').value = 'desc';
        updateTable(false);
    });
}

function updateSelectedOptionsText(checkbox) {
    const dropdownButton = checkbox.closest('.dropdown').querySelector('button');
    const selectedSpan = dropdownButton.querySelector('.selected-options');
    const checkboxes = checkbox.closest('.dropdown-menu').querySelectorAll('input[type="checkbox"]');
    const selectedOptions = Array.from(checkboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.nextElementSibling.textContent);
    
    selectedSpan.textContent = selectedOptions.length > 0 ? 
        selectedOptions.join(', ') : 
        checkbox.classList.contains('filter-campaign') ? 'Wszystkie kampanie' : 'Wszystkie statusy';
}

function updateTable(applyFilters) {
    const tbody = document.querySelector('tbody');
    const searchText = document.getElementById('searchText').value.toLowerCase();
    const selectedCampaigns = Array.from(document.querySelectorAll('.filter-campaign:checked'))
        .map(cb => cb.value);
    const selectedStatuses = Array.from(document.querySelectorAll('.filter-status:checked'))
        .map(cb => cb.value);
    const sortBy = document.getElementById('sortBy').value;
    const sortOrder = document.getElementById('sortOrder').value;
    
    if (!applyFilters) {
        tbody.innerHTML = '';
        originalRows.forEach(row => tbody.appendChild(row.cloneNode(true)));
        return;
    }

    let filteredRows = originalRows.filter(row => {
        const text = row.textContent.toLowerCase();
        const campaignCode = row.querySelector('td:nth-child(2)').textContent.trim();
        const status = row.querySelector('.badge').textContent.trim();
        
        const matchesSearch = !searchText || text.includes(searchText);
        const matchesCampaign = selectedCampaigns.length === 0 || selectedCampaigns.includes(campaignCode);
        const matchesStatus = selectedStatuses.length === 0 || selectedStatuses.includes(status);
        
        return matchesSearch && matchesCampaign && matchesStatus;
    });

    // Sort rows
    if (sortBy) {
        filteredRows.sort((a, b) => {
            const aValue = getRowValue(a, sortBy);
            const bValue = getRowValue(b, sortBy);
            const order = sortOrder === 'asc' ? 1 : -1;
            
            if (typeof aValue === 'string') {
                return aValue.localeCompare(bValue) * order;
            }
            return (aValue - bValue) * order;
        });
    }

    // Update table
    tbody.innerHTML = '';
    filteredRows.forEach(row => tbody.appendChild(row.cloneNode(true)));
    
    // Update URL
    const params = new URLSearchParams({
        search: searchText,
        campaign_code: selectedCampaigns.join(','),
        status: selectedStatuses.join(','),
        sort_by: sortBy,
        sort_order: sortOrder
    });
    
    window.history.pushState({}, '', `${window.location.pathname}?${params.toString()}`);
}

function getRowValue(row, sortBy) {
    // First get the cell based on the data attribute instead of fixed indices
    const cell = row.querySelector(`[data-sort="${sortBy}"]`);
    if (!cell) {
        console.warn(`No cell found with data-sort="${sortBy}"`);
        return null;
    }

    const value = cell.textContent.trim();

    // Handle numeric values
    if (['po1_score', 'po2_score', 'po2_5_score', 'po3_score', 'po4_score', 
         'total_score'].includes(sortBy)) {
        return value === '-' ? -Infinity : parseFloat(value);
    }

    // Handle dates
    if (sortBy === 'created_at') {
        return new Date(value).getTime();
    }

    return value;
}

function setupActionButtons() {
    // Przycisk następnego etapu
    document.querySelectorAll('.next-stage-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const candidateId = this.dataset.candidateId;
            moveToNextStage(candidateId);
        });
    });

    // Przycisk odrzucenia
    document.querySelectorAll('.reject-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const candidateId = this.dataset.candidateId;
            rejectCandidate(candidateId);
        });
    });

    // Przycisk akceptacji
    document.querySelectorAll('.accept-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const candidateId = this.dataset.candidateId;
            acceptCandidate(candidateId);
        });
    });

    // Przycisk usuwania
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const candidateId = this.dataset.candidateId;
            deleteCandidate(candidateId);
        });
    });
}

// Funkcje obsługi akcji
async function moveToNextStage(candidateId) {
    if (!confirm('Czy na pewno chcesz przenieść kandydata do następnego etapu?')) {
        return;
    }

    try {
        const response = await fetch(`/candidates/${candidateId}/next-stage`, {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            showToast('success', 'Kandydat został przeniesiony do następnego etapu');
            window.location.reload();
        } else {
            showToast('error', data.error || 'Wystąpił błąd');
        }
    } catch (error) {
        showToast('error', 'Wystąpił błąd podczas przenoszenia do następnego etapu');
    }
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
            location.reload();
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