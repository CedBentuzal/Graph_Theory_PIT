/**
 * TSP Solver with Dynamic Programming (Held-Karp Algorithm)
 * Real-world Application: COWD Water Bill Delivery Optimization, Cagayan de Oro City
 */

// --- Official Real Data (Google Maps Driving Distances & GPS) ---
const DEFAULT_LOCATIONS = [
  { label: 'A', name: 'Cagayan de Oro City Water District', lat: 8.4834163, lon: 124.6496531, role: 'Origin / HQ' },
  { label: 'B', name: 'Carmen Barangay Hall', lat: 8.4810397, lon: 124.6358978, role: 'Delivery Stop' },
  { label: 'C', name: 'Kauswagan Barangay Hall', lat: 8.4966285, lon: 124.6399332, role: 'Delivery Stop' },
  { label: 'D', name: 'Bulua Barangay Hall', lat: 8.5041399, lon: 124.6160102, role: 'Delivery Stop' },
  { label: 'E', name: 'Macasandig Barangay Hall', lat: 8.4654958, lon: 124.6445623, role: 'Delivery Stop' },
  { label: 'F', name: 'Camaman-an Barangay Hall', lat: 8.4737200, lon: 124.6617633, role: 'Delivery Stop' },
  { label: 'G', name: 'Lapasan Barangay Hall', lat: 8.4833394, lon: 124.6646873, role: 'Delivery Stop' }
];

// Distance matrix (km) from Row to Column
const DEFAULT_MATRIX = [
  [0.0, 1.9, 2.6, 5.1, 3.2, 2.3, 1.9], // A
  [2.1, 0.0, 2.4, 4.1, 2.5, 3.3, 4.2], // B
  [2.6, 2.3, 0.0, 3.0, 4.2, 4.8, 3.9], // C
  [5.0, 4.2, 3.0, 0.0, 6.3, 7.3, 6.4], // D
  [2.3, 2.7, 4.3, 6.5, 0.0, 2.7, 4.1], // E
  [2.4, 3.2, 4.7, 7.2, 2.8, 0.0, 1.8], // F
  [2.0, 4.1, 3.9, 6.4, 4.2, 1.8, 0.0]  // G
];

// App State
let currentMatrix = JSON.parse(JSON.stringify(DEFAULT_MATRIX));
let currentLocations = JSON.parse(JSON.stringify(DEFAULT_LOCATIONS));
let currentResult = null;
let leafletMap = null;
let mapMarkers = [];
let mapPolyline = null;
let riderMarker = null;
let animationFrameId = null;
let isRiderAnimating = false;

// --- Helper Functions ---
function fmt(num) {
  return Number(num).toFixed(1);
}

// Generate bitmask helper
function getSubsetMask(indices) {
  let mask = 0;
  for (const idx of indices) mask |= (1 << idx);
  return mask;
}

// Generate combinations
function* combinations(arr, k) {
  if (k === 0) {
    yield [];
    return;
  }
  for (let i = 0; i <= arr.length - k; i++) {
    const head = arr[i];
    const tail = arr.slice(i + 1);
    for (const comb of combinations(tail, k - 1)) {
      yield [head, ...comb];
    }
  }
}

// --- Dynamic Programming (Held-Karp) Solver ---
function solveHeldKarp(matrix, locations) {
  const n = matrix.length;
  const labels = locations.map(l => l.label);
  const startTime = performance.now();

  // DP table: key `${mask}_${k}` -> { cost, parent }
  const C = new Map();
  const subproblemsList = [];

  // Step 1: Base cases (subsets of size 1)
  for (let k = 1; k < n; k++) {
    const mask = (1 << k);
    const cost = matrix[0][k];
    C.set(`${mask}_${k}`, { cost, parent: 0 });
    subproblemsList.push({
      subset: `{${labels[k]}}`,
      size: 1,
      end: labels[k],
      cost: cost,
      parent: labels[0]
    });
  }

  // Step 2: Subsets of size 2 to n-1
  const nonStart = Array.from({ length: n - 1 }, (_, i) => i + 1);

  for (let size = 2; size < n; size++) {
    for (const places of combinations(nonStart, size)) {
      const mask = getSubsetMask(places);
      const subsetLabel = `{${places.map(p => labels[p]).join(',')}}`;

      for (const k of places) {
        const prevMask = mask ^ (1 << k);
        let minCost = Infinity;
        let bestM = -1;

        for (const m of places) {
          if (m === k) continue;
          const prevEntry = C.get(`${prevMask}_${m}`);
          if (!prevEntry) continue;
          const candidateCost = prevEntry.cost + matrix[m][k];
          if (candidateCost < minCost) {
            minCost = candidateCost;
            bestM = m;
          }
        }

        if (bestM !== -1) {
          C.set(`${mask}_${k}`, { cost: minCost, parent: bestM });
          subproblemsList.push({
            subset: subsetLabel,
            size: size,
            end: labels[k],
            cost: minCost,
            parent: labels[bestM]
          });
        }
      }
    }
  }

  // Step 3: Tour closure back to origin A (0)
  const allMask = getSubsetMask(nonStart);
  let bestTourCost = Infinity;
  let lastStop = -1;

  for (let k = 1; k < n; k++) {
    const entry = C.get(`${allMask}_${k}`);
    if (entry) {
      const totalCost = entry.cost + matrix[k][0];
      if (totalCost < bestTourCost) {
        bestTourCost = totalCost;
        lastStop = k;
      }
    }
  }

  // Step 4: Backtrack to reconstruct tour
  const tour = [0];
  let curr = lastStop;
  let currMask = allMask;

  const reversedPath = [lastStop];
  while (curr !== 0 && currMask > 0) {
    const entry = C.get(`${currMask}_${curr}`);
    if (!entry || entry.parent === 0) break;
    reversedPath.push(entry.parent);
    currMask ^= (1 << curr);
    curr = entry.parent;
  }

  reversedPath.reverse();
  tour.push(...reversedPath);
  tour.push(0);

  const endTime = performance.now();

  return {
    bestCost: Math.round(bestTourCost * 100) / 100,
    tour: tour,
    tourLabels: tour.map(i => labels[i]),
    tableSize: C.size,
    subproblems: subproblemsList,
    timeMs: (endTime - startTime).toFixed(3)
  };
}

// --- Brute Force Solver for Verification ---
function solveBruteForce(matrix) {
  const n = matrix.length;
  const nonStart = Array.from({ length: n - 1 }, (_, i) => i + 1);
  const startTime = performance.now();

  function* permute(arr) {
    if (arr.length <= 1) {
      yield arr;
      return;
    }
    for (let i = 0; i < arr.length; i++) {
      const curr = arr[i];
      const remaining = [...arr.slice(0, i), ...arr.slice(i + 1)];
      for (const p of permute(remaining)) {
        yield [curr, ...p];
      }
    }
  }

  let minCost = Infinity;
  let count = 0;

  for (const p of permute(nonStart)) {
    count++;
    let cost = matrix[0][p[0]];
    for (let i = 0; i < p.length - 1; i++) {
      cost += matrix[p[i]][p[i + 1]];
    }
    cost += matrix[p[p.length - 1]][0];
    if (cost < minCost) {
      minCost = cost;
    }
  }

  const endTime = performance.now();
  return {
    routesChecked: count,
    minCost: Math.round(minCost * 100) / 100,
    timeMs: (endTime - startTime).toFixed(3)
  };
}

// --- UI Rendering ---

// Update Metric Cards
function updateMetrics(dpRes, bfRes) {
  document.getElementById('metricDistance').innerHTML = `${dpRes.bestCost.toFixed(1)} <span style="font-size: 1rem; color: var(--text-dim);">km</span>`;
  document.getElementById('metricPath').textContent = dpRes.tourLabels.join(' → ');
  document.getElementById('metricTableSize').innerHTML = `${dpRes.tableSize} <span style="font-size: 1rem; color: var(--text-dim);">subproblems</span>`;
  document.getElementById('metricBruteRoutes').innerHTML = `${bfRes.routesChecked} <span style="font-size: 1rem; color: var(--text-dim);">routes (${bfRes.minCost.toFixed(1)} km)</span>`;
}

// Render Tour Legs List
function renderTourLegs(tour, matrix, locations) {
  const container = document.getElementById('tourListContainer');
  container.innerHTML = '';

  let cumDist = 0;
  for (let i = 0; i < tour.length - 1; i++) {
    const fromIdx = tour[i];
    const toIdx = tour[i + 1];
    const fromLoc = locations[fromIdx];
    const toLoc = locations[toIdx];
    const legDist = matrix[fromIdx][toIdx];
    cumDist += legDist;

    const item = document.createElement('div');
    item.className = 'tour-step';
    item.id = `stepLeg_${i}`;
    item.innerHTML = `
      <div class="step-info">
        <div class="step-num">${i + 1}</div>
        <div>
          <div class="step-route">${fromLoc.label} <span>→</span> ${toLoc.label}</div>
          <div class="step-name">${fromLoc.name} → ${toLoc.name}</div>
        </div>
      </div>
      <div style="text-align: right;">
        <div class="step-dist">${legDist.toFixed(1)} km</div>
        <div style="font-size: 0.68rem; color: var(--text-dim); margin-top: 2px;">Σ ${cumDist.toFixed(1)} km</div>
      </div>
    `;

    // Click step to focus on map
    item.addEventListener('click', () => {
      highlightStep(i, fromLoc, toLoc);
    });

    container.appendChild(item);
  }
}

// Render DP Subproblem Table Samples
function renderDpTable(subproblems) {
  const tbody = document.getElementById('dpTableBody');
  tbody.innerHTML = '';

  // Show a representative slice (size 1 base cases + sample size 2 + tour finish)
  const samples = [
    ...subproblems.filter(s => s.size === 1),
    ...subproblems.filter(s => s.size === 2).slice(0, 4),
    ...subproblems.slice(-3)
  ];

  samples.forEach(s => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="color: var(--cyan-bright);">${s.subset}</td>
      <td><strong>${s.end}</strong></td>
      <td style="color: var(--emerald-bright); font-weight: bold;">${s.cost.toFixed(1)} km</td>
      <td style="color: var(--text-muted);">${s.parent}</td>
    `;
    tbody.appendChild(tr);
  });

  document.getElementById('dpProgressCount').textContent = `Sample of ${samples.length} from ${subproblems.length} states`;
}

// Render Distance Matrix Table with Editable Cells
function renderMatrixTable(matrix, locations, tour) {
  const table = document.getElementById('distanceMatrixTable');
  table.innerHTML = '';

  // Header row
  const thead = document.createElement('thead');
  const headRow = document.createElement('tr');
  headRow.innerHTML = '<th>From \\ To</th>' + locations.map(l => `<th title="${l.name}">${l.label}</th>`).join('');
  thead.appendChild(headRow);
  table.appendChild(thead);

  // Set of tour legs for visual highlighting
  const legSet = new Set();
  if (tour && tour.length > 1) {
    for (let i = 0; i < tour.length - 1; i++) {
      legSet.add(`${tour[i]}_${tour[i + 1]}`);
    }
  }

  const tbody = document.createElement('tbody');
  for (let r = 0; r < matrix.length; r++) {
    const row = document.createElement('tr');
    const labelCell = document.createElement('td');
    labelCell.innerHTML = `<strong style="color: var(--indigo-bright);" title="${locations[r].name}">${locations[r].label}</strong>`;
    row.appendChild(labelCell);

    for (let c = 0; c < matrix[r].length; c++) {
      const td = document.createElement('td');
      const isDiag = (r === c);
      const isTourLeg = legSet.has(`${r}_${c}`);

      const input = document.createElement('input');
      input.type = 'number';
      input.step = '0.1';
      input.min = '0';
      input.value = matrix[r][c];
      input.className = `matrix-input ${isDiag ? 'diag' : ''} ${isTourLeg ? 'highlight-leg' : ''}`;
      input.dataset.row = r;
      input.dataset.col = c;
      if (isDiag) input.disabled = true;

      input.addEventListener('change', (e) => {
        const val = parseFloat(e.target.value);
        if (!isNaN(val) && val >= 0) {
          currentMatrix[r][c] = val;
        }
      });

      td.appendChild(input);
      row.appendChild(td);
    }
    tbody.appendChild(row);
  }
  table.appendChild(tbody);
}

// --- Leaflet Map Setup & Tour Rendering ---
function initLeafletMap() {
  if (leafletMap) return;

  // Center around Cagayan de Oro City
  leafletMap = L.map('mapView', {
    zoomControl: true,
    attributionControl: false
  }).setView([8.4834, 124.6497], 13.5);

  // Standard OpenStreetMap Tiles (100% Free, No API Key Required)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap'
  }).addTo(leafletMap);
}


function updateMapDisplay(tour, locations) {
  initLeafletMap();

  // Clear previous markers & lines
  mapMarkers.forEach(m => leafletMap.removeLayer(m));
  mapMarkers = [];
  if (mapPolyline) leafletMap.removeLayer(mapPolyline);
  if (riderMarker) leafletMap.removeLayer(riderMarker);

  // Add Location Markers
  locations.forEach((loc, idx) => {
    const isOrigin = (idx === 0);
    const markerHtml = `<div class="custom-marker ${isOrigin ? 'marker-start' : 'marker-optimal'}">${loc.label}</div>`;
    const icon = L.divIcon({
      html: markerHtml,
      className: 'div-marker-wrapper',
      iconSize: [32, 32],
      iconAnchor: [16, 16]
    });

    const marker = L.marker([loc.lat, loc.lon], { icon })
      .bindPopup(`<strong>${loc.label}: ${loc.name}</strong><br><span style="color:#06b6d4;">${loc.role}</span>`)
      .addTo(leafletMap);

    mapMarkers.push(marker);
  });

  // Build Polyline coordinates along the tour
  const latlngs = tour.map(idx => [locations[idx].lat, locations[idx].lon]);

  // Glowing Tour Polyline
  mapPolyline = L.polyline(latlngs, {
    color: '#10b981',
    weight: 4.5,
    opacity: 0.9,
    dashArray: '8, 8',
    lineCap: 'round',
    lineJoin: 'round'
  }).addTo(leafletMap);

  leafletMap.fitBounds(mapPolyline.getBounds(), { padding: [40, 40] });
}

// Highlight a tour step
function highlightStep(stepIdx, fromLoc, toLoc) {
  document.querySelectorAll('.tour-step').forEach(el => el.classList.remove('active-step'));
  const activeEl = document.getElementById(`stepLeg_${stepIdx}`);
  if (activeEl) activeEl.classList.add('active-step');

  if (leafletMap) {
    const bounds = L.latLngBounds([
      [fromLoc.lat, fromLoc.lon],
      [toLoc.lat, toLoc.lon]
    ]);
    leafletMap.fitBounds(bounds, { padding: [60, 60] });
  }
}

// --- Delivery Rider Simulation Animation ---
function startRiderSimulation() {
  if (!currentResult || !leafletMap) return;
  const tour = currentResult.tour;
  const locs = currentLocations;

  if (isRiderAnimating) {
    cancelAnimationFrame(animationFrameId);
    isRiderAnimating = false;
    document.getElementById('btnSimPlay').innerHTML = `
      <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="m11.596 8.697-6.363 3.692c-.54.313-1.233-.066-1.233-.697V4.308c0-.63.692-1.01 1.233-.696l6.363 3.692a.802.802 0 0 1 0 1.393z"/></svg>
      Resume Simulation
    `;
    return;
  }

  isRiderAnimating = true;
  document.getElementById('btnSimPlay').innerHTML = `
    <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M5.5 3.5A1.5 1.5 0 0 1 7 5v6a1.5 1.5 0 0 1-3 0V5a1.5 1.5 0 0 1 1.5-1.5zm5 0A1.5 1.5 0 0 1 12 5v6a1.5 1.5 0 0 1-3 0V5a1.5 1.5 0 0 1 1.5-1.5z"/></svg>
    Pause Rider
  `;

  if (!riderMarker) {
    const riderHtml = `<div style="font-size: 26px; transform: translate(-13px, -13px); filter: drop-shadow(0 0 8px #22d3ee);">🛵</div>`;
    const riderIcon = L.divIcon({ html: riderHtml, className: 'rider-icon', iconSize: [26, 26] });
    riderMarker = L.marker([locs[tour[0]].lat, locs[tour[0]].lon], { icon: riderIcon }).addTo(leafletMap);
  }

  let currentLeg = 0;
  let progress = 0;
  const speed = 0.015; // Animation speed

  function animate() {
    if (!isRiderAnimating) return;

    const fromNode = locs[tour[currentLeg]];
    const toNode = locs[tour[currentLeg + 1]];

    progress += speed;
    if (progress >= 1) {
      progress = 0;
      currentLeg++;
      if (currentLeg >= tour.length - 1) {
        // Finished full tour
        isRiderAnimating = false;
        document.getElementById('riderStatus').textContent = `Tour Complete! Back at ${locs[0].name} (18.8 km)`;
        document.getElementById('btnSimPlay').textContent = '▶ Replay Simulation';
        showToast('Rider successfully completed water bill delivery tour!');
        return;
      }
    }

    const curLat = fromNode.lat + (toNode.lat - fromNode.lat) * progress;
    const curLon = fromNode.lon + (toNode.lon - fromNode.lon) * progress;
    riderMarker.setLatLng([curLat, curLon]);

    document.getElementById('riderStatus').textContent = `Delivering: ${fromNode.label} → ${toNode.label} (${toNode.name})`;
    highlightStep(currentLeg, fromNode, toNode);

    animationFrameId = requestAnimationFrame(animate);
  }

  animate();
}

function resetRiderSimulation() {
  if (isRiderAnimating) {
    cancelAnimationFrame(animationFrameId);
    isRiderAnimating = false;
  }
  document.getElementById('btnSimPlay').innerHTML = `
    <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="m11.596 8.697-6.363 3.692c-.54.313-1.233-.066-1.233-.697V4.308c0-.63.692-1.01 1.233-.696l6.363 3.692a.802.802 0 0 1 0 1.393z"/></svg>
    Simulate Delivery Rider
  `;
  if (riderMarker && leafletMap) {
    leafletMap.removeLayer(riderMarker);
    riderMarker = null;
  }
  document.getElementById('riderStatus').textContent = 'Rider: At Origin (COWD Office A)';
  document.querySelectorAll('.tour-step').forEach(el => el.classList.remove('active-step'));
}

// --- Graph Topology Canvas Visualizer ---
function drawGraphCanvas(tour, locations, matrix) {
  const canvas = document.getElementById('graphCanvas');
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  const n = matrix.length;

  canvas.width = width * dpr;
  canvas.height = height * dpr;

  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  // Geographic scaling matching presentation/graph_diagram.png:
  // Bulua (D) top-left, Carmen (B) middle-west, Macasandig (E) south, etc.
  const lats = locations.map(l => l.lat);
  const lons = locations.map(l => l.lon);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLon = Math.min(...lons);
  const maxLon = Math.max(...lons);
  const latRange = (maxLat - minLat) || 1;
  const lonRange = (maxLon - minLon) || 1;

  const padX = width * 0.14;
  const padY = height * 0.16;
  const usableWidth = width - (2 * padX);
  const usableHeight = height - (2 * padY);

  const shortNames = {
    'A': 'COWD HQ',
    'B': 'Carmen',
    'C': 'Kauswagan',
    'D': 'Bulua',
    'E': 'Macasandig',
    'F': 'Camaman-an',
    'G': 'Lapasan'
  };

  const nodeCoords = locations.map((loc, i) => {
    // lon maps to X (west to east), lat inverted maps to Y (north to south)
    const normX = (loc.lon - minLon) / lonRange;
    const normY = 1.0 - ((loc.lat - minLat) / latRange);
    return {
      x: padX + normX * usableWidth,
      y: padY + normY * usableHeight,
      label: loc.label,
      name: loc.name,
      shortName: shortNames[loc.label] || loc.label,
      isOrigin: (i === 0)
    };
  });

  // Draw subtle background edges for all connections
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
  ctx.lineWidth = 1;
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      if (i !== j) {
        ctx.beginPath();
        ctx.moveTo(nodeCoords[i].x, nodeCoords[i].y);
        ctx.lineTo(nodeCoords[j].x, nodeCoords[j].y);
        ctx.stroke();
      }
    }
  }

  // Draw glowing optimal tour directed arrows
  for (let i = 0; i < tour.length - 1; i++) {
    const u = nodeCoords[tour[i]];
    const v = nodeCoords[tour[i + 1]];
    const dist = matrix[tour[i]][tour[i + 1]];

    // Glowing green edge
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 3.5;
    ctx.shadowColor = '#10b981';
    ctx.shadowBlur = 12;

    ctx.beginPath();
    ctx.moveTo(u.x, u.y);
    ctx.lineTo(v.x, v.y);
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Draw arrow head
    const headLen = 12;
    const angle = Math.atan2(v.y - u.y, v.x - u.x);
    const midX = (u.x + v.x) / 2;
    const midY = (u.y + v.y) / 2;

    ctx.fillStyle = '#34d399';
    ctx.beginPath();
    ctx.moveTo(midX, midY);
    ctx.lineTo(midX - headLen * Math.cos(angle - Math.PI / 6), midY - headLen * Math.sin(angle - Math.PI / 6));
    ctx.lineTo(midX - headLen * Math.cos(angle + Math.PI / 6), midY - headLen * Math.sin(angle + Math.PI / 6));
    ctx.closePath();
    ctx.fill();

    // Distance Badge
    ctx.fillStyle = 'rgba(10, 14, 23, 0.85)';
    ctx.fillRect(midX - 16, midY - 10, 32, 20);
    ctx.fillStyle = '#22d3ee';
    ctx.font = 'bold 11px Outfit, monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(`${dist.toFixed(1)}k`, midX, midY);
  }

  // Draw Vertices
  nodeCoords.forEach((node) => {
    ctx.shadowBlur = node.isOrigin ? 18 : 12;
    ctx.shadowColor = node.isOrigin ? '#ec4899' : '#06b6d4';
    ctx.fillStyle = node.isOrigin ? '#ec4899' : '#0ea5e9';
    ctx.beginPath();
    ctx.arc(node.x, node.y, node.isOrigin ? 22 : 18, 0, Math.PI * 2);
    ctx.fill();

    ctx.lineWidth = 2.5;
    ctx.strokeStyle = '#ffffff';
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Node label
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 13px Outfit, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(node.label, node.x, node.y);

    // Place name caption below node
    ctx.font = '600 11px Outfit, sans-serif';
    ctx.fillStyle = '#94a3b8';
    ctx.fillText(node.shortName, node.x, node.y + (node.isOrigin ? 32 : 28));
  });
}


function showToast(msg) {
  const toast = document.getElementById('toastMessage');
  document.getElementById('toastText').textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3500);
}

// --- Main Execution Flow ---
function executeSolver() {
  const dpResult = solveHeldKarp(currentMatrix, currentLocations);
  const bfResult = solveBruteForce(currentMatrix);
  currentResult = dpResult;

  updateMetrics(dpResult, bfResult);
  renderTourLegs(dpResult.tour, currentMatrix, currentLocations);
  renderDpTable(dpResult.subproblems);
  renderMatrixTable(currentMatrix, currentLocations, dpResult.tour);
  updateMapDisplay(dpResult.tour, currentLocations);
  drawGraphCanvas(dpResult.tour, currentLocations, currentMatrix);

  showToast(`Held-Karp solved optimal tour: ${dpResult.bestCost.toFixed(1)} km!`);
}

// --- Event Listeners Initialization ---
document.addEventListener('DOMContentLoaded', () => {
  // Initial run
  executeSolver();

  // Run Solver Button
  document.getElementById('btnRunSolver').addEventListener('click', () => {
    executeSolver();
  });

  // Reset Data Button
  document.getElementById('btnResetMatrix').addEventListener('click', () => {
    currentMatrix = JSON.parse(JSON.stringify(DEFAULT_MATRIX));
    executeSolver();
    showToast('Reset distance matrix to official Google Maps CDO data.');
  });

  // Recalculate with edited matrix
  document.getElementById('btnRecalculateMatrix').addEventListener('click', () => {
    executeSolver();
  });

  // View Toggle: Map vs Graph
  const btnMap = document.getElementById('btnViewMap');
  const btnGraph = document.getElementById('btnViewGraph');
  const mapView = document.getElementById('mapView');
  const graphCanvas = document.getElementById('graphCanvas');

  btnMap.addEventListener('click', () => {
    btnMap.classList.add('active');
    btnGraph.classList.remove('active');
    mapView.style.display = 'block';
    graphCanvas.style.display = 'none';
    if (leafletMap) leafletMap.invalidateSize();
  });

  btnGraph.addEventListener('click', () => {
    btnGraph.classList.add('active');
    btnMap.classList.remove('active');
    mapView.style.display = 'none';
    graphCanvas.style.display = 'block';
    if (currentResult) {
      drawGraphCanvas(currentResult.tour, currentLocations, currentMatrix);
    }
  });

  // Rider Simulation Controls
  document.getElementById('btnSimPlay').addEventListener('click', startRiderSimulation);
  document.getElementById('btnSimReset').addEventListener('click', resetRiderSimulation);

  // Download PNG directly to user's local device
  const btnDownloadPng = document.getElementById('btnDownloadPng');
  if (btnDownloadPng) {
    btnDownloadPng.addEventListener('click', () => {
      const isGraphActive = (graphCanvas.style.display !== 'none');
      if (isGraphActive) {
        const dataUrl = graphCanvas.toDataURL('image/png');
        const link = document.createElement('a');
        link.download = 'graph_diagram.png';
        link.href = dataUrl;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        showToast('Saved graph_diagram.png directly to your device Downloads!');
      } else {
        const link = document.createElement('a');
        link.download = 'cdo_map.png';
        link.href = 'presentation/cdo_map.png';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        showToast('Saved cdo_map.png directly to your device Downloads!');
      }
    });
  }

  // Window resize re-renders canvas
  window.addEventListener('resize', () => {
    if (graphCanvas.style.display !== 'none' && currentResult) {
      drawGraphCanvas(currentResult.tour, currentLocations, currentMatrix);
    }
    if (leafletMap) {
      leafletMap.invalidateSize();
    }
  });
});
