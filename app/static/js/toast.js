function showToast(message, type = 'success') {
    // First try to find toast in current document
    let toast = document.getElementById('notificationToast');
    let toastMessage = document.getElementById('toastMessage');
    
    // If not found (modal context), try parent document
    if (!toast && window.parent && window.parent.document) {
        toast = window.parent.document.getElementById('notificationToast');
        toastMessage = window.parent.document.getElementById('toastMessage');
    }
    
    // If still not found, try to find in top document
    if (!toast && window.top && window.top.document) {
        toast = window.top.document.getElementById('notificationToast');
        toastMessage = window.top.document.getElementById('toastMessage');
    }
    
    // If no toast container found, create one
    if (!toast) {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed top-0 start-50 translate-middle-x p-3';
        container.style.zIndex = '1070';
        
        toast = document.createElement('div');
        toast.id = 'notificationToast';
        toast.className = 'toast border-0';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        const content = document.createElement('div');
        content.className = 'd-flex align-items-center justify-content-between p-3';
        
        toastMessage = document.createElement('span');
        toastMessage.id = 'toastMessage';
        toastMessage.style.fontSize = '1.1rem';
        
        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'btn-close btn-close-white ms-3';
        closeButton.setAttribute('data-bs-dismiss', 'toast');
        closeButton.addEventListener('click', function(e) {
            e.stopPropagation();
        });
        
        content.appendChild(toastMessage);
        content.appendChild(closeButton);
        toast.appendChild(content);
        container.appendChild(toast);
        document.body.appendChild(container);
    }
    
    // Reset classes
    toast.className = 'toast border-0';
    
    // Add styling based on type
    if (type === 'success') {
        toast.style.backgroundColor = '#198754';
        toast.style.borderLeft = '4px solid #146c43';
    } else {
        toast.style.backgroundColor = '#dc3545';
        toast.style.borderLeft = '4px solid #b02a37';
    }
    
    // Add common styles
    toast.classList.add('text-white');
    
    // Set message
    toastMessage.textContent = message;
    
    // Show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

// Helper function to check and show pending toasts
function checkPendingToast() {
    const pendingToast = sessionStorage.getItem('pendingToast');
    if (pendingToast) {
        try {
            const toastData = JSON.parse(pendingToast);
            showToast(toastData.message, toastData.type);
        } catch (error) {
            console.error('Error showing pending toast:', error);
        } finally {
            sessionStorage.removeItem('pendingToast');
        }
    }
}

// Export functions
window.showToast = showToast;
window.checkPendingToast = checkPendingToast; 