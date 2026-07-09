/* ====================================================
   WISE site config (safe to commit — NO secrets here)
   ====================================================
   GitHub Pages is STATIC only. The AI backend must be
   deployed separately (Render / Railway / Fly.io).

   1) Deploy backend (see DEPLOY.md)
   2) Paste the public HTTPS URL below (no trailing slash)
   3) Commit & push — do NOT put GEMINI_API_KEY in this file
*/
window.WISEF_CONFIG = {
  /**
   * Public FastAPI base URL after cloud deploy.
   * Example: 'https://wisef-rag.onrender.com'
   * Leave empty until backend is deployed.
   */
  productionApiBase: '',

  /**
   * Local backend while developing on your PC.
   */
  localApiBase: 'http://127.0.0.1:8000'
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

  // Fallback: same origin only if you later reverse-proxy /api
  return '';
};
