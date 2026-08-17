const API_BASE = ""; // same origin -- backend serves this page

// All display names resolve through the active language at render time,
// so switching language re-renders from the response already in hand.
const tSign = (i) => t("signs")[i];
const tSignShort = (i) => t("signsShort")[i];
const tNak = (i) => t("nakshatras")[i];
const tPlanet = (n) => t("planets")[n] || n;
const tAbbr = (n) => t("planetAbbr")[n] || n.slice(0, 2);
const tKoota = (n) => t("kootas")[n] || n;
const tQuality = (q) => t("qualities")[q] || q;
// Classification values (varna, yoni, gana, nadi, tatva ...) appear in
// both Avakhada and the koota table; one map keeps them consistent.
const tValue = (v) => (VALUE_I18N[lang()] || {})[v] || v;
const tNamakshar = (nakIndex, pada, fallback) =>
  (NAMAKSHAR_I18N[lang()] ? NAMAKSHAR_I18N[lang()][nakIndex][pada - 1] : fallback);
const SIGN_GLYPHS = ["♈", "♉", "♊", "♋", "♌", "♍",
                     "♎", "♏", "♐", "♑", "♒", "♓"];

// Charts stay on their parchment palette in both light and dark themes.
// A traditional kundli is always drawn on light stock, and inverting it
// makes it read as a UI widget rather than a chart.
const C = {
  bg: "#FDF8EA", bgAsc: "#F4E7C8", border: "#8B5A2B", line: "#C9A063",
  planet: "#8B1A1A", retro: "#C0392B", signNum: "#B8860B",
  signName: "#93866A", houseNum: "#BEB197",
  centerTitle: "#6B4423", centerSub: "#8A7350",
};

function houseOf(bodySignIndex, ascSignIndex) {
  return ((bodySignIndex - ascSignIndex + 12) % 12) + 1;
}

// Retrograde is shown as a raised R, so the trailing tspan resets the
// baseline -- dy accumulates across tspans in SVG and without the reset
// every planet after a retrograde one would sit progressively higher.
function planetMarkup(names, bodies) {
  return names.map((name) => {
    const abbr = tAbbr(name);
    if (!bodies[name] || !bodies[name].retrograde) return abbr;
    return `${abbr}<tspan font-size="65%" dy="-5" fill="${C.retro}">${t("retro_mark")}</tspan><tspan dy="5"></tspan>`;
  }).join("&#160;");
}

// Planets are laid out in rows of at most three so a stellium doesn't
// overflow its cell.
function planetRows(names, bodies, x, y, size, fill) {
  const rows = [];
  for (let i = 0; i < names.length; i += 3) rows.push(names.slice(i, i + 3));
  const startY = y - ((rows.length - 1) * (size + 2)) / 2;
  return rows.map((row, i) => `
    <text x="${x}" y="${startY + i * (size + 2)}" font-size="${size}" font-weight="700"
          fill="${fill || C.planet}" text-anchor="middle" dominant-baseline="middle"
          font-family="Georgia, 'Noto Sans Telugu', serif">${planetMarkup(row, bodies)}</text>
  `).join("");
}

// Gochar overlay: transiting grahas drawn into the natal chart in a second
// colour. Blue reads clearly against the parchment without competing with
// the natal red, and the two never merge into one list.
const TRANSIT_COLOUR = "#1F4E79";

function groupBySign(bodies, signIndexFor) {
  const bySign = {};
  for (let s = 0; s < 12; s++) bySign[s] = [];
  for (const name of Object.keys(bodies)) {
    if (name === "Ascendant") continue;
    bySign[signIndexFor(name)].push(name);
  }
  return bySign;
}

// North Indian: houses are fixed to regions and run ANTICLOCKWISE from the
// top diamond (H1 top, H2 top-left, H3 left-upper, ...). Drawing them
// clockwise mirrors the chart -- an easy mistake, since the house->rashi
// arithmetic stays correct either way and only the picture is wrong.
const NORTH_REGIONS = [
  { poly: "200,0 300,100 200,200 100,100", num: [200, 26], planets: [200, 112] },
  { poly: "0,0 200,0 100,100", num: [158, 20], planets: [100, 50] },
  { poly: "0,0 100,100 0,200", num: [20, 158], planets: [50, 100] },
  { poly: "0,200 100,100 200,200 100,300", num: [26, 200], planets: [112, 200] },
  { poly: "0,200 100,300 0,400", num: [20, 246], planets: [50, 300] },
  { poly: "0,400 100,300 200,400", num: [158, 386], planets: [100, 350] },
  { poly: "200,400 100,300 200,200 300,300", num: [200, 378], planets: [200, 288] },
  { poly: "200,400 300,300 400,400", num: [246, 386], planets: [300, 350] },
  { poly: "400,400 300,300 400,200", num: [382, 246], planets: [350, 300] },
  { poly: "400,200 300,300 200,200 300,100", num: [376, 200], planets: [288, 200] },
  { poly: "400,200 300,100 400,0", num: [382, 158], planets: [350, 100] },
  { poly: "400,0 300,100 200,0", num: [246, 20], planets: [300, 50] },
];

function buildNorthIndianSvg(bodies, signIndexFor, overlay) {
  const ascSignIndex = signIndexFor("Ascendant");
  // The Ascendant isn't drawn as a token. In this style house 1 is always
  // the top diamond by construction, so the Lagna is already unambiguous
  // and an "As" label would just be noise.
  const byHouse = {};
  for (let h = 1; h <= 12; h++) byHouse[h] = [];
  for (const name of Object.keys(bodies)) {
    if (name === "Ascendant") continue;
    byHouse[houseOf(signIndexFor(name), ascSignIndex)].push(name);
  }

  // Transits are grouped by the SAME house frame as the natal chart, so a
  // graha appears in the house it is transiting for this person.
  const overlayByHouse = {};
  if (overlay) {
    for (let h = 1; h <= 12; h++) overlayByHouse[h] = [];
    for (const name of Object.keys(overlay.bodies)) {
      if (name === "Ascendant") continue;
      overlayByHouse[houseOf(overlay.signIndexFor(name), ascSignIndex)].push(name);
    }
  }

  let regions = "";
  for (let h = 1; h <= 12; h++) {
    const r = NORTH_REGIONS[h - 1];
    const rashi = ((ascSignIndex + h - 1) % 12) + 1;
    regions += `<polygon points="${r.poly}" fill="${h === 1 ? C.bgAsc : C.bg}" stroke="none"/>`;
    regions += `<text x="${r.num[0]}" y="${r.num[1]}" font-size="13" font-weight="700"
                      fill="${C.signNum}" text-anchor="middle">${rashi}</text>`;
    if (overlay) {
      regions += planetRows(byHouse[h], bodies, r.planets[0], r.planets[1] - 9, 13);
      regions += planetRows(overlayByHouse[h], overlay.bodies,
                            r.planets[0], r.planets[1] + 9, 13, TRANSIT_COLOUR);
    } else {
      regions += planetRows(byHouse[h], bodies, r.planets[0], r.planets[1], 15);
    }
  }

  const lines = `
    <line x1="0" y1="0" x2="400" y2="400" stroke="${C.line}" stroke-width="1.5"/>
    <line x1="400" y1="0" x2="0" y2="400" stroke="${C.line}" stroke-width="1.5"/>
    <polygon points="200,0 400,200 200,400 0,200" fill="none" stroke="${C.line}" stroke-width="1.5"/>
    <rect x="0" y="0" width="400" height="400" fill="none" stroke="${C.border}" stroke-width="3"/>
  `;

  return `<svg viewBox="0 0 400 400" class="kundli-svg" role="img"
               aria-label="North Indian style chart">${regions}${lines}</svg>`;
}

// South Indian box chart: signs are fixed to grid cells (a 4x4 grid with
// the center 2x2 left empty); houses aren't rotated, the Ascendant's sign
// cell is just highlighted. "Savya" (standard) runs the zodiac clockwise
// starting from Aries at row0/col1; "Apasavya" mirrors that horizontally
// so the sequence runs counter-clockwise instead.
const SOUTH_INDIAN_CELLS_SAVYA = [
  [0, 1], [0, 2], [0, 3], [1, 3], [2, 3], [3, 3],
  [3, 2], [3, 1], [3, 0], [2, 0], [1, 0], [0, 0],
];
const SOUTH_INDIAN_CELLS_APASAVYA = SOUTH_INDIAN_CELLS_SAVYA.map(([r, c]) => [r, 3 - c]);


function formatChartDate(dateStr) {
  if (!dateStr) return "";
  const [y, m, d] = dateStr.split("-").map(Number);
  return `${d} - ${MONTHS[lang()][m - 1]} - ${y}`;
}

function formatChartTime(timeStr) {
  if (!timeStr) return "";
  const [h, m, s] = timeStr.split(":").map(Number);
  const period = h >= 12 ? "PM" : "AM";
  const h12 = ((h + 11) % 12) + 1;
  const pad = (n) => String(n).padStart(2, "0");
  return `${pad(h12)}:${pad(m)}:${pad(s || 0)} ${period}`;
}

function buildSouthIndianSvg(bodies, signIndexFor, mirrored, centerInfo, overlay) {
  const cellFor = mirrored ? SOUTH_INDIAN_CELLS_APASAVYA : SOUTH_INDIAN_CELLS_SAVYA;
  const ascSignIndex = signIndexFor("Ascendant");

  // As above: the Lagna is carried by the shaded cell and the centre
  // caption, not by an "As" token among the grahas.
  const bySign = groupBySign(bodies, signIndexFor);
  const overlayBySign = overlay ? groupBySign(overlay.bodies, overlay.signIndexFor) : null;

  const CELL = 100;
  const SIZE = 400;

  let cells = "";
  for (let s = 0; s < 12; s++) {
    const [row, col] = cellFor[s];
    const x = col * CELL;
    const y = row * CELL;
    const isAsc = s === ascSignIndex;
    const house = houseOf(s, ascSignIndex);

    cells += `<rect x="${x}" y="${y}" width="${CELL}" height="${CELL}"
                    fill="${isAsc ? C.bgAsc : C.bg}" stroke="${C.line}" stroke-width="1"/>`;
    cells += `<text x="${x + 9}" y="${y + 20}" font-size="14" font-weight="700"
                    fill="${C.signNum}">${s + 1}</text>`;
    cells += `<text x="${x + 27}" y="${y + 20}" font-size="11"
                    fill="${C.signName}">${tSignShort(s)}</text>`;
    cells += `<text x="${x + CELL - 9}" y="${y + 20}" font-size="10" fill="${C.houseNum}"
                    text-anchor="end">H${house}</text>`;
    if (overlayBySign) {
      cells += planetRows(bySign[s], bodies, x + CELL / 2, y + CELL / 2 + 1, 13);
      cells += planetRows(overlayBySign[s], overlay.bodies,
                          x + CELL / 2, y + CELL / 2 + 19, 13, TRANSIT_COLOUR);
    } else {
      cells += planetRows(bySign[s], bodies, x + CELL / 2, y + CELL / 2 + 8, 15);
    }
  }

  let center = "";
  if (centerInfo) {
    const ascName = centerInfo.ascSignName;
    const ascGlyph = SIGN_GLYPHS[ascSignIndex];
    center = `
      <rect x="${CELL}" y="${CELL}" width="${CELL * 2}" height="${CELL * 2}"
            fill="${C.bg}" stroke="none"/>
      <text x="200" y="152" font-size="12" fill="${C.centerSub}" text-anchor="middle">${centerInfo.dateLabel}</text>
      <text x="200" y="170" font-size="12" fill="${C.centerSub}" text-anchor="middle">${centerInfo.timeLabel}</text>
      <text x="200" y="205" font-size="23" font-weight="700" fill="${C.centerTitle}"
            text-anchor="middle" font-family="Georgia, 'Noto Sans Telugu', serif">${centerInfo.chartLabel}</text>
      <text x="200" y="232" font-size="14" fill="${C.centerTitle}" text-anchor="middle">
        ${t("chart_asc")}: ${ascGlyph} ${ascName}
      </text>
      <text x="200" y="253" font-size="11" fill="${C.centerSub}" text-anchor="middle">${centerInfo.vargaLabel}</text>
    `;
  }

  const border = `<rect x="0" y="0" width="${SIZE}" height="${SIZE}" fill="none"
                        stroke="${C.border}" stroke-width="3"/>`;

  return `<svg viewBox="0 0 ${SIZE} ${SIZE}" class="kundli-svg" role="img"
               aria-label="South Indian style chart">${cells}${center}${border}</svg>`;
}

function renderCharts(positions, vargas) {
  const style = document.getElementById("chart_style").value;
  const d1SignIndex = (name) => vargas[name].D1.sign_index;
  const d9SignIndex = (name) => vargas[name].D9.sign_index;

  const dateLabel = formatChartDate(document.getElementById("birth_date").value);
  const timeLabel = formatChartTime(document.getElementById("birth_time").value);
  const moonNakshatra = tNak(positions.Moon.nakshatra_index);

  const build = (signIndexFor, chartLabel, vargaLabel) => {
    const centerInfo = {
      dateLabel, timeLabel, chartLabel, vargaLabel, moonNakshatra,
      ascSignName: tSignShort(signIndexFor("Ascendant")),
    };
    if (style === "south_savya") return buildSouthIndianSvg(positions, signIndexFor, false, centerInfo);
    if (style === "south_apasavya") return buildSouthIndianSvg(positions, signIndexFor, true, centerInfo);
    return buildNorthIndianSvg(positions, signIndexFor);
  };

  const caption = style === "north"
    ? `<p class="chart-caption">${dateLabel}, ${timeLabel} &middot; Moon: ${moonNakshatra}</p>`
    : "";

  const pick = document.getElementById("varga_pick").value;
  const vargaName = t("varga_names")[pick] || pick;

  // The Moon chart is the same D1 placement read from the Moon instead of
  // the Ascendant, so it reuses the rasi indices with a swapped reference.
  const secondSignIndex = pick === "MOON"
    ? (name) => (name === "Ascendant" ? positions.Moon.sign_index : vargas[name].D1.sign_index)
    : (name) => vargas[name][pick].sign_index;

  document.getElementById("d1-title").textContent = t("varga_names").D1;
  document.getElementById("d9-title").textContent = vargaName;
  document.getElementById("d1-chart").innerHTML =
    build(d1SignIndex, t("chart_lagna"), t("varga_names").D1) + caption;
  document.getElementById("d9-chart").innerHTML =
    build(secondSignIndex, vargaName, vargaName) + caption;
}

// Takes the raw date/time strings rather than pre-formatted labels, so a
// language switch can re-run this and get the month name in the new
// language without the caller having to re-derive anything.
let lastDetailsArgs = null;

function renderDetailsTable(args) {
  lastDetailsArgs = args;
  const { name, date, time, placeLabel, moon, ayanamsaLabel } = args;
  const tbody = document.querySelector("#details-table tbody");
  const rows = [];
  if (name) rows.push([t("row_name"), name]);
  rows.push([t("row_birth_date"), formatChartDate(date)]);
  rows.push([t("row_birth_time"), formatChartTime(time)]);
  rows.push([t("row_place"), placeLabel]);
  rows.push([t("row_nakshatra"), tNak(moon.nakshatra_index)]);
  rows.push([t("row_rasi"), tSign(moon.sign_index)]);
  rows.push([t("row_ayanamsa"), ayanamsaLabel]);
  tbody.innerHTML = rows.map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`).join("");
}

// Reuses the panchangam card grid so the two read as one system.
function factCard(label, value, sub) {
  return `<div class="pa-card">
    <div class="pa-label">${label}</div>
    <div class="pa-value">${value}</div>
    <div class="pa-sub">${sub || ""}</div>
  </div>`;
}

function renderAvakhada(av) {
  const rows = [
    [t("av_rasi"), tSign(av.rasi.index), tPlanet(av.rasi_lord)],
    [t("av_nakshatra"), tNak(av.nakshatra.index), `${t("av_pada")} ${av.pada}`],
    [t("av_nak_lord"), tPlanet(av.nakshatra_lord), ""],
    [t("av_lagna"), tSign(av.lagna.index), tPlanet(av.lagna_lord)],
    [t("av_namakshar"), tNamakshar(av.nakshatra.index, av.pada, av.namakshar), ""],
    [t("av_tatva"), tValue(av.tatva), ""],
    [t("av_varna"), tValue(av.varna), ""],
    [t("av_vashya"), tValue(av.vashya), ""],
    [t("av_yoni"), tValue(av.yoni), ""],
    [t("av_gana"), tValue(av.gana), ""],
    [t("av_nadi"), tValue(av.nadi), ""],
  ];
  document.getElementById("avakhada-grid").innerHTML =
    rows.map(([l, v, s]) => factCard(l, v, s)).join("");
}

function periodDates(p) {
  return `${formatChartDate(p.start.slice(0, 10))} \u2192 ${formatChartDate(p.end.slice(0, 10))}`;
}

function renderCurrentPeriods(cp) {
  const cards = [];
  if (cp.mahadasha) cards.push(factCard(t("dp_maha"), tPlanet(cp.mahadasha.lord), periodDates(cp.mahadasha)));
  if (cp.antardasha) cards.push(factCard(t("dp_antar"), tPlanet(cp.antardasha.lord), periodDates(cp.antardasha)));
  if (cp.next_antardasha) cards.push(factCard(t("dp_next"), tPlanet(cp.next_antardasha.lord), periodDates(cp.next_antardasha)));
  document.getElementById("current-periods").innerHTML = cards.join("");
}

function renderNatalAspects(asp) {
  const byPlanet = {};
  for (const row of asp.on_planets) {
    byPlanet[row.planet] = row.aspects.map((x) => tPlanet(x.planet)).join(", ");
  }
  document.querySelector("#natal-aspect-table tbody").innerHTML = asp.on_bhavas.map((row) => `
    <tr>
      <td>${tPlanet(row.planet)}</td>
      <td>${byPlanet[row.planet] || "\u2014"}</td>
      <td>${row.houses.join(", ")}</td>
    </tr>`).join("");
}

function renderPositionsTable(positions) {
  const tbody = document.querySelector("#positions-table tbody");
  tbody.innerHTML = "";
  for (const [name, d] of Object.entries(positions)) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${tPlanet(name)}</td>
      <td>${tSign(d.sign_index)}</td>
      <td>${d.degree_in_sign.toFixed(2)}&deg;</td>
      <td>${tNak(d.nakshatra_index)}</td>
      <td>${d.nakshatra_pada}</td>
      <td>${d.retrograde ? t("retro_mark") : ""}</td>
    `;
    tbody.appendChild(tr);
  }
}

function renderDashaTable(periods, current) {
  const tbody = document.querySelector("#dasha-table tbody");
  const runningLord = current && current.mahadasha ? current.mahadasha.lord : null;
  const runningStart = current && current.mahadasha ? current.mahadasha.start : null;
  tbody.innerHTML = "";

  periods.forEach((p) => {
    const tr = document.createElement("tr");
    const isRunning = p.lord === runningLord && p.start === runningStart;
    tr.className = "dasha-row" + (isRunning ? " dasha-running" : "");
    tr.innerHTML = `<td>${tPlanet(p.lord)}</td>
      <td>${formatChartDate(p.start.slice(0, 10))}</td>
      <td>${formatChartDate(p.end.slice(0, 10))}</td>
      <td>${p.years}</td>`;
    tbody.appendChild(tr);

    // Sub-periods are computed on the client from the same rule the server
    // uses, so expanding a row costs nothing.
    const sub = document.createElement("tr");
    sub.className = "dasha-subrow";
    sub.hidden = true;
    sub.innerHTML = `<td colspan="4"><div class="dasha-subs">${
      antardashaRows(p).map((s) => `
        <div class="dasha-sub">
          <span>${tPlanet(s.lord)}</span>
          <span>${formatChartDate(s.start)} \u2192 ${formatChartDate(s.end)}</span>
        </div>`).join("")
    }</div></td>`;
    tbody.appendChild(sub);

    tr.addEventListener("click", () => { sub.hidden = !sub.hidden; });
  });
}

const DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"];
const DASHA_YEARS = { Ketu: 7, Venus: 20, Sun: 6, Moon: 10, Mars: 7, Rahu: 18, Jupiter: 16, Saturn: 19, Mercury: 17 };
const DAYS_PER_YEAR = 365.2425;

function antardashaRows(maha) {
  const startIndex = DASHA_ORDER.indexOf(maha.lord);
  let cursor = new Date(maha.start);
  const iso = (d) => d.toISOString().slice(0, 10);
  const out = [];
  for (let i = 0; i < 9; i++) {
    const lord = DASHA_ORDER[(startIndex + i) % 9];
    const years = maha.years * DASHA_YEARS[lord] / 120;
    const end = new Date(cursor.getTime() + years * DAYS_PER_YEAR * 86400000);
    out.push({ lord, start: iso(cursor), end: iso(end) });
    cursor = end;
  }
  return out;
}

document.getElementById("now_btn").addEventListener("click", () => {
  const now = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  document.getElementById("birth_date").value = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
  document.getElementById("birth_time").value = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
});

// Selected place display names, keyed by field prefix ("" for the birth
// chart form, "bride_"/"groom_" for the matching form). Kept outside the
// DOM so the details table can show a readable place rather than raw
// coordinates.
const selectedPlaceNames = {};

// Nominatim's usage policy caps requests at ~1/second and explicitly
// discourages firing one per keystroke. So: wait for a real pause in
// typing, require a few characters, and cache results per query so
// backspacing or re-focusing never re-hits the API.
const AUTOCOMPLETE_DELAY_MS = 650;
const MIN_QUERY_LENGTH = 3;
const placeCache = new Map();

async function lookupPlaces(query) {
  const key = query.toLowerCase();
  if (placeCache.has(key)) return placeCache.get(key);
  const resp = await fetch(`${API_BASE}/geocode/search?q=${encodeURIComponent(query)}`);
  if (!resp.ok) throw new Error(t("err_lookup_failed").replace("{status}", resp.status));
  const places = await resp.json();
  placeCache.set(key, places);
  return places;
}

function wirePlaceSearch(prefix, errorElId) {
  const id = (suffix) => `${prefix}${suffix}`;
  const input = document.getElementById(id("place_query"));
  if (!input) return;

  const resultsEl = document.getElementById(id("place_results"));
  const selectedEl = document.getElementById(id("place_selected"));
  let timer = null;
  let requestSeq = 0;

  const choose = (place) => {
    document.getElementById(id("latitude")).value = place.latitude;
    document.getElementById(id("longitude")).value = place.longitude;
    selectedPlaceNames[prefix] = place.display_name;
    input.value = place.display_name;
    selectedEl.textContent = `${place.latitude.toFixed(4)}, ${place.longitude.toFixed(4)}`;
    selectedEl.hidden = false;
    resultsEl.innerHTML = "";
  };

  const search = async (query) => {
    // Responses can land out of order; only the newest one may render.
    const seq = ++requestSeq;
    try {
      const places = await lookupPlaces(query);
      if (seq !== requestSeq) return;

      if (places.length === 0) {
        resultsEl.innerHTML = `<li class="place-empty">${t("msg_no_matches")}</li>`;
        return;
      }
      resultsEl.innerHTML = "";
      for (const place of places) {
        const li = document.createElement("li");
        li.textContent = place.display_name;
        li.addEventListener("mousedown", (e) => {
          // mousedown, not click: blur fires first and would hide the
          // list before the click ever registers.
          e.preventDefault();
          choose(place);
        });
        resultsEl.appendChild(li);
      }
    } catch (err) {
      if (seq !== requestSeq) return;
      const errorEl = document.getElementById(errorElId);
      errorEl.textContent = err.message;
      errorEl.hidden = false;
    }
  };

  input.addEventListener("input", () => {
    clearTimeout(timer);
    selectedEl.hidden = true;
    // Any edit invalidates the previously picked place, so clear the
    // coordinates -- otherwise a half-typed city silently keeps the old
    // location and computes a chart for the wrong place.
    document.getElementById(id("latitude")).value = "";
    document.getElementById(id("longitude")).value = "";
    delete selectedPlaceNames[prefix];

    const query = input.value.trim();
    if (query.length < MIN_QUERY_LENGTH) {
      resultsEl.innerHTML = "";
      return;
    }
    timer = setTimeout(() => search(query), AUTOCOMPLETE_DELAY_MS);
  });

  input.addEventListener("blur", () => setTimeout(() => { resultsEl.innerHTML = ""; }, 150));
}

wirePlaceSearch("", "error");
wirePlaceSearch("dh_", "horoscope-error");
wirePlaceSearch("pa_", "panchanga-error");
wirePlaceSearch("id_", "ishta-error");
wirePlaceSearch("rp_", "report-error");
wirePlaceSearch("bride_", "match-error");
wirePlaceSearch("groom_", "match-error");

document.getElementById("chart-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("error");
  const resultsEl = document.getElementById("results");
  errorEl.hidden = true;
  resultsEl.hidden = true;

  const latitude = parseFloat(document.getElementById("latitude").value);
  const longitude = parseFloat(document.getElementById("longitude").value);
  if (Number.isNaN(latitude) || Number.isNaN(longitude)) {
    errorEl.textContent = t("err_need_place");
    errorEl.hidden = false;
    return;
  }

  const date = document.getElementById("birth_date").value;
  const time = document.getElementById("birth_time").value;
  const offset = document.getElementById("utc_offset").value.trim();
  // No offset entered -> send a naive datetime; the backend resolves the
  // correct historical UTC offset for this place/date automatically.
  const birth_datetime = `${date}T${time}${offset}`;

  const payload = {
    birth_datetime,
    latitude,
    longitude,
    ayanamsa: document.getElementById("ayanamsa").value,
    node_type: document.getElementById("node_type").value,
  };

  try {
    const resp = await fetch(`${API_BASE}/charts/compute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) {
      const detail = await resp.json().catch(() => ({}));
      throw new Error(detail.detail ? JSON.stringify(detail.detail)
        : t("err_request_failed").replace("{status}", resp.status));
    }
    const data = await resp.json();
    lastChartData = data;
    renderCharts(data.positions, data.vargas);
    renderPositionsTable(data.positions);
    renderDashaTable(data.vimshottari_dasha, data.current_periods);
    renderAvakhada(data.avakhada);
    renderCurrentPeriods(data.current_periods);
    renderNatalAspects(data.natal_aspects);
    renderShodashavarga(data.vargas);
    renderDetailsTable({
      name: document.getElementById("person_name").value.trim(),
      date,
      time,
      placeLabel: selectedPlaceNames[""] || `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`,
      moon: data.positions.Moon,
      ayanamsaLabel: document.getElementById("ayanamsa").selectedOptions[0].text,
    });
    resultsEl.hidden = false;

    fetchAndRenderDoshas(payload);
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.hidden = false;
  }
});

let lastDoshaData = null;

function renderDoshas(data) {
  const kaalEl = document.getElementById("kaal-sarp-result");
  const sadeEl = document.getElementById("sade-sati-result");

  const ksy = data.kaal_sarp_yoga;
  // The backend names the direction in English; map it to a key rather
  // than interpolating the raw value into a translated sentence.
  const dirKey = ksy.direction === "Rahu to Ketu" ? "ksy_dir_rk" : "ksy_dir_kr";
  kaalEl.textContent = ksy.present
    ? t("ksy_present").replace("{direction}", t(dirKey))
    : t("ksy_absent");

  const ss = data.sade_sati;
  if (ss.in_sade_sati) {
    sadeEl.textContent = t("ss_current")
      .replace("{phase}", t(`ss_phase_${ss.phase}`))
      .replace("{start}", ss.current_window_start)
      .replace("{end}", ss.current_window_end);
  } else if (ss.next_window_start) {
    sadeEl.textContent = t("ss_next").replace("{start}", ss.next_window_start);
  } else {
    sadeEl.textContent = t("ss_none");
  }
}

async function fetchAndRenderDoshas(payload) {
  const kaalEl = document.getElementById("kaal-sarp-result");
  const sadeEl = document.getElementById("sade-sati-result");
  kaalEl.textContent = t("msg_loading");
  sadeEl.textContent = t("msg_loading");
  try {
    const resp = await fetch(`${API_BASE}/charts/doshas`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) throw new Error(t("err_request_failed").replace("{status}", resp.status));
    lastDoshaData = await resp.json();
    renderDoshas(lastDoshaData);
  } catch (err) {
    const failed = t("err_could_not_load").replace("{message}", err.message);
    kaalEl.textContent = failed;
    sadeEl.textContent = failed;
  }
}

// ---------------------- personal daily horoscope ----------------------

// Set once the horoscope form is submitted, so the date navigator can
// re-query other dates without making the user re-enter birth details.
let horoscopePayload = null;

function shiftTransitDate(days) {
  const input = document.getElementById("transit_date");
  const base = input.value ? new Date(`${input.value}T12:00:00`) : new Date();
  base.setDate(base.getDate() + days);
  const pad = (n) => String(n).padStart(2, "0");
  input.value = `${base.getFullYear()}-${pad(base.getMonth() + 1)}-${pad(base.getDate())}`;
  fetchAndRenderTransit();
}

function renderTransit(data) {
  document.getElementById("transit-heading-date").textContent = formatChartDate(data.transit_date);
  document.getElementById("transit-moon-summary").textContent = t("transit_summary")
    .replace("{tsign}", tSign(data.transit_moon.sign_index))
    .replace("{tnak}", tNak(data.transit_moon.nakshatra_index))
    .replace("{nsign}", tSign(data.natal_moon.sign_index))
    .replace("{nnak}", tNak(data.natal_moon.nakshatra_index));

  const asItems = (lines) => lines.map((p) => `<li>${p}</li>`).join("");
  // Rebuilt from the numeric keys rather than reusing the server's English
  // sentences, so switching language needs no new request.
  const todayLines = [
    TARA_TEXT[lang()][data.tara_bala.number - 1],
    HOUSE_TEXT[lang()][data.chandra_bala.house],
  ];
  const ongoingLines = [];
  for (const a of data.aspects) {
    const line = ASPECT_TEXT[lang()][`${a.transit_planet}|${a.natal_point}`];
    if (line && !ongoingLines.includes(line)) ongoingLines.push(line);
  }
  document.getElementById("summary-headline").textContent =
    t("headlines")[data.summary.headline] || data.summary.headline;
  document.getElementById("summary-today").innerHTML = asItems(todayLines);
  document.getElementById("summary-ongoing").innerHTML = asItems(ongoingLines);
  document.getElementById("summary-ongoing-block").hidden = ongoingLines.length === 0;

  const tara = data.tara_bala;
  document.getElementById("tara-name").textContent =
    `${tara.number}. ${t("taraNames")[tara.number - 1]}`;
  document.getElementById("tara-text").textContent = TARA_TEXT[lang()][tara.number - 1];
  const taraPill = document.getElementById("tara-quality");
  taraPill.textContent = tQuality(tara.quality);
  taraPill.className = `quality-pill quality-${tara.quality}`;

  const chandra = data.chandra_bala;
  document.getElementById("chandra-name").textContent =
    `${t("house_label")} ${chandra.house} (${t("bhavas")[chandra.house - 1]})`;
  document.getElementById("chandra-text").textContent = HOUSE_TEXT[lang()][chandra.house];
  const chandraPill = document.getElementById("chandra-quality");
  chandraPill.textContent = tQuality(chandra.quality);
  chandraPill.className = `quality-pill quality-${chandra.quality}`;

  const aspectsEl = document.getElementById("transit-aspects");
  aspectsEl.innerHTML = data.aspects.length
    ? data.aspects.map((a) => `
        <li>
          <div class="aspect-headline">${
            t("aspect_line")
              .replace("{planet}", tPlanet(a.transit_planet))
              .replace("{tsign}", tSign(a.transit_sign_index))
              .replace("{relation}", a.distance === 1
                ? t("aspect_conjunct")
                : t("aspect_drishti").replace("{n}", a.distance))
              .replace("{point}", tPlanet(a.natal_point))
              .replace("{nsign}", tSign(a.natal_sign_index))
          }</div>
          <div class="aspect-note">${ASPECT_TEXT[lang()][`${a.transit_planet}|${a.natal_point}`] || a.note}</div>
        </li>
      `).join("")
    : `<li class="aspect-empty">${t("aspect_none")}</li>`;

  renderGocharChart(data);

  document.querySelector("#transit-table tbody").innerHTML = data.planet_transits.map((p) => `
    <tr>
      <td>${tPlanet(p.planet)}</td>
      <td>${tSign(p.sign_index)}</td>
      <td>${p.degree_in_sign.toFixed(2)}&deg;</td>
      <td>${tNak(p.nakshatra_index)}</td>
      <td>${p.house_from_moon}</td>
      <td>${p.house_from_lagna}</td>
      <td>${p.retrograde ? t("retro_mark") : ""}</td>
    </tr>
  `).join("");
}

// Gochar chart: the natal chart with today's grahas laid over it, so a
// reader sees at a glance which of their houses are currently occupied.
function renderGocharChart(data) {
  const style = document.getElementById("gochar_style").value;
  const natalSign = (n) => data.natal_chart[n].sign_index;
  const transitSign = (n) => data.transit_chart[n].sign_index;
  const overlay = { bodies: data.transit_chart, signIndexFor: transitSign };

  const svg = style === "north"
    ? buildNorthIndianSvg(data.natal_chart, natalSign, overlay)
    : buildSouthIndianSvg(data.natal_chart, natalSign, style === "south_apasavya", {
        dateLabel: formatChartDate(data.transit_date),
        timeLabel: data.transit_time,
        chartLabel: t("h_gochar"),
        vargaLabel: t("gochar_caption"),
        ascSignName: tSignShort(natalSign("Ascendant")),
      }, overlay);

  document.getElementById("gochar-chart").innerHTML = svg;
}

async function fetchAndRenderTransit() {
  if (!horoscopePayload) return;
  const summaryEl = document.getElementById("transit-moon-summary");
  summaryEl.textContent = t("msg_loading");

  const selectedDate = document.getElementById("transit_date").value;
  const selectedTime = document.getElementById("transit_time").value;
  const payload = { ...horoscopePayload };
  if (selectedDate) payload.transit_date = selectedDate;
  if (selectedTime) payload.transit_time = selectedTime.slice(0, 5);

  try {
    const resp = await fetch(`${API_BASE}/transits/daily`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) throw new Error(t("err_request_failed").replace("{status}", resp.status));
    const data = await resp.json();
    // Reflect the resolved date back so "Today" and the first load show it.
    document.getElementById("transit_date").value = data.transit_date;
    document.getElementById("transit_time").value = data.transit_time;
    lastTransitData = data;
    renderTransit(data);
  } catch (err) {
    summaryEl.textContent = t("err_could_not_load").replace("{message}", err.message);
  }
}

document.getElementById("horoscope-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("horoscope-error");
  const resultsEl = document.getElementById("horoscope-results");
  errorEl.hidden = true;

  const latitude = parseFloat(document.getElementById("dh_latitude").value);
  const longitude = parseFloat(document.getElementById("dh_longitude").value);
  if (Number.isNaN(latitude) || Number.isNaN(longitude)) {
    resultsEl.hidden = true;
    errorEl.textContent = t("err_need_place");
    errorEl.hidden = false;
    return;
  }

  horoscopePayload = {
    birth_datetime: `${document.getElementById("dh_birth_date").value}T${document.getElementById("dh_birth_time").value}`,
    latitude,
    longitude,
    ayanamsa: document.getElementById("dh_ayanamsa").value,
  };

  // Blank the date so the backend defaults to today in the birth place's
  // timezone rather than reusing whatever date was last browsed to.
  document.getElementById("transit_date").value = "";
  resultsEl.hidden = false;
  fetchAndRenderTransit();
});

document.getElementById("transit_prev").addEventListener("click", () => shiftTransitDate(-1));
document.getElementById("transit_next").addEventListener("click", () => shiftTransitDate(1));
document.getElementById("transit_today").addEventListener("click", () => {
  document.getElementById("transit_date").value = "";
  fetchAndRenderTransit();
});
document.getElementById("transit_date").addEventListener("change", fetchAndRenderTransit);
document.getElementById("transit_time").addEventListener("change", fetchAndRenderTransit);
document.getElementById("gochar_style").addEventListener("change", () => {
  if (lastTransitData) renderGocharChart(lastTransitData);
});

// Two independent tab levels: mode tabs (Birth Chart / Kundli Matching)
// and, inside the chart mode, result tabs. Scoped by attribute so one
// level's clicks never reset the other's active state.
document.querySelectorAll("[data-mode]").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("[data-mode]").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".mode-panel").forEach((p) => { p.hidden = true; });
    btn.classList.add("active");
    document.getElementById(`mode-${btn.dataset.mode}`).hidden = false;
  });
});

document.querySelectorAll("[data-tab]").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("[data-tab]").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => { p.hidden = true; });
    btn.classList.add("active");
    document.getElementById(`tab-${btn.dataset.tab}`).hidden = false;
  });
});

// ------------------------------- matching -------------------------------

function readPerson(prefix) {
  const id = (suffix) => document.getElementById(`${prefix}${suffix}`);
  const latitude = parseFloat(id("latitude").value);
  const longitude = parseFloat(id("longitude").value);
  const date = id("birth_date").value;
  const time = id("birth_time").value;
  return {
    valid: !Number.isNaN(latitude) && !Number.isNaN(longitude),
    payload: {
      name: id("name").value.trim(),
      birth_datetime: `${date}T${time}`,
      latitude,
      longitude,
    },
    label: id("name").value.trim() || (prefix === "bride_" ? "Bride" : "Groom"),
  };
}

function renderMatchResults(data, brideLabel, groomLabel) {
  document.getElementById("match-total").textContent = data.total;
  document.getElementById("match-verdict").textContent =
    t("verdicts")[data.interpretation] || data.interpretation;

  const moonBody = document.querySelector("#match-moon-table tbody");
  moonBody.innerHTML = `
    <tr><td>${brideLabel}</td><td>${tSign(data.bride_moon.sign_index)}</td><td>${tNak(data.bride_moon.nakshatra_index)}</td></tr>
    <tr><td>${groomLabel}</td><td>${tSign(data.groom_moon.sign_index)}</td><td>${tNak(data.groom_moon.nakshatra_index)}</td></tr>
  `;

  const kootaBody = document.querySelector("#koota-table tbody");
  kootaBody.innerHTML = data.kootas.map((k) => `
    <tr class="${k.score === 0 ? "koota-zero" : ""}">
      <td>${tKoota(k.name)}</td>
      <td>${tValue(k.bride)}</td>
      <td>${tValue(k.groom)}</td>
      <td>${k.score} / ${k.max}</td>
    </tr>
  `).join("") + `
    <tr class="koota-total"><td>${t("col_total")}</td><td></td><td></td><td>${data.total} / ${data.max_total}</td></tr>
  `;

  const mangalRow = (label, m) => `
    <tr>
      <td>${label}</td>
      <td>${m.from_lagna ? `Manglik (Mars in house ${m.mars_house_from_lagna})` : `No (Mars in house ${m.mars_house_from_lagna})`}</td>
      <td>${m.from_moon ? `Manglik (Mars in house ${m.mars_house_from_moon})` : `No (Mars in house ${m.mars_house_from_moon})`}</td>
    </tr>
  `;
  document.querySelector("#mangal-table tbody").innerHTML =
    mangalRow(brideLabel, data.bride_mangal) + mangalRow(groomLabel, data.groom_mangal);
}

document.getElementById("match-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("match-error");
  const resultsEl = document.getElementById("match-results");
  errorEl.hidden = true;
  resultsEl.hidden = true;

  const bride = readPerson("bride_");
  const groom = readPerson("groom_");
  if (!bride.valid || !groom.valid) {
    errorEl.textContent = t("err_need_both_places");
    errorEl.hidden = false;
    return;
  }

  try {
    const resp = await fetch(`${API_BASE}/matching/compute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        bride: bride.payload,
        groom: groom.payload,
        ayanamsa: document.getElementById("match_ayanamsa").value,
      }),
    });
    if (!resp.ok) {
      const detail = await resp.json().catch(() => ({}));
      throw new Error(detail.detail ? JSON.stringify(detail.detail)
        : t("err_request_failed").replace("{status}", resp.status));
    }
    const matchData = await resp.json();
    lastMatchData = { data: matchData, bride: bride.label, groom: groom.label };
    renderMatchResults(matchData, bride.label, groom.label);
    resultsEl.hidden = false;
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.hidden = false;
  }
});

let lastChartData = null;
document.getElementById("chart_style").addEventListener("change", () => {
  if (lastChartData) renderCharts(lastChartData.positions, lastChartData.vargas);
});
document.getElementById("varga_pick").addEventListener("change", () => {
  if (lastChartData) renderCharts(lastChartData.positions, lastChartData.vargas);
});

// ------------------------- iframe auto-height -------------------------
// When embedded (e.g. the WordPress page), report our content height to
// the parent so the iframe can grow to fit. Otherwise the iframe keeps a
// fixed height and gets its own inner scrollbar -- nested scrolling,
// which is awkward on desktop and genuinely bad on touch.
//
// Height is only ever sent, never received, and the message carries a
// type tag so the parent can ignore unrelated postMessage traffic. The
// parent still has to check event.origin before trusting it.
(function reportHeightToParent() {
  if (window.parent === window) return; // not embedded; nothing to do

  let lastHeight = 0;

  const send = () => {
    const height = Math.ceil(
      Math.max(
        document.body.scrollHeight,
        document.documentElement.scrollHeight,
        document.body.offsetHeight,
      )
    );
    // Only post on a real change, and ignore sub-pixel jitter that would
    // otherwise fire a message on every animation frame.
    if (Math.abs(height - lastHeight) < 2) return;
    lastHeight = height;
    window.parent.postMessage({ type: "grahika:height", height }, "*");
  };

  window.addEventListener("load", send);
  window.addEventListener("resize", send);

  // Results appear and tabs switch without any resize event, so watch the
  // DOM itself rather than relying on window events alone.
  if (typeof ResizeObserver !== "undefined") {
    new ResizeObserver(send).observe(document.body);
  } else {
    new MutationObserver(send).observe(document.body, {
      childList: true, subtree: true, attributes: true,
    });
  }

  send();
})();



// ----------------------------- panchangam -----------------------------

let panchangaPlace = null;
let lastPanchanga = null;

// The API sends indices beside every name, so the limbs localise the same
// way the rest of the app does -- from the response already in hand.
const tTithi = (d) =>
  d.name === "Pournami" ? TITHI_NAMES_I18N[lang()][14]
  : d.name === "Amavasya" ? TITHI_NAMES_I18N[lang()][15]
  : TITHI_NAMES_I18N[lang()][d.number - 1];
const tPaksha = (name) => PAKSHA_I18N[lang()][name] || name;
const tVara = (i) => VARA_I18N[lang()][i];

const tMasa = (name) => {
  const idx = MASA_ORDER.indexOf(name);
  return idx >= 0 ? MASA_I18N[lang()][idx] : name;
};
const tDirection = (d) => (DIRECTION_I18N[lang()] || {})[d] || d;
const tPhase = (n) => (MOON_PHASE_I18N[lang()] || {})[n] || n;
// FESTIVAL_I18N is null for English, where the API name is already right.
const tFestival = (n) => (FESTIVAL_I18N[lang()] || {})[n] || n;

function paCard(icon, label, value, sub) {
  return `<div class="pa-card">
    <div class="pa-label"><span class="pa-ico">${icon}</span>${label}</div>
    <div class="pa-value">${value}</div>
    <div class="pa-sub">${sub || ""}</div>
  </div>`;
}

// A limb often changes during the day, so each card lists every value in
// force with the moment it gives way -- which is how a printed almanac
// reads, and why one card can carry two or three lines.
function limbCard(icon, label, entries, nameFor) {
  const lines = entries.map((e) => `
    <div class="pa-line">
      <span class="pa-line-name">${nameFor(e)}</span>
      <span class="pa-line-time">${e.ends_at ? t("p_until") + " " + e.ends_at : t("p_all_day")}</span>
    </div>`).join("");
  return `<div class="pa-card">
    <div class="pa-label"><span class="pa-ico">${icon}</span>${label}</div>
    ${lines}
  </div>`;
}

function renderPanchanga(data) {
  lastPanchanga = data;
  document.getElementById("pa_date").value = data.date;
  document.getElementById("pa-date-label").textContent =
    `${formatChartDate(data.date)} \u00b7 ${tVara(data.vara.index)}`;

  const place = selectedPlaceNames["pa_"] || "";
  document.getElementById("pa-summary").textContent = t("p_summary")
    .replace("{date}", formatChartDate(data.date))
    .replace("{place}", place.split(",")[0] || "")
    .replace("{tithi}", tTithi(data.tithi))
    .replace("{ends}", data.tithi.ends_at || "")
    .replace("{sunrise}", data.sunrise || "--")
    .replace("{nakshatra}", tNak(data.nakshatra.index));

  // --- solar and lunar events ---
  document.getElementById("pa-events").innerHTML = [
    paCard("\u2600\ufe0f", t("p_sunrise"), data.sunrise || "--", ""),
    paCard("\ud83c\udf07", t("p_sunset"), data.sunset || "--", ""),
    paCard("\ud83c\udf19", t("p_moonrise"), data.moonrise || "--", ""),
    paCard("\ud83c\udf11", t("p_moonset"), data.moonset || "--", ""),
    paCard("\u2b50", t("p_sun_sign"), tSign(data.sun_sign.index), ""),
    paCard("\ud83c\udf13", t("p_moon_sign"), tSign(data.moon_sign.index), ""),
    paCard("\u2648", t("p_lagna"), tSign(data.lagna.index), ""),
  ].join("");

  // --- the five limbs ---
  const cards = [
    paCard("\ud83d\uddd3\ufe0f", t("p_masa"), tMasa(data.masa.name), ""),
    paCard("\ud83c\udf12", t("p_paksha"), tPaksha(data.tithi.paksha), ""),
    limbCard("\ud83c\udf19", t("p_tithi"), data.tithis, tTithi),
    limbCard("\u2728", t("p_nakshatra"), data.nakshatras, (e) => tNak(e.index)),
    limbCard("\u23f3", t("p_karana"), data.karanas,
             (e) => KARANA_I18N[lang()][e.name] || e.name),
    limbCard("\ud83d\udd2f", t("p_yoga"), data.yogas, (e) => YOGA_I18N[lang()][e.index]),
    paCard("\ud83e\udded", t("p_dishashool"), tDirection(data.dishashool), t("p_dishashool_note")),
  ];
  if (data.sankranti) {
    cards.push(paCard("\ud83d\udd05", t("p_sankranti"), tSign(data.sankranti.sign_index), ""));
  }
  document.getElementById("pa-limbs").innerHTML = cards.join("");

  // --- muhurats, auspicious first ---
  const period = (icon, label, w, tone) => {
    if (!w) return "";
    return `<div class="pa-period ${tone}">
      <span class="pa-period-name"><span class="pa-ico">${icon}</span>${label}</span>
      <span class="pa-period-time">${w.start} &ndash; ${w.end}</span>
    </div>`;
  };
  const per = data.periods || {};
  document.getElementById("pa-good").innerHTML =
    period("\ud83d\udd4a\ufe0f", t("p_brahma"), per.brahma, "good") +
    period("\u2b50", t("p_abhijit"), per.abhijit, "good") +
    period("\ud83c\udf05", t("p_godhuli"), per.godhuli, "good");

  const durmuhurtas = (per.durmuhurta || [])
    .map((w) => period("\u26a0\ufe0f", t("p_durmuhurta"), w, "bad")).join("");
  document.getElementById("pa-bad").innerHTML =
    period("\u26a0\ufe0f", t("p_rahu"), per.rahu_kalam, "bad") +
    period("\u26a0\ufe0f", t("p_yama"), per.yamagandam, "bad") +
    period("\u26a0\ufe0f", t("p_gulika"), per.gulika_kalam, "bad") +
    durmuhurtas +
    period("\u26a0\ufe0f", t("p_varjyam"), per.varjyam, "bad");

  // --- sidebar ---
  const hours = data.day_length_minutes
    ? `${Math.floor(data.day_length_minutes / 60)}h ${data.day_length_minutes % 60}m` : "--";
  const sideRow = (label, value) =>
    `<div class="pa-side-row"><span>${label}</span><b>${value}</b></div>`;
  document.getElementById("pa-location").innerHTML =
    (place ? `<div class="pa-side-place">${place}</div>` : "") +
    sideRow(t("p_day_length"), hours) +
    sideRow(t("p_moon_phase"), tPhase(data.moon_phase.name)) +
    sideRow(t("p_sunrise"), data.sunrise || "--") +
    sideRow(t("p_sunset"), data.sunset || "--");

  const festivalCard = document.getElementById("pa-festival-card");
  if (data.festivals && data.festivals.length) {
    document.getElementById("pa-festivals").innerHTML = data.festivals.map((f) => `
      <div class="pa-festival${f.major ? " major" : ""}">
        <span>${tFestival(f.name)}</span><span class="pa-festival-kind">${tFestival(f.kind)}</span>
      </div>`).join("");
    festivalCard.hidden = false;
  } else {
    festivalCard.hidden = true;
  }
}

async function fetchPanchanga() {
  if (!panchangaPlace) return;
  const errorEl = document.getElementById("panchanga-error");
  errorEl.hidden = true;
  const chosen = document.getElementById("pa_date").value;
  const payload = { ...panchangaPlace };
  if (chosen) payload.date = chosen;
  try {
    const resp = await fetch(`${API_BASE}/panchanga/daily`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) throw new Error(t("err_request_failed").replace("{status}", resp.status));
    renderPanchanga(await resp.json());
    document.getElementById("panchanga-results").hidden = false;
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.hidden = false;
  }
}

function shiftPanchangaDate(days) {
  const input = document.getElementById("pa_date");
  const base = input.value ? new Date(`${input.value}T12:00:00`) : new Date();
  base.setDate(base.getDate() + days);
  const pad = (n) => String(n).padStart(2, "0");
  input.value = `${base.getFullYear()}-${pad(base.getMonth() + 1)}-${pad(base.getDate())}`;
  fetchPanchanga();
}

document.getElementById("panchanga-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("panchanga-error");
  const lat = parseFloat(document.getElementById("pa_latitude").value);
  const lon = parseFloat(document.getElementById("pa_longitude").value);
  if (Number.isNaN(lat) || Number.isNaN(lon)) {
    document.getElementById("panchanga-results").hidden = true;
    errorEl.textContent = t("err_need_place");
    errorEl.hidden = false;
    return;
  }
  panchangaPlace = { latitude: lat, longitude: lon };
  document.getElementById("pa_date").value = "";
  fetchPanchanga();
});

document.getElementById("pa_prev").addEventListener("click", () => shiftPanchangaDate(-1));
document.getElementById("pa_next").addEventListener("click", () => shiftPanchangaDate(1));
document.getElementById("pa_today").addEventListener("click", () => {
  document.getElementById("pa_date").value = "";
  fetchPanchanga();
});
document.getElementById("pa_date").addEventListener("change", fetchPanchanga);


// ---------------------------- ishta devata ----------------------------

let lastIshta = null;

const tDeity = (n) => DEITY_I18N[lang()][n] || n;
const tKaraka = (n) => KARAKA_I18N[lang()][n] || n;
const tKarakaMeaning = (k) =>
  lang() === "te" ? (KARAKA_MEANING_TE[k.karaka] || k.meaning) : k.meaning;

function renderIshta(data) {
  lastIshta = data;
  document.getElementById("devata-name").textContent = tDeity(data.deity.primary);
  document.getElementById("devata-alt").textContent =
    `${t("id_also")} ${tDeity(data.deity.alternate)}`;

  const card = (label, value, sub) => `
    <div class="pa-card">
      <div class="pa-label">${label}</div>
      <div class="pa-value">${value}</div>
      <div class="pa-sub">${sub || ""}</div>
    </div>`;

  document.getElementById("ishta-facts").innerHTML = [
    card(t("id_atmakaraka"), tPlanet(data.atmakaraka),
         `${data.atmakaraka_degree.toFixed(2)}\u00b0`),
    card(t("id_karakamsha"), tSign(data.karakamsha_sign_index), ""),
    card(t("id_twelfth"), tSign(data.twelfth_sign_index),
         data.occupants.length ? data.occupants.map(tPlanet).join(", ") : ""),
    card(t("id_indicator"), tPlanet(data.indicator_planet), ""),
  ].join("");

  document.querySelector("#karaka-table tbody").innerHTML = data.karakas.map((k) => `
    <tr${k.karaka === "Atmakaraka" ? ' class="karaka-ak"' : ""}>
      <td>${tKaraka(k.karaka)}</td>
      <td>${tPlanet(k.planet)}</td>
      <td>${k.degree.toFixed(2)}&deg;</td>
      <td>${tKarakaMeaning(k)}</td>
    </tr>`).join("");
}

document.getElementById("ishta-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("ishta-error");
  const resultsEl = document.getElementById("ishta-results");
  errorEl.hidden = true;

  const q = (id) => document.getElementById(id);
  const latitude = parseFloat(q("id_latitude").value);
  const longitude = parseFloat(q("id_longitude").value);
  if (Number.isNaN(latitude) || Number.isNaN(longitude)) {
    resultsEl.hidden = true;
    errorEl.textContent = t("err_need_place");
    errorEl.hidden = false;
    return;
  }

  try {
    const resp = await fetch(`${API_BASE}/jaimini/ishta-devata`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        birth_datetime: `${q("id_birth_date").value}T${q("id_birth_time").value}`,
        latitude, longitude,
      }),
    });
    if (!resp.ok) {
      const detail = await resp.json().catch(() => ({}));
      throw new Error(detail.detail ? JSON.stringify(detail.detail)
        : t("err_request_failed").replace("{status}", resp.status));
    }
    renderIshta(await resp.json());
    resultsEl.hidden = false;
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.hidden = false;
  }
});


// ------------------------- shodashavarga table -------------------------

const VARGA_CODES = ["D1","D2","D3","D4","D7","D9","D10","D12",
                     "D16","D20","D24","D27","D30","D40","D45","D60"];
const CHART_BODIES = ["Ascendant","Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"];

function renderShodashavarga(vargas) {
  // Sixteen columns is wide on purpose; the table scrolls inside its own
  // block rather than widening the page.
  document.querySelector("#shodashavarga-table thead tr").innerHTML =
    `<th>${t("col_graha")}</th>` + VARGA_CODES.map((c) => `<th>${c}</th>`).join("");

  document.querySelector("#shodashavarga-table tbody").innerHTML =
    CHART_BODIES.filter((b) => vargas[b]).map((body) => `
      <tr>
        <td>${tPlanet(body)}</td>
        ${VARGA_CODES.map((c) => `<td>${tSignShort(vargas[body][c].sign_index)}</td>`).join("")}
      </tr>`).join("");
}

// ------------------------------- reports -------------------------------

// A report is an ordered assembly of sections the app already renders, so
// it stays in step with the tabs automatically rather than duplicating them.
const REPORT_SECTIONS = {
  pocket: ["details", "charts", "avakhada", "positions", "running", "dasha", "aspects"],
  calculative: ["details", "charts", "avakhada", "positions", "shodashavarga",
                "running", "dasha", "dashaChain", "aspects"],
};

let lastReport = null;

function reportSection(title, bodyHtml) {
  return `<section class="report-section">
    <h2>${title}</h2>
    ${bodyHtml}
  </section>`;
}

function tableFrom(headers, rows) {
  return `<div class="table-block"><table>
    <thead><tr>${headers.map((x) => `<th>${x}</th>`).join("")}</tr></thead>
    <tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody>
  </table></div>`;
}

function buildReport(kind, data, meta) {
  const out = [];
  const has = (name) => REPORT_SECTIONS[kind].includes(name);

  if (has("details")) {
    const av = data.avakhada;
    out.push(reportSection(t("h_birth_details"), tableFrom([], [
      [t("row_name"), meta.name || "\u2014"],
      [t("row_birth_date"), formatChartDate(meta.date)],
      [t("row_birth_time"), formatChartTime(meta.time)],
      [t("row_place"), meta.place],
      [t("row_rasi"), tSign(av.rasi.index)],
      [t("row_nakshatra"), `${tNak(av.nakshatra.index)} (${av.pada})`],
      [t("av_lagna"), tSign(av.lagna.index)],
    ])));
  }

  if (has("charts")) {
    const d1 = (n) => data.vargas[n].D1.sign_index;
    const d9 = (n) => data.vargas[n].D9.sign_index;
    const centre = (label, varga) => ({
      dateLabel: formatChartDate(meta.date), timeLabel: formatChartTime(meta.time),
      chartLabel: label, vargaLabel: varga,
      ascSignName: tSignShort(data.positions.Ascendant.sign_index),
    });
    out.push(reportSection(t("h_positions") + " \u00b7 D1 / D9", `<div class="charts">
      <div class="chart-block">${buildSouthIndianSvg(data.positions, d1, true, centre(t("chart_lagna"), t("varga_names").D1))}</div>
      <div class="chart-block">${buildSouthIndianSvg(data.positions, d9, true, centre(t("varga_names").D9, t("varga_names").D9))}</div>
    </div>`));
  }

  if (has("avakhada")) {
    const av = data.avakhada;
    out.push(reportSection(t("h_avakhada"), tableFrom([], [
      [t("av_rasi_lord"), tPlanet(av.rasi_lord)],
      [t("av_nak_lord"), tPlanet(av.nakshatra_lord)],
      [t("av_namakshar"), tNamakshar(av.nakshatra.index, av.pada, av.namakshar)],
      [t("av_tatva"), tValue(av.tatva)], [t("av_varna"), tValue(av.varna)],
      [t("av_vashya"), tValue(av.vashya)], [t("av_yoni"), tValue(av.yoni)],
      [t("av_gana"), tValue(av.gana)], [t("av_nadi"), tValue(av.nadi)],
    ])));
  }

  if (has("positions")) {
    out.push(reportSection(t("h_positions"), tableFrom(
      [t("col_body"), t("col_sign"), t("col_degree"), t("col_nakshatra"), t("col_pada"), t("col_retro")],
      Object.entries(data.positions).map(([name, d]) => [
        tPlanet(name), tSign(d.sign_index), d.degree_in_sign.toFixed(2) + "\u00b0",
        tNak(d.nakshatra_index), d.nakshatra_pada, d.retrograde ? t("retro_mark") : "",
      ])
    )));
  }

  if (has("shodashavarga")) {
    out.push(reportSection(t("h_shodashavarga"), tableFrom(
      [t("col_graha"), ...VARGA_CODES],
      CHART_BODIES.filter((b) => data.vargas[b]).map((body) => [
        tPlanet(body), ...VARGA_CODES.map((c) => tSignShort(data.vargas[body][c].sign_index)),
      ])
    )));
  }

  if (has("running")) {
    const cp = data.current_periods;
    const rows = [];
    if (cp.mahadasha) rows.push([t("dp_maha"), tPlanet(cp.mahadasha.lord), periodDates(cp.mahadasha)]);
    if (cp.antardasha) rows.push([t("dp_antar"), tPlanet(cp.antardasha.lord), periodDates(cp.antardasha)]);
    if (cp.next_antardasha) rows.push([t("dp_next"), tPlanet(cp.next_antardasha.lord), periodDates(cp.next_antardasha)]);
    out.push(reportSection(t("h_running"), tableFrom([], rows)));
  }

  if (has("dasha")) {
    out.push(reportSection(t("h_dasha"), tableFrom(
      [t("col_lord"), t("col_start"), t("col_end"), t("col_years")],
      data.vimshottari_dasha.map((p) => [
        tPlanet(p.lord), formatChartDate(p.start.slice(0, 10)),
        formatChartDate(p.end.slice(0, 10)), p.years,
      ])
    )));
  }

  // The calculative report goes a level deeper: every antardasha of the
  // running mahadasha, with its pratyantardashas listed under it.
  if (has("dashaChain") && data.current_periods.antardashas) {
    const inner = data.current_periods.antardashas.map((ad) => {
      const pds = antardashaRows({ lord: ad.lord, start: ad.start, years: ad.years });
      return `<h3 class="report-subhead">${tPlanet(ad.lord)} \u00b7 ${periodDates(ad)}</h3>` +
        tableFrom([t("col_lord"), t("col_start"), t("col_end")],
          pds.map((p) => [tPlanet(p.lord), formatChartDate(p.start), formatChartDate(p.end)]));
    }).join("");
    out.push(reportSection(t("dp_antar") + " \u00b7 " + t("dp_next"), inner));
  }

  if (has("aspects")) {
    const byPlanet = {};
    for (const row of data.natal_aspects.on_planets) {
      byPlanet[row.planet] = row.aspects.map((x) => tPlanet(x.planet)).join(", ");
    }
    out.push(reportSection(t("h_natal_aspects"), tableFrom(
      [t("col_graha"), t("col_aspects_planets"), t("col_aspects_houses")],
      data.natal_aspects.on_bhavas.map((row) => [
        tPlanet(row.planet), byPlanet[row.planet] || "\u2014", row.houses.join(", "),
      ])
    )));
  }

  return `<h1 class="report-title">${t("rp_for")} ${meta.name || ""}</h1>` + out.join("");
}

function renderReport() {
  if (!lastReport) return;
  document.getElementById("report-body").innerHTML =
    buildReport(lastReport.kind, lastReport.data, lastReport.meta);
}

document.getElementById("report-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("report-error");
  const resultsEl = document.getElementById("report-results");
  errorEl.hidden = true;

  const q = (id) => document.getElementById(id);
  const latitude = parseFloat(q("rp_latitude").value);
  const longitude = parseFloat(q("rp_longitude").value);
  if (Number.isNaN(latitude) || Number.isNaN(longitude)) {
    resultsEl.hidden = true;
    errorEl.textContent = t("err_need_place");
    errorEl.hidden = false;
    return;
  }

  const date = q("rp_birth_date").value;
  const time = q("rp_birth_time").value;
  try {
    const resp = await fetch(`${API_BASE}/charts/compute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ birth_datetime: `${date}T${time}`, latitude, longitude }),
    });
    if (!resp.ok) throw new Error(t("err_request_failed").replace("{status}", resp.status));
    lastReport = {
      kind: q("report_kind").value,
      data: await resp.json(),
      meta: {
        name: q("rp_name").value.trim(), date, time,
        place: selectedPlaceNames["rp_"] || `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`,
      },
    };
    renderReport();
    resultsEl.hidden = false;
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.hidden = false;
  }
});

document.getElementById("report_kind").addEventListener("change", () => {
  if (lastReport) { lastReport.kind = document.getElementById("report_kind").value; renderReport(); }
});
document.getElementById("report_print").addEventListener("click", () => window.print());

// --------------------------- language switch ---------------------------

let lastTransitData = null;
let lastMatchData = null;

// Static markup carries data-i18n. Elements that also contain an <input>
// (labels) get only their first text node replaced, so the field survives.
function applyTranslations() {
  document.documentElement.lang = lang();
  document.title = t("title") + " - " + t("subtitle");

  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const value = t(el.dataset.i18n);
    if (typeof value !== "string") return;
    const firstText = [...el.childNodes].find(
      (n) => n.nodeType === Node.TEXT_NODE && n.textContent.trim()
    );
    if (el.children.length && firstText) firstText.textContent = value + " ";
    else el.textContent = value;
  });

  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  });

  document.querySelectorAll(".lang-btn").forEach((b) => {
    b.classList.toggle("active", b.dataset.lang === lang());
  });
}

// Re-render whatever is already on screen from responses we still hold, so
// switching language never costs another request.
function rerenderAll() {
  if (lastChartData) {
    renderCharts(lastChartData.positions, lastChartData.vargas);
    renderPositionsTable(lastChartData.positions);
    renderDashaTable(lastChartData.vimshottari_dasha, lastChartData.current_periods);
    renderAvakhada(lastChartData.avakhada);
    renderCurrentPeriods(lastChartData.current_periods);
    renderNatalAspects(lastChartData.natal_aspects);
    renderShodashavarga(lastChartData.vargas);
    if (lastDetailsArgs) renderDetailsTable(lastDetailsArgs);
    if (lastDoshaData) renderDoshas(lastDoshaData);
  }
  if (lastTransitData) renderTransit(lastTransitData);
  if (lastPanchanga) renderPanchanga(lastPanchanga);
  if (lastIshta) renderIshta(lastIshta);
  if (lastReport) renderReport();
  if (lastMatchData) {
    renderMatchResults(lastMatchData.data, lastMatchData.bride, lastMatchData.groom);
  }
}

document.querySelectorAll(".lang-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    setLang(btn.dataset.lang);
    applyTranslations();
    rerenderAll();
  });
});

// The parent-site bar is shown only when this page is the top-level
// document. Embedded in an iframe the host page already supplies its own
// header, and two stacked bars look like a mistake.
(function revealSiteBar() {
  if (window.parent === window) {
    const bar = document.getElementById("site-bar");
    if (bar) bar.hidden = false;
  }
})();

applyTranslations();
