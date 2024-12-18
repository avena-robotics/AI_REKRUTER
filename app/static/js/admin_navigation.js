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

    // Sidebar collapse functionality
    const sidebar = document.getElementById('sidebar');
    const content = document.getElementById('content');
    const sidebarCollapseBtn = document.getElementById('sidebarCollapseBtn');

    if (sidebarCollapseBtn) {
        sidebarCollapseBtn.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            content.classList.toggle('expanded');
            
            // Store the state in both localStorage and cookie
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed);
            document.cookie = `sidebarCollapsed=${isCollapsed}; path=/; max-age=31536000`; // 1 year
        });
    }

    // Groups collapse indicator
    const groupsToggle = document.querySelector('.groups-toggle');
    if (groupsToggle) {
        groupsToggle.addEventListener('click', function() {
            const isExpanded = this.getAttribute('aria-expanded') === 'true';
            const indicator = this.querySelector('.group-indicator');
            
            if (indicator) {
                indicator.style.transform = isExpanded ? 'rotate(0deg)' : 'rotate(180deg)';
            }
        });
    }

    // Handle responsive behavior
    function handleResize() {
        if (window.innerWidth <= 768) {
            sidebar.classList.add('collapsed');
            content.classList.add('expanded');
        }
    }

    window.addEventListener('resize', handleResize);
    handleResize(); // Initial check

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