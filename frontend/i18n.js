// Translations for Grahika.
//
// The API returns stable numeric keys alongside its English text --
// sign_index, nakshatra_index, tara number, house number, and the
// (planet, point) pairs behind each aspect. Everything below is keyed on
// those, so a language switch re-renders from the same response without
// another request and without any backend change.
//
// Telugu terms are the ones actually used in practice, not literal
// translations of the English: a Telugu speaker reads మేషం and అశ్విని
// natively, so this version is arguably plainer than the English one.

const I18N = {
  en: {
    dir: "ltr",
    title: "Grahika",
    subtitle: "Vedic birth chart, dasha & compatibility calculator",
    langName: "English",

    tab_chart: "Birth Chart",
    tab_horoscope: "Personal Daily Horoscope",
    tab_matching: "Kundli Matching",
    tab_chart_short: "Chart",
    tab_horoscope_short: "Daily",
    tab_matching_short: "Matching",
    tab_chart_dasha_short: "Chart",
    tab_doshas_short: "Doshas",
    tab_chart_dasha: "Chart & Dasha",
    tab_doshas: "Kaal Sarp & Sade Sati",

    label_name: "Name (optional)",
    label_birth_date: "Birth date",
    label_birth_time: "Birth time",
    label_birth_place: "Birth place",
    label_now: "Now",
    label_latitude: "Latitude",
    label_longitude: "Longitude",
    label_utc_offset: "Override UTC offset",
    label_manual_coords: "Enter coordinates manually instead",
    label_ayanamsa: "Ayanamsa",
    label_node: "Node",
    label_node_mean: "Mean",
    label_node_true: "True",
    label_chart_style: "Chart style",
    style_north: "North Indian (diamond)",
    style_south_savya: "South Indian - Savya (standard)",
    style_south_apasavya: "South Indian - Apasavya (mirrored)",
    placeholder_place: "e.g. Chennai, India",
    placeholder_name: "e.g. Teja",

    btn_compute: "Compute chart",
    btn_horoscope: "Get my horoscope",
    btn_match: "Match kundlis",
    btn_prev_day: "« Prev day",
    btn_next_day: "Next day »",
    btn_today: "Today",
    label_date: "Date",

    h_birth_details: "Birth Details",
    h_positions: "Positions",
    h_dasha: "Vimshottari Mahadasha",
    h_kaal_sarp: "Kaal Sarp Yoga",
    h_sade_sati: "Sade Sati",
    h_aspects: "Aspects on Your Chart",
    h_all_transits: "All Transiting Grahas",
    h_moon_placements: "Moon Placements",
    h_ashtakoot: "Ashtakoot Breakdown",
    h_mangal: "Mangal Dosha (Manglik)",
    h_detail: "The detail behind it",
    h_ongoing: "Ongoing influences",
    h_bride: "Bride",
    h_groom: "Groom",

    col_body: "Body", col_sign: "Sign", col_degree: "Degree",
    col_nakshatra: "Nakshatra", col_pada: "Pada", col_retro: "Retro",
    col_lord: "Lord", col_start: "Start", col_end: "End", col_years: "Years",
    col_graha: "Graha", col_house_moon: "House from Moon",
    col_house_lagna: "House from Lagna", col_koota: "Koota", col_score: "Score",
    col_rasi_moon: "Rasi (Moon sign)", col_from_lagna: "From Lagna",
    col_from_moon: "From Moon", col_total: "Total",

    row_name: "Name", row_birth_date: "Birth Date", row_birth_time: "Birth Time",
    row_place: "Place of Birth", row_nakshatra: "Nakshatra", row_rasi: "Rasi",
    row_ayanamsa: "Ayanamsa",

    signs: ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"],
    signsShort: ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                 "Libra", "Scorpi", "Sagitt", "Capric", "Aquari", "Pisces"],
    nakshatras: ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
      "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
      "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
      "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
      "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"],
    planets: {
      Sun: "Sun", Moon: "Moon", Mars: "Mars", Mercury: "Mercury", Jupiter: "Jupiter",
      Venus: "Venus", Saturn: "Saturn", Rahu: "Rahu", Ketu: "Ketu", Ascendant: "Ascendant",
    },
    planetAbbr: {
      Sun: "Su", Moon: "Mo", Mars: "Ma", Mercury: "Me", Jupiter: "Ju",
      Venus: "Ve", Saturn: "Sa", Rahu: "Ra", Ketu: "Ke", Ascendant: "As",
    },
    chart_lagna: "Lagna", chart_navamsha: "Navamsha",
    chart_d1: "D1 &middot; Rashi", chart_d9: "D9 &middot; Navamsha",
    chart_asc: "Asc",

    kootas: {
      Varna: "Varna", Vashya: "Vashya", Tara: "Tara", Yoni: "Yoni",
      "Graha Maitri": "Graha Maitri", Gana: "Gana", Bhakoot: "Bhakoot", Nadi: "Nadi",
    },
    verdicts: {
      "Not recommended": "Not recommended", Acceptable: "Acceptable",
      Good: "Good", Excellent: "Excellent",
    },
    headlines: {
      "A strong day": "A strong day",
      "A generally good day": "A generally good day",
      "A mixed day": "A mixed day",
      "A demanding day": "A demanding day",
      "A difficult day": "A difficult day",
    },
    qualities: { favourable: "favourable", mixed: "mixed", challenging: "challenging" },

    taraNames: ["Janma", "Sampat", "Vipat", "Kshema", "Pratyari",
                "Sadhaka", "Vadha", "Mitra", "Ati Mitra"],
    bhavas: ["Janma", "Dhana", "Vikrama", "Sukha", "Putra", "Shatru",
             "Kalatra", "Randhra", "Dharma", "Karma", "Labha", "Vyaya"],

    house_label: "House",
    intro_horoscope: "Your daily forecast by Gochar (Vedic transits) -- where the grahas are today relative to your birth chart. Enter your birth details once, then step through any date.",
    intro_matching: "Ashtakoot (Guna Milan) compatibility -- the 36-point system. Both charts are built from the Moon's sign and nakshatra, so only birth date, time and place are needed for each person.",
    note_sade_sati: "Sade Sati window boundaries vary by convention (Saturn can retrograde in and out of a sign before settling) -- treat the exact dates as approximate, not a substitute for a pundit's reading.",
    note_ongoing: "These come from the slow-moving grahas and stay in place for weeks or months -- they are the backdrop to your day, not today's news.",
    note_detail: "The traditional terms for the same readings, for anyone who wants them.",
    note_transit: "Cast for 12:00 noon at your birth place. The Moon moves about 13 degrees a day and can change sign mid-day, so readings near a sign boundary shift depending on the hour. Positions and house counts here are exact; the readings are conventional traditional significations stated generically, not personalised prediction.",
    note_mangal: "Mangal Dosha is reported separately and is never folded into the 36 points. Traditions differ on whether the Moon-based check counts.",
    note_guna: "Guna Milan tables vary between lineages and between commercial software. Kootas with unambiguous classical tables (Nadi, Bhakoot, Gana, Varna, Tara) are exact here; the Yoni koota's intermediate gradations are simplified, so small per-koota differences against other sites are expected. Treat this as a starting point for a pundit's reading, not a verdict.",
    transit_summary: "Moon transits {tsign} ({tnak}). Your natal Moon is in {nsign} ({nnak}).",
    aspect_line: "Transiting {planet} in {tsign} is {relation} your natal {point} in {nsign}",
    aspect_conjunct: "conjunct",
    aspect_drishti: "{n}th-house aspect on",
    aspect_none: "No aspects from the slow grahas on your Lagna, Moon or Sun today.",
  },

  te: {
    dir: "ltr",
    title: "గ్రహిక",
    subtitle: "జాతకం, దశలు మరియు వివాహ పొంతన",
    langName: "తెలుగు",

    tab_chart: "జాతకం",
    tab_horoscope: "దినఫలం",
    tab_matching: "వివాహ పొంతన",
    tab_chart_short: "జాతకం",
    tab_horoscope_short: "దినఫలం",
    tab_matching_short: "పొంతన",
    tab_chart_dasha_short: "జాతకం",
    tab_doshas_short: "దోషాలు",
    tab_chart_dasha: "జాతకం & దశలు",
    tab_doshas: "కాలసర్ప & ఏలినాటి శని",

    label_name: "పేరు (ఐచ్ఛికం)",
    label_birth_date: "పుట్టిన తేదీ",
    label_birth_time: "పుట్టిన సమయం",
    label_birth_place: "పుట్టిన ప్రదేశం",
    label_now: "ఇప్పుడు",
    label_latitude: "అక్షాంశం",
    label_longitude: "రేఖాంశం",
    label_utc_offset: "UTC ఆఫ్‌సెట్ మార్చండి",
    label_manual_coords: "బదులుగా అక్షాంశ రేఖాంశాలు నమోదు చేయండి",
    label_ayanamsa: "అయనాంశ",
    label_node: "రాహు గణన",
    label_node_mean: "మధ్యమ",
    label_node_true: "నిజ",
    label_chart_style: "చక్ర శైలి",
    style_north: "ఉత్తర భారత శైలి",
    style_south_savya: "దక్షిణ భారత శైలి - సవ్య",
    style_south_apasavya: "దక్షిణ భారత శైలి - అపసవ్య",
    placeholder_place: "ఉదా: హైదరాబాద్, ఇండియా",
    placeholder_name: "ఉదా: తేజ",

    btn_compute: "జాతకం చూడండి",
    btn_horoscope: "నా దినఫలం చూడండి",
    btn_match: "పొంతన చూడండి",
    btn_prev_day: "« నిన్న",
    btn_next_day: "రేపు »",
    btn_today: "ఈరోజు",
    label_date: "తేదీ",

    h_birth_details: "జనన వివరాలు",
    h_positions: "గ్రహ స్థితి",
    h_dasha: "వింశోత్తరి మహాదశ",
    h_kaal_sarp: "కాలసర్ప యోగం",
    h_sade_sati: "ఏలినాటి శని",
    h_aspects: "మీ జాతకంపై దృష్టి",
    h_all_transits: "గోచార గ్రహాలు",
    h_moon_placements: "చంద్ర స్థితి",
    h_ashtakoot: "అష్టకూట వివరాలు",
    h_mangal: "కుజ దోషం",
    h_detail: "సాంకేతిక వివరాలు",
    h_ongoing: "దీర్ఘకాల ప్రభావాలు",
    h_bride: "వధువు",
    h_groom: "వరుడు",

    col_body: "గ్రహం", col_sign: "రాశి", col_degree: "అంశ",
    col_nakshatra: "నక్షత్రం", col_pada: "పాదం", col_retro: "వక్రం",
    col_lord: "దశానాథుడు", col_start: "ప్రారంభం", col_end: "ముగింపు", col_years: "సంవత్సరాలు",
    col_graha: "గ్రహం", col_house_moon: "చంద్రుని నుండి భావం",
    col_house_lagna: "లగ్నం నుండి భావం", col_koota: "కూటం", col_score: "పాయింట్లు",
    col_rasi_moon: "రాశి (చంద్రుడు)", col_from_lagna: "లగ్నం నుండి",
    col_from_moon: "చంద్రుని నుండి", col_total: "మొత్తం",

    row_name: "పేరు", row_birth_date: "పుట్టిన తేదీ", row_birth_time: "పుట్టిన సమయం",
    row_place: "పుట్టిన ప్రదేశం", row_nakshatra: "నక్షత్రం", row_rasi: "రాశి",
    row_ayanamsa: "అయనాంశ",

    signs: ["మేషం", "వృషభం", "మిథునం", "కర్కాటకం", "సింహం", "కన్య",
            "తుల", "వృశ్చికం", "ధనుస్సు", "మకరం", "కుంభం", "మీనం"],
    signsShort: ["మేషం", "వృషభం", "మిథునం", "కర్కాట", "సింహం", "కన్య",
                 "తుల", "వృశ్చిక", "ధనుస్సు", "మకరం", "కుంభం", "మీనం"],
    nakshatras: ["అశ్విని", "భరణి", "కృత్తిక", "రోహిణి", "మృగశిర", "ఆరుద్ర",
      "పునర్వసు", "పుష్యమి", "ఆశ్లేష", "మఖ", "పుబ్బ", "ఉత్తర",
      "హస్త", "చిత్త", "స్వాతి", "విశాఖ", "అనూరాధ", "జ్యేష్ఠ",
      "మూల", "పూర్వాషాఢ", "ఉత్తరాషాఢ", "శ్రవణం", "ధనిష్ఠ",
      "శతభిషం", "పూర్వాభాద్ర", "ఉత్తరాభాద్ర", "రేవతి"],
    planets: {
      Sun: "సూర్యుడు", Moon: "చంద్రుడు", Mars: "కుజుడు", Mercury: "బుధుడు",
      Jupiter: "గురువు", Venus: "శుక్రుడు", Saturn: "శని", Rahu: "రాహువు",
      Ketu: "కేతువు", Ascendant: "లగ్నం",
    },
    planetAbbr: {
      Sun: "సూ", Moon: "చం", Mars: "కు", Mercury: "బు", Jupiter: "గు",
      Venus: "శు", Saturn: "శ", Rahu: "రా", Ketu: "కే", Ascendant: "ల",
    },
    chart_lagna: "లగ్న", chart_navamsha: "నవాంశ",
    chart_d1: "D1 &middot; రాశి", chart_d9: "D9 &middot; నవాంశ",
    chart_asc: "లగ్నం",

    kootas: {
      Varna: "వర్ణ", Vashya: "వశ్య", Tara: "తార", Yoni: "యోని",
      "Graha Maitri": "గ్రహ మైత్రి", Gana: "గణ", Bhakoot: "భకూట", Nadi: "నాడి",
    },
    verdicts: {
      "Not recommended": "సిఫార్సు చేయబడలేదు", Acceptable: "పర్వాలేదు",
      Good: "మంచిది", Excellent: "అత్యుత్తమం",
    },
    headlines: {
      "A strong day": "చాలా మంచి రోజు",
      "A generally good day": "సాధారణంగా మంచి రోజు",
      "A mixed day": "మిశ్రమ ఫలితాల రోజు",
      "A demanding day": "శ్రమతో కూడిన రోజు",
      "A difficult day": "కష్టతరమైన రోజు",
    },
    qualities: { favourable: "అనుకూలం", mixed: "మిశ్రమం", challenging: "ప్రతికూలం" },

    taraNames: ["జన్మ", "సంపత్", "విపత్", "క్షేమ", "ప్రత్యరి",
                "సాధక", "వధ", "మిత్ర", "అతిమిత్ర"],
    bhavas: ["జన్మ", "ధన", "విక్రమ", "సుఖ", "పుత్ర", "శత్రు",
             "కళత్ర", "రంధ్ర", "ధర్మ", "కర్మ", "లాభ", "వ్యయ"],

    house_label: "భావం",
    intro_horoscope: "గోచార గ్రహాల ఆధారంగా మీ దినఫలం — ఈరోజు గ్రహాలు మీ జన్మ జాతకంతో ఎలా ఉన్నాయో చూడండి. జనన వివరాలు ఒకసారి నమోదు చేసి, ఏ తేదీకైనా చూడవచ్చు.",
    intro_matching: "అష్టకూట (గుణ మిలన్) పొంతన — 36 పాయింట్ల పద్ధతి. రెండు జాతకాలూ చంద్రుని రాశి, నక్షత్రం ఆధారంగా లెక్కిస్తారు కాబట్టి, ప్రతి ఒక్కరికీ పుట్టిన తేదీ, సమయం, ప్రదేశం మాత్రమే అవసరం.",
    note_sade_sati: "ఏలినాటి శని కాలపరిమితి సంప్రదాయాన్ని బట్టి మారుతుంది (శని వక్రించి రాశిలోకి వెళ్లి తిరిగి రావచ్చు) — ఈ తేదీలను సుమారుగా భావించండి, పండితుని సలహాకు ప్రత్యామ్నాయంగా కాదు.",
    note_ongoing: "ఇవి మంద గతి గ్రహాల నుండి వస్తాయి, వారాలు లేదా నెలల పాటు కొనసాగుతాయి — ఇవి మీ రోజుకు నేపథ్యం మాత్రమే, ఈరోజు ప్రత్యేక ఫలితం కాదు.",
    note_detail: "అవే ఫలితాలకు సంప్రదాయ పదాలు, ఆసక్తి ఉన్నవారి కోసం.",
    note_transit: "మీ జన్మ స్థలంలో మధ్యాహ్నం 12:00 గంటలకు లెక్కించబడింది. చంద్రుడు రోజుకు సుమారు 13 డిగ్రీలు కదులుతాడు, మధ్యలో రాశి మారవచ్చు. గ్రహ స్థితులు, భావ గణన కచ్చితమైనవి; ఫలితాలు సాధారణ సంప్రదాయ సూచనలు మాత్రమే, వ్యక్తిగత జోస్యం కాదు.",
    note_mangal: "కుజ దోషాన్ని విడిగా చూపిస్తారు, 36 పాయింట్లలో కలపరు. చంద్రుని నుండి చూసే పద్ధతి లెక్కలోకి వస్తుందా అనే విషయంలో సంప్రదాయాలు వేర్వేరుగా ఉంటాయి.",
    note_guna: "గుణ మిలన్ పట్టికలు వంశ పరంపరను బట్టి, సాఫ్ట్‌వేర్‌ను బట్టి మారుతాయి. స్పష్టమైన సంప్రదాయ పట్టికలు ఉన్న కూటాలు (నాడి, భకూట, గణ, వర్ణ, తార) ఇక్కడ కచ్చితమైనవి; యోని కూటంలోని మధ్యస్థ విభజనలు సరళీకరించబడ్డాయి, కాబట్టి ఇతర సైట్లతో చిన్న తేడాలు రావచ్చు. దీన్ని పండితుని సలహాకు ఆరంభంగా భావించండి, తుది నిర్ణయంగా కాదు.",
    transit_summary: "చంద్రుడు {tsign} రాశిలో ({tnak} నక్షత్రం) సంచరిస్తున్నాడు. మీ జన్మ చంద్రుడు {nsign} రాశిలో ({nnak}).",
    aspect_line: "{tsign} రాశిలోని గోచార {planet} మీ జన్మ {point} ({nsign} రాశి) పై {relation}",
    aspect_conjunct: "కలిసి ఉన్నాడు",
    aspect_drishti: "{n}వ దృష్టి వేస్తున్నాడు",
    aspect_none: "ఈరోజు మీ లగ్నం, చంద్రుడు, సూర్యుడిపై మంద గ్రహాల దృష్టి లేదు.",
  },
};

// Interpretive text, keyed the same way the backend keys it so a language
// switch needs no extra request. English mirrors what the API returns;
// Telugu is written to read naturally rather than word-for-word.
const TARA_TEXT = {
  en: [
    "Your energy may run lower than usual. Better for rest and looking after yourself than for starting anything new.",
    "A favourable day for money and for anything you are hoping to gain from.",
    "Take extra care today, particularly with money, travel and risky decisions.",
    "A steady, comfortable day. Good for ordinary work and getting through routine tasks.",
    "Expect some pushback. Things are likely to take more effort than they normally would.",
    "A good day for finishing things you have already started, rather than beginning something new.",
    "The hardest day in the cycle. Best to keep things simple and postpone important decisions.",
    "Support tends to come from other people today. A good day to ask for help.",
    "One of the best days in the cycle. Things tend to fall your way.",
  ],
  te: [
    "శక్తి తక్కువగా ఉండవచ్చు. కొత్త పనులు మొదలుపెట్టడం కంటే విశ్రాంతి తీసుకోవడం మేలు.",
    "ధనం, లాభాల విషయంలో అనుకూలమైన రోజు.",
    "డబ్బు, ప్రయాణం, ధైర్యంతో కూడిన నిర్ణయాల విషయంలో జాగ్రత్త అవసరం.",
    "నిలకడైన, సౌకర్యవంతమైన రోజు. రోజువారీ పనులకు మంచిది.",
    "కొంత ఆటంకం ఎదురుకావచ్చు. పనులు మామూలు కంటే ఎక్కువ శ్రమ కోరతాయి.",
    "కొత్తవి మొదలుపెట్టడం కంటే, ఇప్పటికే మొదలుపెట్టిన పనులు పూర్తి చేయడానికి మంచి రోజు.",
    "ఈ చక్రంలో అత్యంత కష్టమైన రోజు. ముఖ్యమైన నిర్ణయాలు వాయిదా వేయడం మంచిది.",
    "ఇతరుల నుండి సహాయం అందే రోజు. సాయం అడగడానికి అనుకూలం.",
    "ఈ చక్రంలో అత్యుత్తమమైన రోజులలో ఒకటి. పనులు అనుకూలంగా జరుగుతాయి.",
  ],
};

const HOUSE_TEXT = {
  en: {
    1: "Your mood turns inward and energy can dip. Go easy on yourself.",
    2: "Attention goes to family, money and home. Good for domestic matters.",
    3: "You will feel bolder than usual. Good for starting things and for short trips.",
    4: "Feelings sit close to the surface and home pulls at your attention. Outward work feels harder.",
    5: "Good for creativity, learning, children and romance.",
    6: "A strong day for pushing through obstacles -- competition, health routines, clearing debts.",
    7: "Good for dealing with other people: partners, negotiations, travel.",
    8: "A heavy day. Better for quiet reflection than for big moves.",
    9: "Luck runs with you. Good for study, travel and advice from people older or wiser.",
    10: "A strong day for work and career, and for anything public or official.",
    11: "One of the best positions. Gains, friends, and things coming together.",
    12: "Energy drains and costs come up. Good for rest, not for chasing gain.",
  },
  te: {
    1: "మనసు లోపలికి మళ్లుతుంది, శక్తి తగ్గవచ్చు. మీపై ఒత్తిడి పెట్టుకోకండి.",
    2: "కుటుంబం, డబ్బు, ఇంటి విషయాలపై దృష్టి. గృహ వ్యవహారాలకు మంచిది.",
    3: "మామూలు కంటే ధైర్యంగా ఉంటారు. కొత్త పనులు, చిన్న ప్రయాణాలకు అనుకూలం.",
    4: "భావోద్వేగాలు ఎక్కువగా ఉంటాయి, ఇంటి విషయాలు మనసును లాగుతాయి. బయటి పనులు కష్టంగా అనిపిస్తాయి.",
    5: "సృజనాత్మకత, చదువు, పిల్లలు, ప్రేమ విషయాలకు మంచిది.",
    6: "ఆటంకాలను అధిగమించడానికి బలమైన రోజు — పోటీ, ఆరోగ్యం, అప్పులు తీర్చడం.",
    7: "ఇతరులతో వ్యవహారాలకు మంచిది: భాగస్వాములు, చర్చలు, ప్రయాణం.",
    8: "బరువైన రోజు. పెద్ద నిర్ణయాల కంటే ఆలోచనకు మంచిది.",
    9: "అదృష్టం కలిసి వస్తుంది. చదువు, ప్రయాణం, పెద్దల సలహాలకు మంచిది.",
    10: "ఉద్యోగం, వృత్తికి బలమైన రోజు. అధికారిక పనులకు అనుకూలం.",
    11: "అత్యుత్తమ స్థానాలలో ఒకటి. లాభాలు, స్నేహితులు, పనులు కుదురుతాయి.",
    12: "శక్తి, ఖర్చులు ఎక్కువ. విశ్రాంతికి మంచిది, లాభాల వేటకు కాదు.",
  },
};

const ASPECT_TEXT = {
  en: {
    "Mars|Ascendant": "Extra physical energy today, with a tendency to rush. Slow down.",
    "Mars|Moon": "You may feel more restless or short-tempered than usual.",
    "Mars|Sun": "Strong drive today, but watch for friction with people in authority.",
    "Jupiter|Ascendant": "A protective, steadying influence over the day as a whole.",
    "Jupiter|Moon": "Your mood is lifted, and judgement tends to be sound.",
    "Jupiter|Sun": "Support for your confidence and your standing with others.",
    "Saturn|Ascendant": "The day feels slower and heavier than usual. Patience helps.",
    "Saturn|Moon": "Mood may be low or serious. Worth remembering it is not the whole picture.",
    "Saturn|Sun": "Extra responsibility or pressure from above. Steady effort pays off.",
    "Rahu|Ascendant": "Things feel amplified and a little unsettled.",
    "Rahu|Moon": "Emotions may feel exaggerated or hard to place.",
    "Rahu|Sun": "Ambition runs high today; watch for overreach.",
    "Ketu|Ascendant": "You may feel withdrawn or less engaged than usual.",
    "Ketu|Moon": "A detached, inward sort of mood.",
    "Ketu|Sun": "Less interest than usual in recognition or being seen.",
  },
  te: {
    "Mars|Ascendant": "శారీరక శక్తి ఎక్కువ, కానీ తొందరపాటు ఉండవచ్చు. నెమ్మదిగా వెళ్లండి.",
    "Mars|Moon": "మామూలు కంటే చిరాకు, అసహనం ఎక్కువగా అనిపించవచ్చు.",
    "Mars|Sun": "పట్టుదల ఎక్కువ, కానీ పెద్దలతో, అధికారులతో ఘర్షణ రాకుండా చూసుకోండి.",
    "Jupiter|Ascendant": "రోజంతటికీ రక్షణ, స్థిరత్వం ఇచ్చే ప్రభావం.",
    "Jupiter|Moon": "మనసు తేలికగా ఉంటుంది, ఆలోచన సరిగా పనిచేస్తుంది.",
    "Jupiter|Sun": "ఆత్మవిశ్వాసానికి, సమాజంలో గౌరవానికి మద్దతు.",
    "Saturn|Ascendant": "రోజు నెమ్మదిగా, బరువుగా అనిపిస్తుంది. ఓర్పు అవసరం.",
    "Saturn|Moon": "మనసు బాధగా లేదా గంభీరంగా ఉండవచ్చు. అదే పూర్తి చిత్రం కాదని గుర్తుంచుకోండి.",
    "Saturn|Sun": "అదనపు బాధ్యతలు లేదా పైనుండి ఒత్తిడి. నిలకడైన కృషి ఫలిస్తుంది.",
    "Rahu|Ascendant": "విషయాలు పెద్దవిగా, కొంత అస్థిరంగా అనిపిస్తాయి.",
    "Rahu|Moon": "భావోద్వేగాలు అతిగా లేదా అర్థంకాకుండా అనిపించవచ్చు.",
    "Rahu|Sun": "ఆశయాలు ఎక్కువ; మితిమీరకుండా చూసుకోండి.",
    "Ketu|Ascendant": "మామూలు కంటే దూరంగా, ఆసక్తి తక్కువగా అనిపించవచ్చు.",
    "Ketu|Moon": "నిర్లిప్తమైన, అంతర్ముఖమైన మనస్థితి.",
    "Ketu|Sun": "గుర్తింపు, ప్రచారం పట్ల ఆసక్తి తక్కువ.",
  },
};

const MONTHS = {
  en: ["January", "February", "March", "April", "May", "June",
       "July", "August", "September", "October", "November", "December"],
  te: ["జనవరి", "ఫిబ్రవరి", "మార్చి", "ఏప్రిల్", "మే", "జూన్",
       "జూలై", "ఆగస్టు", "సెప్టెంబర్", "అక్టోబర్", "నవంబర్", "డిసెంబర్"],
};

let currentLang = localStorage.getItem("grahika_lang") || "en";

function t(key) {
  const dict = I18N[currentLang] || I18N.en;
  return key in dict ? dict[key] : (I18N.en[key] !== undefined ? I18N.en[key] : key);
}
function lang() { return currentLang; }
function setLang(code) {
  currentLang = I18N[code] ? code : "en";
  localStorage.setItem("grahika_lang", currentLang);
}
