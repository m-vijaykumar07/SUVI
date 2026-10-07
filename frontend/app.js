/**
 * SUVI ✦ ಸುವಿ — Smart Unified Voice Intelligence v3.0
 * Gemini AI Brain · Lady Voice (en-US-JennyNeural) · Wake Word: "Hey Suvi (ಸುವಿ)"
 * Integrates Web Speech Recognition, WebSockets, Web Audio API, and Gemini REST
 */

let reactorInstance = null;
let socket = null;
let recognition = null;
let isListening = false;
let audioContext = null;
let analyser = null;
let micStream = null;
let currentAudio = null;

let deferredInstallPrompt = null;

// User Config State
let masterPin = localStorage.getItem('suvi_pin') || '1234';

// Check if running inside native Android WebView container
const isNativeAndroid = typeof window.AndroidSuvi !== 'undefined';

document.addEventListener('DOMContentLoaded', () => {
    initClock();
    initReactor();
    initWebSocket();
    initSpeechRecognition();
    initEventListeners();
    initPwaSupport();
    fetchTelemetry();
    fetchGeminiStatus();
    setInterval(fetchTelemetry, 3000);
    setInterval(fetchGeminiStatus, 15000);  // Poll Gemini status every 15s
});

/** Poll Gemini AI Brain status and update HUD badge */
async function fetchGeminiStatus() {
    try {
        const res = await fetch('/api/ai/status');
        const data = await res.json();
        const badge = document.getElementById('geminiStatusBadge');
        const indicator = document.getElementById('geminiIndicator');
        const text = document.getElementById('geminiStatusText');
        if (!badge) return;
        if (data.ready) {
            indicator.style.background = '#00f3ff';
            indicator.style.boxShadow = '0 0 8px #00f3ff';
            text.textContent = `🧠 GEMINI ${(data.model || 'AI').toUpperCase()}`;
            badge.title = `Gemini AI Brain ONLINE — ${data.model}`;
        } else {
            indicator.style.background = '#ff4444';
            indicator.style.boxShadow = '0 0 8px #ff4444';
            text.textContent = '🧠 GEMINI OFFLINE';
            badge.title = 'Gemini offline — set GEMINI_API_KEY in .env';
        }
    } catch (e) {
        // Server not yet ready — ignore
    }
}

function initPwaSupport() {
    // Register Service Worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/frontend/service-worker.js')
            .then(reg => console.log('SUVI ServiceWorker active:', reg.scope))
            .catch(err => console.log('ServiceWorker registration error:', err));
    }

    // Capture install prompt
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredInstallPrompt = e;
        const btn = document.getElementById('pwaInstallBtn');
        if (btn) btn.style.display = 'flex';
    });
}

function triggerPwaInstall() {
    if (deferredInstallPrompt) {
        deferredInstallPrompt.prompt();
        deferredInstallPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                const btn = document.getElementById('pwaInstallBtn');
                if (btn) btn.style.display = 'none';
            }
            deferredInstallPrompt = null;
        });
    } else {
        alert("To install SUVI on your phone: Tap your browser's menu (three dots) -> 'Install App' or 'Add to Home Screen'.");
    }
}

// 1. Clock Display
function initClock() {
    const clockEl = document.getElementById('hudClock');
    const update = () => {
        const now = new Date();
        clockEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
    };
    update();
    setInterval(update, 1000);
}

// 2. Arc Reactor Canvas
function initReactor() {
    reactorInstance = new ArcReactor('reactorCanvas');
    initLiveWaveBars();
}

function initLiveWaveBars() {
    const container = document.getElementById('liveAudioWaves');
    if (!container) return;
    container.innerHTML = '';
    for (let i = 0; i < 24; i++) {
        const bar = document.createElement('div');
        bar.className = 'wave-bar';
        container.appendChild(bar);
    }
}

function updateWaveBars(level) {
    const bars = document.querySelectorAll('.wave-bar');
    bars.forEach((bar, idx) => {
        const dist = Math.abs(idx - bars.length / 2) / (bars.length / 2);
        const factor = Math.max(0.1, 1 - dist * 0.7);
        const h = Math.min(36, Math.max(4, level * 36 * factor + Math.random() * 4));
        bar.style.height = `${h}px`;
    });
}

// 3. WebSocket Connection
function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/voice`;
    
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        setReactorState('STANDBY', 'Core Connected');
        updateIndicator(true);
    };

    socket.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        handleSocketMessage(msg);
    };

    socket.onclose = () => {
        setReactorState('STANDBY', 'Reconnecting...');
        updateIndicator(false);
        setTimeout(initWebSocket, 3000);
    };

    socket.onerror = (err) => {
        console.error('WebSocket Error:', err);
    };
}

function handleSocketMessage(msg) {
    if (msg.type === 'state') {
        if (msg.status === 'processing') {
            setReactorState('PROCESSING', 'Analyzing Command...');
        }
    } else if (msg.type === 'response') {
        addMessageToFeed('suvi', msg.response_text, msg.intent);
        setReactorState('SPEAKING', 'Transmitting Voice');

        // Play neural speech response audio if available
        if (msg.audio && msg.audio.audio_url) {
            playResponseAudio(msg.audio.audio_url);
        } else {
            setTimeout(() => setReactorState('STANDBY', 'Online & Standby'), 2500);
        }

        // Handle specific intent outcomes
        handleIntentData(msg.intent, msg.data);
    }
}

function handleIntentData(intent, data) {
    if (!data) return;

    // Native Android hardware hooks
    if (isNativeAndroid && window.AndroidSuvi) {
        window.AndroidSuvi.vibrate(40);
        if (intent === 'PHONE_CALL' && data.number) {
            window.AndroidSuvi.makeCall(data.number);
        } else if (intent === 'WHATSAPP_SEND' && data.recipient) {
            window.AndroidSuvi.sendWhatsApp(data.recipient, data.message || '');
        } else if (intent === 'APP_OPEN' && data.app) {
            window.AndroidSuvi.openApp(data.app);
        }
    }

    if (intent === 'CAMERA_VIEW') {
        openModal('cameraModal');
        document.getElementById('cameraVideoFeed').src = '/api/camera/stream';
    } else if (intent === 'CAMERA_SNAP' && data.base64) {
        openModal('cameraModal');
        const img = document.getElementById('cameraSnapshotPreview');
        img.src = data.base64;
        img.style.display = 'block';
    } else if (intent === 'NOTE_CREATE' || intent === 'NOTE_LIST') {
        loadNotesList();
    }
}

// 4. Speech Recognition (Web Speech API)
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        console.warn('Web Speech API not supported on this browser. Voice input via text fallback.');
        return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
        isListening = true;
        document.getElementById('micToggleBtn').classList.add('active');
        setReactorState('LISTENING', 'Listening to Voice Input...');
        startMicAudioAnalysis();
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        addMessageToFeed('user', transcript);
        sendVoiceCommand(transcript);
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        stopListening();
    };

    recognition.onend = () => {
        stopListening();
    };
}

function toggleListening() {
    if (!recognition) {
        alert('Microphone speech recognition is not supported in this browser. Please use Chrome/Edge or type your command.');
        return;
    }
    if (isListening) {
        recognition.stop();
        stopListening();
    } else {
        try {
            recognition.start();
        } catch (e) {
            console.error('Error starting recognition:', e);
        }
    }
}

function stopListening() {
    isListening = false;
    document.getElementById('micToggleBtn').classList.remove('active');
    stopMicAudioAnalysis();
    if (reactorInstance && reactorInstance.state !== 'PROCESSING' && reactorInstance.state !== 'SPEAKING') {
        setReactorState('STANDBY', 'Online & Standby');
    }
}

// 5. Web Audio API for Live Microphone Frequency Analysis
async function startMicAudioAnalysis() {
    try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return;
        micStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 64;
        const source = audioContext.createMediaStreamSource(micStream);
        source.connect(analyser);

        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        const pollAudio = () => {
            if (!isListening) return;
            analyser.getByteFrequencyData(dataArray);
            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
            const avg = sum / dataArray.length / 255;
            
            if (reactorInstance) reactorInstance.setAudioLevel(avg);
            updateWaveBars(avg);

            requestAnimationFrame(pollAudio);
        };
        pollAudio();
    } catch (err) {
        console.log('Mic analyser access ignored or not granted:', err);
    }
}

function stopMicAudioAnalysis() {
    if (micStream) {
        micStream.getTracks().forEach(track => track.stop());
        micStream = null;
    }
    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }
    if (reactorInstance) reactorInstance.setAudioLevel(0);
    updateWaveBars(0);
}

// 6. Neural Voice Audio Playback
function playResponseAudio(url) {
    if (currentAudio) {
        currentAudio.pause();
    }
    currentAudio = new Audio(url);
    currentAudio.play().then(() => {
        // Start synthetic reactor frequency while speaking
        const interval = setInterval(() => {
            if (currentAudio.paused || currentAudio.ended) {
                clearInterval(interval);
                setReactorState('STANDBY', 'Online & Standby');
                if (reactorInstance) reactorInstance.setAudioLevel(0);
                updateWaveBars(0);
            } else {
                const simulatedLevel = 0.3 + Math.random() * 0.5;
                if (reactorInstance) reactorInstance.setAudioLevel(simulatedLevel);
                updateWaveBars(simulatedLevel);
            }
        }, 100);
    }).catch(err => {
        console.error('Audio playback failed:', err);
        setReactorState('STANDBY', 'Online & Standby');
    });
}

// 7. Command Transmission
function sendVoiceCommand(text) {
    if (!text || !text.trim()) return;

    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: 'command',
            text: text,
            pin: masterPin
        }));
    } else {
        // Fallback to REST API
        setReactorState('PROCESSING', 'Analyzing Command...');
        fetch('/api/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: text, pin: masterPin })
        })
        .then(res => res.json())
        .then(data => {
            addMessageToFeed('suvi', data.response_text, data.intent);
            if (data.audio && data.audio.audio_url) {
                playResponseAudio(data.audio.audio_url);
            } else {
                setReactorState('STANDBY', 'Online & Standby');
            }
            handleIntentData(data.intent, data.data);
        })
        .catch(err => {
            addMessageToFeed('suvi', 'Error executing command.');
            setReactorState('STANDBY', 'System Error');
        });
    }
}

// 8. Feed and Transcript UI
function addMessageToFeed(sender, text, intent = null) {
    const feed = document.getElementById('transcriptFeed');
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender}`;

    const meta = document.createElement('div');
    meta.className = 'bubble-meta';
    meta.innerHTML = `<span>${sender === 'suvi' ? 'SUVI INTELLIGENCE' : 'USER'}</span>${intent ? `<span class="intent-badge">${intent}</span>` : ''}`;

    const content = document.createElement('div');
    content.textContent = text;

    bubble.appendChild(meta);
    bubble.appendChild(content);
    feed.appendChild(bubble);
    feed.scrollTop = feed.scrollHeight;
}

// 9. Hardware Telemetry Fetch
async function fetchTelemetry() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();
        
        // Update Windows telemetry
        if (data.windows) {
            const cpu = data.windows.cpu.percent;
            const ram = data.windows.ram.percent;
            const disk = data.windows.disk.percent;
            const batt = data.windows.battery.percent;

            document.getElementById('cpuPercentText').textContent = `${cpu}%`;
            document.getElementById('cpuBarFill').style.width = `${cpu}%`;

            document.getElementById('ramPercentText').textContent = `${ram}%`;
            document.getElementById('ramBarFill').style.width = `${ram}%`;

            document.getElementById('diskPercentText').textContent = `${disk}%`;
            document.getElementById('diskBarFill').style.width = `${disk}%`;

            document.getElementById('battPercentText').textContent = `${batt}%`;
            document.getElementById('battBarFill').style.width = `${batt}%`;
        }

        // Update Android status
        if (data.android) {
            const statusEl = document.getElementById('androidStatusText');
            if (data.android.devices && data.android.devices.length > 0) {
                const dev = data.android.devices[0];
                statusEl.textContent = `Online (${dev.id})`;
                statusEl.style.color = 'var(--accent-green)';
            } else {
                statusEl.textContent = 'Disconnected / Standby';
                statusEl.style.color = 'var(--text-muted)';
            }
        }
    } catch (e) {
        console.warn('Telemetry fetch error:', e);
    }
}

// 10. Reactor State Helpers
function setReactorState(state, label) {
    if (reactorInstance) reactorInstance.setState(state);
    const labelEl = document.getElementById('reactorStateLabel');
    const subEl = document.getElementById('reactorStateSub');
    if (labelEl) labelEl.textContent = state;
    if (subEl) subEl.textContent = label;
}

function updateIndicator(connected) {
    const ind = document.getElementById('systemIndicator');
    if (ind) {
        ind.className = connected ? 'indicator' : 'indicator amber';
    }
}

// 11. Modal Handlers
function openModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('open');
}

function closeModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('open');
    if (id === 'cameraModal') {
        // Stop stream
        const feed = document.getElementById('cameraVideoFeed');
        if (feed) feed.src = '';
    }
}

// 12. Notes Operations
async function loadNotesList() {
    try {
        const res = await fetch('/api/notes');
        const data = await res.json();
        const listEl = document.getElementById('notesListContainer');
        if (!listEl) return;
        listEl.innerHTML = '';

        if (!data.notes || data.notes.length === 0) {
            listEl.innerHTML = '<p style="color:var(--text-muted);font-size:0.9rem;">No recorded notes found.</p>';
            return;
        }

        data.notes.forEach(note => {
            const card = document.createElement('div');
            card.style.background = 'rgba(0, 243, 255, 0.05)';
            card.style.border = '1px solid rgba(0, 243, 255, 0.2)';
            card.style.borderRadius = '4px';
            card.style.padding = '8px 12px';
            card.style.marginBottom = '8px';

            card.innerHTML = `
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <strong style="color:var(--accent-cyan);">${note.title}</strong>
                    <button onclick="deleteNote(${note.id})" style="background:transparent;border:none;color:var(--accent-red);cursor:pointer;">&times;</button>
                </div>
                <p style="font-size:0.85rem;margin-top:4px;color:var(--text-primary);">${note.content}</p>
                <small style="color:var(--text-muted);font-size:0.75rem;">${note.created_at}</small>
            `;
            listEl.appendChild(card);
        });
    } catch (e) {
        console.error('Failed to load notes:', e);
    }
}

async function deleteNote(id) {
    await fetch(`/api/notes/${id}`, { method: 'DELETE' });
    loadNotesList();
}

async function createNoteFromForm() {
    const input = document.getElementById('newNoteContent');
    const content = input.value.trim();
    if (!content) return;
    await fetch('/api/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: content })
    });
    input.value = '';
    loadNotesList();
}

// 13. Event Listeners & Shortcuts
function initEventListeners() {
    // Mic Toggle
    document.getElementById('micToggleBtn').addEventListener('click', toggleListening);

    // Spacebar to trigger microphone
    window.addEventListener('keydown', (e) => {
        if (e.code === 'Space' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
            e.preventDefault();
            toggleListening();
        }
    });

    // Text Input Submit
    const cmdInput = document.getElementById('textCommandInput');
    cmdInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const text = cmdInput.value.trim();
            if (text) {
                addMessageToFeed('user', text);
                sendVoiceCommand(text);
                cmdInput.value = '';
            }
        }
    });

    // Quick Action Chips
    document.querySelectorAll('.chip-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const cmd = btn.getAttribute('data-cmd');
            addMessageToFeed('user', cmd);
            sendVoiceCommand(cmd);
        });
    });

    // Camera Snapshot button
    const snapBtn = document.getElementById('takeSnapBtn');
    if (snapBtn) {
        snapBtn.addEventListener('click', async () => {
            const res = await fetch('/api/camera/photo', { method: 'POST' });
            const data = await res.json();
            if (data.base64) {
                const img = document.getElementById('cameraSnapshotPreview');
                img.src = data.base64;
                img.style.display = 'block';
            }
        });
    }

    // Call Submit
    const callBtn = document.getElementById('callSubmitBtn');
    if (callBtn) {
        callBtn.addEventListener('click', async () => {
            const number = document.getElementById('callPhoneNumber').value;
            const res = await fetch('/api/phone/call', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone_number: number, pin: masterPin })
            });
            const data = await res.json();
            alert(data.message || data.detail);
            closeModal('callModal');
        });
    }

    // WhatsApp Submit
    const waBtn = document.getElementById('waSubmitBtn');
    if (waBtn) {
        waBtn.addEventListener('click', async () => {
            const recipient = document.getElementById('waRecipient').value;
            const message = document.getElementById('waMessage').value;
            const res = await fetch('/api/whatsapp/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ recipient, message, pin: masterPin })
            });
            const data = await res.json();
            alert(data.info || data.message || data.detail);
            closeModal('whatsappModal');
        });
    }
}
