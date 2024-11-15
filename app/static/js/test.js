class TestTimer {
    constructor(minutes, displayElement) {
        this.timeLeft = minutes * 60;
        this.display = displayElement;
        this.interval = null;
    }

    start() {
        this.interval = setInterval(() => {
            this.timeLeft--;
            this.updateDisplay();
            this.checkWarnings();
            
            if (this.timeLeft <= 0) {
                this.stop();
                document.getElementById('testForm').submit();
            }
        }, 1000);
    }

    stop() {
        if (this.interval) {
            clearInterval(this.interval);
        }
    }

    updateDisplay() {
        const minutes = Math.floor(this.timeLeft / 60);
        const seconds = this.timeLeft % 60;
        this.display.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }

    checkWarnings() {
        const container = this.display.closest('.timer-container');
        const totalTime = this.initialTime;
        
        if (this.timeLeft <= 60) { // Last minute
            container.classList.remove('warning');
            container.classList.add('danger');
        } else if (this.timeLeft <= 300) { // Last 5 minutes
            container.classList.add('warning');
            container.classList.remove('danger');
        }
    }
}

class TestForm {
    constructor(formElement) {
        this.form = formElement;
        this.setupValidation();
        this.setupAutoSave();
    }

    setupValidation() {
        this.form.addEventListener('submit', (e) => {
            if (!this.validateForm()) {
                e.preventDefault();
                this.showValidationErrors();
            }
        });
    }

    validateForm() {
        const requiredQuestions = this.form.querySelectorAll('[required]');
        let isValid = true;
        
        requiredQuestions.forEach(question => {
            const questionCard = question.closest('.question-card');
            
            if (!this.isQuestionAnswered(question)) {
                isValid = false;
                questionCard.classList.add('border-danger');
            } else {
                questionCard.classList.remove('border-danger');
            }
        });
        
        return isValid;
    }

    isQuestionAnswered(question) {
        if (question.type === 'radio') {
            const name = question.name;
            const radioGroup = this.form.querySelectorAll(`input[name="${name}"]:checked`);
            return radioGroup.length > 0;
        }
        return question.value.trim() !== '';
    }

    showValidationErrors() {
        const firstError = this.form.querySelector('.border-danger');
        if (firstError) {
            firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        alert('Proszę odpowiedzieć na wszystkie wymagane pytania.');
    }

    setupAutoSave() {
        const inputs = this.form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('change', () => {
                this.saveProgress();
            });
        });
    }

    saveProgress() {
        const formData = new FormData(this.form);
        const answers = {};
        
        for (let [key, value] of formData.entries()) {
            answers[key] = value;
        }
        
        localStorage.setItem('testProgress', JSON.stringify({
            timestamp: new Date().toISOString(),
            answers: answers
        }));
    }

    loadProgress() {
        const saved = localStorage.getItem('testProgress');
        if (saved) {
            const data = JSON.parse(saved);
            
            for (let [key, value] of Object.entries(data.answers)) {
                const input = this.form.querySelector(`[name="${key}"]`);
                if (input) {
                    if (input.type === 'radio') {
                        const radio = this.form.querySelector(`[name="${key}"][value="${value}"]`);
                        if (radio) radio.checked = true;
                    } else {
                        input.value = value;
                    }
                }
            }
        }
    }
}

// Initialize when document is loaded
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('testForm');
    const timerDisplay = document.getElementById('timer');
    
    if (form) {
        const testForm = new TestForm(form);
        testForm.loadProgress();
    }
    
    if (timerDisplay) {
        const minutes = parseInt(timerDisplay.textContent);
        const timer = new TestTimer(minutes, timerDisplay);
        timer.start();
    }
}); 