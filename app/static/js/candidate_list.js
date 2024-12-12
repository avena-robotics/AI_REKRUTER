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

// Initialize on document load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all dropdowns
    if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap is not loaded!');
        return;
    }

    document.querySelectorAll('[data-bs-toggle="dropdown"]').forEach(function(dropdownToggle) {
        new bootstrap.Dropdown(dropdownToggle, {
            boundary: 'window'
        });
    });

    // Stop click propagation in dropdowns
    document.querySelectorAll('.dropdown-menu').forEach(function(dropdownMenu) {
        dropdownMenu.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });

    // Add note save handler
    document.getElementById('saveNoteBtn').addEventListener('click', async function() {
        const candidateId = this.getAttribute('data-candidate-id');
        const noteType = document.getElementById('noteType').value.trim();
        const noteContent = document.getElementById('noteContent').value.trim();
        
        if (!noteType || !noteContent) {
            showToast('Wypełnij wszystkie pola', 'error');
            return;
        }
        
        setButtonLoading('saveNoteBtn', true);
        
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
            
            // Hide modal and show success message
            bootstrap.Modal.getInstance(document.getElementById('addNoteModal')).hide();
            showToast('Notatka została zapisana', 'success');
            
            // If candidate modal is open, refresh it
            const candidateModal = document.getElementById('candidateModal');
            if (candidateModal.classList.contains('show')) {
                await viewCandidate(candidateId);
            }
            
        } catch (error) {
            console.error('Error:', error);
            showToast('Błąd podczas zapisywania notatki', 'error');
        } finally {
            setButtonLoading('saveNoteBtn', false);
        }
    });
}); 

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