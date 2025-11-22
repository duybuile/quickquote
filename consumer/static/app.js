// QuickQuote Frontend
// Handles voice/text/image communication with the backend API.

let sessionId = `session-${Math.random().toString(36).substring(7)}`; // Unique session ID

// DOM Elements
let voiceBtn, textInput, sendBtn, imageBtn, imageInput, conversation, status, loading, restartBtn;

document.addEventListener('DOMContentLoaded', () => {
    voiceBtn = document.getElementById('voice-btn');
    textInput = document.getElementById('text-input');
    sendBtn = document.getElementById('send-btn');
    imageBtn = document.getElementById('image-btn');
    imageInput = document.getElementById('image-input');
    conversation = document.getElementById('conversation');
    status = document.getElementById('status');
    loading = document.getElementById('loading');
    restartBtn = document.getElementById('restart-btn');

    // Add Event Listeners
    if (voiceBtn) voiceBtn.addEventListener('click', toggleMicrophone);
    if (sendBtn) sendBtn.addEventListener('click', sendTextMessage);
    if (textInput) {
        textInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendTextMessage();
        });
    }
    if (imageBtn && imageInput) imageBtn.addEventListener('click', () => imageInput.click());
    if (imageInput) imageInput.addEventListener('change', handleImageUpload);
    if (restartBtn) restartBtn.addEventListener('click', restartSession);

    console.log('QuickQuote loaded. Ready to connect!');
});

// Toggle Microphone (Web Speech API)
function toggleMicrophone() {
    console.log('Microphone clicked'); // DEBUG
    if (!('webkitSpeechRecognition' in window)) {
        console.error('Web Speech API not supported'); // DEBUG
        showError("Voice input not supported in this browser.");
        return;
    }

    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

let recognition = null;
let isRecording = false;

function startRecording() {
    recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
        isRecording = true;
        voiceBtn.classList.add('recording');
        updateStatus('Listening...', 'listening');
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        console.log('Voice input:', transcript);
        textInput.value = transcript;
        sendTextMessage(); // Send as text
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error', event.error);
        stopRecording();
    };

    recognition.onend = () => {
        stopRecording();
    };

    recognition.start();
}

function stopRecording() {
    if (recognition) {
        recognition.stop();
        recognition = null;
    }
    isRecording = false;
    voiceBtn.classList.remove('recording');
    updateStatus('Connected', 'idle');
}

// Send Text Message
async function sendTextMessage() {
    const text = textInput.value.trim();
    if (!text) return;

    try {
        // Show user message immediately
        addMessage(text, 'user');
        textInput.value = '';

        // Haptic feedback
        if (navigator.vibrate) navigator.vibrate(30);

        showLoading('Thinking...');

        // Call chat API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                message: text
            })
        });

        if (!response.ok) {
            throw new Error('Chat API failed');
        }

        const data = await response.json();

        hideLoading();

        // Show agent response
        addMessage(data.response, 'agent');

        // Show quotes if available
        if (data.quotes && data.quotes.length > 0) {
            displayQuoteResults(data.quotes);
        }

    } catch (error) {
        console.error('Send failed:', error);
        hideLoading();
        showError('Failed to send message.');
    }
}

// Image Upload
async function handleImageUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    // Auto-connect if needed
    if (!isConnected) {
        const success = await connectToRoom();
        if (!success) return;
    }

    try {
        showLoading('Uploading image...');
        const reader = new FileReader();
        reader.onload = async (event) => {
            const imageUrl = event.target.result;

            if (room && isConnected) {
                await room.localParticipant.publishData(
                    new TextEncoder().encode(JSON.stringify({
                        type: 'image',
                        url: imageUrl
                    })),
                    { reliable: true }
                );

                addMessage('📷 Photo uploaded', 'user');
            }
            hideLoading();
        };
        reader.readAsDataURL(file);

    } catch (error) {
        console.error('Upload failed:', error);
        showError('Failed to upload image');
        hideLoading();
    }
}

// Restart Session
async function restartSession() {
    if (confirm('Start a new conversation?')) {
        // In a real app, you might want to disconnect from LiveKit here
        // if (room && isConnected) {
        //     await room.disconnect();
        // }

        // Clear conversation
        conversation.innerHTML = `
            <div class="welcome-card">
                <h2>How can I help?</h2>
                <p>I can get you quotes for home services instantly. Just ask.</p>
            </div>
        `;

        // Reset ID
        // In a real app, you might want to generate a new session ID here

        addMessage('Session restarted.', 'agent');
    }
}

// Add Message to Conversation
function addMessage(text, role) {
    // Remove welcome card if it exists
    const welcomeCard = document.querySelector('.welcome-card');
    if (welcomeCard) {
        welcomeCard.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.textContent = text;
    conversation.appendChild(messageDiv);

    // Scroll to bottom
    conversation.parentElement.scrollTop = conversation.parentElement.scrollHeight;
}

// Display Quote Results
function displayQuoteResults(quotes) {
    const resultsDiv = document.createElement('div');
    resultsDiv.className = 'quote-results';

    resultsDiv.innerHTML = `
        <h3>📋 Quote Results</h3>
        <div class="quotes-list">
            ${quotes.map(quote => `
                <div class="quote-card">
                    <div class="quote-provider">${quote.provider}</div>
                    <div class="quote-price">$${quote.price}</div>
                    <div class="quote-details">${quote.details}</div>
                </div>
            `).join('')}
        </div>
    `;

    conversation.appendChild(resultsDiv);
    conversation.parentElement.scrollTop = conversation.parentElement.scrollHeight;
}

// Update Status
function updateStatus(text, state) {
    const statusText = status.querySelector('.status-text');
    const statusDot = status.querySelector('.status-dot');

    statusText.textContent = text;

    // Update dot color
    const colors = {
        idle: '#94a3b8',
        success: '#10b981',
        speaking: '#f59e0b',
        error: '#ef4444'
    };

    statusDot.style.background = colors[state] || colors.idle;
}

// Loading Overlay
function showLoading(text) {
    if (loading) {
        const p = loading.querySelector('p');
        if (p) p.textContent = text;
        loading.classList.add('active');
    }
}

function hideLoading() {
    if (loading) {
        loading.classList.remove('active');
    }
}

// Error Toast (simple alert for MVP)
function showError(message) {
    alert(message);
    // In production, use a proper toast notification
}

// Utilities
function generateSessionId() {
    return 'session-' + Math.random().toString(36).substr(2, 9);
}
