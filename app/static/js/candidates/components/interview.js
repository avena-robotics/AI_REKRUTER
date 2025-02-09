import { setButtonLoading } from '../utils/buttons.js';
import { refreshTable } from '../utils/table.js';

let currentCandidateId = null;
let emailModal = null;
let quillEditor = null;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize modal
    const modalElement = document.getElementById('interviewEmailModal');
    if (modalElement) {
        emailModal = new bootstrap.Modal(modalElement);
    }
    
    // Initialize Quill editor
    const editorElement = document.getElementById('emailContentEditor');
    if (editorElement) {
        quillEditor = new Quill('#emailContentEditor', {
            theme: 'snow',
            modules: {
                toolbar: [
                    ['bold', 'italic', 'underline'],
                    [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                    ['clean']
                ]
            },
            placeholder: 'Wprowadź treść wiadomości...'
        });
        
        // Update hidden textarea when editor content changes
        quillEditor.on('text-change', function() {
            const textarea = document.getElementById('emailContent');
            if (textarea) {
                textarea.value = quillEditor.root.innerHTML;
            }
        });
    }
    
    // Add event listener for send button
    const sendButton = document.getElementById('sendInterviewEmailBtn');
    if (sendButton) {
        sendButton.addEventListener('click', sendInterviewEmail);
    }
});

async function showInterviewEmailModal(candidateId) {
    try {
        currentCandidateId = candidateId;
        
        // Reset form and editor
        const subjectInput = document.getElementById('emailSubject');
        if (subjectInput) {
            subjectInput.value = '';
        }
        
        if (quillEditor) {
            quillEditor.setText('');
        } else {
            console.error('Quill editor not initialized');
            throw new Error('Wystąpił błąd podczas inicjalizacji edytora');
        }
        
        // Fetch email template
        const response = await fetch(`/candidates/${candidateId}/interview-email-template`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Wystąpił błąd podczas pobierania szablonu email');
        }
        
        const template = await response.json();
        
        // Set subject and content
        if (subjectInput) {
            subjectInput.value = template.subject || '';
        }
        
        if (quillEditor) {
            quillEditor.root.innerHTML = template.content || '';
        }
        
        // Show modal
        if (emailModal) {
            emailModal.show();
        } else {
            throw new Error('Nie można otworzyć okna modalnego');
        }
        
    } catch (error) {
        console.error('Error:', error);
        showToast(error.message, 'error');
    }
}

async function sendInterviewEmail() {
    try {
        const button = document.getElementById('sendInterviewEmailBtn');
        if (!button) {
            throw new Error('Nie znaleziono przycisku wysyłania');
        }
        
        const spinner = button.querySelector('.spinner-border');
        const buttonText = button.querySelector('.button-text');
        
        // Get form data
        const subject = document.getElementById('emailSubject')?.value.trim() || '';
        const content = quillEditor?.root.innerHTML.trim() || '';
        
        if (!subject || !content) {
            throw new Error('Wypełnij wszystkie pola formularza');
        }
        
        // Disable button and show spinner
        button.disabled = true;
        if (spinner) spinner.classList.remove('d-none');
        if (buttonText) buttonText.textContent = 'Wysyłanie...';
        
        // Send request
        const response = await fetch(`/candidates/${currentCandidateId}/send-interview-email`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ subject, content })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Wystąpił błąd podczas wysyłania emaila');
        }
        
        // Hide modal and show success message
        if (emailModal) {
            emailModal.hide();
        }
        showToast('Email został wysłany', 'success');
        
        // Refresh the page to update candidate status
        window.location.reload();
        
    } catch (error) {
        console.error('Error:', error);
        showToast(error.message, 'error');
        
    } finally {
        // Reset button state
        const button = document.getElementById('sendInterviewEmailBtn');
        if (button) {
            const spinner = button.querySelector('.spinner-border');
            const buttonText = button.querySelector('.button-text');
            
            button.disabled = false;
            if (spinner) spinner.classList.add('d-none');
            if (buttonText) buttonText.textContent = 'Wyślij zaproszenie';
        }
    }
}

// Function to invite candidate to interview
export async function inviteToInterview(candidateId) {
    if (!confirm('Czy na pewno chcesz zaprosić kandydata na rozmowę?')) {
        return;
    }
    
    try {
        const button = document.getElementById(`inviteBtn_${candidateId}`);
        if (!button) return;
        
        setButtonLoading(button, true);
        
        const response = await fetch(`/candidates/${candidateId}/invite-to-interview`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Wystąpił błąd podczas zapraszania kandydata na rozmowę');
        }
        
        showToast('Kandydat został zaproszony na rozmowę', 'success');
        await refreshTable(true);
        
    } catch (error) {
        console.error('Error:', error);
        showToast(error.message, 'error');
    } finally {
        const button = document.getElementById(`inviteBtn_${candidateId}`);
        if (button) setButtonLoading(button, false);
    }
}

// Export functions to global scope
window.showInterviewEmailModal = showInterviewEmailModal;
window.sendInterviewEmail = sendInterviewEmail;
window.inviteToInterview = inviteToInterview; 