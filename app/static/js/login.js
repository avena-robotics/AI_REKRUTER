function togglePassword() {
    const passwordInput = document.getElementById('password');
    const toggleIcon = document.getElementById('togglePasswordIcon');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleIcon.classList.remove('bi-eye-slash');
        toggleIcon.classList.add('bi-eye');
    } else {
        passwordInput.type = 'password';
        toggleIcon.classList.remove('bi-eye');
        toggleIcon.classList.add('bi-eye-slash');
    }
}

// Handle form submission
document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const form = this;
    const submitButton = form.querySelector('button[type="submit"]');
    const spinner = submitButton.querySelector('.spinner-border');
    const buttonText = submitButton.querySelector('.button-text');
    
    // Show loading state
    submitButton.disabled = true;
    spinner.classList.remove('d-none');
    buttonText.textContent = 'Logowanie...';
    
    fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: {
            'Accept': 'application/json'
        }
    })
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
            showToast(data.message, data.type);
            // Reset button state
            submitButton.disabled = false;
            spinner.classList.add('d-none');
            buttonText.textContent = 'Zaloguj';
        }
    })
    .catch(error => {
        showToast('Wystąpił błąd podczas logowania', 'error');
        // Reset button state
        submitButton.disabled = false;
        spinner.classList.add('d-none');
        buttonText.textContent = 'Zaloguj';
    });
});

// Check for pending toast after page load
document.addEventListener('DOMContentLoaded', function() {
    checkPendingToast();
}); 