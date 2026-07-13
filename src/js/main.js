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
    const link = e.target.closest('a');
    if (!link) return;
    if (isTransitioning()) { e.preventDefault(); return; }

    const href = link.getAttribute('href');
    if (!href || href.startsWith('#') || href.startsWith('http') || href.startsWith('mailto:') || href.startsWith('tel:')) return;
    if (link.classList.contains('blog-read-more')) return;

    const sameOrigin = href.startsWith('/') || !href.includes('://');
    if (!sameOrigin) return;

    e.preventDefault();
    document.body.classList.add('page-exit');
    setTimeout(() => {
      window.location.href = href;
    }, 300);
  });
}

function initBlogModal() {
  const overlay = document.getElementById('blogModal');
  if (!overlay) return;
  const body = document.getElementById('modalBody');
  const title = document.getElementById('modalTitle');
  const closeBtn = document.getElementById('modalClose');

  let blogData = null;

  async function loadBlogData() {
    if (blogData) return blogData;
    try {
      const res = await fetch('../assets/data/blog-posts.json');
      if (!res.ok) throw new Error('Failed to load local database');
      blogData = await res.json();
      return blogData;
    } catch (err) {
      console.error('[BlogModal] Error loading local blog data:', err);
      return null;
    }
  }

  function closeModal() {
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  }

  closeBtn.addEventListener('click', closeModal);
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeModal();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
  });

  document.querySelectorAll('.blog-read-more').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();

      const url = btn.getAttribute('data-url');
      const card = btn.closest('.blog-card, .project-card');
      const articleTitle = card ? card.querySelector('h3').textContent : 'Article';

      title.textContent = articleTitle;
      body.innerHTML = '<div class="modal__loader">Բեռնվում է...</div>';
      overlay.classList.add('open');
      document.body.style.overflow = 'hidden';

      const db = await loadBlogData();
      if (db && db[url]) {
        const post = db[url];
        body.innerHTML = post.content;
      } else {
        body.innerHTML = '<div class="modal__error">' +
          'Չհաջողվեց բեռնել հոդվածը։ <a href="' + url + '" target="_blank" rel="noopener">Բացել օրիգինալ էջում</a>' +
          '</div>';
      }

      body.querySelectorAll('a').forEach(a => {
        a.setAttribute('target', '_blank');
        a.setAttribute('rel', 'noopener');
      });
    });
  });
}

function initBlogPagination() {
  const pagination = document.querySelector('.pagination');
  if (!pagination) return;

  const cards = document.querySelectorAll('.blog-card[data-page]');
  if (!cards.length) return;

  function showPage(pageNum) {
    cards.forEach(card => {
      const p = card.getAttribute('data-page');
      card.classList.toggle('pagination-hidden', p !== pageNum);
    });

    pagination.querySelectorAll('.pagination__btn').forEach(btn => {
      const isActive = btn.getAttribute('data-page') === pageNum;
      btn.classList.toggle('pagination__btn--active', isActive);
      if (isActive) {
        btn.style.background = 'var(--color-accent)';
        btn.style.color = 'white';
      } else {
        btn.style.background = '';
        btn.style.color = '';
      }
    });
  }

  pagination.addEventListener('click', (e) => {
    const btn = e.target.closest('.pagination__btn');
    if (!btn) return;
    const page = btn.getAttribute('data-page');
    if (page) showPage(page);
  });

  showPage('1');
}

function initContactForm() {
  const form = document.getElementById('contactForm');
  if (!form) return;

  const statusDiv = document.getElementById('formStatus');

  // Pre-fill subject if provided in URL parameter
  const urlParams = new URLSearchParams(window.location.search);
  const serviceKey = urlParams.get('service');
  if (serviceKey) {
    const subjectInput = form.querySelector('input[name="subject"]');
    if (subjectInput) {
      const serviceNames = {
        s1: { hy: 'ՏՀ նախագծում և սպասարկում', en: 'IS Design & Maintenance' },
        s2: { hy: 'Տեղեկատվական համակարգերի բովանդակային սպասարկում', en: 'IS Content Maintenance' },
        s3: { hy: 'Տվյալների մշակում և վերլուծում', en: 'Data Processing & Analysis' },
        s4: { hy: 'Կրթական ծրագրերի նախագծում, իրականացում', en: 'Educational Programs Design & Implementation' },
        s5: { hy: 'Կիբեռանվտանգություն և ցանցային ապահովում', en: 'Cybersecurity & Network Security' },
        s6: { hy: 'Տեխնիկական սպասարկում', en: 'Technical Support' },
        p1: { hy: 'Ընտանիքի անապահովության գնահատման համակարգ', en: 'Family Vulnerability Assessment System' },
        p2: { hy: 'Սոցիալական արագ արձագանքման ՏՀ', en: 'Social Rapid Response IS' },
        p3: { hy: 'Տվյալների փոխանակման ՏՀ', en: 'Data Exchange IS' },
        p4: { hy: '«Գործ» զբաղվածության ՏՀ', en: '"Gorts" Employment IS' },
        p5: { hy: 'Պրոթեզաօրթոպեդիկ պարագաների ՏՀ', en: 'Prosthetic-Orthopedic Devices IS' },
        p6: { hy: '«Մանուկ» երեխաների հաշվառման ՏՀ', en: '"Manuk" Child Registration IS' }
      };
      
      const service = serviceNames[serviceKey];
      if (service) {
        const isArmenian = document.documentElement.lang !== 'en';
        subjectInput.value = isArmenian ? service.hy : service.en;
      }
    }
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
    const isArmenian = document.documentElement.lang !== 'en';
    return {
      sending: isArmenian ? 'Ուղարկվում է...' : 'Sending...',
      success: isArmenian ? '✅ Ձեր հաղորդագրությունը հաջողությամբ ուղարկվեց:' : '✅ Your message has been successfully sent!',
      error: isArmenian ? '❌ Տեղի է ունեցել սխալ: Խնդրում ենք փորձել կրկին:' : '❌ An error occurred. Please try again.'
    };
  }

  form.addEventListener('submit', function(e) {
    e.preventDefault();
    console.log('[ContactForm] Form submitted');

    const texts = getTexts();
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = texts.sending;
    submitBtn.disabled = true;

    if (statusDiv) statusDiv.style.display = 'none';

    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    console.log('[ContactForm] Sending data:', JSON.stringify(data));

    function getContactApiBase() {
      if (typeof window.WISEF_getApiBase === 'function') {
        return window.WISEF_getApiBase();
      }
      var host = (location && location.hostname) || '';
      if (host === 'localhost' || host === '127.0.0.1') {
        return 'http://127.0.0.1:8000';
      }
      return (typeof location !== 'undefined' && location.origin) || '';
    }

    const apiBase = getContactApiBase();
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
        console.log('[ContactForm] Response status:', response.status, url);
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
        console.log('[ContactForm] Result:', JSON.stringify(result));
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
        showStatus(texts.success, true);
        form.reset();
      })
      .catch((error) => {
        console.error('[ContactForm] Error:', error);
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
        showStatus(texts.error, false);
      });
  });
}

function initBlogSearch() {
  const searchInput = document.getElementById('blogSearch');
  if (!searchInput) return;

  const cards = document.querySelectorAll('.blog-card');
  const featured = document.getElementById('featuredPost');
  const pagination = document.querySelector('.pagination');

  searchInput.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase().trim();

    if (query === '') {
      if (pagination) pagination.style.display = 'flex';
      if (featured) featured.style.display = 'block';
      const activeBtn = pagination ? pagination.querySelector('.pagination__btn--active') : null;
      const activePage = activeBtn ? activeBtn.getAttribute('data-page') : '1';
      cards.forEach(card => {
        const p = card.getAttribute('data-page');
        card.classList.toggle('pagination-hidden', p !== activePage);
      });
    } else {
      if (pagination) pagination.style.display = 'none';
      if (featured) featured.style.display = 'none';

      cards.forEach(card => {
        const title = card.querySelector('.blog-card__title').textContent.toLowerCase();
        const excerpt = card.querySelector('.blog-card__excerpt').textContent.toLowerCase();
        const match = title.includes(query) || excerpt.includes(query);

        card.classList.toggle('pagination-hidden', !match);
      });
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initMobileMenu();
  initHeaderScroll();
  initScrollReveal();
  initCounters();
  initSmoothScroll();
  initPageTransitions();
  initBlogModal();
  initBlogPagination();
  initContactForm();
  initBlogSearch();
});
