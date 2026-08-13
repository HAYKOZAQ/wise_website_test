/* ====================================================
   WISE Foundation — Animation runtime
   3D tilt · floating orbs · hero parallax · marquee ·
   theme transition trigger
   ==================================================== */

(function () {
  'use strict';

  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── 3D tilt on cards ── */
  function initTilt() {
    if (reduceMotion || !window.matchMedia('(hover: hover)').matches) return;
    document.querySelectorAll('.wise-tilt').forEach(function (card) {
      var raf = null;
      card.addEventListener('mousemove', function (e) {
        if (raf) return;
        raf = requestAnimationFrame(function () {
          raf = null;
          var r = card.getBoundingClientRect();
          var px = (e.clientX - r.left) / r.width - 0.5;
          var py = (e.clientY - r.top) / r.height - 0.5;
          card.style.transform =
            'perspective(900px) rotateX(' + (-py * 6).toFixed(2) + 'deg) rotateY(' + (px * 6).toFixed(2) + 'deg)';
        });
      });
      card.addEventListener('mouseleave', function () {
        card.style.transform = '';
      });
    });
  }

  /* ── Floating orbs in heroes (injected, mouse-parallax) ── */
  function injectOrbs() {
    document.querySelectorAll('.wise-home-hero, .wise-page-hero').forEach(function (hero) {
      if (hero.querySelector('.wise-orb')) return;
      var configs = [
        { cls: 'wise-orb--yellow', top: '14%', left: '8%', size: 260, dur: 15 },
        { cls: 'wise-orb--navy', top: '8%', left: '68%', size: 320, dur: 19 },
        { cls: 'wise-orb--blue', top: '64%', left: '22%', size: 230, dur: 17 }
      ];
      configs.forEach(function (cfg, i) {
        var orb = document.createElement('div');
        orb.className = 'wise-orb ' + cfg.cls;
        orb.style.top = cfg.top;
        orb.style.left = cfg.left;
        orb.style.width = cfg.size + 'px';
        orb.style.height = cfg.size + 'px';
        orb.style.animationDelay = (i * 1.6) + 's';
        orb.style.animationDuration = cfg.dur + 's';
        orb.setAttribute('aria-hidden', 'true');
        hero.appendChild(orb);
      });
    });
  }

  function initOrbParallax() {
    if (reduceMotion) return;
    var heroes = Array.prototype.slice.call(document.querySelectorAll('.wise-home-hero, .wise-page-hero'));
    if (!heroes.length) return;

    document.addEventListener('mousemove', function (e) {
      heroes.forEach(function (hero) {
        var orbs = hero.querySelectorAll('.wise-orb');
        if (!orbs.length) return;
        var r = hero.getBoundingClientRect();
        var dx = (e.clientX - r.left - r.width / 2) / (r.width / 2);
        var dy = (e.clientY - r.top - r.height / 2) / (r.height / 2);
        orbs.forEach(function (orb, i) {
          var depth = (i + 1) * 10;
          orb.style.translate = (dx * depth) + 'px ' + (dy * depth) + 'px';
        });
      });
    });
  }

  /* ── Marquee: duplicate track for seamless loop ── */
  function initMarquee() {
    document.querySelectorAll('.wise-marquee__track').forEach(function (track) {
      if (track._marqueeReady) return;
      track._marqueeReady = true;
      track.innerHTML += track.innerHTML;
    });
  }

  /* ── Theme transition trigger ── */
  function initThemeTransition() {
    document.querySelectorAll('.theme-toggle').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var html = document.documentElement;
        html.classList.add('theme-anim');
        clearTimeout(html._themeTimer);
        html._themeTimer = setTimeout(function () {
          html.classList.remove('theme-anim');
        }, 600);
      });
    });
  }

  /* ── Scroll reveal: also handle elements already in view on load ── */
  function initReveal() {
    var els = document.querySelectorAll('.fade-in, .fade-in-left, .fade-in-right, .fade-in-scale');
    if (!els.length) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    els.forEach(function (el) { io.observe(el); });
  }

  /* ── Job card details (accordion) ── */
  function jobToggleLabel(key) {
    if (window.wisefI18n && window.wisefI18n.t) {
      var v = window.wisefI18n.t(key);
      if (v && v !== key) return v;
    }
    return key === 'careers.hide' ? 'Թաքցնել' : 'Մանրամասներ';
  }

  function initJobToggles() {
    document.querySelectorAll('[data-job]').forEach(function (card) {
      var toggle = card.querySelector('[data-job-toggle]');
      var details = card.querySelector('[data-job-details]');
      if (!toggle || !details) return;
      toggle.addEventListener('click', function () {
        var isOpen = details.getAttribute('data-open') === 'true';
        details.setAttribute('data-open', isOpen ? 'false' : 'true');
        toggle.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
        toggle.textContent = jobToggleLabel(isOpen ? 'careers.details' : 'careers.hide');
      });
    });
  }

  function init() {
    initTilt();
    injectOrbs();
    initOrbParallax();
    initMarquee();
    initThemeTransition();
    initReveal();
    initJobToggles();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
