/* ====================================================
   WISE Foundation — Floating AI Chatbot Widget (Gemma 2 RAG)
   ─ Clean, responsive, glassmorphic design
   ─ Multi-language support matching active site language
   ─ Automatically translates dynamically on event 'wisefLangChanged'
   ==================================================== */

(function () {
  'use strict';

  // API Backend config
  const API_BASE = "http://127.0.0.1:8000";
  let backendStatus = {
    online: false,
    vector: false
  };

  // State
  let chatOpen = false;
  let chatInitialized = false;

  // DOM Elements references
  let widgetContainer, chatToggleBtn, chatWindow, chatMessages, chatInput, chatSendBtn, statusDot, statusText;

  // Initialize chatbot
  function initChat() {
    if (chatInitialized) return;
    
    // Inject CSS styles dynamically to support custom animations and layouts for the widget
    injectStyles();

    // Create widget elements
    createWidgetDOM();

    // Setup Event Listeners
    setupListeners();

    // Check backend status immediately
    checkBackendStatus();
    setInterval(checkBackendStatus, 15000); // Check status every 15s

    chatInitialized = true;
  }

  function injectStyles() {
    // We already put styles in components.css, but we will inject a few key styles or variables to be safe.
    // However, the main rules will be in components.css.
  }

  function createWidgetDOM() {
    widgetContainer = document.createElement('div');
    widgetContainer.className = 'wise-chat-widget';
    widgetContainer.setAttribute('aria-label', 'WISE AI Assistant');

    // Floating Button
    chatToggleBtn = document.createElement('button');
    chatToggleBtn.className = 'wise-chat-toggle glass';
    chatToggleBtn.type = 'button';
    chatToggleBtn.setAttribute('aria-expanded', 'false');
    chatToggleBtn.setAttribute('aria-label', 'Open chat');
    chatToggleBtn.innerHTML = `
      <svg class="wise-chat-toggle__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
      </svg>
      <svg class="wise-chat-toggle__close" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:none;">
        <line x1="18" y1="6" x2="6" y2="18"></line>
        <line x1="6" y1="6" x2="18" y2="18"></line>
      </svg>
    `;

    // Chat Window
    chatWindow = document.createElement('div');
    chatWindow.className = 'wise-chat-window glass';
    chatWindow.style.display = 'none';

    // Header
    const header = document.createElement('div');
    header.className = 'wise-chat-header';
    header.innerHTML = `
      <div class="wise-chat-header__info">
        <h3 class="wise-chat-header__title" data-i18n="chat.title">WISE AI Օգնական (Gemma 2)</h3>
        <div class="wise-chat-header__status">
          <span class="wise-chat-header__dot"></span>
          <span class="wise-chat-header__status-text" data-i18n="chat.status_offline">Անցանց</span>
        </div>
      </div>
      <button class="wise-chat-header__close" type="button" aria-label="Close chat">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    `;

    // Messages Container
    chatMessages = document.createElement('div');
    chatMessages.className = 'wise-chat-messages';

    // Suggestions Grid
    const suggestions = document.createElement('div');
    suggestions.className = 'wise-chat-suggestions';
    suggestions.innerHTML = `
      <button type="button" class="wise-chat-suggest-btn" data-i18n="chat.suggest1">Մինչև 2 տարեկան երեխայի նպաստ</button>
      <button type="button" class="wise-chat-suggest-btn" data-i18n="chat.suggest2">Ծննդյան միանվագ նպաստ</button>
      <button type="button" class="wise-chat-suggest-btn" data-i18n="chat.suggest3">Ընտանեկան նպաստներ</button>
      <button type="button" class="wise-chat-suggest-btn" data-i18n="chat.suggest4">Տարիքային կենսաթոշակ</button>
    `;

    // Footer
    const footer = document.createElement('form');
    footer.className = 'wise-chat-footer';
    footer.innerHTML = `
      <input type="text" class="wise-chat-input" placeholder="Հարցրեք MLSA սոցիալական ծրագրերի մասին..." data-i18n="chat.placeholder" required autocomplete="off">
      <button type="submit" class="wise-chat-send" aria-label="Send message">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="22" y1="2" x2="11" y2="13"></line>
          <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
        </svg>
      </button>
    `;

    chatInput = footer.querySelector('.wise-chat-input');
    chatSendBtn = footer.querySelector('.wise-chat-send');
    statusDot = header.querySelector('.wise-chat-header__dot');
    statusText = header.querySelector('.wise-chat-header__status-text');

    // Assemble Widget
    chatWindow.appendChild(header);
    chatWindow.appendChild(chatMessages);
    chatWindow.appendChild(suggestions);
    chatWindow.appendChild(footer);

    widgetContainer.appendChild(chatToggleBtn);
    widgetContainer.appendChild(chatWindow);
    document.body.appendChild(widgetContainer);

    // Initial greeting
    addGreeting();
  }

  function addGreeting() {
    const welcomeMsg = window.wisefI18n ? window.wisefI18n.t('chat.welcome') : "Ողջույն! Ես WISE AI օգնականն եմ: Կարող եմ տրամադրել տեղեկատվություն ՀՀ սոցիալական ապահովության և նպաստների ծրագրերի մասին:";
    appendMessage(welcomeMsg, 'assistant');
  }

  function setupListeners() {
    // Open/Close
    chatToggleBtn.addEventListener('click', toggleChat);
    chatWindow.querySelector('.wise-chat-header__close').addEventListener('click', toggleChat);

    // Form submit
    chatWindow.querySelector('.wise-chat-footer').addEventListener('submit', (e) => {
      e.preventDefault();
      const text = chatInput.value.strip ? chatInput.value.strip() : chatInput.value.trim();
      if (!text) return;
      chatInput.value = "";
      handleUserMessage(text);
    });

    // Suggestions submit
    chatWindow.querySelectorAll('.wise-chat-suggest-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const text = btn.textContent;
        handleUserMessage(text);
      });
    });

    // Listen for language changes to update existing UI labels dynamically
    document.addEventListener('wisefLangChanged', () => {
      translateUI();
    });
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
      chatInput.focus();
    } else {
      chatWindow.style.display = 'none';
      chatWindow.classList.remove('wise-chat-window--open');
      iconChat.style.display = 'block';
      iconClose.style.display = 'none';
    }
  }

  function translateUI() {
    if (!window.wisefI18n) return;
    
    // Title
    const titleEl = chatWindow.querySelector('.wise-chat-header__title');
    if (titleEl) titleEl.textContent = window.wisefI18n.t('chat.title');

    // Input placeholder
    if (chatInput) chatInput.placeholder = window.wisefI18n.t('chat.placeholder');

    // Suggestions
    chatWindow.querySelectorAll('.wise-chat-suggest-btn').forEach((btn, index) => {
      btn.textContent = window.wisefI18n.t(`chat.suggest${index + 1}`);
    });

    // Update online status text according to current lang
    updateStatusText();
  }

  async function checkBackendStatus() {
    try {
      const r = await fetch(`${API_BASE}/api/status`, { signal: AbortSignal.timeout(3000) });
      if (r.ok) {
        const data = await r.json();
        backendStatus.online = true;
        backendStatus.vector = data.vector_search_active;
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
    } else {
      statusDot.className = 'wise-chat-header__dot wise-chat-header__dot--offline';
      statusText.textContent = window.wisefI18n ? window.wisefI18n.t('chat.status_offline') : 'Անցանց';
    }
  }

  function updateStatusText() {
    if (!statusText || !backendStatus.online) return;
    if (backendStatus.vector) {
      statusText.textContent = window.wisefI18n ? window.wisefI18n.t('chat.status_active') : 'Ակտիվ (Vector)';
    } else {
      statusText.textContent = window.wisefI18n ? window.wisefI18n.t('chat.status_keyword') : 'Ակտիվ (Keyword)';
    }
  }

  function appendMessage(text, sender) {
    const msg = document.createElement('div');
    msg.className = `wise-chat-msg wise-chat-msg--${sender}`;
    msg.innerHTML = `
      <div class="wise-chat-msg__bubble">
        <p class="wise-chat-msg__text">${escapeHTML(text).replace(/\n/g, '<br>')}</p>
      </div>
    `;
    chatMessages.appendChild(msg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function appendTypingIndicator() {
    const ind = document.createElement('div');
    ind.className = 'wise-chat-msg wise-chat-msg--assistant wise-chat-typing-indicator';
    ind.innerHTML = `
      <div class="wise-chat-msg__bubble">
        <div class="wise-chat-dots">
          <span></span><span></span><span></span>
        </div>
      </div>
    `;
    chatMessages.appendChild(ind);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return ind;
  }

  function escapeHTML(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  async function handleUserMessage(text) {
    // 1. Add user message
    appendMessage(text, 'user');

    // 2. Add loading state
    const typingIndicator = appendTypingIndicator();

    // 3. Prepare payload
    const lang = window.wisefI18n ? window.wisefI18n.getLang() : "hy";
    
    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: text, lang: lang })
      });
      
      // Remove loading indicator
      typingIndicator.remove();

      if (response.ok) {
        const data = await response.json();
        appendMessage(data.answer, 'assistant');
        
        // Show sources if available
        if (data.sources && data.sources.length > 0) {
          const uniqueSources = [...new Set(data.sources)];
          const sourceText = lang === 'en' 
            ? `Sources: ${uniqueSources.join(', ')}` 
            : `Աղբյուրներ՝ ${uniqueSources.join(', ')}`;
          appendSourceBadge(sourceText);
        }
      } else {
        const errText = window.wisefI18n ? window.wisefI18n.t('chat.err_offline') : "Սերվերի սխալ: Խնդրում ենք կրկին փորձել:";
        appendMessage(errText, 'assistant');
      }
    } catch (e) {
      typingIndicator.remove();
      const errText = window.wisefI18n ? window.wisefI18n.t('chat.err_offline') : "Կապի սխալ: Խնդրում ենք համոզվել, որ RAG սերվերը միացված է:";
      appendMessage(errText, 'assistant');
    }
  }

  function appendSourceBadge(text) {
    const badge = document.createElement('div');
    badge.className = 'wise-chat-sources';
    badge.innerHTML = `<span class="wise-chat-sources__tag">${escapeHTML(text)}</span>`;
    chatMessages.appendChild(badge);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // Load chat once DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initChat);
  } else {
    initChat();
  }

})();
