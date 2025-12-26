// MyZenBrain - Pomodoro Timer

class PomodoroTimer {
    constructor() {
        this.settings = {
            focus_duration: 25,
            short_break_duration: 5,
            long_break_duration: 15,
            sessions_until_long_break: 4
        };

        this.sessionType = 'focus';
        this.timeRemaining = this.settings.focus_duration * 60;
        this.isRunning = false;
        this.interval = null;
        this.sessionsCompleted = 0;

        this.loadSettings();
        this.setupEventListeners();
        this.updateDisplay();
    }

    async loadSettings() {
        try {
            const res = await fetch('/pomodoro/api/settings');
            this.settings = await res.json();
            this.timeRemaining = this.settings.focus_duration * 60;
            this.updateDisplay();
            this.updateSettingsForm();
        } catch (e) {
            console.error('Failed to load settings:', e);
        }
    }

    updateSettingsForm() {
        document.getElementById('focus-duration').value = this.settings.focus_duration;
        document.getElementById('short-break-duration').value = this.settings.short_break_duration;
        document.getElementById('long-break-duration').value = this.settings.long_break_duration;
        document.getElementById('sessions-until-long').value = this.settings.sessions_until_long_break;
    }

    setupEventListeners() {
        // Start/Pause button
        document.getElementById('start-btn').addEventListener('click', () => {
            if (this.isRunning) {
                this.pause();
            } else {
                this.start();
            }
        });

        // Reset button
        document.getElementById('reset-btn').addEventListener('click', () => this.reset());

        // Skip button
        document.getElementById('skip-btn').addEventListener('click', () => this.skip());

        // Session type buttons
        document.querySelectorAll('.session-type-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                if (!this.isRunning) {
                    this.setSessionType(btn.dataset.type);
                }
            });
        });

        // Settings toggle
        document.getElementById('settings-toggle').addEventListener('click', () => {
            const panel = document.getElementById('settings-panel');
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        });

        // Save settings
        document.getElementById('save-settings').addEventListener('click', () => this.saveSettings());

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && e.target.tagName !== 'INPUT') {
                e.preventDefault();
                if (this.isRunning) {
                    this.pause();
                } else {
                    this.start();
                }
            }
        });
    }

    start() {
        this.isRunning = true;
        document.getElementById('start-btn').innerHTML = '<i class="fas fa-pause"></i>';

        this.interval = setInterval(() => this.tick(), 1000);
    }

    pause() {
        this.isRunning = false;
        document.getElementById('start-btn').innerHTML = '<i class="fas fa-play"></i>';

        clearInterval(this.interval);
    }

    reset() {
        this.pause();
        this.timeRemaining = this.getDuration() * 60;
        this.updateDisplay();
    }

    skip() {
        this.pause();
        this.completeSession();
    }

    tick() {
        if (this.timeRemaining > 0) {
            this.timeRemaining--;
            this.updateDisplay();
        } else {
            this.completeSession();
        }
    }

    async completeSession() {
        this.pause();

        // Play notification sound
        this.playSound();

        // Show browser notification
        this.showNotification();

        // Log session if it was a focus session
        if (this.sessionType === 'focus') {
            await this.logSession();
            this.sessionsCompleted++;
            document.getElementById('session-count').textContent = this.sessionsCompleted;
        }

        // Switch to next session type
        this.switchSessionType();
    }

    switchSessionType() {
        if (this.sessionType === 'focus') {
            // Check if it's time for a long break
            if (this.sessionsCompleted % this.settings.sessions_until_long_break === 0) {
                this.setSessionType('long_break');
            } else {
                this.setSessionType('short_break');
            }
        } else {
            this.setSessionType('focus');
        }
    }

    setSessionType(type) {
        this.sessionType = type;
        this.timeRemaining = this.getDuration() * 60;

        // Update UI
        document.querySelectorAll('.session-type-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.type === type);
        });

        const labels = {
            focus: 'Focus Time',
            short_break: 'Short Break',
            long_break: 'Long Break'
        };
        document.getElementById('timer-label').textContent = labels[type];

        this.updateDisplay();
    }

    getDuration() {
        switch (this.sessionType) {
            case 'focus': return this.settings.focus_duration;
            case 'short_break': return this.settings.short_break_duration;
            case 'long_break': return this.settings.long_break_duration;
            default: return 25;
        }
    }

    updateDisplay() {
        const minutes = Math.floor(this.timeRemaining / 60);
        const seconds = this.timeRemaining % 60;
        document.getElementById('timer-display').textContent =
            `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }

    async logSession() {
        try {
            await fetch('/pomodoro/api/session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_type: this.sessionType,
                    duration_minutes: this.getDuration()
                })
            });
        } catch (e) {
            console.error('Failed to log session:', e);
        }
    }

    async saveSettings() {
        this.settings.focus_duration = parseInt(document.getElementById('focus-duration').value);
        this.settings.short_break_duration = parseInt(document.getElementById('short-break-duration').value);
        this.settings.long_break_duration = parseInt(document.getElementById('long-break-duration').value);
        this.settings.sessions_until_long_break = parseInt(document.getElementById('sessions-until-long').value);

        try {
            await fetch('/pomodoro/api/settings', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.settings)
            });

            // Reset timer with new duration
            this.reset();
            document.getElementById('settings-panel').style.display = 'none';
            alert('Settings saved!');
        } catch (e) {
            console.error('Failed to save settings:', e);
        }
    }

    playSound() {
        // Create a simple beep sound
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            oscillator.frequency.value = 800;
            oscillator.type = 'sine';

            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
        } catch (e) {
            console.log('Audio not supported');
        }
    }

    showNotification() {
        if ('Notification' in window && Notification.permission === 'granted') {
            const messages = {
                focus: 'Focus session complete! Time for a break.',
                short_break: 'Break is over! Ready to focus?',
                long_break: 'Long break is over! Ready to focus?'
            };
            new Notification('MyZenBrain', {
                body: messages[this.sessionType],
                icon: '/static/images/logo.png'
            });
        }
    }
}

// Request notification permission
if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
}

// Initialize timer
const timer = new PomodoroTimer();
