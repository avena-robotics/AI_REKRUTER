document.addEventListener('DOMContentLoaded', function() {
    // Obsługa dodawania notatek
    const addNoteBtn = document.getElementById('add-note-btn');
    if (addNoteBtn) {
        addNoteBtn.addEventListener('click', showAddNoteModal);
    }

    // Obsługa edycji notatek
    document.querySelectorAll('.edit-note').forEach(btn => {
        btn.addEventListener('click', function() {
            const noteId = this.dataset.noteId;
            const noteType = this.dataset.noteType;
            const noteContent = this.dataset.noteContent;
            const userEmail = this.dataset.userEmail;
            showEditNoteModal(noteId, noteType, noteContent, userEmail);
        });
    });

    // Obsługa usuwania notatek
    document.querySelectorAll('.delete-note').forEach(btn => {
        btn.addEventListener('click', function() {
            if (confirm('Czy na pewno chcesz usunąć tę notatkę?')) {
                const noteId = this.dataset.noteId;
                deleteNote(noteId);
            }
        });
    });
});

// Modal notatek
let noteModal;

function showAddNoteModal() {
    const modal = document.getElementById('noteModal');
    noteModal = new bootstrap.Modal(modal);
    
    // Reset form
    document.getElementById('noteId').value = '';
    document.getElementById('noteType').value = '';
    document.getElementById('noteContent').value = '';
    document.getElementById('noteModalLabel').textContent = 'Dodaj notatkę';
    
    // Clear author info
    const authorInfo = document.getElementById('noteAuthorInfo');
    if (authorInfo) {
        authorInfo.textContent = '';
    }
    
    noteModal.show();
}

function showEditNoteModal(noteId, noteType, noteContent, userEmail) {
    const modal = document.getElementById('noteModal');
    noteModal = new bootstrap.Modal(modal);
    
    // Fill form with note data
    document.getElementById('noteId').value = noteId;
    document.getElementById('noteType').value = noteType;
    document.getElementById('noteContent').value = noteContent;
    document.getElementById('noteModalLabel').textContent = 'Edytuj notatkę';
    
    // Add author information
    const authorInfo = document.getElementById('noteAuthorInfo');
    if (authorInfo && userEmail) {
        authorInfo.innerHTML = `<i class="bi bi-person me-1"></i>Utworzone przez: ${userEmail}`;
    }
    
    noteModal.show();
}

async function saveNote() {
    const noteId = document.getElementById('noteId').value;
    const noteType = document.getElementById('noteType').value;
    const content = document.getElementById('noteContent').value;
    const candidateId = document.querySelector('[data-candidate-id]').dataset.candidateId;

    if (!noteType || !content) {
        showToast('Wypełnij wszystkie pola', 'error');
        return;
    }

    const saveBtn = document.querySelector('#noteModal .btn-primary');
    setButtonLoading(saveBtn, true);

    try {
        let url = `/candidates/${candidateId}/notes`;
        let method = 'POST';

        if (noteId) {
            url += `/${noteId}`;
            method = 'PUT';
        }

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                note_type: noteType,
                content: content
            })
        });

        const data = await response.json();

        if (data.success) {
            noteModal.hide();
            showToast(noteId ? 'Notatka została zaktualizowana' : 'Notatka została dodana', 'success');
            window.location.reload();
        } else {
            showToast(data.error || 'Wystąpił błąd', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Wystąpił błąd podczas zapisywania notatki', 'error');
    } finally {
        setButtonLoading(saveBtn, false);
    }
}

async function deleteNote(noteId) {
    const candidateId = document.querySelector('[data-candidate-id]').dataset.candidateId;

    try {
        const response = await fetch(`/candidates/${candidateId}/notes/${noteId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            showToast('Notatka została usunięta', 'success');
            window.location.reload();
        } else {
            showToast(data.error || 'Wystąpił błąd', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Wystąpił błąd podczas usuwania notatki', 'error');
    }
}

// Helper function to handle button loading state
function setButtonLoading(button, isLoading) {
    const spinner = button.querySelector('.spinner-border');
    const text = button.querySelector('.button-text');
    
    if (isLoading) {
        spinner.classList.remove('d-none');
        text.classList.add('d-none');
        button.disabled = true;
    } else {
        spinner.classList.add('d-none');
        text.classList.remove('d-none');
        button.disabled = false;
    }
}