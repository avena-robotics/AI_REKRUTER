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