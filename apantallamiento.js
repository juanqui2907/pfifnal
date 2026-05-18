/* =============================================
   TERRASHIELD — Módulo de Apantallamiento
   Gestión de mástiles, equipos, cables de
   guarda y renderizado del modelo 3D.
   ============================================= */

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

const ApantState = {
  masts:      [],   // [{x, y, h}]
  cubes:      [],   // [{name, x, y, z, dx, dy, dz, color}]
  guardWires: [],   // [[i, j]]
};

let _apantAuxIndices         = [];    // índices de trazas auxiliares (se calculan al renderizar)
let _apantCleanMode          = false; // estado del toggle de vista limpia
let _apantVerifData          = null;  // último resultado de verificación por equipo
let _apantVerifOpen          = false; // panel de verificación visible
let _apantModelTraces        = [];    // trazas del modelo (para actualizar chart sin recalcular)
let _apantModelLayout        = null;
let _apantLastRecommendations = null; // últimas recomendaciones generadas
let _apantSurfaceTraceIdx    = -1;   // índice de la traza de superficie principal (para colorbar)
let _apantLastResult         = null; // resultado consolidado del último cálculo (usado por exportarPDF)

// Patrón de trazas auxiliares que el modelo genera como geometría de construcción
const _APANT_AUX_PATTERNS = [
  /^Base\s/i, /^Segmento\s/i, /^Cresta/i, /^Borde\s/i, /^Bordes\s/i,
  /^Puntos\sQ/i, /^Q\s/i, /^Q$/i, /^Q\sactivos/i,
  /^Puntos\sinteriores/i, /eliminado/i,
  /^Proyecci/i, /^Esfera\sde\sapoyo/i,
  /^Plano\s/i, /^Suelo$/i, /^Contactos\s/i,
  /^C1[23]\s*\|/i, /^C23\s*\|/i,
];

/* ─── Tabs ──────────────────────────────────────────────────────────────────── */

function apantSwitchTab(tab) {
  ['mastiles', 'equipos', 'guardas'].forEach(t => {
    const pane = document.getElementById('apant-tab-' + t);
    if (pane) pane.style.display = t === tab ? '' : 'none';
  });
  document.querySelectorAll('#apant-tab-bar .toggle-btn').forEach((btn, i) => {
    const tabs = ['mastiles', 'equipos', 'guardas'];
    btn.classList.toggle('active', tabs[i] === tab);
  });
}

/* ─── Mástiles ──────────────────────────────────────────────────────────────── */

function apantRenderMasts() {
  const list = document.getElementById('apant-mastiles-list');
  if (!list) return;

  if (ApantState.masts.length === 0) {
    list.innerHTML = '<div class="apant-list-empty">Sin mástiles — agregue al menos uno para calcular</div>';
  } else {
    list.innerHTML = ApantState.masts.map((m, i) => `
      <div class="apant-list-item">
        <span class="apant-list-num">M${i}</span>
        <span class="apant-list-text">x&nbsp;=&nbsp;${m.x}&thinsp;m &nbsp;·&nbsp; y&nbsp;=&nbsp;${m.y}&thinsp;m &nbsp;·&nbsp; h&nbsp;=&nbsp;${m.h}&thinsp;m</span>
        <button class="btn btn-danger" style="height:26px;padding:0 10px;font-size:0.75rem;line-height:1;" onclick="apantRemoveMast(${i})">×</button>
      </div>`).join('');
  }
  apantUpdateGuardSelects();
}

function apantAddMast() {
  const x = parseFloat(document.getElementById('apant-new-mx').value) || 0;
  const y = parseFloat(document.getElementById('apant-new-my').value) || 0;
  const h = parseFloat(document.getElementById('apant-new-mh').value);
  if (!h || h <= 0) {
    showToast('La altura del mástil debe ser mayor a 0', 'error');
    return;
  }
  const duplicate = ApantState.masts.find(m => m.x === x && m.y === y);
  if (duplicate) {
    showToast(`Ya existe un mástil en (${x}, ${y}). Cambie la posición.`, 'error');
    return;
  }
  ApantState.masts.push({ x, y, h });
  apantRenderMasts();
  apantRenderGuardWires();
}

function apantRemoveMast(idx) {
  // Eliminar cables que referencien este mástil y reasignar índices
  ApantState.guardWires = ApantState.guardWires
    .filter(([a, b]) => a !== idx && b !== idx)
    .map(([a, b]) => [a > idx ? a - 1 : a, b > idx ? b - 1 : b]);
  ApantState.masts.splice(idx, 1);
  apantRenderMasts();
  apantRenderGuardWires();
}

/* ─── Equipos (cubos) ───────────────────────────────────────────────────────── */

function apantRenderCubes() {
  const list = document.getElementById('apant-equipos-list');
  if (!list) return;

  if (ApantState.cubes.length === 0) {
    list.innerHTML = '<div class="apant-list-empty">Sin equipos definidos — opcional, para verificar apantallamiento</div>';
  } else {
    list.innerHTML = ApantState.cubes.map((c, i) => `
      <div class="apant-list-item">
        <span class="apant-list-num">E${i}</span>
        <span style="width:14px;height:14px;border-radius:3px;flex-shrink:0;background:${c.hexColor || '#F5C400'};border:1px solid rgba(0,0,0,0.15);display:inline-block;"></span>
        <span class="apant-list-text">
          <strong>${c.name}</strong>&nbsp;&nbsp;
          pos&nbsp;(${c.x},&thinsp;${c.y},&thinsp;${c.z})&thinsp;m&nbsp;&nbsp;
          dim&nbsp;${c.dx}&thinsp;×&thinsp;${c.dy}&thinsp;×&thinsp;${c.dz}&thinsp;m
        </span>
        <button class="btn btn-danger" style="height:26px;padding:0 10px;font-size:0.75rem;line-height:1;" onclick="apantRemoveCube(${i})">×</button>
      </div>`).join('');
  }
}

function apantAddCube() {
  const name = document.getElementById('apant-new-cname').value.trim()
             || `Equipo ${ApantState.cubes.length + 1}`;
  const x  = parseFloat(document.getElementById('apant-new-cx').value)  || 0;
  const y  = parseFloat(document.getElementById('apant-new-cy').value)  || 0;
  const z  = parseFloat(document.getElementById('apant-new-cz').value)  || 0;
  const dx = parseFloat(document.getElementById('apant-new-cdx').value);
  const dy = parseFloat(document.getElementById('apant-new-cdy').value);
  const dz = parseFloat(document.getElementById('apant-new-cdz').value);

  if (!dx || !dy || !dz || dx <= 0 || dy <= 0 || dz <= 0) {
    showToast('Las dimensiones dx, dy y dz deben ser mayores a 0', 'error');
    return;
  }

  // Validación: el nuevo equipo no puede solaparse en planta con ningún equipo existente
  const overlap = ApantState.cubes.find(c => {
    const noOverlapX = (x + dx <= c.x) || (x >= c.x + c.dx);
    const noOverlapY = (y + dy <= c.y) || (y >= c.y + c.dy);
    return !(noOverlapX || noOverlapY);
  });
  if (overlap) {
    showToast(`El equipo se solapa en planta con "${overlap.name}". Ajuste la posición o dimensiones.`, 'error');
    return;
  }

  const hexColor = document.getElementById('apant-new-ccolor')?.value || '#F5C400';
  const color    = hexToRgba(hexColor, 0.95);
  ApantState.cubes.push({ name, x, y, z, dx, dy, dz, color, hexColor });
  apantRenderCubes();
  document.getElementById('apant-new-cname').value = '';
  _apantRefreshEquipment();
}

function apantRemoveCube(idx) {
  ApantState.cubes.splice(idx, 1);
  apantRenderCubes();
  _apantRefreshEquipment();
}

/* ─── Cables de guarda ──────────────────────────────────────────────────────── */

function apantUpdateGuardSelects() {
  const selA = document.getElementById('apant-new-gi');
  const selB = document.getElementById('apant-new-gj');
  if (!selA || !selB) return;

  const opts = ApantState.masts.length
    ? ApantState.masts.map((m, i) =>
        `<option value="${i}">M${i} — (x=${m.x}, y=${m.y}, h=${m.h}m)</option>`
      ).join('')
    : '<option value="">— Agregue mástiles primero —</option>';

  selA.innerHTML = opts;
  selB.innerHTML = opts;
  if (ApantState.masts.length >= 2) selB.selectedIndex = 1;
}

function apantRenderGuardWires() {
  const list = document.getElementById('apant-guardas-list');
  if (!list) return;

  if (ApantState.guardWires.length === 0) {
    list.innerHTML = '<div class="apant-list-empty">Sin cables de guarda — opcional</div>';
  } else {
    list.innerHTML = ApantState.guardWires.map(([a, b], i) => `
      <div class="apant-list-item">
        <span class="apant-list-num">G${i}</span>
        <span class="apant-list-text">M${a} &nbsp;—&nbsp; M${b}</span>
        <button class="btn btn-danger" style="height:26px;padding:0 10px;font-size:0.75rem;line-height:1;" onclick="apantRemoveGuardWire(${i})">×</button>
      </div>`).join('');
  }
  apantUpdateGuardSelects();
}

function apantAddGuardWire() {
  const selA = document.getElementById('apant-new-gi');
  const selB = document.getElementById('apant-new-gj');
  if (!selA || !selB || selA.value === '' || selB.value === '') {
    showToast('Seleccione dos mástiles para el cable de guarda', 'error');
    return;
  }
  const a = parseInt(selA.value);
  const b = parseInt(selB.value);
  if (a === b) {
    showToast('Los dos mástiles deben ser diferentes', 'error');
    return;
  }
  if (ApantState.guardWires.some(([x, y]) => (x === a && y === b) || (x === b && y === a))) {
    showToast('Ese cable de guarda ya existe', 'error');
    return;
  }
  ApantState.guardWires.push([a, b]);
  apantRenderGuardWires();
}

function apantRemoveGuardWire(idx) {
  ApantState.guardWires.splice(idx, 1);
  apantRenderGuardWires();
}

/* ─── Ejecutar cálculo ──────────────────────────────────────────────────────── */

async function apantCalcular() {
  if (ApantState.masts.length === 0) {
    showToast('Agregue al menos un mástil antes de calcular', 'error');
    apantSwitchTab('mastiles');
    return;
  }

  const btn     = document.getElementById('apant-btn-calc');
  const spinner = document.getElementById('apant-spinner');
  const errorEl = document.getElementById('apant-error');

  btn.disabled               = true;
  spinner.style.display      = 'flex';
  errorEl.style.display      = 'none';
  errorEl.textContent        = '';
  document.getElementById('apant-resultados').style.display = 'none';

  // Ocultar panel de verificación durante recálculo
  _apantVerifData  = null;
  _apantLastResult = null;
  _apantVerifOpen  = false;
  const _vpReset = document.getElementById('apant-verif-panel');
  if (_vpReset) _vpReset.style.display = 'none';
  const verifRowReset = document.getElementById('apant-verif-row');
  if (verifRowReset) verifRowReset.style.display = 'none';

  const BIL = parseFloat(document.getElementById('apant-bil').value) || 350;
  const Zs  = parseFloat(document.getElementById('apant-zs').value)  || 300;
  const k   = parseFloat(document.getElementById('apant-k').value)   || 1.2;

  const body = {
    masts:                 ApantState.masts,
    cubes:                 ApantState.cubes,
    guard_wire_pairs:      ApantState.guardWires,
    BIL, Zs, k,
    final_grid_n:          80,
    mmq_patch_n:           40,
    mmm_patch_n:           40,
    verification_margin:   0,
    verification_sample_n: 15,
    include_bottom:        false,
  };

  try {
    const res  = await fetch('/apantallamiento/calcular', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(body),
    });
    const data = await res.json();

    if (!res.ok || data.error) {
      const msg = data.error || `Error del servidor (${res.status})`;
      errorEl.textContent   = msg;
      errorEl.style.display = '';
      showToast('Error en el cálculo de apantallamiento', 'error');
    } else {
      // Guardar datos de verificación y resetear panel
      _apantVerifData = (data.verification && data.verification.length > 0) ? data.verification : null;
      _apantVerifOpen = false;
      const verifPanel = document.getElementById('apant-verif-panel');
      if (verifPanel) verifPanel.style.display = 'none';
      const verifRow = document.getElementById('apant-verif-row');
      if (verifRow) verifRow.style.display = 'flex';
      _apantLastResult = { S: data.S, verification: data.verification || [], _recs: null };
      apantRenderResults(data);
      showToast('Cálculo de apantallamiento completado', 'success');
    }
  } catch (err) {
    errorEl.textContent   = `Sin conexión con el servidor: ${err.message}`;
    errorEl.style.display = '';
    showToast('No se pudo conectar con el servidor', 'error');
  } finally {
    btn.disabled          = false;
    spinner.style.display = 'none';
  }
}

/* ─── Wireframe de aristas de equipos ──────────────────────────────────────── */

function _apantBuildEdgeTraces() {
  const traces = [];
  for (const c of ApantState.cubes) {
    const x0 = c.x,        x1 = c.x + c.dx;
    const y0 = c.y,        y1 = c.y + c.dy;
    const z0 = c.z,        z1 = c.z + c.dz;
    const col = c.hexColor || '#F5C400';

    // ── Caras coloreadas semitransparentes (Mesh3d) ──────────────────────────
    // 8 vértices del cubo
    const vx = [x0, x1, x1, x0, x0, x1, x1, x0];
    const vy = [y0, y0, y1, y1, y0, y0, y1, y1];
    const vz = [z0, z0, z0, z0, z1, z1, z1, z1];
    // 12 triángulos (6 caras × 2)
    const i_ = [0,0, 4,4, 0,0, 2,2, 0,0, 1,1];
    const j_ = [1,2, 5,6, 1,5, 3,7, 3,7, 2,6];
    const k_ = [2,3, 6,7, 5,4, 7,6, 7,4, 6,5];
    // Extraer RGB del hex para poder añadir alpha
    const r = parseInt(col.slice(1,3),16);
    const g = parseInt(col.slice(3,5),16);
    const b = parseInt(col.slice(5,7),16);
    traces.push({
      type: 'mesh3d',
      x: vx, y: vy, z: vz,
      i: i_, j: j_, k: k_,
      color: `rgba(${r},${g},${b},0.30)`,
      name: c.name,
      showlegend: true,
      hoverinfo: 'name',
      flatshading: false,
    });

    // ── Aristas (wireframe) ──────────────────────────────────────────────────
    const ex = [], ey = [], ez = [];
    const segs = [
      [x0,y0,z0, x1,y0,z0], [x1,y0,z0, x1,y1,z0],   // cara inferior
      [x1,y1,z0, x0,y1,z0], [x0,y1,z0, x0,y0,z0],
      [x0,y0,z1, x1,y0,z1], [x1,y0,z1, x1,y1,z1],   // cara superior
      [x1,y1,z1, x0,y1,z1], [x0,y1,z1, x0,y0,z1],
      [x0,y0,z0, x0,y0,z1], [x1,y0,z0, x1,y0,z1],   // pilares verticales
      [x1,y1,z0, x1,y1,z1], [x0,y1,z0, x0,y1,z1],
    ];
    for (const [ax,ay,az,bx,by,bz] of segs) {
      ex.push(ax, bx, null);
      ey.push(ay, by, null);
      ez.push(az, bz, null);
    }
    traces.push({
      type: 'scatter3d', mode: 'lines',
      x: ex, y: ey, z: ez,
      line: { color: col, width: 4 },
      name: `Marco ${c.name}`,
      showlegend: false, hoverinfo: 'skip',
    });

    // ── Patas punteadas al suelo ─────────────────────────────────────────────
    if (z0 > 0.01) {
      const lx = [], ly = [], lz = [];
      for (const [px, py] of [[x0,y0],[x1,y0],[x1,y1],[x0,y1]]) {
        lx.push(px, px, null);
        ly.push(py, py, null);
        lz.push(z0, 0,  null);
      }
      traces.push({
        type: 'scatter3d', mode: 'lines',
        x: lx, y: ly, z: lz,
        line: { color: col, width: 1, dash: 'dot' },
        name: `Patas ${c.name}`,
        showlegend: false, hoverinfo: 'skip', opacity: 0.5,
      });
    }
  }
  return traces;
}

/* ─── Renderizar resultados ─────────────────────────────────────────────────── */

function apantRenderResults(data) {
  // Radio de esfera
  const S = data.S;
  document.getElementById('apant-val-S').textContent = S ? S.toFixed(2) : '—';

  // Gráfico 3D Plotly
  if (data.fig_json) {
    try {
      const fig = JSON.parse(data.fig_json);

      // Guardar trazas del modelo para actualizar el chart sin recalcular.
      // Excluir trazas de equipos que Python también mete en la figura —
      // el JS las gestiona exclusivamente vía _apantBuildEdgeTraces().
      // Python genera:
      //   Mesh3d   → name = cubeName  o  "Volumen del equipo - cubeName"
      //   Scatter3d→ name = "Aristas cubeName"  o  "Aristas del equipo - cubeName"
      const _cubeNameSet = new Set(ApantState.cubes.map(c => c.name));
      _apantModelTraces = fig.data.filter(t => {
        const tname = (t.name || '').trim();
        const baseName = tname.split(' | ')[0].trim();
        // Nombre exacto (Mesh3d del cuerpo)
        if (_cubeNameSet.has(tname) || _cubeNameSet.has(baseName)) return false;
        // Variantes con prefijo que genera Python
        for (const cname of _cubeNameSet) {
          if (tname === `Aristas ${cname}`             || baseName === `Aristas ${cname}`)             return false;
          if (tname === `Aristas del equipo - ${cname}`|| baseName === `Aristas del equipo - ${cname}`) return false;
          if (tname === `Volumen del equipo - ${cname}`|| baseName === `Volumen del equipo - ${cname}`) return false;
        }
        return true;
      });
      _apantModelLayout = Object.assign({}, fig.layout, {
        paper_bgcolor: 'transparent',
        plot_bgcolor:  'transparent',
        margin:        { l: 0, r: 0, t: 24, b: 0 },
        font:          { family: 'DM Sans, sans-serif', size: 11, color: '#4A5E7A' },
        title:         { text: '' },
      });

      // Colorbar chica: solo a la primera superficie que no sea el suelo
      for (const t of fig.data) {
        if (t.type !== 'surface') continue;
        const n = (t.name || '').toLowerCase();
        if (n === 'suelo' || n === '') continue;
        t.showscale = true;
        t.colorbar  = { thickness: 12, len: 0.38, x: 1.02, y: 0.28,
                        title: { text: 'm', side: 'right', font: { size: 10 } },
                        tickfont: { size: 9 }, outlinewidth: 0 };
        break;
      }

      // Localizar la primera superficie significativa y preparar colorbar (oculta)
      _apantSurfaceTraceIdx = -1;
      for (let _si = 0; _si < fig.data.length; _si++) {
        const _t = fig.data[_si];
        if (_t.type !== 'surface') continue;
        const _n = (_t.name || '').toLowerCase();
        if (_n === 'suelo' || _n === '') continue;
        _t.showscale = false;
        _t.colorbar  = { thickness: 12, len: 0.45, x: 1.02, y: 0.28,
                         title: { text: 'm', side: 'right', font: { size: 10 } },
                         tickfont: { size: 9 }, outlinewidth: 0 };
        _apantSurfaceTraceIdx = _si;
        break;
      }

      // Añadir wireframes de equipos al mismo render (sin flash)
      const allTraces = [...fig.data, ..._apantBuildEdgeTraces()];

      // Clasificar trazas auxiliares del modelo (antes de añadir las propias)
      _apantAuxIndices = allTraces.reduce((acc, t, i) => {
        if (_APANT_AUX_PATTERNS.some(p => p.test((t.name || '').trim()))) acc.push(i);
        return acc;
      }, []);

      Plotly.react('apant-chart', allTraces, _apantModelLayout, {
        responsive:                true,
        displayModeBar:            true,
        showEditInChartStudio:     false,
        showSendToCloud:           false,
        modeBarButtonsToRemove:    ['toImage', 'sendDataToCloud', 'editInChartStudio'],
      });

      _apantCleanMode = false;
      const btnClean = document.getElementById('apant-btn-clean');
      if (btnClean) { btnClean.classList.remove('active'); btnClean.textContent = 'Vista limpia'; }
    } catch (e) {
      console.error('Error al parsear fig_json:', e);
    }
  }

  // Cálculos estadísticos IEEE 998
  apantCalcIEEE998();

  // Mostrar sección de resultados
  const resEl = document.getElementById('apant-resultados');
  resEl.style.display = '';

  // Forzar resize del gráfico 3D (estaba oculto antes de mostrar resultados)
  setTimeout(() => {
    if (typeof Plotly !== 'undefined') Plotly.Plots.resize('apant-chart');
  }, 100);
}

/* ─── Cálculos estadísticos IEEE 998 ───────────────────────────────────────── */

function apantCalcIEEE998() {
  const BIL = parseFloat(document.getElementById('apant-bil')?.value) || 350;
  const Zs  = parseFloat(document.getElementById('apant-zs')?.value)  || 300;
  const k   = parseFloat(document.getElementById('apant-k')?.value)   || 1.2;
  const A   = parseFloat(document.getElementById('apant-area')?.value);
  // Ng tomado del campo calculado (GFD del proyecto o desde Td)
  const Ng  = parseFloat(document.getElementById('apant-ng-calc')?.value);

  const wrap = document.getElementById('apant-ieee-wrap');
  const body = document.getElementById('apant-ieee-body');
  if (!wrap || !body) return;

  const hasNg = Ng > 0;
  const hasA  = A  > 0;

  const sig    = v => parseFloat(v.toPrecision(4));
  const fmtNum = (v, u) => `${sig(v)} <span style="font-size:0.7rem;font-weight:400;color:var(--text-light);">${u}</span>`;
  const fmtPct = v      => `${sig(v * 100)} <span style="font-size:0.7rem;font-weight:400;color:var(--text-light);">%</span>`;
  const NA     = (hint) => `<span style="font-size:0.82rem;color:var(--text-light);font-style:italic;">— ${hint}</span>`;

  // Valores que siempre se pueden calcular (solo necesitan BIL, Zs, k)
  const Is       = (2.2 * BIL) / Zs;
  const S        = 8 * k * Math.pow(Is, 0.65);
  const P_supera = 1 / (1 + Math.pow(Is / 24, 2.6));
  const P_pen    = 1 - P_supera;

  // Valores que dependen de Ng y A
  const Ns         = hasNg && hasA  ? Ng * A / 1_000_000        : null;
  const Ts         = Ns   > 0       ? 1 / Ns                    : null;
  const lambda_pen = Ns   != null   ? Ns * P_pen                : null;
  const T_pen      = lambda_pen > 0 ? 1 / lambda_pen            : null;

  const rows = [
    {
      formula: 'Ng (del proyecto)',
      label:   'Ng — Densidad de descargas a tierra',
      val:     hasNg ? fmtNum(Ng, 'flashes/km²·año') : NA('ingrese Td o cargue ubicación'),
    },
    {
      formula: 'Ns = Ng × A / 10⁶',
      label:   'Ns — Impactos directos esperados sobre el patio',
      val:     Ns != null ? (Ns > 0 ? fmtNum(Ns, 'impactos/año') : 'No calculable') : NA('ingrese Ng y A'),
    },
    {
      formula: 'Ts = 1 / Ns',
      label:   'Ts — Años promedio entre impactos directos',
      val:     Ns != null ? (Ts ? fmtNum(Ts, 'años/impacto') : '∞') : NA('ingrese Ng y A'),
    },
    {
      formula: 'Is = 2.2 × BIL / Zs',
      label:   'Is — Corriente crítica de rayo',
      val:     fmtNum(Is, 'kA'),
    },
    {
      formula: 'S = 8 × k × Is⁰·⁶⁵',
      label:   'S — Distancia de impacto (radio de esfera equivalente)',
      val:     fmtNum(S, 'm'),
    },
    {
      formula: 'P = 1 / (1 + (Is/24)²·⁶)',
      label:   'P — Probabilidad de que un rayo supere Is',
      val:     fmtPct(P_supera),
    },
    {
      formula: 'P_pen = 1 − P',
      label:   'P_pen — Probabilidad de penetración estimada',
      val:     fmtPct(P_pen),
    },
    {
      formula: 'λ = Ns × P_pen',
      label:   'λ — Tasa anual estimada de penetración',
      val:     lambda_pen != null ? (lambda_pen > 0 ? fmtNum(lambda_pen, 'penetraciones/año') : 'No calculable') : NA('ingrese Ng y A'),
    },
    {
      formula: 'T_pen = 1 / λ',
      label:   'T_pen — Años promedio entre penetraciones',
      val:     lambda_pen != null ? (T_pen ? fmtNum(T_pen, 'años/penetración') : '∞') : NA('ingrese Ng y A'),
    },
  ];

  const missingNote = (!hasNg || !hasA)
    ? `<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:var(--radius-md);padding:8px 12px;margin-bottom:12px;font-size:0.72rem;color:#92400e;">Para los parámetros estadísticos completos, asegúrese de ingresar <strong>Ng</strong> (configure la ubicación o ingrese Td) y <strong>A</strong> (área de la subestación).</div>`
    : '';

  body.innerHTML = `
    ${missingNote}
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px 14px;margin-bottom:14px;">
      ${rows.map(r => `
        <div style="border:1px solid var(--grey-line);border-radius:var(--radius-md);padding:11px 13px;background:var(--white);">
          <div style="font-size:0.68rem;color:var(--text-light);font-family:var(--font-mono);margin-bottom:3px;">${r.formula}</div>
          <div style="font-size:0.73rem;color:var(--text-mid);margin-bottom:5px;line-height:1.3;">${r.label}</div>
          <div style="font-size:1.05rem;font-weight:700;font-family:var(--font-mono);color:var(--blue-dark);">${r.val}</div>
        </div>`).join('')}
    </div>
    <div style="font-size:0.7rem;color:var(--text-light);line-height:1.6;border-top:1px solid var(--grey-line);padding-top:10px;">
      <strong>Nota:</strong> P_pen es la probabilidad complementaria de no intercepción (P_pen = 1 − P_supera). No equivale directamente a probabilidad de falla del sistema. La tasa λ indica la frecuencia estimada con que un rayo podría superar la envolvente de apantallamiento.
    </div>`;
  wrap.style.display = '';
}

/* ─── Exportar imagen ───────────────────────────────────────────────────────── */

function apantDescargarImagen() {
  Plotly.downloadImage('apant-chart', {
    format:   'png',
    width:    1600,
    height:   1000,
    filename: 'apantallamiento_terrashield',
  });
}

/* ─── Actualizar gráfico con wireframes sin recalcular ──────────────────────── */

function _apantRefreshEquipment() {
  if (_apantModelTraces.length === 0) return;
  const allTraces = [..._apantModelTraces, ..._apantBuildEdgeTraces()];
  // Recalcular aux indices con el nuevo set
  _apantAuxIndices = allTraces.reduce((acc, t, i) => {
    if (_APANT_AUX_PATTERNS.some(p => p.test((t.name || '').trim()))) acc.push(i);
    return acc;
  }, []);
  Plotly.react('apant-chart', allTraces, _apantModelLayout, {
    responsive: true, displayModeBar: true, showEditInChartStudio: false,
    showSendToCloud: false, modeBarButtonsToRemove: ['toImage', 'sendDataToCloud', 'editInChartStudio'],
  });
  // Si estaba en modo limpio, aplicarlo al nuevo chart
  if (_apantCleanMode) {
    Plotly.restyle('apant-chart', { visible: false }, _apantAuxIndices);
  }
}

/* ─── Verificación de apantallamiento ──────────────────────────────────────── */

async function apantVerificar() {
  if (ApantState.cubes.length === 0) {
    showToast('Agregue al menos un equipo para verificar', 'error');
    return;
  }

  const btn     = document.getElementById('apant-btn-verif-main');
  const spinner = document.getElementById('apant-verif-spinner');
  const errEl   = document.getElementById('apant-verif-error');
  const panel   = document.getElementById('apant-verif-panel');

  if (btn) btn.disabled = true;
  if (spinner) spinner.style.display = 'flex';
  if (errEl)   errEl.style.display   = 'none';

  try {
    const res  = await fetch('/apantallamiento/verificar', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ cubes: ApantState.cubes }),
    });
    const data = await res.json();

    if (!res.ok || data.error) {
      if (errEl) { errEl.textContent = data.error || 'Error en verificación'; errEl.style.display = ''; }
      showToast('Error en la verificación', 'error');
    } else {
      _apantVerifData = data.verification;
      if (_apantLastResult) _apantLastResult.verification = data.verification;
      apantRenderVerif(data.verification);
      if (panel) panel.style.display = '';
      showToast('Verificación completada', 'success');
    }
  } catch (err) {
    if (errEl) { errEl.textContent = `Sin conexión: ${err.message}`; errEl.style.display = ''; }
    showToast('No se pudo conectar con el servidor', 'error');
  } finally {
    if (btn)     btn.disabled         = false;
    if (spinner) spinner.style.display = 'none';
  }
}

function apantRenderVerif(verif) {
  const body = document.getElementById('apant-verif-body');
  if (!body) return;

  const allOk = verif.every(v => v.fully_shielded);

  // Mostrar/ocultar botón de recomendaciones
  const recBtn = document.getElementById('apant-btn-recomendaciones');
  if (recBtn) {
    recBtn.style.display = allOk ? 'none' : '';
  }

  // Resumen general
  const nOk    = verif.filter(v => v.fully_shielded).length;
  const nTotal = verif.length;

  const summaryColor = allOk ? '#16a34a' : nOk === 0 ? '#dc2626' : '#d97706';
  const summaryIcon  = allOk
    ? '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>'
    : '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>';
  const summaryText  = allOk
    ? `Todos los equipos quedan dentro de la capa de apantallamiento.`
    : `${nTotal - nOk} de ${nTotal} equipo${nTotal - nOk !== 1 ? 's' : ''} presenta${nTotal - nOk === 1 ? '' : 'n'} puntos fuera de la capa resultante.`;

  const rows = verif.map(v => {
    const pct = v.points_evaluated > 0
      ? (v.points_protected / v.points_evaluated) * 100
      : null;
    const pctStr   = pct != null ? pct.toFixed(1) + '%' : '—';
    const pctColor = pct == null ? '' : pct >= 100 ? 'color:#16a34a;' : pct >= 80 ? 'color:#d97706;' : 'color:#dc2626;';

    const badge = v.fully_shielded
      ? '<span class="badge-ok"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>Apantallado</span>'
      : '<span class="badge-error"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>Fuera de capa</span>';

    return `
      <tr>
        <td>${v.equipment_name || '—'}</td>
        <td class="mono">${v.points_protected}&nbsp;/&nbsp;${v.points_evaluated}</td>
        <td class="mono" style="font-weight:700;${pctColor}">${pctStr}</td>
        <td>${badge}</td>
      </tr>`;
  }).join('');

  body.innerHTML = `
    <div style="display:flex;align-items:center;gap:8px;padding:10px 16px;background:${allOk ? '#f0fdf4' : nOk === 0 ? '#fef2f2' : '#fffbeb'};border-bottom:1px solid var(--grey-line);">
      <span style="color:${summaryColor};display:flex;align-items:center;">${summaryIcon}</span>
      <span style="font-size:0.76rem;color:${summaryColor};font-weight:600;">${summaryText}</span>
    </div>
    <div style="overflow-x:auto;">
      <table class="result-table" style="margin:0;">
        <thead>
          <tr>
            <th>Equipo</th>
            <th>Puntos dentro&nbsp;/&nbsp;evaluados</th>
            <th>Cobertura</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
    <div style="padding:9px 16px;font-size:0.71rem;color:var(--text-light);border-top:1px solid var(--grey-line);">
      Verificación geométrica directa: cada punto muestreado del equipo se proyecta verticalmente contra la capa de apantallamiento resultante (superficies M-M-Q, M-M-M, M-M-N, N-N-M y mástil solo). Un punto queda protegido si la capa tiene al menos esa altura en esa coordenada.
    </div>`;
}

function apantToggleCleanView() {
  if (_apantAuxIndices.length === 0) return;
  _apantCleanMode = !_apantCleanMode;
  const btn = document.getElementById('apant-btn-clean');
  Plotly.restyle('apant-chart', { visible: !_apantCleanMode }, _apantAuxIndices);
  // Mostrar/ocultar colorbar junto con la vista limpia
  if (_apantSurfaceTraceIdx >= 0) {
    Plotly.restyle('apant-chart', { showscale: _apantCleanMode }, [_apantSurfaceTraceIdx]);
  }
  if (btn) {
    btn.textContent = _apantCleanMode ? 'Vista completa' : 'Vista limpia';
    btn.classList.toggle('active', _apantCleanMode);
  }
}

/* ─── Presets de cámara ─────────────────────────────────────────────────────── */

function apantSetCamera(view) {
  const UP = { x: 0, y: 0, z: 1 }; // mismo up en todos → comportamiento de ratón consistente
  const cameras = {
    top:   { eye: { x: 0.001, y: 0.001, z: 1.7  } },
    front: { eye: { x: 0.001, y: -1.7,  z: 0.001 } },
    side:  { eye: { x: 1.7,   y: 0.001, z: 0.001 } },
    '3d':  { eye: { x: 1.1,   y: 1.1,   z: 0.85  } },
  };
  const cam = cameras[view];
  if (!cam) return;
  Plotly.relayout('apant-chart', {
    'scene.camera': { eye: cam.eye, up: UP, center: { x: 0, y: 0, z: 0 } },
  });
}

/* ─── Recomendaciones ─────────────────────────────────────────────────────────── */

async function apantGenerarRecomendaciones() {
  if (!_apantVerifData) {
    showToast('Primero debes calcular el apantallamiento', 'error');
    return;
  }

  const btn = document.getElementById('apant-btn-recomendaciones');
  const _btnOriginalHTML = btn ? btn.innerHTML : '';
  const _SPINNER_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;animation:spin 1s linear infinite;"><circle cx="12" cy="12" r="10" stroke-opacity="0.25"/><path d="M12 2a10 10 0 0 1 10 10" stroke-opacity="1"/></svg>';

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `${_SPINNER_SVG} Generando...`;
  }

  try {
    const SVal = document.getElementById('apant-val-S')?.textContent || '100';
    const S = parseFloat(SVal) || 100;

    const payload = {
      params: {
        masts: ApantState.masts,
        cubes: ApantState.cubes,
        guard_wire_pairs: ApantState.guardWires,
        BIL: parseFloat(document.getElementById('apant-bil')?.value || '350'),
        Zs: parseFloat(document.getElementById('apant-zs')?.value || '300'),
        k: parseFloat(document.getElementById('apant-k')?.value || '1.2'),
        S: S,
      },
      S: S,
      verification: _apantVerifData,
    };

    const response = await fetch('/apantallamiento/recomendar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const result = await response.json();

    if (result.ok && Array.isArray(result.recommendations) && result.recommendations.length > 0) {
      apantRenderRecommendations(result.recommendations);
      showToast(`${result.recommendations.length} recomendación(es) generada(s)`, 'success');
    } else if (result.ok) {
      // El backend respondió OK pero no encontró soluciones válidas
      apantRenderNoRecommendations(result.diagnostics || []);
      showToast('No se encontró solución automática para la configuración actual', 'info');
    } else {
      showToast('Error del servidor: ' + (result.error || 'desconocido'), 'error');
    }
  } catch (error) {
    showToast('Error de conexión: ' + error.message, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = _btnOriginalHTML;
    }
  }
}

function apantRenderNoRecommendations(diagnostics) {
  const panel = document.getElementById('apant-recs-panel');
  const body  = document.getElementById('apant-recs-body');
  if (!panel || !body) return;

  _apantLastRecommendations = null;

  let diagHTML = '';
  if (diagnostics && diagnostics.length > 0) {
    diagHTML = `<ul style="margin:8px 0 0 0;padding-left:18px;font-size:0.75rem;color:var(--text-light);">
      ${diagnostics.map(d => `<li>${d}</li>`).join('')}
    </ul>`;
  }

  body.innerHTML = `
    <div style="display:flex;gap:12px;align-items:flex-start;padding:4px 0;">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
           style="width:18px;height:18px;flex-shrink:0;margin-top:1px;color:#d97706;">
        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <div>
        <div style="font-size:0.82rem;font-weight:600;color:var(--text-dark);margin-bottom:4px;">
          No se encontró solución automática
        </div>
        <div style="font-size:0.78rem;color:var(--text-light);">
          El modelo no pudo garantizar cobertura completa con las opciones evaluadas
          (mástil alineado o cable entre mástiles existentes). Revisa la configuración
          o ajusta manualmente la altura y posición de los mástiles.
        </div>
        ${diagHTML}
      </div>
    </div>`;
  panel.style.display = '';
}

function apantRenderRecommendations(recommendations) {
  const panel = document.getElementById('apant-recs-panel');
  const body = document.getElementById('apant-recs-body');

  if (!recommendations || recommendations.length === 0) {
    apantRenderNoRecommendations([]);
    return;
  }

  // Guardar recomendaciones para usar en apantApplyRecommendation y exportarPDF
  _apantLastRecommendations = recommendations;
  if (_apantLastResult) _apantLastResult._recs = recommendations;

  let html = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">';
  recommendations.forEach((rec, idx) => {
    const typeIcon = rec.type === 'add_mast'
      ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px;color:#3b82f6;flex-shrink:0;"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>'
      : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px;color:#8b5cf6;flex-shrink:0;"><path d="M3 4.5C3 3.12 4.12 2 5.5 2h13C19.88 2 21 3.12 21 4.5v15c0 1.38-1.12 2.5-2.5 2.5h-13C4.12 22 3 20.88 3 19.5v-15z"/><path d="M8 13h8"/></svg>';

    const plotDivId = `apant-rec-plot-${idx}`;

    html += `
      <div style="padding:14px 16px;border:1px solid var(--grey-line);border-radius:8px;margin-bottom:12px;background:var(--bg-light);">
        <div style="display:flex;gap:10px;align-items:flex-start;margin-bottom:8px;">
          ${typeIcon}
          <div style="flex:1;">
            <div style="font-weight:600;color:var(--text-dark);margin-bottom:4px;">${rec.title}</div>
            <div style="font-size:0.78rem;color:var(--text-light);">${rec.reason || ''}</div>
          </div>
        </div>
        <div style="font-size:0.74rem;padding:6px 0;border-top:1px solid rgba(0,0,0,0.06);margin-bottom:6px;">
          <span style="color:var(--text-light);">Equipo objetivo:</span>
          <strong style="color:var(--text-dark);">${rec.target_equipment || '—'}</strong>
        </div>
        ${rec.fig_json ? `<div id="${plotDivId}" style="width:100%;height:270px;border-radius:6px;overflow:hidden;background:#f8fafc;margin-bottom:8px;"></div>` : ''}
        <div style="display:flex;gap:6px;margin-top:8px;">
          <button class="btn btn-secondary" onclick="apantApplyRecommendation(${idx})" style="height:30px;font-size:0.73rem;flex:1;">Aplicar</button>
          <button class="btn" onclick="apantDismissRecommendation()" style="height:30px;font-size:0.73rem;flex:0 0 auto;padding:0 14px;">Descartar</button>
        </div>
      </div>`;
  });
  html += '</div>';

  body.innerHTML = html;
  panel.style.display = '';

  // Renderizar figuras Plotly 3D despues de insertar el HTML
  recommendations.forEach((rec, idx) => {
    if (!rec.fig_json) return;
    const div = document.getElementById(`apant-rec-plot-${idx}`);
    if (!div) return;
    try {
      const fig = JSON.parse(rec.fig_json);
      Plotly.react(div, fig.data, Object.assign({}, fig.layout, {
        margin: { l: 0, r: 0, t: 8, b: 0 },
        height: 270,
        paper_bgcolor: 'rgba(0,0,0,0)',
      }), { responsive: true, displayModeBar: false });
    } catch (e) {
      console.warn('Error al renderizar gráfico de recomendación:', e);
    }
  });
}

function apantHideRecommendations() {
  const panel = document.getElementById('apant-recs-panel');
  if (panel) panel.style.display = 'none';
}

function apantApplyRecommendation(idx) {
  // Obtener la recomendación actual del HTML (si todavía existe)
  if (!_apantLastRecommendations || idx >= _apantLastRecommendations.length) {
    showToast('La recomendación ya no está disponible', 'error');
    return;
  }

  const rec = _apantLastRecommendations[idx];
  if (!rec || !rec.actions) {
    showToast('Datos de recomendación inválidos', 'error');
    return;
  }

  console.log('[apantApplyRecommendation] Aplicando:', rec.title, rec.actions);

  // Rastrear índices de nuevos mástiles para cables
  let newMastIndices = [];

  // Aplicar cada acción de la recomendación
  for (const action of rec.actions) {
    if (action.action === 'add_mast') {
      // Agregar nuevo mástil
      const newMastIdx = ApantState.masts.length;
      ApantState.masts.push({
        x: action.x,
        y: action.y,
        h: action.h,
      });
      newMastIndices.push(newMastIdx);
      console.log(`  → Agregado mástil M${newMastIdx} en (${action.x}, ${action.y}, h=${action.h})`);

    } else if (action.action === 'add_guard_wire') {
      // Determinar índices del cable
      let from_idx, to_idx;

      if (action.from_existing !== undefined && action.to_existing !== undefined) {
        // Cable entre dos mástiles existentes
        from_idx = action.from_existing;
        to_idx = action.to_existing;
      } else if (action.from_existing !== undefined && action.to_new !== undefined) {
        // Cable del existente al nuevo
        from_idx = action.from_existing;
        if (newMastIndices[action.to_new] === undefined) {
          console.warn(`  ⚠ Índice de mástil nuevo inválido: to_new=${action.to_new}`, action);
          continue;
        }
        to_idx = newMastIndices[action.to_new];
      } else if (action.from_new !== undefined && action.to_new !== undefined) {
        // Cable entre dos nuevos
        if (newMastIndices[action.from_new] === undefined || newMastIndices[action.to_new] === undefined) {
          console.warn(`  ⚠ Índices de mástil nuevo inválidos: from_new=${action.from_new}, to_new=${action.to_new}`, action);
          continue;
        }
        from_idx = newMastIndices[action.from_new];
        to_idx = newMastIndices[action.to_new];
      } else {
        console.warn('  ⚠ Índices de cable inválidos:', action);
        continue;
      }

      ApantState.guardWires.push([from_idx, to_idx]);
      console.log(`  → Agregado cable M${from_idx} ← → M${to_idx}`);
    }
  }

  // Renderizar cambios en UI
  apantRenderMasts();
  apantRenderGuardWires();
  apantRenderCubes();

  // Ocultar panel de recomendaciones
  apantHideRecommendations();

  // Mostrar toast
  showToast(`✓ Recomendación aplicada: ${rec.title}`, 'success');

  // Recalcular apantallamiento con delay para que vea el cambio en UI
  setTimeout(() => {
    apantCalcular();
  }, 500);
}

function apantDismissRecommendation() {
  apantHideRecommendations();
}

