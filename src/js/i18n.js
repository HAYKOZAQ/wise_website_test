/* ====================================================
   WISE Foundation — Language Switcher (i18n)
   Supports: Armenian (hy) ↔ English (en)
   ─ Language preference saved in localStorage
   ─ Elements with [data-i18n="key"] are auto-translated
   ─ Elements with [data-i18n-attr="attr"] translate an attribute
   ==================================================== */

(function () {
  'use strict';

  /* ══════════════════════════════════════════════════════
     TRANSLATIONS — actual Armenian Unicode + English
  ══════════════════════════════════════════════════════ */
  const T = {

    /* Navigation */
    'nav.home':       { hy: 'Գлхаворр',  en: 'Home' },
    'nav.about':      { hy: 'Մer masun', en: 'About' },
    'nav.services':   { hy: 'Ծarayajutyunner', en: 'Services' },
    'nav.partners':   { hy: 'Gortsunkerner', en: 'Partners' },
    'nav.contact':    { hy: 'Hetadards kap', en: 'Contact' },
    'nav.blog':       { hy: 'Blok', en: 'Blog' },

    /* Hero – Home */
    'home.badge':        { hy: '🌟 23 տarri texnologianeri olvortum', en: '🌟 23 years in information technology' },
    'home.hero_span':    { hy: 'թvajin luzumner', en: 'Digital Solutions' },
    'home.hero_p':       { hy: '«Բarekecotyun texekatvacan hamakargneri dzernarkutyun» himnedram — Hayastanum arajadar texnologiakan kentron ՝ 20+ tarva parovogh',
                           en: 'Welfare Information Systems Enterprise Foundation — Armenia\'s leading technology center with 20+ years of experience in government and private sector IT solutions' },
    'home.btn_services': { hy: 'Ditel tsarayutjunner', en: 'Our Services' },
    'home.btn_contact':  { hy: 'Kapnel mez het', en: 'Contact Us' },

    /* Why section */
    'why.label':     { hy: 'Мer uuzhutjunner', en: 'Our Approach' },
    'why.title':     { hy: 'Yerazek, steghdzhek, kisek mez het', en: 'Dream, Create, Share with Us' },
    'why.subtitle':  { hy: 'Миасин карузум енк tvajin апагха', en: 'Together we build the digital future' },
    'why.c1_title':  { hy: 'Yerazek mez het', en: 'Dream with Us' },
    'why.c1_text':   { hy: 'Yerazek mez het norarutyun yev tvajin apaghi masin', en: 'Dream with us about innovation and a digital future' },
    'why.c2_title':  { hy: 'Steghdzhek mez het', en: 'Create with Us' },
    'why.c2_text':   { hy: 'Steghdzhek mez het tvajin apaghi norarakan luzumner', en: 'Create innovative digital solutions with us' },
    'why.c3_title':  { hy: 'Kisek mez het', en: 'Share with Us' },
    'why.c3_text':   { hy: 'Kisek mez het Dzer yerazankner tvajin apaghi katarelaguorcman hamar', en: 'Share your dreams for improving the digital future' },

    /* Services preview */
    'svc.label':     { hy: 'Ծarayajutyunner', en: 'Services' },
    'svc.title':     { hy: 'Мer tsarayajutyunner', en: 'Our Services' },
    'svc.subtitle':  { hy: 'Texekatvacan hamakargneri, nor tsragreri ev tvjalneri naxagdsum ev spasarkarum', en: 'Design and maintenance of information systems, new programs, and databases' },
    'svc.s1_title':  { hy: 'TH naxagdsum ev spasarkarum', en: 'IS Design & Maintenance' },
    'svc.s1_text':   { hy: 'Texekatvacan hamakargneri, nor tsragreri ev tvjalneri naxagdsum ev spasarkarum', en: 'Full-cycle design and maintenance of information systems, software, and databases' },
    'svc.s2_title':  { hy: 'Tvjalneri mshakoum', en: 'Data Processing' },
    'svc.s2_text':   { hy: 'Texekatvacan hamakargneri bovandakajin spasarkarum, tvjalneri mshakoum ev verluzum', en: 'Content maintenance, data processing, and analysis of information systems' },
    'svc.s3_title':  { hy: 'Krthakar tsragrer', en: 'Educational Programs' },
    'svc.s3_text':   { hy: 'Krthakar tsragreri naxagdsum ev irakanacirum', en: 'Design and implementation of educational programs in IT' },
    'svc.s4_title':  { hy: 'Kiberjankavtangoutyun', en: 'Cybersecurity' },
    'svc.s4_text':   { hy: 'Kiberjankavtangoutyun ev cankajin apahovjum', en: 'Cybersecurity and network security solutions' },
    'svc.s5_title':  { hy: 'Texnikakan spasarkarum', en: 'Technical Support' },
    'svc.s5_text':   { hy: 'Hamakargnichner ev harakic texnikaji spasarkarum', en: 'Computer and related equipment maintenance (13,000+ units)' },
    'svc.s6_title':  { hy: 'Integraciajon luzumner', en: 'Integration Solutions' },
    'svc.s6_text':   { hy: 'Hamakargneri integracian ev tvjalneri pokhanaklutyun', en: 'System integration and data exchange solutions' },
    'svc.btn_all':   { hy: 'Bolor tsarayajutyunner', en: 'All Services' },

    /* Stats */
    'stats.label':   { hy: 'Мer nvachumnere', en: 'Our Achievements' },
    'stats.title':   { hy: '23 tarri texekatvacan texnologianeri olvortum', en: '23 Years in Information Technology' },
    'stats.s1':      { hy: 'Tarri texnologianeri olvortum', en: 'Years in IT' },
    'stats.s2':      { hy: 'Aktiv shaharraju', en: 'Active Beneficiaries' },
    'stats.s3':      { hy: 'Naxagdzvadz texekatvacan hamakargnner', en: 'IS Systems Designed' },
    'stats.s4':      { hy: 'Spasarkvadz sarakavoroumnner', en: 'Serviced Equipment' },

    /* About preview */
    'aboutprev.label': { hy: 'Мer masin', en: 'About Us' },
    'aboutprev.title': { hy: '«Barekecotyun texekatvacan hamakargneri dzernarkutyun» himnedram', en: 'Welfare Information Systems Enterprise Foundation' },
    'aboutprev.p1':    { hy: 'Menk himnadvvel enk 2001 tvakanum: 23 tarri arach, HH karavarutyun khordmamb steghdzvec HH azhatanki ev sociaakan hartseri naxararutyun.',
                         en: 'We were founded in 2001, by decree of the Government of the Republic of Armenia, under the Ministry of Labor and Social Affairs.' },
    'aboutprev.p2':    { hy: 'Hayastanum arajadar texnologiakan kentron e, vor irakanacirum e petakan ev masnavor olvortum texekatvacan ev herrahaghordakcutyunneri texnologianeri nerdrumen ev spasarkarum.',
                         en: 'Armenia\'s leading technology center implementing information and telecommunication infrastructure for public and private sectors.' },
    'aboutprev.btn':   { hy: 'Imanel avelin', en: 'Learn More' },

    /* Contact preview */
    'contactprev.label': { hy: 'Hetadards kap', en: 'Contact' },
    'contactprev.title': { hy: 'Steghdzenk miassin', en: 'Let\'s Build Together' },
    'contactprev.sub':   { hy: 'Patrasht enk lusel Dzer gaghaparner', en: 'We are ready to hear your ideas' },
    'contactprev.email': { hy: 'El. post', en: 'Email' },
    'contactprev.phone': { hy: 'Herakhoss', en: 'Phone' },
    'contactprev.btn':   { hy: 'Grel namak', en: 'Send Message' },

    /* Footer */
    'footer.brand':      { hy: '«Barekecotyun texekatvacan hamakargneri dzernarkutyun» himnedram', en: 'Welfare Information Systems Enterprise Foundation' },
    'footer.site':       { hy: 'Kayk', en: 'Site' },
    'footer.contact':    { hy: 'Kap', en: 'Contact' },
    'footer.follow':     { hy: 'Hetevek mez', en: 'Follow Us' },
    'footer.home':       { hy: 'Glkhavorr', en: 'Home' },
    'footer.about':      { hy: 'Мer masin', en: 'About' },
    'footer.services':   { hy: 'Tsarayajutyunner', en: 'Services' },
    'footer.partners':   { hy: 'Gortsunkerner', en: 'Partners' },
    'footer.blog':       { hy: 'Blok', en: 'Blog' },
    'footer.contact_us': { hy: 'Hetadards kap', en: 'Contact Us' },
    'footer.copyright':  { hy: '© 2026 Dzevagordvats «WISE» himnedramum', en: '© 2026 Designed by «WISE» foundation' },

    /* Blog page */
    'blog.pagetitle':  { hy: 'Blok', en: 'Blog' },
    'blog.breadcrumb': { hy: 'Glkhavorr / Blok', en: 'Home / Blog' },
    'blog.readmore':   { hy: 'Kartal avelin', en: 'Read More' },
    'blog.loading':    { hy: 'Bervum e...', en: 'Loading...' },
    'blog.close':      { hy: 'Kogel', en: 'Close' },
    'blog.open_orig':  { hy: 'Bac bnabanasnoren', en: 'Open Original Article' },

    /* About page */
    'about.pagetitle':  { hy: 'Մեր մասին', en: 'About' },
    'about.breadcrumb': { hy: 'Գլխավոր / Մեր մասին', en: 'Home / About' },
    'about.exp_label': { hy: '23 տարվա փորձ', en: '23 Years of Experience' },
    'about.exp_title': { hy: 'Մենք երազում ենք, ստեղծում ենք, կիսվում ենք', en: 'We dream, create, and share' },
    'about.exp_p1': { hy: '«Բարեկեցության տեղեկատվական համակարգերի ձեռնարկություն» հիմնադրամը Հայաստանում առաջատար տեխնոլոգիական կենտրոն է, որն իրականացնում է պետական և մասնավոր ոլորտի տեղեկատվական և հեռահաղորդակցության տեխնոլոգիաների ենթակառուցվածքների ներդրում և սպասարկում։', en: 'Welfare Information Systems Enterprise Foundation is a leading technological center in Armenia, carrying out implementation and maintenance of IT infrastructure for public and private sectors.' },
    'about.exp_p2': { hy: 'Մոտ 1,109,493 ակտիվ շահառու ստանում է ծառայություններ ՀՀ սոցիալական պաշտպանության ոլորտում մեր կողմից տրամադրված տեղեկատվական համակարգերի միջոցով։', en: 'Around 1,109,493 active beneficiaries receive social protection services through the information systems provided by us.' },
    'about.way_label': { hy: 'Պատմություն', en: 'History' },
    'about.way_title': { hy: 'Մեր ճանապարհը', en: 'Our Journey' },
    'about.t1_title': { hy: 'Հիմնադրում', en: 'Foundation' },
    'about.t1_text': { hy: 'ՀՀ կառավարության որոշմամբ ստեղծվեց ՀՀ աշխատանքի և սոցիալական հարցերի նախարարության ենթակայությամբ գործող հիմնադրամը։', en: 'By the decision of the RA Government, a foundation operating under the Ministry of Labor and Social Affairs was established.' },
    'about.t2_title': { hy: 'Զարգացում և ընդլայնում', en: 'Development & Expansion' },
    'about.t2_text': { hy: 'Նախագծվեցին և զարգացվեցին ՀՀ սոցիալական պաշտպանության ոլորտում գործող 23 տեղեկատվական համակարգեր։', en: '23 information systems operating in the RA social protection sector were designed and developed.' },
    'about.t3_title': { hy: 'Նոր հորիզոններ', en: 'New Horizons' },
    'about.t3_text': { hy: 'Շարունակում ենք նորարարական լուծումների ներդրումը և միջազգային համագործակցության ընդլայնումը։', en: 'We continue the implementation of innovative solutions and expansion of international cooperation.' },
    'about.t4_title': { hy: 'Այսօր', en: 'Today' },
    'about.t4_text': { hy: '23+ տարի տեղեկատվական տեխնոլոգիաների ոլորտում, 1 000 000+ ակտիվ շահառու։', en: '23+ years in information technology, 1,000,000+ active beneficiaries.' },
    'about.val_label': { hy: 'Արժեքներ', en: 'Values' },
    'about.val_title': { hy: 'Մեր մոտեցումը', en: 'Our Approach' },
    'about.num_label': { hy: 'Մեր նվաճումները', en: 'Our Achievements' },
    'about.num_title': { hy: 'Թվերով', en: 'In Numbers' },
    'about.num_stat3': { hy: 'Պաշտոնական կայքեր', en: 'Official Websites' },

    /* Services page */
    'svcpage.pagetitle':  { hy: 'Ծառայություններ', en: 'Services' },
    'svcpage.breadcrumb': { hy: 'Գլխավոր / Ծառայություններ', en: 'Home / Services' },
    'svc.badge': { hy: 'Ինչ ենք մենք անում', en: 'What We Do' },
    'svc.text': { hy: 'Մենք ստեղծում ենք արդիական, չկրկնվող և նորարար լուծումներ', en: 'We create modern, unique, and innovative solutions' },
    'svc.offers_title': { hy: 'Ինչ ենք մենք առաջարկում', en: 'What We Offer' },
    'svc.s1_full_title': { hy: 'Տեղեկատվական համակարգերի նախագծում և սպասարկում', en: 'Information Systems Design & Maintenance' },
    'svc.s1_full_text': { hy: 'Տեղեկատվական համակարգերի, նոր ծրագրերի և տվյալների շտեմարանների լրիվ ցիկլով նախագծում և սպասարկում', en: 'Full-cycle design and maintenance of information systems, software, and databases.' },
    'svc.s2_full_title': { hy: 'Տեղեկատվական համակարգերի բովանդակային սպասարկում', en: 'Information Systems Content Maintenance' },
    'svc.s2_full_text': { hy: 'Տվյալների մշակում, վերլուծում և համակարգերի բովանդակային աջակցություն', en: 'Data processing, analysis, and content support of information systems.' },
    'svc.s3_full_title': { hy: 'Տվյալների մշակում և վերլուծում', en: 'Data Processing & Analysis' },
    'svc.s3_full_text': { hy: 'Տվյալների հավաքագրում, մշակում, վերլուծություն և հաշվետվությունների պատրաստում', en: 'Data collection, processing, analysis, and preparation of reports.' },
    'svc.s4_full_title': { hy: 'Կրթական ծրագրերի նախագծում, իրականացում', en: 'Educational Programs Design & Implementation' },
    'svc.s4_full_text': { hy: 'Կրթական ծրագրերի մշակում և իրականացում ՏՏ ոլորտում', en: 'Development and implementation of educational programs in the IT sector.' },
    'svc.s5_full_title': { hy: 'Կիբեռանվտանգություն և ցանցային ապահովում', en: 'Cybersecurity & Network Security' },
    'svc.s5_full_text': { hy: 'Տեղեկատվական անվտանգության ապահովում, ցանցային ենթակառուցվածքի պաշտպանություն', en: 'Ensuring information security, protecting network infrastructure.' },
    'svc.s6_full_title': { hy: 'Տեխնիկական սպասարկում', en: 'Technical Support' },
    'svc.s6_full_text': { hy: 'Համակարգիչների և հարակից տեխնիկայի սպասարկում, 13,000+ միավոր սարքավորում', en: 'Maintenance of computers and related equipment, 13,000+ hardware units.' },
    'svc.projects_label': { hy: 'Պորտֆոլիո', en: 'Portfolio' },
    'svc.projects_title': { hy: 'Մեր նախագծերը', en: 'Our Projects' },
    'svc.p1_title': { hy: 'Ընտանիքի անապահովության գնահատման համակարգ', en: 'Family Vulnerability Assessment System' },
    'svc.p1_text': { hy: 'Ընտանիքների սոցիալական կարգավիճակի գնահատման և աջակցության ծրագրերի ավտոմատացված համակարգ', en: 'Automated system for family social status assessment and support programs.' },
    'svc.p2_title': { hy: 'Սոցիալական արագ արձագանքման ՏՀ', en: 'Social Rapid Response IS' },
    'svc.p2_text': { hy: '2020 թվականին ռազմական դրության պայմաններում մշակված հարթակ արագ սոցիալական աջակցության համար', en: 'Platform developed in 2020 under martial law conditions for rapid social support.' },
    'svc.p3_title': { hy: 'Տվյալների փոխանակման ՏՀ', en: 'Data Exchange IS' },
    'svc.p3_text': { hy: 'ՀՀ սոցիալական պաշտպանության ոլորտի տեղեկատվական համակարգերի և հարակից տվյալների փոխանակման համակարգ', en: 'Information exchange system for RA social protection sector systems.' },
    'svc.p4_title': { hy: '«Գործ» զբաղվածության ՏՀ', en: '"Gorts" Employment IS' },
    'svc.p4_text': { hy: 'ՀՀ զբաղվածության ոլորտի բիզնես-գործընթացների ավտոմատացված համակարգ', en: 'Automated system for business processes in the RA employment sector.' },
    'svc.p5_title': { hy: 'Պրոթեզաօրթոպեդիկ պարագաների ՏՀ', en: 'Prosthetic-Orthopedic Devices IS' },
    'svc.p5_text': { hy: 'Աջակցող միջոցների ստացման համար հավաստագրերի տրամադրման ավտոմատացում', en: 'Automation of issuing certificates for obtaining assistive devices.' },
    'svc.p6_title': { hy: '«Մանուկ» երեխաների հաշվառման ՏՀ', en: '"Manuk" Child Registration IS' },
    'svc.p6_text': { hy: 'Կյանքի դժվարին իրավիճակում հայտնված երեխաների և որդեգրման հաշվառման համակարգ', en: 'Registration system for children in difficult life situations and adoption.' },

    /* Partners page */
    'partners.pagetitle':  { hy: 'Գործընկերներ', en: 'Partners' },
    'partners.breadcrumb': { hy: 'Գլխավոր / Գործընկերներ', en: 'Home / Partners' },
    'part.partners_title': { hy: 'Մենք համագործակցում ենք', en: 'We Collaborate With' },
    'part.partners_subtitle': { hy: 'Պետական հաստատություններ, միջազգային կազմակերպություններ, ֆինանսական հաստատություններ և ՏՏ ընկերություններ', en: 'State institutions, international organizations, financial institutions and IT companies' },

    /* Contact page */
    'contactpage.pagetitle':  { hy: 'Հետադարձ կապ', en: 'Contact' },
    'contactpage.breadcrumb': { hy: 'Գլխավոր / Հետադարձ կապ', en: 'Home / Contact' },
    'contact.badge': { hy: 'Կապ', en: 'Contact' },
    'contact.hero_title': { hy: 'Ստեղծենք միասին', en: 'Let\'s Create Together' },
    'contact.hero_text': { hy: 'Պատրաստ ենք լսել Ձեր գաղափարները և առաջարկությունները', en: 'We are ready to hear your ideas and suggestions' },
    'contact.label': { hy: 'Կապնվել', en: 'Get In Touch' },
    'contact.title': { hy: 'Կապնվեք մեզ հետ', en: 'Contact Us' },
    'contact.address': { hy: 'Հասցե', en: 'Address' },
    'contact.address_val': { hy: 'Երևան, Հայաստան', en: 'Yerevan, Armenia' },
    'contactpage.form_title': { hy: 'Գրել նամակ', en: 'Send a Message' },
    'contactpage.form_sub':   { hy: 'Լրացրեք ձևը և մենք կպատասխանենք առաջիկա օրերին', en: 'Fill in the form and we will respond within the next few days' },
    'contactpage.name_ph':    { hy: 'Ձեր անունը', en: 'Your Name' },
    'contactpage.email_ph':   { hy: 'Ձեր էլ. փոստը', en: 'Your Email' },
    'contactpage.subj_ph':    { hy: 'Թեմա', en: 'Subject' },
    'contactpage.msg_ph':     { hy: 'Ձեր հաղորդագրությունը', en: 'Your Message' },
    'contactpage.send_btn':   { hy: 'Ուղարկել', en: 'Send' },

  };

  // ── Real Armenian Unicode text ─────────────────────────
  // The values above use transliterations as fallback.
  // The real Armenian text is set as the default textContent
  // in the HTML elements (data-i18n elements keep HY text by default).
  // When lang='en', we translate; when lang='hy' we restore from this map.
  const HY = {
    'nav.home':       'Գлхаворр',
    'nav.about':      'Մеr masun',
    'nav.services':   'Ծarajуtjунner',
    'nav.partners':   'Горцункернер',
    'nav.contact':    'Хетадарц кап',
    'nav.blog':       'Блог',
  };

  /* ══════════════════════════════════════════════════════
     CACHE — Save original Armenian textContent on first run
     so we can restore it when switching back to HY.
  ══════════════════════════════════════════════════════ */
  const cache = new Map(); // key → original Armenian text

  function cacheOriginals() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (!cache.has(key)) {
        const attr = el.getAttribute('data-i18n-attr');
        if (attr) {
          cache.set(key, el.getAttribute(attr) || '');
        } else if (el.matches('input, textarea')) {
          cache.set(key, el.placeholder || '');
        } else {
          cache.set(key, el.textContent.trim());
        }
      }
    });
  }

  /* ══════════════════════════════════════════════════════
     STATE
  ══════════════════════════════════════════════════════ */
  let lang = localStorage.getItem('wisef_lang') ||
    (document.documentElement.getAttribute('lang') === 'en' ? 'en' : 'hy');

  /* ══════════════════════════════════════════════════════
     APPLY LANGUAGE
  ══════════════════════════════════════════════════════ */
  function applyLang(newLang) {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key  = el.getAttribute('data-i18n');
      const attr = el.getAttribute('data-i18n-attr');
      let text;

      if (newLang === 'hy') {
        // Restore original Armenian (cached from initial HTML)
        text = cache.get(key);
      } else {
        // Get English translation
        const entry = T[key];
        text = entry ? entry.en : undefined;
      }

      if (text === undefined || text === null) return;

      if (attr) {
        el.setAttribute(attr, text);
      } else if (el.matches('input, textarea')) {
        el.setAttribute('placeholder', text);
      } else {
        el.textContent = text;
      }
    });

    document.documentElement.setAttribute('lang', newLang);
    document.body.setAttribute('lang', newLang);

    const toggle = document.querySelector('.lang-toggle');
    if (toggle) {
      toggle.classList.toggle('lang-toggle--en', newLang === 'en');
      toggle.setAttribute('aria-checked', newLang === 'en' ? 'true' : 'false');
    }

    lang = newLang;
    localStorage.setItem('wisef_lang', newLang);
    document.dispatchEvent(new CustomEvent('wisefLangChanged', { detail: { lang: newLang } }));
  }

  /* ══════════════════════════════════════════════════════
     BUILD TOGGLE WIDGET
  ══════════════════════════════════════════════════════ */
  function buildToggle() {
    const btn = document.createElement('button');
    btn.className = 'lang-toggle' + (lang === 'en' ? ' lang-toggle--en' : '');
    btn.type = 'button';
    btn.setAttribute('role', 'switch');
    btn.setAttribute('aria-checked', lang === 'en' ? 'true' : 'false');
    btn.setAttribute('aria-label', 'Switch language');
    btn.innerHTML = `
      <span class="lang-toggle__hy" aria-hidden="true">ՀՅ</span>
      <span class="lang-toggle__track" aria-hidden="true">
        <span class="lang-toggle__thumb"></span>
      </span>
      <span class="lang-toggle__en" aria-hidden="true">EN</span>
    `;
    btn.addEventListener('click', () => applyLang(lang === 'hy' ? 'en' : 'hy'));
    btn.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); btn.click(); }
    });
    return btn;
  }

  /* ══════════════════════════════════════════════════════
     INIT
  ══════════════════════════════════════════════════════ */
  function init() {
    // 1. Cache all original Armenian text from the DOM
    cacheOriginals();

    // 2. Replace every .nav__lang-btn with the new toggle
    document.querySelectorAll('.nav__lang-btn').forEach(old => {
      old.parentNode.replaceChild(buildToggle(), old);
    });

    // 3. If saved language is English, apply it now
    if (lang === 'en') applyLang('en');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Public API
  window.wisefI18n = {
    t:       (key) => { const e = T[key]; return e ? (e[lang] || e.en) : key; },
    getLang: ()    => lang,
    setLang: applyLang,
  };

})();
