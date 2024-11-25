document.addEventListener('DOMContentLoaded', function() {
    let remainingSeconds = parseInt(localStorage.getItem('remainingSeconds')) || 0;
    let timeoutModalShown = false;
    let modalTimeoutId = null;
    let timerInterval;

    function updateTimer() {
        if (remainingSeconds <= 0) {  // Check first
            if (timerInterval) {
                clearInterval(timerInterval);
            }
            if (!timeoutModalShown) {
                showTimeoutModal();
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
        // let modalSeconds = 300;
        let modalSeconds = 30;
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
        document.getElementById('testForm').submit();
    }

    function cancelTest() {
        if (modalTimeoutId) clearTimeout(modalTimeoutId);
        window.location.href = "/test/" + window.location.pathname.split('/')[2] + "/cancel";
    }

    // Initial update and start interval
    if (document.getElementById('timer')) {
        updateTimer();
        timerInterval = setInterval(updateTimer, 1000);
    }

    // Make functions globally available
    window.submitTest = submitTest;
    window.cancelTest = cancelTest;
}); 