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
}); 