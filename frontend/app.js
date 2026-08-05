const API_BASE = ""; // same origin -- backend serves this page

const PLANET_ABBR = {
  Sun: "Su", Moon: "Mo", Mars: "Ma", Mercury: "Me", Jupiter: "Ju",
  Venus: "Ve", Saturn: "Sa", Rahu: "Ra", Ketu: "Ke", Ascendant: "As",
};

const SIGN_SHORT = [
  "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
  "Libra", "Scorpi", "Sagitt", "Capric", "Aquari", "Pisces",
];
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
    const abbr = PLANET_ABBR[name] || name.slice(0, 2);
    if (!bodies[name] || !bodies[name].retrograde) return abbr;
    return `${abbr}<tspan font-size="65%" dy="-5" fill="${C.retro}">R</tspan><tspan dy="5"></tspan>`;
  }).join("&#160;");
}

// Planets are laid out in rows of at most three so a stellium doesn't
// overflow its cell.
function planetRows(names, bodies, x, y, size) {
  const rows = [];
  for (let i = 0; i < names.length; i += 3) rows.push(names.slice(i, i + 3));
  const startY = y - ((rows.length - 1) * (size + 2)) / 2;
  return rows.map((row, i) => `
    <text x="${x}" y="${startY + i * (size + 2)}" font-size="${size}" font-weight="700"
          fill="${C.planet}" text-anchor="middle" dominant-baseline="middle"
          font-family="Georgia, serif">${planetMarkup(row, bodies)}</text>
  `).join("");
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

function buildNorthIndianSvg(bodies, signIndexFor) {
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

  let regions = "";
  for (let h = 1; h <= 12; h++) {
    const r = NORTH_REGIONS[h - 1];
    const rashi = ((ascSignIndex + h - 1) % 12) + 1;
    regions += `<polygon points="${r.poly}" fill="${h === 1 ? C.bgAsc : C.bg}" stroke="none"/>`;
    regions += `<text x="${r.num[0]}" y="${r.num[1]}" font-size="13" font-weight="700"
                      fill="${C.signNum}" text-anchor="middle">${rashi}</text>`;
    regions += planetRows(byHouse[h], bodies, r.planets[0], r.planets[1], 15);
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

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

function formatChartDate(dateStr) {
  if (!dateStr) return "";
  const [y, m, d] = dateStr.split("-").map(Number);
  return `${d} - ${MONTH_NAMES[m - 1]} - ${y}`;
}

function formatChartTime(timeStr) {
  if (!timeStr) return "";
  const [h, m, s] = timeStr.split(":").map(Number);
  const period = h >= 12 ? "PM" : "AM";
  const h12 = ((h + 11) % 12) + 1;
  const pad = (n) => String(n).padStart(2, "0");
  return `${pad(h12)}:${pad(m)}:${pad(s || 0)} ${period}`;
}

function buildSouthIndianSvg(bodies, signIndexFor, mirrored, centerInfo) {
  const cellFor = mirrored ? SOUTH_INDIAN_CELLS_APASAVYA : SOUTH_INDIAN_CELLS_SAVYA;
  const ascSignIndex = signIndexFor("Ascendant");

  // As above: the Lagna is carried by the shaded cell and the centre
  // caption, not by an "As" token among the grahas.
  const bySign = {};
  for (let s = 0; s < 12; s++) bySign[s] = [];
  for (const name of Object.keys(bodies)) {
    if (name === "Ascendant") continue;
    bySign[signIndexFor(name)].push(name);
  }

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
                    fill="${C.signName}">${SIGN_SHORT[s]}</text>`;
    cells += `<text x="${x + CELL - 9}" y="${y + 20}" font-size="10" fill="${C.houseNum}"
                    text-anchor="end">H${house}</text>`;
    cells += planetRows(bySign[s], bodies, x + CELL / 2, y + CELL / 2 + 8, 15);
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
            text-anchor="middle" font-family="Georgia, serif">${centerInfo.chartLabel} Chart</text>
      <text x="200" y="232" font-size="14" fill="${C.centerTitle}" text-anchor="middle">
        Asc: ${ascGlyph} ${ascName}
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
  const moonNakshatra = positions.Moon.nakshatra;

  const build = (signIndexFor, chartLabel, vargaLabel) => {
    const centerInfo = {
      dateLabel, timeLabel, chartLabel, vargaLabel, moonNakshatra,
      ascSignName: SIGN_SHORT[signIndexFor("Ascendant")],
    };
    if (style === "south_savya") return buildSouthIndianSvg(positions, signIndexFor, false, centerInfo);
    if (style === "south_apasavya") return buildSouthIndianSvg(positions, signIndexFor, true, centerInfo);
    return buildNorthIndianSvg(positions, signIndexFor);
  };

  const caption = style === "north"
    ? `<p class="chart-caption">${dateLabel}, ${timeLabel} &middot; Moon: ${moonNakshatra}</p>`
    : "";

  document.getElementById("d1-chart").innerHTML = build(d1SignIndex, "Lagna", "D1 &middot; Rashi") + caption;
  document.getElementById("d9-chart").innerHTML = build(d9SignIndex, "Navamsha", "D9 &middot; Navamsha") + caption;
}

function renderDetailsTable({ name, dateLabel, timeLabel, placeLabel, moon, ayanamsaLabel }) {
  const tbody = document.querySelector("#details-table tbody");
  const rows = [];
  if (name) rows.push(["Name", name]);
  rows.push(["Birth Date", dateLabel]);
  rows.push(["Birth Time", timeLabel]);
  rows.push(["Place of Birth", placeLabel]);
  rows.push(["Nakshatra", moon.nakshatra]);
  rows.push(["Rasi", moon.sign]);
  rows.push(["Ayanamsa", ayanamsaLabel]);
  tbody.innerHTML = rows.map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`).join("");
}

function renderPositionsTable(positions) {
  const tbody = document.querySelector("#positions-table tbody");
  tbody.innerHTML = "";
  for (const [name, d] of Object.entries(positions)) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${name}</td>
      <td>${d.sign}</td>
      <td>${d.degree_in_sign.toFixed(2)}&deg;</td>
      <td>${d.nakshatra}</td>
      <td>${d.nakshatra_pada}</td>
      <td>${d.retrograde ? "R" : ""}</td>
    `;
    tbody.appendChild(tr);
  }
}

function renderDashaTable(periods) {
  const tbody = document.querySelector("#dasha-table tbody");
  tbody.innerHTML = "";
  for (const p of periods) {
    const tr = document.createElement("tr");
    const start = new Date(p.start).toLocaleDateString();
    const end = new Date(p.end).toLocaleDateString();
    tr.innerHTML = `<td>${p.lord}</td><td>${start}</td><td>${end}</td><td>${p.years}</td>`;
    tbody.appendChild(tr);
  }
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
  if (!resp.ok) throw new Error(`Place lookup failed (${resp.status})`);
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
        resultsEl.innerHTML = `<li class="place-empty">No matches -- try adding the country</li>`;
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
    errorEl.textContent = "Search for a birth place above, or expand \"Enter coordinates manually\" and fill in latitude/longitude.";
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
      throw new Error(detail.detail ? JSON.stringify(detail.detail) : `Request failed (${resp.status})`);
    }
    const data = await resp.json();
    lastChartData = data;
    renderCharts(data.positions, data.vargas);
    renderPositionsTable(data.positions);
    renderDashaTable(data.vimshottari_dasha);
    renderDetailsTable({
      name: document.getElementById("person_name").value.trim(),
      dateLabel: formatChartDate(date),
      timeLabel: formatChartTime(time),
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

async function fetchAndRenderDoshas(payload) {
  const kaalEl = document.getElementById("kaal-sarp-result");
  const sadeEl = document.getElementById("sade-sati-result");
  kaalEl.textContent = "Loading…";
  sadeEl.textContent = "Loading…";
  try {
    const resp = await fetch(`${API_BASE}/charts/doshas`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) throw new Error(`Request failed (${resp.status})`);
    const data = await resp.json();

    const ksy = data.kaal_sarp_yoga;
    kaalEl.textContent = ksy.present
      ? `Present -- all 7 classical planets fall between Rahu and Ketu (${ksy.direction}).`
      : "Not present.";

    const ss = data.sade_sati;
    if (ss.in_sade_sati) {
      sadeEl.textContent = `Currently in Sade Sati (${ss.phase} phase), approximately ${ss.current_window_start} to ${ss.current_window_end}.`;
    } else if (ss.next_window_start) {
      sadeEl.textContent = `Not currently in Sade Sati. Next window begins around ${ss.next_window_start}.`;
    } else {
      sadeEl.textContent = "Not currently in Sade Sati.";
    }
  } catch (err) {
    kaalEl.textContent = `Couldn't load: ${err.message}`;
    sadeEl.textContent = `Couldn't load: ${err.message}`;
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
  document.getElementById("transit-moon-summary").textContent =
    `Moon transits ${data.transit_moon.sign} (${data.transit_moon.nakshatra}). ` +
    `Your natal Moon is in ${data.natal_moon.sign} (${data.natal_moon.nakshatra}).`;

  const asItems = (lines) => lines.map((p) => `<li>${p}</li>`).join("");
  document.getElementById("summary-headline").textContent = data.summary.headline;
  document.getElementById("summary-today").innerHTML = asItems(data.summary.today);
  document.getElementById("summary-ongoing").innerHTML = asItems(data.summary.ongoing);
  document.getElementById("summary-ongoing-block").hidden = data.summary.ongoing.length === 0;

  const tara = data.tara_bala;
  document.getElementById("tara-name").textContent = `${tara.number}. ${tara.name}`;
  document.getElementById("tara-text").textContent = tara.description;
  const taraPill = document.getElementById("tara-quality");
  taraPill.textContent = tara.quality;
  taraPill.className = `quality-pill quality-${tara.quality}`;

  const chandra = data.chandra_bala;
  document.getElementById("chandra-name").textContent =
    `House ${chandra.house} (${chandra.bhava})`;
  document.getElementById("chandra-text").textContent = chandra.description;
  const chandraPill = document.getElementById("chandra-quality");
  chandraPill.textContent = chandra.quality;
  chandraPill.className = `quality-pill quality-${chandra.quality}`;

  const aspectsEl = document.getElementById("transit-aspects");
  aspectsEl.innerHTML = data.aspects.length
    ? data.aspects.map((a) => `
        <li>
          <div class="aspect-headline">
            Transiting ${a.transit_planet} in ${a.transit_sign} is ${a.relation}
            your natal ${a.natal_point} in ${a.natal_sign}
          </div>
          <div class="aspect-note">${a.note}</div>
        </li>
      `).join("")
    : `<li class="aspect-empty">No aspects from the slow grahas on your Lagna, Moon or Sun today.</li>`;

  document.querySelector("#transit-table tbody").innerHTML = data.planet_transits.map((p) => `
    <tr>
      <td>${p.planet}</td>
      <td>${p.sign}</td>
      <td>${p.degree_in_sign.toFixed(2)}&deg;</td>
      <td>${p.nakshatra}</td>
      <td>${p.house_from_moon}</td>
      <td>${p.house_from_lagna}</td>
      <td>${p.retrograde ? "R" : ""}</td>
    </tr>
  `).join("");
}

async function fetchAndRenderTransit() {
  if (!horoscopePayload) return;
  const summaryEl = document.getElementById("transit-moon-summary");
  summaryEl.textContent = "Loading…";

  const selectedDate = document.getElementById("transit_date").value;
  const payload = { ...horoscopePayload };
  if (selectedDate) payload.transit_date = selectedDate;

  try {
    const resp = await fetch(`${API_BASE}/transits/daily`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) throw new Error(`Request failed (${resp.status})`);
    const data = await resp.json();
    // Reflect the resolved date back so "Today" and the first load show it.
    document.getElementById("transit_date").value = data.transit_date;
    renderTransit(data);
  } catch (err) {
    summaryEl.textContent = `Couldn't load transit: ${err.message}`;
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
    errorEl.textContent = "Search for your birth place above, or expand \"Enter coordinates manually\" and fill in latitude/longitude.";
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
  document.getElementById("match-verdict").textContent = data.interpretation;

  const moonBody = document.querySelector("#match-moon-table tbody");
  moonBody.innerHTML = `
    <tr><td>${brideLabel}</td><td>${data.bride_moon.sign}</td><td>${data.bride_moon.nakshatra}</td></tr>
    <tr><td>${groomLabel}</td><td>${data.groom_moon.sign}</td><td>${data.groom_moon.nakshatra}</td></tr>
  `;

  const kootaBody = document.querySelector("#koota-table tbody");
  kootaBody.innerHTML = data.kootas.map((k) => `
    <tr class="${k.score === 0 ? "koota-zero" : ""}">
      <td>${k.name}</td>
      <td>${k.bride}</td>
      <td>${k.groom}</td>
      <td>${k.score} / ${k.max}</td>
    </tr>
  `).join("") + `
    <tr class="koota-total"><td>Total</td><td></td><td></td><td>${data.total} / ${data.max_total}</td></tr>
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
    errorEl.textContent = "Search for a birth place for both people (or enter coordinates manually).";
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
      throw new Error(detail.detail ? JSON.stringify(detail.detail) : `Request failed (${resp.status})`);
    }
    renderMatchResults(await resp.json(), bride.label, groom.label);
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
