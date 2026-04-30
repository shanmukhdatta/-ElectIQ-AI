/* ══════════════════════════════════════════════════════
   INTRO / LANDING PAGE CONTROLLER
   ══════════════════════════════════════════════════════ */

(function initIntro() {
  // Mark body so sidebar/main are hidden until intro dismissed
  document.body.classList.add('intro-active');

  // ── Counter animation ────────────────────────────────
  function animateCounters() {
    document.querySelectorAll('.intro-stat-val[data-count]').forEach(el => {
      const target = parseInt(el.dataset.count, 10);
      const duration = 1800;
      const start = performance.now();

      function step(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(eased * target);
        if (progress < 1) requestAnimationFrame(step);
        else el.textContent = target;
      }

      requestAnimationFrame(step);
    });
  }

  // ── Scroll to feature cards ──────────────────────────
  window.scrollToFeatures = function () {
    const features = document.getElementById('intro-features');
    if (features) {
      features.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  // ── Enter app transition ─────────────────────────────
  window.enterApp = function () {
    const intro = document.getElementById('intro-screen');
    if (!intro || intro.classList.contains('leaving')) return;

    // Track with Google Analytics if available
    if (window.trackEvent) {
      window.trackEvent('Intro', 'enter_app', 'cta_click');
    }

    intro.classList.add('leaving');

    // After fade-out, remove intro and reveal app
    setTimeout(() => {
      intro.classList.add('gone');
      document.body.classList.remove('intro-active');

      // Focus the chat input so keyboard users land somewhere useful
      const chatInput = document.getElementById('chat-input');
      if (chatInput) chatInput.focus();

      // Remember: don't show intro again this session
      try { sessionStorage.setItem('electiq_intro_seen', '1'); } catch (e) {}
    }, 700);
  };

  // ── Keyboard: Escape or Enter to skip ───────────────
  document.addEventListener('keydown', function onIntroKey(e) {
    const intro = document.getElementById('intro-screen');
    if (!intro || intro.classList.contains('gone')) {
      document.removeEventListener('keydown', onIntroKey);
      return;
    }
    if (e.key === 'Escape' || e.key === 'Enter') {
      e.preventDefault();
      window.enterApp();
    }
  });

  // ── Auto-skip if already seen this session ────────────
  try {
    if (sessionStorage.getItem('electiq_intro_seen')) {
      // Already seen — skip intro immediately (no animation)
      const intro = document.getElementById('intro-screen');
      if (intro) {
        intro.classList.add('gone');
        document.body.classList.remove('intro-active');
      }
      return; // exit initIntro early
    }
  } catch (e) {}

  // ── Start counter animation after slight delay ────────
  setTimeout(animateCounters, 800);

  // ── Auto-enter after 12 seconds (safety fallback) ────
  const autoTimer = setTimeout(() => {
    const intro = document.getElementById('intro-screen');
    if (intro && !intro.classList.contains('gone')) {
      window.enterApp();
    }
  }, 12000);

  // Clear timer if user enters manually
  const enterBtn = document.getElementById('intro-enter-btn');
  if (enterBtn) {
    enterBtn.addEventListener('click', () => clearTimeout(autoTimer), { once: true });
  }
})();

/* ══════════════════════════════════════════════════════════
   ElectIQ — Frontend Application
   ══════════════════════════════════════════════════════════ */

const API = '';
let chatHistory = [];
let userProfile = { state: 'Maharashtra', constituency: 'Mumbai North', language: 'English', first_time: false };
let quizData = { questions: [], current: 0, score: 0, answered: false };

// ─────────────────────────────────────────────────────────────────────────────
// NAVIGATION
// ─────────────────────────────────────────────────────────────────────────────

document.querySelectorAll('.nav-link').forEach(link => {
  link.addEventListener('click', (e) => {
    e.preventDefault();
    const view = link.dataset.view;
    switchView(view);
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    link.classList.add('active');
    if (window.innerWidth <= 768) closeSidebar();
  });
});

function switchView(view) {
  if (window.trackView) window.trackView(view);
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  const el = document.getElementById('view-' + view);
  if (el) el.classList.add('active');
  
  document.querySelectorAll('.nav-link').forEach(l => l.removeAttribute('aria-current'));
  const activeLink = document.querySelector(`.nav-link[data-view="${view}"]`);
  if (activeLink) activeLink.setAttribute('aria-current', 'page');

  const loaders = {
    journey:    loadJourney,
    candidates: loadCandidates,
    compare:    loadCompare,
    booth:      loadBooths,
    warroom:    loadWarRoom,
    history:    loadHistory,
    quiz:       loadQuiz,
    impact:     loadImpact,
  };
  if (loaders[view]) loaders[view]();
}

// Mobile sidebar
document.getElementById('hamburger').addEventListener('click', () => {
  const sidebar = document.getElementById('sidebar');
  sidebar.classList.toggle('open');
  const hamburger = document.getElementById('hamburger');
  if (hamburger) {
    hamburger.setAttribute('aria-expanded', 
      sidebar.classList.contains('open') ? 'true' : 'false');
  }
});

function closeSidebar() {
  document.getElementById('sidebar').classList.remove('open');
}

// ─────────────────────────────────────────────────────────────────────────────
// CHAT
// ─────────────────────────────────────────────────────────────────────────────

async function sendMessage() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text) return;

  appendMessage('user', text);
  input.value = '';
  input.style.height = 'auto';
  chatHistory.push({ role: 'user', content: text });

  const lang = document.getElementById('lang-select').value;
  userProfile.language = lang;

  showTyping();
  
  const sendBtn = document.getElementById('send-btn');
  if (sendBtn) sendBtn.disabled = true;

  try {
    const res = await fetch(`${API}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: chatHistory, profile: userProfile })
    });
    const data = await res.json();
    removeTyping();
    appendMessage('assistant', data.reply);
    chatHistory.push({ role: 'assistant', content: data.reply });
  } catch (err) {
    removeTyping();
    appendMessage('assistant', '⚠️ Connection error. Please ensure the backend is running.');
  } finally {
    if (sendBtn) sendBtn.disabled = false;
  }
}

function sendChip(text) {
  document.getElementById('chat-input').value = text;
  sendMessage();
}

function appendMessage(role, text) {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `chat-message ${role}`;

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = role === 'assistant' ? '⚡' : '👤';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.innerHTML = markdownToHTML(text);

  div.appendChild(avatar);
  div.appendChild(bubble);
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function showTyping() {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'chat-message assistant';
  div.id = 'typing-indicator';
  div.innerHTML = `<div class="msg-avatar">⚡</div><div class="msg-bubble"><div class="typing-indicator"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div></div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function removeTyping() {
  const el = document.getElementById('typing-indicator');
  if (el) el.remove();
}

function markdownToHTML(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^### (.*$)/gm, '<h4 style="margin:12px 0 6px;color:var(--gold-light)">$1</h4>')
    .replace(/^## (.*$)/gm, '<h3 style="margin:12px 0 8px;font-family:Playfair Display,serif">$1</h3>')
    .replace(/^- (.*$)/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(?!<)/gm, '')
    .replace(/\n/g, '<br>');
}

// Auto-resize textarea
document.getElementById('chat-input').addEventListener('input', function () {
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

document.getElementById('chat-input').addEventListener('keydown', function (e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// JOURNEY
// ─────────────────────────────────────────────────────────────────────────────

function loadJourney() {
  const steps = [
    { icon: '✅', status: 'done', title: 'Check Eligibility', desc: 'You must be 18+ and an Indian citizen to vote. You need a valid EPIC (Voter ID) card.' },
    { icon: '📝', status: 'done', title: 'Register to Vote', desc: 'Register on voters.eci.gov.in. Provide proof of age, address, and identity. Deadline: April 20, 2026.', action: { label: 'Check Registration', fn: "switchView('voter')" } },
    { icon: '📍', status: 'active', title: 'Find Your Polling Booth', desc: 'Use your EPIC number to locate your designated polling booth. Check the ward, officer name, and queue status.', action: { label: 'Find My Booth ➤', fn: "switchView('booth')" } },
    { icon: '👥', status: 'pending', title: 'Know Your Candidates', desc: 'Review candidate backgrounds, manifestos, asset declarations, and ElectIQ Integrity Scores.', action: { label: 'View Candidates ➤', fn: "switchView('candidates')" } },
    { icon: '🗳️', status: 'pending', title: 'Cast Your Vote', desc: 'Polling Day: May 15, 2026. Bring your EPIC card. Polling hours: 7AM to 6PM. Press EVM button for your candidate.' },
    { icon: '📊', status: 'pending', title: 'Track Results', desc: 'Result Day: May 18, 2026. Use the War Room for live constituency-level updates.', action: { label: 'Open War Room ➤', fn: "switchView('warroom')" } },
  ];

  const container = document.getElementById('journey-steps');
  container.innerHTML = steps.map((s, i) => `
    <div class="journey-step">
      <div class="step-indicator">
        <div class="step-circle ${s.status === 'done' ? 'done' : s.status === 'active' ? 'active' : ''}">${s.icon}</div>
      </div>
      <div class="step-content">
        <div class="step-title">
          Step ${i + 1}: ${s.title}
          ${s.status === 'done' ? '<span class="step-done-badge">✓ DONE</span>' : ''}
          ${s.status === 'active' ? '<span class="step-active-badge">NOW</span>' : ''}
        </div>
        <div class="step-desc">${s.desc}</div>
        ${s.action ? `<div class="step-action"><button class="btn-primary" onclick="${s.action.fn}">${s.action.label}</button></div>` : ''}
      </div>
    </div>
  `).join('');
}

// ─────────────────────────────────────────────────────────────────────────────
// CANDIDATES
// ─────────────────────────────────────────────────────────────────────────────

async function loadCandidates() {
  const res = await fetch(`${API}/api/candidates`);
  const data = await res.json();
  const container = document.getElementById('candidates-grid');

  container.innerHTML = data.candidates.map(c => `
    <div class="candidate-card" onclick="openCandidateModal(${c.id})">
      <div class="cand-header">
        <div class="cand-avatar">${c.photo}</div>
        <div>
          <div class="cand-name">${c.name}</div>
          <div class="cand-party" style="color:${c.party_color}">${c.party}</div>
        </div>
      </div>
      <div class="cand-stats">
        <div class="stat-box">
          <div class="stat-value">${c.attendance}</div>
          <div class="stat-label">Attendance</div>
        </div>
        <div class="stat-box">
          <div class="stat-value">${c.criminal_cases === 0 ? '✓ 0' : '⚠ ' + c.criminal_cases}</div>
          <div class="stat-label">Cases</div>
        </div>
      </div>
      <div class="integrity-bar">
        <div class="integrity-label">
          <span>ElectIQ Integrity Score</span>
          <span class="text-gold mono">${c.integrity_score}/100</span>
        </div>
        <div class="bar-track">
          <div class="bar-fill" style="width:${c.integrity_score}%"></div>
        </div>
      </div>
      <button class="view-detail-btn">View Full Profile →</button>
    </div>
  `).join('');
}

let lastFocusedElement = null;

async function openCandidateModal(id) {
  lastFocusedElement = document.activeElement;
  const res = await fetch(`${API}/api/candidate/${id}`);
  const c = await res.json();

  document.getElementById('modal-content').innerHTML = `
    <div class="modal-candidate-header">
      <div class="modal-avatar">${c.photo}</div>
      <div>
        <div class="modal-candidate-name">${c.name}</div>
        <div class="modal-party" style="color:${c.party_color}">${c.party}</div>
        <div style="margin-top:8px">
          <span class="score-badge ${c.integrity_score >= 80 ? 'high' : c.integrity_score >= 60 ? 'mid' : 'low'}">
            ⚡ ${c.integrity_score}/100 Integrity Score
          </span>
        </div>
      </div>
    </div>

    <div class="modal-section">
      <div class="modal-section-title">📋 Profile</div>
      <div class="modal-fact-grid">
        <div class="modal-fact"><div class="modal-fact-label">Education</div><div class="modal-fact-value">${c.education}</div></div>
        <div class="modal-fact"><div class="modal-fact-label">Declared Assets</div><div class="modal-fact-value text-gold">${c.assets}</div></div>
        <div class="modal-fact"><div class="modal-fact-label">House Attendance</div><div class="modal-fact-value">${c.attendance}</div></div>
        <div class="modal-fact"><div class="modal-fact-label">Criminal Cases</div><div class="modal-fact-value ${c.criminal_cases === 0 ? 'text-green' : 'text-red'}">${c.criminal_cases === 0 ? '✓ None' : '⚠ ' + c.criminal_cases + ' filed'}</div></div>
      </div>
    </div>

    <div class="modal-section">
      <div class="modal-section-title">📜 Manifesto — Key Positions</div>
      ${Object.entries(c.manifesto).map(([k, v]) => `
        <div class="manifesto-item">
          <div class="manifesto-key">${k}</div>
          <div class="manifesto-val">${v}</div>
        </div>
      `).join('')}
    </div>
  `;

  document.getElementById('modal-overlay').classList.add('open');
  const closeBtn = document.querySelector('.modal-close');
  if (closeBtn) closeBtn.focus();
  document.addEventListener('keydown', handleModalKeydown);
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('open');
  document.removeEventListener('keydown', handleModalKeydown);
  if (lastFocusedElement) {
    lastFocusedElement.focus();
    lastFocusedElement = null;
  }
}

function handleModalKeydown(e) {
  if (e.key === 'Escape') {
    closeModal();
    return;
  }
  if (e.key === 'Tab') {
    const modal = document.getElementById('candidate-modal');
    if (!modal) return;
    const focusable = modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    if (focusable.length === 0) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    
    if (e.shiftKey) {
      if (document.activeElement === first) {
        last.focus();
        e.preventDefault();
      }
    } else {
      if (document.activeElement === last) {
        first.focus();
        e.preventDefault();
      }
    }
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// COMPARE
// ─────────────────────────────────────────────────────────────────────────────

async function loadCompare() {
  const res = await fetch(`${API}/api/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ids: [1, 2, 3] })
  });
  const data = await res.json();
  const candidates = data.candidates;

  const policies = ['education', 'healthcare', 'economy', 'environment', 'infrastructure'];

  const container = document.getElementById('compare-container');
  container.innerHTML = `
    <div class="compare-grid">
      <div class="cmp-header-cell" style="background:var(--surface2)"></div>
      ${candidates.map(c => `
        <div class="cmp-header-cell">
          <div class="cmp-avatar">${c.photo}</div>
          <div class="cmp-name">${c.name}</div>
          <div class="cmp-party" style="color:${c.party_color}">${c.party}</div>
        </div>
      `).join('')}

      <div class="cmp-label-cell">⚡ Integrity Score</div>
      ${candidates.map(c => `
        <div class="cmp-value-cell ${c.integrity_score === Math.max(...candidates.map(x => x.integrity_score)) ? 'winner' : ''}">
          <span class="score-badge ${c.integrity_score >= 80 ? 'high' : c.integrity_score >= 60 ? 'mid' : 'low'}">${c.integrity_score}</span>
        </div>
      `).join('')}

      <div class="cmp-label-cell">📊 Attendance</div>
      ${candidates.map(c => `<div class="cmp-value-cell mono">${c.attendance}</div>`).join('')}

      <div class="cmp-label-cell">⚖️ Criminal Cases</div>
      ${candidates.map(c => `
        <div class="cmp-value-cell">
          <span class="cases-badge ${c.criminal_cases === 0 ? 'clean' : 'flagged'}">${c.criminal_cases === 0 ? '✓ Clean' : '⚠ ' + c.criminal_cases}</span>
        </div>
      `).join('')}

      <div class="cmp-label-cell">💰 Declared Assets</div>
      ${candidates.map(c => `<div class="cmp-value-cell mono">${c.assets}</div>`).join('')}

      ${policies.map(p => `
        <div class="cmp-label-cell" style="text-transform:capitalize">📋 ${p}</div>
        ${candidates.map(c => `<div class="cmp-value-cell" style="font-size:12px;color:var(--text-2);text-align:left;padding:12px">${c.manifesto[p]}</div>`).join('')}
      `).join('')}
    </div>
    <div class="divider"></div>
    <p class="text-muted" style="font-size:12px;text-align:center">
      ⚖️ All candidates are presented with equal prominence. ElectIQ is politically neutral.
    </p>
  `;
}

// ─────────────────────────────────────────────────────────────────────────────
// BOOTHS
// ─────────────────────────────────────────────────────────────────────────────

async function loadBooths() {
  const res = await fetch(`${API}/api/booths`);
  const data = await res.json();

  const queueClass = q => q.includes('Short') ? 'queue-short' : q.includes('Moderate') ? 'queue-moderate' : 'queue-long';

  document.getElementById('booth-container').innerHTML = `
    <p class="text-muted mb-16">Showing booths for <strong class="text-gold">Mumbai North</strong> constituency</p>
    ${data.booths.map(b => `
      <div class="booth-card">
        <div class="booth-num">${b.id}</div>
        <div style="flex:1">
          <div class="booth-name">📍 ${b.name}</div>
          <div class="booth-officer">Officer: ${b.officer} &nbsp;|&nbsp; ${b.ward}</div>
          <div class="booth-meta">
            <span class="meta-tag ${queueClass(b.queue)}">🕐 ${b.queue}</span>
            ${b.accessibility ? '<span class="meta-tag" style="border-color:rgba(34,197,94,0.3);color:var(--green)">♿ Accessible</span>' : ''}
          </div>
        </div>
        <div class="booth-actions">
          <button class="btn-primary" onclick="alert('Opening Google Maps directions to ${b.name}')">Get Directions 🗺️</button>
          <button class="btn-outline" onclick="alert('Check-in registered at ${b.name}! Queue updated.')">Check In 📍</button>
        </div>
      </div>
    `).join('')}
    <div style="margin-top:16px;padding:16px;background:var(--surface2);border-radius:var(--radius);font-size:13px;color:var(--text-2)">
      💡 Queue estimates are updated every 15 minutes via crowd-sourced check-ins. Tap "Check In" when you arrive.
    </div>
  `;
}

// ─────────────────────────────────────────────────────────────────────────────
// WAR ROOM
// ─────────────────────────────────────────────────────────────────────────────

async function loadWarRoom() {
  const res = await fetch(`${API}/api/turnout`);
  const data = await res.json();

  const maxTurnout = Math.max(...data.hours.filter(h => h.turnout !== null).map(h => h.turnout));

  document.getElementById('warroom-container').innerHTML = `
    <div class="warroom-grid">
      <div class="war-stat">
        <div class="war-stat-value">${data.current}%</div>
        <div class="war-stat-label">Current Turnout (Mumbai North)</div>
      </div>
      <div class="war-stat">
        <div class="war-stat-value">${data.last_election}%</div>
        <div class="war-stat-label">Last Election Turnout</div>
      </div>
      <div class="war-stat">
        <div class="war-stat-value">${data.national_avg}%</div>
        <div class="war-stat-label">National Average</div>
      </div>
    </div>

    <div class="section-title">📊 Hourly Turnout Tracker</div>
    <div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);padding:28px;margin-bottom:24px">
      <div class="turnout-hourly" style="height:160px">
        ${data.hours.map(h => `
          <div class="hour-col">
            <div class="hour-bar-wrap" style="flex:1;display:flex;align-items:flex-end">
              <div class="hour-bar ${h.turnout === null ? 'empty' : ''}"
                style="width:100%;height:${h.turnout !== null ? Math.round((h.turnout / 100) * 140) + 'px' : '20px'}">
              </div>
            </div>
            <div class="hour-label">${h.hour}</div>
            <div class="hour-label text-gold">${h.turnout !== null ? h.turnout + '%' : '--'}</div>
          </div>
        `).join('')}
      </div>
      <div class="text-muted mt-16" style="font-size:12px">Dashed bars = upcoming hours. Data updates every 30 minutes from ECI feeds.</div>
    </div>

    <div class="section-title">🗳️ Polling Window</div>
    <div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);padding:24px;text-align:center">
      <div style="font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--text-3);margin-bottom:8px">ELECTION DAY COUNTDOWN</div>
      <div id="countdown-display" style="font-family:'Playfair Display',serif;font-size:48px;font-weight:900;color:var(--gold-light)">Loading...</div>
      <div style="font-size:13px;color:var(--text-2);margin-top:8px">until polls close on May 15, 2026 at 6:00 PM</div>
    </div>
  `;

  updateCountdown();
  setInterval(updateCountdown, 1000);
}

function updateCountdown() {
  const el = document.getElementById('countdown-display');
  if (!el) return;
  const target = new Date('2026-05-15T18:00:00');
  const now = new Date();
  const diff = target - now;
  if (diff <= 0) { el.textContent = 'Polls Closed'; return; }
  const d = Math.floor(diff / 86400000);
  const h = Math.floor((diff % 86400000) / 3600000);
  const m = Math.floor((diff % 3600000) / 60000);
  el.textContent = `${d}d ${h}h ${m}m`;
}

// ─────────────────────────────────────────────────────────────────────────────
// HISTORY
// ─────────────────────────────────────────────────────────────────────────────

async function loadHistory() {
  const res = await fetch(`${API}/api/history`);
  const data = await res.json();

  const partyColors = { 'BJP': '#f97316', 'Congress': '#3b82f6', 'AAP': '#22c55e' };

  document.getElementById('history-container').innerHTML = `
    <div class="section-title">🗺️ Mumbai North — Electoral History</div>
    <div class="history-timeline">
      ${data.history.map((h, i) => {
        const prev = data.history[i - 1];
        const flipped = prev && prev.winner !== h.winner;
        return `
          <div class="history-item">
            <div class="history-year">📅 ${h.year} General Election</div>
            <div class="history-winner" style="color:${partyColors[h.winner] || '#d4a843'}">
              ${flipped ? '🔄 ' : ''}${h.winner}
              ${flipped ? '<small style="font-size:14px;color:var(--text-2)"> (Seat flipped!)</small>' : ''}
            </div>
            <div class="history-meta">
              <span>📊 Turnout: <strong>${h.turnout}%</strong></span>
              <span>🏆 Margin: <strong class="mono">${h.margin.toLocaleString()} votes</strong></span>
            </div>
          </div>
        `;
      }).reverse().join('')}
    </div>
    <div class="divider"></div>
    <div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);padding:24px;margin-top:20px">
      <div class="section-title" style="font-size:16px">🤖 AI Analysis</div>
      <p class="text-muted" style="font-size:14px;line-height:1.8">
        Mumbai North has been <strong class="text-gold">highly competitive</strong> over the last three elections. 
        The seat flipped in 2019 with a narrow margin of just 4,300 votes before returning to BJP in 2024. 
        Historical turnout has been rising (58% → 67%), suggesting growing voter engagement. 
        Based on demographic trends and recent polling, the 2026 race is expected to be the closest yet.
      </p>
    </div>
  `;
}

// ─────────────────────────────────────────────────────────────────────────────
// QUIZ
// ─────────────────────────────────────────────────────────────────────────────

async function loadQuiz() {
  if (quizData.questions.length === 0) {
    const res = await fetch(`${API}/api/quiz`);
    const data = await res.json();
    quizData.questions = data.questions;
    quizData.current = 0;
    quizData.score = 0;
  }
  renderQuiz();
}

function renderQuiz() {
  const q = quizData;
  if (q.current >= q.questions.length) {
    showQuizResult();
    return;
  }
  const cur = q.questions[q.current];
  const progress = q.questions.map((_, i) => `
    <div class="quiz-prog-dot ${i < q.current ? 'done' : i === q.current ? 'active' : ''}"></div>
  `).join('');

  document.getElementById('quiz-container').innerHTML = `
    <div class="quiz-card">
      <div class="quiz-progress">${progress}</div>
      <div style="font-size:12px;color:var(--text-3);margin-bottom:12px">Question ${q.current + 1} of ${q.questions.length}</div>
      <div class="quiz-question">${cur.q}</div>
      <div class="quiz-options">
        ${cur.options.map((opt, i) => `
          <button class="quiz-option" onclick="answerQuiz(${i})" id="qopt-${i}">${opt}</button>
        `).join('')}
      </div>
      <div id="quiz-explanation" style="display:none" class="quiz-explanation"></div>
      <div id="quiz-next-btn" style="display:none;margin-top:20px">
        <button class="btn-primary" onclick="nextQuestion()">
          ${q.current + 1 === q.questions.length ? 'See Results 🏆' : 'Next Question →'}
        </button>
      </div>
    </div>
  `;
}

function answerQuiz(selected) {
  if (quizData.answered) return;
  quizData.answered = true;
  const cur = quizData.questions[quizData.current];

  document.querySelectorAll('.quiz-option').forEach((btn, i) => {
    btn.disabled = true;
    if (i === cur.answer) btn.classList.add('correct');
    if (i === selected && i !== cur.answer) btn.classList.add('wrong');
  });

  if (selected === cur.answer) quizData.score++;

  const expEl = document.getElementById('quiz-explanation');
  expEl.style.display = 'block';
  expEl.innerHTML = `<strong>${selected === cur.answer ? '✅ Correct!' : '❌ Incorrect.'}</strong> ${cur.explanation}`;

  document.getElementById('quiz-next-btn').style.display = 'block';
}

function nextQuestion() {
  quizData.current++;
  quizData.answered = false;
  renderQuiz();
}

function showQuizResult() {
  const pct = Math.round((quizData.score / quizData.questions.length) * 100);
  const badge = pct === 100 ? '🥇 Civic Champion' : pct >= 80 ? '🥈 Democracy Expert' : pct >= 60 ? '🥉 Informed Voter' : '📚 Keep Learning';

  document.getElementById('quiz-container').innerHTML = `
    <div class="quiz-card" style="text-align:center">
      <div class="quiz-score-val">${pct}%</div>
      <div style="font-size:24px;margin:16px 0">${badge}</div>
      <div style="font-size:16px;color:var(--text-2);margin-bottom:28px">
        You got <strong class="text-gold">${quizData.score} out of ${quizData.questions.length}</strong> questions correct
      </div>
      <button class="btn-primary" onclick="resetQuiz()">Try Again 🔄</button>
    </div>
  `;
}

function resetQuiz() {
  quizData = { questions: [], current: 0, score: 0, answered: false };
  loadQuiz();
}

// ─────────────────────────────────────────────────────────────────────────────
// IMPACT
// ─────────────────────────────────────────────────────────────────────────────

async function loadImpact() {
  const res = await fetch(`${API}/api/impact`);
  const d = await res.json();

  document.getElementById('impact-container').innerHTML = `
    <div class="impact-grid">
      <div class="impact-card">
        <div class="impact-number">${d.last_margin.toLocaleString()}</div>
        <div class="impact-label">votes decided the last election in ${d.constituency}</div>
      </div>
      <div class="impact-card">
        <div class="impact-number">${d.your_area_turnout}%</div>
        <div class="impact-label">turnout in your area vs ${d.national_avg}% national average</div>
      </div>
      <div class="impact-card">
        <div class="impact-number">${d.turnout_last}%</div>
        <div class="impact-label">turnout in the last election</div>
      </div>
    </div>

    <div class="impact-message">
      <div class="impact-message-text">🗳️ "${d.message}"</div>
      <p style="color:var(--text-2);font-size:14px">
        If turnout in your area increased from ${d.your_area_turnout}% to just ${d.national_avg}%,
        that's thousands of additional voices that could flip the result.
      </p>
    </div>

    <div class="divider"></div>
    <div class="section-title" style="margin-top:24px">Share Your Pledge</div>
    <div style="display:flex;gap:12px;flex-wrap:wrap">
      <button class="btn-primary" onclick="alert('Pledge registered! You are voter #12,847 to pledge for Mumbai North.')">🗳️ I Pledge to Vote</button>
      <button class="btn-outline" onclick="alert('Sharing card generated! Copy this link to WhatsApp.')">📱 Share on WhatsApp</button>
      <button class="btn-outline" onclick="alert('Calendar event added: Polling Day — May 15, 2026 at 7AM')">📅 Add to Calendar</button>
    </div>
  `;
}

// ─────────────────────────────────────────────────────────────────────────────
// VOTER CHECK
// ─────────────────────────────────────────────────────────────────────────────

async function checkVoter() {
  const epic = document.getElementById('epic-input').value.trim();
  if (!epic) { alert('Please enter an EPIC number'); return; }

  const resultEl = document.getElementById('voter-result');
  resultEl.innerHTML = '<div style="text-align:center;padding:20px"><div class="loading-spinner"></div></div>';
  resultEl.className = 'voter-result';

  const res = await fetch(`${API}/api/voter-check`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ epic })
  });
  const data = await res.json();

  if (data.registered) {
    resultEl.className = 'voter-result success';
    resultEl.innerHTML = `
      <div style="text-align:center;margin-bottom:16px;font-size:24px">✅ Registered Voter</div>
      ${[
        ['Constituency', data.constituency],
        ['Polling Booth', data.booth],
        ['Booth Number', data.booth_no],
        ['Serial Number', data.serial_no],
      ].map(([k, v]) => `
        <div class="voter-result-row">
          <span class="voter-result-key">${k}</span>
          <span class="voter-result-val">${v}</span>
        </div>
      `).join('')}
    `;
  } else {
    resultEl.className = 'voter-result fail';
    resultEl.innerHTML = `<div style="text-align:center;padding:20px">❌ ${data.message}<br><br><a href="https://voters.eci.gov.in" target="_blank" style="color:var(--gold)">Register on voters.eci.gov.in →</a></div>`;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// INIT
// ─────────────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // Chat is the default view — nothing to load
  console.log('⚡ ElectIQ initialized');
});
