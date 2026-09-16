document.addEventListener('DOMContentLoaded', () => {
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

    let sessionId = localStorage.getItem('english_coach_session_id') || generateUUID();
    localStorage.setItem('english_coach_session_id', sessionId);

    let messageCount = parseInt(localStorage.getItem('english_coach_msg_count') || '0', 10);
    msgCountElem.textContent = messageCount;

    let isTTSEnabled = localStorage.getItem('english_coach_tts') === 'true';
    if (isTTSEnabled) ttsToggleBtn.classList.add('active');

    let recognition = null;
    initSpeechRecognition();

    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
    });

    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = userInput.value.trim();
        if (!text) return;

        userInput.value = '';
        userInput.style.height = 'auto';
        appendMessage('user', text);
        messageCount++;
        msgCountElem.textContent = messageCount;
        localStorage.setItem('english_coach_msg_count', messageCount.toString());

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
                body: JSON.stringify({ message: text, session_id: sessionId })
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

            if (isTTSEnabled) {
                speakText(data.reply, data.lesson_state?.phase);
            }
        } catch (err) {
            loadingCard.remove();
            appendMessage('coach', `⚠️ *Connection Error:* Could not communicate with server (${err.message}).`);
        }
    });

    const summaryBtn = document.getElementById('summary-btn');
    if (summaryBtn) {
        summaryBtn.addEventListener('click', async () => {
            if (messageCount === 0) {
                alert('Még nem küldtél üzenetet a mai munkamenetben.');
                return;
            }

            const loadingCard = createLoadingCard();
            messagesFeed.appendChild(loadingCard);
            scrollToBottom();

            try {
                const response = await fetch('/summary', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Session-ID': sessionId
                    },
                    body: JSON.stringify({ session_id: sessionId })
                });

                loadingCard.remove();

                if (!response.ok) {
                    const errData = await response.json();
                    appendMessage('coach', `⚠️ *Hiba:* ${errData.details || errData.error || 'Nem sikerült legenerálni az összefoglalót.'}`);
                    return;
                }

                const data = await response.json();
                appendMessage('coach', data.summary, true);

                if (isTTSEnabled) {
                    speakText(data.summary, data.lesson_state?.phase);
                }
            } catch (err) {
                loadingCard.remove();
                appendMessage('coach', `⚠️ *Kapcsolódási Hiba:* ${err.message}`);
            }
        });
    }

    topicChips.forEach(chip => {
        chip.addEventListener('click', () => {
            topicChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');

            const topicText = chip.getAttribute('data-topic');
            const chipLabel = chip.innerText.trim();
            activeTopicTitle.textContent = chipLabel + ' Practice';
            userInput.value = `Hi! I would like to practice: ${topicText}.`;
            userInput.style.height = 'auto';
            userInput.focus();
        });
    });

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

    ttsToggleBtn.addEventListener('click', () => {
        isTTSEnabled = !isTTSEnabled;
        localStorage.setItem('english_coach_tts', isTTSEnabled.toString());
        ttsToggleBtn.classList.toggle('active', isTTSEnabled);

        if (!isTTSEnabled && window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
    });

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    function appendMessage(sender, rawText, isSummary = false) {
        const card = document.createElement('div');
        const cardClass = sender === 'user' ? 'user-message' : (isSummary ? 'coach-message summary-card' : 'coach-message');
        card.className = `message-card ${cardClass}`;

        const formattedHtml = typeof marked !== 'undefined' ? marked.parse(rawText) : escapeHtml(rawText);
        const timeNow = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const senderTitle = sender === 'user' ? 'Te' : (isSummary ? 'English Coach — Munkamenet Összegzés 📊' : 'English Coach');

        card.innerHTML = `
            <div class="message-header">
                <span class="sender-name">${senderTitle}</span>
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

    function ttsProfileForPhase(phase) {
        if (['vocab_pass_1', 'vocab_pass_2', 'story_round_1', 'story_round_2'].includes(phase)) {
            return { rate: 0.68, pauseMs: 650 };
        }
        if (['vocab_pass_3', 'story_round_3'].includes(phase)) {
            return { rate: 0.82, pauseMs: 250 };
        }
        if (['vocab_pass_4', 'story_round_4'].includes(phase)) {
            return { rate: 0.95, pauseMs: 100 };
        }
        if (phase && phase.startsWith('story_expansion_')) {
            return { rate: 0.82, pauseMs: 250 };
        }
        return { rate: 0.9, pauseMs: 120 };
    }

    function splitForSpeech(text) {
        const cleanText = text
            .replace(/```[\s\S]*?```/g, '')
            .replace(/<[^>]*>?/gm, '')
            .replace(/\s+/g, ' ')
            .trim();
        return cleanText.match(/[^.!?]+[.!?]?/g)?.map(s => s.trim()).filter(Boolean) || [];
    }

    function speakText(text, phase = null) {
        if (!('speechSynthesis' in window)) return;
        window.speechSynthesis.cancel();

        const profile = ttsProfileForPhase(phase);
        const sentences = splitForSpeech(text);
        if (!sentences.length) return;

        let index = 0;
        const speakNext = () => {
            if (!isTTSEnabled || index >= sentences.length) return;
            const utterance = new SpeechSynthesisUtterance(sentences[index]);
            utterance.lang = 'en-US';
            utterance.rate = profile.rate;
            utterance.onend = () => {
                index++;
                if (index < sentences.length && isTTSEnabled) {
                    window.setTimeout(speakNext, profile.pauseMs);
                }
            };
            window.speechSynthesis.speak(utterance);
        };
        speakNext();
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

    if (resetBtn) {
        resetBtn.addEventListener('click', async () => {
            if (window.speechSynthesis) window.speechSynthesis.cancel();
            await fetch('/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Session-ID': sessionId
                },
                body: JSON.stringify({ session_id: sessionId })
            });
            messageCount = 0;
            msgCountElem.textContent = '0';
            localStorage.setItem('english_coach_msg_count', '0');
            messagesFeed.querySelectorAll('.message-card').forEach(card => card.remove());
        });
    }
});
