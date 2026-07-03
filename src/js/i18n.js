(function() {
  const langSwitch = document.querySelector('.nav__lang-btn');
  if (!langSwitch) return;

  const currentLang = document.documentElement.lang || 'hy';
  const path = window.location.pathname;

  const pageMap = {
    '/pages/index.html': { hy: '/pages/index.html', en: '/pages/en/index.html' },
    '/pages/about.html': { hy: '/pages/about.html', en: '/pages/en/about.html' },
    '/pages/services.html': { hy: '/pages/services.html', en: '/pages/en/services.html' },
    '/pages/partners.html': { hy: '/pages/partners.html', en: '/pages/en/partners.html' },
    '/pages/contact.html': { hy: '/pages/contact.html', en: '/pages/en/contact.html' },
    '/pages/blog.html': { hy: '/pages/blog.html', en: '/pages/en/blog.html' },
    '/pages/en/index.html': { hy: '/pages/index.html', en: '/pages/en/index.html' },
    '/pages/en/about.html': { hy: '/pages/about.html', en: '/pages/en/about.html' },
    '/pages/en/services.html': { hy: '/pages/services.html', en: '/pages/en/services.html' },
    '/pages/en/partners.html': { hy: '/pages/partners.html', en: '/pages/en/partners.html' },
    '/pages/en/contact.html': { hy: '/pages/contact.html', en: '/pages/en/contact.html' },
    '/pages/en/blog.html': { hy: '/pages/blog.html', en: '/pages/en/blog.html' },
  };

  langSwitch.addEventListener('click', function(e) {
    e.preventDefault();
    const cleanPath = path.replace(/\/$/, '') || '/pages/index.html';
    const target = currentLang === 'hy'
      ? (pageMap[cleanPath]?.en || '/pages/en/index.html')
      : (pageMap[cleanPath]?.hy || '/pages/index.html');
    window.location.href = target;
  });
})();
