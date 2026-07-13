/* ====================================================
   WISE — Simple Social Help Assistant
   Clean, readable citizen UI · HY/EN · RAG backend
   ==================================================== */

(function () {
  'use strict';

  function getApiBase() {
    if (typeof window.WISEF_getApiBase === 'function') {
      return window.WISEF_getApiBase();
    }
    var host = (location && location.hostname) || '';
    if (host === 'localhost' || host === '127.0.0.1') {
      return 'http://127.0.0.1:8000';
    }
    return '';
  }

  let backendOnline = false;
  let chatOpen = false;
  let chatInitialized = false;
  let hasConversation = false;
  /** Multi-turn context sent to /api/chat */
  let conversationHistory = [];

  let root, fab, panel, messagesEl, inputEl, sendBtn, statusEl, homeEl, topicsEl;

  /** Flat list of easy questions — no tabs, no jargon */
  const TOPICS = [
    { icon: '👶', key: 'chat.q1', hy: 'Մինչև 2 տարեկան երեխայի նպաստ', en: 'Childcare allowance under 2' },
    { icon: '🎁', key: 'chat.q2', hy: 'Երեխայի ծննդյան միանվագ նպաստ', en: 'One-time childbirth benefit' },
    { icon: '👨‍👩‍👧‍👦', key: 'chat.q3', hy: 'Ընտանեկան նպաստ', en: 'Family benefit' },
    { icon: '👴', key: 'chat.q4', hy: 'Տարիքային կենսաթոշակ', en: 'Age pension' },
    { icon: '♿', key: 'chat.q5', hy: 'Հաշմանդամության կենսաթոշակ', en: 'Disability pension' },
    { icon: '💼', key: 'chat.q6', hy: 'Գործազրկության կարգավիճակ', en: 'Unemployment status' },
    { icon: '⚡', key: 'chat.q7', hy: 'Էլեկտրաէներգիայի փոխհատուցում', en: 'Electricity subsidy' },
    { icon: '🏠', key: 'chat.q9', hy: 'Տեղահանվածների աջակցություն', en: 'Displaced persons support' },
    { icon: '🩺', key: 'chat.q10', hy: 'Ֆունկցիոնալության գնահատում', en: 'Functional assessment / disability' },
    { icon: '📞', key: 'chat.q8', hy: 'ՄՍԾ թեժ գիծ 114', en: 'Hotline 114 contacts' }
  ];

  function t(key, fallback) {
    if (window.wisefI18n && typeof window.wisefI18n.t === 'function') {
      const v = window.wisefI18n.t(key);
      if (v && v !== key) return v;
    }
    return fallback || key;
  }

  function lang() {
    return window.wisefI18n ? window.wisefI18n.getLang() : 'hy';
  }

  function topicLabel(item) {
    return t(item.key, lang() === 'en' ? item.en : item.hy);
  }

  function init() {
    if (chatInitialized) return;
    buildUI();
    bindEvents();
    renderTopics();
    pollStatus();
    setInterval(pollStatus, 12000);
    chatInitialized = true;
  }

  function buildUI() {
    root = document.createElement('div');
    root.className = 'wise-help';
    root.innerHTML = `
      <button type="button" class="wise-help__fab" aria-expanded="false" aria-controls="wise-help-panel">
        <span class="wise-help__fab-icon" aria-hidden="true">
          <svg class="wise-help__fab-svg wise-help__fab-svg--chat" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          <svg class="wise-help__fab-svg wise-help__fab-svg--close" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </span>
        <span class="wise-help__fab-label" data-i18n="chat.fab">Հարցրեք մեզ</span>
      </button>

      <div class="wise-help__panel" id="wise-help-panel" role="dialog" aria-modal="true" aria-labelledby="wise-help-title" hidden>
        <header class="wise-help__header">
          <div class="wise-help__header-text">
            <h2 class="wise-help__title" id="wise-help-title" data-i18n="chat.title">Սոցիալական օգնական</h2>
            <p class="wise-help__status" data-status>
              <span class="wise-help__status-dot"></span>
              <span class="wise-help__status-text" data-i18n="chat.status_offline">Միացում…</span>
            </p>
          </div>
          <button type="button" class="wise-help__close" aria-label="Close">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </header>

        <div class="wise-help__body">
          <div class="wise-help__home" data-home>
            <p class="wise-help__hello" data-i18n="chat.welcome_title">Բարև ձեզ</p>
            <p class="wise-help__intro" data-i18n="chat.welcome">
              Հարցրեք նպաստների, կենսաթոշակների և սոցիալական ծրագրերի մասին։ Պատասխանները հիմնված են պաշտոնական տեղեկատվության վրա։
            </p>
            <p class="wise-help__topics-label" data-i18n="chat.topics_label">Ընտրեք թեմա կամ գրեք հարց</p>
            <div class="wise-help__topics" data-topics></div>
          </div>

          <div class="wise-help__messages" data-messages hidden></div>
        </div>

        <form class="wise-help__composer" data-composer>
          <label class="wise-help__sr-only" for="wise-help-input" data-i18n="chat.placeholder">Գրեք հարցը</label>
          <input
            id="wise-help-input"
            class="wise-help__input"
            type="text"
            autocomplete="off"
            enterkeyhint="send"
            placeholder="Օրինակ՝ տարիքային կենսաթոշակ"
            data-i18n="chat.placeholder"
          />
          <button type="submit" class="wise-help__send" aria-label="Send">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </button>
        </form>

        <p class="wise-help__foot" data-i18n="chat.disclaimer">
          Տեղեկատվական է · Պաշտոնական որոշման համար՝ 114
        </p>
      </div>
    `;

    document.body.appendChild(root);

    fab = root.querySelector('.wise-help__fab');
    panel = root.querySelector('.wise-help__panel');
    messagesEl = root.querySelector('[data-messages]');
    homeEl = root.querySelector('[data-home]');
    topicsEl = root.querySelector('[data-topics]');
    inputEl = root.querySelector('.wise-help__input');
    sendBtn = root.querySelector('.wise-help__send');
    statusEl = root.querySelector('[data-status]');
  }

  function renderTopics() {
    if (!topicsEl) return;
    topicsEl.innerHTML = '';
    TOPICS.forEach((item) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'wise-help__topic';
      btn.innerHTML = `
        <span class="wise-help__topic-icon" aria-hidden="true">${item.icon}</span>
        <span class="wise-help__topic-text">${escapeHtml(topicLabel(item))}</span>
      `;
      btn.addEventListener('click', () => ask(topicLabel(item)));
      topicsEl.appendChild(btn);
    });
  }

  function bindEvents() {
    fab.addEventListener('click', toggle);
    root.querySelector('.wise-help__close').addEventListener('click', close);

    root.querySelector('[data-composer]').addEventListener('submit', (e) => {
      e.preventDefault();
      const q = (inputEl.value || '').trim();
      if (!q) return;
      inputEl.value = '';
      ask(q);
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && chatOpen) close();
    });

    document.addEventListener('wisefLangChanged', () => {
      applyI18n();
      renderTopics();
      updateStatusUI();
    });
  }

  function applyI18n() {
    if (!window.wisefI18n) return;
    root.querySelectorAll('[data-i18n]').forEach((el) => {
      const key = el.getAttribute('data-i18n');
      if (!key) return;
      if (el.matches('input, textarea')) {
        el.placeholder = t(key, el.placeholder);
      } else {
        el.textContent = t(key, el.textContent);
      }
    });
  }

  let animating = false;

  function toggle() {
    if (animating) return;
    if (chatOpen) close();
    else open();
  }

  function open() {
    if (chatOpen || animating) return;
    animating = true;
    chatOpen = true;

    panel.hidden = false;
    panel.classList.remove('wise-help__panel--closing');
    fab.setAttribute('aria-expanded', 'true');
    fab.classList.add('wise-help__fab--open');
    root.classList.add('wise-help--open');
    applyI18n();

    // Double rAF so the browser applies the "from" state before animating "to"
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        panel.classList.add('wise-help__panel--open');
        animating = false;
        setTimeout(function () {
          if (chatOpen && inputEl) inputEl.focus();
        }, 320);
      });
    });
  }

  function close() {
    if (!chatOpen || animating) return;
    animating = true;
    chatOpen = false;

    fab.setAttribute('aria-expanded', 'false');
    fab.classList.remove('wise-help__fab--open');
    root.classList.remove('wise-help--open');
    panel.classList.remove('wise-help__panel--open');
    panel.classList.add('wise-help__panel--closing');

    var finished = false;
    function finishClose() {
      if (finished) return;
      finished = true;
      panel.removeEventListener('transitionend', onEnd);
      panel.hidden = true;
      panel.classList.remove('wise-help__panel--closing');
      animating = false;
    }

    function onEnd(e) {
      if (e.target !== panel) return;
      if (e.propertyName !== 'opacity' && e.propertyName !== 'transform') return;
      finishClose();
    }

    panel.addEventListener('transitionend', onEnd);
    // Fallback if transitionend doesn't fire
    setTimeout(finishClose, 380);
  }

  async function pollStatus() {
    const API_BASE = getApiBase();
    if (!API_BASE) {
      backendOnline = false;
      updateStatusUI();
      return;
    }
    try {
      const r = await fetch(`${API_BASE}/api/status`, { signal: AbortSignal.timeout(5000) });
      backendOnline = r.ok && (await r.json()).status === 'ready';
    } catch (e) {
      backendOnline = false;
    }
    updateStatusUI();
  }

  function updateStatusUI() {
    if (!statusEl) return;
    const text = statusEl.querySelector('.wise-help__status-text');
    statusEl.classList.toggle('wise-help__status--on', backendOnline);
    statusEl.classList.toggle('wise-help__status--off', !backendOnline);
    if (text) {
      text.textContent = backendOnline
        ? t('chat.status_ready', 'Պատրաստ է օգնել')
        : t('chat.status_offline', 'Սերվերը անջատված է');
    }
  }

  function showConversation() {
    if (hasConversation) return;
    hasConversation = true;
    homeEl.hidden = true;
    messagesEl.hidden = false;
    root.classList.add('wise-help--chatting');
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function formatAnswer(text) {
    let html = escapeHtml(text || '');
    html = html.replace(/^###\s+(.+)$/gm, '<h4 class="wise-help__h">$1</h4>');
    html = html.replace(/^##\s+(.+)$/gm, '<h3 class="wise-help__h">$1</h3>');
    html = html.replace(/^#\s+(.+)$/gm, '<h3 class="wise-help__h">$1</h3>');
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    const lines = html.split('\n');
    const out = [];
    let inUl = false;
    let inOl = false;

    for (const line of lines) {
      const tr = line.trim();
      if (tr.startsWith('- ') || tr.startsWith('* ')) {
        if (inOl) { out.push('</ol>'); inOl = false; }
        if (!inUl) { out.push('<ul class="wise-help__list">'); inUl = true; }
        out.push('<li>' + tr.slice(2) + '</li>');
      } else if (/^\d+\.\s/.test(tr)) {
        if (inUl) { out.push('</ul>'); inUl = false; }
        if (!inOl) { out.push('<ol class="wise-help__list">'); inOl = true; }
        out.push('<li>' + tr.replace(/^\d+\.\s/, '') + '</li>');
      } else {
        if (inUl) { out.push('</ul>'); inUl = false; }
        if (inOl) { out.push('</ol>'); inOl = false; }
        if (!tr) continue;
        if (tr.startsWith('<h3') || tr.startsWith('<h4')) out.push(tr);
        else out.push('<p>' + tr + '</p>');
      }
    }
    if (inUl) out.push('</ul>');
    if (inOl) out.push('</ol>');
    return out.join('');
  }

  function addUserBubble(text) {
    const el = document.createElement('div');
    el.className = 'wise-help__msg wise-help__msg--user';
    el.innerHTML = `<div class="wise-help__bubble">${escapeHtml(text)}</div>`;
    messagesEl.appendChild(el);
  }

  function addBotBubble(htmlInner, extras) {
    const el = document.createElement('div');
    el.className = 'wise-help__msg wise-help__msg--bot';
    let body = `<div class="wise-help__bubble wise-help__bubble--bot">${htmlInner}</div>`;

    if (extras && extras.sources && extras.sources.length) {
      const links = extras.sources
        .slice(0, 4)
        .map((s) => {
          const title = typeof s === 'string' ? s : (s.title || 'Source');
          const url = typeof s === 'object' ? s.url : null;
          const short = title.length > 42 ? title.slice(0, 40) + '…' : title;
          if (url) {
            return `<a class="wise-help__source" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(short)}</a>`;
          }
          return `<span class="wise-help__source wise-help__source--plain">${escapeHtml(short)}</span>`;
        })
        .join('');
      body += `<div class="wise-help__sources"><span class="wise-help__sources-label">${escapeHtml(t('chat.sources_label', 'Աղբյուրներ'))}</span>${links}</div>`;
    }

    if (extras && extras.follow_ups && extras.follow_ups.length) {
      const chips = extras.follow_ups
        .slice(0, 3)
        .map(
          (q) =>
            `<button type="button" class="wise-help__chip" data-q="${escapeHtml(q)}">${escapeHtml(q)}</button>`
        )
        .join('');
      body += `<div class="wise-help__chips">${chips}</div>`;
    }

    if (extras && extras.fidelity && typeof extras.fidelity.grounding_score === 'number') {
      const g = extras.fidelity.grounding_score;
      const risk = extras.fidelity.risk || '';
      const pct = Math.round(g * 100);
      const label =
        lang() === 'en'
          ? `Answer grounded in sources: ${pct}% (${risk} risk)`
          : `Աղբյուրներին համապատասխանություն՝ ${pct}% (${risk})`;
      body += `<p class="wise-help__ground">${escapeHtml(label)}</p>`;
    }

    el.innerHTML = body;
    el.querySelectorAll('.wise-help__chip').forEach((btn) => {
      btn.addEventListener('click', () => ask(btn.getAttribute('data-q') || btn.textContent));
    });
    messagesEl.appendChild(el);
  }

  function addTyping() {
    const el = document.createElement('div');
    el.className = 'wise-help__msg wise-help__msg--bot wise-help__typing';
    el.innerHTML = `
      <div class="wise-help__bubble wise-help__bubble--bot">
        <span class="wise-help__dots"><i></i><i></i><i></i></span>
        <span class="wise-help__typing-text">${escapeHtml(t('chat.thinking', 'Մտածում եմ…'))}</span>
      </div>`;
    messagesEl.appendChild(el);
    return el;
  }

  async function ask(text) {
    const q = (text || '').trim();
    if (!q) return;

    showConversation();
    addUserBubble(q);
    const typing = addTyping();

    const API_BASE = getApiBase();
    if (!API_BASE) {
      typing.remove();
      addBotBubble(
        `<p>${escapeHtml(
          t(
            'chat.err_no_api',
            'Արտադրական կայքում AI-ն աշխատելու համար պետք է տեղադրել backend-ը (Render/Railway) և լրացնել productionApiBase-ը config.js-ում։ Տե՛ս DEPLOY.md։'
          )
        )}</p>`
      );
      return;
    }

    try {
      const historyPayload = conversationHistory.slice(-8);
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q, lang: lang(), history: historyPayload })
      });
      typing.remove();

      if (!res.ok) {
        if (res.status === 429) {
          addBotBubble(
            `<p>${escapeHtml(
              lang() === 'en'
                ? 'Too many questions in a short time. Please wait a minute and try again.'
                : 'Շատ հարցեր կարճ ժամանակում։ Սպասեք մեկ րոպե և կրկին փորձեք։'
            )}</p>`
          );
          return;
        }
        addBotBubble(
          `<p>${escapeHtml(t('chat.err_offline', 'Հիմա չեմ կարող պատասխանել։ Ստուգեք, որ սերվերն աշխատում է։'))}</p>`
        );
        return;
      }

      const data = await res.json();
      conversationHistory.push({ role: 'user', content: q });
      if (data.answer) {
        conversationHistory.push({ role: 'assistant', content: String(data.answer).slice(0, 2000) });
      }
      if (conversationHistory.length > 16) {
        conversationHistory = conversationHistory.slice(-16);
      }
      addBotBubble(formatAnswer(data.answer), {
        sources: data.sources || [],
        follow_ups: data.follow_ups || [],
        fidelity: data.fidelity || null
      });
    } catch (e) {
      typing.remove();
      addBotBubble(
        `<p>${escapeHtml(t('chat.err_offline', 'Կապ չկա սերվերի հետ։ Գործարկեք start_backend.bat և կրկին փորձեք։'))}</p>
         <p><strong>114</strong> — ՄՍԾ թեժ գիծ</p>`
      );
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
