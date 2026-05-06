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

let _apantAuxIndices  = [];    // índices de trazas auxiliares (se calculan al renderizar)
let _apantCleanMode   = false; // estado del toggle de vista limpia
let _apantLastParams  = null;  // último body enviado a /calcular (para recomendaciones)
let _apantLastResult  = null;  // último resultado de /calcular (incluye S y verification)

// Patrón de trazas auxiliares que el modelo genera como geometría de construcción
const _APANT_AUX_PATTERNS = [
  /^Base\s/i, /^Segmento\s/i, /^Cresta/i, /^Borde\s/i,
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
  const hexColor = document.getElementById('apant-new-ccolor')?.value || '#F5C400';
  const color    = hexToRgba(hexColor, 0.95);
  ApantState.cubes.push({ name, x, y, z, dx, dy, dz, color, hexColor });
  apantRenderCubes();
  document.getElementById('apant-new-cname').value = '';
}

function apantRemoveCube(idx) {
  ApantState.cubes.splice(idx, 1);
  apantRenderCubes();
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

  const BIL = parseFloat(document.getElementById('apant-bil').value) || 350;
  const Zs  = parseFloat(document.getElementById('apant-zs').value)  || 300;
  const k   = parseFloat(document.getElementById('apant-k').value)   || 1.2;

  _apantLastParams = {
    masts:            JSON.parse(JSON.stringify(ApantState.masts)),
    cubes:            JSON.parse(JSON.stringify(ApantState.cubes)),
    guard_wire_pairs: JSON.parse(JSON.stringify(ApantState.guardWires)),
    BIL, Zs, k,
  };

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
      _apantLastResult = data;
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

    // Las 12 aristas del cubo como un único scatter3d con separadores null
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

    // Patas punteadas al suelo desde las 4 esquinas inferiores (cue de profundidad)
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

      // Clasificar trazas auxiliares del modelo (antes de añadir las propias)
      _apantAuxIndices = fig.data.reduce((acc, t, i) => {
        if (_APANT_AUX_PATTERNS.some(p => p.test((t.name || '').trim()))) acc.push(i);
        return acc;
      }, []);

      // Añadir wireframes de equipos al mismo render (sin flash)
      const allTraces = [...fig.data, ..._apantBuildEdgeTraces()];

      Plotly.react('apant-chart', allTraces, Object.assign({}, fig.layout, {
        paper_bgcolor: 'transparent',
        plot_bgcolor:  'transparent',
        margin:        { l: 0, r: 0, t: 24, b: 0 },
        font:          { family: 'DM Sans, sans-serif', size: 11, color: '#4A5E7A' },
      }), {
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

  // Tabla de verificación
  const verif     = data.verification || [];
  const verifWrap = document.getElementById('apant-verif-wrap');
  const tbody     = document.getElementById('apant-verif-tbody');

  if (verif.length > 0 && tbody && verifWrap) {
    tbody.innerHTML = verif.map(v => {
      const badge  = v.fully_shielded
        ? '<span class="badge-ok"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>Protegido</span>'
        : '<span class="badge-error"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>Sin protección</span>';
      const pctVal = v.points_evaluated > 0
        ? (v.points_protected / v.points_evaluated) * 100
        : null;
      const pctStr = pctVal != null ? pctVal.toFixed(1) + '%' : '—';
      const pctColor = pctVal == null ? '' : pctVal >= 100 ? 'color:#16a34a;' : pctVal >= 80 ? 'color:#d97706;' : 'color:#dc2626;';
      const excess = v.max_excess_m != null
        ? `+${v.max_excess_m.toFixed(2)} m`
        : '—';
      return `
        <tr>
          <td>${v.equipment_name || '—'}</td>
          <td class="mono">${v.points_protected}&nbsp;/&nbsp;${v.points_evaluated}</td>
          <td class="mono" style="font-weight:700;${pctColor}">${pctStr}</td>
          <td class="mono">${v.fully_shielded ? '<span style="color:var(--text-light)">—</span>' : excess}</td>
          <td>${badge}</td>
        </tr>`;
    }).join('');
    verifWrap.style.display = '';
  } else if (verifWrap) {
    verifWrap.style.display = 'none';
  }

  // Cálculos estadísticos IEEE 998
  apantCalcIEEE998();

  // Panel de recomendaciones (solo si hay equipos no apantallados)
  const recsOuter = document.getElementById('apant-recs-outer');
  const recsBody  = document.getElementById('apant-recs-body');
  const hasUnshielded = (data.verification || []).some(v => !v.fully_shielded);
  if (recsOuter) {
    recsOuter.style.display = hasUnshielded ? '' : 'none';
    if (recsBody && hasUnshielded) {
      recsBody.innerHTML = '<div style="font-size:0.78rem;color:var(--text-light);">Haga clic en "Analizar recomendaciones" para generar propuestas de mejora basadas en los puntos críticos.</div>';
    }
  }

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

function apantToggleCleanView() {
  if (_apantAuxIndices.length === 0) return;
  _apantCleanMode = !_apantCleanMode;
  const btn = document.getElementById('apant-btn-clean');
  Plotly.restyle('apant-chart', { visible: !_apantCleanMode }, _apantAuxIndices);
  if (btn) {
    btn.textContent = _apantCleanMode ? 'Vista completa' : 'Vista limpia';
    btn.classList.toggle('active', _apantCleanMode);
  }
}

/* ─── Recomendaciones correctivas ──────────────────────────────────────────── */

async function apantGetRecommendations() {
  if (!_apantLastParams || !_apantLastResult) {
    showToast('Calcule el apantallamiento primero', 'error');
    return;
  }

  const btn  = document.getElementById('apant-btn-recs');
  const body = document.getElementById('apant-recs-body');
  if (!btn || !body) return;

  btn.disabled  = true;
  body.innerHTML = '<div style="font-size:0.78rem;color:var(--text-light);display:flex;align-items:center;gap:8px;"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;animation:spin 1s linear infinite;"><path d="M21 12a9 9 0 11-6.219-8.56"/></svg>Analizando puntos críticos y generando propuestas…</div>';

  try {
    const res  = await fetch('/apantallamiento/recomendar', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        params:       _apantLastParams,
        S:            _apantLastResult.S,
        verification: _apantLastResult.verification,
      }),
    });
    const data = await res.json();
    if (!res.ok || data.error) {
      body.innerHTML = `<div style="font-size:0.78rem;color:var(--error);">${data.error || 'Error al generar recomendaciones'}</div>`;
    } else {
      const recs = data.recommendations || [];
      if (_apantLastResult) _apantLastResult._recs = recs;
      apantRenderRecommendations(recs);
    }
  } catch (err) {
    body.innerHTML = `<div style="font-size:0.78rem;color:var(--error);">Sin conexión: ${err.message}</div>`;
  } finally {
    btn.disabled = false;
  }
}

function apantRenderRecommendations(recs) {
  const body = document.getElementById('apant-recs-body');
  if (!body) return;

  if (recs.length === 0) {
    body.innerHTML = '<div style="font-size:0.78rem;color:var(--text-light);">No se generaron propuestas. Verifique que existan equipos sin protección completa.</div>';
    return;
  }

  const typeIcon = {
    add_mast:              '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;flex-shrink:0;"><line x1="12" y1="2" x2="12" y2="22"/><path d="M8 6h4M8 10h6M8 14h4"/></svg>',
    add_guard_wire:        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;flex-shrink:0;"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>',
    reduce_spacing:        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;flex-shrink:0;"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>',
    add_intermediate_guard:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;flex-shrink:0;"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
  };

  body.innerHTML = recs.map((rec, idx) => {
    const v     = rec.validation || {};
    const ok    = v.predicted_fully_shielded;
    const badge = ok === true
      ? '<span class="badge-ok" style="font-size:0.68rem;"><svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>Verificado: protección completa</span>'
      : ok === false
        ? '<span class="badge-error" style="font-size:0.68rem;"><svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>Protección parcial</span>'
        : '<span style="font-size:0.68rem;color:var(--text-light);">Sin verificación</span>';

    const actionsHtml = (rec.actions || [])
      .filter(a => a.action !== 'add_intermediate_guard')
      .map(a => {
        if (a.action === 'add_mast')
          return `<li>Agregar mástil en <strong>x = ${a.x} m</strong>, <strong>y = ${a.y} m</strong>, <strong>h = ${a.h} m</strong></li>`;
        if (a.action === 'add_guard_wire')
          return `<li>Agregar cable de guarda entre los dos mástiles nuevos</li>`;
        return '';
      }).join('');

    const canApply = (rec.actions || []).some(a => a.action === 'add_mast' || a.action === 'add_guard_wire');

    return `
      <div style="border:1px solid var(--grey-line);border-radius:var(--radius-md);padding:14px 16px;margin-bottom:12px;background:var(--white);">
        <div style="display:flex;align-items:flex-start;gap:9px;margin-bottom:8px;">
          <span style="color:var(--blue-mid);margin-top:1px;">${typeIcon[rec.type] || ''}</span>
          <div style="flex:1;">
            <div style="font-size:0.82rem;font-weight:700;color:var(--text-dark);margin-bottom:3px;">${rec.title}</div>
            <div style="font-size:0.73rem;color:var(--text-mid);line-height:1.5;">${rec.reason}</div>
          </div>
          ${badge}
        </div>
        ${actionsHtml ? `<ul style="margin:0 0 10px 20px;padding:0;font-size:0.75rem;color:var(--text-mid);line-height:1.7;">${actionsHtml}</ul>` : ''}
        ${v.notes ? `<div style="font-size:0.7rem;color:var(--text-light);margin-bottom:10px;">${v.notes}${v.equipment_coverage ? ' &nbsp;·&nbsp; ' + v.equipment_coverage : ''}</div>` : ''}
        ${canApply ? `<button class="btn btn-secondary" style="height:30px;font-size:0.74rem;padding:0 14px;" onclick="apantApplyRecommendation(${idx})">Aplicar recomendación</button>` : ''}
      </div>`;
  }).join('');
}

function apantApplyRecommendation(idx) {
  const recs = _apantLastResult && _apantLastResult._recs;
  // Fallback: read from rendered DOM is not needed — store recs on _apantLastResult
  if (!recs || !recs[idx]) {
    showToast('Datos de recomendación no disponibles', 'error');
    return;
  }

  const rec      = recs[idx];
  const actions  = rec.actions || [];
  const newMastIndices = [];

  for (const action of actions) {
    if (action.action === 'add_mast') {
      newMastIndices.push(ApantState.masts.length);
      ApantState.masts.push({ x: action.x, y: action.y, h: action.h });
    } else if (action.action === 'add_guard_wire') {
      const fromIdx = newMastIndices[action.from_new] ?? newMastIndices[0];
      const toIdx   = newMastIndices[action.to_new]   ?? newMastIndices[1];
      if (fromIdx !== undefined && toIdx !== undefined && fromIdx !== toIdx) {
        ApantState.guardWires.push([fromIdx, toIdx]);
      }
    }
  }

  apantRenderMasts();
  apantRenderGuardWires();
  showToast('Recomendación aplicada. Recalcule para verificar los resultados.', 'success');
  if (newMastIndices.length > 0) apantSwitchTab('mastiles');
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

