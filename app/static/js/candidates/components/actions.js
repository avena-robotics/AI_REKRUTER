import { setButtonLoading } from '../utils/buttons.js';
import { refreshTable } from '../utils/table.js';

// Function to move candidate to next stage
export async function moveToNextStage(candidateId) {
    try {
        const button = document.getElementById(`nextStageBtn_${candidateId}`);
        if (!button) return;
        
        setButtonLoading(button, true);
        
        const response = await fetch(`/candidates/${candidateId}/next-stage`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Wystąpił błąd podczas przechodzenia do kolejnego etapu');
        }
        
        showToast('Kandydat został przeniesiony do kolejnego etapu', 'success');
        await refreshTable(true);
        
    } catch (error) {
        console.error('Error:', error);
        showToast(error.message, 'error');
    } finally {
        const button = document.getElementById(`nextStageBtn_${candidateId}`);
        if (button) setButtonLoading(button, false);
    }
}

// Function to reject candidate
export async function rejectCandidate(candidateId) {
    if (!confirm('Czy na pewno chcesz odrzucić tego kandydata?')) {
        return;
    }
    
    try {
        const button = document.getElementById(`rejectBtn_${candidateId}`);
        if (!button) return;
        
        setButtonLoading(button, true);
        
        const response = await fetch(`/candidates/${candidateId}/reject`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Wystąpił błąd podczas odrzucania kandydata');
        }
        
        showToast('Kandydat został odrzucony', 'success');
        await refreshTable(true);
        
    } catch (error) {
        console.error('Error:', error);
        showToast(error.message, 'error');
    } finally {
        const button = document.getElementById(`rejectBtn_${candidateId}`);
        if (button) setButtonLoading(button, false);
    }
}

// Function to accept candidate
export async function acceptCandidate(candidateId) {
    if (!confirm('Czy na pewno chcesz zaakceptować tego kandydata?')) {
        return;
    }
    
    try {
        const button = document.getElementById(`acceptBtn_${candidateId}`);
        if (!button) return;
        
        setButtonLoading(button, true);
        
        const response = await fetch(`/candidates/${candidateId}/accept`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Wystąpił błąd podczas akceptowania kandydata');
        }
        
        showToast('Kandydat został zaakceptowany', 'success');
        await refreshTable(true);
        
    } catch (error) {
        console.error('Error:', error);
        showToast(error.message, 'error');
    } finally {
        const button = document.getElementById(`acceptBtn_${candidateId}`);
        if (button) setButtonLoading(button, false);
    }
}

// Function to delete candidate
export async function deleteCandidate(candidateId) {
    if (!confirm('Czy na pewno chcesz usunąć tego kandydata? Ta operacja jest nieodwracalna.')) {
        return;
    }
    
    try {
        const button = document.getElementById(`deleteBtn_${candidateId}`);
        if (!button) return;
        
        setButtonLoading(button, true);
        
        const response = await fetch(`/candidates/${candidateId}/delete`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Wystąpił błąd podczas usuwania kandydata');
        }
        
        showToast('Kandydat został usunięty', 'success');
        await refreshTable(true);
        
    } catch (error) {
        console.error('Error:', error);
        showToast(error.message, 'error');
    } finally {
        const button = document.getElementById(`deleteBtn_${candidateId}`);
        if (button) setButtonLoading(button, false);
    }
}

// Function to set awaiting decision
export async function setAwaitingDecision(candidateId) {
    try {
        const button = document.getElementById(`awaitingBtn_${candidateId}`);
        if (!button) return;
        
        setButtonLoading(button, true);
        
        const response = await fetch(`/candidates/${candidateId}/set-awaiting-decision`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Wystąpił błąd podczas ustawiania statusu oczekiwania na decyzję');
        }
        
        showToast('Status kandydata został zmieniony na "Oczekuje na decyzję"', 'success');
        await refreshTable(true);
        
    } catch (error) {
        console.error('Error:', error);
        showToast(error.message, 'error');
    } finally {
        const button = document.getElementById(`awaitingBtn_${candidateId}`);
        if (button) setButtonLoading(button, false);
    }
}

// Function to recalculate scores
export async function recalculateScores(candidateId) {
    try {
        const button = document.getElementById(`recalculateBtn_${candidateId}`);
        if (!button) return;
        
        setButtonLoading(button, true);
        
        const response = await fetch(`/candidates/${candidateId}/recalculate`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Wystąpił błąd podczas przeliczania punktów');
        }
        
        showToast('Punkty zostały przeliczone', 'success');
        await refreshTable(true);
        
    } catch (error) {
        console.error('Error:', error);
        showToast(error.message, 'error');
    } finally {
        const button = document.getElementById(`recalculateBtn_${candidateId}`);
        if (button) setButtonLoading(button, false);
    }
}

// Function to view candidate details
export async function viewCandidate(candidateId) {
    try {
        const button = document.getElementById(`viewBtn_${candidateId}`);
        if (button) setButtonLoading(button, true);
        
        const response = await fetch(`/candidates/${candidateId}`);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Wystąpił błąd podczas pobierania danych kandydata');
        }
        
        const html = await response.text();
        
        const modalBody = document.getElementById('candidateModalBody');
        if (modalBody) {
            modalBody.innerHTML = html;
            // Initialize details view after loading content
            if (typeof initializeDetailsView === 'function') {
                initializeDetailsView();
            } else {
                console.error('initializeDetailsView function not found!');
            }
        } else {
            console.error('Modal body element not found!');
        }
        
        const modal = new bootstrap.Modal(document.getElementById('candidateModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error:', error);
        showToast(error.message, 'error');
    } finally {
        const button = document.getElementById(`viewBtn_${candidateId}`);
        if (button) setButtonLoading(button, false);
    }
}

// Function to bulk recalculate scores
export async function bulkRecalculateScores() {
    // Get candidates list first
    const candidates = Array.from(document.querySelectorAll('#candidatesTable tbody tr'))
        .filter(row => row.style.display !== 'none')
        .map(row => {
            const id = row.querySelector('.dropdown-menu').getAttribute('aria-labelledby').replace('dropdownMenuButton', '');
            return { id };
        });
    
    const total = candidates.length;
    
    // Reset and initialize modal state
    const progressBar = document.querySelector('#bulkRecalculateModal .progress-bar');
    const processedCount = document.getElementById('processedCount');
    const totalCount = document.getElementById('totalCount');
    
    if (progressBar) {
        progressBar.style.width = '0%';
        progressBar.setAttribute('aria-valuenow', 0);
    }
    if (processedCount) processedCount.textContent = '0';
    if (totalCount) totalCount.textContent = total.toString();
    
    const modal = new bootstrap.Modal(document.getElementById('bulkRecalculateModal'));
    modal.show();
    
    let isCancelled = false;
    const cancelButton = document.getElementById('cancelRecalculation');
    if (cancelButton) {
        cancelButton.onclick = () => {
            isCancelled = true;
            modal.hide();
        };
    }
    
    try {
        let processed = 0;
        
        for (const candidate of candidates) {
            if (isCancelled) break;
            
            try {
                const response = await fetch(`/candidates/${candidate.id}/recalculate`, {
                    method: 'POST'
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    console.error(`Error recalculating scores for candidate ${candidate.id}:`, error);
                }
                
            } catch (error) {
                console.error(`Error recalculating scores for candidate ${candidate.id}:`, error);
            }
            
            processed++;
            updateRecalculationProgress(processed, total);
        }
        
        if (!isCancelled) {
            showToast('Punkty zostały przeliczone', 'success');
            await refreshTable(true);
        }
        
    } catch (error) {
        console.error('Error:', error);
        showToast('Wystąpił błąd podczas przeliczania punktów', 'error');
    } finally {
        modal.hide();
    }
}

// Function to update recalculation progress
function updateRecalculationProgress(processed, total) {
    const progressBar = document.querySelector('#bulkRecalculateModal .progress-bar');
    const processedCount = document.getElementById('processedCount');
    const totalCount = document.getElementById('totalCount');
    
    if (progressBar) {
        const percentage = (processed / total) * 100;
        progressBar.style.width = `${percentage}%`;
        progressBar.setAttribute('aria-valuenow', percentage);
    }
    
    if (processedCount) processedCount.textContent = processed;
    if (totalCount) totalCount.textContent = total;
}

// Export functions to global scope for HTML event handlers
Object.assign(window, {
    moveToNextStage,
    rejectCandidate,
    acceptCandidate,
    deleteCandidate,
    setAwaitingDecision,
    recalculateScores,
    viewCandidate,
    bulkRecalculateScores
}); 