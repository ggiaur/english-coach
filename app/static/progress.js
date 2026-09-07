document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const summaryBtn = document.getElementById('summary-btn');
    if (!sidebar) return;

    const sessionId = localStorage.getItem('english_coach_session_id');
    const panel = document.createElement('div');
    panel.className = 'sidebar-section learner-progress-section';
    panel.innerHTML = `
        <h3 class="section-title">Your Progress</h3>
        <div class="insights-card" id="learner-progress-card" aria-live="polite">
            <div class="stat-row">
                <span class="stat-label">Completed sessions:</span>
                <span class="stat-value highlight" id="progress-session-count">—</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Current focus:</span>
                <span class="stat-value" id="progress-focus">—</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Practice pace:</span>
                <span class="stat-value" id="progress-pace">—</span>
            </div>
            <div id="progress-review-wrap" style="display:none; margin-top:12px; padding-top:12px; border-top:1px solid rgba(255,255,255,.1);">
                <div class="stat-label" style="margin-bottom:6px;">Practice again</div>
                <div id="progress-review-items"></div>
                <div style="font-size:.74rem; opacity:.68; margin-top:6px; line-height:1.35;">Your coach will reuse these in the next session until they become natural.</div>
            </div>
            <div id="progress-latest-wrap" style="display:none; margin-top:12px; padding-top:12px; border-top:1px solid rgba(255,255,255,.1);">
                <div class="stat-label" style="margin-bottom:6px;">Latest coach note</div>
                <div id="progress-latest-summary" style="font-size:.82rem; line-height:1.45; opacity:.92; max-height:8.6em; overflow:hidden;"></div>
            </div>
            <div id="progress-empty" style="font-size:.82rem; line-height:1.45; opacity:.72; margin-top:10px;">
                Finish a session with “Összegzés Kérése” and your next practice will build on it.
            </div>
        </div>
    `;

    const overviewSection = Array.from(sidebar.querySelectorAll('.sidebar-section'))
        .find(section => section.textContent.includes('Munkamenet Áttekintés'));
    if (overviewSection && overviewSection.nextSibling) {
        sidebar.insertBefore(panel, overviewSection.nextSibling);
    } else {
        sidebar.appendChild(panel);
    }

    function compactSummary(text) {
        if (!text) return '';
        return text
            .replace(/```[\s\S]*?```/g, ' ')
            .replace(/[#*_>`~-]/g, '')
            .replace(/\s+/g, ' ')
            .trim()
            .slice(0, 360);
    }

    function renderReviewItems(items) {
        const wrap = document.getElementById('progress-review-wrap');
        const container = document.getElementById('progress-review-items');
        container.replaceChildren();
        if (!Array.isArray(items) || items.length === 0) {
            wrap.style.display = 'none';
            return;
        }
        items.slice(-3).reverse().forEach(item => {
            const row = document.createElement('div');
            row.style.cssText = 'font-size:.8rem; line-height:1.4; margin-bottom:7px;';
            const oldForm = document.createElement('div');
            oldForm.style.cssText = 'opacity:.65; text-decoration:line-through;';
            oldForm.textContent = item.phrase || '';
            const betterForm = document.createElement('div');
            betterForm.style.cssText = 'font-weight:600;';
            betterForm.textContent = `→ ${item.correction || ''}`;
            row.append(oldForm, betterForm);
            if (item.note) {
                const note = document.createElement('div');
                note.style.cssText = 'font-size:.72rem; opacity:.68; margin-top:1px;';
                note.textContent = item.note;
                row.appendChild(note);
            }
            container.appendChild(row);
        });
        wrap.style.display = 'block';
    }

    async function loadProgress() {
        const headers = sessionId ? { 'X-Session-ID': sessionId } : {};
        try {
            const response = await fetch('/progress', { headers });
            if (!response.ok) return;
            const data = await response.json();
            const preferences = data.preferences || {};
            const summaries = data.recent_session_summaries || [];

            document.getElementById('progress-session-count').textContent = data.practice_count || 0;
            document.getElementById('progress-focus').textContent = (preferences.focus || 'it-support').replaceAll('-', ' ');
            document.getElementById('progress-pace').textContent = (preferences.pace || 'four-pass').replaceAll('-', ' ');
            renderReviewItems(data.review_items || []);

            const latest = compactSummary(summaries[summaries.length - 1]);
            const latestWrap = document.getElementById('progress-latest-wrap');
            const latestSummary = document.getElementById('progress-latest-summary');
            const empty = document.getElementById('progress-empty');
            if (latest) {
                latestSummary.textContent = latest;
                latestWrap.style.display = 'block';
                empty.style.display = 'none';
            } else {
                latestWrap.style.display = 'none';
                empty.style.display = 'block';
            }
        } catch (error) {
            console.debug('Progress panel unavailable:', error);
        }
    }

    loadProgress();

    if (summaryBtn) {
        summaryBtn.addEventListener('click', () => {
            window.setTimeout(loadProgress, 1500);
            window.setTimeout(loadProgress, 4500);
        });
    }

    window.addEventListener('focus', loadProgress);
});
