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
    Convierte fase6_verification_records del notebook al formato
    que espera la API REST de TerraShield.
    """
    out = []
    for rec in records:
        cube        = rec.get('cube', {})
        is_ok       = bool(rec.get('is_ok', False))
        protected   = int(rec.get('protected_count', 0))
        total       = int(rec.get('total_count', 0))
        min_margin  = rec.get('min_margin')
        unprotected = rec.get('unprotected_points', [])

        max_excess = None
        if not is_ok and min_margin is not None:
            max_excess = abs(float(min_margin))

        critical_pts = [
            {'x': float(p['x']), 'y': float(p['y']), 'z': float(p['z'])}
            for p in unprotected
        ]

        out.append({
            'equipment_name':               cube.get('name', 'Equipo'),
            'fully_shielded':               is_ok,
            'points_evaluated':             total,
            'points_protected':             protected,
            'points_not_protected':         total - protected,
            'points_without_interpolation': 0,
            'max_excess_m':                 max_excess,
            'status_text':  'Apantallado' if is_ok else 'No completamente protegido',
            'critical_points':              critical_pts,
        })
    return out


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
