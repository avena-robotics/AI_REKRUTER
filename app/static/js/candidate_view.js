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
            showEditNoteModal(noteId, noteType, noteContent);
        });
    });

    // Obsługa usuwania notatek
    document.querySelectorAll('.delete-note').forEach(btn => {
        btn.addEventListener('click', function() {
            const noteId = this.dataset.noteId;
            deleteNote(noteId);
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
    document.getElementById('noteType').value = 'NEUTRAL';
    document.getElementById('noteContent').value = '';
    document.getElementById('noteModalLabel').textContent = 'Dodaj notatkę';
    
    noteModal.show();
}

function showEditNoteModal(noteId, noteType, noteContent) {
    const modal = document.getElementById('noteModal');
    noteModal = new bootstrap.Modal(modal);
    
    // Fill form with note data
    document.getElementById('noteId').value = noteId;
    document.getElementById('noteType').value = noteType;
    document.getElementById('noteContent').value = noteContent;
    document.getElementById('noteModalLabel').textContent = 'Edytuj notatkę';
    
    noteModal.show();
}

async function saveNote() {
    const noteId = document.getElementById('noteId').value;
    const noteType = document.getElementById('noteType').value;
    const content = document.getElementById('noteContent').value;
    const candidateId = document.querySelector('[data-candidate-id]').dataset.candidateId;

    if (!content) {
        showToast('error', 'Treść notatki jest wymagana');
        return;
    }

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
            showToast('success', noteId ? 'Notatka została zaktualizowana' : 'Notatka została dodana');
            window.location.reload();
        } else {
            showToast('error', data.error || 'Wystąpił błąd');
        }
    } catch (error) {
        showToast('error', 'Wystąpił błąd podczas zapisywania notatki');
    }
}

async function deleteNote(noteId) {
    if (!confirm('Czy na pewno chcesz usunąć tę notatkę?')) {
        return;
    }

    const candidateId = document.querySelector('[data-candidate-id]').dataset.candidateId;

    try {
        const response = await fetch(`/candidates/${candidateId}/notes/${noteId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            showToast('success', 'Notatka została usunięta');
            window.location.reload();
        } else {
            showToast('error', data.error || 'Wystąpił błąd');
        }
    } catch (error) {
        showToast('error', 'Wystąpił błąd podczas usuwania notatki');
    }
}