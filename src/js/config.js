/* ====================================================
   WISE site config (safe to commit — NO secrets here)
   ====================================================
   Put GEMINI_API_KEY only on Render/Railway (server env).
   Never put the key in this file.
*/
window.WISEF_CONFIG = {
  /**
   * Optional: public API URL if backend is on a DIFFERENT domain.
   * Example: 'https://wisef-rag-api.onrender.com'
   *
   * Leave empty when the website is served FROM the same Render
   * service as the API (recommended) — chat will use this domain.
   */
  productionApiBase: '',

  /** Local backend while developing on your PC */
  localApiBase: 'http://127.0.0.1:8000',

  /**
   * Optional secondary contact URL (only if /api/contact is unreachable).
   * Leave empty — primary path is POST /api/contact on the backend.
   */
  contactFallbackUrl: ''
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
  if (prod) return prod;

  // Same host as the page (Docker/Render serves site + API together)
  if (typeof location !== 'undefined' && location.origin) {
    return location.origin.replace(/\/$/, '');
  }
  return '';
};
