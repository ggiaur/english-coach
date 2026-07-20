document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const messagesFeed = document.getElementById('messages-feed');
    const resetBtn = document.getElementById('reset-btn');
    const topicChips = document.querySelectorAll('.topic-chip');
    const activeTopicTitle = document.getElementById('active-topic-title');
    const msgCountElem = document.getElementById('msg-count');
    const ttsToggleBtn = document.getElementById('tts-toggle');
    const voiceBtn = document.getElementById('voice-btn');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');

    // App State
    let sessionId = localStorage.getItem('english_coach_session_id') || generateUUID();
    localStorage.setItem('english_coach_session_id', sessionId);

    let messageCount = parseInt(localStorage.getItem('english_coach_msg_count') || '0', 10);
    msgCountElem.textContent = messageCount;

    let isTTSEnabled = localStorage.getItem('english_coach_tts') === 'true';
    if (isTTSEnabled) ttsToggleBtn.classList.add('active');

    let recognition = null;
    initSpeechRecognition();

    // Auto-resize textarea
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
    });

    // Enter key submit (Shift+Enter for newline)
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    // Handle Form Submit
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = userInput.value.trim();
        if (!text) return;

        // Reset input height
        userInput.value = '';
        userInput.style.height = 'auto';

        // Add user message to UI
        appendMessage('user', text);
        messageCount++;
        msgCountElem.textContent = messageCount;
        localStorage.setItem('english_coach_msg_count', messageCount.toString());

        // Add loading indicator
        const loadingCard = createLoadingCard();
        messagesFeed.appendChild(loadingCard);
        scrollToBottom();

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Session-ID': sessionId
                },
                body: JSON.stringify({
                    message: text,
                    session_id: sessionId
                })
            });

            loadingCard.remove();

            if (!response.ok) {
                const errData = await response.json();
                appendMessage('coach', `⚠️ *Error:* ${errData.details || errData.error || 'Failed to connect to English Coach service.'}`);
                return;
            }

            const data = await response.json();
            if (data.session_id) {
                sessionId = data.session_id;
                localStorage.setItem('english_coach_session_id', sessionId);
            }

            appendMessage('coach', data.reply);

            // Speak response if TTS enabled
            if (isTTSEnabled) {
                speakText(data.reply);
            }
        } catch (err) {
            loadingCard.remove();
            appendMessage('coach', `⚠️ *Connection Error:* Could not communicate with server (${err.message}).`);
        }
    });

    // Handle Reset Button
    resetBtn.addEventListener('click', async () => {
        if (!confirm('Biztosan új beszélgetést szeretnél indítani?')) return;

        try {
            await fetch('/reset', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            });

            // Generate new session ID
            sessionId = generateUUID();
            localStorage.setItem('english_coach_session_id', sessionId);
            messageCount = 0;
            msgCountElem.textContent = '0';
            localStorage.setItem('english_coach_msg_count', '0');

            // Clear feed except welcome card
            messagesFeed.innerHTML = `
                <div class="message-card coach-message welcome-card">
                    <div class="message-header">
                        <span class="sender-name">English Coach</span>
                        <span class="time-stamp">Új munkamenet</span>
                    </div>
                    <div class="message-content">
                        <p>Hi! 👋 I've reset our conversation history.</p>
                        <p>Which topic would you like to practice today?</p>
                    </div>
                </div>
            `;
        } catch (err) {
            alert('A munkamenet törlése nem sikerült: ' + err.message);
        }
    });

    // Topic Selection
    topicChips.forEach(chip => {
        chip.addEventListener('click', () => {
            topicChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');

            const topicText = chip.getAttribute('data-topic');
            const chipLabel = chip.innerText.trim();
            activeTopicTitle.textContent = chipLabel + ' Practice';

            // Send initial prompt for selected topic
            userInput.value = `Hi! I would like to practice: ${topicText}.`;
            userInput.style.height = 'auto';
            userInput.focus();
        });
    });

    // Quick Prompts Event Delegation
    messagesFeed.addEventListener('click', (e) => {
        const promptBtn = e.target.closest('.prompt-btn');
        if (promptBtn) {
            const promptText = promptBtn.getAttribute('data-text');
            if (promptText) {
                userInput.value = promptText;
                chatForm.dispatchEvent(new Event('submit'));
            }
        }
    });

    // TTS Toggle Button
    ttsToggleBtn.addEventListener('click', () => {
        isTTSEnabled = !isTTSEnabled;
        localStorage.setItem('english_coach_tts', isTTSEnabled.toString());
        ttsToggleBtn.classList.toggle('active', isTTSEnabled);

        if (!isTTSEnabled && window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
    });

    // Sidebar Toggle for Mobile
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    // Helper Functions
    function appendMessage(sender, rawText) {
        const card = document.createElement('div');
        card.className = `message-card ${sender === 'user' ? 'user-message' : 'coach-message'}`;

        const formattedHtml = typeof marked !== 'undefined' ? marked.parse(rawText) : escapeHtml(rawText);
        const timeNow = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        card.innerHTML = `
            <div class="message-header">
                <span class="sender-name">${sender === 'user' ? 'Te' : 'English Coach'}</span>
                <span class="time-stamp">${timeNow}</span>
            </div>
            <div class="message-content">${formattedHtml}</div>
        `;

        messagesFeed.appendChild(card);
        scrollToBottom();
    }

    function createLoadingCard() {
        const card = document.createElement('div');
        card.className = 'message-card coach-message loading-card';
        card.innerHTML = `
            <div class="message-header">
                <span class="sender-name">English Coach</span>
                <span class="time-stamp">Gondolkodik...</span>
            </div>
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        return card;
    }

    function scrollToBottom() {
        messagesFeed.scrollTop = messagesFeed.scrollHeight;
    }

    function generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.innerText = text;
        return div.innerHTML;
    }

    function speakText(text) {
        if (!('speechSynthesis' in window)) return;
        window.speechSynthesis.cancel();

        // Strip markdown code blocks & HTML before speaking
        const cleanText = text.replace(/```[\s\S]*?```/g, '').replace(/<[^>]*>?/gm, '');
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = 'en-US';
        utterance.rate = 0.95; // slightly deliberate pace for language practice
        window.speechSynthesis.speak(utterance);
    }

    function initSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            voiceBtn.style.display = 'none';
            return;
        }

        recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = () => {
            voiceBtn.classList.add('listening');
        };

        recognition.onend = () => {
            voiceBtn.classList.remove('listening');
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            userInput.value = (userInput.value ? userInput.value + ' ' : '') + transcript;
            userInput.style.height = 'auto';
            userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
        };

        voiceBtn.addEventListener('click', () => {
            if (voiceBtn.classList.contains('listening')) {
                recognition.stop();
            } else {
                recognition.start();
            }
        });
    }
});
