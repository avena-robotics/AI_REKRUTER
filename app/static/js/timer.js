class TestTimer {
    constructor(timerToken, onTimeExpired) {
        this.timerToken = timerToken;
        this.onTimeExpired = onTimeExpired;
        this.timerInterval = null;
        this.remainingSeconds = 0;
        this.timeoutModalShown = false;
    }

    async start() {
        if (!this.timerToken) {
            console.warn('No timer token provided');
            return;
        }

        try {
            const response = await this.validateTimer();
            
            if (response.valid) {
                this.remainingSeconds = response.remaining_seconds;
                this.updateTimerDisplay();
                this.startCountdown();
            } else if (response.expired) {
                this.handleExpiredTimer();
            }
        } catch (error) {
            console.error('Error starting timer:', error);
        }
    }

    async validateTimer() {
        try {
            const response = await fetch('/api/timer/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ timer_token: this.timerToken })
            });

            if (!response.ok) {
                throw new Error('Timer validation failed');
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Timer validation error:', error);
            throw error;
        }
    }

    startCountdown() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }

        this.timerInterval = setInterval(async () => {
            try {
                const validation = await this.validateTimer();
                
                if (!validation.valid || validation.expired) {
                    this.handleExpiredTimer();
                    return;
                }
                
                this.remainingSeconds = validation.remaining_seconds;
                this.updateTimerDisplay();
                
                if (this.remainingSeconds <= 0) {
                    this.handleExpiredTimer();
                }
            } catch (error) {
                console.error('Error in countdown:', error);
            }
        }, 1000);
    }

    updateTimerDisplay() {
        const minutes = Math.floor(this.remainingSeconds / 60);
        const seconds = this.remainingSeconds % 60;
        const timerElement = document.getElementById('timer');
        if (timerElement) {
            timerElement.textContent = 
                `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        }
    }

    handleExpiredTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
        
        if (!this.timeoutModalShown) {
            this.timeoutModalShown = true;
            this.onTimeExpired();
        }
    }

    stop() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }
} 