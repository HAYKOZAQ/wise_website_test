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
      const apiBase = typeof window.WISEF_getApiBase === 'function' ? window.WISEF_getApiBase() : '';
      const blogUrl = apiBase ? apiBase.replace(/\/$/, '') + '/assets/data/blog-posts.json' : '../assets/data/blog-posts.json';
      const res = await fetch(blogUrl);
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

  function showToast(message) {
    let t = document.getElementById('blogToast');
    if (!t) {
      t = document.createElement('div');
      t.id = 'blogToast';
      t.className = 'blog-toast';
      t.setAttribute('role', 'status');
      t.setAttribute('aria-live', 'polite');
      document.body.appendChild(t);
    }
    t.textContent = message;
    t.classList.add('blog-toast--show');
    clearTimeout(t._timer);
    t._timer = setTimeout(() => t.classList.remove('blog-toast--show'), 3200);
  }

  function slugify(s) {
    // Include ASCII letters/digits + Armenian (U+0531–U+0587) + apostrophe & dot
    return String(s || '')
      .replace(/[^\w\u0531-\u0587\s.-]+/g, '')
      .replace(/[\s_]+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^[-.]+|[-.]+$/g, '')
      .slice(0, 80) || 'article';
  }

  function todayStamp() {
    const d = new Date();
    const p = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
  }

  function buildDownloadHtml({ title, date, content, sourceUrl }) {
    const safeTitle = String(title || 'Article').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const safeDate = String(date || '').replace(/</g, '&lt;');
    const safeSource = String(sourceUrl || '').replace(/"/g, '&quot;');
    return `<!DOCTYPE html>
<html lang="hy">
<head>
<meta charset="UTF-8">
<title>${safeTitle}</title>
<style>
  body { font-family: 'Inter','Noto Sans Armenian',system-ui,sans-serif; max-width: 760px; margin: 40px auto; padding: 0 20px; line-height: 1.7; color: #183960; }
  h1 { font-size: 1.875rem; margin-bottom: 0.5rem; line-height: 1.25; }
  .meta { color: #5a6a7e; font-size: 0.9rem; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid #e2e8f0; }
  .source { display: inline-block; margin-top: 1.5rem; padding: 8px 14px; background: #183960; color: #fff; border-radius: 6px; text-decoration: none; font-size: 0.875rem; }
  figure { margin: 1rem 0; }
  img { max-width: 100%; height: auto; }
  blockquote { border-left: 3px solid #183960; padding: 0.5rem 1rem; margin: 1rem 0; color: #5a6a7e; }
</style>
</head>
<body>
<h1>${safeTitle}</h1>
<p class="meta">${safeDate ? safeDate + ' • ' : ''}Source: <a href="${safeSource}">${safeSource}</a></p>
${content || '<p>Content not available offline.</p>'}
<p><a class="source" href="${safeSource}" target="_blank" rel="noopener">View original →</a></p>
</body>
</html>`;
  }

  function triggerDownload(filename, html) {
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  closeBtn.addEventListener('click', closeModal);
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeModal();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && overlay.classList.contains('open')) closeModal();
  });

  document.querySelectorAll('.blog-read-more').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();

      const url = btn.getAttribute('data-url');
      const card = btn.closest('.blog-card, .project-card');
      const articleTitle = card?.querySelector('h3')?.textContent ?? 'Article';

      // Always allow the original URL to be opened from the modal/view-original link
      const openOriginal = () => window.open(url, '_blank', 'noopener');

      let entry = null;
      try {
        const db = await loadBlogData();
        if (db) entry = db[url] || null;
      } catch (_) { /* fall through */ }

      if (!entry) {
        showToast('Բեռնվում է բնօրինակը…');
        openOriginal();
        return;
      }

      // 1) Build a clean, self-contained HTML file and trigger download
      const slug = slugify(articleTitle);
      const filename = `wisef-${todayStamp()}-${slug}.html`;
      const fileHtml = buildDownloadHtml({
        title: articleTitle,
        date: entry.date || '',
        content: entry.content || '',
        sourceUrl: url,
      });
      try {
        triggerDownload(filename, fileHtml);
        showToast('Ֆայլը բեռնվեց՝ ' + filename);
      } catch (err) {
        console.error('[Blog] download failed', err);
        showToast('Բեռնումը ձախողվեց — բացվում է բնօրինակը');
        openOriginal();
        return;
      }

      // 2) Open modal as a confirmation preview
      title.textContent = articleTitle;
      body.innerHTML =
        `<div class="blog-download-banner">
           <span class="blog-download-banner__icon">⬇</span>
           <div class="blog-download-banner__text">
             <strong>Ֆայլը բեռնվեց՝</strong>
             <code>${filename}</code>
             <a class="blog-download-banner__view" href="${url}" target="_blank" rel="noopener">Բացել բնօրինակ էջը →</a>
           </div>
         </div>
         <div class="blog-download-body">${entry.content || '<p>Content not available.</p>'}</div>`;
      overlay.classList.add('open');
      document.body.style.overflow = 'hidden';

      body.querySelectorAll('a').forEach(a => {
        a.setAttribute('target', '_blank');
        a.setAttribute('rel', 'noopener');
      });
    });
  });
}

function initServiceDetailModal() {
  const overlay = document.getElementById('serviceModal');
  if (!overlay) return;

  const titleEl = document.getElementById('serviceModalTitle');
  const bodyEl = document.getElementById('serviceModalBody');
  const closeBtn = document.getElementById('serviceModalClose');

  let detailData = null;
  let currentKey = null;

  async function loadDetailData() {
    if (detailData) return detailData;
    try {
      const apiBase = typeof window.WISEF_getApiBase === 'function' ? window.WISEF_getApiBase() : '';
      const dataUrl = apiBase ? apiBase.replace(/\/$/, '') + '/assets/data/services-detail.json' : '../assets/data/services-detail.json';
      const res = await fetch(dataUrl);
      if (!res.ok) throw new Error('Failed to load service details');
      detailData = await res.json();
      return detailData;
    } catch (err) {
      console.error('[ServiceDetailModal] Error loading details:', err);
      return null;
    }
  }

  function getLang() {
    return (window.wisefI18n && window.wisefI18n.getLang()) ||
      localStorage.getItem('wisef_lang') ||
      (document.documentElement.getAttribute('lang') === 'en' ? 'en' : 'hy');
  }

  function t(key, fallback) {
    if (!window.wisefI18n || !window.wisefI18n.t) return fallback;
    return window.wisefI18n.t(key) || fallback;
  }

  function render() {
    if (!currentKey || !detailData) return;
    const entry = detailData[currentKey];
    if (!entry) return;
    const lang = getLang();
    const loc = entry[lang] || entry.en || entry.hy;
    const icon = entry.icon || '';

    titleEl.textContent = loc.title || '';
    bodyEl.innerHTML = `
      <div class="service-detail-modal__icon">${icon}</div>
      <h2 class="service-detail-modal__title">${loc.title || ''}</h2>
      <div class="service-detail-modal__content">${loc.content || ''}</div>
      <div class="service-detail-modal__footer">
        <a href="contact.html?service=${currentKey}" class="glass-btn">${t('svc.contact_about', 'Contact us about this project')}</a>
      </div>
    `;
  }

  function openModal(key) {
    currentKey = key;
    render();
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeModal() {
    overlay.classList.remove('open');
    document.body.style.overflow = '';
    currentKey = null;
  }

  closeBtn.addEventListener('click', closeModal);
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeModal();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && overlay.classList.contains('open')) closeModal();
  });

  document.querySelectorAll('.service-detail-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();

      const href = btn.getAttribute('href') || '';
      const match = href.match(/[?&]service=(p\d+)/);
      const key = match ? match[1] : null;
      if (!key) return;

      const card = btn.closest('.project-card');
      const icon = card ? (card.querySelector('div[style*="font-size"], .project-card__icon')?.textContent?.trim() || '') : '';

      const data = await loadDetailData();
      if (!data || !data[key]) {
        window.location.href = href;
        return;
      }

      if (data[key] && icon && !data[key].icon) {
        data[key].icon = icon;
      }

      openModal(key);
    });
  });

  document.addEventListener('wisefLangChanged', () => {
    if (overlay.classList.contains('open')) render();
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

      if (featured) {
        const featuredTitle = featured.querySelector('h3')?.textContent.toLowerCase() || '';
        const featuredText = featured.querySelector('p')?.textContent.toLowerCase() || '';
        const featuredMatch = featuredTitle.includes(query) || featuredText.includes(query);
        featured.style.display = featuredMatch ? 'block' : 'none';
      }

      cards.forEach(card => {
        const title = card.querySelector('.blog-card__title').textContent.toLowerCase();
        const excerpt = card.querySelector('.blog-card__excerpt').textContent.toLowerCase();
        const match = title.includes(query) || excerpt.includes(query);

        card.classList.toggle('pagination-hidden', !match);
      });
    }
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

document.addEventListener('DOMContentLoaded', () => {
  forcePageHeaderContrast();
  initMobileMenu();
  initHeaderScroll();
  initScrollReveal();
  initCounters();
  initSmoothScroll();
  initPageTransitions();
  initBlogModal();
  initServiceDetailModal();
  initBlogPagination();
  initContactForm();
  initBlogSearch();
});
