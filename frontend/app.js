const API_BASE = ""; // same origin -- backend serves this page

const PLANET_ABBR = {
  Sun: "Su", Moon: "Mo", Mars: "Ma", Mercury: "Me", Jupiter: "Ju",
  Venus: "Ve", Saturn: "Sa", Rahu: "Ra", Ketu: "Ke", Ascendant: "As",
};

// North Indian diamond chart: fixed house positions (1 = top kite, then
// clockwise). Only the label anchor points are precise here; the dividing
// lines are the standard square + diagonals + inner diamond construction.
const HOUSE_LABEL_POS = [
  [150, 50], [215, 35], [265, 85], [250, 150], [265, 215], [215, 265],
  [150, 250], [85, 265], [35, 215], [50, 150], [35, 85], [85, 35],
];

function houseOf(bodySignIndex, ascSignIndex) {
  return ((bodySignIndex - ascSignIndex + 12) % 12) + 1;
}

function buildNorthIndianSvg(bodies, signIndexFor) {
  const ascSignIndex = signIndexFor("Ascendant");
  const byHouse = {};
  for (let h = 1; h <= 12; h++) byHouse[h] = { sign: ((ascSignIndex + h - 1) % 12) + 1, planets: [] };

  for (const [name, data] of Object.entries(bodies)) {
    const h = houseOf(signIndexFor(name), ascSignIndex);
    byHouse[h].planets.push(PLANET_ABBR[name] || name.slice(0, 2));
  }

  const lines = `
    <polygon points="0,0 300,0 300,300 0,300" fill="none" stroke-width="2"/>
    <line x1="0" y1="0" x2="300" y2="300" stroke-width="1"/>
    <line x1="300" y1="0" x2="0" y2="300" stroke-width="1"/>
    <polygon points="150,0 300,150 150,300 0,150" fill="none" stroke-width="1"/>
  `;

  let labels = "";
  for (let h = 1; h <= 12; h++) {
    const [x, y] = HOUSE_LABEL_POS[h - 1];
    const info = byHouse[h];
    labels += `
      <text x="${x}" y="${y - 6}" font-size="8" opacity="0.6" text-anchor="middle">${info.sign}</text>
      <text x="${x}" y="${y + 8}" font-size="11" font-weight="600" text-anchor="middle">${info.planets.join(",")}</text>
    `;
  }

  return `<svg viewBox="0 0 300 300" width="300" height="300">${lines}${labels}</svg>`;
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

function buildSouthIndianSvg(bodies, signIndexFor, mirrored) {
  const cellFor = mirrored ? SOUTH_INDIAN_CELLS_APASAVYA : SOUTH_INDIAN_CELLS_SAVYA;
  const ascSignIndex = signIndexFor("Ascendant");

  const bySign = {};
  for (let s = 0; s < 12; s++) bySign[s] = [];
  for (const name of Object.keys(bodies)) {
    bySign[signIndexFor(name)].push(PLANET_ABBR[name] || name.slice(0, 2));
  }

  const CELL = 80;
  const lines = `
    <polygon points="0,0 320,0 320,320 0,320" fill="none" stroke-width="2"/>
    <polygon points="80,80 240,80 240,240 80,240" fill="none" stroke-width="1"/>
    <line x1="160" y1="0" x2="160" y2="80" stroke-width="1"/>
    <line x1="160" y1="240" x2="160" y2="320" stroke-width="1"/>
    <line x1="0" y1="160" x2="80" y2="160" stroke-width="1"/>
    <line x1="240" y1="160" x2="320" y2="160" stroke-width="1"/>
  `;

  let cells = "";
  for (let s = 0; s < 12; s++) {
    const [row, col] = cellFor[s];
    const x = col * CELL;
    const y = row * CELL;
    const isAsc = s === ascSignIndex;
    if (isAsc) {
      cells += `<rect x="${x + 2}" y="${y + 2}" width="${CELL - 4}" height="${CELL - 4}" fill="none" stroke-width="2" stroke-dasharray="4,2"/>`;
    }
    cells += `
      <text x="${x + 10}" y="${y + 16}" font-size="9" opacity="0.6">${s + 1}</text>
      <text x="${x + CELL / 2}" y="${y + CELL / 2 + 6}" font-size="11" font-weight="600" text-anchor="middle">${bySign[s].join(",")}</text>
    `;
  }

  return `<svg viewBox="0 0 320 320" width="320" height="320">${lines}${cells}</svg>`;
}

function renderCharts(positions, vargas) {
  const style = document.getElementById("chart_style").value;
  const d1SignIndex = (name) => vargas[name].D1.sign_index;
  const d9SignIndex = (name) => vargas[name].D9.sign_index;

  const build = (signIndexFor) => {
    if (style === "south_savya") return buildSouthIndianSvg(positions, signIndexFor, false);
    if (style === "south_apasavya") return buildSouthIndianSvg(positions, signIndexFor, true);
    return buildNorthIndianSvg(positions, signIndexFor);
  };

  document.getElementById("d1-chart").innerHTML = build(d1SignIndex);
  document.getElementById("d9-chart").innerHTML = build(d9SignIndex);
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
      <td>${d.nakshatra} (${d.nakshatra_pada})</td>
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

document.getElementById("place_search_btn").addEventListener("click", async () => {
  const errorEl = document.getElementById("error");
  const query = document.getElementById("place_query").value.trim();
  const resultsEl = document.getElementById("place_results");
  resultsEl.innerHTML = "";
  errorEl.hidden = true;
  if (query.length < 2) return;

  try {
    const resp = await fetch(`${API_BASE}/geocode/search?q=${encodeURIComponent(query)}`);
    if (!resp.ok) throw new Error(`Place lookup failed (${resp.status})`);
    const places = await resp.json();
    if (places.length === 0) {
      resultsEl.innerHTML = "<li>No matches -- try a different spelling or add the country</li>";
      return;
    }
    for (const place of places) {
      const li = document.createElement("li");
      li.textContent = place.display_name;
      li.addEventListener("click", () => {
        document.getElementById("latitude").value = place.latitude;
        document.getElementById("longitude").value = place.longitude;
        const selected = document.getElementById("place_selected");
        selected.textContent = `Selected: ${place.display_name} (${place.latitude.toFixed(4)}, ${place.longitude.toFixed(4)})`;
        selected.hidden = false;
        resultsEl.innerHTML = "";
      });
      resultsEl.appendChild(li);
    }
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.hidden = false;
  }
});

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
