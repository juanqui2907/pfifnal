# -*- coding: utf-8 -*-
"""
TerraShield — calculos_apant.py

Wrapper Flask para el módulo de apantallamiento.
Carga modelo_shielding_v2.py (basado en notebook__shielding.py) y
expone calcular_apantallamiento() y calcular_recomendaciones().
"""

import os
import sys
import math
import importlib.util
import numpy as np

_BASE      = os.path.dirname(os.path.abspath(__file__))
_V2_FILE   = os.path.join(_BASE, 'apantallamiento_3d', 'modelo_shielding_v2.py')
_V2_KEY    = 'modelo_shielding_v2'


def _get_model():
    """
    Carga modelo_shielding_v2 y lo cachea en sys.modules para que
    el código compilado del notebook persista entre reloads de este wrapper.
    """
    if _V2_KEY not in sys.modules:
        spec = importlib.util.spec_from_file_location(_V2_KEY, _V2_FILE)
        mod  = importlib.util.module_from_spec(spec)
        sys.modules[_V2_KEY] = mod   # registrar ANTES de exec (evita re-entrada)
        spec.loader.exec_module(mod)
    return sys.modules[_V2_KEY]


# ─── API principal ────────────────────────────────────────────────────────────

def calcular_apantallamiento(params: dict) -> dict:
    mast_inputs = [
        (float(m['x']), float(m['y']), float(m['h']))
        for m in params.get('masts', [])
    ]

    cubes_raw = params.get('cubes') or []
    cube_inputs = [
        {
            'name':  c.get('name', f'Equipo {i + 1}'),
            'x':     float(c['x']),
            'y':     float(c['y']),
            'z':     float(c['z']),
            'dx':    float(c['dx']),
            'dy':    float(c['dy']),
            'dz':    float(c['dz']),
            'color': c.get('color', 'rgba(245,196,0,0.35)'),
        }
        for i, c in enumerate(cubes_raw)
    ] or None

    raw_pairs   = params.get('guard_wire_pairs') or []
    guard_pairs = [tuple(int(x) for x in p) for p in raw_pairs] or None

    mod    = _get_model()
    result = mod.run_shielding_model_ui(
        mast_inputs          = mast_inputs,
        cube_inputs          = cube_inputs,
        BIL                  = float(params.get('BIL', 350)),
        Zs                   = float(params.get('Zs', 300)),
        k                    = float(params.get('k', 1.2)),
        S                    = float(params['S']) if params.get('S') else None,
        guard_wire_pairs     = guard_pairs,
        verification_margin  = float(params.get('verification_margin', 0.0)),
        verification_sample_n= int(params.get('verification_sample_n', 15)),
        include_bottom       = bool(params.get('include_bottom', False)),
        show_final           = False,
        final_grid_n         = int(params.get('final_grid_n', 80)),
        mmq_patch_n          = 40,
        mmm_patch_n          = 40,
        return_raw           = False,
    )

    return {
        'fig_json':     result.get('fig_json'),
        'S':            result.get('S'),
        'verification': result.get('verification', []),
    }


# ─── Helper interno de verificación rápida ───────────────────────────────────

def _quick_verify(params: dict, mod) -> dict:
    """
    Ejecuta el modelo en baja resolución para validar una configuración propuesta.
    Devuelve {'verification': [...], 'validated': bool, 'error': str|None}.
    Nunca lanza excepción: los fallos internos se devuelven con validated=False.
    """
    try:
        mast_inputs = [
            (float(m['x']), float(m['y']), float(m['h']))
            for m in params.get('masts', [])
        ]
        cubes_raw   = params.get('cubes') or []
        cube_inputs = [
            {
                'name': c.get('name', f'Equipo {i + 1}'),
                'x': float(c['x']), 'y': float(c['y']), 'z': float(c['z']),
                'dx': float(c['dx']), 'dy': float(c['dy']), 'dz': float(c['dz']),
            }
            for i, c in enumerate(cubes_raw)
        ] or None

        raw_pairs   = params.get('guard_wire_pairs') or []
        guard_pairs = [tuple(int(x) for x in p) for p in raw_pairs] or None

        result = mod.run_shielding_model_ui(
            mast_inputs           = mast_inputs,
            cube_inputs           = cube_inputs,
            BIL                   = float(params.get('BIL', 350)),
            Zs                    = float(params.get('Zs', 300)),
            k                     = float(params.get('k', 1.2)),
            S                     = float(params['S']) if params.get('S') else None,
            guard_wire_pairs      = guard_pairs,
            final_grid_n          = 20,
            mmq_patch_n           = 15,
            mmm_patch_n           = 15,
            verification_sample_n = 8,
            suppress_output       = True,
        )
        return {'verification': result.get('verification', []), 'validated': True, 'error': None, 'error_type': None}
    except Exception as e:
        return {'verification': [], 'validated': False, 'error': str(e), 'error_type': type(e).__name__}


# ─── Validación de longitud de cable ─────────────────────────────────────────

def _guard_length_ok(x1, y1, x2, y2, S, safety=0.98):
    """Devuelve (ok, length, max_allowed). ok=True si length <= safety*2*S."""
    length = math.hypot(x2 - x1, y2 - y1)
    max_allowed = safety * 2.0 * S
    return length <= max_allowed, length, max_allowed


# ─── Geometría de guardas ─────────────────────────────────────────────────────

def _perp_dist_2d(px, py, lx0, ly0, lvx, lvy):
    """Distancia perpendicular del punto (px,py) a la línea que pasa por (lx0,ly0) con dirección (lvx,lvy)."""
    norm = (lvx ** 2 + lvy ** 2) ** 0.5
    if norm < 1e-9:
        return ((px - lx0) ** 2 + (py - ly0) ** 2) ** 0.5
    return abs((px - lx0) * lvy - (py - ly0) * lvx) / norm


def _min_dist_cubes_to_line(cubes, unshielded_names, lvx, lvy, lx0, ly0):
    """Mínima distancia perpendicular desde las esquinas de los equipos no apantallados a la línea."""
    min_d = float('inf')
    for c in cubes:
        if c.get('name') not in unshielded_names:
            continue
        cx, cy   = float(c['x']), float(c['y'])
        dx, dy   = float(c['dx']), float(c['dy'])
        for xi in (cx, cx + dx):
            for yi in (cy, cy + dy):
                min_d = min(min_d, _perp_dist_2d(xi, yi, lx0, ly0, lvx, lvy))
    return min_d if min_d < float('inf') else 0.0


# ─── Recomendación A: cable de guarda usando mástil existente ─────────────────

def _recommend_guard_one_existing(params, unshielded, S, h_rec, mod):
    """
    Prueba múltiples candidatas (distancia más allá del equipo × altura del mástil).
    Devuelve la primera que logre protección completa; si ninguna la logra,
    devuelve la mejor validada o None si todo falla internamente.
    """
    masts  = params.get('masts', [])
    cubes  = params.get('cubes') or []
    gwp    = [(int(p[0]), int(p[1])) for p in (params.get('guard_wire_pairs') or [])]

    if not masts:
        return None

    all_crit = [p for v in unshielded for p in v.get('critical_points', [])]
    if not all_crit:
        return None

    cx = sum(p['x'] for p in all_crit) / len(all_crit)
    cy = sum(p['y'] for p in all_crit) / len(all_crit)

    # Ordenar mástiles por cercanía al centroide; intentar cada uno como anclaje
    mast_order = sorted(
        range(len(masts)),
        key=lambda i: (float(masts[i]['x']) - cx) ** 2 + (float(masts[i]['y']) - cy) ** 2,
    )

    # Candidatos de desplazamiento más allá del equipo
    beyond_vals = (S * 0.3, S * 0.5, S * 0.8)
    h_variants  = sorted({h_rec, round(h_rec * 1.25, 1), round(h_rec * 1.5, 1)})

    # best = (anchor_idx, new_x, new_y, h_c, all_ok, qv_dict)
    best = None

    for anchor_idx in mast_order:
        ax = float(masts[anchor_idx]['x'])
        ay = float(masts[anchor_idx]['y'])
        ddx, ddy = cx - ax, cy - ay
        dist_anchor_eq = math.hypot(ddx, ddy)
        if dist_anchor_eq < 1e-6:
            continue
        vx = ddx / dist_anchor_eq
        vy = ddy / dist_anchor_eq

        for beyond in beyond_vals:
            new_x = round(ax + vx * (dist_anchor_eq + beyond), 1)
            new_y = round(ay + vy * (dist_anchor_eq + beyond), 1)

            # Filtro de longitud: descartar antes de llamar al modelo
            ok_len, _, _ = _guard_length_ok(ax, ay, new_x, new_y, S)
            if not ok_len:
                continue  # cable demasiado largo, probar siguiente beyond/anclaje

            for h_c in h_variants:
                new_idx = len(masts)
                tp = dict(params)
                tp['masts']            = list(masts) + [{'x': new_x, 'y': new_y, 'h': h_c}]
                tp['guard_wire_pairs'] = list(gwp)   + [[anchor_idx, new_idx]]

                qv = _quick_verify(tp, mod)

                if best is None:
                    best = (anchor_idx, new_x, new_y, h_c, False, qv)

                if not qv['validated']:
                    continue

                verif  = qv['verification']
                all_ok = all(v.get('fully_shielded', False) for v in verif)

                if not best[5]['validated']:
                    best = (anchor_idx, new_x, new_y, h_c, all_ok, qv)

                if all_ok:
                    best = (anchor_idx, new_x, new_y, h_c, True, qv)
                    break  # protección completa encontrada

            if best is not None and best[4]:
                break  # salir del bucle beyond si ya tenemos solución completa

        if best is not None and best[4]:
            break  # salir del bucle de anclajes

    if best is None:
        return None

    anchor_idx, new_x, new_y, h_best, all_ok, qv = best
    new_idx   = len(masts)
    validated = qv['validated']
    verif     = qv['verification']
    n_ok      = sum(1 for v in verif if v.get('fully_shielded', False))
    n_total   = len(verif) or len(cubes)

    return {
        'type':  'add_guard_wire',
        'title': (
            f'Cable de guarda: M{anchor_idx} (existente) + M{new_idx} nuevo '
            f'en ({new_x}, {new_y}, h={h_best} m)'
        ),
        'reason': (
            f'El mástil M{anchor_idx} actúa de anclaje; M{new_idx} se ubica al otro '
            f'lado del equipo para que el cable cruce sobre su área '
            f'(S={S:.1f} m, h={h_best} m).'
        ),
        'actions': [
            {'action': 'add_mast',       'x': new_x, 'y': new_y, 'h': h_best},
            {'action': 'add_guard_wire', 'from_existing': anchor_idx, 'to_new': 0},
        ],
        'validation': {
            'predicted_fully_shielded': all_ok,
            'validated':                validated,
            'error':                    qv.get('error'),
            'error_message':            qv.get('error'),
            'error_type':               qv.get('error_type'),
            'equipment_coverage':       f'{n_ok}/{n_total} equipos protegidos',
            'notes':                    'Evaluado con el modelo de esfera rodante.' if validated else '',
        },
    }


# ─── Recomendación B: dos mástiles nuevos alineados con los más cercanos ──────

def _recommend_guard_two_new_aligned(params, unshielded, S, h_rec, mod):
    """
    Prueba multiples orientaciones (X, Y, mayor/menor eje del equipo) y offsets
    perpendiculares. Solo devuelve si encuentra proteccion completa verificada.
    """
    masts = params.get('masts', [])
    cubes = params.get('cubes') or []
    gwp   = [(int(p[0]), int(p[1])) for p in (params.get('guard_wire_pairs') or [])]

    if not masts:
        return None

    unshielded_names = {v.get('equipment_name', '') for v in unshielded}

    # Bounding box del equipamiento no apantallado
    xs, ys = [], []
    for c in cubes:
        if c.get('name') not in unshielded_names:
            continue
        xs += [float(c['x']), float(c['x']) + float(c['dx'])]
        ys += [float(c['y']), float(c['y']) + float(c['dy'])]

    if not xs:
        return None

    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    eq_cx = (x_min + x_max) / 2.0
    eq_cy = (y_min + y_max) / 2.0
    eq_hx = (x_max - x_min) / 2.0   # semiextension a lo largo de X
    eq_hy = (y_max - y_min) / 2.0   # semiextension a lo largo de Y

    # Orientaciones candidatas: (vx, vy, semiextension del equipo en esa direccion)
    # vx,vy = vector unitario a lo largo del cable
    # Para cada orientacion, el offset es en la direccion perpendicular (nx,ny = -vy, vx)
    orientations = [
        (1.0, 0.0, eq_hx),   # cable paralelo a X, offset en Y
        (0.0, 1.0, eq_hy),   # cable paralelo a Y, offset en X
    ]

    offsets  = [0, 1.5, -1.5, 3.0, -3.0, 4.5, -4.5, 6.0, -6.0]
    margins  = [2, 4, 6, 8, 10]
    h_variants = sorted({h_rec, round(h_rec * 1.25, 1), round(h_rec * 1.5, 1)})

    # best = (m1x, m1y, m2x, m2y, h_c, all_ok, qv_dict)
    best = None

    for vx, vy, eq_half in orientations:
        nx, ny = -vy, vx   # direccion perpendicular al cable

        for offset in offsets:
            line_cx = eq_cx + offset * nx
            line_cy = eq_cy + offset * ny

            for margin in margins:
                half_span = eq_half + margin

                m1x = round(line_cx - vx * half_span, 1)
                m1y = round(line_cy - vy * half_span, 1)
                m2x = round(line_cx + vx * half_span, 1)
                m2y = round(line_cy + vy * half_span, 1)

                ok_len, _, _ = _guard_length_ok(m1x, m1y, m2x, m2y, S)
                if not ok_len:
                    continue   # cable demasiado largo, saltear

                for h_c in h_variants:
                    base_idx = len(masts)
                    tp = dict(params)
                    tp['masts'] = list(masts) + [
                        {'x': m1x, 'y': m1y, 'h': h_c},
                        {'x': m2x, 'y': m2y, 'h': h_c},
                    ]
                    tp['guard_wire_pairs'] = list(gwp) + [[base_idx, base_idx + 1]]

                    qv = _quick_verify(tp, mod)

                    if best is None:
                        best = (m1x, m1y, m2x, m2y, h_c, False, qv)

                    if not qv['validated']:
                        continue

                    verif  = qv['verification']
                    all_ok = all(v.get('fully_shielded', False) for v in verif)

                    if not best[6]['validated']:
                        best = (m1x, m1y, m2x, m2y, h_c, all_ok, qv)

                    if all_ok:
                        best = (m1x, m1y, m2x, m2y, h_c, True, qv)
                        break   # proteccion completa encontrada

                if best is not None and best[5]:
                    break   # salir de margins
            if best is not None and best[5]:
                break   # salir de offsets
        if best is not None and best[5]:
            break   # salir de orientaciones

    # Solo devolver como recomendacion principal si hay proteccion completa
    if best is None or not best[5]:
        return None

    m1x, m1y, m2x, m2y, h_best, all_ok, qv = best
    base_idx  = len(masts)
    validated = qv['validated']
    verif     = qv['verification']
    n_ok      = sum(1 for v in verif if v.get('fully_shielded', False))
    n_total   = len(verif) or len(cubes)
    span      = round(math.hypot(m2x - m1x, m2y - m1y), 1)

    return {
        'type':  'add_guard_wire',
        'title': (
            f'Dos mastiles nuevos M{base_idx} ({m1x},{m1y}) y '
            f'M{base_idx + 1} ({m2x},{m2y}) con cable de guarda'
        ),
        'reason': (
            f'Cable a h={h_best} m, span={span} m sobre el equipo no apantallado.'
        ),
        'actions': [
            {'action': 'add_mast',       'x': m1x, 'y': m1y, 'h': h_best},
            {'action': 'add_mast',       'x': m2x, 'y': m2y, 'h': h_best},
            {'action': 'add_guard_wire', 'from_new': 0, 'to_new': 1},
        ],
        'validation': {
            'predicted_fully_shielded': all_ok,
            'validated':                validated,
            'error':                    qv.get('error'),
            'error_message':            qv.get('error'),
            'error_type':               qv.get('error_type'),
            'equipment_coverage':       f'{n_ok}/{n_total} equipos protegidos',
            'notes':                    'Evaluado con el modelo de esfera rodante.' if validated else '',
        },
    }


def calcular_recomendaciones(params: dict, S: float, verification: list) -> list:
    """Genera recomendaciones de cable de guarda para equipos no apantallados."""
    unshielded = [v for v in verification if not v.get('fully_shielded', True)]
    if not unshielded:
        return []

    masts = params.get('masts', [])
    h_rec = max((float(m['h']) for m in masts), default=15.0)
    mod   = _get_model()
    recs  = []

    rec_a = _recommend_guard_one_existing(params, unshielded, S, h_rec, mod)
    if rec_a:
        recs.append(rec_a)

    rec_b = _recommend_guard_two_new_aligned(params, unshielded, S, h_rec, mod)
    if rec_b:
        recs.append(rec_b)

    return recs
