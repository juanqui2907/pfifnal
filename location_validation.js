/* =============================================
   TERRASHIELD — location_validation.js
   Interacción con el mapa SVG y validación
   de ubicación vía APIs externas.
   Ng: valores de referencia predefinidos por
   departamento (GFD, flashes/km²/año).
   ============================================= */

// Grilla Ng — COMB_TRM_ISS AnnualMean (0.1°), cargada desde ng_caribe.json
let NG_CARIBE_INDEX = null; // Map: "lat_lon" → ng

fetch('ng_caribe.json')
  .then(r => r.json())
  .then(json => {
    NG_CARIBE_INDEX = {};
    for (const p of json.data) {
      const key = p.lat.toFixed(2) + '_' + p.lon.toFixed(2);
      NG_CARIBE_INDEX[key] = p.ng;
    }
    console.log(`✓ ng_caribe.json cargado — ${json.data.length} puntos (COMB_TRM_ISS AnnualMean)`);
  })
  .catch(() => console.warn('ng_caribe.json no encontrado'));

// Busca el Ng más cercano en la grilla ng_caribe.json para un punto lat/lon
function getNgFromGrid(lat, lon) {
  if (!NG_CARIBE_INDEX) return null;

  // Redondear al múltiplo de 0.1 más cercano (resolución de la grilla)
  const roundTo1 = v => Math.round(v * 10) / 10;
  const snapLat  = roundTo1(lat);
  const snapLon  = roundTo1(lon);

  const key = snapLat.toFixed(2) + '_' + snapLon.toFixed(2);
  if (NG_CARIBE_INDEX[key] !== undefined) return NG_CARIBE_INDEX[key];

  // Fallback: buscar el punto más cercano (por si cae en borde de grilla)
  let minDist = Infinity, best = null;
  for (const k of Object.keys(NG_CARIBE_INDEX)) {
    const [kLat, kLon] = k.split('_').map(Number);
    const d = (kLat - lat) ** 2 + (kLon - lon) ** 2;
    if (d < minDist) { minDist = d; best = NG_CARIBE_INDEX[k]; }
  }
  return best;
}

// Datos de suelos IEEE 80 — consultados al servidor vía API (sin descarga masiva)
// El servidor carga suelos_data_v2.json una sola vez en memoria al arrancar.
async function getSueloFromAPI(lat, lon) {
  try {
    const res = await fetch(`/suelo?lat=${lat}&lon=${lon}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    console.warn('API /suelo no disponible — se usará valor por defecto');
    return null;
  }
}

// Datos de referencia por departamento (coordenadas, municipio, temperatura)
const deptData = {
  'La Guajira': { lat: 11.5444, lon: -72.9072, municipio: 'Riohacha',     ng: 12.4, temp: 29.2 },
  'Magdalena':  { lat: 11.2408, lon: -74.2011, municipio: 'Santa Marta',  ng: 14.8, temp: 28.5 },
  'Atlántico':  { lat: 10.9639, lon: -74.7964, municipio: 'Barranquilla', ng: 15.2, temp: 27.9 },
  'Bolívar':    { lat: 10.3910, lon: -75.4794, municipio: 'Cartagena',    ng: 13.6, temp: 28.2 },
  'Sucre':      { lat: 9.3047,  lon: -75.3978, municipio: 'Sincelejo',    ng: 16.1, temp: 29.0 },
  'Córdoba':    { lat: 8.7479,  lon: -75.8814, municipio: 'Montería',     ng: 17.3, temp: 28.8 },
  'Cesar':      { lat: 10.4631, lon: -73.2532, municipio: 'Valledupar',   ng: 11.9, temp: 30.1 }
};

const CARIBE_BOUNDS = { latMin: 8.0, latMax: 12.5, lonMin: -76.5, lonMax: -71.0 };

function isInCaribe(lat, lon) {
  return lat >= CARIBE_BOUNDS.latMin && lat <= CARIBE_BOUNDS.latMax &&
         lon >= CARIBE_BOUNDS.lonMin  && lon <= CARIBE_BOUNDS.lonMax;
}


/* =============================================
   LEAFLET MAP — post-validación
   ============================================= */
let _leafletMap = null;
let _leafletMarker = null;

function showLeafletMap(lat, lon, municipio, dept) {
  const svgWrap  = document.getElementById('map-area');
  const mapWrap  = document.getElementById('leaflet-map-wrap');
  if (!svgWrap || !mapWrap) return;

  svgWrap.style.display  = 'none';
  mapWrap.style.display  = 'block';

  if (!_leafletMap) {
    _leafletMap = L.map('leaflet-map', { zoomControl: true, scrollWheelZoom: false });
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 18
    }).addTo(_leafletMap);
  }

  _leafletMap.setView([lat, lon], 13);

  if (_leafletMarker) _leafletMarker.remove();

  const icon = L.divIcon({
    className: '',
    html: `<div style="
      width:14px;height:14px;background:#F5C400;border:2.5px solid #0A3D91;
      border-radius:50%;box-shadow:0 2px 6px rgba(0,0,0,0.3);
    "></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7]
  });

  _leafletMarker = L.marker([lat, lon], { icon })
    .addTo(_leafletMap)
    .bindPopup(`<strong>${municipio || dept}</strong><br>${dept}<br><span style="font-size:0.75rem;color:#666;">${lat.toFixed(4)}°N, ${lon.toFixed(4)}°W</span>`)
    .openPopup();

  setTimeout(() => _leafletMap.invalidateSize(), 100);
}

function resetToSvgMap() {
  const svgWrap = document.getElementById('map-area');
  const mapWrap = document.getElementById('leaflet-map-wrap');
  const resultBox = document.getElementById('location-result');
  if (svgWrap) svgWrap.style.display = 'block';
  if (mapWrap) mapWrap.style.display = 'none';
  if (resultBox) { resultBox.classList.remove('show'); resultBox.classList.remove('error-state'); }
  AppState.locationValidated = false;
  AppState.validatedData = null;
  // Reset coord inputs
  document.getElementById('new-lat').value = '';
  document.getElementById('new-lon').value = '';
  // Reset dept selection
  document.querySelectorAll('.dept-path').forEach(p => { p.classList.remove('selected-dept'); p.style.fill = ''; });
  document.getElementById('map-selected-pin').setAttribute('display', 'none');
}

/* =============================================
   MAP INTERACTION
   ============================================= */
document.querySelectorAll('.dept-path').forEach(path => {
  path.addEventListener('mouseenter', function() {
    this.style.fill = '#2F6FCC'; this.style.opacity = '0.85';
  });
  path.addEventListener('mouseleave', function() {
    if (!this.classList.contains('selected-dept')) { this.style.fill = ''; this.style.opacity = ''; }
  });
  path.addEventListener('click', function() {
    document.querySelectorAll('.dept-path').forEach(p => { p.classList.remove('selected-dept'); p.style.fill = ''; });
    this.classList.add('selected-dept');
    this.style.fill = '#0A3D91';
    const data = deptData[this.getAttribute('data-dept')];
    if (data) {
      document.getElementById('new-lat').value = data.lat.toFixed(4);
      document.getElementById('new-lon').value = data.lon.toFixed(4);
      showMapPin(this);
    }
  });
});

function showMapPin(elem) {
  const pin = document.getElementById('map-selected-pin');
  const bbox = elem.getBBox ? elem.getBBox() : null;
  if (pin && bbox) {
    const cx = bbox.x + bbox.width / 2;
    const cy = bbox.y + bbox.height / 2;
    document.getElementById('map-pin-circle').setAttribute('cx', cx);
    document.getElementById('map-pin-circle').setAttribute('cy', cy);
    document.getElementById('map-pin-line').setAttribute('x1', cx);
    document.getElementById('map-pin-line').setAttribute('y1', cy);
    document.getElementById('map-pin-line').setAttribute('x2', cx);
    document.getElementById('map-pin-line').setAttribute('y2', cy - 12);
    pin.setAttribute('display', '');
  }
}

/* =============================================
   LOCATION VALIDATION
   ============================================= */
async function validarUbicacion() {
  const lat         = parseFloat(document.getElementById('new-lat').value);
  const lon         = parseFloat(document.getElementById('new-lon').value);
  const resultBox   = document.getElementById('location-result');
  const resultTitle = document.getElementById('loc-result-title');
  const resultBody  = document.getElementById('loc-result-body');

  resultBox.classList.remove('error-state');
  resultBox.classList.add('show');

  if (isNaN(lat) || isNaN(lon)) {
    resultBox.classList.add('error-state');
    resultTitle.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg> Error de validación`;
    resultBody.innerHTML  = `<div class="msg-error" style="grid-column:1/-1;">Ingrese coordenadas válidas antes de validar.</div>`;
    AppState.locationValidated = false;
    return;
  }

  const inCaribe = isInCaribe(lat, lon);
  if (!inCaribe) {
    resultBox.classList.add('error-state');
    resultTitle.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg> Ubicación fuera del área permitida`;
    resultBody.innerHTML  = `<div class="msg-error" style="grid-column:1/-1;">Las coordenadas (${lat.toFixed(4)}°N, ${lon.toFixed(4)}°W) no pertenecen a la región Caribe colombiana.</div>`;
    AppState.locationValidated = false;
    return;
  }

  resultTitle.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg> Validando ubicación...`;
  resultBody.innerHTML  = `<div style="grid-column:1/-1;text-align:center;padding:10px;color:var(--text-mid);">Obteniendo datos...</div>`;

  try {
    // 1. Nominatim
    const nominatimRes = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=10&addressdetails=1&accept-language=es`,
      { headers: { 'Accept': 'application/json' } }
    );
    if (!nominatimRes.ok) throw new Error('Error Nominatim');
    const geoData = await nominatimRes.json();
    const address = geoData.address || {};
    let dept      = (address.state || address.province || 'Región Caribe').trim();
    let municipio = (address.city  || address.town    || address.county  || 'N/D (área rural)').trim();



    // 2. Open-Meteo
    let temp = 28, humedad = 75, altitud = 20;
    try {
      const mRes = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m&timezone=auto`);
      if (mRes.ok) { const m = await mRes.json(); if (m.current) { temp = m.current.temperature_2m || 28; humedad = m.current.relative_humidity_2m || 75; } }
    } catch { console.warn('Open-Meteo no disponible'); }

    // 3. Open-Elevation
    try {
      const eRes = await fetch(`https://api.open-elevation.com/api/v1/lookup?locations=${lat},${lon}`);
      if (eRes.ok) { const e = await eRes.json(); if (e.results?.length > 0) altitud = Math.round(e.results[0].elevation); }
    } catch { console.warn('Open-Elevation no disponible'); }

    // 4. Ng — grilla COMB_TRM_ISS AnnualMean (ng_caribe.json, resolución 0.1°)
    let ng        = getNgFromGrid(lat, lon);
    let ngFuente  = '';
    let ngDisplay = ng !== null ? ng.toFixed(4) : 'No disponible';

    // 5. Tipo de suelo IEEE 80 — consultado al servidor (no descarga local)
    let tipoSuelo   = 'Suelo Húmedo'; // fallback por defecto (Moist Soil)
    let rhoSuelo    = 100;
    let sueloFuente = 'Valor por defecto (Moist Soil)';
    let sueloNota   = null; // mensaje explicativo cuando no es clasificable
    const sueloData = await getSueloFromAPI(lat, lon);
    if (sueloData) {
      if (sueloData.subtipo_nc) {
        // Zona urbana, cuerpo de agua, etc.
        tipoSuelo   = 'No clasificable';
        rhoSuelo    = null;
        sueloFuente = null;
        sueloNota   = 'Este punto se encuentra en un área no clasificable para estimación preliminar de suelo.';
      } else if (!sueloData.tipo_suelo) {
        // Ambigüedad o sin convergencia
        tipoSuelo   = 'No clasificable';
        rhoSuelo    = null;
        sueloFuente = null;
        sueloNota   = 'La información encontrada para este punto es ambigua y no permite una clasificación preliminar confiable.';
      } else {
        tipoSuelo   = sueloData.tipo_suelo;
        rhoSuelo    = sueloData.rho;
        sueloFuente = null;
      }
    } else {
      // Sin polígono coincidente
      tipoSuelo   = 'No clasificable';
      rhoSuelo    = null;
      sueloFuente = null;
      sueloNota   = 'No hay datos suficientes para clasificar el tipo de suelo en este punto.';
    }

    AppState.locationValidated = true;
    AppState.validatedData = { lat, lon, departamento: dept, municipio, ng, ngDisplay, temp, tipoSuelo, rhoSuelo, altitud, humedad, ngFuente, sueloFuente, sueloNota };

    resultTitle.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 11 12 14 22 4"/></svg> Ubicación validada — Región Caribe`;
    showLeafletMap(lat, lon, municipio, dept);
    showLeafletMap(lat, lon, municipio, dept);
    resultBody.innerHTML  = `
      <div class="result-item"><div class="ri-label">Departamento</div><div class="ri-val">${dept}</div></div>
      <div class="result-item"><div class="ri-label">Municipio ref.</div><div class="ri-val">${municipio}</div></div>
      <div class="result-item"><div class="ri-label">Tipo de suelo (IEEE 80)</div><div class="ri-val">${tipoSuelo}${sueloNota ? `<span style="font-size:0.6rem;color:var(--text-light);display:block;margin-top:2px;">${sueloNota}</span>` : rhoSuelo !== null ? `<span style="font-size:0.6rem;color:var(--text-light);display:block;">ρ ≈ ${rhoSuelo.toLocaleString()} Ω·m${sueloFuente ? ' · ' + sueloFuente : ''}</span>` : ''}</div></div>
      <div class="result-item"><div class="ri-label">Altitud est.</div><div class="ri-val">~${altitud} msnm</div></div>
      <div class="result-item"><div class="ri-label">Temperatura est.</div><div class="ri-val">${temp.toFixed(1)} °C</div></div>
      <div class="result-item">
        <div class="ri-label">Ng — GFD (flashes/km²/año)</div>
        <div class="ri-val">${ngDisplay}</div>
      </div>
      <div class="result-item"><div class="ri-label">Latitud</div><div class="ri-val">${lat.toFixed(4)}°N</div></div>
      <div class="result-item"><div class="ri-label">Longitud</div><div class="ri-val">${lon.toFixed(4)}°W</div></div>
      <div class="result-item"><div class="ri-label">Humedad rel. est.</div><div class="ri-val">${humedad}%</div></div>
    `;

  } catch (error) {
    console.error('Error validando ubicación:', error);
    resultBox.classList.add('error-state');
    resultTitle.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg> Error al validar`;
    resultBody.innerHTML  = `<div class="msg-error" style="grid-column:1/-1;">Error al consultar datos. Verifique su conexión e intente de nuevo.</div>`;
    AppState.locationValidated = false;
  }
}