/* ====================================================
   WISE — Social Help Assistant
   Resizable panel · New chat · Persistent history
   ==================================================== */

(function () {
  'use strict';

  var STORAGE_KEY = 'wisef_chat_v1';
  var SIZE_KEY = 'wisef_chat_size_v1';
  var API_BASE = (typeof window.WISEF_getApiBase === 'function') ? window.WISEF_getApiBase() : '';

  var backendOnline = false;
  var chatOpen = false;
  var chatInitialized = false;
  var pollTimer = null;
  var POLL_INTERVAL_OPEN = 12000;
  var POLL_INTERVAL_CLOSED = 60000;
  var hasConversation = false;
  var conversationHistory = [];
  /** @type {{id:string,title:string,history:Array,messages:Array,updated:number}|null} */
  var activeSession = null;

  var root, fab, panel, messagesEl, inputEl, sendBtn, statusEl, homeEl, topicsEl, newChatBtn;

  var TOPICS = [
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
      var v = window.wisefI18n.t(key);
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

  function uid() {
    return 'c' + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
  }

  function loadStore() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return { activeId: null, sessions: [] };
      var data = JSON.parse(raw);
      if (!data || !Array.isArray(data.sessions)) return { activeId: null, sessions: [] };
      return data;
    } catch (e) {
      return { activeId: null, sessions: [] };
    }
  }

  function saveStore(store) {
    try {
      // Cap storage: keep last 12 sessions, trim long answers
      store.sessions = (store.sessions || [])
        .sort(function (a, b) { return (b.updated || 0) - (a.updated || 0); })
        .slice(0, 12)
        .map(function (s) {
          return {
            id: s.id,
            title: (s.title || 'Chat').slice(0, 80),
            updated: s.updated || Date.now(),
            history: (s.history || []).slice(-16).map(function (h) {
              return { role: h.role, content: String(h.content || '').slice(0, 2000) };
            }),
            messages: (s.messages || []).slice(-40).map(function (m) {
              return {
                role: m.role,
                content: String(m.content || '').slice(0, 8000),
                sources: (m.sources || []).slice(0, 4),
                follow_ups: (m.follow_ups || []).slice(0, 3),
                fidelity: m.fidelity || null
              };
            })
          };
        });
      localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
    } catch (e) {
      console.warn('[wise-help] history save failed', e);
    }
  }

  function persistActive() {
    if (!activeSession) return;
    activeSession.history = conversationHistory.slice();
    activeSession.updated = Date.now();
    var store = loadStore();
    var idx = store.sessions.findIndex(function (s) { return s.id === activeSession.id; });
    if (idx >= 0) store.sessions[idx] = activeSession;
    else store.sessions.unshift(activeSession);
    store.activeId = activeSession.id;
    saveStore(store);
  }

  function ensureSession() {
    if (activeSession) return activeSession;
    var store = loadStore();
    if (store.activeId) {
      var found = store.sessions.find(function (s) { return s.id === store.activeId; });
      if (found) {
        activeSession = found;
        conversationHistory = (found.history || []).slice();
        return activeSession;
      }
    }
    activeSession = {
      id: uid(),
      title: lang() === 'en' ? 'New chat' : 'Նոր զրույց',
      history: [],
      messages: [],
      updated: Date.now()
    };
    conversationHistory = [];
    store.sessions.unshift(activeSession);
    store.activeId = activeSession.id;
    saveStore(store);
    return activeSession;
  }

  function startNewChat() {
    // Save current first
    if (activeSession && (conversationHistory.length || (activeSession.messages || []).length)) {
      persistActive();
    }
    activeSession = {
      id: uid(),
      title: lang() === 'en' ? 'New chat' : 'Նոր զրույց',
      history: [],
      messages: [],
      updated: Date.now()
    };
    conversationHistory = [];
    hasConversation = false;
    if (messagesEl) messagesEl.innerHTML = '';
    if (homeEl) homeEl.hidden = false;
    if (messagesEl) messagesEl.hidden = true;
    if (root) root.classList.remove('wise-help--chatting');
    var store = loadStore();
    store.sessions.unshift(activeSession);
    store.activeId = activeSession.id;
    saveStore(store);
    if (inputEl) {
      inputEl.value = '';
      inputEl.focus();
    }
  }

  function restoreMessagesFromSession() {
    ensureSession();
    if (!activeSession.messages || !activeSession.messages.length) {
      hasConversation = false;
      if (homeEl) homeEl.hidden = false;
      if (messagesEl) {
        messagesEl.hidden = true;
        messagesEl.innerHTML = '';
      }
      return;
    }
    hasConversation = true;
    if (homeEl) homeEl.hidden = true;
    if (messagesEl) {
      messagesEl.hidden = false;
      messagesEl.innerHTML = '';
    }
    if (root) root.classList.add('wise-help--chatting');
    activeSession.messages.forEach(function (m) {
      if (m.role === 'user') {
        addUserBubble(m.content, true);
      } else {
        addBotBubble(formatAnswer(m.content), {
          sources: m.sources || [],
          follow_ups: m.follow_ups || [],
          fidelity: m.fidelity || null
        }, true);
      }
    });
    scrollMessagesBottom();
  }

  function recordMessage(role, content, extras) {
    ensureSession();
    if (!activeSession.messages) activeSession.messages = [];
    activeSession.messages.push({
      role: role,
      content: content,
      sources: extras && extras.sources ? extras.sources : [],
      follow_ups: extras && extras.follow_ups ? extras.follow_ups : [],
      fidelity: extras && extras.fidelity ? extras.fidelity : null
    });
    if (role === 'user' && (!activeSession.title || activeSession.title === 'New chat' || activeSession.title === 'Նոր զրույց')) {
      activeSession.title = String(content).slice(0, 48);
    }
    persistActive();
  }

  function applySavedSize() {
    if (!panel) return;
    try {
      var raw = localStorage.getItem(SIZE_KEY);
      if (!raw) return;
      var size = JSON.parse(raw);
      if (size && size.w) panel.style.width = Math.max(300, Math.min(size.w, window.innerWidth - 24)) + 'px';
      if (size && size.h) panel.style.height = Math.max(360, Math.min(size.h, window.innerHeight - 80)) + 'px';
    } catch (e) { /* ignore */ }
  }

  function saveSize() {
    if (!panel) return;
    try {
      var rect = panel.getBoundingClientRect();
      localStorage.setItem(SIZE_KEY, JSON.stringify({ w: Math.round(rect.width), h: Math.round(rect.height) }));
    } catch (e) { /* ignore */ }
  }

  function initResize() {
    if (!panel) return;
    var handle = panel.querySelector('[data-resize]');
    if (!handle) return;
    var startX, startY, startW, startH;
    function onMove(e) {
      var dx = startX - e.clientX; // drag from top-left of panel (NW)
      var dy = startY - e.clientY;
      var nw = Math.max(300, Math.min(window.innerWidth - 24, startW + dx));
      var nh = Math.max(360, Math.min(window.innerHeight - 80, startH + dy));
      panel.style.width = nw + 'px';
      panel.style.height = nh + 'px';
    }
    function onUp() {
      document.removeEventListener('pointermove', onMove);
      document.removeEventListener('pointerup', onUp);
      document.body.classList.remove('wise-help-resizing');
      saveSize();
    }
    handle.addEventListener('pointerdown', function (e) {
      e.preventDefault();
      var rect = panel.getBoundingClientRect();
      startX = e.clientX;
      startY = e.clientY;
      startW = rect.width;
      startH = rect.height;
      document.body.classList.add('wise-help-resizing');
      document.addEventListener('pointermove', onMove);
      document.addEventListener('pointerup', onUp);
    });
  }

  function init() {
    if (chatInitialized) return;
    buildUI();
    bindEvents();
    renderTopics();
    applySavedSize();
    initResize();
    ensureSession();
    restoreMessagesFromSession();
    schedulePoll(true);
    if (typeof document !== 'undefined') {
      document.addEventListener('visibilitychange', onVisibilityChange);
    }
    chatInitialized = true;
  }

  function schedulePoll(immediate) {
    if (pollTimer) {
      clearTimeout(pollTimer);
      pollTimer = null;
    }
    if (immediate) {
      pollStatus();
    }
    // Don't schedule another tick if the tab is hidden (saves bandwidth/battery).
    if (typeof document !== 'undefined' && document.hidden) return;
    var interval = chatOpen ? POLL_INTERVAL_OPEN : POLL_INTERVAL_CLOSED;
    pollTimer = setTimeout(function () {
      schedulePoll(true);
    }, interval);
  }

  function onVisibilityChange() {
    if (document.hidden) {
      if (pollTimer) { clearTimeout(pollTimer); pollTimer = null; }
    } else {
      // Tab became visible again: poll immediately, then resume schedule.
      schedulePoll(true);
    }
  }

  function buildUI() {
    root = document.createElement('div');
    root.className = 'wise-help';
    root.innerHTML =
      '<button type="button" class="wise-help__fab" aria-expanded="false" aria-controls="wise-help-panel">' +
      '<span class="wise-help__fab-icon" aria-hidden="true">' +
      '<svg class="wise-help__fab-svg wise-help__fab-svg--chat" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">' +
      '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>' +
      '<svg class="wise-help__fab-svg wise-help__fab-svg--close" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">' +
      '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>' +
      '</span>' +
      '<span class="wise-help__fab-label" data-i18n="chat.fab">Հարցրեք մեզ</span>' +
      '</button>' +
      '<div class="wise-help__panel" id="wise-help-panel" role="dialog" aria-modal="true" aria-labelledby="wise-help-title" hidden>' +
      '<div class="wise-help__resize" data-resize title="Resize" aria-label="Resize chat"></div>' +
      '<header class="wise-help__header">' +
      '<div class="wise-help__header-text">' +
      '<h2 class="wise-help__title" id="wise-help-title" data-i18n="chat.title">Սոցիալական օգնական</h2>' +
      '<p class="wise-help__status" data-status>' +
      '<span class="wise-help__status-dot"></span>' +
      '<span class="wise-help__status-text" data-i18n="chat.status_offline">Միացում…</span>' +
      '</p></div>' +
      '<div class="wise-help__header-actions">' +
      '<button type="button" class="wise-help__new" data-new-chat data-i18n-title="chat.new" title="New chat" aria-label="New chat">' +
      '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">' +
      '<path d="M12 5v14M5 12h14"/></svg>' +
      '<span class="wise-help__new-label" data-i18n="chat.new">Նոր</span>' +
      '</button>' +
      '<button type="button" class="wise-help__close" aria-label="Close">' +
      '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">' +
      '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>' +
      '</button></div></header>' +
      '<div class="wise-help__body">' +
      '<div class="wise-help__home" data-home>' +
      '<p class="wise-help__hello" data-i18n="chat.welcome_title">Բարև ձեզ</p>' +
      '<p class="wise-help__intro" data-i18n="chat.welcome">' +
      'Հարցրեք նպաստների, կենսաթոշակների և սոցիալական ծրագրերի մասին։ Պատասխանները հիմնված են պաշտոնական տեղեկատվության վրա։' +
      '</p>' +
      '<p class="wise-help__topics-label" data-i18n="chat.topics_label">Ընտրեք թեմա կամ գրեք հարց</p>' +
      '<div class="wise-help__topics" data-topics></div>' +
      '</div>' +
      '<div class="wise-help__messages" data-messages hidden></div>' +
      '</div>' +
      '<form class="wise-help__composer" data-composer>' +
      '<label class="wise-help__sr-only" for="wise-help-input" data-i18n="chat.placeholder">Գրեք հարցը</label>' +
      '<input id="wise-help-input" class="wise-help__input" type="text" autocomplete="off" enterkeyhint="send" ' +
      'placeholder="Օրինակ՝ տարիքային կենսաթոշակ" data-i18n="chat.placeholder" />' +
      '<button type="submit" class="wise-help__send" aria-label="Send">' +
      '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>' +
      '</button></form>' +
      '<p class="wise-help__foot" data-i18n="chat.disclaimer">Տեղեկատվական է · Պաշտոնական որոշման համար՝ 114</p>' +
      '</div>';

    document.body.appendChild(root);

    fab = root.querySelector('.wise-help__fab');
    panel = root.querySelector('.wise-help__panel');
    messagesEl = root.querySelector('[data-messages]');
    homeEl = root.querySelector('[data-home]');
    topicsEl = root.querySelector('[data-topics]');
    inputEl = root.querySelector('.wise-help__input');
    sendBtn = root.querySelector('.wise-help__send');
    statusEl = root.querySelector('[data-status]');
    newChatBtn = root.querySelector('[data-new-chat]');
  }

  function renderTopics() {
    if (!topicsEl) return;
    topicsEl.innerHTML = '';
    TOPICS.forEach(function (item) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'wise-help__topic';
      btn.innerHTML =
        '<span class="wise-help__topic-icon" aria-hidden="true">' + item.icon + '</span>' +
        '<span class="wise-help__topic-text">' + escapeHtml(topicLabel(item)) + '</span>';
      btn.addEventListener('click', function () { ask(topicLabel(item)); });
      topicsEl.appendChild(btn);
    });
  }

  function bindEvents() {
    fab.addEventListener('click', toggle);
    root.querySelector('.wise-help__close').addEventListener('click', close);
    if (newChatBtn) {
      newChatBtn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        startNewChat();
      });
    }

    root.querySelector('[data-composer]').addEventListener('submit', function (e) {
      e.preventDefault();
      var q = (inputEl.value || '').trim();
      if (!q) return;
      inputEl.value = '';
      ask(q);
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && chatOpen) close();
    });

    document.addEventListener('wisefLangChanged', function () {
      applyI18n();
      renderTopics();
      updateStatusUI();
    });

    window.addEventListener('beforeunload', function () {
      persistActive();
      saveSize();
    });
  }

  function applyI18n() {
    if (!window.wisefI18n) return;
    root.querySelectorAll('[data-i18n]').forEach(function (el) {
      var key = el.getAttribute('data-i18n');
      if (!key) return;
      if (el.matches('input, textarea')) {
        el.placeholder = t(key, el.placeholder);
      } else {
        el.textContent = t(key, el.textContent);
      }
    });
    if (newChatBtn) {
      newChatBtn.setAttribute('title', t('chat.new', lang() === 'en' ? 'New chat' : 'Նոր զրույց'));
      newChatBtn.setAttribute('aria-label', t('chat.new', lang() === 'en' ? 'New chat' : 'Նոր զրույց'));
    }
  }

  var animating = false;

  function toggle() {
    if (animating) return;
    if (chatOpen) close();
    else open();
  }

  function open() {
    if (chatOpen || animating) return;
    animating = true;
    chatOpen = true;
    schedulePoll(false);  // switch to faster polling while open
    panel.hidden = false;
    panel.classList.remove('wise-help__panel--closing');
    fab.setAttribute('aria-expanded', 'true');
    fab.classList.add('wise-help__fab--open');
    root.classList.add('wise-help--open');
    applyI18n();
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
    schedulePoll(false);  // switch to slower polling while closed
    persistActive();
    saveSize();
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
    setTimeout(finishClose, 380);
  }

  async function pollStatus() {
    if (!API_BASE) {
      backendOnline = false;
      updateStatusUI();
      return;
    }
    try {
      var signal = null;
      if (typeof AbortSignal !== 'undefined' && typeof AbortSignal.timeout === 'function') {
        signal = AbortSignal.timeout(5000);
      }
      var opts = signal ? { signal: signal } : {};
      var r = await fetch(API_BASE + '/api/status', opts);
      backendOnline = r.ok && (await r.json()).status === 'ready';
    } catch (e) {
      backendOnline = false;
    }
    updateStatusUI();
  }

  function updateStatusUI() {
    if (!statusEl) return;
    var text = statusEl.querySelector('.wise-help__status-text');
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

  function scrollMessagesBottom() {
    if (!messagesEl) return;
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function formatAnswer(text) {
    var html = escapeHtml(text || '');
    html = html.replace(/^###\s+(.+)$/gm, '<h4 class="wise-help__h">$1</h4>');
    html = html.replace(/^##\s+(.+)$/gm, '<h3 class="wise-help__h">$1</h3>');
    html = html.replace(/^#\s+(.+)$/gm, '<h3 class="wise-help__h">$1</h3>');
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    var lines = html.split('\n');
    var out = [];
    var inUl = false;
    var inOl = false;
    for (var i = 0; i < lines.length; i++) {
      var tr = lines[i].trim();
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

  function addUserBubble(text, skipRecord) {
    var el = document.createElement('div');
    el.className = 'wise-help__msg wise-help__msg--user';
    el.innerHTML = '<div class="wise-help__bubble">' + escapeHtml(text) + '</div>';
    messagesEl.appendChild(el);
    if (!skipRecord) recordMessage('user', text);
    scrollMessagesBottom();
  }

  function addBotBubble(htmlInner, extras, skipRecord) {
    var el = document.createElement('div');
    el.className = 'wise-help__msg wise-help__msg--bot';
    var body = '<div class="wise-help__bubble wise-help__bubble--bot">' + htmlInner + '</div>';

    if (extras && extras.sources && extras.sources.length) {
      var links = extras.sources.slice(0, 4).map(function (s) {
        var title = typeof s === 'string' ? s : (s.title || 'Source');
        var url = typeof s === 'object' ? s.url : null;
        var short = title.length > 42 ? title.slice(0, 40) + '…' : title;
        if (url) {
          return '<a class="wise-help__source" href="' + escapeHtml(url) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(short) + '</a>';
        }
        return '<span class="wise-help__source wise-help__source--plain">' + escapeHtml(short) + '</span>';
      }).join('');
      body += '<div class="wise-help__sources"><span class="wise-help__sources-label">' +
        escapeHtml(t('chat.sources_label', 'Աղբյուրներ')) + '</span>' + links + '</div>';
    }

    if (extras && extras.follow_ups && extras.follow_ups.length) {
      var chips = extras.follow_ups.slice(0, 3).map(function (q) {
        return '<button type="button" class="wise-help__chip" data-q="' + escapeHtml(q) + '">' + escapeHtml(q) + '</button>';
      }).join('');
      body += '<div class="wise-help__chips">' + chips + '</div>';
    }

    if (extras && extras.fidelity && typeof extras.fidelity.grounding_score === 'number') {
      var g = extras.fidelity.grounding_score;
      var risk = extras.fidelity.risk || '';
      var pct = Math.round(g * 100);
      var label = lang() === 'en'
        ? 'Answer grounded in sources: ' + pct + '% (' + risk + ' risk)'
        : 'Աղբյուրներին համապատասխանություն՝ ' + pct + '% (' + risk + ')';
      body += '<p class="wise-help__ground">' + escapeHtml(label) + '</p>';
    }

    el.innerHTML = body;
    el.querySelectorAll('.wise-help__chip').forEach(function (btn) {
      btn.addEventListener('click', function () {
        ask(btn.getAttribute('data-q') || btn.textContent);
      });
    });
    messagesEl.appendChild(el);
    if (!skipRecord) {
      // store plain text answer if we can extract from history later
      var plain = '';
      try {
        plain = el.querySelector('.wise-help__bubble--bot')
          ? el.querySelector('.wise-help__bubble--bot').innerText
          : '';
      } catch (e) { plain = ''; }
      recordMessage('assistant', plain || htmlInner, extras);
    }
    scrollMessagesBottom();
  }

  function addTyping() {
    var el = document.createElement('div');
    el.className = 'wise-help__msg wise-help__msg--bot wise-help__typing';
    el.innerHTML =
      '<div class="wise-help__bubble wise-help__bubble--bot">' +
      '<span class="wise-help__dots"><i></i><i></i><i></i></span>' +
      '<span class="wise-help__typing-text">' + escapeHtml(t('chat.thinking', 'Մտածում եմ…')) + '</span>' +
      '</div>';
    messagesEl.appendChild(el);
    scrollMessagesBottom();
    return el;
  }

  async function ask(text) {
    var q = (text || '').trim();
    if (!q) return;

    ensureSession();
    showConversation();
    addUserBubble(q);
    conversationHistory.push({ role: 'user', content: q });
    if (conversationHistory.length > 16) {
      conversationHistory = conversationHistory.slice(-16);
    }
    persistActive();

    var typing = addTyping();
    if (!API_BASE) {
      typing.remove();
      addBotBubble(
        '<p>' + escapeHtml(t('chat.err_no_api', 'AI backend is not configured.')) + '</p>'
      );
      return;
    }

    try {
      var historyPayload = conversationHistory.slice(0, -1).slice(-8);
      var res = await fetch(API_BASE + '/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q, lang: lang(), history: historyPayload })
      });
      typing.remove();

      if (!res.ok) {
        if (res.status === 429) {
          addBotBubble(
            '<p>' + escapeHtml(
              lang() === 'en'
                ? 'Too many questions in a short time. Please wait a minute and try again.'
                : 'Շատ հարցեր կարճ ժամանակում։ Սպասեք մեկ րոպե և կրկին փորձեք։'
            ) + '</p>'
          );
          return;
        }
        if (res.status === 500) {
          addBotBubble(
            '<p>' + escapeHtml(t('chat.err_offline', 'Հիմա չեմ կարող պատասխանել։')) + '</p>' +
            '<p style="font-size:0.85rem;margin-top:4px;opacity:0.7">' + escapeHtml(
              lang() === 'en'
                ? 'The AI service encountered an error. Our team has been notified.'
                : 'AI ծառայությունը սխալ է հայտնաբերել։ Մեր թիմը տեղեկացված է։'
            ) + '</p>'
          );
          return;
        }
        addBotBubble(
          '<p>' + escapeHtml(t('chat.err_offline', 'Հիմա չեմ կարող պատասխանել։')) + '</p>'
        );
        return;
      }

      var data = await res.json();
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
      persistActive();
    } catch (e) {
      typing.remove();
      addBotBubble(
        '<p>' + escapeHtml(t('chat.err_offline', 'Կապ չկա սերվերի հետ։')) + '</p>' +
        '<p><strong>114</strong> — ՄՍԾ թեժ գիծ</p>'
      );
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
