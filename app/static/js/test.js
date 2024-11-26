document.addEventListener('DOMContentLoaded', function() {
    let remainingSeconds = parseInt(localStorage.getItem('remainingSeconds')) || 0;
    let timeoutModalShown = false;
    let modalTimeoutId = null;
    let timerInterval;

    function validateForm() {
        const form = document.getElementById('testForm');
        if (!form) return false;
        
        // Check all required fields
        const requiredFields = form.querySelectorAll('[required]');
        for (let field of requiredFields) {
            if (!field.value) {
                return false;
            }
            if (field.type === 'radio') {
                const radioGroup = form.querySelectorAll(`[name="${field.name}"]`);
                const checked = Array.from(radioGroup).some(radio => radio.checked);
                if (!checked) return false;
            }
        }
        return true;
    }

    function updateTimer() {
        if (remainingSeconds <= 0) {  // Check first
            if (timerInterval) {
                clearInterval(timerInterval);
            }
            if (!timeoutModalShown) {
                if (validateForm()) {
                    showTimeoutModal();
                } else {
                    cancelTest(); // Automatically cancel if form is invalid
                }
            }
            const timerElement = document.getElementById('timer');
            if (timerElement) {
                timerElement.textContent = "00:00";  // Ensure we show 00:00
            }
            return;
        }

        const minutes = Math.floor(remainingSeconds / 60);
        const seconds = remainingSeconds % 60;
        const timerElement = document.getElementById('timer');
        if (timerElement) {
            timerElement.textContent = 
                `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        }

        localStorage.setItem('remainingSeconds', remainingSeconds);
        remainingSeconds--;
    }

    function showTimeoutModal() {
        timeoutModalShown = true;
        const modal = new bootstrap.Modal(document.getElementById('timeoutModal'));
        modal.show();

        // Start 5-minute countdown for modal
        let modalSeconds = 10;
        const modalInterval = setInterval(() => {
            if (modalSeconds <= 0) {
                clearInterval(modalInterval);
                cancelTest();
                return;
            }
            const min = Math.floor(modalSeconds / 60);
            const sec = modalSeconds % 60;
            const modalCountdown = document.getElementById('modalCountdown');
            if (modalCountdown) {
                modalCountdown.textContent = 
                    `${min}:${String(sec).padStart(2, '0')}`;
            }
            modalSeconds--;
        }, 1000);

        modalTimeoutId = setTimeout(() => {
            clearInterval(modalInterval);
            cancelTest();
        }, 300000); // 5 minutes
    }

    function submitTest() {
        if (modalTimeoutId) clearTimeout(modalTimeoutId);
        if (validateForm()) {
            document.getElementById('testForm').submit();
        } else {
            cancelTest();
        }
    }

    function cancelTest() {
        if (modalTimeoutId) clearTimeout(modalTimeoutId);
        
        // Check if this is a candidate test based on URL pattern
        const pathParts = window.location.pathname.split('/');
        const isCandidateTest = pathParts.includes('candidate');
        
        if (isCandidateTest) {
            window.location.href = "/test/candidate/" + pathParts[3] + "/cancel";
        } else {
            window.location.href = "/test/" + pathParts[2] + "/cancel";
        }
    }

    // Initial update and start interval
    if (document.getElementById('timer')) {
        updateTimer();
        timerInterval = setInterval(updateTimer, 1000);
    }

    // Make functions globally available
    window.submitTest = submitTest;
    window.cancelTest = cancelTest;

    // Update form validation for groups
    ['addTestForm', 'editTestForm'].forEach(formId => {
        const form = document.getElementById(formId);
        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                let isValid = true;
                let errorMessage = '';

                // Reset all validation states
                form.querySelectorAll('.is-invalid').forEach(el => {
                    el.classList.remove('is-invalid');
                });
                form.querySelectorAll('.border-danger').forEach(el => {
                    el.classList.remove('border-danger');
                });

                // Validate required fields
                form.querySelectorAll('[required]').forEach(field => {
                    if (!field.value.trim()) {
                        field.classList.add('is-invalid');
                        isValid = false;
                        errorMessage = 'Uzupełnij wszystkie wymagane pola';
                    }
                });

                // Validate passing threshold
                const threshold = form.querySelector('[name="passing_threshold"]');
                if (threshold && (!threshold.value.trim() || isNaN(threshold.value))) {
                    threshold.classList.add('is-invalid');
                    isValid = false;
                    errorMessage = 'Wprowadź poprawny próg zaliczenia';
                }

                // Validate groups
                const checkedGroups = form.querySelectorAll('input[name="groups[]"]:checked');
                if (!checkedGroups.length) {
                    const groupsContainer = form.querySelector('#groupsContainer');
                    groupsContainer.classList.add('border-danger');
                    isValid = false;
                    errorMessage = 'Aby zapisać test, musisz wybrać przynajmniej jedną grupę';
                }

                if (!isValid) {
                    showToast(errorMessage, 'error');
                    return;
                }

                // If everything is valid, submit the form
                form.classList.add('was-validated');
                const formData = new FormData(form);
                
                fetch(form.action, {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.location.reload();
                    } else {
                        showToast(data.error || 'Wystąpił błąd podczas zapisywania', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showToast('Wystąpił błąd podczas zapisywania', 'error');
                });
            });

            // Reset validation state when any checkbox is clicked
            form.querySelectorAll('.group-checkbox').forEach(checkbox => {
                checkbox.addEventListener('change', function() {
                    const groupsContainer = this.closest('#groupsContainer');
                    const checkedGroups = form.querySelectorAll('input[name="groups[]"]:checked');
                    
                    if (checkedGroups.length) {
                        groupsContainer.classList.remove('border-danger');
                    }
                });
            });
        }
    });
}); 