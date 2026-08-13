/* ====================================================
   WISE Foundation — Blog: modal + auto-playing slider
   ─ Click a post card → modal opens with article
   ─ Image slider: auto-play, arrows, dots, swipe, keyboard
   ==================================================== */

(function () {
  'use strict';

  function initSlider(root) {
    var track = root.querySelector('.wise-slider__track');
    var slides = root.querySelectorAll('.wise-slider__slide');
    var dotsWrap = root.querySelector('[data-slide-dots]');
    if (!track || !slides.length) return;

    var index = 0;
    var timer = null;
    var interval = 4000;

    function go(i) {
      index = (i + slides.length) % slides.length;
      track.style.transform = 'translateX(-' + index * 100 + '%)';
      if (dotsWrap) {
        var dots = dotsWrap.querySelectorAll('.wise-slider__dot');
        dots.forEach(function (d, k) {
          d.classList.toggle('wise-slider__dot--active', k === index);
        });
      }
    }

    function next() { go(index + 1); }
    function prev() { go(index - 1); }

    function restart() {
      if (timer) clearInterval(timer);
      timer = setInterval(next, interval);
    }

    function stop() {
      if (timer) { clearInterval(timer); timer = null; }
    }

    if (dotsWrap) {
      dotsWrap.innerHTML = '';
      for (var k = 0; k < slides.length; k++) {
        (function (i) {
          var dot = document.createElement('button');
          dot.type = 'button';
          dot.className = 'wise-slider__dot';
          dot.setAttribute('aria-label', 'Slide ' + (i + 1));
          dot.addEventListener('click', function () { go(i); restart(); });
          dotsWrap.appendChild(dot);
        })(k);
      }
    }

    var prevBtn = root.querySelector('[data-slide-prev]');
    var nextBtn = root.querySelector('[data-slide-next]');
    if (prevBtn) prevBtn.addEventListener('click', function () { prev(); restart(); });
    if (nextBtn) nextBtn.addEventListener('click', function () { next(); restart(); });

    // Swipe (touch)
    var startX = null, startY = null;
    root.addEventListener('touchstart', function (e) {
      startX = e.touches[0].clientX;
      startY = e.touches[0].clientY;
    }, { passive: true });
    root.addEventListener('touchend', function (e) {
      if (startX === null) return;
      var dx = e.changedTouches[0].clientX - startX;
      var dy = e.changedTouches[0].clientY - startY;
      startX = null; startY = null;
      if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) {
        if (dx < 0) { next(); } else { prev(); }
        restart();
      }
    }, { passive: true });

    // Keyboard arrows
    root.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') { next(); restart(); }
      if (e.key === 'ArrowLeft') { prev(); restart(); }
    });

    // Pause on hover, resume after
    root.addEventListener('mouseenter', stop);
    root.addEventListener('mouseleave', restart);

    go(0);
    restart();

    root._wiseStop = stop;
    root._wiseRestart = restart;
  }

  function openNews() {
    var modal = document.getElementById('wiseNewsModal');
    if (!modal) return;
    modal.hidden = false;
    document.body.classList.add('wise-modal-open');
    var slider = modal.querySelector('.wise-slider');
    if (slider) {
      if (!slider._wiseSliderInit) {
        slider._wiseSliderInit = true;
        initSlider(slider);
      } else if (typeof slider._wiseRestart === 'function') {
        slider._wiseRestart();
      }
    }
  }

  function closeNews() {
    var modal = document.getElementById('wiseNewsModal');
    if (!modal) return;
    modal.hidden = true;
    document.body.classList.remove('wise-modal-open');
    var slider = modal.querySelector('.wise-slider');
    if (slider && typeof slider._wiseStop === 'function') {
      slider._wiseStop();
    }
  }

  function init() {
    document.querySelectorAll('[data-open-news]').forEach(function (card) {
      function open(e) {
        if (e.target.closest && e.target.closest('.wise-btn')) return; // button handles itself
        e.preventDefault();
        openNews(card);
      }
      card.addEventListener('click', open);
      card.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openNews(card); }
      });
    });

    // Card's "Read more" button triggers the same modal
    document.querySelectorAll('[data-open-news] .wise-btn').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        openNews(btn.closest('[data-open-news]'));
      });
    });

    document.querySelectorAll('[data-close-news]').forEach(function (el) {
      el.addEventListener('click', closeNews);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeNews();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
