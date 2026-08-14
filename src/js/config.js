/* ====================================================
   WISE site config (safe to commit — NO secrets here)
   ==================================================== */
window.WISEF = window.WISEF || {};

window.WISEF_CONFIG = {
  productionApiBase: '__WISEF_API_BASE__',
  localApiBase: 'http://127.0.0.1:8000',
  contactFallbackUrl: '',
  contactToEmail: 'info@wisef.am'
};

window.WISEF.config = window.WISEF_CONFIG;

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
  if (prod === '__WISEF_API_BASE__') prod = '';
  if (prod) return prod;

  if (typeof location !== 'undefined' && location.origin) {
    return location.origin.replace(/\/$/, '');
  }
  return '';
};

window.WISEF.getApiBase = window.WISEF_getApiBase;
