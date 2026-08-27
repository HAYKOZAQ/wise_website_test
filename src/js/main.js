function initMobileMenu() {
  const toggle = document.querySelector('.mobile-toggle');
  const nav = document.querySelector('.nav');
  if (!toggle || !nav) return;

  function closeMenu() {
    toggle.classList.remove('active');
    nav.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
  }

  toggle.setAttribute('aria-expanded', 'false');
  toggle.setAttribute('aria-label', 'Toggle Navigation Menu');

  toggle.addEventListener('click', () => {
    const isOpen = nav.classList.toggle('open');
    toggle.classList.toggle('active', isOpen);
    toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  });

  document.querySelectorAll('.nav__link').forEach(link => {
    link.addEventListener('click', closeMenu);
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && nav.classList.contains('open')) {
      closeMenu();
    }
  });
}

function initHeaderScroll() {
  const header = document.querySelector('.header');
  if (!header) return;

  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
      header.classList.add('scrolled');
    } else {
      header.classList.remove('scrolled');
    }
  }, { passive: true });
}

function initScrollReveal() {
  const revealElement = (el) => {
    el.classList.add('visible');
  };

  if (!('IntersectionObserver' in window)) {
    document.querySelectorAll('.fade-in, .fade-in-left, .fade-in-right, .fade-in-scale').forEach(revealElement);
    return;
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.05,
    rootMargin: '50px 0px 50px 0px'
  });

  document.querySelectorAll('.fade-in, .fade-in-left, .fade-in-right, .fade-in-scale').forEach(el => {
    const rect = el.getBoundingClientRect();
    if (rect.top < window.innerHeight && rect.bottom > 0) {
      revealElement(el);
    } else {
      observer.observe(el);
    }
  });
}

function initCounters() {
  const counters = document.querySelectorAll('[data-counter]');
  if (!counters.length) return;

  function fmt(n) {
    return n >= 10000 ? n.toLocaleString('en-US') : String(n);
  }

  function animate(el) {
    const target = parseInt(el.getAttribute('data-counter'), 10) || 0;
    const suffix = el.getAttribute('data-suffix') || '';
    const duration = 2400;
    const delay = parseInt(el.getAttribute('data-delay') || '0', 10);
    const startTime = performance.now() + delay;
    const stat = el.closest('.wise-stat');
    if (stat) stat.classList.add('wise-stat--counting');

    function tick(currentTime) {
      const elapsed = Math.max(currentTime - startTime, 0);
      const progress = Math.min(elapsed / duration, 1);
      // easeOutExpo: fast start, smooth settle
      const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
      const current = Math.round(eased * target);
      el.textContent = fmt(current) + suffix;
      if (progress < 1) {
        requestAnimationFrame(tick);
      } else {
        el.textContent = fmt(target) + suffix;
        el.classList.add('wise-stat__num--done');
        el.closest('.wise-stat') && el.closest('.wise-stat').classList.add('wise-stat--counted');
      }
    }

    requestAnimationFrame(tick);
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        animate(el);
        observer.unobserve(el);
      }
    });
  }, { threshold: 0.4, rootMargin: '0px 0px -40px 0px' });

  counters.forEach(el => observer.observe(el));
}

function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      const target = document.querySelector(anchor.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}

function initPageTransitions() {
  const isTransitioning = () => document.body.classList.contains('page-exit');

  document.addEventListener('click', (e) => {
    if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey || e.button !== 0) return;
    const link = e.target.closest('a');
    if (!link) return;
    if (isTransitioning()) { e.preventDefault(); return; }

    const href = link.getAttribute('href');
    if (!href || href.startsWith('#') || href.startsWith('http') || href.startsWith('mailto:') || href.startsWith('tel:')) return;

    const sameOrigin = href.startsWith('/') || !href.includes('://');
    if (!sameOrigin) return;

    e.preventDefault();
    document.body.classList.add('page-exit');
    setTimeout(() => {
      window.location.href = href;
    }, 300);
  });
}function initContactForm() {
  const form = document.getElementById('contactForm');
  if (!form) return;

  const statusDiv = document.getElementById('formStatus');

  // Pre-fill subject if provided in URL parameter
  const urlParams = new URLSearchParams(window.location.search);
      const serviceKey = urlParams.get('service');
  if (serviceKey) {
    const subjectInput = form.querySelector('input[name="subject"]');
    if (subjectInput) {
      subjectInput.value = _serviceName(serviceKey);
    }
  }

  function _serviceName(key) {
    if (!window.wisefI18n || !window.wisefI18n.t) return '';
    const match = String(key || '').match(/^(s|p)(\d+)$/);
    if (!match) return '';
    const [, kind, num] = match;
    const i18nKey = kind === 's'
      ? 'svc.' + key + '_full_title'
      : 'svc.p' + num + '_title';
    return window.wisefI18n.t(i18nKey) || '';
  }

  function showStatus(message, isSuccess) {
    if (statusDiv) {
      statusDiv.style.display = 'block';
      statusDiv.textContent = message;
      statusDiv.style.background = isSuccess 
        ? 'rgba(16, 185, 129, 0.15)' 
        : 'rgba(239, 68, 68, 0.15)';
      statusDiv.style.color = isSuccess ? '#10b981' : '#ef4444';
      statusDiv.style.border = isSuccess 
        ? '1px solid rgba(16, 185, 129, 0.3)' 
        : '1px solid rgba(239, 68, 68, 0.3)';
    }
  }

  function getTexts() {
    const lang = document.documentElement.lang;
    if (lang === 'en') {
      return {
        sending: 'Sending...',
        success: '✅ Your message has been successfully sent!',
        error: '❌ An error occurred. Please try again.',
        mailto: '✉️ Your email app opened — just press Send to deliver the message.'
      };
    }
    if (lang === 'ru') {
      return {
        sending: 'Отправка...',
        success: '✅ Ваше сообщение успешно отправлено!',
        error: '❌ Произошла ошибка. Пожалуйста, попробуйте ещё раз.',
        mailto: '✉️ Открылось ваше почтовое приложение — нажмите «Отправить», чтобы доставить письмо.'
      };
    }
    return {
      sending: 'Ուղարկվում է...',
      success: '✅ Ձեր հաղորդագրությունը հաջողությամբ ուղարկվեց:',
      error: '❌ Տեղի է ունեցել սխալ: Խնդրում ենք փորձել կրկին:',
      mailto: '✉️ Բացվել է Ձեր էլ. փոստի ծրագիրը — սեղմեք «Ուղարկել»՝ նամակն առաքելու համար։'
    };
  }

  form.addEventListener('submit', function(e) {
    e.preventDefault();

    const texts = getTexts();
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = texts.sending;
    submitBtn.disabled = true;

    if (statusDiv) statusDiv.style.display = 'none';

    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    const apiBase = typeof window.WISEF_getApiBase === 'function' ? window.WISEF_getApiBase() : '';
    const primaryUrl = apiBase ? (apiBase.replace(/\/$/, '') + '/api/contact') : '';
    // Optional secondary path only if site owner configures window.WISEF_CONTACT_FALLBACK_URL
    const fallbackUrl = (window.WISEF_CONFIG && window.WISEF_CONFIG.contactFallbackUrl) || '';

    function postContact(url) {
      return fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(data)
      }).then(async (response) => {
        let result = {};
        try {
          result = await response.json();
        } catch (_) {}
        if (!response.ok) {
          throw new Error((result && result.detail) || ('HTTP ' + response.status));
        }
        return result;
      });
    }

    // Delivery channels in order: backend API first, then the visitor's own
    // email app (mailto) as a zero-config fallback — the letter is pre-filled
    // to info@wisef.am and sent from the visitor's account.
    const channels = [];
    if (primaryUrl) channels.push(() => postContact(primaryUrl));
    if (fallbackUrl && primaryUrl) channels.push(() => postContact(fallbackUrl));
    channels.push(openMailto);

    function openMailto() {
      const to = (window.WISEF_CONFIG && window.WISEF_CONFIG.contactToEmail || 'info@wisef.am').trim();
      const subject = encodeURIComponent(data.subject || 'Website contact');
      const body = encodeURIComponent(
        (data.name ? 'Name: ' + data.name + '\n' : '') +
        (data.email ? 'Email: ' + data.email + '\n\n' : '') +
        (data.message || '')
      );
      const href = 'mailto:' + to + '?subject=' + subject + '&body=' + body;
      window.location.href = href;
      return Promise.resolve({ via: 'mailto' });
    }

    (async function deliver() {
      let lastErr = null;
      let sentVia = null;
      for (const send of channels) {
        try {
          const res = await send();
          sentVia = (res && res.via) || 'auto';
          return { via: sentVia };
        } catch (err) {
          lastErr = err;
          console.warn('[ContactForm] delivery failed, trying next channel:', err.message || err);
        }
      }
      throw lastErr;
    })()
      .then((result) => {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
        const texts = getTexts();
        if (result && result.via === 'mailto') {
          showStatus(texts.mailto, true);
        } else {
          showStatus(texts.success, true);
        }
        form.reset();
      })
      .catch((error) => {
        console.warn('[ContactForm] submission failed:', error.message || error);
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
        showStatus(getTexts().error, false);
      });
  });
}

/** Ensure page-header stays navy + white (beats theme/cascade glitches). */
function forcePageHeaderContrast() {
  document.querySelectorAll('.page-header').forEach((el) => {
    el.style.setProperty('background', '#0f2740', 'important');
    el.style.setProperty('color', '#ffffff', 'important');
    el.classList.remove('fade-in');
    el.classList.add('visible');
    el.querySelectorAll('.page-header__title, h1').forEach((title) => {
      title.style.setProperty('color', '#ffffff', 'important');
      title.style.setProperty('-webkit-text-fill-color', '#ffffff', 'important');
    });
  });
}

function initReadingProgress() {
  const bar = document.createElement('div');
  bar.className = 'wise-reading-progress';
  bar.id = 'wiseReadingProgress';
  bar.setAttribute('aria-hidden', 'true');
  document.body.appendChild(bar);

  function update() {
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    const progress = scrollHeight > 0 ? Math.min(Math.max((scrollTop / scrollHeight) * 100, 0), 100) : 0;
    bar.style.width = progress + '%';
  }

  window.addEventListener('scroll', update, { passive: true });
  update();
}

function initScrollToTop() {
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'wise-scroll-top';
  btn.id = 'wiseScrollTop';
  btn.setAttribute('aria-label', 'Scroll to top');
  btn.setAttribute('title', 'Scroll to top');
  btn.innerHTML =
    '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    '<path d="M18 15l-6-6-6 6"/>' +
    '</svg>';
  document.body.appendChild(btn);

  let visible = false;
  function check() {
    const shouldShow = (window.scrollY || document.documentElement.scrollTop) > 350;
    if (shouldShow !== visible) {
      visible = shouldShow;
      btn.classList.toggle('wise-scroll-top--visible', visible);
    }
  }

  btn.addEventListener('click', (e) => {
    e.preventDefault();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  window.addEventListener('scroll', check, { passive: true });
  check();
}

function initFaqSearch() {
  const searchInput = document.getElementById('faqSearchInput');
  const clearBtn = document.getElementById('faqSearchClear');
  const faqList = document.getElementById('faqList');
  const noResults = document.getElementById('faqNoResults');
  if (!searchInput || !faqList) return;

  const items = faqList.querySelectorAll('.wise-faq-item');

  function filter() {
    const q = (searchInput.value || '').trim().toLowerCase();
    let visibleCount = 0;

    if (clearBtn) {
      clearBtn.style.display = q.length > 0 ? 'grid' : 'none';
    }

    items.forEach((item) => {
      const summaryText = (item.querySelector('summary')?.textContent || '').toLowerCase();
      const answerText = (item.querySelector('.wise-faq-item__answer')?.textContent || '').toLowerCase();
      const matches = !q || summaryText.includes(q) || answerText.includes(q);

      if (matches) {
        item.style.display = '';
        if (q.length > 1) {
          item.setAttribute('open', '');
        }
        visibleCount++;
      } else {
        item.style.display = 'none';
        item.removeAttribute('open');
      }
    });

    if (noResults) {
      noResults.style.display = visibleCount === 0 ? 'block' : 'none';
    }
  }

  searchInput.addEventListener('input', filter);

  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      searchInput.value = '';
      filter();
      searchInput.focus();
    });
  }
}

function initClipboardCopy() {
  document.querySelectorAll('.wise-contact-detail__row a').forEach((link) => {
    link.addEventListener('click', () => {
      const href = link.getAttribute('href') || '';
      if (href.startsWith('mailto:') || href.startsWith('tel:')) {
        const rawText = link.textContent.trim();
        if (navigator.clipboard && rawText) {
          navigator.clipboard.writeText(rawText).catch(() => {});
        }
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  forcePageHeaderContrast();
  initMobileMenu();
  initHeaderScroll();
  initScrollReveal();
  initCounters();
  initSmoothScroll();
  initPageTransitions();
  initContactForm();
  initReadingProgress();
  initScrollToTop();
  initFaqSearch();
  initClipboardCopy();
});
