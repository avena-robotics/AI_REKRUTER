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
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            updateTable(true);
        });
    }

    // Filter buttons
    document.getElementById('applyFiltersBtn').addEventListener('click', function() {
        updateTable(true);
    });

    document.getElementById('resetFiltersBtn').addEventListener('click', function() {
        resetFilters();
    });
}

function updateTable(applyFilters) {
    const tbody = document.querySelector('tbody');
    const searchText = document.getElementById('searchText').value.toLowerCase();
    const filterCampaign = document.getElementById('filterCampaign').value;
    const filterStatus = document.getElementById('filterStatus').value;
    const sortBy = document.getElementById('sortBy').value;
    const sortOrder = document.getElementById('sortOrder').value;
    
    if (!applyFilters) {
        // Reset to original state
        tbody.innerHTML = '';
        originalRows.forEach(row => tbody.appendChild(row.cloneNode(true)));
        return;
    }

    // Filter rows
    let filteredRows = originalRows.filter(row => {
        const text = row.textContent.toLowerCase();
        const campaignCode = row.querySelector('td:nth-child(2)').textContent.trim();
        const status = row.querySelector('.badge').textContent.trim();
        
        const matchesSearch = !searchText || text.includes(searchText);
        const matchesCampaign = !filterCampaign || campaignCode === filterCampaign;
        const matchesStatus = !filterStatus || status === filterStatus;
        
        return matchesSearch && matchesCampaign && matchesStatus;
    });

    // Sort rows
    filteredRows.sort((a, b) => {
        let aValue = getRowValue(a, sortBy);
        let bValue = getRowValue(b, sortBy);
        
        if (sortOrder === 'desc') {
            [aValue, bValue] = [bValue, aValue];
        }
        
        if (typeof aValue === 'number' && typeof bValue === 'number') {
            return aValue - bValue;
        }
        return String(aValue).localeCompare(String(bValue));
    });

    // Update table
    tbody.innerHTML = '';
    filteredRows.forEach(row => {
        const newRow = row.cloneNode(true);
        tbody.appendChild(newRow);
    });
    
    // Update URL without page reload
    const params = new URLSearchParams({
        search: searchText,
        campaign_code: filterCampaign,
        status: filterStatus,
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
         'total_score', 'score_ko', 'score_re', 'score_w', 'score_in', 
         'score_pz', 'score_kz', 'score_dz', 'score_sw'].includes(sortBy)) {
        return value === '-' ? -Infinity : parseFloat(value);
    }

    // Handle dates
    if (sortBy === 'created_at') {
        return new Date(value).getTime();
    }

    return value;
}

function resetFilters() {
    document.getElementById('searchText').value = '';
    document.getElementById('filterCampaign').value = '';
    document.getElementById('filterStatus').value = '';
    document.getElementById('sortBy').value = 'created_at';
    document.getElementById('sortOrder').value = 'desc';
    
    updateTable(false);
    window.history.pushState({}, '', window.location.pathname);
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