/* ====================================================
   WISE site config (safe to commit — NO secrets here)
   ====================================================
   Put GEMINI_API_KEY only on the API host (server environment).
   Never put the key in this file.
*/
window.WISEF_CONFIG = {
  /**
   * Optional: public API URL if backend is on a DIFFERENT domain.
   * Example: 'https://your-space.hf.space'
   *
   * Cloudflare Pages builds replace the marker from WISEF_API_BASE. Leave
   * the build variable empty when the website and API share one origin.
   */
  productionApiBase: '__WISEF_API_BASE__',

  /** Local backend while developing on your PC */
  localApiBase: 'http://127.0.0.1:8000',

  /**
   * Optional secondary contact URL (only if /api/contact is unreachable).
   * Leave empty — primary path is POST /api/contact on the backend.
   */
  contactFallbackUrl: '',

  /**
   * Recipient of contact form messages when the mailto fallback is used
   * (opens the visitor's own email app pre-filled to this address).
   */
  contactToEmail: 'info@wisef.am'
};

/** Resolve which API the chat should call */
window.WISEF_getApiBase = function () {
  var cfg = window.WISEF_CONFIG || {};
  var host = (typeof location !== 'undefined' && location.hostname) || '';
  var isLocal =
    host === 'localhost' ||
    host === '127.0.0.1' ||
    host === '' ||
    host === '[::1]';

  if (isLocal) {
    return (cfg.localApiBase || 'http://127.0.0.1:8000').replace(/\/$/, '');
  }

  var prod = (cfg.productionApiBase || '').trim().replace(/\/$/, '');
  // Keep local Eleventy/dev output safe before the optional build injection.
  if (prod === '__WISEF_API_BASE__') prod = '';
  if (prod) return prod;

  // Same host as the page (Docker/Render serves site + API together)
  if (typeof location !== 'undefined' && location.origin) {
    return location.origin.replace(/\/$/, '');
  }
  return '';
};
