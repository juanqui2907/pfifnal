# -*- coding: utf-8 -*-
"""
TerraShield — modelo_shielding_v2.py

Envuelve notebook__shielding.py como motor de cálculo callable.
Expone run_shielding_model_ui() con la misma firma que el modelo legacy
(modelo_apantallamiento_ui_extraido).
"""

import os
import sys
import io
import re
import types
import builtins

_NOTEBOOK_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'notebook__shielding.py'
)

# Código compilado del notebook — se construye una sola vez por proceso
_COMPILED_CODE      = None
_COMPILED_CODE_MTIME = None   # mtime del notebook al compilar


# ─── No-op universal ──────────────────────────────────────────────────────────

def _noop(*a, **kw):
    return None


class _NoOpObj:
    """Objeto que absorbe cualquier llamada o acceso sin hacer nada."""
    def __call__(self, *a, **kw):   return _NoOpObj()
    def __getattr__(self, name):    return _NoOpObj()
    def __setattr__(self, n, v):    pass
    def __iter__(self):             return iter([])
    def __bool__(self):             return False
    def __len__(self):              return 0
    def __enter__(self):            return self
    def __exit__(self, *a):         return False


# ─── Mock de matplotlib ───────────────────────────────────────────────────────

class _NoOpAxes(_NoOpObj):
    pass


class _PltMock(types.ModuleType):
    def __init__(self):
        super().__init__('matplotlib.pyplot')

    def subplots(self, *a, **kw):
        return _NoOpObj(), _NoOpAxes()

    def figure(self, *a, **kw):
        return _NoOpObj()

    def show(self, *a, **kw):      pass
    def tight_layout(self, *a, **kw): pass
    def savefig(self, *a, **kw):   pass
    def close(self, *a, **kw):     pass

    def __getattr__(self, name):
        return _noop


_plt_mock = _PltMock()

# Force non-interactive backend so real matplotlib never tries to open a window
try:
    import matplotlib
    matplotlib.use('Agg')
except Exception:
    pass


# ─── Mocks de IPython e ipywidgets ────────────────────────────────────────────

def _make_ipython_mock():
    ip   = types.ModuleType('IPython')
    disp = types.ModuleType('IPython.display')
    disp.display      = _noop
    disp.HTML         = _noop
    disp.clear_output = _noop
    ip.display        = disp
    ip.get_ipython    = lambda: None
    # Matplotlib consulta version_info cuando detecta IPython.
    ip.version_info   = (9, 0, 0)
    return ip, disp


def _make_widgets_mock():
    w = types.ModuleType('ipywidgets')

    class _W(_NoOpObj):
        def __init__(self, *a, **kw):
            self.value   = kw.get('value', ())
            self.options = kw.get('options', [])
        def on_click(self, *a, **kw): pass
        def observe(self, *a, **kw):  pass

    for cls_name in [
        'SelectMultiple', 'Button', 'Output', 'HTML',
        'VBox', 'HBox', 'Layout', 'Checkbox',
        'IntSlider', 'FloatSlider', 'Text', 'Dropdown',
        'BoundedIntText',
    ]:
        setattr(w, cls_name, type(cls_name, (_W,), {}))

    return w


# ─── Preprocesador del notebook ───────────────────────────────────────────────

# Variables de figura final — NO se envuelven en try/except
_FINAL_FIG_NAMES = frozenset({
    'fig_superficies_mmq_mmm',
    'fig_superficies_mmq_mmm_3B',
    'fig_fase6_verificacion',
    'fig_superficies_mmq_mmm_con_equipos',
})


def _preprocess_notebook(code: str) -> str:
    """
    1. Elimina las asignaciones de entradas de ejemplo en las primeras ~200
       líneas (mast_inputs, cube_inputs, BIL, Zs, k, Is, S).
    2. Suprime todas las llamadas *.show().
    3. Envuelve en try/except las llamadas a funciones de figura diagnóstica
       (fig_N = plot_*(...) / fig_* = build_*(...)) que no son el resultado
       final, para que un fallo en FASE 4 no detenga FASE 6.
    """
    lines = code.split('\n')
    out   = []
    i     = 0
    n     = len(lines)

    # Patrón: línea a columna 0 que asigna una figura diagnóstica
    _diag_pat = re.compile(r'^(fig_\w+)\s*=\s*(plot_|build_)\w*\s*\(')

    while i < n:
        line     = lines[i]
        stripped = line.strip()

        # ── Neutralizar asignaciones de entrada en las primeras ~200 líneas ──
        if i < 200 and not stripped.startswith('#') and not stripped.startswith('"""'):

            # Listas multi-línea: mast_inputs = [...] / cube_inputs = [...]
            if re.match(r'^(mast_inputs|cube_inputs)\s*=\s*\[', stripped):
                depth = 0
                while i < n:
                    for ch in lines[i]:
                        if ch == '[':  depth += 1
                        elif ch == ']': depth -= 1
                    out.append('')
                    if depth <= 0:
                        break
                    i += 1
                i += 1
                continue

            # Escalares: BIL = ..., Zs = ..., k = ..., Is = ..., S = ...
            if re.match(r'^(BIL|Zs|k|Is|S)\s*=\s*\S', stripped):
                out.append('')
                i += 1
                continue

            # print() sobre S / radio de esfera
            if re.match(r'^print\(', stripped):
                out.append('')
                i += 1
                continue

        # ── Suprimir cualquier llamada .show() ────────────────────────────────
        if stripped.endswith('.show()') and not stripped.startswith('#'):
            indent = len(line) - len(line.lstrip())
            out.append(' ' * indent + 'pass  # .show() suppressed')
            i += 1
            continue

        # ── Neutralizar constantes visuales de equipos (se inyectan desde ns) ──
        if re.match(r'^(FASE6_EQUIPMENT_MESH_COLOR|FASE6_EQUIPMENT_MESH_OPACITY)\s*=', stripped):
            out.append('')
            i += 1
            continue

        # ── Envolver figuras diagnósticas en try/except ───────────────────────
        # Solo líneas a columna 0 (módulo-level) que no sean figuras finales
        diag_m = _diag_pat.match(line)
        if diag_m and diag_m.group(1) not in _FINAL_FIG_NAMES:
            fig_var = diag_m.group(1)
            # Recoger el bloque multi-línea completo (hasta cerrar el paréntesis)
            block = [line]
            depth = line.count('(') - line.count(')')
            j = i + 1
            while depth > 0 and j < n:
                block.append(lines[j])
                depth += lines[j].count('(') - lines[j].count(')')
                j += 1
            out.append('try:')
            for bl in block:
                out.append('    ' + bl)
            out.append('except Exception:')
            out.append(f'    {fig_var} = None')
            i = j
            continue

        out.append(line)
        i += 1

    return '\n'.join(out)


def _get_compiled_code():
    """Devuelve el código compilado del notebook; recompila si el archivo cambió."""
    global _COMPILED_CODE, _COMPILED_CODE_MTIME
    current_mtime = os.path.getmtime(_NOTEBOOK_PATH)
    if _COMPILED_CODE is None or current_mtime != _COMPILED_CODE_MTIME:
        with open(_NOTEBOOK_PATH, 'r', encoding='utf-8') as fh:
            raw = fh.read()
        processed          = _preprocess_notebook(raw)
        _COMPILED_CODE     = compile(processed, _NOTEBOOK_PATH, 'exec')
        _COMPILED_CODE_MTIME = current_mtime
    return _COMPILED_CODE


# ─── Formateador de verificación ──────────────────────────────────────────────

def _format_verification(records: list) -> list:
    """
    Convierte los registros de FASE 6 al formato que espera la API REST de
    TerraShield. Mantiene compatibilidad con registros antiguos y con la nueva
    verificación volumétrica por nube de puntos.
    """
    out = []
    for rec in records or []:
        cube = rec.get('cube', {}) or {}

        # Compatibilidad: la FASE 6 volumétrica puede entregar porcentajes con
        # nombres nuevos; la interfaz sigue consumiendo conteos de puntos.
        protected = int(rec.get('protected_count', rec.get('protected_points', 0)) or 0)
        total = int(rec.get('total_count', rec.get('total_points', 0)) or 0)

        if total <= 0 and 'protected_percentage' in rec:
            total = int(rec.get('total_points', 0) or 0)
            protected = int(round(total * float(rec.get('protected_percentage', 0.0)) / 100.0))

        pct = (protected / total * 100.0) if total > 0 else float(rec.get('protected_percentage', 0.0) or 0.0)
        is_ok = bool(rec.get('is_ok', pct >= 100.0 - 1e-9))

        min_margin = rec.get('min_margin')
        unprotected = rec.get('unprotected_points', []) or []

        max_excess = None
        if not is_ok and min_margin is not None:
            try:
                max_excess = abs(float(min_margin))
            except Exception:
                max_excess = None

        critical_pts = []
        for p in unprotected:
            try:
                critical_pts.append({
                    'x': float(p['x']),
                    'y': float(p['y']),
                    'z': float(p.get('z', p.get('z_equipment'))),
                })
            except Exception:
                continue

        out.append({
            'equipment_name':               cube.get('name') or rec.get('equipment_name', 'Equipo'),
            'fully_shielded':               is_ok,
            'points_evaluated':             total,
            'points_protected':             protected,
            'points_not_protected':         max(0, total - protected),
            'points_without_interpolation': int(rec.get('points_without_layer_xy', rec.get('points_without_interpolation', 0)) or 0),
            'max_excess_m':                 max_excess,
            'shielded_pct':                 pct,
            'status_text':  'Apantallado' if is_ok else 'No completamente protegido',
            'critical_points':              critical_pts,
        })
    return out


# Caché de la superficie calculada — persiste entre reloads de calculos_apant
_shield_cache = None  # dict con 'triangles', 'spatial_index', 'functions'


# ─── Punto de entrada principal ───────────────────────────────────────────────

def run_shielding_model_ui(
    mast_inputs,
    cube_inputs=None,
    *,
    BIL=350,
    Zs=300,
    k=1.2,
    S=None,
    guard_wire_pairs=None,
    verification_margin=0.0,
    verification_sample_n=15,
    include_bottom=False,
    show_final=False,
    final_grid_n=80,
    mmq_patch_n=40,
    mmm_patch_n=40,
    return_raw=False,
    suppress_output=True,
    namespace_overrides=None,
):
    # ── Normalizar entradas ────────────────────────────────────────────────────
    mast_inputs_clean = [(float(x), float(y), float(h)) for x, y, h in mast_inputs]
    cube_inputs_clean = [dict(c) for c in (cube_inputs or [])]
    pairs_clean = [
        tuple(sorted((int(a), int(b))))
        for a, b in (guard_wire_pairs or [])
    ]

    BIL_f = float(BIL)
    Zs_f  = float(Zs)
    k_f   = float(k)
    Is_f  = (2.2 * BIL_f) / Zs_f
    S_f   = float(S) if S is not None else k_f * 8.0 * Is_f ** 0.65

    guard_wire_inputs_list = [
        {'i': i, 'j': j, 'label_i': f'M{i}', 'label_j': f'M{j}'}
        for i, j in pairs_clean
    ]

    # ── Namespace de ejecución (los inputs anulan los del notebook) ────────────
    ns = {
        '__name__':          '__shielding_v2__',
        '__builtins__':      builtins,
        'mast_inputs':       mast_inputs_clean,
        'cube_inputs':       cube_inputs_clean,
        'BIL':               BIL_f,
        'Zs':                Zs_f,
        'k':                 k_f,
        'S':                 S_f,
        'guard_wire_pairs':  pairs_clean,
        'guard_wire_inputs': guard_wire_inputs_list,
        # Forzar modo sin widgets para evitar código de UI interactivo
        'WIDGETS_AVAILABLE': False,
        # Visual de equipos: sólido por defecto (se sobreescribe por cubo abajo)
        'FASE6_EQUIPMENT_MESH_COLOR':   'rgba(70,130,180,1.0)',
        'FASE6_EQUIPMENT_MESH_OPACITY': 0.80,
    }

    # Inyectar overrides opcionales (p.ej. para reducir resolución en _quick_verify)
    if namespace_overrides:
        ns.update(namespace_overrides)

    # ── Inyectar mocks de módulos con efectos secundarios ─────────────────────
    ip_mod, ip_disp = _make_ipython_mock()
    wg_mod          = _make_widgets_mock()

    mocks = {
        'IPython':           ip_mod,
        'IPython.display':   ip_disp,
        'ipywidgets':        wg_mod,
        'matplotlib.pyplot': _plt_mock,
    }
    originals = {k: sys.modules.get(k) for k in mocks}
    for k, v in mocks.items():
        sys.modules[k] = v

    # Inyectar en el namespace para cuando el notebook hace
    # "from IPython.display import display"
    ns['display']      = _noop
    ns['clear_output'] = _noop

    # ── Silenciar salida estándar durante la ejecución ─────────────────────────
    if suppress_output:
        _old_out, _old_err = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = io.StringIO()

    try:
        code_obj = _get_compiled_code()
        exec(code_obj, ns)

    finally:
        if suppress_output:
            sys.stdout, sys.stderr = _old_out, _old_err
        # Restaurar módulos reales
        for k, orig in originals.items():
            if orig is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = orig

    # ── Cachear superficie para verificación rápida posterior ─────────────────
    global _shield_cache
    try:
        _shield_cache = {
            # Nueva FASE 6 volumétrica: interpoladores directos de capa.
            'surface_interpolators': ns.get('fase6_surface_interpolators', []),
            'fn_build_cloud':        ns.get('fase6_build_equipment_point_cloud'),
            'fn_verify_cloud':       ns.get('fase6_verify_equipment_cloud'),
            'point_spacing':         ns.get('FASE6_POINT_SPACING', 0.25),
            'z_tol':                 ns.get('FASE6_Z_TOL', 1e-6),

            # Compatibilidad con la verificación anterior.
            'triangles':     ns.get('fase6_shield_triangles', []),
            'spatial_index': ns.get('fase6_spatial_index'),
            'fn_normalize':  ns.get('normalize_cube_record_fase6'),
            'fn_verify':     ns.get('verify_cube_shielding_fase6'),
            'ok_threshold':  ns.get('FASE6_OK_PERCENT_THRESHOLD', 100.0),
        }
    except Exception:
        _shield_cache = None

    # ── Extraer resultados ─────────────────────────────────────────────────────
    fig = (
        ns.get('fig_superficies_mmq_mmm_con_equipos')
        or ns.get('fig_fase6_verificacion')
        or ns.get('fig_superficies_mmq_mmm')
    )
    S_used  = float(ns.get('S', S_f))
    records = ns.get('fase6_verification_records', [])

    # ── Aplicar color propio de cada cubo en la figura ────────────────────────
    if fig is not None and cube_inputs_clean:
        _cube_colors = [
            (c['name'], c.get('color', 'rgba(70,130,180,1.0)'))
            for c in cube_inputs_clean
        ]
        try:
            for trace in fig.data:
                if getattr(trace, 'type', None) != 'mesh3d':
                    continue
                trace_name = getattr(trace, 'name', '') or ''
                for cube_name, cube_color in _cube_colors:
                    if trace_name == cube_name or trace_name.startswith(cube_name + ' |'):
                        trace.color   = cube_color
                        trace.opacity = 0.80
                        break
        except Exception:
            pass

    fig_json = None
    if fig is not None:
        try:
            fig_json = fig.to_json()
        except Exception:
            pass

    return {
        'fig_json':     fig_json,
        'S':            S_used,
        'verification': _format_verification(records),
    }


def _clamp_bary_z(px, py, tri):
    """
    Devuelve (z_clamped, dist2_xy) donde:
      - z_clamped es la altura del triángulo en el punto más cercano de su
        superficie 2-D al punto (px, py).  Se obtiene proyectando (px,py) al
        triángulo via baricéntricas recortadas a [0,1] y renormalizadas.
      - dist2_xy  es la distancia cuadrada en XY desde (px,py) hasta ese
        punto más cercano en el triángulo.
    """
    A, B, C = tri['A'], tri['B'], tri['C']
    v0 = (B[0]-A[0], B[1]-A[1])
    v1 = (C[0]-A[0], C[1]-A[1])
    v2 = (px-A[0],   py-A[1])
    den = v0[0]*v1[1] - v1[0]*v0[1]
    if abs(den) <= 1e-14:
        # Triángulo degenerado: retroceder al vértice más cercano
        best_d2 = float('inf')
        best_z  = A[2]
        for vx, vy, vz in (A, B, C):
            d2 = (px-vx)**2 + (py-vy)**2
            if d2 < best_d2:
                best_d2, best_z = d2, vz
        return best_z, best_d2

    u = (v2[0]*v1[1] - v1[0]*v2[1]) / den
    v = (v0[0]*v2[1] - v2[0]*v0[1]) / den
    w = 1.0 - u - v
    # Recortar y renormalizar → punto más cercano dentro del triángulo
    u = max(0.0, u)
    v = max(0.0, v)
    w = max(0.0, w)
    s = u + v + w
    if s < 1e-14:
        return A[2], (px-A[0])**2 + (py-A[1])**2
    u /= s; v /= s; w /= s
    qx = u*B[0] + v*C[0] + w*A[0]
    qy = u*B[1] + v*C[1] + w*A[1]
    qz = u*B[2] + v*C[2] + w*A[2]
    dist2 = (px-qx)**2 + (py-qy)**2
    return qz, dist2


def _query_shield_robust(px, py, triangles, spatial_index, search_radius=6):
    """
    Consulta la altura de la superficie de apantallamiento en (px, py).

    Estrategia en dos fases:
    1. Búsqueda exacta (baricéntrica): expande hasta search_radius celdas del
       índice espacial 2-D.  Si algún triángulo contiene (px,py) se devuelve
       la z interpolada máxima.
    2. Aproximación por triángulo más cercano: si no hay triángulo que
       contenga el punto exactamente (brecha entre parches), se busca el
       triángulo cuyo borde 2-D más cercano está más próximo a (px,py) y se
       devuelve la altura de ese punto más cercano.  Esto cubre correctamente
       las costuras entre superficies sin declararlos "no apantallados".
    """
    # ── Caso sin índice: recorrer todos los triángulos ────────────────────────
    if spatial_index is None:
        z_exact   = None
        best_d2   = float('inf')
        best_fall = None
        for tri in triangles:
            A, B, C = tri['A'], tri['B'], tri['C']
            v0 = (B[0]-A[0], B[1]-A[1])
            v1 = (C[0]-A[0], C[1]-A[1])
            v2 = (px-A[0],   py-A[1])
            den = v0[0]*v1[1] - v1[0]*v0[1]
            if abs(den) > 1e-14:
                u = (v2[0]*v1[1] - v1[0]*v2[1]) / den
                v = (v0[0]*v2[1] - v2[0]*v0[1]) / den
                ww = 1.0 - u - v
                if u >= -1e-9 and v >= -1e-9 and ww >= -1e-9:
                    z = ww*A[2] + u*B[2] + v*C[2]
                    if z_exact is None or z > z_exact:
                        z_exact = z
            qz, d2 = _clamp_bary_z(px, py, tri)
            if d2 < best_d2:
                best_d2, best_fall = d2, qz
        return z_exact if z_exact is not None else best_fall

    xmin   = spatial_index['xmin']
    xmax   = spatial_index['xmax']
    ymin   = spatial_index['ymin']
    ymax   = spatial_index['ymax']
    n_bins = spatial_index['n_bins']
    grid   = spatial_index['grid']

    def to_ix(x):
        return int(max(0, min(n_bins-1, (x - xmin) / (xmax - xmin) * n_bins)))
    def to_iy(y):
        return int(max(0, min(n_bins-1, (y - ymin) / (ymax - ymin) * n_bins)))

    # Anclar al índice aunque el punto esté ligeramente fuera de los límites
    cx = to_ix(max(xmin, min(xmax, px)))
    cy = to_iy(max(ymin, min(ymax, py)))

    def _eval_exact(candidate_ids):
        """Devuelve z exacta (baricéntrica) o None si el punto no está en ningún triángulo."""
        z_best = None
        for idx in candidate_ids:
            tri = triangles[idx]
            A, B, C = tri['A'], tri['B'], tri['C']
            v0 = (B[0]-A[0], B[1]-A[1])
            v1 = (C[0]-A[0], C[1]-A[1])
            v2 = (px-A[0],   py-A[1])
            den = v0[0]*v1[1] - v1[0]*v0[1]
            if abs(den) <= 1e-14:
                continue
            u = (v2[0]*v1[1] - v1[0]*v2[1]) / den
            v = (v0[0]*v2[1] - v2[0]*v0[1]) / den
            ww = 1.0 - u - v
            if u >= -1e-9 and v >= -1e-9 and ww >= -1e-9:
                z = ww*A[2] + u*B[2] + v*C[2]
                if z_best is None or z > z_best:
                    z_best = z
        return z_best

    def _maxz_fallback(candidate_ids):
        """
        Devuelve la MAXIMA z proyectada sobre los triangulos candidatos.
        Uso: cuando el punto cae en una brecha entre parches, la mayor z
        de los triangulos cercanos representa el techo del domo sobre ese punto.
        NO usar la z del triangulo mas cercano (podria ser un triangulo de la
        base/borde del domo con z~0 que esta cerca en XY pero debajo del punto).
        """
        best_z = None
        for idx in candidate_ids:
            qz, _ = _clamp_bary_z(px, py, triangles[idx])
            if best_z is None or qz > best_z:
                best_z = qz
        return best_z

    # Acumular candidatos expandiendo el radio hasta search_radius
    all_candidates = set()
    z_exact = None

    for r in range(0, search_radius + 1):
        if r == 0:
            new_cells = [(cx, cy)]
        else:
            new_cells = []
            for dix in range(-r, r + 1):
                for diy in range(-r, r + 1):
                    if abs(dix) == r or abs(diy) == r:
                        new_cells.append((
                            max(0, min(n_bins-1, cx + dix)),
                            max(0, min(n_bins-1, cy + diy)),
                        ))

        new_ids = set()
        for cell in new_cells:
            new_ids.update(grid.get(cell, []))
        all_candidates |= new_ids

        if all_candidates:
            z_exact = _eval_exact(all_candidates)
            if z_exact is not None:
                return z_exact          # Coincidencia exacta → retornar

    # ── Fase 2: máxima z proyectada sobre candidatos ──────────────────────────
    # El punto cae en una brecha entre parches.
    # La mayor z entre todos los triángulos candidatos cercanos representa
    # el techo del domo sobre ese punto (los triángulos de base/borde con z~0
    # son ignorados al tomar el máximo).
    if all_candidates:
        return _maxz_fallback(all_candidates)

    # Último recurso: ningún candidato en el radio → máximo global (raro).
    best_z = None
    for tri in triangles:
        qz, _ = _clamp_bary_z(px, py, tri)
        if best_z is None or qz > best_z:
            best_z = qz
    return best_z


def _verify_cube_robust(cube, triangles, spatial_index, ok_threshold=100.0, vertical_tol=0.0):
    """
    Verifica un cubo contra la superficie de apantallamiento usando una
    grilla volumétrica 3-D uniforme.

    Para cada punto (px, py, pz) de la grilla interior se consulta la
    altura del escudo z_shield(px, py) y se verifica si pz <= z_shield.
    El porcentaje resultante es la fracción del VOLUMEN del equipo que
    queda bajo la capa de apantallamiento, independientemente de la forma
    curva de dicha capa.
    """
    import numpy as np

    x0, x1 = cube['x0'], cube['x1']
    y0, y1 = cube['y0'], cube['y1']
    z0, z1 = cube['z0'], cube['z1']

    # Grilla 3-D: 15×15×10 = 2250 puntos interiores
    # Suficiente resolución para capturar la intersección de la capa curva
    # con el volumen del equipo sin ser excesivamente lento.
    NX, NY, NZ = 15, 15, 10

    protected_count = 0
    total_count     = 0
    protected_pts   = []
    unprotected_pts = []
    min_margin      = None
    max_margin      = None

    for px in np.linspace(x0, x1, NX):
        for py in np.linspace(y0, y1, NY):
            # Una sola consulta por columna (px, py): reutilizar z_shield
            # para todos los NZ niveles verticales de esa columna.
            z_shield = _query_shield_robust(float(px), float(py),
                                            triangles, spatial_index)
            for pz in np.linspace(z0, z1, NZ):
                total_count += 1
                pz_f = float(pz)
                if z_shield is None:
                    is_ok  = False
                    margin = None
                else:
                    margin = float(z_shield - pz_f)
                    is_ok  = pz_f <= z_shield + vertical_tol
                    min_margin = margin if min_margin is None else min(min_margin, margin)
                    max_margin = margin if max_margin is None else max(max_margin, margin)

                if is_ok:
                    protected_count += 1
                    protected_pts.append({'x': float(px), 'y': float(py), 'z': pz_f})
                else:
                    unprotected_pts.append({'x': float(px), 'y': float(py), 'z': pz_f})

    percent_area = 100.0 * protected_count / total_count if total_count > 0 else 0.0
    is_ok        = percent_area >= ok_threshold

    return {
        'cube':               cube,
        'is_ok':              is_ok,
        'percent_area':       percent_area,
        'protected_count':    protected_count,
        'total_count':        total_count,
        'protected_weight':   float(protected_count),
        'total_weight':       float(total_count),
        'min_margin':         min_margin,
        'protected_points':   protected_pts,
        'unprotected_points': unprotected_pts,
    }


def _legacy_record_from_cloud_result(cube_dict, summary, point_rows, max_points=1200):
    """
    Adapta el resultado de la FASE 6 volumétrica al formato interno heredado
    para no tocar la lógica de recomendaciones ni el frontend existente.
    """
    import numpy as _np

    protected = _np.asarray(point_rows['protected'], dtype=bool)
    unprotected = ~protected
    z_layer = _np.asarray(point_rows['z_layer'], dtype=float)
    z_eq = _np.asarray(point_rows['z_equipment'], dtype=float)
    margin = z_layer - z_eq
    finite_margin = margin[_np.isfinite(margin)]

    min_margin = float(_np.min(finite_margin)) if finite_margin.size else None
    max_margin = float(_np.max(finite_margin)) if finite_margin.size else None

    def _sample_indices(mask, limit):
        idx = _np.where(mask)[0]
        if limit is not None and len(idx) > limit:
            # Muestreo determinístico para evitar respuestas JSON excesivas.
            step = max(1, int(_np.ceil(len(idx) / float(limit))))
            idx = idx[::step][:limit]
        return idx

    def _float_or_none(v):
        try:
            vf = float(v)
            return vf if _np.isfinite(vf) else None
        except Exception:
            return None

    def _points(mask):
        pts = []
        for ii in _sample_indices(mask, max_points):
            pts.append({
                'x': float(point_rows['x'][ii]),
                'y': float(point_rows['y'][ii]),
                'z': float(point_rows['z_equipment'][ii]),
                'z_shield': _float_or_none(point_rows['z_layer'][ii]),
                'margin': _float_or_none(margin[ii]),
                'protected': bool(point_rows['protected'][ii]),
            })
        return pts

    total = int(summary.get('total_points', len(protected)))
    n_ok = int(summary.get('protected_points', int(_np.count_nonzero(protected))))
    pct = float(summary.get('protected_percentage', (100.0 * n_ok / total if total else 0.0)))

    return {
        'cube': {
            'name': cube_dict.get('name', summary.get('equipment_name', 'Equipo')),
            'x0': float(cube_dict['x']),
            'x1': float(cube_dict['x']) + float(cube_dict['dx']),
            'y0': float(cube_dict['y']),
            'y1': float(cube_dict['y']) + float(cube_dict['dy']),
            'z0': float(cube_dict.get('z', 0.0)),
            'z1': float(cube_dict.get('z', 0.0)) + float(cube_dict['dz']),
            'dx': float(cube_dict['dx']),
            'dy': float(cube_dict['dy']),
            'dz': float(cube_dict['dz']),
        },
        'is_ok': bool(pct >= 100.0 - 1e-9),
        'percent_area': pct,
        'percent_points': pct,
        'protected_count': n_ok,
        'total_count': total,
        'protected_weight': float(n_ok),
        'total_weight': float(total),
        'min_margin': min_margin,
        'max_margin': max_margin,
        'points_without_layer_xy': int(summary.get('points_without_layer_xy', 0) or 0),
        'protected_points': _points(protected),
        'unprotected_points': _points(unprotected),
        'face_percentages': {},
    }


def verify_equipos_rapido(cubes_raw):
    global _shield_cache
    if not _shield_cache:
        raise RuntimeError('No hay superficie de apantallamiento calculada. Calcule primero.')

    # Preferir la nueva verificación volumétrica de FASE 6.
    surface_interpolators = _shield_cache.get('surface_interpolators') or []
    fn_build_cloud = _shield_cache.get('fn_build_cloud')
    fn_verify_cloud = _shield_cache.get('fn_verify_cloud')

    if surface_interpolators and callable(fn_build_cloud) and callable(fn_verify_cloud):
        records = []
        spacing = float(_shield_cache.get('point_spacing', 0.25) or 0.25)
        z_tol = float(_shield_cache.get('z_tol', 1e-6) or 1e-6)

        for i, c in enumerate(cubes_raw):
            cube_dict = {
                'name': c.get('name', 'Equipo ' + str(i + 1)),
                'x':    float(c['x']),
                'y':    float(c['y']),
                'z':    float(c.get('z', 0.0)),
                'dx':   float(c['dx']),
                'dy':   float(c['dy']),
                'dz':   float(c['dz']),
            }
            cloud = fn_build_cloud(cube_dict, spacing=spacing)
            summary, point_rows = fn_verify_cloud(
                equipment_cloud=cloud,
                surface_interpolators=surface_interpolators,
                z_tol=z_tol,
            )
            records.append(_legacy_record_from_cloud_result(cube_dict, summary, point_rows))

        return _format_verification(records)

    # Compatibilidad con el método anterior, por si se ejecuta un notebook viejo.
    triangles = _shield_cache.get('triangles') or []
    if not triangles:
        raise RuntimeError('No hay superficie de apantallamiento calculada. Calcule primero.')

    spatial_index = _shield_cache.get('spatial_index')
    fn_normalize = _shield_cache.get('fn_normalize')
    ok_threshold = _shield_cache.get('ok_threshold', 100.0)

    if fn_normalize is None:
        raise RuntimeError('Funciones de normalizacion no disponibles en el cache.')

    records = []
    for i, c in enumerate(cubes_raw):
        cube_dict = {
            'name': c.get('name', 'Equipo ' + str(i + 1)),
            'x':    float(c['x']),
            'y':    float(c['y']),
            'z':    float(c.get('z', 0.0)),
            'dx':   float(c['dx']),
            'dy':   float(c['dy']),
            'dz':   float(c['dz']),
        }
        cube = fn_normalize(cube_dict, i)
        record = _verify_cube_robust(cube, triangles, spatial_index, ok_threshold)
        records.append(record)

    return _format_verification(records)
