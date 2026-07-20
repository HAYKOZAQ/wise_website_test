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
     TRANSLATIONS — Clean, correct Armenian Unicode & English
  ══════════════════════════════════════════════════════ */
  const T = {

    /* Navigation */
    'nav.home':       { hy: 'Գլխավոր',  en: 'Home' },
    'nav.about':      { hy: 'Մեր մասին', en: 'About' },
    'nav.services':   { hy: 'Ծառայություններ', en: 'Services' },
    'nav.partners':   { hy: 'Գործընկերներ', en: 'Partners' },
    'nav.contact':    { hy: 'Հետադարձ կապ', en: 'Contact' },
    'nav.blog':       { hy: 'Բլոգ', en: 'Blog' },

    /* Hero – Home */
    'home.badge':        { hy: '🌟 25 տարի տեխնոլոգիաների ոլորտում', en: '🌟 25 years in information technology' },
    'home.hero_h1a':     { hy: 'Մենք ստեղծում ենք', en: 'We Create' },
    'home.hero_h1b':     { hy: 'թվային լուծումներ', en: 'Digital Solutions' },
    'home.hero_p':       { hy: '«Բարեկեցության տեղեկատվական համակարգերի ձեռնարկություն» հիմնադրամ — Հայաստանում առաջատար տեխնոլոգիական կենտրոն՝ 25+ տարվա փորձով',
                           en: 'Welfare Information Systems Enterprise Foundation — Armenia\'s leading technology center with 25+ years of experience in government and private sector IT solutions' },
    'home.btn_services': { hy: 'Դիտել ծառայությունները', en: 'Our Services' },
    'home.btn_contact':  { hy: 'Կապնվել մեզ հետ', en: 'Contact Us' },

    /* Why section */
    'why.label':     { hy: 'Մեր ուղղությունները', en: 'Our Approach' },
    'why.title':     { hy: 'Երազեք, ստեղծեք, կիսվեք մեզ հետ', en: 'Dream, Create, Share with Us' },
    'why.subtitle':  { hy: 'Միասին կառուցում ենք թվային ապագան', en: 'Together we build the digital future' },
    'why.c1_title':  { hy: 'Երազեք մեզ հետ', en: 'Dream with Us' },
    'why.c1_text':   { hy: 'Երազեք մեզ հետ նորարության և թվային ապագայի մասին', en: 'Dream with us about innovation and a digital future' },
    'why.c2_title':  { hy: 'Ստեղծեք մեզ հետ', en: 'Create with Us' },
    'why.c2_text':   { hy: 'Ստեղծեք մեզ հետ թվային ապագայի նորարական լուծումներ', en: 'Create innovative digital solutions with us' },
    'why.c3_title':  { hy: 'Կիսվեք մեզ հետ', en: 'Share with Us' },
    'why.c3_text':   { hy: 'Կիսվեք մեզ հետ Ձեր երազանքներով թվային ապագայի կատարելագործման համար', en: 'Share your dreams for improving the digital future' },

    /* Services preview */
    'svc.label':     { hy: 'Ծառայություններ', en: 'Services' },
    'svc.title':     { hy: 'Մեր ծառայությունները', en: 'Our Services' },
    'svc.subtitle':  { hy: 'Տեղեկատվական համակարգերի, նոր ծրագրերի և տվյալների շտեմարանների նախագծում և սպասարկում', en: 'Design and maintenance of information systems, new programs, and databases' },
    'svc.s1_title':  { hy: 'ՏՀ նախագծում և սպասարկում', en: 'IS Design & Maintenance' },
    'svc.s1_text':   { hy: 'Տեղեկատվական համակարգերի, նոր ծրագրերի և տվյալների շտեմարանների նախագծում և սպասարկում', en: 'Full-cycle design and maintenance of information systems, software, and databases' },
    'svc.s2_title':  { hy: 'Տվյալների մշակում', en: 'Data Processing' },
    'svc.s2_text':   { hy: 'Տեղեկատվական համակարգերի բովանդակային սպասարկում, տվյալների մշակում և վերլուծում', en: 'Content maintenance, data processing, and analysis of information systems' },
    'svc.s3_title':  { hy: 'Կրթական ծրագրեր', en: 'Educational Programs' },
    'svc.s3_text':   { hy: 'Կրթական ծրագրերի նախագծում և իրականացում', en: 'Design and implementation of educational programs in IT' },
    'svc.s4_title':  { hy: 'Կիբեռանվտանգություն', en: 'Cybersecurity' },
    'svc.s4_text':   { hy: 'Կիբեռանվտանգություն և ցանցային ապահովում', en: 'Cybersecurity and network security solutions' },
    'svc.s5_title':  { hy: 'Տեխնիկական սպասարկում', en: 'Technical Support' },
    'svc.s5_text':   { hy: 'Համակարգիչների և հարակից տեխնիկայի սպասարկում', en: 'Computer and related equipment maintenance (13,000+ units)' },
    'svc.s6_title':  { hy: 'Ինտեգրացիոն լուծումներ', en: 'Integration Solutions' },
    'svc.s6_text':   { hy: 'Համակարգերի ինտեգրացիա և տվյալների փոխանակման ապահովում', en: 'System integration and data exchange solutions' },
    'svc.btn_all':   { hy: 'Բոլոր ծառայությունները', en: 'All Services' },

    /* Stats */
    'stats.label':   { hy: 'Մեր նվաճումները', en: 'Our Achievements' },
    'stats.title':   { hy: '25 տարի տեղեկատվական տեխնոլոգիաների ոլորտում', en: '25 Years in Information Technology' },
    'stats.s1':      { hy: 'Տարի տեխնոլոգիաների ոլորտում', en: 'Years in IT' },
    'stats.s2':      { hy: 'Ակտիվ շահառու', en: 'Active Beneficiaries' },
    'stats.s3':      { hy: 'Նախագծված տեղեկատվական համակարգեր', en: 'IS Systems Designed' },
    'stats.s4':      { hy: 'Սպասարկվող սարքավորումներ', en: 'Serviced Equipment' },

    /* About preview */
    'aboutprev.label': { hy: 'Մեր մասին', en: 'About Us' },
    'aboutprev.title': { hy: '«Բարեկեցության տեղեկատվական համակարգերի ձեռնարկություն» հիմնադրամ', en: 'Welfare Information Systems Enterprise Foundation' },
    'aboutprev.p1':    { hy: 'Մենք հիմնադրվել ենք 2001 թվականին։ 25 տարի առաջ, ՀՀ կառավարության որոշմամբ ստեղծվեց ՀՀ աշխատանքի և սոցիալական հարցերի նախարարության ենթակայությամբ գործող հիմնադրամ։',
                         en: 'We were founded in 2001, by decree of the Government of the Republic of Armenia, under the Ministry of Labor and Social Affairs.' },
    'aboutprev.p2':    { hy: 'Հայաստանում առաջատար տեխնոլոգիական կենտրոն է, որն իրականացնում է պետական և մասնավոր ոլորտի տեղեկատվական և հեռահաղորդակցության տեխնոլոգիաների ենթակառուցվածքների ներդրում և սպասարկում։',
                         en: 'Armenia\'s leading technology center implementing information and telecommunication infrastructure for public and private sectors.' },
    'aboutprev.btn':   { hy: 'Իմանալ ավելին', en: 'Learn More' },

    /* Contact preview */
    'contactprev.label': { hy: 'Հետադարձ կապ', en: 'Contact' },
    'contactprev.title': { hy: 'Ստեղծենք միասին', en: 'Let\'s Build Together' },
    'contactprev.sub':   { hy: 'Պատրաստ ենք լսել Ձեր գաղափարները', en: 'We are ready to hear your ideas' },
    'contactprev.email': { hy: 'Էլ. փոստ', en: 'Email' },
    'contactprev.phone': { hy: 'Հեռախոս', en: 'Phone' },
    'contactprev.btn':   { hy: 'Գրել նամակ', en: 'Send Message' },

    /* About page */
    'about.pagetitle':  { hy: 'Մեր մասին', en: 'About Us' },
    'about.exp_label': { hy: '25 տարվա փորձ', en: '25 Years of Experience' },
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
    'about.t4_text': { hy: '25+ տարի տեղեկատվական տեխնոլոգիաների ոլորտում, 1 000 000+ ակտիվ շահառու։', en: '25+ years in information technology, 1,000,000+ active beneficiaries.' },
    'about.val_label': { hy: 'Արժեքներ', en: 'Values' },
    'about.val_title': { hy: 'Մեր մոտեցումը', en: 'Our Approach' },
    'about.val1_title': { hy: 'ՍՏԵՂԾԱԳՈՐԾԱԿԱՆ ՄՈՏԵՑՈՒՄ ՅՈՒՐԱՔԱՆՉՅՈՒՐ ՆԱԽԱԳԾԻՆ', en: 'CREATIVE APPROACH TO EACH PROJECT' },
    'about.val1_text':  { hy: 'Ստեղծագործական մոտեցում յուրաքանչյուր նախագծին', en: 'Creative approach to each project' },
    'about.val2_title': { hy: 'ՊԱՀԱՆՋՆԵՐԻ ՀՍՏԱԿ ՍԱՀՄԱՆՈՒՄ', en: 'CLEAR DEFINITION OF REQUIREMENTS' },
    'about.val2_text':  { hy: 'Պահանջների հստակ սահմանում', en: 'Clear definition of requirements' },
    'about.val3_title': { hy: 'ՃՇԳՐԻՏ ՊԼԱՆԱՎՈՐՈՒՄ ԵՎ ՎԵՐԱՀՍԿՈՂՈՒԹՅՈՒՆ', en: 'ACCURATE PLANNING AND CONTROL' },
    'about.val3_text':  { hy: 'Ճշգրիտ պլանավորում և վերահսկողություն', en: 'Accurate planning and control' },
    'about.val4_title': { hy: 'ԱՐԴՅՈՒՆԱՎԵՏ ԿԱՌԱՎԱՐՈՒՄ', en: 'EFFECTIVE MANAGEMENT' },
    'about.val4_text':  { hy: 'Արդյունավետ կառավարում որակի ապահովման նպատակով', en: 'Effective management ensuring quality' },
    'about.val5_title': { hy: 'ՀԵՌԱՀԱՐ ԶԱՐԳԱՑՄԱՆ ՏԵՍԼԱԿԱՆ', en: 'VISION OF DISTANCE DEVELOPMENT' },
    'about.val5_text':  { hy: 'Հեռահար զարգացման տեսլական', en: 'Vision of distance development' },
    'about.val6_title': { hy: 'ԳՈՐԾԱՌՆԱԿԱՆ ԱՋԱԿՑՈՒԹՅՈՒՆ ԵՎ ԽՈՐՀՐԴԱՏՎՈՒԹՅՈՒՆ', en: 'OPERATION SUPPORT AND CONSULTING' },
    'about.val6_text':  { hy: 'Գործառնական աջակցություն և խորհրդատվություն', en: 'Operation support and consulting' },
    'about.num_label': { hy: 'Մեր նվաճումները', en: 'Our Achievements' },
    'about.num_title': { hy: 'Թվերով', en: 'In Numbers' },
    'about.num_stat3': { hy: 'Պաշտոնական կայքեր', en: 'Official Websites' },

    /* Footer */
    'footer.brand':      { hy: '«Բարեկեցության տեղեկատվական համակարգերի ձեռնարկություն» հիմնադրամ', en: 'Welfare Information Systems Enterprise Foundation' },
    'footer.site':       { hy: 'Կայք', en: 'Site' },
    'footer.contact':    { hy: 'Կապ', en: 'Contact' },
    'footer.follow':     { hy: 'Հետևեք մեզ', en: 'Follow Us' },
    'footer.home':       { hy: 'Գլխավոր', en: 'Home' },
    'footer.about':      { hy: 'Մեր մասին', en: 'About' },
    'footer.services':   { hy: 'Ծառայություններ', en: 'Services' },
    'footer.partners':   { hy: 'Գործընկերներ', en: 'Partners' },
    'footer.blog':       { hy: 'Բլոգ', en: 'Blog' },
    'footer.contact_us': { hy: 'Հետադարձ կապ', en: 'Contact Us' },
    'footer.copyright':  { hy: '© 2026 Designed by «WISE» foundation', en: '© 2026 Designed by «WISE» foundation' },

    /* Blog page */
    'blog.pagetitle':  { hy: 'Բլոգ', en: 'Blog' },
    'blog.breadcrumb': { hy: 'Գլխավոր / Բլոգ', en: 'Home / Blog' },
    'blog.readmore':   { hy: 'Կարդալ ավելին', en: 'Read More' },
    'blog.loading':    { hy: 'Բեռնվում է...', en: 'Loading...' },
    'blog.close':      { hy: 'Փակել', en: 'Close' },
    'blog.open_orig':  { hy: 'Բացել օրիգինալ էջում', en: 'Open Original Article' },
    'blog.search_ph':  { hy: 'Որոնել հոդվածներ...', en: 'Search articles...' },
    'blog.featured_date': { hy: 'Հուլիս 24, 2024', en: 'July 24, 2024' },
    'blog.featured_title':{ hy: 'Պատրաստ է գործարկման «Աշխատանք առանց սահմանների» որոնման միասնական համակարգ»-ը', en: '"Work Without Borders" Unified Search System Launched' },
    'blog.featured_text': { hy: '«Աշխատանքի էլեկտրոնային բորսա» ծրագրի ֆինանսական աուդիտի հաշվետվությունները', en: 'Financial audit reports of the Electronic Labor Exchange program' },

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

    'svc.p7_title': { hy: 'Ընտանիքում բռնության դեպքերի հաշվառման ՏՀ', en: 'Domestic Violence Registration IS' },
    'svc.p7_text': { hy: 'Ընտանիքում բռնության դեպքերի կենտրոնացված հաշվառման համակարգ՝ ընտանեկան բռնության խնդիրների լուծման համար', en: 'Centralized registration system for domestic violence cases.' },
    'svc.p8_title': { hy: 'Տեղահանված ընտանիքների բնակարանային ապահովման ՏՀ', en: 'Housing Support for Displaced Families IS' },
    'svc.p8_text': { hy: 'Լեռնային Ղարաբաղից բռնի տեղահանված ընտանիքների բնակարանային ապահովման պետական աջակցության ծրագրի կառավարման համակարգ', en: 'Management system for state housing support program for displaced families.' },
    'svc.p9_title': { hy: 'Հրատապ արձագանքման հարթակ', en: 'Urgent Response Platform' },
    'svc.p9_text': { hy: 'www.hratapkariq.am — սոցիալական պաշտպանության ոլորտի ընթացիկ բարեփոխումների շրջանակներում գործարկված հարթակ', en: 'www.hratapkariq.am — platform for urgent social response.' },
    'svc.p10_title': { hy: 'Քաղաքացիական ծառայողների ատեստավորման ՏՀ', en: 'Civil Servants Attestation IS' },
    'svc.p10_text': { hy: 'Քաղաքացիական ծառայողների ատեստավորման հարցաշարերի տեղեկատվական համակարգ (մշակվել է 2010 թվականին)', en: 'IS for civil servants attestation questionnaires (2010).' },
    'svc.p11_title': { hy: 'Համալիր սոցիալական ծառայությունների ընդունարանների ՏՀ', en: 'Integrated Social Services Reception IS' },
    'svc.p11_text': { hy: 'Սոցիալական խնդիրներով դիմումների հաշվառման տարածքային մարմինների միասնական համակարգ', en: 'Unified application registration system for integrated social services.' },
    'svc.p12_title': { hy: 'Տարեցների և հաշմանդամների հաշվառման ՏՀ', en: 'Senior Citizens and Disabled Registration IS' },
    'svc.p12_text': { hy: 'Սոցիալական պաշտպանության ծրագրերում ընդգրկված և խնամք ստացող տարեցների ու հաշմանդամների հաշվառում', en: 'Registration of senior citizens and disabled persons in social programs.' },
    'svc.p13_title': { hy: 'Հաշմանդամների հաշվառման «Փյունիկ» ՏՀ', en: 'Pyunik Disability Registration IS' },
    'svc.p13_text': { hy: 'Հաշմանդամության կարգ ստանալու համար դիմած անձանց տվյալների և որոշումների հաշվառման համակարգ', en: 'Registration system for persons applying for disability status.' },
    'svc.p14_title': { hy: 'Բարեգործական ծրագրերի հաշվառման ՏՀ', en: 'Charitable Programs Registration IS' },
    'svc.p14_text': { hy: 'Բարեգործական ծրագրերի, կարիքների հաշվառման և բարեգործության ստացման 3 ենթահամակարգով ՏՀ', en: 'IS with 3 subsystems: programs, needs, and charity receipt.' },
    'svc.p15_title': { hy: 'Սոցիալական բնակարանային ֆոնդի ՏՀ', en: 'Social Housing Fund Registration IS' },
    'svc.p15_text': { hy: 'Կացարանների հաշվառման և հերթացուցակի ձևավորման տեղեկատվական համակարգ (նախագծվել է 2014 թվականին)', en: 'IS for housing registration and waiting list (2014).' },
    'svc.p16_title': { hy: 'Սոցիալական դեպքի վարման ՏՀ', en: 'Social Case Management IS' },
    'svc.p16_text': { hy: 'Սոցիալական դեպքի վարման գործընթացի ավտոմատացում՝ դիմումից մինչև ընտանիքի անդամների տվյալների մշակում', en: 'Automation of social case management process.' },
    'svc.p17_title': { hy: 'ԽՍՀՄ խնայբանկի ավանդների փոխհատուցման ՏՀ', en: 'USSR Savings Bank Compensation IS' },
    'svc.p17_text': { hy: 'Մինչև 10.06.1993թ. ներդրված դրամական ավանդների փոխհատուցման ավտոմատացված համակարգ', en: 'Compensation system for pre-1993 USSR Savings Bank deposits.' },
    'svc.p18_title': { hy: 'Ընտանիքների անապահովության «Նպաստ» ՏՀ', en: 'Npast Family Vulnerability Assessment IS' },
    'svc.p18_text': { hy: 'Ընտանիքների անապահովության գնահատման միավորի հաշվարկի ավտոմատացված համակարգ', en: 'Automated system for family vulnerability assessment scoring.' },

    'svc.details_label': { hy: 'Ծառայությունների մանրամասներ', en: 'Service Details' },
    'svc.details_title': { hy: 'Ինչ ենք մենք տրամադրում', en: 'What We Provide' },
    'svc.sd1_title': { hy: 'Տեղեկատվական համակարգերի նախագծում և սպասարկում', en: 'IS Design and Maintenance' },
    'svc.sd1_intro': { hy: 'ՏՏ նախագծերի կառավարման մեթոդաբանություն՝ PMBoK, Agile', en: 'IT project management: PMBoK, Agile' },
    'svc.sd1_l1': { hy: 'Back-End ծրագրավորում: PHP, C# ASP.NET WCF (Yii, React)', en: 'Back-End: PHP, C# ASP.NET WCF (Yii, React)' },
    'svc.sd1_l2': { hy: 'Տվյալների բազաներ: MySQL, PostgreSQL, Oracle', en: 'Databases: MySQL, PostgreSQL, Oracle' },
    'svc.sd1_l3': { hy: 'Front-End: HTML/CSS/JS (BootStrap)', en: 'Front-End: HTML/CSS/JS (BootStrap)' },
    'svc.sd2_title': { hy: 'Տեղեկատվական համակարգերի բովանդակային սպասարկում', en: 'IS Content Maintenance' },
    'svc.sd2_text': { hy: 'Տվյալների մշակում, վերլուծում և համակարգերի բովանդակային աջակցություն: Մենք ապահովում ենք ՏՀ-երի բովանդակային թարմացումը և տվյալների որակի վերահսկողությունը', en: 'Data processing, analysis and content support with quality control.' },
    'svc.sd3_title': { hy: 'Տվյալների մշակում և վերլուծում', en: 'Data Processing and Analysis' },
    'svc.sd3_text': { hy: 'Տվյալների հավաքագրում, մշակում, վերլուծություն և հաշվետվությունների պատրաստում: Մենք տրամադրում ենք վերլուծական հաշվետվություններ պետական մարմինների համար', en: 'Data collection, processing, analysis and report preparation.' },
    'svc.sd4_title': { hy: 'Կրթական ծրագրերի նախագծում, իրականացում', en: 'Educational Programs Design' },
    'svc.sd4_text': { hy: 'Սոցիալական ծառայություններ տրամադրելու գործընթացում կիրառվող տեղեկատվական համակարգերի ուսուցում: Վերապատրաստման դասընթացների վերաբերյալ տեղեկատվությունը ՀՀ աշխատանքի և սոցիալական հարցերի նախարարության կայքում', en: 'Training on IS used in social service delivery.' },
    'svc.sd5_title': { hy: 'Կիբեռանվտանգություն և ցանցային ապահովում', en: 'Cybersecurity and Network Support' },
    'svc.sd5_text': { hy: 'Տեղեկատվական անվտանգության ապահովում, ցանցային ենթակառուցվածքի պաշտպանություն: Տվյալների պաշտպանություն և կիբեռահարձադույց', en: 'Information security, network infrastructure protection.' },
    'svc.sd6_title': { hy: 'Համակարգիչների և հարակից տեխնիկայի սպասարկում', en: 'Computer and Equipment Maintenance' },
    'svc.sd6_text': { hy: 'Համակարգչային տեխնիկայի դիագնոստիկա, տեղադրում, ծրագրային ապահովման կարգավորում, ցանցային կառուցում: 13,000+ միավոր սարքավորում', en: 'Computer diagnostics, installation, software setup: 13,000+ units.' },
    'svc.loading': { hy: 'Բեռնվում է...', en: 'Loading...' },
    'svc.contact_about': { hy: 'Կապնվել այս ծրագրի շուրջ', en: 'Contact us about this project' },

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

    /* Partner Names */
    'part.p1': { hy: 'ՀՀ Կառավարություն', en: 'Government of RA' },
    'part.p2': { hy: 'Ազգային անվտանգության ծառայություն', en: 'National Security Service' },
    'part.p3': { hy: 'Ասոցիալական հետազոտությունների ինստիտուտ', en: 'National Institute of Labor and Social Research' },
    'part.p4': { hy: 'ՀՀ Ոստիկանություն', en: 'Police of RA' },
    'part.p5': { hy: 'Հայփոստ', en: 'Haypost' },
    'part.p6': { hy: 'Յուքոմ', en: 'Ucom' },
    'part.p7': { hy: 'UNFPA', en: 'UNFPA' },
    'part.p8': { hy: 'Հայաստանի Ամերիկյան Համալսարան', en: 'American University of Armenia' },
    'part.p9': { hy: 'USAID', en: 'USAID' },
    'part.p10': { hy: 'WFP', en: 'WFP' },
    'part.p11': { hy: 'UITE', en: 'UITE' },
    'part.p12': { hy: 'IBM', en: 'IBM' },
    'part.p13': { hy: 'Microsoft', en: 'Microsoft' },
    'part.p14': { hy: 'Համաշխարհային Բանկ', en: 'World Bank' },
    'part.p15': { hy: 'Ամերիաբանկ', en: 'Ameriabank' },
    'part.p16': { hy: 'Էվոկա բանկ', en: 'Evocabank' },
    'part.p17': { hy: 'Ակբա բանկ', en: 'Acba Bank' },
    'part.p18': { hy: 'Կոնվերս բանկ', en: 'Converse Bank' },
    'part.p19': { hy: 'Յունիբանկ', en: 'Unibank' },
    'part.p20': { hy: 'Արդշինբանկ', en: 'Ardshinbank' },
    'part.p21': { hy: 'Պետական եկամուտների կոմիտե', en: 'State Revenue Committee' },
    'part.p22': { hy: 'Միասնական Սոցիալական Ծառայություն', en: 'Unified Social Service' },
    'part.p23': { hy: 'Գիտության և տեխնոլոգիաների միջազգային կենտրոն', en: 'International Science and Technology Center' },
    'part.p24': { hy: 'Ձեռնարկությունների ինկուբատոր հիմնադրամ', en: 'Enterprise Incubator Foundation' },
    'part.p25': { hy: 'Այ Դի բանկ', en: 'ID Bank' },
    'part.p26': { hy: 'Բիբլոս բանկ', en: 'Biblos Bank' },
    'part.p27': { hy: 'Մելլաթ բանկ', en: 'Mellat Bank' },
    'part.p28': { hy: 'Ինեկոբանկ', en: 'Inecobank' },
    'part.p29': { hy: 'Հայբիզնեսբանկ', en: 'Haybusinessbank' },
    'part.p30': { hy: 'Հայէկենեմբանկ', en: 'Hayeknembank' },
    'part.p31': { hy: 'ՎՏԲ բանկ', en: 'VTB Bank' },
    'part.p32': { hy: 'Credo Finance UCO', en: 'Credo Finance UCO' },
    'part.p33': { hy: 'Mogo UCO', en: 'Mogo UCO' },
    'part.p34': { hy: 'Aregak UCO', en: 'Aregak UCO' },
    'part.p35': { hy: 'Rosgosstrakh', en: 'Rosgosstrakh' },
    'part.p36': { hy: 'Armenia Insurance', en: 'Armenia Insurance' },
    'part.p37': { hy: 'Global Credit', en: 'Global Credit' },
    'part.p38': { hy: 'Norman Credit', en: 'Norman Credit' },
    'part.p39': { hy: 'SEF International', en: 'SEF International' },
    'part.p40': { hy: 'Finca', en: 'Finca' },
    'part.p41': { hy: 'Araratbank', en: 'Araratbank' },
    'part.p42': { hy: 'KAMURJ UCO', en: 'KAMURJ UCO' },
    'part.p43': { hy: 'Rostelecom', en: 'Rostelecom' },

    /* Simple Help Assistant */
    'chat.fab':            { hy: 'Հարցրեք մեզ', en: 'Ask us' },
    'chat.title':          { hy: 'Սոցիալական օգնական', en: 'Social Help Assistant' },
    'chat.placeholder':    { hy: 'Օրինակ՝ տարիքային կենսաթոշակ', en: 'e.g. age pension' },
    'chat.welcome_title':  { hy: 'Բարև ձեզ', en: 'Hello' },
    'chat.welcome':        { hy: 'Հարցրեք նպաստների, կենսաթոշակների և սոցիալական ծրագրերի մասին։ Պատասխանները հիմնված են պաշտոնական տեղեկատվության վրա։', en: 'Ask about benefits, pensions, and social programs. Answers are based on official information.' },
    'chat.topics_label':   { hy: 'Ընտրեք թեմա կամ գրեք հարց', en: 'Pick a topic or type a question' },
    'chat.disclaimer':     { hy: 'Տեղեկատվական է · Պաշտոնական որոշման համար՝ 114', en: 'For information only · Official decisions: call 114' },
    'chat.err_offline':    { hy: 'Հիմա չեմ կարող պատասխանել։ Ստուգեք, որ սերվերն աշխատում է (start_backend.bat կամ cloud API)։', en: 'I cannot answer right now. Please start the server (local or cloud API).' },
    'chat.err_no_api':     { hy: 'Արտադրական կայքում AI-ն աշխատելու համար տեղադրեք backend-ը (Render/Railway) և լրացրեք productionApiBase-ը config.js-ում։ Տե՛ս DEPLOY.md։', en: 'To use AI on the live site, deploy the backend (Render/Railway) and set productionApiBase in config.js. See DEPLOY.md.' },
    'chat.status_ready':   { hy: 'Պատրաստ է օգնել', en: 'Ready to help' },
    'chat.status_offline': { hy: 'Սերվերը անջատված է', en: 'Server is offline' },
    'chat.thinking':       { hy: 'Մտածում եմ…', en: 'Thinking…' },
    'chat.sources_label':  { hy: 'Աղբյուրներ', en: 'Sources' },
    'chat.new':            { hy: 'Նոր զրույց', en: 'New chat' },

    /* Topic buttons */
    'chat.q1': { hy: 'Մինչև 2 տարեկան երեխայի նպաստ', en: 'Childcare allowance under 2' },
    'chat.q2': { hy: 'Երեխայի ծննդյան միանվագ նպաստ', en: 'One-time childbirth benefit' },
    'chat.q3': { hy: 'Ընտանեկան նպաստ', en: 'Family benefit' },
    'chat.q4': { hy: 'Տարիքային կենսաթոշակ', en: 'Age pension' },
    'chat.q5': { hy: 'Հաշմանդամության կենսաթոշակ', en: 'Disability pension' },
    'chat.q9': { hy: 'Տեղահանվածների աջակցություն', en: 'Displaced persons support' },
    'chat.q10': { hy: 'Ֆունկցիոնալության գնահատում', en: 'Functional assessment / disability' },
    'chat.q6': { hy: 'Գործազրկության կարգավիճակ', en: 'Unemployment status' },
    'chat.q7': { hy: 'Էլեկտրաէներգիայի փոխհատուցում', en: 'Electricity subsidy' },
    'chat.q8': { hy: 'ՄՍԾ թեժ գիծ 114', en: 'Hotline 114 contacts' },

    /* Page titles */
    'site.title.home':     { hy: 'WISE Foundation — «Բարեկեցության տեղեկատվական համակարգերի ձեռնարկություն» հիմնադրամ', en: 'WISE Foundation — Welfare Information Systems Enterprise Foundation' },
    'site.title.about':    { hy: 'Մեր մասին — WISE Foundation', en: 'About Us — WISE Foundation' },
    'site.title.services': { hy: 'Ծառայություններ — WISE Foundation', en: 'Services — WISE Foundation' },
    'site.title.partners': { hy: 'Գործընկերներ — WISE Foundation', en: 'Partners — WISE Foundation' },
    'site.title.contact':  { hy: 'Հետադարձ կապ — WISE Foundation', en: 'Contact Us — WISE Foundation' },
    'site.title.blog':     { hy: 'Բլոգ — WISE Foundation', en: 'Blog — WISE Foundation' },

    /* Meta descriptions */
    'site.desc.home':     { hy: 'WISE Foundation — 25 տարի տեղեկատվական տեխնոլոգիաների ոլորտում: Մենք ստեղծում ենք թվային լուծումներ:', en: 'WISE Foundation — 25 years in information technology. We create digital solutions for government and private sector.' },
    'site.desc.about':    { hy: 'Իմացեք ավելին WISE Foundation-ի մասին՝ 25 տարվա փորձ տեղեկատվական տեխնոլոգիաների ոլորտում:', en: 'Learn more about WISE Foundation — 25 years of experience in information technology.' },
    'site.desc.services': { hy: 'WISE Foundation-ի ծառայություններ՝ տեղեկատվական համակարգերի նախագծում, կիբեռանվտանգություն, տվյալների մշակում և ավելին:', en: 'WISE Foundation services — information systems design, cybersecurity, data processing and more.' },
    'site.desc.partners': { hy: 'WISE Foundation-ի գործընկերներ՝ պետական հաստատություններ, միջազգային կազմակերպություններ, բանկեր:', en: 'WISE Foundation partners — government institutions, international organizations, banks.' },
    'site.desc.contact':  { hy: 'Կապնվեք WISE Foundation-ի հետ: Էլ. փոստ, հեռախոս, կոնտակտային ձև:', en: 'Contact WISE Foundation. Email, phone, contact form.' },
    'site.desc.blog':     { hy: 'WISE Foundation-ի բլոգ՝ նորություններ, հոդվածներ և հայտարարություններ տեղեկատվական տեխնոլոգիաների ոլորտում:', en: 'WISE Foundation blog — news, articles and announcements in information technology.' }
  };

  /* ══════════════════════════════════════════════════════
     CACHE — Save original Armenian textContent on first run
  ══════════════════════════════════════════════════════ */
  const cache = new Map();

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
        const entry = T[key];
        text = (entry && entry.hy) ? entry.hy : cache.get(key);
      } else {
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
     THEME SWITCHER
  ══════════════════════════════════════════════════════ */
  function buildThemeToggle() {
    const btn = document.createElement('button');
    btn.className = 'theme-toggle';
    btn.type = 'button';
    btn.setAttribute('aria-label', 'Toggle theme');
    btn.innerHTML = `
      <svg class="theme-toggle__moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
      </svg>
      <svg class="theme-toggle__sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="5"></circle>
        <line x1="12" y1="1" x2="12" y2="3"></line>
        <line x1="12" y1="21" x2="12" y2="23"></line>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
        <line x1="1" y1="12" x2="3" y2="12"></line>
        <line x1="21" y1="12" x2="23" y2="12"></line>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
      </svg>
    `;
    btn.addEventListener('click', () => {
      const theme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', theme);
      document.documentElement.style.colorScheme = theme === 'dark' ? 'dark' : 'light';
      localStorage.setItem('wisef_theme', theme);
      applyHeaderLogo(theme);
    });
    return btn;
  }

  function applyHeaderLogo(theme) {
    const dark = theme === 'dark';
    document.querySelectorAll('.header__logo img').forEach((img) => {
      const src = img.getAttribute('src') || '';
      if (dark) {
        img.setAttribute('src', src.replace('wisef-logo.svg', 'wisef-logo-white.svg'));
      } else {
        img.setAttribute('src', src.replace('wisef-logo-white.svg', 'wisef-logo.svg'));
      }
    });
  }

  /* ══════════════════════════════════════════════════════
     INIT
  ══════════════════════════════════════════════════════ */
  function init() {
    cacheOriginals();
    const initialTheme = document.documentElement.getAttribute('data-theme') || 'light';
    applyHeaderLogo(initialTheme);

    // Build header controls as a sibling of .nav (centered nav, controls on right)
    document.querySelectorAll('.header__inner').forEach((inner) => {
      if (inner.querySelector('.header-controls')) return;

      const container = document.createElement('div');
      container.className = 'header-controls';
      container.appendChild(buildToggle());
      container.appendChild(buildThemeToggle());

      // Remove legacy lang button inside nav if present
      inner.querySelectorAll('.nav__lang-btn').forEach((old) => old.remove());

      const mobile = inner.querySelector('.mobile-toggle');
      if (mobile) {
        inner.insertBefore(container, mobile);
      } else {
        inner.appendChild(container);
      }
    });

    if (lang === 'en') applyLang('en');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.wisefI18n = {
    t:       (key) => { const e = T[key]; return e ? (e[lang] || e.en) : key; },
    getLang: ()    => lang,
    setLang: applyLang,
  };

})();
