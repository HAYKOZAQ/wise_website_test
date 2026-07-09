/* ====================================================
   WISE Foundation — Social Programs AI Assistant
   Glassmorphic redesign · ARLIS-backed RAG · HY/EN
   ==================================================== */

(function () {
  'use strict';

  const API_BASE = 'http://127.0.0.1:8000';
  let backendStatus = { online: false, vector: false, legalActs: 0 };
  let chatOpen = false;
  let chatInitialized = false;

  let widgetContainer, chatToggleBtn, chatWindow, chatMessages, chatInput, chatSendBtn;
  let statusDot, statusText, emptyState, suggestionsBox;

  const suggestionData = {
    allowances: [
      { key: 'chat.suggest_allow_1', fallback: 'Մինչև 2 տարեկան երեխայի նպաստ' },
      { key: 'chat.suggest_allow_2', fallback: 'Երեխայի ծննդյան միանվագ նպաստ' },
      { key: 'chat.suggest_allow_3', fallback: 'Ընտանեկան նպաստ չափորոշիչներ' },
      { key: 'chat.suggest_allow_4', fallback: 'Մայրության նպաստ' }
    ],
    pensions: [
      { key: 'chat.suggest_pens_1', fallback: 'Տարիքային կենսաթոշակ' },
      { key: 'chat.suggest_pens_2', fallback: 'Հաշմանդամության կենսաթոշակ' },
      { key: 'chat.suggest_pens_3', fallback: 'Կերակրողին կորցնելու կենսաթոշակ' },
      { key: 'chat.suggest_pens_4', fallback: 'Ծերության սոցիալական նպաստ' }
    ],
    employment: [
      { key: 'chat.suggest_emp_1', fallback: 'Գործազրկության կարգավիճակի ձևակերպում' },
      { key: 'chat.suggest_emp_2', fallback: 'Անվճար մասնագիտական ուսուցում' },
      { key: 'chat.suggest_emp_3', fallback: 'Գործատուներին աջակցություն' },
      { key: 'chat.suggest_emp_4', fallback: 'Սեզոնային զբաղվածություն' }
    ],
    services: [
      { key: 'chat.suggest_svc_1', fallback: 'Պրոթեզաօրթոպեդիկ պարագաներ' },
      { key: 'chat.suggest_svc_2', fallback: 'Տնային խնամքի ծառայություններ' },
      { key: 'chat.suggest_svc_3', fallback: 'Զինծառայողների սոցիալական աջակցություն' }
    ],
    contacts: [
      { key: 'chat.suggest_util_1', fallback: 'ՄՍԾ թեժ գիծ և կոնտակտներ' },
      { key: 'chat.suggest_util_2', fallback: 'Էլեկտրաէներգիայի սակագնի փոխհատուցում' },
      { key: 'chat.suggest_util_3', fallback: 'Բնական գազի սակագնի զեղչեր' }
    ]
  };

  let activeCategory = 'allowances';

  function t(key, fallback) {
    if (window.wisefI18n) return window.wisefI18n.t(key);
    return fallback || key;
  }

  function getLang() {
    return window.wisefI18n ? window.wisefI18n.getLang() : 'hy';
  }

  function initChat() {
    if (chatInitialized) return;
    createWidgetDOM();
    setupListeners();
    renderSuggestions();
    checkBackendStatus();
    setInterval(checkBackendStatus, 15000);
    chatInitialized = true;
  }

  function createWidgetDOM() {
    widgetContainer = document.createElement('div');
    widgetContainer.className = 'wise-chat-widget';
    widgetContainer.setAttribute('aria-label', 'WISE AI Assistant');

    chatToggleBtn = document.createElement('button');
    chatToggleBtn.className = 'wise-chat-toggle glass';
    chatToggleBtn.type = 'button';
    chatToggleBtn.setAttribute('aria-expanded', 'false');
    chatToggleBtn.setAttribute('aria-label', 'Open chat');
    chatToggleBtn.innerHTML = `
      <span class="wise-chat-toggle__pulse" aria-hidden="true"></span>
      <svg class="wise-chat-toggle__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
      </svg>
      <svg class="wise-chat-toggle__close" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:none;">
        <line x1="18" y1="6" x2="6" y2="18"></line>
        <line x1="6" y1="6" x2="18" y2="18"></line>
      </svg>
    `;

    chatWindow = document.createElement('div');
    chatWindow.className = 'wise-chat-window glass';
    chatWindow.style.display = 'none';
    chatWindow.setAttribute('role', 'dialog');
    chatWindow.setAttribute('aria-modal', 'true');

    const header = document.createElement('div');
    header.className = 'wise-chat-header';
    header.innerHTML = `
      <div class="wise-chat-header__brand">
        <div class="wise-chat-header__avatar" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
          </svg>
        </div>
        <div class="wise-chat-header__info">
          <h3 class="wise-chat-header__title" data-i18n="chat.title">Սոցիալական ծրագրերի օգնական</h3>
          <div class="wise-chat-header__meta">
            <span class="wise-chat-header__status">
              <span class="wise-chat-header__dot"></span>
              <span class="wise-chat-header__status-text" data-i18n="chat.status_offline">Անցանց</span>
            </span>
            <span class="wise-chat-header__powered" data-i18n="chat.powered">ARLIS իրավական բազա</span>
          </div>
        </div>
      </div>
      <button class="wise-chat-header__close" type="button" aria-label="Close chat">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    `;

    chatMessages = document.createElement('div');
    chatMessages.className = 'wise-chat-messages';

    emptyState = document.createElement('div');
    emptyState.className = 'wise-chat-empty';
    emptyState.innerHTML = `
      <div class="wise-chat-empty__icon" aria-hidden="true">💬</div>
      <p class="wise-chat-empty__title" data-i18n="chat.welcome_title">Հարցրեք սոցիալական ծրագրերի մասին</p>
      <p class="wise-chat-empty__text" data-i18n="chat.welcome">Պատասխանները հիմնված են ARLIS պաշտոնական ակտերի և ծրագրերի կանոնների վրա։</p>
    `;
    chatMessages.appendChild(emptyState);

    suggestionsBox = document.createElement('div');
    suggestionsBox.className = 'wise-chat-suggestions-box';
    suggestionsBox.innerHTML = `
      <div class="wise-chat-tabs" role="tablist">
        <button type="button" class="wise-chat-tab active" data-cat="allowances" data-i18n="chat.cat_allowances">Նպաստներ</button>
        <button type="button" class="wise-chat-tab" data-cat="pensions" data-i18n="chat.cat_pensions">Կենսաթոշակներ</button>
        <button type="button" class="wise-chat-tab" data-cat="employment" data-i18n="chat.cat_employment">Աշխատանք</button>
        <button type="button" class="wise-chat-tab" data-cat="services" data-i18n="chat.cat_services">Ծառայություններ</button>
        <button type="button" class="wise-chat-tab" data-cat="contacts" data-i18n="chat.cat_contacts">Կապ & Կոմունալ</button>
      </div>
      <div class="wise-chat-suggestions"></div>
    `;

    const footer = document.createElement('form');
    footer.className = 'wise-chat-footer';
    footer.innerHTML = `
      <div class="wise-chat-composer">
        <textarea class="wise-chat-input" rows="1" placeholder="Հարցրեք նպաստների, կենսաթոշակների կամ ծրագրերի մասին..." data-i18n="chat.placeholder" required></textarea>
        <button type="submit" class="wise-chat-send" aria-label="Send message">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </div>
      <p class="wise-chat-disclaimer" data-i18n="chat.disclaimer">Տեղեկատվական բնույթի է · Պաշտոնական որոշման համար՝ ՄՍԾ 114</p>
    `;

    chatInput = footer.querySelector('.wise-chat-input');
    chatSendBtn = footer.querySelector('.wise-chat-send');
    statusDot = header.querySelector('.wise-chat-header__dot');
    statusText = header.querySelector('.wise-chat-header__status-text');

    chatWindow.appendChild(header);
    chatWindow.appendChild(chatMessages);
    chatWindow.appendChild(suggestionsBox);
    chatWindow.appendChild(footer);

    widgetContainer.appendChild(chatToggleBtn);
    widgetContainer.appendChild(chatWindow);
    document.body.appendChild(widgetContainer);
  }

  function hideEmptyState() {
    if (emptyState) emptyState.style.display = 'none';
  }

  function renderSuggestions() {
    const grid = chatWindow.querySelector('.wise-chat-suggestions');
    if (!grid) return;
    grid.innerHTML = '';
    const items = suggestionData[activeCategory] || [];
    items.forEach((item) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'wise-chat-suggest-btn';
      btn.textContent = t(item.key, item.fallback);
      btn.addEventListener('click', () => handleUserMessage(btn.textContent));
      grid.appendChild(btn);
    });
  }

  function setupListeners() {
    chatToggleBtn.addEventListener('click', toggleChat);
    chatWindow.querySelector('.wise-chat-header__close').addEventListener('click', toggleChat);

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && chatOpen) {
        e.preventDefault();
        toggleChat();
      }
    });

    chatWindow.querySelector('.wise-chat-footer').addEventListener('submit', (e) => {
      e.preventDefault();
      const text = chatInput.value.trim();
      if (!text) return;
      chatInput.value = '';
      autoResizeInput();
      handleUserMessage(text);
    });

    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatWindow.querySelector('.wise-chat-footer').requestSubmit();
      }
    });

    chatInput.addEventListener('input', autoResizeInput);

    chatWindow.querySelectorAll('.wise-chat-tab').forEach((tab) => {
      tab.addEventListener('click', () => {
        chatWindow.querySelectorAll('.wise-chat-tab').forEach((x) => x.classList.remove('active'));
        tab.classList.add('active');
        activeCategory = tab.getAttribute('data-cat');
        renderSuggestions();
      });
    });

    document.addEventListener('wisefLangChanged', () => translateUI());
  }

  function autoResizeInput() {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
  }

  function toggleChat() {
    chatOpen = !chatOpen;
    chatToggleBtn.setAttribute('aria-expanded', chatOpen ? 'true' : 'false');
    const iconChat = chatToggleBtn.querySelector('.wise-chat-toggle__icon');
    const iconClose = chatToggleBtn.querySelector('.wise-chat-toggle__close');

    if (chatOpen) {
      chatWindow.style.display = 'flex';
      chatWindow.classList.add('wise-chat-window--open');
      iconChat.style.display = 'none';
      iconClose.style.display = 'block';
      setTimeout(() => chatInput.focus(), 50);
    } else {
      chatWindow.style.display = 'none';
      chatWindow.classList.remove('wise-chat-window--open');
      iconChat.style.display = 'block';
      iconClose.style.display = 'none';
    }
  }

  function translateUI() {
    if (!window.wisefI18n) return;
    const map = [
      ['.wise-chat-header__title', 'chat.title'],
      ['.wise-chat-header__powered', 'chat.powered'],
      ['.wise-chat-empty__title', 'chat.welcome_title'],
      ['.wise-chat-empty__text', 'chat.welcome'],
      ['.wise-chat-disclaimer', 'chat.disclaimer']
    ];
    map.forEach(([sel, key]) => {
      const el = chatWindow.querySelector(sel);
      if (el) el.textContent = t(key);
    });
    if (chatInput) chatInput.placeholder = t('chat.placeholder');
    chatWindow.querySelectorAll('.wise-chat-tab').forEach((tab) => {
      const cat = tab.getAttribute('data-cat');
      tab.textContent = t(`chat.cat_${cat}`);
    });
    renderSuggestions();
    updateStatusText();
  }

  async function checkBackendStatus() {
    try {
      const r = await fetch(`${API_BASE}/api/status`, { signal: AbortSignal.timeout(3000) });
      if (r.ok) {
        const data = await r.json();
        backendStatus.online = data.status === 'ready';
        backendStatus.vector = !!data.vector_search_active;
        backendStatus.legalActs = data.legal_acts || 0;
      } else {
        backendStatus.online = false;
      }
    } catch (e) {
      backendStatus.online = false;
    }
    updateStatusUI();
  }

  function updateStatusUI() {
    if (!statusDot || !statusText) return;
    if (backendStatus.online) {
      statusDot.className = 'wise-chat-header__dot wise-chat-header__dot--online';
      updateStatusText();
      chatSendBtn.disabled = false;
      chatInput.disabled = false;
    } else {
      statusDot.className = 'wise-chat-header__dot wise-chat-header__dot--offline';
      statusText.textContent = t('chat.status_offline', 'Անցանց');
      chatSendBtn.disabled = false; // still allow attempt / show error
    }
  }

  function updateStatusText() {
    if (!statusText || !backendStatus.online) return;
    if (backendStatus.vector) {
      statusText.textContent = t('chat.status_active', 'Ակտիվ · Vector');
    } else {
      statusText.textContent = t('chat.status_keyword', 'Ակտիվ · Keyword');
    }
  }

  function escapeHTML(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function parseMarkdown(text) {
    let html = escapeHTML(text);
    // Headings ## /
    html = html.replace(/^###\s+(.+)$/gm, '<h5 class="wise-chat-h">$1</h5>');
    html = html.replace(/^##\s+(.+)$/gm, '<h4 class="wise-chat-h">$1</h4>');
    html = html.replace(/^#\s+(.+)$/gm, '<h4 class="wise-chat-h">$1</h4>');
    // Bold
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    const lines = html.split('\n');
    const result = [];
    let inUl = false;
    let inOl = false;

    for (let line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
        if (inOl) { result.push('</ol>'); inOl = false; }
        if (!inUl) { result.push('<ul class="wise-chat-list">'); inUl = true; }
        result.push('<li>' + trimmed.substring(2) + '</li>');
      } else if (/^\d+\.\s/.test(trimmed)) {
        if (inUl) { result.push('</ul>'); inUl = false; }
        if (!inOl) { result.push('<ol class="wise-chat-list">'); inOl = true; }
        result.push('<li>' + trimmed.replace(/^\d+\.\s/, '') + '</li>');
      } else {
        if (inUl) { result.push('</ul>'); inUl = false; }
        if (inOl) { result.push('</ol>'); inOl = false; }
        if (trimmed.startsWith('<h4') || trimmed.startsWith('<h5')) {
          result.push(trimmed);
        } else if (trimmed === '') {
          result.push('');
        } else {
          result.push('<p class="wise-chat-p">' + line + '</p>');
        }
      }
    }
    if (inUl) result.push('</ul>');
    if (inOl) result.push('</ol>');
    return result.join('\n');
  }

  function appendMessage(text, sender, extras) {
    hideEmptyState();
    const msg = document.createElement('div');
    msg.className = `wise-chat-msg wise-chat-msg--${sender}`;
    const body = sender === 'assistant' ? parseMarkdown(text) : escapeHTML(text);
    msg.innerHTML = `
      <div class="wise-chat-msg__bubble">
        <div class="wise-chat-msg__text">${body}</div>
      </div>
    `;
    chatMessages.appendChild(msg);

    if (extras && extras.sources && extras.sources.length) {
      appendSources(extras.sources);
    }
    if (extras && extras.follow_ups && extras.follow_ups.length) {
      appendFollowUps(extras.follow_ups);
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function appendSources(sources) {
    const wrap = document.createElement('div');
    wrap.className = 'wise-chat-sources';
    const label = document.createElement('span');
    label.className = 'wise-chat-sources__label';
    label.textContent = t('chat.sources_label', 'Աղբյուրներ');
    wrap.appendChild(label);

    const seen = new Set();
    sources.forEach((s) => {
      const title = typeof s === 'string' ? s : (s.title || 'Source');
      const url = typeof s === 'object' ? s.url : null;
      const key = title + (url || '');
      if (seen.has(key)) return;
      seen.add(key);

      if (url) {
        const a = document.createElement('a');
        a.className = 'wise-chat-sources__tag wise-chat-sources__tag--link';
        a.href = url;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.textContent = title.length > 48 ? title.slice(0, 46) + '…' : title;
        a.title = title;
        wrap.appendChild(a);
      } else {
        const span = document.createElement('span');
        span.className = 'wise-chat-sources__tag';
        span.textContent = title.length > 48 ? title.slice(0, 46) + '…' : title;
        span.title = title;
        wrap.appendChild(span);
      }
    });
    chatMessages.appendChild(wrap);
  }

  function appendFollowUps(items) {
    const wrap = document.createElement('div');
    wrap.className = 'wise-chat-followups';
    items.forEach((q) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'wise-chat-followup-btn';
      btn.textContent = q;
      btn.addEventListener('click', () => handleUserMessage(q));
      wrap.appendChild(btn);
    });
    chatMessages.appendChild(wrap);
  }

  function appendTypingIndicator() {
    hideEmptyState();
    const ind = document.createElement('div');
    ind.className = 'wise-chat-msg wise-chat-msg--assistant wise-chat-typing-indicator';
    ind.innerHTML = `
      <div class="wise-chat-msg__bubble wise-chat-msg__bubble--typing">
        <div class="wise-chat-dots"><span></span><span></span><span></span></div>
      </div>
    `;
    chatMessages.appendChild(ind);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return ind;
  }

  async function handleUserMessage(text) {
    if (!text || !text.trim()) return;
    appendMessage(text.trim(), 'user');
    const typing = appendTypingIndicator();
    const lang = getLang();

    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text.trim(), lang })
      });
      typing.remove();

      if (response.ok) {
        const data = await response.json();
        appendMessage(data.answer, 'assistant', {
          sources: data.sources || [],
          follow_ups: data.follow_ups || []
        });
      } else {
        appendMessage(t('chat.err_offline', 'Սերվերի սխալ։ Կրկին փորձեք։'), 'assistant');
      }
    } catch (e) {
      typing.remove();
      appendMessage(
        t('chat.err_offline', 'Կապի սխալ։ Խնդրում ենք միացնել RAG սերվերը (start_backend.bat)։'),
        'assistant'
      );
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initChat);
  } else {
    initChat();
  }
})();
