/* =============================================
   TERRASHIELD — app.js
   Estado global, navegación, modales,
   gestión de proyectos, config y toasts.
   ============================================= */

/* =============================================
   APP STATE
   ============================================= */
const AppState = {
  currentProject: null,
  config: {
    theme: 'light',
    decimals: 4,
    decimalSep: '.',
    exportFormat: 'pdf',
    filename: 'TerraShield_Reporte'
  },
  locationValidated: false,
  validatedData: null,
  mallaHistoria: [],
  exportarDesbloqueado: false,
};

/* =============================================
   BOOT SEQUENCE
   ============================================= */
(function boot() {
  const bar    = document.getElementById('boot-bar');
  const splash = document.getElementById('screen-splash');

  const steps = [
    { pct: 25,  delay: 120 },
    { pct: 55,  delay: 300 },
    { pct: 78,  delay: 500 },
    { pct: 92,  delay: 700 },
    { pct: 100, delay: 900 }
  ];

  steps.forEach(s => {
    setTimeout(() => { bar.style.width = s.pct + '%'; }, s.delay);
  });

  setTimeout(() => {
    splash.style.opacity = '0';
    setTimeout(() => {
      splash.style.display = 'none';
      showScreen('screen-home');
    }, 600);
  }, 1200);
})();

/* =============================================
   SCREEN NAVIGATION
   ============================================= */
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => {
    s.classList.remove('active');
    s.style.display = 'none';
  });
  const target = document.getElementById(id);
  if (target) {
    target.style.display = 'flex';
    target.classList.add('active');
  }
}

/* =============================================
   MODAL MANAGEMENT
   ============================================= */
function openModal(id)  { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

// Cerrar modal al hacer clic en el overlay
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', function(e) {
    if (e.target === this) this.classList.remove('open');
  });
});

/* =============================================
   PAGE NAVIGATION (App)
   ============================================= */
function showPage(pageId, navItem) {
  document.querySelectorAll('.section-page').forEach(p => p.classList.remove('active'));
  const page = document.getElementById(pageId);
  if (page) page.classList.add('active');

  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  if (navItem) navItem.classList.add('active');

  const labels = {
    'page-inicio':   'INICIO',
    'page-apant':    'APANTALLAMIENTO',
    'page-malla':    'MALLA A TIERRA',
    'page-exportar': 'EXPORTAR REPORTE'
  };
  document.getElementById('topbar-section-name').textContent = labels[pageId] || pageId;
}

/* =============================================
   APANTALLAMIENTO: METHOD SELECT
   ============================================= */
function selectMethod(card) {
  document.querySelectorAll('.method-card').forEach(c => c.classList.remove('selected'));
  card.classList.add('selected');
}

/* =============================================
   APANTALLAMIENTO: Ng DESDE Td
   Ng = 0.0017 × Td^1.56  (IEEE Std 998)
   ============================================= */
function calcNgFromTd() {
  const td      = parseFloat(document.getElementById('apant-td')?.value);
  const ngInput = document.getElementById('apant-ng-calc');
  const fuente  = document.getElementById('apant-ng-fuente');
  if (!ngInput) return;

  if (!isNaN(td) && td > 0) {
    const ng = parseFloat((0.0017 * Math.pow(td, 1.56)).toFixed(3));
    ngInput.value = ng;
    if (fuente) fuente.textContent = '';
  } else {
    // Restaurar valor de referencia del proyecto si Td se borra
    const d = AppState.validatedData;
    if (d) {
      ngInput.value = d.ngDisplay || (d.ng !== null && d.ng !== undefined ? d.ng : 'No disponible');
      if (fuente) fuente.textContent = '';
    } else {
      ngInput.value = '';
      if (fuente) fuente.textContent = '';
    }
  }
}

/* =============================================
   MALLA: PRE-CARGAR ρ DESDE CLASIFICACIÓN
   ============================================= */
const MALLA_RHO_IEEE80 = {
  'Suelo Orgánico Húmedo': 10,
  'Suelo Húmedo':          100,
  'Suelo Seco':            1000,
  'Roca':                  10000
};

function mallaPrecargarRho(d) {
  const inputRho  = document.getElementById('m-rho');
  const selectCls = document.getElementById('m-rho-clase');
  const notaEl    = document.getElementById('m-rho-nota');
  if (!inputRho) return;

  const rho       = d.rhoSuelo  ?? null;
  const tipoSuelo = d.tipoSuelo ?? null;
  const sueloNota = d.sueloNota ?? null;

  // Determinar opción del select que corresponde al tipo clasificado
  const rhoClase = tipoSuelo && MALLA_RHO_IEEE80[tipoSuelo] !== undefined
    ? MALLA_RHO_IEEE80[tipoSuelo]
    : null;

  if (selectCls) {
    selectCls.value = rhoClase !== null ? String(rhoClase) : '';
  }

  if (rho !== null) {
    inputRho.value = rho;
  } else if (rhoClase !== null) {
    inputRho.value = rhoClase;
  }
  // Si no hay rho (no clasificable), dejar el valor actual sin tocar

  // Nota explicativa
  if (notaEl) {
    if (sueloNota) {
      notaEl.textContent = sueloNota;
      notaEl.style.display = 'block';
    } else {
      notaEl.textContent = '';
      notaEl.style.display = 'none';
    }
  }
}

/* =============================================
   CREATE PROJECT
   ============================================= */
function crearProyecto() {
  const name = document.getElementById('new-proj-name').value.trim();
  if (!name) {
    showToast('Ingrese un nombre para el proyecto', 'error');
    document.getElementById('new-proj-name').classList.add('error');
    return;
  }
  document.getElementById('new-proj-name').classList.remove('error');

  if (!AppState.locationValidated) {
    showToast('Valide la ubicación antes de crear el proyecto', 'error');
    return;
  }

  AppState.currentProject = {
    version: '1.0.0',
    nombre: name,
    tipo: 'Subestacion',
    creado: new Date().toISOString(),
    ubicacion: AppState.validatedData || {},
    datosGenerales: {},
    apantallamiento: {},
    malla: {},
    resultados: {}
  };

  document.getElementById('sb-proj-name').textContent = name;
  document.getElementById('topbar-proj-breadcrumb').textContent = `/ ${name}`;
  document.getElementById('dg-nombre').value = name;

  if (AppState.validatedData) {
    const d = AppState.validatedData;
    document.getElementById('stat-ng').textContent        = d.ng !== null && d.ng !== undefined ? parseFloat(d.ng).toFixed(2) : '—';
    document.getElementById('stat-ubicacion').textContent = d.municipio || '—';
    document.getElementById('stat-depto').textContent     = d.departamento || '—';

    // Temperatura en panel principal
    const statTemp = document.getElementById('stat-temp');
    if (statTemp) statTemp.textContent = d.temp ? d.temp.toFixed(1) : '—';

    // Pre-rellenar Tamb en módulo de malla
    if (d.temp) {
      const mTamb = document.getElementById('m-Tamb');
      const mTambFuente = document.getElementById('m-Tamb-fuente');
      if (mTamb) mTamb.value = parseFloat(d.temp.toFixed(1));
      if (mTambFuente) mTambFuente.style.display = '';
    }


    // Resistividad en módulo de malla — desde clasificación de suelo validada
    mallaPrecargarRho(d);

    // Ng en módulo de apantallamiento
    const apantNg     = document.getElementById('apant-ng-calc');
    const apantFuente = document.getElementById('apant-ng-fuente');
    if (apantNg) {
      apantNg.value = d.ng !== null && d.ng !== undefined ? d.ng : 'No disponible';
      if (apantFuente) apantFuente.textContent = '';
    }
  }

  // Crear archivo de historial en servidor
  fetch('/proyectos/nuevo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nombre: name })
  }).catch(() => {});

  // Resetear historial y estado de exportación
  AppState.mallaHistoria = [];
  AppState.exportarDesbloqueado = false;
  if (typeof mallaUpdateExportState === 'function') mallaUpdateExportState([]);

  closeModal('modal-new-project');
  showScreen('screen-app');
  showToast(`Proyecto "${name}" creado exitosamente`, 'success');
}

/* =============================================
   LOAD PROJECT (JSON)
   ============================================= */
function loadProject() {
  document.getElementById('file-input-project').click();
}

function handleProjectFile(event) {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(e) {
    try {
      const proj = JSON.parse(e.target.result);
      AppState.currentProject  = proj;
      AppState.locationValidated = true;
      AppState.validatedData   = proj.ubicacion || null;

      const name = proj.nombre || 'Proyecto cargado';
      document.getElementById('sb-proj-name').textContent = name;
      document.getElementById('topbar-proj-breadcrumb').textContent = `/ ${name}`;
      if (proj.datosGenerales?.nombre) {
        document.getElementById('dg-nombre').value = proj.datosGenerales.nombre;
      }

      if (proj.ubicacion) {
        const d = proj.ubicacion;
        if (d.ng)           document.getElementById('stat-ng').textContent = parseFloat(d.ng).toFixed(2);
        if (d.municipio)    document.getElementById('stat-ubicacion').textContent = d.municipio;
        if (d.departamento) document.getElementById('stat-depto').textContent     = d.departamento;
        const statTemp = document.getElementById('stat-temp');
        if (statTemp && d.temp) statTemp.textContent = parseFloat(d.temp).toFixed(1);
        if (d.temp) {
          const mTamb = document.getElementById('m-Tamb');
          const mTambFuente = document.getElementById('m-Tamb-fuente');
          if (mTamb) mTamb.value = parseFloat(parseFloat(d.temp).toFixed(1));
          if (mTambFuente) mTambFuente.style.display = '';
        }
        mallaPrecargarRho(d);
      }

      // Crear archivo de historial si no existe y cargar historial previo
      fetch('/proyectos/nuevo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre: name })
      }).then(() =>
        fetch(`/proyectos/${encodeURIComponent(name)}`)
      ).then(r => r.json()).then(hist => {
        AppState.mallaHistoria = hist;
        if (typeof mallaRenderHistorial === 'function')   mallaRenderHistorial(hist);
        if (typeof mallaUpdateExportState === 'function') mallaUpdateExportState(hist);
      }).catch(() => {
        AppState.mallaHistoria = [];
        AppState.exportarDesbloqueado = false;
      });

      showScreen('screen-app');
      showToast(`Proyecto "${name}" cargado correctamente`, 'success');
    } catch (err) {
      showToast('Error al leer el archivo JSON', 'error');
    }
  };
  reader.readAsText(file);
  event.target.value = '';
}

/* =============================================
   SAVE PROJECT (JSON)
   ============================================= */
function saveProject() {
  if (!AppState.currentProject) {
    showToast('No hay proyecto activo para guardar', 'error');
    return;
  }

  AppState.currentProject.datosGenerales = {
    nombre:       document.getElementById('dg-nombre')?.value       || AppState.currentProject.nombre,
    propietario:  document.getElementById('dg-propietario')?.value  || '',
    responsable:  document.getElementById('dg-responsable')?.value  || '',
    actualizado:  new Date().toISOString()
  };

  // Guardar historial de malla si existe
  if (AppState.mallaHistoria?.length > 0) {
    AppState.currentProject.malla = { historial: AppState.mallaHistoria };
  }

  const blob = new Blob([JSON.stringify(AppState.currentProject, null, 2)], { type: 'application/json' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = (AppState.config.filename || 'TerraShield_Proyecto') + '.json';
  a.click();
  URL.revokeObjectURL(url);
  showToast('Proyecto guardado como JSON', 'success');
}

/* =============================================
   EXPORT TXT
   ============================================= */
function exportTXT() {
  if (!AppState.currentProject) { showToast('No hay proyecto activo', 'error'); return; }
  const p = AppState.currentProject;
  const d = p.ubicacion || {};
  let txt  = `=== TERRASHIELD v1.0.0 — REPORTE TÉCNICO ===\n`;
  txt += `Fecha: ${new Date().toLocaleString('es-CO')}\n\n`;
  txt += `PROYECTO: ${p.nombre || '—'}\n`;
  txt += `Tipo: Subestación eléctrica\n\n`;
  txt += `--- UBICACIÓN ---\n`;
  txt += `Departamento: ${d.departamento || '—'}\n`;
  txt += `Municipio: ${d.municipio || '—'}\n`;
  txt += `Latitud: ${d.lat || '—'}°N\n`;
  txt += `Longitud: ${d.lon || '—'}°W\n`;
  txt += `Ng (densidad de rayos): ${d.ng || '—'} rayos/km²/año\n`;
  txt += `Temperatura estimada: ${d.temp || '—'} °C\n\n`;
  // Apantallamiento
  txt += `--- APANTALLAMIENTO (IEEE Std 998 — EGM) ---\n`;
  if (typeof _apantLastResult !== 'undefined' && _apantLastResult && _apantLastResult.S) {
    const ar = _apantLastResult;
    txt += `BIL: ${document.getElementById('apant-bil')?.value || '—'} kV\n`;
    txt += `Zs:  ${document.getElementById('apant-zs')?.value  || '—'} Ω\n`;
    txt += `k:   ${document.getElementById('apant-k')?.value   || '—'}\n`;
    txt += `S (radio de esfera rodante): ${ar.S != null ? ar.S.toFixed(2) : '—'} m\n`;
    const ngTxt = document.getElementById('apant-ng-calc')?.value?.trim() || '—';
    const aTxt  = document.getElementById('apant-area')?.value || '—';
    txt += `Ng:  ${ngTxt} flashes/km²·año\n`;
    txt += `A (área subestación): ${aTxt} m²\n`;
    const ngN = parseFloat(ngTxt);
    const aN  = parseFloat(aTxt);
    if (ngN > 0 && aN > 0) {
      const bilN = parseFloat(document.getElementById('apant-bil')?.value) || 350;
      const zsN  = parseFloat(document.getElementById('apant-zs')?.value)  || 300;
      const kN   = parseFloat(document.getElementById('apant-k')?.value)   || 1.2;
      const IsN  = (2.2 * bilN) / zsN;
      const NsN  = ngN * aN / 1e6;
      const PsN  = 1 / (1 + Math.pow(IsN / 24, 2.6));
      const PpN  = 1 - PsN;
      const lamN = NsN * PpN;
      const f4   = v => isFinite(v) ? parseFloat(v.toPrecision(4)) : '∞';
      txt += `Is (corriente crítica): ${f4(IsN)} kA\n`;
      txt += `Ns (impactos directos esperados): ${f4(NsN)} impactos/año\n`;
      txt += `P_pen (prob. de penetración estimada): ${f4(PpN * 100)} %\n`;
      txt += `λ (tasa anual de penetración): ${lamN > 0 ? f4(lamN) : '0'} pen./año\n`;
      txt += `T_pen (años entre penetraciones): ${lamN > 0 ? f4(1/lamN) : '∞'} años/pen.\n`;
    }
    if (ar.verification && ar.verification.length > 0) {
      txt += `\nVerificación de equipos:\n`;
      ar.verification.forEach(v => {
        const pct = v.points_evaluated > 0
          ? ((v.points_protected / v.points_evaluated) * 100).toFixed(1) + '%'
          : '—';
        const exceso = v.max_excess_m != null ? ` | exceso max: +${v.max_excess_m.toFixed(2)} m` : '';
        txt += `  ${v.equipment_name}: ${v.fully_shielded ? 'PROTEGIDO' : 'SIN PROTECCION'} (${pct} cobertura${exceso})\n`;
      });
    }
    const recs = ar._recs || [];
    if (recs.length > 0) {
      txt += `\nRecomendaciones correctivas:\n`;
      recs.forEach((r, i) => { txt += `  [${i+1}] ${r.title}\n`; });
    }
  } else {
    txt += `Sin cálculo de apantallamiento registrado en esta sesión.\n`;
  }
  txt += `\n`;
  txt += `--- MALLA A TIERRA ---\nEn espera de cálculo (backend Python).\n\n`;
  txt += `=== FIN DEL REPORTE ===\n`;

  const blob = new Blob([txt], { type: 'text/plain;charset=utf-8' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = (AppState.config.filename || 'TerraShield') + '.txt';
  a.click();
  URL.revokeObjectURL(url);
  showToast('Reporte TXT exportado', 'success');
}

/* =============================================
   CONFIGURATION
   ============================================= */
function setTheme(theme) {
  AppState.config.theme = theme;
  if (theme === 'dark') {
    document.body.classList.add('dark-theme');
    document.getElementById('theme-dark-btn').classList.add('active');
    document.getElementById('theme-light-btn').classList.remove('active');
  } else {
    document.body.classList.remove('dark-theme');
    document.getElementById('theme-light-btn').classList.add('active');
    document.getElementById('theme-dark-btn').classList.remove('active');
  }
}

function toggleDecSep(btn, sep) {
  btn.closest('.toggle-group').querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  AppState.config.decimalSep = sep;
}

function toggleExportFmt(btn, fmt) {
  btn.closest('.toggle-group').querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  AppState.config.exportFormat = fmt;
}

function saveConfig() {
  AppState.config.decimals = parseInt(document.getElementById('cfg-decimals').value) || 4;
  AppState.config.filename = document.getElementById('cfg-filename').value || 'TerraShield_Reporte';
  closeModal('modal-config');
  showToast('Configuración guardada', 'success');
}

function resetConfig() {
  document.getElementById('cfg-decimals').value = 4;
  document.getElementById('cfg-filename').value = 'TerraShield_Reporte';
  setTheme('light');
  showToast('Configuración restablecida', 'info');
}

/* =============================================
   TOAST NOTIFICATIONS
   ============================================= */
function showToast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast     = document.createElement('div');
  toast.className = `toast ${type === 'success' ? 'success' : type === 'error' ? 'error' : ''}`;

  let icon = '';
  if (type === 'success')
    icon = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>`;
  else if (type === 'error')
    icon = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`;
  else
    icon = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;

  toast.innerHTML = `${icon} <span>${msg}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity   = '0';
    toast.style.transform = 'translateY(16px)';
    toast.style.transition = 'opacity 0.3s, transform 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

/* =============================================
   KEYBOARD SHORTCUTS
   ============================================= */
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
  }
});