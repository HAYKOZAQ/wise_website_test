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

      try {
        const res = await fetch(url, { mode: 'cors' });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const html = await res.text();

        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');

        const article = doc.querySelector('article') ||
                        doc.querySelector('.entry-content') ||
                        doc.querySelector('.post-content') ||
                        doc.querySelector('main');

        if (article) {
          article.querySelectorAll('script, style, iframe, .sharedaddy, .jp-relatedposts').forEach(el => el.remove());
          body.innerHTML = article.innerHTML;
        } else {
          const contentDiv = doc.body;
          contentDiv.querySelectorAll('script, style, iframe, nav, header, footer').forEach(el => el.remove());
          body.innerHTML = contentDiv.innerHTML.substring(0, 10000);
        }

        body.querySelectorAll('a').forEach(a => {
          a.setAttribute('target', '_blank');
          a.setAttribute('rel', 'noopener');
        });
      } catch (err) {
        body.innerHTML = '<div class="modal__error">' +
          'Չհաջողվեց բեռնել հոդվածը։ <a href="' + url + '" target="_blank" rel="noopener">Բացել օրիգինալ էջում</a>' +
          '</div>';
      }
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

  const isArmenian = document.documentElement.lang === 'hy';
  const statusDiv = document.getElementById('formStatus');

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

  const texts = {
    sending: isArmenian ? 'Ուղարկվում է...' : 'Sending...',
    success: isArmenian ? '✅ Ձեր հաղորդագրությունը հաջողությամբ ուղարկվեց:' : '✅ Your message has been successfully sent!',
    error: isArmenian ? '❌ Տեղի է ունեցել սխալ: Խնդրում ենք փորձել կրկին:' : '❌ An error occurred. Please try again.'
  };

  form.addEventListener('submit', function(e) {
    e.preventDefault();
    console.log('[ContactForm] Form submitted');

    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = texts.sending;
    submitBtn.disabled = true;

    if (statusDiv) statusDiv.style.display = 'none';

    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    console.log('[ContactForm] Sending data:', JSON.stringify(data));

    fetch("https://formsubmit.co/ajax/hayko16140@gmail.com", {
      method: "POST",
      headers: { 
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(data)
    })
    .then(response => {
      console.log('[ContactForm] Response status:', response.status);
      return response.json();
    })
    .then(result => {
      console.log('[ContactForm] Result:', JSON.stringify(result));
      submitBtn.textContent = originalText;
      submitBtn.disabled = false;

      if (result.success === "true" || result.success === true) {
        showStatus(texts.success, true);
        form.reset();
      } else {
        showStatus(texts.success, true);
        form.reset();
      }
    })
    .catch(error => {
      console.error('[ContactForm] Error:', error);
      submitBtn.textContent = originalText;
      submitBtn.disabled = false;
      showStatus(texts.error, false);
    });
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
});
