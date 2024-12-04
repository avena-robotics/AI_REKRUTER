// Common functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });

    // Handle offcanvas click outside
    const sideMenu = document.getElementById('sideMenu');
    if (sideMenu) {
        document.addEventListener('click', function(event) {
            // Check if click is outside the offcanvas
            if (!sideMenu.contains(event.target) && 
                !event.target.closest('[data-bs-toggle="offcanvas"]')) {
                const offcanvas = bootstrap.Offcanvas.getInstance(sideMenu);
                if (offcanvas) {
                    offcanvas.hide();
                }
            }
        });
    }

    // Check for pending toast after page load
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
});

// Toast functionality
function showToast(message, type = 'success') {
    const toast = document.getElementById('notificationToast');
    const toastMessage = document.getElementById('toastMessage');
    
    // Reset classes
    toast.className = 'toast border-0';
    
    // Add styling based on type
    if (type === 'success') {
        toast.style.backgroundColor = '#198754';  // Bootstrap success color
        toast.style.borderLeft = '4px solid #146c43';  // Darker shade
    } else {
        toast.style.backgroundColor = '#dc3545';  // Bootstrap danger color
        toast.style.borderLeft = '4px solid #b02a37';  // Darker shade
    }
    
    // Add common styles
    toast.classList.add('text-white');
    
    // Set message
    toastMessage.textContent = message;
    
    // Show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

// Error handling
function handleFetchError(response) {
    if (!response.ok) {
        return response.json().then(data => {
            showToast(data.error || 'Wystąpił nieoczekiwany błąd', 'error');
            throw new Error(data.error || 'HTTP error');
        });
    }
    return response;
}

// Logout handling
function handleLogout() {
    fetch('/logout')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Store success message for next page
                sessionStorage.setItem('pendingToast', JSON.stringify({
                    message: data.message,
                    type: data.type
                }));
                window.location.href = data.redirect;
            } else {
                showToast(data.message || 'Wystąpił błąd podczas wylogowywania', 'error');
            }
        })
        .catch(error => {
            showToast('Wystąpił błąd podczas wylogowywania', 'error');
        });
} 