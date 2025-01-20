console.log('tokens.js loaded');

import { setButtonLoading } from '../utils/buttons.js';

// Function to format date and time
export function formatDateTime(date) {
    return date.toLocaleDateString('pl-PL', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).replace(',', '');
}

// Function to format time remaining
function formatTimeRemaining(diff) {
    if (diff <= 0) {
        return 'token wygasł';
    }

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    let timeText = [];
    if (days > 0) {
        timeText.push(`${days} ${days === 1 ? 'dzień' : 'dni'}`);
    }
    if (hours > 0 || days > 0) {
        timeText.push(`${hours} ${hours === 1 ? 'godzina' : hours < 5 ? 'godziny' : 'godzin'}`);
    }
    timeText.push(`${minutes} ${minutes === 1 ? 'minuta' : minutes < 5 ? 'minuty' : 'minut'}`);

    return timeText.join(' ');
}

// Function to initialize copy links
export function initializeCopyLinks() {
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

// Function to update time remaining displays
function updateTimeRemainingDisplays() {
    ['PO2', 'PO3'].forEach(stage => {
        const expirySpan = document.getElementById(`expiryTime${stage}`);
        const remainingSpan = document.getElementById(`timeRemaining${stage}`);
        
        if (expirySpan && remainingSpan) {
            const expiryText = expirySpan.textContent.trim();
            if (expiryText) {
                const [datePart, timePart] = expiryText.split(' ');
                const [day, month, year] = datePart.split('.');
                const [hours, minutes] = timePart.split(':');
                
                const expiryDate = new Date(year, month - 1, day, hours, minutes);
                const now = new Date();
                const diff = expiryDate - now;
                
                remainingSpan.textContent = `(${formatTimeRemaining(diff)})`;
            }
        }
    });
}

// Function to regenerate token
export async function regenerateToken(candidateId, stage) {
    if (!confirm('Czy na pewno chcesz wygenerować nowy token? Stary token przestanie działać, a już wykonany test zostanie usunięty.')) {
        return;
    }
    
    try {
        const response = await fetch(`/candidates/${candidateId}/regenerate-token/${stage}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Wystąpił błąd podczas generowania nowego tokenu');
        }
        
        const data = await response.json();
        
        // Update token section
        const tokenSection = document.querySelector(`.token-section[data-stage="${stage}"]`);
        if (tokenSection) {
            // Update link
            const linkInput = tokenSection.querySelector('input[type="text"]');
            const copyButton = tokenSection.querySelector('.copy-link');
            const newLink = `${window.location.origin}/test/candidate/${data.token}`;
            
            if (linkInput) linkInput.value = newLink;
            if (copyButton) copyButton.dataset.link = newLink;
            
            // Update expiry date
            const expirySpan = tokenSection.querySelector(`#expiryTime${stage}`);
            if (expirySpan && data.new_expiry) {
                const expiryDate = new Date(data.new_expiry);
                expirySpan.textContent = formatDateTime(expiryDate);
            }
            
            // Update status
            const statusBadge = tokenSection.querySelector('.badge');
            if (statusBadge) {
                statusBadge.className = 'badge bg-success ms-2';
                statusBadge.textContent = 'Niewykorzystany';
            }
        }
        
        showToast('Token został wygenerowany pomyślnie', 'success');
        
    } catch (error) {
        console.error('Error:', error);
        showToast(error.message, 'error');
    }
}

// Initialize token functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeCopyLinks();
    updateTimeRemainingDisplays();
    
    // Update time remaining every minute
    setInterval(updateTimeRemainingDisplays, 60000);
});

// Export functions to global scope
window.regenerateToken = regenerateToken;

console.log('tokens.js finished loading'); 