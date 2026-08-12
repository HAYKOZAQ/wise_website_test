/* ====================================================
   WISE Foundation — Language Switcher (i18n)
   Supports: Armenian (hy) ↔ English (en) ↔ Russian (ru)
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
    'nav.blog':       { hy: 'Նորություններ', en: 'News' },
    'nav.careers':    { hy: 'Կարիերա', en: 'Careers' },
    'nav.faq':        { hy: 'ՀՏՀ', en: 'FAQ' },

    /* Hero – Home */
    'home.badge':        { hy: '🌟 25 տարի տեխնոլոգիաների ոլորտում', en: '🌟 25 years in information technology' },
    'home.hero_h1a':     { hy: 'Մենք ստեղծում ենք', en: 'We Create' },
    'home.hero_h1b':     { hy: 'թվային լուծումներ', en: 'Digital Solutions' },
    'home.hero_p':       { hy: '«Բարեկեցության տեղեկատվական համակարգերի ձեռնարկություն» հիմնադրամ — Հայաստանում առաջատար տեխնոլոգիական կենտրոն՝ 25+ տարվա փորձով',
                           en: 'Welfare Information Systems Enterprise Foundation — Armenia\'s leading technology center with 25+ years of experience in government and private sector IT solutions' },
    'home.btn_services': { hy: 'Դիտել ծառայությունները', en: 'Our Services' },
    'home.btn_contact':  { hy: 'Կապնվել մեզ հետ', en: 'Contact Us' },
    'home.hero_title':   { hy: 'Թվային լուծումներ՝ հանուն մարդու բարեկեցության', en: 'Join us,<br>shape the digital solutions of the future' },
    'home.hero_presentation_text': { hy: 'Միասնական, մարդակենտրոն և վստահելի թվային միջավայր՝ յուրաքանչյուր քաղաքացու համար', en: 'We build trusted, accessible technology solutions for the public and private sectors that make people\'s lives easier.' },
    'home.hero_career':  { hy: 'Ուղարկել ինքնակենսագրություն', en: 'Send your CV' },
    'home.hero_about':   { hy: 'Իմանալ ավելին մեր մասին', en: 'Learn more about us' },
    'home.why_label':    { hy: 'Ինչու աշխատել WISE-ում', en: 'Why work at WISE' },
    'home.why_title':    { hy: 'Ի՞նչ ենք մենք առաջարկում', en: 'What we offer' },
    'home.why_text':     { hy: 'Աշխատանքը մեզ մոտ նշանակում է ազդեցություն, զարգացում և թիմ, որը տեսնում է մարդուն։', en: 'Working with us means impact, growth, and a team that sees people.' },
    'home.why_1_title':  { hy: 'Իմաստալից աշխատանք', en: 'Meaningful work' },
    'home.why_1_text':   { hy: 'Աշխատանք, որի արդյունքը փոխում է մարդկանց առօրյան և դարձնում ծառայությունները հասանելի։', en: 'Work whose results change people\'s everyday lives and make services accessible.' },
    'home.why_2_title':  { hy: 'Աճի հնարավորություններ', en: 'Growth opportunities' },
    'home.why_2_text':   { hy: 'Սովորում ենք միասին, աշխատում ենք բարդ խնդիրների վրա և զարգացնում ենք մասնագիտական ներուժը։', en: 'We learn together, solve complex problems, and grow professional potential.' },
    'home.why_3_title':  { hy: 'Մարդակենտրոն միջավայր', en: 'People-centered culture' },
    'home.why_3_text':   { hy: 'Թիմային մշակույթ, որտեղ կարծիքը լսելի է, իսկ փոխադարձ աջակցությունը՝ աշխատանքի հիմքում։', en: 'A team culture where opinions are heard and mutual support is at the core.' },
    'home.cta_title':    { hy: 'Ունե՞ք հարց, մեզ միանալու մասին', en: 'Have a question about joining us?' },
    'home.cta_text':     { hy: 'Գրեք մեզ, և կկապվենք Ձեզ հետ երկու աշխատանքային օրվա ընթացքում։', en: 'Write to us and we will get back to you within two working days.' },
    'home.cta_button':   { hy: 'Կապվել մեզ հետ', en: 'Contact us' },

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
    'about.presentation_label': { hy: 'Մեր մասին', en: 'About Us' },
    'about.presentation_title': { hy: '«Բարեկեցության տեղեկատվական համակարգերի ձեռնարկություն» հիմնադրամ', en: 'Welfare Information Systems Enterprise Foundation' },
    'about.presentation_lede': { hy: 'Հայաստանում առաջատար տեխնոլոգիական կենտրոն ենք, որը պետական և մասնավոր ոլորտի գործընկերների համար ստեղծում է տեղեկատվական և հեռահաղորդակցության ենթակառուցվածքներ։', en: 'We are a leading technology center in Armenia building information and telecommunications infrastructure for public and private sector partners.' },
    'about.stat_1':     { hy: 'ակտիվ շահառու ստանում է ծառայություններ մեր համակարգերի միջոցով', en: 'active beneficiaries receive services through our systems' },
    'about.stat_2':     { hy: 'սպասարկվող տեղեկատվական համակարգ ՀՀ սոցիալական պաշտպանության ոլորտում', en: 'information systems maintained in RA social protection' },
    'about.stat_3':     { hy: 'հիմնադրման տարեթիվ՝ ՀՀ կառավարության որոշմամբ', en: 'founded by decision of the RA Government' },
    'about.stat_4':     { hy: 'տարվա փորձ սոցիալական ոլորտի թվայնացման գործում', en: 'years of experience in digitalizing the social sector' },
    'about.story_label': { hy: 'Մեր պատմությունը', en: 'Our Story' },
    'about.story_title': { hy: 'Ի՞նչ ենք մենք անում', en: 'What we do' },
    'about.story_p1':   { hy: 'Հիմնադրամը ստեղծվել է 2001 թվականին՝ Հայաստանի Հանրապետության կառավարության որոշմամբ, և գործում է աշխատանքի ու սոցիալական հարցերի ոլորտում։', en: 'The Foundation was established in 2001 by a decision of the Government of the Republic of Armenia and operates in the field of labor and social affairs.' },
    'about.story_p2':   { hy: 'Մենք մշակում և ներդնում ենք թվային լուծումներ պետական մարմինների հետ համատեղ, կառուցում ենք տվյալների կառավարման համակարգեր, ծառայությունների թվայնացում և մարդկանց համար հասանելի միջավայր։', en: 'Together with state bodies we develop and implement digital solutions, build data management systems, digitalize services, and create accessible environments for people.' },
    'about.story_p3':   { hy: 'Մեր շահառուները Հայաստանի բոլոր քաղաքացիներն են։ Ավելի քան մեկ միլիոն ակտիվ շահառու ամեն օր օգտվում է մեր ստեղծած տեղեկատվական համակարգերի միջոցով մատուցվող ծառայություններից։', en: 'Our beneficiaries are all citizens of Armenia. More than one million active beneficiaries use services delivered through our information systems every day.' },
    'about.value_1_title': { hy: 'Ստեղծագործական մոտեցում', en: 'Creative approach' },
    'about.value_1_text':  { hy: 'Յուրաքանչյուր նախագծի համար գտնում ենք պարզ, կիրառելի և երկարաժամկետ լուծում։', en: 'We find simple, practical, and long-term solutions for every project.' },
    'about.value_2_title': { hy: 'Հստակ պահանջներ', en: 'Clear requirements' },
    'about.value_2_text':  { hy: 'Լսում ենք խնդիրն ամբողջությամբ, ձևակերպում ենք պահանջները և չափելի արդյունքը։', en: 'We listen to the whole problem and define requirements with measurable outcomes.' },
    'about.value_3_title': { hy: 'Չափելի ազդեցություն', en: 'Measurable impact' },
    'about.value_3_text':  { hy: 'Տվյալների, ծառայությունների և տեխնոլոգիաների միջոցով ստեղծում ենք իրական հանրային արժեք։', en: 'Through data, services, and technology we create real public value.' },
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
    'footer.blog':       { hy: 'Նորություններ', en: 'News' },
    'footer.faq':        { hy: 'Հաճախ տրվող հարցեր', en: 'FAQ' },
    'footer.careers':    { hy: 'Կարիերա', en: 'Careers' },
    'footer.contact_us': { hy: 'Հետադարձ կապ', en: 'Contact Us' },
    'footer.copyright':  { hy: '© 2026 Designed by «WISE» foundation', en: '© 2026 Designed by «WISE» foundation' },

    /* Blog page */
    'blog.pagetitle':  { hy: 'Նորություններ', en: 'News' },
    'blog.breadcrumb': { hy: 'Գլխավոր / Նորություններ', en: 'Home / News' },
    'blog.readmore':   { hy: 'Կարդալ ավելին', en: 'Read More' },
    'blog.loading':    { hy: 'Բեռնվում է...', en: 'Loading...' },
    'blog.close':      { hy: 'Փակել', en: 'Close' },
    'blog.open_orig':  { hy: 'Բացել օրիգինալ էջում', en: 'Open Original Article' },
    'blog.search_ph':  { hy: 'Որոնել հոդվածներ...', en: 'Search articles...' },
    'blog.featured_date': { hy: 'Հուլիս 24, 2024', en: 'July 24, 2024' },
    'blog.featured_title':{ hy: 'Պատրաստ է գործարկման «Աշխատանք առանց սահմանների» որոնման միասնական համակարգ»-ը', en: '"Work Without Borders" Unified Search System Launched' },
    'blog.featured_text': { hy: '«Աշխատանքի էլեկտրոնային բորսա» ծրագրի ֆինանսական աուդիտի հաշվետվությունները', en: 'Financial audit reports of the Electronic Labor Exchange program' },
    'blog.news_title':  { hy: 'Նորություններ և հայտարարություններ', en: 'News & Announcements' },
    'blog.empty':       { hy: 'Առայժմ հայտարարություններ չկան։', en: 'No announcements yet.' },
    'blog.news_text':   { hy: 'Մեր համակարգերի, ծրագրերի և թիմի կյանքի մասին թարմ տեղեկություններ։', en: 'Fresh updates about our systems, programs, and team.' },
    'blog.news_badge':  { hy: 'Լրահոս', en: 'News' },

    /* Services page */
    'svcpage.pagetitle':  { hy: 'Ծառայություններ', en: 'Services' },
    'svcpage.breadcrumb': { hy: 'Գլխավոր / Ծառայություններ', en: 'Home / Services' },
    'svc.badge': { hy: 'Ինչ ենք մենք անում', en: 'What We Do' },
    'svc.services_title': { hy: 'Ինչ ենք մենք առաջարկում', en: 'What We Offer' },
    'svc.text': { hy: 'Մենք ստեղծում ենք արդիական, չկրկնվող և նորարար լուծումներ', en: 'We create modern, unique, and innovative solutions' },
    'svc.cta_title': { hy: 'Կառուցե՞նք Ձեր հաջորդ թվային լուծումը', en: 'Let\'s build your next digital solution' },
    'svc.cta_text': { hy: 'Կպատմեք խնդրի մասին, իսկ մենք կառաջարկենք աշխատող մոտեցում։', en: 'Tell us about the problem and we will offer a working approach.' },
    'svc.cta_button': { hy: 'Կապվել մեզ հետ', en: 'Contact us' },
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
    'svc.projects_label': { hy: 'Մեր նախագծերը', en: 'Our Projects' },
    'svc.projects_title': { hy: 'Լուծումներ, որոնք աշխատում են մարդկանց համար', en: 'Solutions that work for people' },
    'svc.proj1_title': { hy: 'Տարեցների հերթագրման համակարգ', en: 'Elderly Queue Registration System' },
    'svc.proj2_title': { hy: 'Անապահովության գնահատման համակարգ', en: 'Vulnerability Assessment System' },
    'svc.proj3_title': { hy: 'Կենսաթոշակի հաշվիչ', en: 'Pension Calculator' },
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
    'partners.presentation_label': { hy: 'Գործընկերներ', en: 'Partners' },
    'partners.presentation_title': { hy: 'Ովքեր են վստահում մեզ', en: 'Who trusts us' },
    'partners.presentation_lede': { hy: 'Համագործակցում ենք պետական մարմինների, միջազգային կազմակերպությունների և առաջատար տեխնոլոգիական ընկերությունների հետ։', en: 'We collaborate with state bodies, international organizations, and leading technology companies.' },
    'partners.gov_title': { hy: 'Պետական մարմիններ', en: 'Government Institutions' },
    'partners.intl_title': { hy: 'Միջազգային կազմակերպություններ', en: 'International Organizations' },
    'partners.business_title': { hy: 'Կրթություն և բիզնես', en: 'Education & Business' },

    /* Contact page */
    'contactpage.pagetitle':  { hy: 'Հետադարձ կապ', en: 'Contact' },
    'contactpage.breadcrumb': { hy: 'Գլխավոր / Հետադարձ կապ', en: 'Home / Contact' },
    'contact.badge': { hy: 'Կապ', en: 'Contact' },
    'contact.hero_title': { hy: 'Ստեղծենք միասին', en: 'Let\'s Create Together' },
    'contact.hero_text': { hy: 'Պատրաստ ենք լսել Ձեր գաղափարները և առաջարկությունները', en: 'We are ready to hear your ideas and suggestions' },
    'contact.label': { hy: 'Կապնվել', en: 'Get In Touch' },
    'contact.title': { hy: 'Կապվեք մեզ հետ', en: 'Contact Us' },
    'contact.address': { hy: 'Հասցե', en: 'Address' },
    'contact.address_val': { hy: 'Երևան, Հայաստան', en: 'Yerevan, Armenia' },
    'contact.panel_title': { hy: 'Գրեք մեզ, և կպատասխանենք', en: 'Write to us and we will reply' },
    'contact.panel_text': { hy: 'Երկու աշխատանքային օրվա ընթացքում կկապվենք Ձեզ հետ։', en: 'We will get back to you within two working days.' },
    'contactpage.form_title': { hy: 'Գրել նամակ', en: 'Send a Message' },
    'contactpage.form_sub':   { hy: 'Լրացրեք ձևը և մենք կպատասխանենք առաջիկա օրերին', en: 'Fill in the form and we will respond within the next few days' },
    'contactpage.name_lbl':   { hy: 'Անուն', en: 'Name' },
    'contactpage.email_lbl':  { hy: 'Էլ. փոստ', en: 'Email' },
    'contactpage.subj_lbl':   { hy: 'Թեմա', en: 'Subject' },
    'contactpage.msg_lbl':    { hy: 'Հաղորդագրություն', en: 'Message' },
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
    'chat.err_no_api':     { hy: 'Արտադրական կայքում AI-ն աշխատելու համար տեղադրեք backend-ը (Hugging Face կամ Render) և լրացրեք API հասցեն build-ի WISEF_API_BASE փոփոխականով։ Տե՛ս DEPLOY.md։', en: 'To use AI on the live site, deploy the backend (Hugging Face or Render) and set WISEF_API_BASE during the frontend build. See DEPLOY.md.' },
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

    /* FAQ page */
    'faq.eyebrow':     { hy: 'Հաճախ տրվող հարցեր', en: 'Frequently Asked Questions' },
    'faq.title':       { hy: 'Ինչ են մեզ հարցնում', en: 'What people ask us' },
    'faq.lede':        { hy: 'Պատասխաններ ամենահաճախ հնչող հարցերին մեր գործունեության, ծառայությունների և կարիերայի մասին։', en: 'Answers to the most common questions about our work, services, and careers.' },
    'faq.q1':          { hy: 'Որո՞նք են ձեր հիմնական գործունեության ուղղությունները', en: 'What are your main areas of activity?' },
    'faq.a1':          { hy: 'Մենք նախագծում, սպասարկում և զարգացնում ենք տեղեկատվական համակարգեր սոցիալական պաշտպանության ոլորտի համար, մշակում և վերլուծում ենք տվյալներ, իրականացնում ենք կրթական ծրագրեր և ապահովում կիբեռանվտանգություն։', en: 'We design, maintain, and develop information systems for the social protection sector, process and analyze data, run educational programs, and ensure cybersecurity.' },
    'faq.q2':          { hy: 'Ինչպե՞ս կարող եմ դառնալ ձեր գործընկերը', en: 'How can I become your partner?' },
    'faq.a2':          { hy: 'Գրեք մեզ հետադարձ կապի էջի միջոցով՝ նշելով Ձեր կազմակերպությունը և համագործակցության առաջարկը։ Մեր թիմը կապվելու է Ձեզ հետ երկու աշխատանքային օրվա ընթացքում։', en: 'Write to us via the contact page with your organization and proposal. Our team will get back to you within two working days.' },
    'faq.q3':          { hy: 'Ինչպե՞ս կարող եմ միանալ ձեր թիմին', en: 'How can I join your team?' },
    'faq.a3':          { hy: 'Կարիերա էջում հրապարակում ենք թափուր հաստիքները։ Կարող եք նաև ուղարկել Ձեր ինքնակենսագրությունը՝ նշելով հետաքրքրող մասնագիտությունը, և մենք կքննարկենք այն առկա հնարավորությունների հետ։', en: 'Open positions are published on the Careers page. You can also send your CV with your area of interest and we will consider it for current opportunities.' },
    'faq.q4':          { hy: 'Ո՞ւմ են սպասարկում ձեր տեղեկատվական համակարգերը', en: 'Who uses your information systems?' },
    'faq.a4':          { hy: 'Մեր համակարգերը սպասարկում են ՀՀ քաղաքացիներին՝ սոցիալական ծառայությունների, զբաղվածության և այլ ոլորտների գործընթացները դարձնելով հասանելի և թափանցիկ։', en: 'Our systems serve citizens of Armenia, making social services, employment, and other processes accessible and transparent.' },
    'faq.q5':          { hy: 'Ինչպե՞ս եք ապահովում տվյալների անվտանգությունը', en: 'How do you ensure data security?' },
    'faq.a5':          { hy: 'Տվյալների անվտանգությունը մեր ամենօրյա աշխատանքի մասն է. մշտապես թարմացնում ենք պաշտպանական մեխանիզմները, իրականացնում ենք աուդիտ և վերապատրաստում թիմի համար։', en: 'Data security is part of our daily work: we constantly update protection mechanisms, conduct audits, and train our team.' },
    'faq.cta_title':   { hy: 'Չեք գտե՞լ Ձեր հարցի պատասխանը', en: 'Didn\'t find an answer to your question?' },
    'faq.cta_text':    { hy: 'Կապվեք մեզ հետ, և մենք կպատասխանենք։', en: 'Contact us and we will answer.' },
    'faq.cta_button':  { hy: 'Կապվել մեզ հետ', en: 'Contact us' },

    /* Careers page */
    'careers.eyebrow':     { hy: 'Կարիերա', en: 'Careers' },
    'careers.title':       { hy: 'Աշխատանք, որը փոխում է կյանքեր', en: 'Work that changes lives' },
    'careers.lede':        { hy: 'Յուրաքանչյուր համակարգ, որը մենք կառուցում ենք, օգնում է հազարավոր մարդկանց հասանելիություն ստանալ ծառայություններին։', en: 'Every system we build helps thousands of people gain access to services.' },
    'careers.openings_link': { hy: 'Տեսնել թափուր տեղերը', en: 'See open positions' },
    'careers.openings_label': { hy: 'Թափուր հաստիքներով', en: 'Open Positions' },
    'careers.openings_title': { hy: 'Մենք փնտրում ենք', en: 'Current openings' },
    'careers.job1_title':  { hy: 'Full Stack Developer', en: 'Full Stack Developer' },
    'careers.job1_meta':   { hy: 'Երևան · Լրիվ դրույք', en: 'Yerevan · Full-time' },
    'careers.job1_text':   { hy: 'Մենք փնտրում ենք փորձառու Full Stack մշակող՝ մեր սոցիալական ծառայությունների նախագծերի համար։', en: 'We are looking for an experienced Full Stack developer for our social services projects.' },
    'careers.job2_title':  { hy: 'UI/UX Designer', en: 'UI/UX Designer' },
    'careers.job2_meta':   { hy: 'Երևան · Լրիվ դրույք', en: 'Yerevan · Full-time' },
    'careers.job2_text':   { hy: 'Դիզայներ, որը մարդկանց համար կդարձնի հանրային ծառայությունները պարզ և հաճելի։', en: 'A designer who will make public services simple and pleasant for people.' },
    'careers.job3_title':  { hy: 'QA Engineer', en: 'QA Engineer' },
    'careers.job3_meta':   { hy: 'Երևան · Լրիվ դրույք', en: 'Yerevan · Full-time' },
    'careers.job3_text':   { hy: 'Մեր համակարգերի որակի և հուսալիության պատասխանատու՝ ավտոմատացված և մեխանիկական թեստավորում։', en: 'Responsible for the quality and reliability of our systems through automated and manual testing.' },
    'careers.apply':       { hy: 'Դիմել', en: 'Apply' },
    'careers.cv_title':    { hy: 'Չեք գտե՞լ Ձեզ հարմար հաստիք', en: 'No position that fits?' },
    'careers.cv_text':     { hy: 'Ուղարկեք Ձեր ինքնակենսագրությունը, և կապվելու ենք առկա հնարավորությունների շրջանակում։', en: 'Send your CV and we will reach out within current opportunities.' },
    'careers.cv_button':   { hy: 'Ուղարկել ինքնակենսագրություն', en: 'Send your CV' },

    /* Page titles */
    'site.title.home':     { hy: 'WISE Foundation — «Բարեկեցության տեղեկատվական համակարգերի ձեռնարկություն» հիմնադրամ', en: 'WISE Foundation — Welfare Information Systems Enterprise Foundation' },
    'site.title.about':    { hy: 'Մեր մասին — WISE Foundation', en: 'About Us — WISE Foundation' },
    'site.title.services': { hy: 'Ծառայություններ — WISE Foundation', en: 'Services — WISE Foundation' },
    'site.title.partners': { hy: 'Գործընկերներ — WISE Foundation', en: 'Partners — WISE Foundation' },
    'site.title.contact':  { hy: 'Հետադարձ կապ — WISE Foundation', en: 'Contact Us — WISE Foundation' },
    'site.title.blog':     { hy: 'Նորություններ — WISE Foundation', en: 'News — WISE Foundation' },
    'site.title.faq':      { hy: 'Հաճախ տրվող հարցեր — WISE Foundation', en: 'FAQ — WISE Foundation' },
    'site.title.careers':  { hy: 'Կարիերա — WISE Foundation', en: 'Careers — WISE Foundation' },

    /* Meta descriptions */
    'site.desc.home':     { hy: 'WISE Foundation — 25 տարի տեղեկատվական տեխնոլոգիաների ոլորտում: Մենք ստեղծում ենք թվային լուծումներ:', en: 'WISE Foundation — 25 years in information technology. We create digital solutions for government and private sector.' },
    'site.desc.about':    { hy: 'Իմացեք ավելին WISE Foundation-ի մասին՝ 25 տարվա փորձ տեղեկատվական տեխնոլոգիաների ոլորտում:', en: 'Learn more about WISE Foundation — 25 years of experience in information technology.' },
    'site.desc.services': { hy: 'WISE Foundation-ի ծառայություններ՝ տեղեկատվական համակարգերի նախագծում, կիբեռանվտանգություն, տվյալների մշակում և ավելին:', en: 'WISE Foundation services — information systems design, cybersecurity, data processing and more.' },
    'site.desc.partners': { hy: 'WISE Foundation-ի գործընկերներ՝ պետական հաստատություններ, միջազգային կազմակերպություններ, բանկեր:', en: 'WISE Foundation partners — government institutions, international organizations, banks.' },
    'site.desc.contact':  { hy: 'Կապվեք WISE Foundation-ի հետ: Էլ. փոստ, հեռախոս, կոնտակտային ձև:', en: 'Contact WISE Foundation. Email, phone, contact form.' },
    'site.desc.blog':     { hy: 'WISE Foundation-ի բլոգ՝ նորություններ, հոդվածներ և հայտարարություններ տեղեկատվական տեխնոլոգիաների ոլորտում:', en: 'WISE Foundation blog — news, articles and announcements in information technology.' },
    'site.desc.faq':      { hy: 'Պատասխաններ WISE Foundation-ի ծառայությունների, կարիերայի և համագործակցության վերաբերյալ հաճախ տրվող հարցերին։', en: 'Answers to frequently asked questions about WISE Foundation services, careers, and cooperation.' },
    'site.desc.careers':  { hy: 'Աշխատեք WISE Foundation-ում. թափուր հաստիքներ, թիմ, մշակույթ և ինքնակենսագրություն ուղարկելու հնարավորություն։', en: 'Work at WISE Foundation. Open positions, team, culture, and the ability to submit your CV.' }
  };

  /* ══════════════════════════════════════════════════════
     RUSSIAN (ru) — translations override T for lang='ru'
  ══════════════════════════════════════════════════════ */
  const RU = {
    'nav.home': 'Главная',
    'nav.about': 'О нас',
    'nav.services': 'Услуги',
    'nav.partners': 'Партнёры',
    'nav.contact': 'Контакты',
    'nav.blog': 'Новости',
    'nav.careers': 'Карьера',
    'nav.faq': 'Вопросы и ответы',

    'home.badge': '🌟 25 лет в сфере информационных технологий',
    'home.hero_h1a': 'Мы создаём',
    'home.hero_h1b': 'цифровые решения',
    'home.hero_p': 'Фонд «Предприятие информационных систем благосостояния» — ведущий технологический центр Армении с опытом более 25 лет в сфере ИТ',
    'home.btn_services': 'Наши услуги',
    'home.btn_contact': 'Связаться с нами',
    'home.hero_title': 'Цифровые решения для благополучия человека',
    'home.hero_presentation_text': 'Единая, человекоцентричная и надёжная цифровая среда для каждого гражданина',
    'home.hero_career': 'Отправить резюме',
    'home.hero_about': 'Узнать больше о нас',
    'home.why_label': 'Почему работать в WISE',
    'home.why_title': 'Что мы предлагаем',
    'home.why_text': 'Работа у нас — это влияние, развитие и команда, которая видит человека.',
    'home.why_1_title': 'Осмысленная работа',
    'home.why_1_text': 'Работа, результат которой меняет повседневную жизнь людей и делает услуги доступными.',
    'home.why_2_title': 'Возможности роста',
    'home.why_2_text': 'Мы учимся вместе, решаем сложные задачи и развиваем профессиональный потенциал.',
    'home.why_3_title': 'Человекоцентричная среда',
    'home.why_3_text': 'Командная культура, где мнение слышат, а взаимная поддержка — основа работы.',
    'home.cta_title': 'Есть вопрос о присоединении к нам?',
    'home.cta_text': 'Напишите нам, и мы свяжемся с вами в течение двух рабочих дней.',
    'home.cta_button': 'Связаться с нами',

    'why.label': 'Наши направления',
    'why.title': 'Мечтайте, создавайте, делитесь с нами',
    'why.subtitle': 'Вместе строим цифровое будущее',
    'why.c1_title': 'Мечтайте с нами',
    'why.c1_text': 'Мечтайте с нами об инновациях и цифровом будущем',
    'why.c2_title': 'Создавайте с нами',
    'why.c2_text': 'Создавайте с нами инновационные цифровые решения',
    'why.c3_title': 'Делитесь с нами',
    'why.c3_text': 'Делитесь с нами мечтами о совершенствовании цифрового будущего',

    'svc.label': 'Услуги',
    'svc.title': 'Наши услуги',
    'svc.subtitle': 'Проектирование и обслуживание информационных систем, новых программ и баз данных',
    'svc.s1_title': 'Проектирование и обслуживание ИС',
    'svc.s1_text': 'Полный цикл проектирования и обслуживания информационных систем, программного обеспечения и баз данных',
    'svc.s2_title': 'Обработка данных',
    'svc.s2_text': 'Контентное обслуживание, обработка и анализ данных информационных систем',
    'svc.s3_title': 'Образовательные программы',
    'svc.s3_text': 'Проектирование и реализация образовательных программ в сфере ИТ',
    'svc.s4_title': 'Кибербезопасность',
    'svc.s4_text': 'Кибербезопасность и сетевое обеспечение',
    'svc.s5_title': 'Техническое обслуживание',
    'svc.s5_text': 'Обслуживание компьютеров и сопутствующей техники (13 000+ единиц)',
    'svc.s6_title': 'Интеграционные решения',
    'svc.s6_text': 'Интеграция систем и обеспечение обмена данными',
    'svc.btn_all': 'Все услуги',

    'stats.label': 'Наши достижения',
    'stats.title': '25 лет в сфере информационных технологий',
    'stats.s1': 'Лет в сфере технологий',
    'stats.s2': 'Активных бенефициаров',
    'stats.s3': 'Спроектировано информационных систем',
    'stats.s4': 'Обслуживаемое оборудование',

    'aboutprev.label': 'О нас',
    'aboutprev.title': 'Фонд «Предприятие информационных систем благосостояния»',
    'aboutprev.p1': 'Мы основаны в 2001 году по решению Правительства Республики Армения и действуем при Министерстве труда и социальных вопросов.',
    'aboutprev.p2': 'Ведущий технологический центр Армении, внедряющий и обслуживающий информационно-телекоммуникационную инфраструктуру государственного и частного секторов.',
    'aboutprev.btn': 'Узнать больше',

    'contactprev.label': 'Контакты',
    'contactprev.title': 'Создадим вместе',
    'contactprev.sub': 'Мы готовы выслушать ваши идеи',
    'contactprev.email': 'Эл. почта',
    'contactprev.phone': 'Телефон',
    'contactprev.btn': 'Отправить сообщение',

    'about.pagetitle': 'О нас',
    'about.presentation_label': 'О нас',
    'about.presentation_title': 'Фонд «Предприятие информационных систем благосостояния»',
    'about.presentation_lede': 'Мы — ведущий технологический центр Армении, создающий информационную и телекоммуникационную инфраструктуру для государственных и частных партнёров.',
    'about.stat_1': 'активных бенефициаров получают услуги через наши системы',
    'about.stat_2': 'обслуживаемых информационных систем в сфере социальной защиты РА',
    'about.stat_3': 'год основания — по решению Правительства РА',
    'about.stat_4': 'лет опыта в цифровизации социальной сферы',
    'about.story_label': 'Наша история',
    'about.story_title': 'Чем мы занимаемся',
    'about.story_p1': 'Фонд основан в 2001 году по решению Правительства Республики Армения и действует в сфере труда и социальных вопросов.',
    'about.story_p2': 'Вместе с государственными органами мы разрабатываем и внедряем цифровые решения, создаём системы управления данными, цифровизируем услуги и делаем их доступными для людей.',
    'about.story_p3': 'Наши бенефициары — все граждане Армении. Более миллиона активных бенефициаров ежедневно пользуются услугами, предоставляемыми через созданные нами информационные системы.',
    'about.value_1_title': 'Творческий подход',
    'about.value_1_text': 'Для каждого проекта находим простое, применимое и долгосрочное решение.',
    'about.value_2_title': 'Чёткие требования',
    'about.value_2_text': 'Выслушиваем проблему целиком, формулируем требования и измеримый результат.',
    'about.value_3_title': 'Измеримое влияние',
    'about.value_3_text': 'Через данные, услуги и технологии создаём реальную общественную ценность.',
    'about.exp_label': '25 лет опыта',
    'about.exp_title': 'Мы мечтаем, создаём и делимся',
    'about.exp_p1': 'Фонд «Предприятие информационных систем благосостояния» — ведущий технологический центр Армении, осуществляющий внедрение и обслуживание информационно-телекоммуникационной инфраструктуры государственного и частного секторов.',
    'about.exp_p2': 'Около 1 109 493 активных бенефициаров получают услуги в сфере социальной защиты РА через предоставленные нами информационные системы.',
    'about.way_label': 'История',
    'about.way_title': 'Наш путь',
    'about.t1_title': 'Основание',
    'about.t1_text': 'По решению Правительства РА создан фонд, действующий при Министерстве труда и социальных вопросов.',
    'about.t2_title': 'Развитие и расширение',
    'about.t2_text': 'Спроектированы и развиты 23 информационные системы, действующие в сфере социальной защиты РА.',
    'about.t3_title': 'Новые горизонты',
    'about.t3_text': 'Продолжаем внедрение инновационных решений и расширение международного сотрудничества.',
    'about.t4_title': 'Сегодня',
    'about.t4_text': '25+ лет в сфере информационных технологий, 1 000 000+ активных бенефициаров.',
    'about.val_label': 'Ценности',
    'about.val_title': 'Наш подход',
    'about.val1_title': 'ТВОРЧЕСКИЙ ПОДХОД К КАЖДОМУ ПРОЕКТУ',
    'about.val1_text': 'Творческий подход к каждому проекту',
    'about.val2_title': 'ЧЁТКОЕ ОПРЕДЕЛЕНИЕ ТРЕБОВАНИЙ',
    'about.val2_text': 'Чёткое определение требований',
    'about.val3_title': 'ТОЧНОЕ ПЛАНИРОВАНИЕ И КОНТРОЛЬ',
    'about.val3_text': 'Точное планирование и контроль',
    'about.val4_title': 'ЭФФЕКТИВНОЕ УПРАВЛЕНИЕ',
    'about.val4_text': 'Эффективное управление для обеспечения качества',
    'about.val5_title': 'ВИДЕНИЕ ДИСТАНЦИОННОГО РАЗВИТИЯ',
    'about.val5_text': 'Видение дистанционного развития',
    'about.val6_title': 'ОПЕРАЦИОННАЯ ПОДДЕРЖКА И КОНСУЛЬТИРОВАНИЕ',
    'about.val6_text': 'Операционная поддержка и консультирование',
    'about.num_label': 'Наши достижения',
    'about.num_title': 'В цифрах',
    'about.num_stat3': 'Официальных сайтов',

    'footer.brand': 'Фонд «Предприятие информационных систем благосостояния»',
    'footer.site': 'Сайт',
    'footer.contact': 'Контакты',
    'footer.follow': 'Следите за нами',
    'footer.home': 'Главная',
    'footer.about': 'О нас',
    'footer.services': 'Услуги',
    'footer.partners': 'Партнёры',
    'footer.blog': 'Новости',
    'footer.faq': 'Часто задаваемые вопросы',
    'footer.careers': 'Карьера',
    'footer.contact_us': 'Связаться с нами',
    'footer.copyright': '© 2026 Разработано фондом «WISE»',

    'blog.pagetitle': 'Новости',
    'blog.breadcrumb': 'Главная / Новости',
    'blog.readmore': 'Читать далее',
    'blog.loading': 'Загрузка...',
    'blog.close': 'Закрыть',
    'blog.open_orig': 'Открыть оригинальную статью',
    'blog.search_ph': 'Поиск статей...',
    'blog.featured_date': '24 июля 2024',
    'blog.featured_title': 'Запущена единая поисковая система «Работа без границ»',
    'blog.featured_text': 'Финансовые отчёты аудита программы «Электронная биржа труда»',
    'blog.news_title': 'Новости и объявления',
    'blog.empty': 'Пока нет объявлений.',
    'blog.news_text': 'Свежие новости о наших системах, программах и команде.',
    'blog.news_badge': 'Новости',

    'svcpage.pagetitle': 'Услуги',
    'svcpage.breadcrumb': 'Главная / Услуги',
    'svc.badge': 'Чем мы занимаемся',
    'svc.services_title': 'Что мы предлагаем',
    'svc.text': 'Мы создаём современные, уникальные и инновационные решения',
    'svc.cta_title': 'Построим ваше следующее цифровое решение?',
    'svc.cta_text': 'Расскажите о проблеме, и мы предложим работающий подход.',
    'svc.cta_button': 'Связаться с нами',
    'svc.offers_title': 'Что мы предлагаем',
    'svc.s1_full_title': 'Проектирование и обслуживание информационных систем',
    'svc.s1_full_text': 'Полный цикл проектирования и обслуживания информационных систем, программного обеспечения и баз данных.',
    'svc.s2_full_title': 'Контентное обслуживание информационных систем',
    'svc.s2_full_text': 'Обработка и анализ данных, контентная поддержка информационных систем.',
    'svc.s3_full_title': 'Обработка и анализ данных',
    'svc.s3_full_text': 'Сбор, обработка, анализ данных и подготовка отчётов.',
    'svc.s4_full_title': 'Проектирование и реализация образовательных программ',
    'svc.s4_full_text': 'Разработка и реализация образовательных программ в сфере ИТ.',
    'svc.s5_full_title': 'Кибербезопасность и сетевое обеспечение',
    'svc.s5_full_text': 'Обеспечение информационной безопасности и защита сетевой инфраструктуры.',
    'svc.s6_full_title': 'Техническое обслуживание',
    'svc.s6_full_text': 'Обслуживание компьютеров и сопутствующей техники, 13 000+ единиц оборудования.',
    'svc.projects_label': 'Наши проекты',
    'svc.projects_title': 'Решения, которые работают для людей',
    'svc.proj1_title': 'Система записи пожилых граждан',
    'svc.proj2_title': 'Система оценки уязвимости',
    'svc.proj3_title': 'Пенсионный калькулятор',
    'svc.p1_title': 'Система оценки уязвимости семьи',
    'svc.p1_text': 'Автоматизированная система оценки социального статуса семей и программ поддержки.',
    'svc.p2_title': 'ИС быстрого социального реагирования',
    'svc.p2_text': 'Платформа, разработанная в 2020 году в условиях военного положения для быстрой социальной поддержки.',
    'svc.p3_title': 'ИС обмена данными',
    'svc.p3_text': 'Система обмена данными информационных систем сферы социальной защиты РА.',
    'svc.p4_title': 'ИС занятости «Горц»',
    'svc.p4_text': 'Автоматизированная система бизнес-процессов в сфере занятости РА.',
    'svc.p5_title': 'ИС протезно-ортопедических изделий',
    'svc.p5_text': 'Автоматизация выдачи сертификатов на получение вспомогательных средств.',
    'svc.p6_title': 'ИС учёта детей «Манук»',
    'svc.p6_text': 'Система учёта детей в трудной жизненной ситуации и усыновления.',
    'svc.p7_title': 'ИС учёта случаев семейного насилия',
    'svc.p7_text': 'Централизованная система учёта случаев семейного насилия.',
    'svc.p8_title': 'ИС жилищного обеспечения перемещённых семей',
    'svc.p8_text': 'Система управления государственной программой жилищного обеспечения семей, перемещённых из Нагорного Карабаха.',
    'svc.p9_title': 'Платформа срочного реагирования',
    'svc.p9_text': 'www.hratapkariq.am — платформа срочного социального реагирования.',
    'svc.p10_title': 'ИС аттестации госслужащих',
    'svc.p10_text': 'ИС анкет аттестации государственных служащих (2010 г.).',
    'svc.p11_title': 'ИС приёмных комплексных социальных служб',
    'svc.p11_text': 'Единая система регистрации обращений в территориальных органах.',
    'svc.p12_title': 'ИС учёта пожилых и инвалидов',
    'svc.p12_text': 'Учёт пожилых и инвалидов в программах социальной защиты.',
    'svc.p13_title': 'ИС учёта инвалидов «Пюник»',
    'svc.p13_text': 'Система учёта данных и решений лиц, обратившихся за установлением инвалидности.',
    'svc.p14_title': 'ИС учёта благотворительных программ',
    'svc.p14_text': 'ИС с 3 подсистемами: программы, потребности и получение помощи.',
    'svc.p15_title': 'ИС социального жилищного фонда',
    'svc.p15_text': 'ИС учёта жилья и формирования очереди (2014 г.).',
    'svc.p16_title': 'ИС ведения социального дела',
    'svc.p16_text': 'Автоматизация процесса ведения социального дела от обращения до обработки данных членов семьи.',
    'svc.p17_title': 'ИС компенсации вкладов Сбербанка СССР',
    'svc.p17_text': 'Автоматизированная система компенсации денежных вкладов, внесённых до 10.06.1993 г.',
    'svc.p18_title': 'ИС оценки уязвимости семей «Нпаст»',
    'svc.p18_text': 'Автоматизированная система расчёта балла уязвимости семей.',

    'svc.details_label': 'Детали услуг',
    'svc.details_title': 'Что мы предоставляем',
    'svc.sd1_title': 'Проектирование и обслуживание информационных систем',
    'svc.sd1_intro': 'Методология управления ИТ-проектами: PMBoK, Agile',
    'svc.sd1_l1': 'Back-End разработка: PHP, C# ASP.NET WCF (Yii, React)',
    'svc.sd1_l2': 'Базы данных: MySQL, PostgreSQL, Oracle',
    'svc.sd1_l3': 'Front-End: HTML/CSS/JS (Bootstrap)',
    'svc.sd2_title': 'Контентное обслуживание информационных систем',
    'svc.sd2_text': 'Обработка и анализ данных, контентная поддержка систем с контролем качества.',
    'svc.sd3_title': 'Обработка и анализ данных',
    'svc.sd3_text': 'Сбор, обработка, анализ данных и подготовка отчётов для государственных органов.',
    'svc.sd4_title': 'Проектирование и реализация образовательных программ',
    'svc.sd4_text': 'Обучение работе с информационными системами, используемыми при предоставлении социальных услуг.',
    'svc.sd5_title': 'Кибербезопасность и сетевое обеспечение',
    'svc.sd5_text': 'Обеспечение информационной безопасности и защита сетевой инфраструктуры.',
    'svc.sd6_title': 'Обслуживание компьютеров и сопутствующей техники',
    'svc.sd6_text': 'Диагностика, установка, настройка программного обеспечения, построение сетей: 13 000+ единиц.',
    'svc.loading': 'Загрузка...',
    'svc.contact_about': 'Связаться по этому проекту',

    'partners.pagetitle': 'Партнёры',
    'partners.breadcrumb': 'Главная / Партнёры',
    'part.partners_title': 'Мы сотрудничаем',
    'part.partners_subtitle': 'Государственные учреждения, международные организации, финансовые институты и ИТ-компании',
    'partners.presentation_label': 'Партнёры',
    'partners.presentation_title': 'Кто нам доверяет',
    'partners.presentation_lede': 'Мы сотрудничаем с государственными органами, международными организациями и ведущими технологическими компаниями.',
    'partners.gov_title': 'Государственные органы',
    'partners.intl_title': 'Международные организации',
    'partners.business_title': 'Образование и бизнес',

    'contactpage.pagetitle': 'Контакты',
    'contactpage.breadcrumb': 'Главная / Контакты',
    'contact.badge': 'Контакты',
    'contact.hero_title': 'Создадим вместе',
    'contact.hero_text': 'Мы готовы выслушать ваши идеи и предложения',
    'contact.label': 'Связаться',
    'contact.title': 'Свяжитесь с нами',
    'contact.address': 'Адрес',
    'contact.address_val': 'Ереван, Армения',
    'contact.panel_title': 'Напишите нам, и мы ответим',
    'contact.panel_text': 'Мы свяжемся с вами в течение двух рабочих дней.',
    'contactpage.form_title': 'Отправить сообщение',
    'contactpage.form_sub': 'Заполните форму, и мы ответим в ближайшие дни',
    'contactpage.name_lbl': 'Имя',
    'contactpage.email_lbl': 'Эл. почта',
    'contactpage.subj_lbl': 'Тема',
    'contactpage.msg_lbl': 'Сообщение',
    'contactpage.name_ph': 'Ваше имя',
    'contactpage.email_ph': 'Ваша электронная почта',
    'contactpage.subj_ph': 'Тема',
    'contactpage.msg_ph': 'Ваше сообщение',
    'contactpage.send_btn': 'Отправить',

    'part.p1': 'Правительство РА',
    'part.p2': 'Служба национальной безопасности',
    'part.p3': 'Национальный институт труда и социальных исследований',
    'part.p4': 'Полиция РА',
    'part.p5': 'Айпост',
    'part.p6': 'Юком',
    'part.p7': 'UNFPA',
    'part.p8': 'Американский университет Армении',
    'part.p9': 'USAID',
    'part.p10': 'WFP',
    'part.p11': 'UITE',
    'part.p12': 'IBM',
    'part.p13': 'Microsoft',
    'part.p14': 'Всемирный банк',
    'part.p15': 'Америабанк',
    'part.p16': 'Эвокабанк',
    'part.p17': 'Акба банк',
    'part.p18': 'Конверс банк',
    'part.p19': 'Юнибанк',
    'part.p20': 'Ардшинбанк',
    'part.p21': 'Комитет государственных доходов',
    'part.p22': 'Единая социальная служба',
    'part.p23': 'Международный центр науки и технологий',
    'part.p24': 'Фонд инкубатор предприятий',
    'part.p25': 'ID Bank',
    'part.p26': 'Библос банк',
    'part.p27': 'Меллат банк',
    'part.p28': 'Инекобанк',
    'part.p29': 'Хайбизнесбанк',
    'part.p30': 'Хайэкнембанк',
    'part.p31': 'ВТБ Банк',
    'part.p32': 'Credo Finance UCO',
    'part.p33': 'Mogo UCO',
    'part.p34': 'Aregak UCO',
    'part.p35': 'Росгосстрах',
    'part.p36': 'Armenia Insurance',
    'part.p37': 'Global Credit',
    'part.p38': 'Norman Credit',
    'part.p39': 'SEF International',
    'part.p40': 'Finca',
    'part.p41': 'Araratbank',
    'part.p42': 'KAMURJ UCO',
    'part.p43': 'Ростелеком',

    'chat.fab': 'Спросите нас',
    'chat.title': 'Социальный помощник',
    'chat.placeholder': 'Например, возрастная пенсия',
    'chat.welcome_title': 'Здравствуйте',
    'chat.welcome': 'Спрашивайте о пособиях, пенсиях и социальных программах. Ответы основаны на официальной информации.',
    'chat.topics_label': 'Выберите тему или напишите вопрос',
    'chat.disclaimer': 'Информационно · Официальные решения: 114',
    'chat.err_offline': 'Сейчас не могу ответить. Проверьте, что сервер работает (start_backend.bat или облачный API).',
    'chat.err_no_api': 'Для работы ИИ на сайте разверните backend (Hugging Face или Render) и укажите адрес API при сборке через WISEF_API_BASE. См. DEPLOY.md.',
    'chat.status_ready': 'Готов помочь',
    'chat.status_offline': 'Сервер отключён',
    'chat.thinking': 'Думаю…',
    'chat.sources_label': 'Источники',
    'chat.new': 'Новый чат',
    'chat.q1': 'Пособие на ребёнка до 2 лет',
    'chat.q2': 'Единовременное пособие при рождении ребёнка',
    'chat.q3': 'Семейное пособие',
    'chat.q4': 'Возрастная пенсия',
    'chat.q5': 'Пенсия по инвалидности',
    'chat.q9': 'Поддержка перемещённых лиц',
    'chat.q10': 'Оценка функциональности / инвалидность',
    'chat.q6': 'Статус безработного',
    'chat.q7': 'Компенсация за электроэнергию',
    'chat.q8': 'Горячая линия МСС 114',

    'faq.eyebrow': 'Часто задаваемые вопросы',
    'faq.title': 'Что нас спрашивают',
    'faq.lede': 'Ответы на самые частые вопросы о нашей деятельности, услугах и карьере.',
    'faq.q1': 'Каковы ваши основные направления деятельности?',
    'faq.a1': 'Мы проектируем, обслуживаем и развиваем информационные системы для сферы социальной защиты, обрабатываем и анализируем данные, реализуем образовательные программы и обеспечиваем кибербезопасность.',
    'faq.q2': 'Как я могу стать вашим партнёром?',
    'faq.a2': 'Напишите нам через страницу контактов, указав вашу организацию и предложение о сотрудничестве. Наша команда свяжется с вами в течение двух рабочих дней.',
    'faq.q3': 'Как я могу присоединиться к вашей команде?',
    'faq.a3': 'Открытые вакансии публикуются на странице «Карьера». Вы также можете отправить резюме с указанием интересующей специальности, и мы рассмотрим его в рамках имеющихся возможностей.',
    'faq.q4': 'Кто пользуется вашими информационными системами?',
    'faq.a4': 'Наши системы обслуживают граждан РА, делая процессы социальных услуг, занятости и других сфер доступными и прозрачными.',
    'faq.q5': 'Как вы обеспечиваете безопасность данных?',
    'faq.a5': 'Безопасность данных — часть нашей повседневной работы: мы постоянно обновляем механизмы защиты, проводим аудит и обучаем команду.',
    'faq.cta_title': 'Не нашли ответ на свой вопрос?',
    'faq.cta_text': 'Свяжитесь с нами, и мы ответим.',
    'faq.cta_button': 'Связаться с нами',

    'careers.eyebrow': 'Карьера',
    'careers.title': 'Работа, которая меняет жизни',
    'careers.lede': 'Каждая система, которую мы создаём, помогает тысячам людей получить доступ к услугам.',
    'careers.openings_link': 'Смотреть вакансии',
    'careers.openings_label': 'Открытые вакансии',
    'careers.openings_title': 'Мы ищем',
    'careers.job1_title': 'Full Stack Developer',
    'careers.job1_meta': 'Ереван · Полная занятость',
    'careers.job1_text': 'Мы ищем опытного Full Stack разработчика для наших проектов в сфере социальных услуг.',
    'careers.job2_title': 'UI/UX Designer',
    'careers.job2_meta': 'Ереван · Полная занятость',
    'careers.job2_text': 'Дизайнер, который сделает государственные услуги простыми и удобными для людей.',
    'careers.job3_title': 'QA Engineer',
    'careers.job3_meta': 'Ереван · Полная занятость',
    'careers.job3_text': 'Ответственный за качество и надёжность наших систем: автоматизированное и ручное тестирование.',
    'careers.apply': 'Подать заявку',
    'careers.cv_title': 'Не нашли подходящую должность?',
    'careers.cv_text': 'Отправьте резюме, и мы свяжемся с вами в рамках имеющихся возможностей.',
    'careers.cv_button': 'Отправить резюме',

    'site.title.home': 'WISE Foundation — Фонд «Предприятие информационных систем благосостояния»',
    'site.title.about': 'О нас — WISE Foundation',
    'site.title.services': 'Услуги — WISE Foundation',
    'site.title.partners': 'Партнёры — WISE Foundation',
    'site.title.contact': 'Контакты — WISE Foundation',
    'site.title.blog': 'Новости — WISE Foundation',
    'site.title.faq': 'Часто задаваемые вопросы — WISE Foundation',
    'site.title.careers': 'Карьера — WISE Foundation',

    'site.desc.home': 'WISE Foundation — 25 лет в сфере информационных технологий. Мы создаём цифровые решения для государства и частного сектора.',
    'site.desc.about': 'Узнайте больше о WISE Foundation — 25 лет опыта в сфере информационных технологий.',
    'site.desc.services': 'Услуги WISE Foundation — проектирование информационных систем, кибербезопасность, обработка данных и другое.',
    'site.desc.partners': 'Партнёры WISE Foundation — государственные учреждения, международные организации, банки.',
    'site.desc.contact': 'Свяжитесь с WISE Foundation: эл. почта, телефон, форма обратной связи.',
    'site.desc.blog': 'Блог WISE Foundation — новости, статьи и объявления в сфере информационных технологий.',
    'site.desc.faq': 'Ответы на часто задаваемые вопросы о WISE Foundation: услуги, карьера, сотрудничество.',
    'site.desc.careers': 'Работа в WISE Foundation: открытые вакансии, команда, культура и возможность отправить резюме.'
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
  if (lang !== 'hy' && lang !== 'en' && lang !== 'ru') lang = 'hy';

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
      } else if (newLang === 'ru') {
        text = RU[key] || (T[key] ? T[key].en : undefined);
      } else {
        const entry = T[key];
        text = entry ? entry.en : undefined;
      }

      if (text === undefined || text === null) return;

      if (attr) {
        el.setAttribute(attr, text);
      } else if (el.matches('input, textarea')) {
        el.setAttribute('placeholder', text);
      } else if (/<[a-z][\s\S]*>/i.test(text)) {
        el.innerHTML = text;
      } else {
        el.textContent = text;
      }
    });

    document.documentElement.setAttribute('lang', newLang);
    document.body.setAttribute('lang', newLang);

    document.querySelectorAll('.lang-toggle__opt').forEach(opt => {
      opt.classList.toggle('lang-toggle__opt--active', opt.getAttribute('data-lang') === newLang);
      opt.setAttribute('aria-pressed', opt.getAttribute('data-lang') === newLang ? 'true' : 'false');
    });

    lang = newLang;
    localStorage.setItem('wisef_lang', newLang);
    document.dispatchEvent(new CustomEvent('wisefLangChanged', { detail: { lang: newLang } }));
  }

  /* ══════════════════════════════════════════════════════
     BUILD TOGGLE WIDGET
  ══════════════════════════════════════════════════════ */
  function buildToggle() {
    const wrap = document.createElement('div');
    wrap.className = 'lang-toggle';
    wrap.setAttribute('role', 'group');
    wrap.setAttribute('aria-label', 'Language');

    const options = [
      { code: 'hy', label: 'ՀՅ' },
      { code: 'en', label: 'EN' },
      { code: 'ru', label: 'РУ' }
    ];
    options.forEach(opt => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'lang-toggle__opt' + (lang === opt.code ? ' lang-toggle__opt--active' : '');
      btn.setAttribute('data-lang', opt.code);
      btn.setAttribute('aria-pressed', lang === opt.code ? 'true' : 'false');
      btn.textContent = opt.label;
      btn.addEventListener('click', () => applyLang(opt.code));
      wrap.appendChild(btn);
    });
    return wrap;
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

    if (lang !== 'hy') applyLang(lang);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.wisefI18n = {
    t:       (key) => {
      const e = T[key];
      if (lang === 'ru') return RU[key] || (e ? e.en : key);
      return e ? (e[lang] || e.en) : key;
    },
    getLang: ()    => lang,
    setLang: applyLang,
  };

})();
