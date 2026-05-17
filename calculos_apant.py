# -*- coding: utf-8 -*-
"""
TerraShield - calculos_apant.py
Wrapper Flask para el modulo de apantallamiento.
"""

import os
import sys
import math
import importlib.util
import numpy as np

_BASE    = os.path.dirname(os.path.abspath(__file__))
_V2_FILE = os.path.join(_BASE, 'apantallamiento_3d', 'modelo_shielding_v2.py')
_V2_KEY  = 'modelo_shielding_v2'


def _get_model():
    if _V2_KEY not in sys.modules:
        spec = importlib.util.spec_from_file_location(_V2_KEY, _V2_FILE)
        mod  = importlib.util.module_from_spec(spec)
        sys.modules[_V2_KEY] = mod
        spec.loader.exec_module(mod)
    return sys.modules[_V2_KEY]


# ------------------------------------------------------------
# API principal
# ------------------------------------------------------------

def calcular_apantallamiento(params: dict) -> dict:
    mast_inputs = [
        (float(m['x']), float(m['y']), float(m['h']))
        for m in params.get('masts', [])
    ]
    cubes_raw   = params.get('cubes') or []
    cube_inputs = [
        {
            'name':  c.get('name', f'Equipo {i+1}'),
            'x':     float(c['x']), 'y': float(c['y']), 'z': float(c['z']),
            'dx':    float(c['dx']), 'dy': float(c['dy']), 'dz': float(c['dz']),
            'color': c.get('color', 'rgba(245,196,0,0.35)'),
        }
        for i, c in enumerate(cubes_raw)
    ] or None
    raw_pairs   = params.get('guard_wire_pairs') or []
    guard_pairs = [tuple(int(x) for x in p) for p in raw_pairs] or None
    mod    = _get_model()
    result = mod.run_shielding_model_ui(
        mast_inputs           = mast_inputs,
        cube_inputs           = cube_inputs,
        BIL                   = float(params.get('BIL', 350)),
        Zs                    = float(params.get('Zs', 300)),
        k                     = float(params.get('k', 1.2)),
        S                     = float(params['S']) if params.get('S') else None,
        guard_wire_pairs      = guard_pairs,
        verification_margin   = float(params.get('verification_margin', 0.0)),
        verification_sample_n = int(params.get('verification_sample_n', 15)),
        include_bottom        = bool(params.get('include_bottom', False)),
        show_final            = False,
        final_grid_n          = int(params.get('final_grid_n', 80)),
        mmq_patch_n           = 40,
        mmm_patch_n           = 40,
        return_raw            = False,
    )
    return {
        'fig_json':     result.get('fig_json'),
        'S':            result.get('S'),
        'verification': result.get('verification', []),
    }


# ------------------------------------------------------------
# Verificacion rapida publica
# ------------------------------------------------------------

def verificar_equipos_rapido(cubes: list) -> list:
    """
    Verifica equipos contra la superficie cacheada (sin re-ejecutar el modelo).
    """
    mod = _get_model()
    return mod.verify_equipos_rapido(cubes)


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _vfy_name(v: dict) -> str:
    return v.get('equipment_name') or v.get('name', '')


def _vfy_pct(v: dict) -> float:
    if 'shielded_pct' in v:
        return float(v['shielded_pct'])
    total = v.get('points_evaluated', 0)
    ok    = v.get('points_protected', 0)
    return (ok / total * 100.0) if total > 0 else 0.0


def _mast_h(h_eq: float, d: float, S: float) -> float:
    """
    Altura minima estimada del mastil para proteger un punto a distancia d
    y altura h_eq, segun la geometria de la esfera rodante.
    """
    if d < S:
        return h_eq + S - math.sqrt(S * S - d * d)
    return h_eq + S


def _uncovered_direction(cx: float, cy: float, mast_inputs: list):
    """
    Vector unitario hacia el lado del equipo con menos cobertura:
    opuesto al promedio normalizado de las direcciones a los mastiles existentes.
    Sin mastiles -> apunta al norte.
    """
    if not mast_inputs:
        return 0.0, 1.0

    vx, vy = 0.0, 0.0
    for mx, my, _ in mast_inputs:
        dx, dy = mx - cx, my - cy
        d = math.hypot(dx, dy)
        if d > 0:
            vx += dx / d
            vy += dy / d

    mag = math.hypot(vx, vy)
    if mag < 1e-9:
        return 0.0, 1.0
    return -vx / mag, -vy / mag


def _snap_to_guard_orientation(px: float, py: float,
                               guard_wire_pairs: list, mast_inputs: list):
    """
    Ajusta (px, py) para que sea paralelo o perpendicular a los cables de
    guarda existentes.  Si no hay guardas, devuelve (px, py) sin cambios.
    Elige la opcion (paralela o perpendicular a cada guarda existente) cuyo
    vector forme el menor angulo con el (px, py) original.
    """
    if not guard_wire_pairs or len(mast_inputs) < 2:
        return px, py

    candidates = []
    for i, j in guard_wire_pairs:
        if i >= len(mast_inputs) or j >= len(mast_inputs):
            continue
        mx1, my1, _ = mast_inputs[i]
        mx2, my2, _ = mast_inputs[j]
        dx, dy = mx2 - mx1, my2 - my1
        d = math.hypot(dx, dy)
        if d < 1e-9:
            continue
        gx, gy = dx / d, dy / d
        # Paralelo y perpendicular (con ambos sentidos)
        candidates += [(gx, gy), (-gx, -gy), (-gy, gx), (gy, -gx)]

    if not candidates:
        return px, py

    best_dot, best = -2.0, (px, py)
    for cx, cy in candidates:
        dot = px * cx + py * cy
        if dot > best_dot:
            best_dot, best = dot, (cx, cy)
    return best


def _enforce_guard_separation(wx: float, wy: float,
                               px: float, py: float,
                               guard_wire_pairs: list, mast_inputs: list,
                               S: float) -> tuple:
    """
    Mueve (wx, wy) en la direccion perpendicular al cable (px, py) para que
    la separacion con cada guarda existente paralela no supere 2S.
    Devuelve (wx_corr, wy_corr, ajustado: bool).
    """
    if not guard_wire_pairs or len(mast_inputs) < 2:
        return wx, wy, False

    # Perpendicular unitaria al nuevo cable
    npx, npy = -py, px
    adjusted = False

    for i, j in guard_wire_pairs:
        if i >= len(mast_inputs) or j >= len(mast_inputs):
            continue
        mx1, my1, _ = mast_inputs[i]
        mx2, my2, _ = mast_inputs[j]
        dx, dy = mx2 - mx1, my2 - my1
        d = math.hypot(dx, dy)
        if d < 1e-9:
            continue
        gx, gy = dx / d, dy / d
        # Solo guardas paralelas (|cos θ| ≈ 1)
        if abs(px * gx + py * gy) < 0.95:
            continue
        # Separacion perpendicular con signo: positiva si el nuevo cable esta
        # en la direccion +np respecto al punto inicial de la guarda existente
        signed_sep = (wx - mx1) * npx + (wy - my1) * npy
        if abs(signed_sep) > 2 * S:
            excess = abs(signed_sep) - 2 * S
            sign   = 1 if signed_sep > 0 else -1
            wx -= sign * excess * npx
            wy -= sign * excess * npy
            adjusted = True

    return wx, wy, adjusted


def _compass_label(ux: float, uy: float) -> str:
    angle = math.degrees(math.atan2(uy, ux)) % 360
    sectors = [
        (22.5,  'este'),    (67.5,  'noreste'), (112.5, 'norte'),
        (157.5, 'noroeste'),(202.5, 'oeste'),   (247.5, 'suroeste'),
        (292.5, 'sur'),     (337.5, 'sureste'), (360.0, 'este'),
    ]
    for limit, label in sectors:
        if angle < limit:
            return label
    return 'este'


def _make_rec_fig(cube_inputs, mast_inputs, new_masts, new_wire):
    """
    Genera una figura Plotly 3D ligera para previsualizar una recomendacion.

    cube_inputs  : lista de dicts con x,y,z,dx,dy,dz,name
    mast_inputs  : lista de (x,y,h) mastiles existentes
    new_masts    : lista de (x,y,h) mastiles nuevos propuestos
    new_wire     : tupla (idx1, idx2) en new_masts para la guarda, o None
    """
    import plotly.graph_objects as go

    traces = []

    # --- Equipos (cajas wireframe con el color original de cada equipo) ---
    for cube in cube_inputs:
        x0, y0, z0 = cube['x'], cube['y'], cube['z']
        x1 = x0 + cube['dx']
        y1 = y0 + cube['dy']
        z1 = z0 + cube['dz']
        # Extraer color solido desde el rgba del cubo (puede ser 'rgba(r,g,b,a)')
        raw_color = cube.get('color', 'rgba(245,196,0,0.9)')
        # Usar el color tal cual para el wireframe (opacity ignorada, linea siempre opaca)
        import re as _re
        m = _re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', raw_color)
        line_color = f'rgb({m.group(1)},{m.group(2)},{m.group(3)})' if m else '#f5c400'

        lx, ly, lz = [], [], []
        for xa, ya, za, xb, yb, zb in [
            (x0,y0,z0,x1,y0,z0),(x1,y0,z0,x1,y1,z0),
            (x1,y1,z0,x0,y1,z0),(x0,y1,z0,x0,y0,z0),
            (x0,y0,z1,x1,y0,z1),(x1,y0,z1,x1,y1,z1),
            (x1,y1,z1,x0,y1,z1),(x0,y1,z1,x0,y0,z1),
            (x0,y0,z0,x0,y0,z1),(x1,y0,z0,x1,y0,z1),
            (x1,y1,z0,x1,y1,z1),(x0,y1,z0,x0,y1,z1),
        ]:
            lx += [xa, xb, None]
            ly += [ya, yb, None]
            lz += [za, zb, None]
        traces.append(go.Scatter3d(
            x=lx, y=ly, z=lz, mode='lines',
            line=dict(color=line_color, width=3),
            name=cube['name'], showlegend=True,
        ))

    # --- Mastiles existentes (azul) ---
    for i, (mx, my, mh) in enumerate(mast_inputs):
        traces.append(go.Scatter3d(
            x=[mx, mx], y=[my, my], z=[0, mh],
            mode='lines+markers',
            line=dict(color='#3b82f6', width=4),
            marker=dict(size=[0, 6], color='#3b82f6'),
            name=f'M{i}', showlegend=True,
        ))

    # --- Mastiles nuevos propuestos (naranja) ---
    for j, (nx, ny, nh) in enumerate(new_masts):
        traces.append(go.Scatter3d(
            x=[nx, nx], y=[ny, ny], z=[0, nh],
            mode='lines+markers',
            line=dict(color='#f97316', width=4),
            marker=dict(size=[0, 7], color='#f97316'),
            name=f'M{len(mast_inputs)+j} (nuevo)', showlegend=True,
        ))

    # --- Cable de guarda nuevo (naranja discontinuo) ---
    if new_wire is not None and len(new_masts) > max(new_wire):
        i1, i2 = new_wire
        m1, m2 = new_masts[i1], new_masts[i2]
        traces.append(go.Scatter3d(
            x=[m1[0], m2[0]], y=[m1[1], m2[1]], z=[m1[2], m2[2]],
            mode='lines',
            line=dict(color='#f97316', width=4, dash='dash'),
            name='Guarda nueva', showlegend=True,
        ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        margin=dict(l=0, r=0, t=8, b=0),
        height=270,
        scene=dict(
            xaxis=dict(title='X (m)'),
            yaxis=dict(title='Y (m)'),
            zaxis=dict(title='Z (m)'),
            bgcolor='rgba(248,250,252,1)',
            aspectmode='data',
        ),
        legend=dict(font=dict(size=9), bgcolor='rgba(255,255,255,0.8)',
                    x=0, y=1, xanchor='left'),
        paper_bgcolor='rgba(0,0,0,0)',
    )
    return fig.to_json()


# ------------------------------------------------------------
# API de recomendaciones (geometria pura, sin modelo)
# ------------------------------------------------------------

def calcular_recomendaciones(params: dict, S: float, verification: list):
    """
    Genera sugerencias geometricas para equipos sin cobertura.
    El mastil/cable sugerido se coloca en el lado opuesto al promedio
    de los mastiles existentes (lado con menos cobertura estimada).
    Retorna (recommendations: list, diagnostics: list).
    """
    unshielded = [v for v in verification if _vfy_pct(v) < 100.0]
    if not unshielded:
        return [], [{'strategy': 'none',
                     'reason': 'Todos los equipos ya estan apantallados.'}]

    cubes_raw = params.get('cubes') or []
    cube_map  = {
        c.get('name', f'Equipo {i+1}'): {
            'name':  c.get('name', f'Equipo {i+1}'),
            'x':  float(c['x']),  'y':  float(c['y']),  'z':  float(c['z']),
            'dx': float(c['dx']), 'dy': float(c['dy']), 'dz': float(c['dz']),
            'color': c.get('color', 'rgba(245,196,0,0.9)'),
        }
        for i, c in enumerate(cubes_raw)
    }
    all_cubes = list(cube_map.values())

    mast_inputs = [
        (float(m['x']), float(m['y']), float(m['h']))
        for m in params.get('masts', [])
    ]
    n_existing = len(mast_inputs)

    raw_pairs   = params.get('guard_wire_pairs') or []
    guard_pairs = [tuple(int(x) for x in p) for p in raw_pairs] or []

    recs = []

    for vitem in unshielded:
        name = _vfy_name(vitem)
        cube = cube_map.get(name)
        if cube is None:
            continue

        cx   = cube['x'] + cube['dx'] / 2.0
        cy   = cube['y'] + cube['dy'] / 2.0
        h_eq = cube['z'] + cube['dz']
        hdx  = cube['dx'] / 2.0
        hdy  = cube['dy'] / 2.0

        # Vector hacia el lado descubierto
        ux, uy = _uncovered_direction(cx, cy, mast_inputs)
        label  = _compass_label(ux, uy)

        # Vector perpendicular (para el cable de guarda),
        # ajustado para ser paralelo o perpendicular a guardas existentes
        px, py = _snap_to_guard_orientation(-uy, ux, guard_pairs, mast_inputs)

        # --------------------------------------------------
        # Recomendacion 1: mastil unico
        # --------------------------------------------------
        edge_proj = abs(ux) * hdx + abs(uy) * hdy
        dist_mast = edge_proj + 1.5

        mx1 = cx + ux * dist_mast
        my1 = cy + uy * dist_mast

        # Altura: la esfera debe cubrir la esquina MAS LEJANA del equipo
        x0c, x1c = cube['x'], cube['x'] + cube['dx']
        y0c, y1c = cube['y'], cube['y'] + cube['dy']
        d_max = max(
            math.hypot(mx1 - x0c, my1 - y0c),
            math.hypot(mx1 - x1c, my1 - y0c),
            math.hypot(mx1 - x0c, my1 - y1c),
            math.hypot(mx1 - x1c, my1 - y1c),
        )
        h1 = round(max(10.0, _mast_h(h_eq, d_max, S) + 1.0), 2)

        idx1 = n_existing + len(recs)
        new_masts_1 = [(round(mx1, 2), round(my1, 2), h1)]

        recs.append({
            'type':             'add_mast',
            'title':            f'Mastil M{idx1} al {label} de "{name}"',
            'reason':           (f'Nuevo mastil en ({mx1:.1f}, {my1:.1f}), '
                                 f'altura estimada {h1:.1f} m. '
                                 f'Aplicar y recalcular para verificar.'),
            'target_equipment': name,
            'actions':          [{'action': 'add_mast',
                                  'x': round(mx1, 2), 'y': round(my1, 2), 'h': h1}],
            'fig_json':         _make_rec_fig(all_cubes, mast_inputs, new_masts_1, None),
        })

        # --------------------------------------------------
        # Recomendacion 2: cable de guarda con 2 mastiles nuevos
        # --------------------------------------------------
        dist_wire      = edge_proj + 1.5
        wx, wy         = cx + ux * dist_wire, cy + uy * dist_wire
        # Garantizar separacion ≤ 2S con guardas existentes paralelas
        wx, wy, sep_adj = _enforce_guard_separation(
            wx, wy, px, py, guard_pairs, mast_inputs, S)
        perp_proj  = abs(px) * hdx + abs(py) * hdy
        half_cable = min(perp_proj + S * 0.35, S)

        gm1x = round(wx - px * half_cable, 2)
        gm1y = round(wy - py * half_cable, 2)
        gm2x = round(wx + px * half_cable, 2)
        gm2y = round(wy + py * half_cable, 2)

        # Altura: cada mastil debe cubrir la esquina MAS LEJANA del equipo
        d_max_gm1 = max(
            math.hypot(gm1x - x0c, gm1y - y0c),
            math.hypot(gm1x - x1c, gm1y - y0c),
            math.hypot(gm1x - x0c, gm1y - y1c),
            math.hypot(gm1x - x1c, gm1y - y1c),
        )
        d_max_gm2 = max(
            math.hypot(gm2x - x0c, gm2y - y0c),
            math.hypot(gm2x - x1c, gm2y - y0c),
            math.hypot(gm2x - x0c, gm2y - y1c),
            math.hypot(gm2x - x1c, gm2y - y1c),
        )
        # Usar la mayor de las dos distancias para que ambos mastiles tengan igual altura
        d_max_wire = max(d_max_gm1, d_max_gm2)
        h_wire = round(max(10.0, _mast_h(h_eq, d_max_wire, S) + 1.0), 2)

        idx2 = n_existing + len(recs)
        idx3 = idx2 + 1
        new_masts_2 = [(gm1x, gm1y, h_wire), (gm2x, gm2y, h_wire)]

        sep_note = (' Posicion ajustada para cumplir separacion ≤ 2S.' if sep_adj else '')

        recs.append({
            'type':             'add_guard_wire',
            'title':            f'Cable de guarda al {label} de "{name}"',
            'reason':           (f'M{idx2} ({gm1x:.1f}, {gm1y:.1f}) y '
                                 f'M{idx3} ({gm2x:.1f}, {gm2y:.1f}), h≈{h_wire:.1f} m. '
                                 f'Aplicar y recalcular para verificar.{sep_note}'),
            'target_equipment': name,
            'actions':          [
                {'action': 'add_mast',       'x': gm1x, 'y': gm1y, 'h': h_wire},
                {'action': 'add_mast',       'x': gm2x, 'y': gm2y, 'h': h_wire},
                {'action': 'add_guard_wire', 'from_new': 0, 'to_new': 1},
            ],
            'fig_json':         _make_rec_fig(all_cubes, mast_inputs, new_masts_2, (0, 1)),
        })

    return recs, []
