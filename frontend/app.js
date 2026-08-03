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

function renderCharts(positions, vargas) {
  const d1SignIndex = (name) => vargas[name].D1.sign_index;
  const d9SignIndex = (name) => vargas[name].D9.sign_index;

  document.getElementById("d1-chart").innerHTML = buildNorthIndianSvg(positions, d1SignIndex);
  document.getElementById("d9-chart").innerHTML = buildNorthIndianSvg(positions, d9SignIndex);
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

document.getElementById("chart-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("error");
  const resultsEl = document.getElementById("results");
  errorEl.hidden = true;
  resultsEl.hidden = true;

  const date = document.getElementById("birth_date").value;
  const time = document.getElementById("birth_time").value;
  const offset = document.getElementById("utc_offset").value.trim();
  const birth_datetime = `${date}T${time}${offset}`;

  const payload = {
    birth_datetime,
    latitude: parseFloat(document.getElementById("latitude").value),
    longitude: parseFloat(document.getElementById("longitude").value),
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
    renderCharts(data.positions, data.vargas);
    renderPositionsTable(data.positions);
    renderDashaTable(data.vimshottari_dasha);
    resultsEl.hidden = false;
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.hidden = false;
  }
});
