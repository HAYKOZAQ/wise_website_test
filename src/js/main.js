function initMobileMenu() {
  const toggle = document.querySelector('.mobile-toggle');
  const nav = document.querySelector('.nav');
  if (!toggle || !nav) return;

  toggle.addEventListener('click', () => {
    toggle.classList.toggle('active');
    nav.classList.toggle('open');
  });

  document.querySelectorAll('.nav__link').forEach(link => {
    link.addEventListener('click', () => {
      toggle.classList.remove('active');
      nav.classList.remove('open');
    });
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
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  });

  document.querySelectorAll('.fade-in, .fade-in-left, .fade-in-right, .fade-in-scale').forEach(el => {
    observer.observe(el);
  });
}

function initCounters() {
  const counters = document.querySelectorAll('[data-counter]');
  if (!counters.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const target = parseInt(el.getAttribute('data-counter'));
        const duration = 2000;
        const startTime = performance.now();

        function update(currentTime) {
          const elapsed = currentTime - startTime;
          const progress = Math.min(elapsed / duration, 1);
          const eased = 1 - Math.pow(1 - progress, 3);
          const current = Math.floor(eased * target);
          el.textContent = current + (el.getAttribute('data-suffix') || '');
          if (progress < 1) {
            requestAnimationFrame(update);
          } else {
            el.textContent = target + (el.getAttribute('data-suffix') || '');
          }
        }

        requestAnimationFrame(update);
        observer.unobserve(el);
      }
    });
  }, { threshold: 0.3 });

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
        error: '❌ An error occurred. Please try again.'
      };
    }
    if (lang === 'ru') {
      return {
        sending: 'Отправка...',
        success: '✅ Ваше сообщение успешно отправлено!',
        error: '❌ Произошла ошибка. Пожалуйста, попробуйте ещё раз.'
      };
    }
    return {
      sending: 'Ուղարկվում է...',
      success: '✅ Ձեր հաղորդագրությունը հաջողությամբ ուղարկվեց:',
      error: '❌ Տեղի է ունեցել սխալ: Խնդրում ենք փորձել կրկին:'
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

    if (!primaryUrl) {
      submitBtn.textContent = originalText;
      submitBtn.disabled = false;
      showStatus(texts.error, false);
      return;
    }

    const tryPrimary = fallbackUrl
      ? postContact(primaryUrl).catch((err) => {
          console.warn('[ContactForm] API contact failed, trying configured fallback:', err);
          return postContact(fallbackUrl);
        })
      : postContact(primaryUrl);

    tryPrimary
      .then((result) => {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
        showStatus(texts.success, true);
        form.reset();
      })
      .catch((error) => {
        console.warn('[ContactForm] submission failed:', error.message || error);
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
        showStatus(texts.error, false);
      });
  });
}/** Ensure page-header stays navy + white (beats theme/cascade glitches). */
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

document.addEventListener('DOMContentLoaded', () => {
  forcePageHeaderContrast();
  initMobileMenu();
  initHeaderScroll();
  initScrollReveal();
  initCounters();
  initSmoothScroll();
  initPageTransitions();
  initContactForm();
});
