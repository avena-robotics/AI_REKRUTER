// Utility function to set button loading state
function setButtonLoading(buttonId, isLoading) {
    const button = typeof buttonId === 'string' ? document.getElementById(buttonId) : buttonId;
    if (!button) return;
    
    const spinner = button.querySelector('.spinner-border');
    const text = button.querySelector('.button-text');
    if (isLoading) {
        spinner?.classList.remove('d-none');
        text?.classList.add('d-none');
        button.disabled = true;
    } else {
        spinner?.classList.add('d-none');
        text?.classList.remove('d-none');
        button.disabled = false;
    }
}

// Function to show add note modal from list view
window.addNoteFromList = function(candidateId) {
    const modal = new bootstrap.Modal(document.getElementById('listAddNoteModal'));
    const saveBtn = document.getElementById('listSaveNoteBtn');
    if (!saveBtn) return;
    
    // Clear form
    const typeInput = document.getElementById('listNoteType');
    const contentInput = document.getElementById('listNoteContent');
    if (typeInput) typeInput.value = '';
    if (contentInput) contentInput.value = '';
    
    // Set up save button handler
    saveBtn.onclick = () => saveNote(candidateId, 'list');
    
    // Store candidate ID
    saveBtn.dataset.candidateId = candidateId;
    
    modal.show();
};

// Function to show add note modal in detailed view
window.showAddNoteModal = function(candidateId) {
    const form = document.getElementById('viewNoteForm');
    const saveBtn = document.getElementById('viewSaveNoteBtn');
    if (!form || !saveBtn) return;
    
    // Clear form
    const typeInput = document.getElementById('viewNoteType');
    const contentInput = document.getElementById('viewNoteContent');
    if (typeInput) typeInput.value = '';
    if (contentInput) contentInput.value = '';
    
    // Show form
    form.classList.remove('d-none');
    
    // Set up save button handler
    saveBtn.onclick = () => saveNote(candidateId, 'view');
};

// Function to hide add note modal in detailed view
window.hideAddNoteModal = function() {
    const form = document.getElementById('viewNoteForm');
    if (!form) return;
    form.classList.add('d-none');
};

// Function to refresh notes list
async function refreshNotesList(candidateId) {
    try {
        const response = await fetch(`/candidates/${candidateId}/notes/list`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const html = await response.text();
        const notesContainer = document.querySelector('.notes-list');
        if (notesContainer) {
            notesContainer.innerHTML = html;
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Wystąpił błąd podczas odświeżania listy notatek', 'error');
    }
}

// Function to save a note (works for both list and view)
async function saveNote(candidateId, context) {
    const isListContext = context === 'list';
    const typeInput = document.getElementById(isListContext ? 'listNoteType' : 'viewNoteType');
    const contentInput = document.getElementById(isListContext ? 'listNoteContent' : 'viewNoteContent');
    const saveBtn = document.getElementById(isListContext ? 'listSaveNoteBtn' : 'viewSaveNoteBtn');
    
    if (!typeInput || !contentInput || !saveBtn) {
        showToast('Błąd: Nie znaleziono elementów formularza', 'error');
        return;
    }
    
    const noteType = typeInput.value.trim();
    const content = contentInput.value.trim();
    
    if (!noteType || !content) {
        showToast('Wypełnij wszystkie pola', 'error');
        return;
    }
    
    setButtonLoading(saveBtn, true);
    
    try {
        const response = await fetch(`/candidates/${candidateId}/notes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                note_type: noteType,
                content: content
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        if (isListContext) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('listAddNoteModal'));
            if (modal) {
                modal.hide();
            }
        } else {
            hideAddNoteModal();
        }
        
        showToast('Notatka została dodana', 'success');
        await refreshNotesList(candidateId);
        
    } catch (error) {
        console.error('Error:', error);
        showToast('Wystąpił błąd podczas zapisywania notatki', 'error');
    } finally {
        setButtonLoading(saveBtn, false);
    }
}

// Function to update notes list
async function updateNotesList(candidateId) {
    try {
        // For view context, refresh the whole candidate view
        if (window.location.pathname.includes(`/candidates/${candidateId}`)) {
            window.location.reload();
            return;
        }
        
        // For list context, just close the modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('listAddNoteModal'));
        if (modal) {
            modal.hide();
            showToast('Notatka została dodana', 'success');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Wystąpił błąd podczas aktualizacji listy notatek', 'error');
    }
}

// Function to edit a note
window.editNote = function(candidateId, noteId, noteType, noteContent) {
    const form = document.getElementById('viewNoteForm');
    const typeInput = document.getElementById('viewNoteType');
    const contentInput = document.getElementById('viewNoteContent');
    const saveBtn = document.getElementById('viewSaveNoteBtn');
    
    if (!form || !typeInput || !contentInput || !saveBtn) {
        showToast('Błąd: Nie znaleziono elementów formularza', 'error');
        return;
    }
    
    // Show form and fill with data
    form.classList.remove('d-none');
    typeInput.value = noteType;
    contentInput.value = noteContent;
    
    // Set up save button handler for editing
    saveBtn.onclick = async function() {
        const updatedType = typeInput.value.trim();
        const updatedContent = contentInput.value.trim();
        
        if (!updatedType || !updatedContent) {
            showToast('Wypełnij wszystkie pola', 'error');
            return;
        }
        
        setButtonLoading(saveBtn, true);
        
        try {
            const response = await fetch(`/candidates/${candidateId}/notes/${noteId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    note_type: updatedType,
                    content: updatedContent
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            hideAddNoteModal();
            showToast('Notatka została zaktualizowana', 'success');
            await refreshNotesList(candidateId);
            
        } catch (error) {
            console.error('Error:', error);
            showToast('Błąd podczas aktualizacji notatki', 'error');
        } finally {
            setButtonLoading(saveBtn, false);
        }
    };
};

// Function to delete a note
window.deleteNote = async function(candidateId, noteId) {
    if (!confirm('Czy na pewno chcesz usunąć tę notatkę?')) {
        return;
    }
    
    try {
        const response = await fetch(`/candidates/${candidateId}/notes/${noteId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        showToast('Notatka została usunięta', 'success');
        await refreshNotesList(candidateId);
        
    } catch (error) {
        console.error('Error:', error);
        showToast('Wystąpił błąd podczas usuwania notatki', 'error');
    }
}; 