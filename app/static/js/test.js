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

    // Initialize bootstrap-select
    if ($('.selectpicker').length > 0) {
        console.log('Initializing selectpicker...'); // Debug log
        $('.selectpicker').selectpicker({
            noneSelectedText: 'Wybierz grupy...',
            selectAllText: 'Zaznacz wszystkie',
            deselectAllText: 'Odznacz wszystkie',
            selectedTextFormat: 'count > 2',
            countSelectedText: '{0} grup wybrano'
        });
    }

    // Add modal show event handlers
    ['addTestModal', 'editTestModal'].forEach(modalId => {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.addEventListener('show.bs.modal', function() {
                console.log('Modal showing...'); // Debug log
                setTimeout(() => {
                    $('.selectpicker').selectpicker('refresh');
                }, 0);
            });
        }
    });

    // Update editTest function
    window.editTest = function(testId) {
        fetch(`/tests/${testId}/data`)
            .then(response => response.json())
            .then(test => {
                console.log('Test data:', test); // Debug log
                const form = document.getElementById('editTestForm');
                form.action = `/tests/${testId}/edit`;
                
                // Populate basic test fields
                form.querySelector('[name="test_type"]').value = test.test_type || '';
                form.querySelector('[name="stage"]').value = test.stage || '';
                form.querySelector('[name="description"]').value = test.description || '';
                form.querySelector('[name="passing_threshold"]').value = test.passing_threshold || 0;
                form.querySelector('[name="time_limit_minutes"]').value = test.time_limit_minutes || '';

                // Set selected groups
                if (test.groups) {
                    test.groups.forEach(groupId => {
                        const checkbox = form.querySelector(`input[name="groups[]"][value="${groupId}"]`);
                        if (checkbox) {
                            checkbox.checked = true;
                        }
                    });
                }

                // Clear and populate questions
                const questionsContainer = form.querySelector('.questions-container');
                questionsContainer.innerHTML = '';
                
                if (test.questions?.length > 0) {
                    test.questions
                        .sort((a, b) => a.order_number - b.order_number)
                        .forEach(question => {
                            const questionHtml = createQuestionHtml(question);
                            questionsContainer.insertAdjacentHTML('beforeend', questionHtml);
                        });
                }

                // Show modal
                const modal = new bootstrap.Modal(document.getElementById('editTestModal'));
                modal.show();
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Błąd podczas ładowania danych testu', 'error');
            });
    };
}); 