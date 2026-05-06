"""
TerraShield — wrapper del modelo de apantallamiento.
Carga dinamicamente el modulo de HOLA (nombre con espacio) y
expone calcular_apantallamiento() y calcular_recomendaciones()
para los endpoints Flask.
"""
import os
import sys
import types
import importlib.util
import numpy as np

_BASE       = os.path.dirname(os.path.abspath(__file__))
_MODEL_FILE = os.path.join(_BASE, 'apantallamiento_3d', 'modelo_apantallamiento_ui_extraido (1).py')


def _mock_ipython():
    """Evita ImportError de IPython fuera de entornos Jupyter."""
    ip = types.ModuleType('IPython')
    ip.display = types.ModuleType('IPython.display')
    ip.display.display       = lambda *a, **kw: None
    ip.display.HTML          = lambda *a, **kw: None
    ip.display.clear_output  = lambda *a, **kw: None
    ip.get_ipython           = lambda: None
    sys.modules.setdefault('IPython',         ip)
    sys.modules.setdefault('IPython.display', ip.display)


def _get_model():
    _mock_ipython()
    spec = importlib.util.spec_from_file_location('modelo_apant', _MODEL_FILE)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _build_run_kwargs(params, mod=None, low_res=False):
    """Construye kwargs para run_shielding_model_ui desde un dict de params."""
    mast_inputs = [
        (float(m['x']), float(m['y']), float(m['h']))
        for m in params.get('masts', [])
    ]
    cubes = params.get('cubes') or []
    cube_inputs = [
        {
            'name':  c.get('name', f'Equipo {i + 1}'),
            'x':  float(c['x']),  'y':  float(c['y']),  'z':  float(c['z']),
            'dx': float(c['dx']), 'dy': float(c['dy']), 'dz': float(c['dz']),
            'color': c.get('color', 'rgba(245,196,0,0.35)'),
        }
        for i, c in enumerate(cubes)
    ] or None

    raw_pairs = params.get('guard_wire_pairs') or []
    guard_wire_pairs = [tuple(int(x) for x in p) for p in raw_pairs] or None

    grid_n = 20 if low_res else int(params.get('final_grid_n', 80))
    patch  = 15 if low_res else 40
    samp_n = 8  if low_res else int(params.get('verification_sample_n', 15))

    return dict(
        mast_inputs          = mast_inputs,
        cube_inputs          = cube_inputs,
        BIL                  = float(params.get('BIL', 350)),
        Zs                   = float(params.get('Zs', 300)),
        k                    = float(params.get('k', 1.2)),
        S                    = float(params['S']) if params.get('S') else None,
        guard_wire_pairs     = guard_wire_pairs,
        verification_margin  = float(params.get('verification_margin', 0.0)),
        verification_sample_n= samp_n,
        include_bottom       = bool(params.get('include_bottom', False)),
        show_final           = False,
        final_grid_n         = grid_n,
        mmq_patch_n          = patch,
        mmm_patch_n          = patch,
        return_raw           = False,
    )


def calcular_apantallamiento(params: dict) -> dict:
    mod    = _get_model()
    kwargs = _build_run_kwargs(params)
    kwargs['show_final'] = False
    result = mod.run_shielding_model_ui(**kwargs)
    return {
        'fig_json':     result.get('fig_json'),
        'S':            result.get('S'),
        'verification': result.get('verification', []),
    }


# ─── Motor de recomendaciones ─────────────────────────────────────────────────

def _quick_verify(params: dict, mod) -> list:
    """Ejecuta el modelo en baja resolución y devuelve la lista de verificación."""
    kwargs = _build_run_kwargs(params, mod=mod, low_res=True)
    result = mod.run_shielding_model_ui(**kwargs)
    return result.get('verification', [])


def _recommend_add_mast(params: dict, critical_pts: list, S: float,
                        h_rec: float, mod) -> dict | None:
    """Propone un único mástil nuevo que cubra la mayor cantidad de puntos críticos."""
    if not critical_pts:
        return None

    crit_xy = np.array([[p['x'], p['y']] for p in critical_pts])
    crit_z  = np.array([p['z'] for p in critical_pts])

    # Radio efectivo desde un mástil de altura h_rec hacia cada punto crítico
    radii = []
    for z in crit_z:
        a_h = (max(2 * S * h_rec - h_rec ** 2, 0)) ** 0.5
        a_z = (max(2 * S * z   - z    ** 2, 0)) ** 0.5
        radii.append(max(a_h - a_z, 0.0))
    radii = np.array(radii)

    # Búsqueda en grilla 7×7 alrededor del centroide
    cx, cy   = crit_xy.mean(axis=0)
    span     = min(max(float(np.ptp(crit_xy, axis=0).max()), S * 0.5), S * 2.0)
    step     = max(span / 3.0, 1.0)

    best_coverage = -1
    best_xy       = (round(cx, 1), round(cy, 1))

    xs = np.arange(cx - span, cx + span + step * 0.5, step)
    ys = np.arange(cy - span, cy + span + step * 0.5, step)
    for gx in xs:
        for gy in ys:
            dist     = np.hypot(crit_xy[:, 0] - gx, crit_xy[:, 1] - gy)
            coverage = int(np.sum(dist <= radii))
            if coverage > best_coverage:
                best_coverage = coverage
                best_xy       = (gx, gy)

    new_x = round(float(best_xy[0]), 1)
    new_y = round(float(best_xy[1]), 1)
    new_idx = len(params.get('masts', []))

    test_params = dict(params)
    test_params['masts'] = list(params.get('masts', [])) + [
        {'x': new_x, 'y': new_y, 'h': h_rec}
    ]

    try:
        verif        = _quick_verify(test_params, mod)
        all_shielded = all(v.get('fully_shielded', False) for v in verif)
        n_ok         = sum(1 for v in verif if v.get('fully_shielded', False))
        n_total      = len(verif)
        validated    = True
    except Exception:
        all_shielded = False
        n_ok, n_total, validated = 0, len(params.get('cubes', [])), False

    return {
        'type':   'add_mast',
        'title':  f'Agregar mástil M{new_idx} en x = {new_x} m, y = {new_y} m, h = {h_rec} m',
        'reason': (
            f'Los puntos críticos no apantallados requieren cobertura adicional. '
            f'La posición propuesta maximiza la cobertura de {best_coverage}/{len(critical_pts)} '
            f'puntos críticos según el radio efectivo del EGM (S = {round(S,2)} m).'
        ),
        'actions': [
            {'action': 'add_mast', 'x': new_x, 'y': new_y, 'h': h_rec}
        ],
        'validation': {
            'predicted_fully_shielded': all_shielded,
            'equipment_coverage':       f'{n_ok}/{n_total} equipos protegidos',
            'notes': 'Propuesta evaluada con el modelo de esfera rodante.' if validated
                     else 'No se pudo verificar internamente.',
        },
    }


def _recommend_add_two_masts(params: dict, critical_pts: list, S: float,
                              h_rec: float, mod) -> dict | None:
    """Propone dos mástiles + cable de guarda a lo largo del eje principal de los puntos críticos."""
    if not critical_pts:
        return None

    crit_xy = np.array([[p['x'], p['y']] for p in critical_pts])
    cx, cy  = crit_xy.mean(axis=0)

    if len(crit_xy) >= 2:
        cov = np.cov(crit_xy.T)
        try:
            eigvals, eigvecs = np.linalg.eigh(cov if cov.ndim == 2 else np.eye(2))
            main_vec = eigvecs[:, np.argmax(eigvals)]
        except Exception:
            main_vec = np.array([1.0, 0.0])
        extent = max(np.linalg.norm(crit_xy - np.array([cx, cy]), axis=1).max(), S * 0.4)
        p1 = np.array([cx, cy]) - main_vec * (extent * 0.65)
        p2 = np.array([cx, cy]) + main_vec * (extent * 0.65)
    else:
        p1 = np.array([cx - S * 0.5, cy])
        p2 = np.array([cx + S * 0.5, cy])

    m1x, m1y = round(float(p1[0]), 1), round(float(p1[1]), 1)
    m2x, m2y = round(float(p2[0]), 1), round(float(p2[1]), 1)
    base_idx  = len(params.get('masts', []))

    test_params = dict(params)
    test_params['masts'] = list(params.get('masts', [])) + [
        {'x': m1x, 'y': m1y, 'h': h_rec},
        {'x': m2x, 'y': m2y, 'h': h_rec},
    ]
    test_params['guard_wire_pairs'] = list(params.get('guard_wire_pairs') or []) + [
        [base_idx, base_idx + 1]
    ]

    try:
        verif        = _quick_verify(test_params, mod)
        all_shielded = all(v.get('fully_shielded', False) for v in verif)
        n_ok         = sum(1 for v in verif if v.get('fully_shielded', False))
        n_total      = len(verif)
        validated    = True
    except Exception:
        all_shielded = False
        n_ok, n_total, validated = 0, len(params.get('cubes', [])), False

    return {
        'type':   'add_guard_wire',
        'title':  (f'Agregar mástiles M{base_idx} ({m1x},{m1y}) y M{base_idx+1} ({m2x},{m2y}) '
                   f'con cable de guarda entre ellos'),
        'reason': (
            'La distribución de puntos críticos sugiere cobertura lineal. '
            'Se proponen dos mástiles en los extremos del eje principal de exposición '
            'y un cable de guarda entre ellos para extender la envolvente de protección.'
        ),
        'actions': [
            {'action': 'add_mast',       'x': m1x, 'y': m1y, 'h': h_rec},
            {'action': 'add_mast',       'x': m2x, 'y': m2y, 'h': h_rec},
            {'action': 'add_guard_wire', 'from_new': 0, 'to_new': 1},
        ],
        'validation': {
            'predicted_fully_shielded': all_shielded,
            'equipment_coverage':       f'{n_ok}/{n_total} equipos protegidos',
            'notes': 'Propuesta evaluada con el modelo de esfera rodante.' if validated
                     else 'No se pudo verificar internamente.',
        },
    }


def _recommend_reduce_guard_spacing(params: dict, S: float,
                                    masts: list) -> dict | None:
    """Detecta cables de guarda con separación > 2S y recomienda una guarda intermedia."""
    guard_pairs = params.get('guard_wire_pairs') or []
    if len(guard_pairs) < 2 or len(masts) < 2:
        return None

    threshold = 2.0 * S
    worst     = None

    for i in range(len(guard_pairs)):
        for j in range(i + 1, len(guard_pairs)):
            ai, bi = guard_pairs[i]
            aj, bj = guard_pairs[j]
            if any(idx >= len(masts) for idx in [ai, bi, aj, bj]):
                continue
            mid_i = ((masts[ai]['x'] + masts[bi]['x']) / 2,
                     (masts[ai]['y'] + masts[bi]['y']) / 2)
            mid_j = ((masts[aj]['x'] + masts[bj]['x']) / 2,
                     (masts[aj]['y'] + masts[bj]['y']) / 2)
            dist  = float(np.hypot(mid_i[0] - mid_j[0], mid_i[1] - mid_j[1]))
            if dist > threshold:
                if worst is None or dist > worst['dist']:
                    worst = {'wire_a': i, 'wire_b': j, 'dist': round(dist, 2)}

    if worst is None:
        return None

    return {
        'type':   'reduce_spacing',
        'title':  (f'Reducir separación entre guardas G{worst["wire_a"]} '
                   f'y G{worst["wire_b"]} — separación actual ≈ {worst["dist"]} m'),
        'reason': (
            f'La separación entre cables de guarda G{worst["wire_a"]} y '
            f'G{worst["wire_b"]} es ≈ {worst["dist"]} m, que supera el límite '
            f'2S = {round(threshold, 2)} m. Esto puede crear zonas de '
            f'penetración entre las guardas.'
        ),
        'actions': [
            {
                'action': 'add_intermediate_guard',
                'note':   (f'Agregar guarda intermedia entre G{worst["wire_a"]} '
                           f'y G{worst["wire_b"]} a la línea media entre ambas.'),
            }
        ],
        'validation': {
            'predicted_fully_shielded': None,
            'equipment_coverage':       'No verificado automáticamente — requiere redefinición geométrica',
            'notes':                    (f'Reducir separación a ≤ {round(threshold, 2)} m '
                                         f'o agregar una guarda intermedia.'),
        },
    }


def calcular_recomendaciones(params: dict, S: float, verification: list) -> list:
    """
    Genera recomendaciones correctivas para equipos no apantallados.
    Cada propuesta se verifica internamente con el modelo EGM en baja resolución.
    """
    unshielded = [v for v in verification if not v.get('fully_shielded', True)]
    if not unshielded:
        return []

    all_critical = []
    for v in unshielded:
        all_critical.extend(v.get('critical_points', []))

    if not all_critical:
        return []

    masts = params.get('masts', [])
    h_rec = max((float(m['h']) for m in masts), default=15.0)
    mod   = _get_model()
    recs  = []

    # Recomendación A: un mástil
    rec_a = _recommend_add_mast(params, all_critical, S, h_rec, mod)
    if rec_a:
        recs.append(rec_a)

    # Recomendación B: dos mástiles + cable de guarda
    # Se genera siempre como alternativa, aunque A sea exitosa
    if len(all_critical) >= 1:
        rec_b = _recommend_add_two_masts(params, all_critical, S, h_rec, mod)
        if rec_b:
            recs.append(rec_b)

    # Recomendación C: reducir separación entre guardas
    rec_c = _recommend_reduce_guard_spacing(params, S, masts)
    if rec_c:
        recs.append(rec_c)

    return recs
