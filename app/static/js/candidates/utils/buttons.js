// Utility function to set button loading state
export function setButtonLoading(buttonId, isLoading) {
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