# -*- coding: utf-8 -*-
"""
Modelo limpio para interfaz de usuario.

Contiene solo definiciones y una función principal que devuelve:
- fig: gráfico final Plotly
- verification: resumen de verificación
- raw: variables internas principales

Generado a partir del notebook del modelo, eliminando ejecuciones y gráficas intermedias.
"""


from math import sqrt


from itertools import combinations


try:
    import ipywidgets as widgets
except Exception:
    class _DummyWidget:
        def __init__(self, *args, **kwargs):
            self.value = kwargs.get("value", tuple())
        def on_click(self, *args, **kwargs):
            return None
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
    class _DummyWidgets:
        SelectMultiple = _DummyWidget
        Button = _DummyWidget
        Output = _DummyWidget
        Layout = _DummyWidget
    widgets = _DummyWidgets()


from IPython.display import display, clear_output


BIL = 350
Zs = 300
k = 1.2
Is = (2.2 * BIL) / Zs
S = k * 8 * Is**0.65  # radio de la esfera rodante


from collections import defaultdict


from math import sqrt, isfinite


from itertools import combinations


try:
    import ipywidgets as widgets
except Exception:
    class _DummyWidget:
        def __init__(self, *args, **kwargs):
            self.value = kwargs.get("value", tuple())
        def on_click(self, *args, **kwargs):
            return None
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
    class _DummyWidgets:
        SelectMultiple = _DummyWidget
        Button = _DummyWidget
        Output = _DummyWidget
        Layout = _DummyWidget
    widgets = _DummyWidgets()


from IPython.display import display, clear_output


ANGLE_TOL_GUARDS = 1e-7


DIST_TOL_GUARDS = 1e-7


SHOW_DEBUG_GUARD_VALIDATION = False


def edge_key_int(i, j):
    return tuple(sorted((int(i), int(j))))


def edge_label(edge):
    i, j = edge
    return f"M{i}-M{j}"


def mast_xy(idx):
    x, y, _ = mast_inputs[int(idx)]
    return (float(x), float(y))


def mast_xyz(idx):
    x, y, h = mast_inputs[int(idx)]
    return (float(x), float(y), float(h))


def vec_xy(edge):
    i, j = edge
    xi, yi = mast_xy(i)
    xj, yj = mast_xy(j)
    return (xj - xi, yj - yi)


def norm2(v):
    return sqrt(v[0]**2 + v[1]**2)


def dot2(u, v):
    return u[0]*v[0] + u[1]*v[1]


def cross2(u, v):
    return u[0]*v[1] - u[1]*v[0]


def are_parallel_edges(e1, e2, tol=ANGLE_TOL_GUARDS):
    v1 = vec_xy(e1)
    v2 = vec_xy(e2)

    n1 = norm2(v1)
    n2 = norm2(v2)

    if n1 <= tol or n2 <= tol:
        return False

    return abs(cross2(v1, v2)) <= tol * n1 * n2


def are_perpendicular_edges(e1, e2, tol=ANGLE_TOL_GUARDS):
    v1 = vec_xy(e1)
    v2 = vec_xy(e2)

    n1 = norm2(v1)
    n2 = norm2(v2)

    if n1 <= tol or n2 <= tol:
        return False

    return abs(dot2(v1, v2)) <= tol * n1 * n2


def edges_are_parallel_or_perpendicular(e1, e2):
    return are_parallel_edges(e1, e2) or are_perpendicular_edges(e1, e2)


def distance_xy_between_masts(i, j):
    xi, yi = mast_xy(i)
    xj, yj = mast_xy(j)
    return sqrt((xj - xi)**2 + (yj - yi)**2)


def distance_3d_between_masts(i, j):
    xi, yi, hi = mast_xyz(i)
    xj, yj, hj = mast_xyz(j)
    return sqrt((xj - xi)**2 + (yj - yi)**2 + (hj - hi)**2)


def perpendicular_distance_between_parallel_edges(e1, e2):
    """
    Distancia perpendicular entre dos guardas paralelas en planta XY.
    Se calcula entre las rectas infinitas que contienen las guardas.
    """
    a, b = e1
    c, _ = e2

    A = mast_xy(a)
    C = mast_xy(c)

    v = vec_xy(e1)
    nv = norm2(v)

    if nv <= 1e-12:
        return None

    AC = (C[0] - A[0], C[1] - A[1])
    return abs(cross2(v, AC)) / nv


def projection_interval_on_edge_direction(edge_ref, edge_target):
    """
    Proyecta los extremos de edge_target sobre la dirección de edge_ref.
    Sirve para saber si dos guardas paralelas quedan enfrentadas.
    """
    a, b = edge_ref
    c, d = edge_target

    A = mast_xy(a)
    C = mast_xy(c)
    D = mast_xy(d)

    v = vec_xy(edge_ref)
    nv = norm2(v)

    if nv <= 1e-12:
        return None

    ux = v[0] / nv
    uy = v[1] / nv

    tC = (C[0] - A[0]) * ux + (C[1] - A[1]) * uy
    tD = (D[0] - A[0]) * ux + (D[1] - A[1]) * uy

    return (min(tC, tD), max(tC, tD))


def own_projection_interval(edge):
    v = vec_xy(edge)
    nv = norm2(v)
    return (0.0, nv)


def intervals_overlap(i1, i2, tol=DIST_TOL_GUARDS):
    a, b = i1
    c, d = i2
    return max(a, c) <= min(b, d) + tol


def parallel_edges_have_overlap(e1, e2):
    """
    Determina si dos guardas paralelas están enfrentadas en planta.
    Esto evita tomar como 'dos guardas paralelas relacionadas' a segmentos
    paralelos muy separados longitudinalmente.
    """
    if not are_parallel_edges(e1, e2):
        return False

    i1 = own_projection_interval(e1)
    i2 = projection_interval_on_edge_direction(e1, e2)

    if i1 is None or i2 is None:
        return False

    return intervals_overlap(i1, i2)


def orient_xy(a, b, c):
    return (
        (b[0] - a[0]) * (c[1] - a[1])
        -
        (b[1] - a[1]) * (c[0] - a[0])
    )


def segments_cross_xy_edges(e1, e2, tol=1e-9):
    """
    Detecta cruce interior en planta XY entre dos guardas que no comparten mástil.
    """
    if set(e1).intersection(set(e2)):
        return False

    a, b = e1
    c, d = e2

    A = mast_xy(a)
    B = mast_xy(b)
    C = mast_xy(c)
    D = mast_xy(d)

    o1 = orient_xy(A, B, C)
    o2 = orient_xy(A, B, D)
    o3 = orient_xy(C, D, A)
    o4 = orient_xy(C, D, B)

    return (o1 * o2 < -tol) and (o3 * o4 < -tol)


def build_guard_graph(edges):
    adj = defaultdict(set)

    for i, j in edges:
        adj[i].add(j)
        adj[j].add(i)

    return adj


def connected_components_edges(edges):
    """
    Devuelve componentes conectadas del grafo de guardas.
    Cada componente incluye:
      - nodes
      - edges
    """
    edges = [edge_key_int(i, j) for i, j in edges]

    if not edges:
        return []

    adj = build_guard_graph(edges)

    visited_nodes = set()
    components = []

    for start in sorted(adj):
        if start in visited_nodes:
            continue

        stack = [start]
        comp_nodes = set()

        while stack:
            u = stack.pop()

            if u in comp_nodes:
                continue

            comp_nodes.add(u)

            for v in adj[u]:
                if v not in comp_nodes:
                    stack.append(v)

        visited_nodes.update(comp_nodes)

        comp_edges = [
            e for e in edges
            if e[0] in comp_nodes and e[1] in comp_nodes
        ]

        components.append({
            "nodes": sorted(comp_nodes),
            "edges": sorted(comp_edges),
        })

    return components


def component_degrees(component):
    deg = defaultdict(int)

    for i, j in component["edges"]:
        deg[i] += 1
        deg[j] += 1

    return dict(deg)


def component_is_straight_independent_guard_line(component):
    """
    Permite una guarda independiente o una línea recta de guardas colineales.
    Ejemplos:
      - M0-M1
      - M0-M1-M2 si ambas guardas son colineales.
    """
    edges = component["edges"]

    if len(edges) == 1:
        return True

    for e1, e2 in combinations(edges, 2):
        if not are_parallel_edges(e1, e2):
            return False

    return True


def order_path_edges(component):
    """
    Ordena una componente tipo camino.
    Retorna la lista de aristas en orden.
    """
    edges = component["edges"]
    deg = component_degrees(component)

    endpoints = [n for n, d in deg.items() if d == 1]

    if len(endpoints) != 2:
        return None

    adj = build_guard_graph(edges)

    start = endpoints[0]
    current = start
    prev = None
    ordered_edges = []

    while True:
        next_nodes = [n for n in adj[current] if n != prev]

        if not next_nodes:
            break

        nxt = next_nodes[0]
        ordered_edges.append(edge_key_int(current, nxt))

        prev = current
        current = nxt

        if current == endpoints[1]:
            break

    if len(ordered_edges) != len(edges):
        return None

    return ordered_edges


def component_is_three_joined_guards(component):
    """
    Tres guardas unidas:
        e0 -- e1 -- e2

    Requisito:
      - componente camino de 3 aristas;
      - e0 paralelo a e2;
      - e1 perpendicular a e0 y e2;
      - distancia perpendicular entre e0 y e2 <= 2S.
    """
    if len(component["edges"]) != 3:
        return False, None

    ordered = order_path_edges(component)

    if ordered is None or len(ordered) != 3:
        return False, {
            "reason": "no forma un camino de tres guardas",
            "edges": component["edges"]
        }

    e0, e1, e2 = ordered

    if not are_parallel_edges(e0, e2):
        return False, {
            "reason": "las guardas extremas no son paralelas",
            "edges": ordered
        }

    if not are_perpendicular_edges(e0, e1) or not are_perpendicular_edges(e1, e2):
        return False, {
            "reason": "la guarda central no es perpendicular a las guardas extremas",
            "edges": ordered
        }

    d_perp = perpendicular_distance_between_parallel_edges(e0, e2)
    limit = 2.0 * S

    if d_perp is None or d_perp > limit + DIST_TOL_GUARDS:
        return False, {
            "reason": "la distancia perpendicular entre guardas extremas supera 2S",
            "edges": ordered,
            "distance": d_perp,
            "limit": limit
        }

    return True, {
        "type": "three_joined_guards",
        "edges": ordered,
        "distance": d_perp,
        "limit": limit
    }


def order_cycle_edges_4(component):
    """
    Ordena una componente cerrada de 4 guardas.
    """
    edges = component["edges"]
    nodes = component["nodes"]
    deg = component_degrees(component)

    if len(edges) != 4 or len(nodes) != 4:
        return None

    if any(deg.get(n, 0) != 2 for n in nodes):
        return None

    adj = build_guard_graph(edges)

    start = min(nodes)
    neighbors = sorted(adj[start])

    for first_next in neighbors:
        ordered_nodes = [start, first_next]
        prev = start
        current = first_next

        while len(ordered_nodes) < 4:
            candidates = [n for n in adj[current] if n != prev]

            if not candidates:
                break

            nxt = candidates[0]

            if nxt == start:
                break

            ordered_nodes.append(nxt)
            prev = current
            current = nxt

        if len(ordered_nodes) != 4:
            continue

        if start not in adj[ordered_nodes[-1]]:
            continue

        ordered_edges = []

        for k in range(4):
            a = ordered_nodes[k]
            b = ordered_nodes[(k + 1) % 4]
            ordered_edges.append(edge_key_int(a, b))

        if set(ordered_edges) == set(edges):
            return ordered_edges

    return None


def component_is_four_guard_square(component):
    """
    Cuatro guardas formando cuadrado/rectángulo ortogonal:
      - ciclo cerrado de 4 guardas;
      - lados opuestos paralelos;
      - lados adyacentes perpendiculares;
      - ambas distancias perpendiculares entre lados opuestos <= 2S.
    """
    ordered = order_cycle_edges_4(component)

    if ordered is None:
        return False, None

    e0, e1, e2, e3 = ordered

    adjacent_ok = (
        are_perpendicular_edges(e0, e1)
        and are_perpendicular_edges(e1, e2)
        and are_perpendicular_edges(e2, e3)
        and are_perpendicular_edges(e3, e0)
    )

    opposite_ok = (
        are_parallel_edges(e0, e2)
        and are_parallel_edges(e1, e3)
    )

    if not adjacent_ok or not opposite_ok:
        return False, {
            "reason": "el ciclo de 4 guardas no forma un cuadrado/rectángulo ortogonal",
            "edges": ordered
        }

    d_02 = perpendicular_distance_between_parallel_edges(e0, e2)
    d_13 = perpendicular_distance_between_parallel_edges(e1, e3)
    limit = 2.0 * S

    if d_02 is None or d_02 > limit + DIST_TOL_GUARDS:
        return False, {
            "reason": "la distancia perpendicular entre un par de lados opuestos supera 2S",
            "edges": ordered,
            "distance": d_02,
            "limit": limit
        }

    if d_13 is None or d_13 > limit + DIST_TOL_GUARDS:
        return False, {
            "reason": "la distancia perpendicular entre el otro par de lados opuestos supera 2S",
            "edges": ordered,
            "distance": d_13,
            "limit": limit
        }

    return True, {
        "type": "four_guard_square",
        "edges": ordered,
        "distance_pair_1": d_02,
        "distance_pair_2": d_13,
        "limit": limit
    }


def validate_all_guards_parallel_or_perpendicular(edges):
    errors = []

    for e1, e2 in combinations(edges, 2):
        if not edges_are_parallel_or_perpendicular(e1, e2):
            errors.append(
                f"{edge_label(e1)} y {edge_label(e2)} no son paralelas ni perpendiculares entre sí."
            )

    return errors


def validate_no_crossing_guard_wires(edges):
    errors = []

    for e1, e2 in combinations(edges, 2):
        if segments_cross_xy_edges(e1, e2):
            errors.append(
                f"{edge_label(e1)} cruza en planta con {edge_label(e2)} sin compartir mástil."
            )

    return errors


def validate_parallel_guard_distances(edges):
    """
    Caso dos guardas paralelas:
    Si dos guardas paralelas quedan enfrentadas en planta,
    su distancia perpendicular no puede ser mayor que 2S.
    """
    errors = []
    limit = 2.0 * S

    for e1, e2 in combinations(edges, 2):
        if set(e1).intersection(set(e2)):
            continue

        if not are_parallel_edges(e1, e2):
            continue

        # Solo se consideran como par paralelo local si sus proyecciones se enfrentan.
        if not parallel_edges_have_overlap(e1, e2):
            continue

        d_perp = perpendicular_distance_between_parallel_edges(e1, e2)

        if d_perp is None:
            continue

        if d_perp > limit + DIST_TOL_GUARDS:
            errors.append(
                f"Dos guardas paralelas {edge_label(e1)} y {edge_label(e2)} "
                f"tienen distancia perpendicular {d_perp:.6f} > 2S = {limit:.6f}."
            )

    return errors


def validate_guard_components(edges):
    """
    Valida que cada componente conectada pertenezca a una configuración soportada:
      - guarda independiente / línea recta de guardas colineales;
      - tres guardas unidas;
      - cuatro guardas formando cuadrado/rectángulo.
    """
    errors = []
    info = []

    components = connected_components_edges(edges)

    for comp_idx, comp in enumerate(components):
        comp_edges = comp["edges"]
        comp_label = ", ".join(edge_label(e) for e in comp_edges)

        # 1) Guarda independiente o línea recta de guardas colineales.
        if component_is_straight_independent_guard_line(comp):
            info.append({
                "component": comp_idx,
                "type": "guarda_independiente_o_linea_recta",
                "edges": comp_edges
            })
            continue

        # 2) Tres guardas unidas.
        ok3, data3 = component_is_three_joined_guards(comp)

        if ok3:
            info.append({
                "component": comp_idx,
                **data3
            })
            continue

        if len(comp_edges) == 3 and data3 is not None:
            msg = data3.get("reason", "no cumple geometría de tres guardas unidas")
            extra = ""

            if "distance" in data3:
                extra = f" Distancia = {data3['distance']:.6f}, límite 2S = {data3['limit']:.6f}."

            errors.append(
                f"Componente {comp_idx} ({comp_label}) no cumple el caso de 3 guardas unidas: {msg}.{extra}"
            )
            continue

        # 3) Cuatro guardas formando cuadrado/rectángulo.
        ok4, data4 = component_is_four_guard_square(comp)

        if ok4:
            info.append({
                "component": comp_idx,
                **data4
            })
            continue

        if len(comp_edges) == 4 and data4 is not None:
            msg = data4.get("reason", "no cumple geometría de 4 guardas cerradas")
            extra = ""

            if "distance" in data4:
                extra = f" Distancia = {data4['distance']:.6f}, límite 2S = {data4['limit']:.6f}."

            errors.append(
                f"Componente {comp_idx} ({comp_label}) no cumple el caso de 4 guardas formando cuadrado: {msg}.{extra}"
            )
            continue

        errors.append(
            f"Componente {comp_idx} ({comp_label}) no corresponde a una configuración soportada. "
            "Solo se permiten guardas independientes, dos guardas paralelas, "
            "tres guardas unidas o cuatro guardas formando cuadrado/rectángulo ortogonal."
        )

    return errors, info


def validate_guard_wire_selection(selected_pairs):
    """
    Valida toda la selección de guardas.
    Si hay errores, lanza ValueError.
    """
    errors = []
    edges = []

    for pair in selected_pairs:
        if len(pair) != 2:
            errors.append(f"Par inválido: {pair}. Debe tener formato (i, j).")
            continue

        i, j = int(pair[0]), int(pair[1])

        if i == j:
            errors.append(f"No se permite una guarda entre el mismo mástil: M{i}-M{j}.")
            continue

        if i < 0 or i >= len(mast_inputs):
            errors.append(f"El mástil M{i} no existe.")
            continue

        if j < 0 or j >= len(mast_inputs):
            errors.append(f"El mástil M{j} no existe.")
            continue

        key = edge_key_int(i, j)

        if key in edges:
            errors.append(f"Guarda duplicada: {edge_label(key)}.")
            continue

        edges.append(key)

    component_info = []

    if not errors:
        errors.extend(validate_all_guards_parallel_or_perpendicular(edges))
        errors.extend(validate_no_crossing_guard_wires(edges))
        errors.extend(validate_parallel_guard_distances(edges))

        component_errors, component_info = validate_guard_components(edges)
        errors.extend(component_errors)

    if errors:
        print("\nERROR EN LA SELECCIÓN DE CABLES DE GUARDA")
        print("=========================================")

        for err in errors:
            print(f"  - {err}")

        print("\nRecomendación:")
        print("  Disminuye la distancia entre mástiles, ajusta la geometría")
        print("  o selecciona guardas que formen únicamente las configuraciones soportadas.")

        raise ValueError(
            "La selección de cables de guarda contiene configuraciones no soportadas."
        )

    guard_wire_inputs_valid = []

    for i, j in edges:
        xi, yi, hi = mast_inputs[i]
        xj, yj, hj = mast_inputs[j]

        guard_wire_inputs_valid.append({
            "i": i,
            "j": j,
            "p1": (xi, yi, hi),
            "p2": (xj, yj, hj),
            "dxy": distance_xy_between_masts(i, j),
            "d3d": distance_3d_between_masts(i, j)
        })

    return edges, guard_wire_inputs_valid, component_info


def confirmar_cables(b):
    global guard_wire_pairs, guard_wire_inputs

    with out_wires:
        clear_output()

        selected_pairs = [
            tuple(map(int, pair))
            for pair in wire_selector.value
        ]

        try:
            guard_wire_pairs, guard_wire_inputs, component_info = validate_guard_wire_selection(
                selected_pairs
            )

            print("Cables de guarda seleccionados y validados:")
            print("===========================================")

            if not guard_wire_inputs:
                print("No se seleccionaron cables de guarda.")
            else:
                for k, wire in enumerate(guard_wire_inputs):
                    print(
                        f"Cable {k}: "
                        f"M{wire['i']} → M{wire['j']} | "
                        f"dXY={wire['dxy']:.3f} m | "
                        f"d3D={wire['d3d']:.3f} m | "
                        f"{wire['p1']} → {wire['p2']}"
                    )

            print("\nVariable guard_wire_pairs:")
            print(guard_wire_pairs)

            print("\nConfiguraciones detectadas:")
            print("===========================")

            if not component_info:
                print("No hay configuraciones especiales detectadas.")
            else:
                for item in component_info:
                    edges_txt = ", ".join(edge_label(e) for e in item["edges"])

                    if item["type"] == "guarda_independiente_o_linea_recta":
                        print(
                            f"  Componente {item['component']}: "
                            f"guarda independiente / línea recta -> {edges_txt}"
                        )

                    elif item["type"] == "three_joined_guards":
                        print(
                            f"  Componente {item['component']}: "
                            f"3 guardas unidas -> {edges_txt} | "
                            f"d_perp={item['distance']:.3f} <= 2S={item['limit']:.3f}"
                        )

                    elif item["type"] == "four_guard_square":
                        print(
                            f"  Componente {item['component']}: "
                            f"4 guardas formando cuadrado/rectángulo -> {edges_txt} | "
                            f"d1={item['distance_pair_1']:.3f}, "
                            f"d2={item['distance_pair_2']:.3f}, "
                            f"2S={item['limit']:.3f}"
                        )

        except Exception as e:
            guard_wire_inputs = []
            guard_wire_pairs = []

            print("La selección NO fue aceptada.")
            print(str(e))
            print("\nCorrige la selección y vuelve a presionar el botón.")


import plotly.graph_objects as go


import matplotlib.pyplot as plt


_ORIGINAL_PLOTLY_SHOW = go.Figure.show


_ORIGINAL_MATPLOTLIB_SHOW = plt.show


def _silent_plotly_show(self, *args, **kwargs):
    return None


def _silent_matplotlib_show(*args, **kwargs):
    return None


import numpy as np


import matplotlib.pyplot as plt


from dataclasses import dataclass


from math import atan2, pi, sqrt


@dataclass
class Mast:
    x: float
    y: float
    h: float


@dataclass
class PairBlockResult:
    i: int
    j: int
    ai: float
    aj: float
    dij: float
    alpha_ij: float
    phi_ij: float
    q_plus: tuple
    q_minus: tuple
    blocked_intervals_0_2pi: list


def wrap_to_pi(angle: float) -> float:
    return (angle + pi) % (2.0 * pi) - pi


def normalize_0_2pi(angle: float) -> float:
    return angle % (2.0 * pi)


def distance(p1, p2) -> float:
    return sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def effective_radius(height: float, sphere_radius: float) -> float:
    z_star = min(sphere_radius, height)
    radicand = sphere_radius**2 - (sphere_radius - z_star) ** 2
    return sqrt(max(0.0, radicand))


def split_wrapped_interval(theta_min: float, theta_max: float):
    theta_min = normalize_0_2pi(theta_min)
    theta_max = normalize_0_2pi(theta_max)

    if theta_min <= theta_max:
        return [(theta_min, theta_max)]
    else:
        return [(theta_min, 2.0 * pi), (0.0, theta_max)]


def merge_intervals(intervals, tol=1e-12):
    if not intervals:
        return []

    intervals = sorted(intervals, key=lambda x: x[0])
    merged = [intervals[0]]

    for start, end in intervals[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end + tol:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged


def complement_intervals(intervals, domain_start=0.0, domain_end=2.0 * pi, tol=1e-12):
    if not intervals:
        return [(domain_start, domain_end)]

    intervals = merge_intervals(intervals, tol=tol)
    comp = []
    current = domain_start

    for start, end in intervals:
        if start > current + tol:
            comp.append((current, start))
        current = max(current, end)

    if current < domain_end - tol:
        comp.append((current, domain_end))

    return comp


def pair_block_for_i_due_to_j(i, j, masts, sphere_radius, tol=1e-12):
    mi = masts[i]
    mj = masts[j]

    Ai = np.array([mi.x, mi.y], dtype=float)
    Aj = np.array([mj.x, mj.y], dtype=float)

    ai = effective_radius(mi.h, sphere_radius)
    aj = effective_radius(mj.h, sphere_radius)

    dij = distance(Ai, Aj)
    if dij <= tol:
        raise ValueError(f"Los mástiles {i} y {j} están en la misma posición.")

    # condición de intersección
    if not (abs(ai - aj) <= dij + tol and dij <= ai + aj + tol):
        return None

    eij = (Aj - Ai) / dij
    nij = np.array([-eij[1], eij[0]])

    uij = (dij**2 + ai**2 - aj**2) / (2.0 * dij)
    bij_sq = ai**2 - uij**2
    if bij_sq < -tol:
        return None

    bij = sqrt(max(0.0, bij_sq))

    q_plus = Ai + uij * eij + bij * nij
    q_minus = Ai + uij * eij - bij * nij

    alpha_ij = atan2(Aj[1] - Ai[1], Aj[0] - Ai[0])

    beta_plus = atan2(q_plus[1] - Ai[1], q_plus[0] - Ai[0])
    beta_minus = atan2(q_minus[1] - Ai[1], q_minus[0] - Ai[0])

    delta_plus = wrap_to_pi(beta_plus - alpha_ij)
    delta_minus = wrap_to_pi(beta_minus - alpha_ij)

    phi_ij = max(abs(delta_plus), abs(delta_minus))

    theta_min = normalize_0_2pi(alpha_ij - phi_ij)
    theta_max = normalize_0_2pi(alpha_ij + phi_ij)

    blocked_intervals = split_wrapped_interval(theta_min, theta_max)

    return PairBlockResult(
        i=i,
        j=j,
        ai=ai,
        aj=aj,
        dij=dij,
        alpha_ij=alpha_ij,
        phi_ij=phi_ij,
        q_plus=(float(q_plus[0]), float(q_plus[1])),
        q_minus=(float(q_minus[0]), float(q_minus[1])),
        blocked_intervals_0_2pi=blocked_intervals,
    )


def useful_angle_ranges_for_each_mast(masts, sphere_radius, tol=1e-12):
    n = len(masts)
    results = {}

    for i in range(n):
        pair_results = []
        blocked_intervals = []

        for j in range(n):
            if i == j:
                continue

            pr = pair_block_for_i_due_to_j(i, j, masts, sphere_radius, tol=tol)
            if pr is None:
                continue

            pair_results.append(pr)
            blocked_intervals.extend(pr.blocked_intervals_0_2pi)

        blocked_merged = merge_intervals(blocked_intervals, tol=tol)
        useful = complement_intervals(blocked_merged, 0.0, 2.0 * pi, tol=tol)

        results[i] = {
            "pair_results": pair_results,
            "blocked_intervals_raw": blocked_intervals,
            "blocked_intervals_merged": blocked_merged,
            "useful_intervals": useful,
        }

    return results


def rad_to_deg(x):
    return x * 180.0 / np.pi


def plot_interval_on_circle(ax, center, radius, interval, color="green", lw=4, npts=300, label=None):
    """
    Dibuja un intervalo angular [theta1, theta2] sobre una circunferencia.
    Se asume theta1 <= theta2 y ambos en [0, 2pi).
    """
    theta1, theta2 = interval
    t = np.linspace(theta1, theta2, npts)
    x = center[0] + radius * np.cos(t)
    y = center[1] + radius * np.sin(t)
    ax.plot(x, y, color=color, lw=lw, label=label)


def plot_all_circles_and_ranges(
    masts,
    sphere_radius,
    results,
    mast_index,
    show_blocked=True,
    show_useful=True,
    show_q_points=True,
    figsize=(9, 9)
):
    """
    Dibuja todas las circunferencias en planta y resalta, para un mástil específico,
    sus intervalos bloqueados y/o útiles.
    """
    fig, ax = plt.subplots(figsize=figsize)

    # 1) Dibujar todas las circunferencias base
    t = np.linspace(0, 2.0 * np.pi, 600)

    for k, m in enumerate(masts):
        ak = effective_radius(m.h, sphere_radius)
        x = m.x + ak * np.cos(t)
        y = m.y + ak * np.sin(t)
        ax.plot(x, y, color="lightgray", lw=1.5)
        ax.scatter(m.x, m.y, color="black", s=35, zorder=5)
        ax.text(m.x + 0.2, m.y + 0.2, f"A{k}", fontsize=11)

    # 2) Resaltar la circunferencia del mástil elegido
    mi = masts[mast_index]
    ai = effective_radius(mi.h, sphere_radius)
    x = mi.x + ai * np.cos(t)
    y = mi.y + ai * np.sin(t)
    ax.plot(x, y, color="steelblue", lw=2.5, label=f"Circunferencia mástil {mast_index}")

    # 3) Intervalos bloqueados unidos
    blocked = results[mast_index]["blocked_intervals_merged"]
    useful = results[mast_index]["useful_intervals"]

    first_blocked = True
    if show_blocked:
        for interval in blocked:
            plot_interval_on_circle(
                ax,
                center=(mi.x, mi.y),
                radius=ai,
                interval=interval,
                color="crimson",
                lw=5,
                label="Bloqueado" if first_blocked else None,
            )
            first_blocked = False

    first_useful = True
    if show_useful:
        for interval in useful:
            plot_interval_on_circle(
                ax,
                center=(mi.x, mi.y),
                radius=ai,
                interval=interval,
                color="limegreen",
                lw=5,
                label="Útil" if first_useful else None,
            )
            first_useful = False

    # 4) Dibujar los puntos Q del mástil elegido
    if show_q_points:
        for pr in results[mast_index]["pair_results"]:
            q_plus = pr.q_plus
            q_minus = pr.q_minus

            ax.scatter(q_plus[0], q_plus[1], color="darkorange", s=40, zorder=6)
            ax.scatter(q_minus[0], q_minus[1], color="darkorange", s=40, zorder=6)

            ax.text(q_plus[0] + 0.15, q_plus[1] + 0.15, f"Q+({mast_index},{pr.j})", fontsize=9)
            ax.text(q_minus[0] + 0.15, q_minus[1] - 0.35, f"Q-({mast_index},{pr.j})", fontsize=9)

            # Línea de referencia hacia el otro mástil
            mj = masts[pr.j]
            ax.plot([mi.x, mj.x], [mi.y, mj.y], linestyle="--", color="gray", lw=1)

    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.25)
    ax.set_title(f"Planta con ángulos útiles/bloqueados del mástil {mast_index}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend()
    plt.show()


def print_useful_intervals(results, in_degrees=True):
    """
    Imprime los intervalos útiles y bloqueados por mástil.
    """
    for i, data in results.items():
        print("=" * 70)
        print(f"MÁSTIL {i}")

        blocked = data["blocked_intervals_merged"]
        useful = data["useful_intervals"]

        if in_degrees:
            blocked_fmt = [(round(np.degrees(a), 2), round(np.degrees(b), 2)) for a, b in blocked]
            useful_fmt = [(round(np.degrees(a), 2), round(np.degrees(b), 2)) for a, b in useful]
            print("Bloqueados [grados]:", blocked_fmt)
            print("Útiles     [grados]:", useful_fmt)
        else:
            print("Bloqueados [rad]:", blocked)
            print("Útiles     [rad]:", useful)


def plot_multiple_masts_overlay(
    masts,
    sphere_radius,
    results,
    mast_indices=None,
    show_blocked=True,
    show_useful=True,
    show_q_points=False,
    figsize=(9, 9),
):
    fig, ax = plt.subplots(figsize=figsize)
    t = np.linspace(0, 2.0 * np.pi, 600)

    colors = ["steelblue", "darkorange", "purple", "teal", "brown"]

    if mast_indices is None:
        mast_indices = tuple(range(len(masts)))

    # Todas las circunferencias base
    for k, m in enumerate(masts):
        ak = effective_radius(m.h, sphere_radius)
        x = m.x + ak * np.cos(t)
        y = m.y + ak * np.sin(t)
        ax.plot(x, y, color="lightgray", lw=1.2)
        ax.scatter(m.x, m.y, color="black", s=30, zorder=5)
        ax.text(m.x + 0.2, m.y + 0.2, f"A{k}", fontsize=10)

    # Resaltados
    for idx_pos, mast_index in enumerate(mast_indices):
        color = colors[idx_pos % len(colors)]
        mi = masts[mast_index]
        ai = effective_radius(mi.h, sphere_radius)

        x = mi.x + ai * np.cos(t)
        y = mi.y + ai * np.sin(t)
        ax.plot(x, y, color=color, lw=2.4, label=f"Mástil {mast_index}")

        blocked = results[mast_index]["blocked_intervals_merged"]
        useful = results[mast_index]["useful_intervals"]

        if show_blocked:
            for interval in blocked:
                plot_interval_on_circle(
                    ax,
                    center=(mi.x, mi.y),
                    radius=ai,
                    interval=interval,
                    color="crimson",
                    lw=3,
                )

        if show_useful:
            for interval in useful:
                plot_interval_on_circle(
                    ax,
                    center=(mi.x, mi.y),
                    radius=ai,
                    interval=interval,
                    color="limegreen",
                    lw=3,
                )

        if show_q_points:
            for pr in results[mast_index]["pair_results"]:
                q_plus = pr.q_plus
                q_minus = pr.q_minus
                ax.scatter(q_plus[0], q_plus[1], color=color, s=25, zorder=6)
                ax.scatter(q_minus[0], q_minus[1], color=color, s=25, zorder=6)

    ax.set_title("Varios mástiles al mismo tiempo")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.25)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend()
    plt.tight_layout()
    plt.show()


import plotly.graph_objects as go


def rolling_sphere_z(u, a, R):
    """
    Perfil generatriz:
        z(u) = R - sqrt(R^2 - (u - a)^2)
    con 0 <= u <= a

    - En u = 0  -> z = altura del mástil (si a fue calculado con esa altura)
    - En u = a  -> z = 0
    """
    inside = R**2 - (u - a)**2
    inside = np.maximum(inside, 0.0)
    return R - np.sqrt(inside)


def build_partial_surface_for_interval(mast, sphere_radius, interval, nr=45, nt=80):
    """
    Construye una porción de superficie 3D solo en un intervalo angular útil.
    """
    a = effective_radius(mast.h, sphere_radius)

    if a <= 1e-12:
        return None

    theta1, theta2 = interval
    u = np.linspace(0.0, a, nr)
    theta = np.linspace(theta1, theta2, nt)

    U, TH = np.meshgrid(u, theta, indexing="xy")

    X = mast.x + U * np.cos(TH)
    Y = mast.y + U * np.sin(TH)
    Z = rolling_sphere_z(U, a, sphere_radius)

    return X, Y, Z


def add_mast_to_figure(fig, mast, idx, sphere_radius, results,
                       show_mast_line=True, show_base_circle=True):
    """
    Agrega al gráfico:
    - el segmento vertical del mástil
    - la circunferencia base en z=0
    - las superficies 3D solo en ángulos útiles
    """
    a = effective_radius(mast.h, sphere_radius)

    # Línea del mástil
    if show_mast_line:
        fig.add_trace(go.Scatter3d(
            x=[mast.x, mast.x],
            y=[mast.y, mast.y],
            z=[0.0, mast.h],
            mode="lines+markers+text",
            text=["", f"M{idx}"],
            textposition="top center",
            line=dict(width=8),
            marker=dict(size=4),
            name=f"Mástil {idx}"
        ))

    # Circunferencia base completa en z=0
    if show_base_circle and a > 1e-12:
        t = np.linspace(0.0, 2.0 * np.pi, 240)
        xb = mast.x + a * np.cos(t)
        yb = mast.y + a * np.sin(t)
        zb = np.zeros_like(t)

        fig.add_trace(go.Scatter3d(
            x=xb, y=yb, z=zb,
            mode="lines",
            line=dict(width=3, dash="dot"),
            name=f"Base M{idx}"
        ))

    # Superficies solo en los ángulos útiles
    useful_intervals = results[idx]["useful_intervals"]

    for k, interval in enumerate(useful_intervals):
        surface_data = build_partial_surface_for_interval(
            mast=mast,
            sphere_radius=sphere_radius,
            interval=interval,
            nr=45,
            nt=80
        )

        if surface_data is None:
            continue

        X, Y, Z = surface_data

        fig.add_trace(go.Surface(
            x=X,
            y=Y,
            z=Z,
            showscale=False,
            opacity=0.82,
            name=f"M{idx} útil {k+1}",
            hovertemplate=(
                f"Mástil {idx}<br>"
                "x=%{x:.2f}<br>"
                "y=%{y:.2f}<br>"
                "z=%{z:.2f}<extra></extra>"
            )
        ))


def dibujar_aristas_Q(fig, masts, results, S, n_pts=200):
    """
    Dibuja, sobre el gráfico de superficies de mástil solo, las aristas
    correspondientes a los puntos Q útiles para cada mástil.

    Cada arista sigue EXACTAMENTE la misma lógica geométrica de la
    superficie de esfera rodante del mástil:
        r in [0, a]
        x = x_m + r cos(theta_q)
        y = y_m + r sin(theta_q)
        z = rolling_sphere_z(r, a, S)
    """
    for i, data in results.items():
        mi = masts[i]
        ai = effective_radius(mi.h, S)

        if ai <= 1e-12:
            continue

        for pr in data["pair_results"]:
            for q in [pr.q_plus, pr.q_minus]:
                angle_q_i = normalize_0_2pi(atan2(q[1] - mi.y, q[0] - mi.x))

                is_useful = any(
                    low - 1e-9 <= angle_q_i <= high + 1e-9
                    for low, high in data["useful_intervals"]
                )

                if not is_useful:
                    continue

                # Arista radial exacta sobre la superficie del mástil solo
                r_vals = np.linspace(0.0, ai, n_pts)
                x1 = mi.x + r_vals * np.cos(angle_q_i)
                y1 = mi.y + r_vals * np.sin(angle_q_i)
                z1 = rolling_sphere_z(r_vals, ai, S)

                fig.add_trace(go.Scatter3d(
                    x=x1,
                    y=y1,
                    z=z1,
                    mode='lines',
                    line=dict(color='red', width=4),
                    showlegend=False
                ))


def plot_interactive_3d_rolling_surfaces(masts, sphere_radius, results):
    fig = go.Figure()

    for i, mast in enumerate(masts):
        add_mast_to_figure(
            fig=fig,
            mast=mast,
            idx=i,
            sphere_radius=sphere_radius,
            results=results,
            show_mast_line=True,
            show_base_circle=True
        )

    # =====================================================
    # Aristas Q sobre las superficies de mástil solo
    # =====================================================
    dibujar_aristas_Q(fig, masts, results, sphere_radius, n_pts=200)

    # Plano z = 0
    all_x = [m.x for m in masts]
    all_y = [m.y for m in masts]
    max_a = max(effective_radius(m.h, sphere_radius) for m in masts)

    xmin = min(all_x) - max_a - 5
    xmax = max(all_x) + max_a + 5
    ymin = min(all_y) - max_a - 5
    ymax = max(all_y) + max_a + 5

    Xg, Yg = np.meshgrid(
        np.linspace(xmin, xmax, 2),
        np.linspace(ymin, ymax, 2)
    )
    Zg = np.zeros_like(Xg)

    fig.add_trace(go.Surface(
        x=Xg, y=Yg, z=Zg,
        showscale=False,
        opacity=0.20,
        name="Plano z=0",
        hoverinfo="skip"
    ))

    fig.update_layout(
        title=f"Superficies 3D de esfera rodante (solo ángulos útiles) - R = {sphere_radius}",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="data"
        ),
        height=750
    )

    fig.show()


def run_model(mast_inputs, sphere_radius):
    """
    Usa directamente la única sección de entradas definida al inicio:
      - mast_inputs: lista de tuplas (x, y, h)
      - sphere_radius: radio de la esfera
    """
    masts = [Mast(x, y, h) for x, y, h in mast_inputs]
    results = useful_angle_ranges_for_each_mast(masts, sphere_radius)

    print_useful_intervals(results, in_degrees=True)
    plot_interactive_3d_rolling_surfaces(masts, sphere_radius, results)

    return masts, results


import itertools


import numpy as np


import plotly.graph_objects as go


def build_candidate_nodes(all_points):
    """
    Construye los nodos candidatos:
    - puntas de mástiles -> z = h
    - puntos Q           -> z = 0
    """
    real_masts = [p for p in all_points if p.h > 1e-12]
    q_points   = [p for p in all_points if abs(p.h) < 1e-12]

    tri_nodes = []

    for i, m in enumerate(real_masts):
        tri_nodes.append({
            "type": "mast_top",
            "label": f"M{i}",
            "x": float(m.x),
            "y": float(m.y),
            "z": float(m.h),
            "obj": m
        })

    for k, q in enumerate(q_points):
        tri_nodes.append({
            "type": "Q",
            "label": f"Q{k}",
            "x": float(q.x),
            "y": float(q.y),
            "z": 0.0,
            "obj": q
        })

    return tri_nodes


def area_xy_of_triangle(n1, n2, n3):
    """
    Área en planta (XY) del triángulo.
    Sirve para detectar ternas degeneradas/colineales en XY.
    """
    x1, y1 = n1["x"], n1["y"]
    x2, y2 = n2["x"], n2["y"]
    x3, y3 = n3["x"], n3["y"]

    return 0.5 * abs(
        (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)
    )


def triangle_is_on_ground(n1, n2, n3, z_tol=1e-12):
    """
    True si los tres vértices están en z=0.
    """
    return (
        abs(n1["z"]) <= z_tol and
        abs(n2["z"]) <= z_tol and
        abs(n3["z"]) <= z_tol
    )


def generate_all_candidate_triangles(tri_nodes, area_tol=1e-9, z_tol=1e-12):
    """
    Genera todas las combinaciones de 3 nodos y descarta:
    1) ternas degeneradas en planta
    2) triángulos totalmente sobre el suelo (Q-Q-Q)
    """
    candidate_triangles = []
    degenerate_count = 0
    ground_count = 0

    for idxs in itertools.combinations(range(len(tri_nodes)), 3):
        i, j, k = idxs
        n1, n2, n3 = tri_nodes[i], tri_nodes[j], tri_nodes[k]

        # 1) descartar degenerados en XY
        area_xy = area_xy_of_triangle(n1, n2, n3)
        if area_xy <= area_tol:
            degenerate_count += 1
            continue

        # 2) descartar triángulos totalmente en el suelo
        if triangle_is_on_ground(n1, n2, n3, z_tol=z_tol):
            ground_count += 1
            continue

        candidate_triangles.append({
            "indices": (i, j, k),
            "labels": (n1["label"], n2["label"], n3["label"]),
            "nodes": (n1, n2, n3),
            "area_xy": area_xy
        })

    return candidate_triangles, degenerate_count, ground_count


def plot_all_candidate_triangles(all_points):
    """
    Dibuja:
    - mástiles
    - puntos Q
    - TODAS las ternas válidas como triángulos candidatos,
      excluyendo las que quedan totalmente sobre el suelo
    """
    tri_nodes = build_candidate_nodes(all_points)
    candidate_triangles, degenerate_count, ground_count = generate_all_candidate_triangles(tri_nodes)

    print(f"Número total de nodos                  : {len(tri_nodes)}")
    print(f"Número de ternas degeneradas en XY    : {degenerate_count}")
    print(f"Número de triángulos sobre el suelo   : {ground_count}")
    print(f"Número de triángulos candidatos útiles: {len(candidate_triangles)}")

    fig = go.Figure()

    # ---------------------------------
    # 1) Dibujar todas las aristas de todos los triángulos candidatos
    # ---------------------------------
    for tri_data in candidate_triangles:
        n1, n2, n3 = tri_data["nodes"]
        labels = tri_data["labels"]

        fig.add_trace(go.Scatter3d(
            x=[n1["x"], n2["x"]],
            y=[n1["y"], n2["y"]],
            z=[n1["z"], n2["z"]],
            mode="lines",
            line=dict(color="gray", width=3),
            showlegend=False,
            hoverinfo="text",
            text=[f"{labels[0]} - {labels[1]}", f"{labels[0]} - {labels[1]}"]
        ))

        fig.add_trace(go.Scatter3d(
            x=[n2["x"], n3["x"]],
            y=[n2["y"], n3["y"]],
            z=[n2["z"], n3["z"]],
            mode="lines",
            line=dict(color="gray", width=3),
            showlegend=False,
            hoverinfo="text",
            text=[f"{labels[1]} - {labels[2]}", f"{labels[1]} - {labels[2]}"]
        ))

        fig.add_trace(go.Scatter3d(
            x=[n3["x"], n1["x"]],
            y=[n3["y"], n1["y"]],
            z=[n3["z"], n1["z"]],
            mode="lines",
            line=dict(color="gray", width=3),
            showlegend=False,
            hoverinfo="text",
            text=[f"{labels[2]} - {labels[0]}", f"{labels[2]} - {labels[0]}"]
        ))

    # ---------------------------------
    # 2) Dibujar puntos Q
    # ---------------------------------
    q_nodes = [n for n in tri_nodes if n["type"] == "Q"]
    if q_nodes:
        fig.add_trace(go.Scatter3d(
            x=[n["x"] for n in q_nodes],
            y=[n["y"] for n in q_nodes],
            z=[0.0 for _ in q_nodes],
            mode="markers+text",
            marker=dict(size=6, color="orange"),
            text=[n["label"] for n in q_nodes],
            textposition="top center",
            name="Puntos Q"
        ))

    # ---------------------------------
    # 3) Dibujar mástiles
    # ---------------------------------
    mast_nodes = [n for n in tri_nodes if n["type"] == "mast_top"]

    for n in mast_nodes:
        fig.add_trace(go.Scatter3d(
            x=[n["x"], n["x"]],
            y=[n["y"], n["y"]],
            z=[0.0, n["z"]],
            mode="lines",
            line=dict(color="blue", width=8),
            showlegend=False,
            hoverinfo="skip"
        ))

        fig.add_trace(go.Scatter3d(
            x=[n["x"]],
            y=[n["y"]],
            z=[n["z"]],
            mode="markers+text",
            marker=dict(size=5, color="black"),
            text=[n["label"]],
            textposition="top center",
            name=n["label"]
        ))

    # ---------------------------------
    # 4) Plano de suelo
    # ---------------------------------
    xy = np.array([[n["x"], n["y"]] for n in tri_nodes], dtype=float)
    xmin, ymin = np.min(xy, axis=0) - 5
    xmax, ymax = np.max(xy, axis=0) + 5

    Xg, Yg = np.meshgrid(
        np.linspace(xmin, xmax, 2),
        np.linspace(ymin, ymax, 2)
    )
    Zg = np.zeros_like(Xg)

    fig.add_trace(go.Surface(
        x=Xg,
        y=Yg,
        z=Zg,
        showscale=False,
        opacity=0.10,
        hoverinfo="skip",
        name="Suelo"
    ))

    # ---------------------------------
    # 5) Layout
    # ---------------------------------
    fig.update_layout(
        title="Todos los triángulos candidatos (sin triángulos totalmente en el suelo)",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="data"
        ),
        height=850
    )

    fig.show()

    return tri_nodes, candidate_triangles


import numpy as np


import plotly.graph_objects as go


def classify_triangle_type(tri_data):
    """
    Retorna el tipo del triángulo según sus nodos:
    - M-M-M
    - M-M-Q
    - M-Q-Q
    - Q-Q-Q
    """
    node_types = [n["type"] for n in tri_data["nodes"]]

    nM = sum(1 for t in node_types if t == "mast_top")
    nQ = sum(1 for t in node_types if t == "Q")

    if nM == 3:
        return "M-M-M"
    elif nM == 2 and nQ == 1:
        return "M-M-Q"
    elif nM == 1 and nQ == 2:
        return "M-Q-Q"
    elif nQ == 3:
        return "Q-Q-Q"
    else:
        return "UNKNOWN"


def filter_out_mqq_triangles(triangles):
    """
    Descarta todos los triángulos tipo M-Q-Q.

    Motivo:
    Estos triángulos no representan una superficie útil del modelo,
    y además no deben competir contra la superficie de mástil solo
    en filtros posteriores.
    """
    kept = []
    removed = []

    for tri_data in triangles:
        tri_type = classify_triangle_type(tri_data)

        tri_ext = dict(tri_data)
        tri_ext["triangle_type"] = tri_type

        if tri_type == "M-Q-Q":
            removed.append(tri_ext)
        else:
            kept.append(tri_ext)

    return kept, removed


def plot_triangles_after_type_filter(
    tri_nodes,
    kept_triangles,
    masts=None,
    results=None,
    sphere_radius=None,
    title_suffix="",
    show_single_mast_reference=True
):
    fig = go.Figure()

    # ---------------------------------
    # 1) Triángulos conservados
    # ---------------------------------
    for tri_data in kept_triangles:
        n1, n2, n3 = tri_data["nodes"]
        labels = tri_data["labels"]

        for a, b in [(n1, n2), (n2, n3), (n3, n1)]:
            fig.add_trace(go.Scatter3d(
                x=[a["x"], b["x"]],
                y=[a["y"], b["y"]],
                z=[a["z"], b["z"]],
                mode="lines",
                line=dict(color="gray", width=3),
                showlegend=False,
                hoverinfo="text",
                text=[f"{labels}", f"{labels}"]
            ))

    # ---------------------------------
    # 2) Puntos Q
    # ---------------------------------
    q_nodes = [n for n in tri_nodes if n["type"] == "Q"]

    if q_nodes:
        fig.add_trace(go.Scatter3d(
            x=[n["x"] for n in q_nodes],
            y=[n["y"] for n in q_nodes],
            z=[0.0 for _ in q_nodes],
            mode="markers+text",
            marker=dict(size=6, color="orange"),
            text=[n["label"] for n in q_nodes],
            textposition="top center",
            name="Q"
        ))

    # ---------------------------------
    # 3) Mástiles
    # ---------------------------------
    mast_nodes = [n for n in tri_nodes if n["type"] == "mast_top"]

    for n in mast_nodes:
        fig.add_trace(go.Scatter3d(
            x=[n["x"], n["x"]],
            y=[n["y"], n["y"]],
            z=[0.0, n["z"]],
            mode="lines",
            line=dict(color="blue", width=8),
            showlegend=False,
            hoverinfo="skip"
        ))

        fig.add_trace(go.Scatter3d(
            x=[n["x"]],
            y=[n["y"]],
            z=[n["z"]],
            mode="markers+text",
            marker=dict(size=5, color="black"),
            text=[n["label"]],
            textposition="top center",
            name=n["label"]
        ))

    # ---------------------------------
    # 4) Referencia de mástil solo
    #    Se muestra solo si ya existen masts, results y S.
    # ---------------------------------
    if (
        show_single_mast_reference
        and masts is not None
        and results is not None
        and sphere_radius is not None
    ):
        for i, mast in enumerate(masts):
            ai = effective_radius(mast.h, sphere_radius)
            useful_intervals = results[i]["useful_intervals"]

            for th1, th2 in useful_intervals:
                theta = np.linspace(th1, th2, 80)
                r = np.linspace(0.0, ai, 20)

                TH, RR = np.meshgrid(theta, r, indexing="xy")

                X = mast.x + RR * np.cos(TH)
                Y = mast.y + RR * np.sin(TH)
                Z = np.zeros_like(X)

                fig.add_trace(go.Surface(
                    x=X,
                    y=Y,
                    z=Z,
                    showscale=False,
                    opacity=0.10,
                    hoverinfo="skip",
                    name=f"Referencia mástil solo M{i}"
                ))

    # ---------------------------------
    # 5) Plano base
    # ---------------------------------
    xy = np.array([[n["x"], n["y"]] for n in tri_nodes], dtype=float)

    xmin, ymin = xy.min(axis=0) - 5
    xmax, ymax = xy.max(axis=0) + 5

    Xg, Yg = np.meshgrid(
        np.linspace(xmin, xmax, 2),
        np.linspace(ymin, ymax, 2)
    )

    fig.add_trace(go.Surface(
        x=Xg,
        y=Yg,
        z=np.zeros_like(Xg),
        opacity=0.08,
        showscale=False,
        hoverinfo="skip",
        name="Suelo"
    ))

    fig.update_layout(
        title=f"Segundo filtro: triángulos tras eliminar M-Q-Q{title_suffix}",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="data"
        ),
        height=850
    )

    fig.show()


import numpy as np


import plotly.graph_objects as go


def angular_diff(a, b):
    d = abs(a - b) % (2*np.pi)
    return min(d, 2*np.pi - d)


def get_all_useful_edges(mast_index, results_obj):
    edges = []

    for a, b in results_obj[mast_index]["useful_intervals"]:
        edges.append(normalize_0_2pi(a))
        edges.append(normalize_0_2pi(b))

    return edges


def direction_angle_from_mast_to_q(q_node, mast_node):
    dx = q_node["x"] - mast_node["x"]
    dy = q_node["y"] - mast_node["y"]

    return normalize_0_2pi(np.arctan2(dy, dx))


def node_matches_surviving_original_edge(
    q_node,
    mast_node,
    mast_index,
    original_results,
    updated_results,
    angle_tol=1e-4
):
    theta = direction_angle_from_mast_to_q(q_node, mast_node)

    original_edges = get_all_useful_edges(mast_index, original_results)
    updated_edges = get_all_useful_edges(mast_index, updated_results)

    for original_edge in original_edges:
        if angular_diff(theta, original_edge) > angle_tol:
            continue

        for updated_edge in updated_edges:
            if angular_diff(original_edge, updated_edge) <= angle_tol:
                return True, original_edge

    return False, None


def filter_mmq_by_surviving_original_useful_edges(
    triangles,
    original_results,
    updated_results,
    angle_tol=1e-4
):
    kept = []
    removed = []

    for tri in triangles:
        tri_type = tri.get("triangle_type", classify_triangle_type(tri))

        tri_ext = dict(tri)
        tri_ext["triangle_type"] = tri_type

        if tri_type != "M-M-Q":
            kept.append(tri_ext)
            continue

        mast_nodes = [n for n in tri["nodes"] if n["type"] == "mast_top"]
        q_nodes = [n for n in tri["nodes"] if n["type"] == "Q"]

        if len(mast_nodes) != 2 or len(q_nodes) != 1:
            tri_ext["removed_reason"] = "M-M-Q inválido"
            removed.append(tri_ext)
            continue

        q_node = q_nodes[0]
        m1, m2 = mast_nodes

        idx1 = int(m1["label"].replace("M", ""))
        idx2 = int(m2["label"].replace("M", ""))

        theta1 = direction_angle_from_mast_to_q(q_node, m1)
        theta2 = direction_angle_from_mast_to_q(q_node, m2)

        ok1, edge1 = node_matches_surviving_original_edge(
            q_node=q_node,
            mast_node=m1,
            mast_index=idx1,
            original_results=original_results,
            updated_results=updated_results,
            angle_tol=angle_tol
        )

        ok2, edge2 = node_matches_surviving_original_edge(
            q_node=q_node,
            mast_node=m2,
            mast_index=idx2,
            original_results=original_results,
            updated_results=updated_results,
            angle_tol=angle_tol
        )

        tri_ext["mmq_theta_m1_rad"] = theta1
        tri_ext["mmq_theta_m2_rad"] = theta2
        tri_ext["mmq_theta_m1_deg"] = np.degrees(theta1)
        tri_ext["mmq_theta_m2_deg"] = np.degrees(theta2)

        tri_ext["mmq_q_edge_match_m1"] = ok1
        tri_ext["mmq_q_edge_match_m2"] = ok2
        tri_ext["mmq_q_edge_info_m1"] = edge1
        tri_ext["mmq_q_edge_info_m2"] = edge2

        if ok1 and ok2:
            kept.append(tri_ext)
        else:
            reasons = []

            if not ok1:
                reasons.append(
                    f"{m1['label']}->{q_node['label']} no coincide con borde original vigente"
                )

            if not ok2:
                reasons.append(
                    f"{m2['label']}->{q_node['label']} no coincide con borde original vigente"
                )

            tri_ext["removed_reason"] = " | ".join(reasons)
            removed.append(tri_ext)

    return kept, removed


def build_active_tri_nodes_from_triangles(tri_nodes, triangles):
    """
    Conserva:
    - todos los mástiles;
    - solo los puntos Q que aparecen en los triángulos conservados.

    Esto elimina puntos Q huérfanos después del filtro M-M-Q.
    """
    active_labels = set()

    for tri in triangles:
        for n in tri["nodes"]:
            active_labels.add(n["label"])

    active_tri_nodes = [
        n for n in tri_nodes
        if n["type"] == "mast_top" or n["label"] in active_labels
    ]

    return active_tri_nodes


def plot_triangles_after_mmq_edge_filter(
    tri_nodes,
    kept_triangles,
    masts,
    results,
    sphere_radius,
    show_single_mast_reference=True
):
    fig = go.Figure()

    # ---------------------------------
    # 1) Triángulos conservados
    # ---------------------------------
    for tri_data in kept_triangles:
        n1, n2, n3 = tri_data["nodes"]
        labels = tri_data["labels"]
        tri_type = tri_data.get("triangle_type", classify_triangle_type(tri_data))

        hover_txt = f"{labels} | {tri_type}"

        for a, b in [(n1, n2), (n2, n3), (n3, n1)]:
            fig.add_trace(go.Scatter3d(
                x=[a["x"], b["x"]],
                y=[a["y"], b["y"]],
                z=[a["z"], b["z"]],
                mode="lines",
                line=dict(color="gray", width=4),
                showlegend=False,
                hoverinfo="text",
                text=[hover_txt, hover_txt]
            ))

    # ---------------------------------
    # 2) Puntos Q activos
    # ---------------------------------
    q_nodes = [n for n in tri_nodes if n["type"] == "Q"]

    if q_nodes:
        fig.add_trace(go.Scatter3d(
            x=[n["x"] for n in q_nodes],
            y=[n["y"] for n in q_nodes],
            z=[0.0 for _ in q_nodes],
            mode="markers+text",
            marker=dict(size=6, color="orange"),
            text=[n["label"] for n in q_nodes],
            textposition="top center",
            name="Q activos"
        ))

    # ---------------------------------
    # 3) Mástiles
    # ---------------------------------
    mast_nodes = [n for n in tri_nodes if n["type"] == "mast_top"]

    for n in mast_nodes:
        fig.add_trace(go.Scatter3d(
            x=[n["x"], n["x"]],
            y=[n["y"], n["y"]],
            z=[0.0, n["z"]],
            mode="lines",
            line=dict(color="blue", width=8),
            showlegend=False,
            hoverinfo="skip"
        ))

        fig.add_trace(go.Scatter3d(
            x=[n["x"]],
            y=[n["y"]],
            z=[n["z"]],
            mode="markers+text",
            marker=dict(size=5, color="black"),
            text=[n["label"]],
            textposition="top center",
            name=n["label"]
        ))

    # ---------------------------------
    # 4) Sombras de mástil solo actualizadas
    # ---------------------------------
    if show_single_mast_reference:
        for i, mast in enumerate(masts):
            ai = effective_radius(mast.h, sphere_radius)
            useful_intervals = results[i]["useful_intervals"]

            for th1, th2 in useful_intervals:
                theta = np.linspace(th1, th2, 80)
                r = np.linspace(0.0, ai, 20)

                TH, RR = np.meshgrid(theta, r, indexing="xy")

                X = mast.x + RR * np.cos(TH)
                Y = mast.y + RR * np.sin(TH)
                Z = np.zeros_like(X)

                fig.add_trace(go.Surface(
                    x=X,
                    y=Y,
                    z=Z,
                    showscale=False,
                    opacity=0.10,
                    hoverinfo="skip",
                    name=f"Mástil solo M{i}"
                ))

    # ---------------------------------
    # 5) Plano base
    # ---------------------------------
    xy = np.array([[n["x"], n["y"]] for n in tri_nodes], dtype=float)

    xmin, ymin = xy.min(axis=0) - 5
    xmax, ymax = xy.max(axis=0) + 5

    Xg, Yg = np.meshgrid(
        np.linspace(xmin, xmax, 2),
        np.linspace(ymin, ymax, 2)
    )

    fig.add_trace(go.Surface(
        x=Xg,
        y=Yg,
        z=np.zeros_like(Xg),
        opacity=0.08,
        showscale=False,
        hoverinfo="skip",
        name="Suelo"
    ))

    fig.update_layout(
        title="Tercer filtro: M-M-Q usando solo bordes originales vigentes",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="data"
        ),
        height=850
    )

    fig.show()


import numpy as np


import plotly.graph_objects as go


from itertools import combinations, product


from collections import defaultdict


MIN_CYCLE_LEN_4 = 3


MAX_CYCLE_LEN_4 = 8


RADIAL_TOL_4 = 0.35


ANGLE_TOL_4 = 1e-3


MAX_CYCLE_AREA_FACTOR_4 = 3.0


MIN_CYCLE_AREA_FACTOR_4 = 1e-7


REQUIRE_CENTROID_INSIDE_MAST_HULL_4 = True


REQUIRE_NO_MAST_INSIDE_4 = True


REQUIRE_CENTROID_UNCOVERED_4 = True


MAX_SIDE_ARC_DEG_4 = 180.0


ARC_SAMPLE_N_4 = 21


OTHER_MAST_COVER_MARGIN_4 = 1e-6


SHOW_REMOVED_CLOSED_CYCLES_4 = True


def norm_0_2pi_4(theta):
    return float(theta % (2*np.pi))


def classify_triangle_type_4(tri_data):
    if "classify_triangle_type" in globals():
        return classify_triangle_type(tri_data)

    node_types = [n["type"] for n in tri_data["nodes"]]
    nM = sum(1 for t in node_types if t == "mast_top")
    nQ = sum(1 for t in node_types if t == "Q")

    if nM == 3:
        return "M-M-M"
    elif nM == 2 and nQ == 1:
        return "M-M-Q"
    elif nM == 1 and nQ == 2:
        return "M-Q-Q"
    elif nQ == 3:
        return "Q-Q-Q"
    else:
        return "UNKNOWN"


def copy_results_robust_4(results_obj):
    if isinstance(results_obj, dict):
        copied = {}

        for k, r in results_obj.items():
            r_new = dict(r)
            r_new["useful_intervals"] = list(r.get("useful_intervals", []))
            copied[k] = r_new

        return copied

    copied = []

    for r in results_obj:
        r_new = dict(r)
        r_new["useful_intervals"] = list(r.get("useful_intervals", []))
        copied.append(r_new)

    return copied


def get_result_by_mast_4(results_obj, mast_idx):
    return results_obj[mast_idx]


def angle_mast_to_q_4(mast, q_node):
    return norm_0_2pi_4(
        np.arctan2(
            q_node["y"] - mast.y,
            q_node["x"] - mast.x
        )
    )


def dist_xy_4(p, q):
    return float(np.hypot(p[0] - q[0], p[1] - q[1]))


def dist_mast_q_xy_4(mast, q_node):
    return float(
        np.hypot(
            q_node["x"] - mast.x,
            q_node["y"] - mast.y
        )
    )


def arc_width_ccw_4(theta_a, theta_b):
    theta_a = norm_0_2pi_4(theta_a)
    theta_b = norm_0_2pi_4(theta_b)

    if theta_b < theta_a:
        theta_b += 2*np.pi

    return theta_b - theta_a


def split_ccw_arc_to_intervals_4(theta_a, theta_b, min_width=1e-9):
    theta_a = norm_0_2pi_4(theta_a)
    theta_b = norm_0_2pi_4(theta_b)

    if theta_b < theta_a:
        theta_b += 2*np.pi

    if theta_b - theta_a <= min_width:
        return []

    if theta_b <= 2*np.pi:
        return [(theta_a, theta_b)]

    return [
        (theta_a, 2*np.pi),
        (0.0, theta_b - 2*np.pi)
    ]


def normalize_interval_parts_4(interval, min_width=1e-9):
    a, b = interval

    a = norm_0_2pi_4(a)
    b = norm_0_2pi_4(b)

    if a <= b:
        if b - a > min_width:
            return [(a, b)]
        return []

    parts = []

    if 2*np.pi - a > min_width:
        parts.append((a, 2*np.pi))

    if b > min_width:
        parts.append((0.0, b))

    return parts


def theta_in_interval_4(theta, interval, tol=1e-9):
    theta = norm_0_2pi_4(theta)

    for a, b in normalize_interval_parts_4(interval):
        if a - tol <= theta <= b + tol:
            return True

    return False


def theta_in_any_interval_4(theta, intervals, tol=1e-9):
    return any(
        theta_in_interval_4(theta, interval, tol=tol)
        for interval in intervals
    )


def subtract_interval_1d_4(base_interval, cut_interval, min_width=1e-8):
    a, b = base_interval
    c, d = cut_interval

    if d <= a or c >= b:
        return [(a, b)]

    pieces = []

    left = (a, max(a, c))
    right = (min(b, d), b)

    if left[1] - left[0] > min_width:
        pieces.append(left)

    if right[1] - right[0] > min_width:
        pieces.append(right)

    return pieces


def apply_cut_intervals_to_results_4(updated_results, mast_idx, cut_intervals):
    old_intervals = get_result_by_mast_4(
        updated_results,
        mast_idx
    )["useful_intervals"]

    expanded_old = []

    for interval in old_intervals:
        expanded_old.extend(normalize_interval_parts_4(interval))

    new_intervals = expanded_old

    for cut_interval in cut_intervals:
        cut_parts = normalize_interval_parts_4(cut_interval)

        for cut_piece in cut_parts:
            temp = []

            for base_interval in new_intervals:
                temp.extend(
                    subtract_interval_1d_4(
                        base_interval,
                        cut_piece
                    )
                )

            new_intervals = temp

    get_result_by_mast_4(
        updated_results,
        mast_idx
    )["useful_intervals"] = new_intervals


def polygon_area_xy_4(points):
    pts = np.asarray(points, dtype=float)

    x = pts[:, 0]
    y = pts[:, 1]

    return 0.5 * float(
        np.dot(x, np.roll(y, -1)) -
        np.dot(y, np.roll(x, -1))
    )


def polygon_centroid_xy_4(points):
    pts = np.asarray(points, dtype=float)
    area = polygon_area_xy_4(points)

    if abs(area) < 1e-12:
        return np.mean(pts, axis=0)

    x = pts[:, 0]
    y = pts[:, 1]

    cross = x*np.roll(y, -1) - np.roll(x, -1)*y

    cx = np.sum((x + np.roll(x, -1))*cross) / (6*area)
    cy = np.sum((y + np.roll(y, -1))*cross) / (6*area)

    return np.array([cx, cy], dtype=float)


def point_in_polygon_xy_4(point, polygon):
    x, y = point
    pts = np.asarray(polygon, dtype=float)

    inside = False
    j = len(pts) - 1

    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]

        cond = (yi > y) != (yj > y)

        if cond:
            x_cross = (xj - xi)*(y - yi)/(yj - yi + 1e-15) + xi

            if x < x_cross:
                inside = not inside

        j = i

    return inside


def ccw_4(a, b, c):
    return (c[1] - a[1])*(b[0] - a[0]) > (b[1] - a[1])*(c[0] - a[0])


def segments_intersect_4(a, b, c, d):
    return (
        ccw_4(a, c, d) != ccw_4(b, c, d)
        and
        ccw_4(a, b, c) != ccw_4(a, b, d)
    )


def polygon_self_intersects_4(points):
    pts = np.asarray(points, dtype=float)
    n = len(pts)

    for i in range(n):
        a = pts[i]
        b = pts[(i + 1) % n]

        for j in range(i + 1, n):
            if j == i:
                continue

            if j == (i + 1) % n:
                continue

            if (j + 1) % n == i:
                continue

            c = pts[j]
            d = pts[(j + 1) % n]

            if segments_intersect_4(a, b, c, d):
                return True

    return False


def order_q_labels_as_polygon_4(q_labels, q_by_label):
    pts = np.array(
        [
            [q_by_label[q]["x"], q_by_label[q]["y"]]
            for q in q_labels
        ],
        dtype=float
    )

    center = pts.mean(axis=0)

    ang = np.arctan2(
        pts[:, 1] - center[1],
        pts[:, 0] - center[0]
    )

    order = np.argsort(ang)

    return [q_labels[i] for i in order]


def canonical_cycle_4(cycle):
    cycle = list(cycle)
    n = len(cycle)

    candidates = []

    for i in range(n):
        candidates.append(tuple(cycle[i:] + cycle[:i]))

    rev = list(reversed(cycle))

    for i in range(n):
        candidates.append(tuple(rev[i:] + rev[:i]))

    return min(candidates)


def convex_hull_xy_4(points):
    pts = sorted(set((float(x), float(y)) for x, y in points))

    if len(pts) <= 1:
        return pts

    def cross(o, a, b):
        return (
            (a[0] - o[0])*(b[1] - o[1])
            -
            (a[1] - o[1])*(b[0] - o[0])
        )

    lower = []

    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()

        lower.append(p)

    upper = []

    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()

        upper.append(p)

    return lower[:-1] + upper[:-1]


def point_in_or_on_polygon_xy_4(point, polygon, tol=1e-9):
    if point_in_polygon_xy_4(point, polygon):
        return True

    p = np.asarray(point, dtype=float)
    pts = np.asarray(polygon, dtype=float)

    for i in range(len(pts)):
        a = pts[i]
        b = pts[(i + 1) % len(pts)]

        ab = b - a
        ap = p - a

        den = np.dot(ab, ab)

        if den <= 1e-15:
            continue

        t = np.clip(np.dot(ap, ab) / den, 0.0, 1.0)
        proj = a + t*ab

        if np.linalg.norm(p - proj) <= tol:
            return True

    return False


def point_covered_by_any_other_mast_4(
    x,
    y,
    masts,
    sphere_radius,
    excluded_mast_idx,
    margin=1e-6
):
    for j, mast in enumerate(masts):
        if j == excluded_mast_idx:
            continue

        aj = effective_radius(mast.h, sphere_radius)
        d = np.hypot(x - mast.x, y - mast.y)

        if d < aj - margin:
            return True

    return False


def sample_arc_points_4(mast, theta_a, theta_b, n=21):
    width = arc_width_ccw_4(theta_a, theta_b)
    theta_vals = theta_a + np.linspace(0.0, width, n)
    theta_vals = np.array([norm_0_2pi_4(t) for t in theta_vals])

    return theta_vals


def arc_is_inside_useful_intervals_4(
    theta_a,
    theta_b,
    useful_intervals,
    angle_tol=1e-3,
    n=21
):
    theta_vals = sample_arc_points_4(
        mast=None,
        theta_a=theta_a,
        theta_b=theta_b,
        n=n
    )

    for th in theta_vals:
        if not theta_in_any_interval_4(
            th,
            useful_intervals,
            tol=angle_tol
        ):
            return False

    return True


def arc_has_free_side_4(
    mast_idx,
    mast,
    theta_a,
    theta_b,
    masts,
    sphere_radius,
    n=21,
    margin=1e-6
):
    """
    Verifica que el arco Q-Q sobre un mástil sea frontera libre:
    sus puntos no deben quedar claramente dentro de otro disco efectivo.

    Esto es clave para detectar el diamante central como celda vacía.
    """
    ai = effective_radius(mast.h, sphere_radius)

    theta_vals = sample_arc_points_4(
        mast=mast,
        theta_a=theta_a,
        theta_b=theta_b,
        n=n
    )

    # Evitar extremos exactos porque los Q pertenecen a dos circunferencias.
    if len(theta_vals) > 4:
        theta_vals_check = theta_vals[2:-2]
    else:
        theta_vals_check = theta_vals

    free_count = 0

    for th in theta_vals_check:
        x = mast.x + ai*np.cos(th)
        y = mast.y + ai*np.sin(th)

        covered_other = point_covered_by_any_other_mast_4(
            x=x,
            y=y,
            masts=masts,
            sphere_radius=sphere_radius,
            excluded_mast_idx=mast_idx,
            margin=margin
        )

        if not covered_other:
            free_count += 1

    if len(theta_vals_check) == 0:
        return False

    # La mayoría del arco debe ser libre.
    return free_count >= 0.70*len(theta_vals_check)


def candidate_arc_supports_for_q_pair_4(
    q1,
    q2,
    q_by_label,
    masts,
    results_obj,
    sphere_radius,
    radial_tol=0.35,
    angle_tol=1e-3,
    max_side_arc_deg=180.0,
    arc_sample_n=21,
    other_mast_cover_margin=1e-6
):
    supports = []

    qn1 = q_by_label[q1]
    qn2 = q_by_label[q2]

    for mast_idx, mast in enumerate(masts):
        ai = effective_radius(mast.h, sphere_radius)

        r1 = dist_mast_q_xy_4(mast, qn1)
        r2 = dist_mast_q_xy_4(mast, qn2)

        if abs(r1 - ai) > radial_tol:
            continue

        if abs(r2 - ai) > radial_tol:
            continue

        useful_intervals = get_result_by_mast_4(
            results_obj,
            mast_idx
        )["useful_intervals"]

        th1 = angle_mast_to_q_4(mast, qn1)
        th2 = angle_mast_to_q_4(mast, qn2)

        # Probar ambas orientaciones del arco.
        for qa, qb, tha, thb in [
            (q1, q2, th1, th2),
            (q2, q1, th2, th1)
        ]:
            width = arc_width_ccw_4(tha, thb)

            if width <= 1e-9:
                continue

            if width > np.deg2rad(max_side_arc_deg):
                continue

            inside_useful = arc_is_inside_useful_intervals_4(
                theta_a=tha,
                theta_b=thb,
                useful_intervals=useful_intervals,
                angle_tol=angle_tol,
                n=arc_sample_n
            )

            if not inside_useful:
                continue

            free_arc = arc_has_free_side_4(
                mast_idx=mast_idx,
                mast=mast,
                theta_a=tha,
                theta_b=thb,
                masts=masts,
                sphere_radius=sphere_radius,
                n=arc_sample_n,
                margin=other_mast_cover_margin
            )

            if not free_arc:
                continue

            cut_pieces = split_ccw_arc_to_intervals_4(tha, thb)

            if not cut_pieces:
                continue

            supports.append({
                "mast_idx": mast_idx,
                "q_start": qa,
                "q_end": qb,
                "theta_start": tha,
                "theta_end": thb,
                "width_rad": width,
                "width_deg": np.degrees(width),
                "cut_pieces": cut_pieces
            })

    return supports


def detect_closed_inner_q_cells_4(
    tri_nodes_input,
    masts,
    results_obj,
    sphere_radius
):
    q_nodes = [n for n in tri_nodes_input if n["type"] == "Q"]
    q_by_label = {n["label"]: n for n in q_nodes}
    q_labels_all = list(q_by_label.keys())

    mast_xy = [(m.x, m.y) for m in masts]
    mast_hull = convex_hull_xy_4(mast_xy)

    min_area = MIN_CYCLE_AREA_FACTOR_4 * sphere_radius**2
    max_area = MAX_CYCLE_AREA_FACTOR_4 * sphere_radius**2

    selected_cells = []
    rejected_debug = []
    seen = set()

    for n_cycle in range(MIN_CYCLE_LEN_4, MAX_CYCLE_LEN_4 + 1):
        for q_comb in combinations(q_labels_all, n_cycle):
            ordered_cycle = order_q_labels_as_polygon_4(
                list(q_comb),
                q_by_label
            )

            canon = canonical_cycle_4(ordered_cycle)

            if canon in seen:
                continue

            seen.add(canon)

            polygon = [
                [q_by_label[q]["x"], q_by_label[q]["y"]]
                for q in ordered_cycle
            ]

            area = abs(polygon_area_xy_4(polygon))

            if area <= min_area:
                rejected_debug.append((ordered_cycle, "área degenerada", area))
                continue

            if area > max_area:
                rejected_debug.append((ordered_cycle, "área muy grande", area))
                continue

            if polygon_self_intersects_4(polygon):
                rejected_debug.append((ordered_cycle, "auto-intersección", area))
                continue

            centroid = polygon_centroid_xy_4(polygon)

            if REQUIRE_CENTROID_INSIDE_MAST_HULL_4:
                if len(mast_hull) >= 3:
                    if not point_in_or_on_polygon_xy_4(centroid, mast_hull, tol=1e-6):
                        rejected_debug.append((ordered_cycle, "centroide fuera de la envolvente de mástiles", area))
                        continue

            if REQUIRE_NO_MAST_INSIDE_4:
                contains_mast = False

                for i, mast in enumerate(masts):
                    if point_in_polygon_xy_4(
                        [mast.x, mast.y],
                        polygon
                    ):
                        contains_mast = True
                        break

                if contains_mast:
                    rejected_debug.append((ordered_cycle, "contiene un mástil", area))
                    continue

            if REQUIRE_CENTROID_UNCOVERED_4:
                centroid_covered = False

                for i, mast in enumerate(masts):
                    ai = effective_radius(mast.h, sphere_radius)
                    d = np.hypot(centroid[0] - mast.x, centroid[1] - mast.y)

                    if d < ai - 1e-6:
                        centroid_covered = True
                        break

                if centroid_covered:
                    rejected_debug.append((ordered_cycle, "centroide cubierto; no es celda vacía", area))
                    continue

            side_support_lists = []
            all_sides_supported = True

            for i in range(n_cycle):
                q1 = ordered_cycle[i]
                q2 = ordered_cycle[(i + 1) % n_cycle]

                supports = candidate_arc_supports_for_q_pair_4(
                    q1=q1,
                    q2=q2,
                    q_by_label=q_by_label,
                    masts=masts,
                    results_obj=results_obj,
                    sphere_radius=sphere_radius,
                    radial_tol=RADIAL_TOL_4,
                    angle_tol=ANGLE_TOL_4,
                    max_side_arc_deg=MAX_SIDE_ARC_DEG_4,
                    arc_sample_n=ARC_SAMPLE_N_4,
                    other_mast_cover_margin=OTHER_MAST_COVER_MARGIN_4
                )

                if not supports:
                    all_sides_supported = False
                    break

                side_support_lists.append(supports)

            if not all_sides_supported:
                rejected_debug.append((ordered_cycle, "algún lado no tiene arco libre útil", area))
                continue

            best_combo = None
            best_score = None

            for combo in product(*side_support_lists):
                edge_masts = [e["mast_idx"] for e in combo]
                unique_masts = sorted(set(edge_masts))

                total_width = sum(e["width_rad"] for e in combo)

                # Preferimos:
                # - más mástiles distintos;
                # - arcos más cortos;
                # - celdas más pequeñas.
                score = (
                    len(unique_masts),
                    -total_width,
                    -area
                )

                if best_score is None or score > best_score:
                    best_score = score
                    best_combo = list(combo)

            if best_combo is None:
                rejected_debug.append((ordered_cycle, "sin combinación válida de arcos", area))
                continue

            edge_masts = [e["mast_idx"] for e in best_combo]

            selected_cells.append({
                "cycle": ordered_cycle,
                "polygon_xy": polygon,
                "area_xy": area,
                "centroid_xy": centroid,
                "edge_masts": edge_masts,
                "edge_supports": best_combo
            })

    # Ordenar por área: primero las celdas más pequeñas.
    selected_cells.sort(key=lambda c: c["area_xy"])

    # Evitar celdas redundantes/superpuestas.
    final_cells = []

    for cell in selected_cells:
        c_cent = cell["centroid_xy"]

        overlaps = False

        for prev in final_cells:
            if point_in_polygon_xy_4(c_cent, prev["polygon_xy"]):
                overlaps = True
                break

            if point_in_polygon_xy_4(prev["centroid_xy"], cell["polygon_xy"]):
                overlaps = True
                break

        if not overlaps:
            final_cells.append(cell)

    return final_cells, rejected_debug


def triangle_has_forbidden_mq_edge_4(tri, forbidden_mq_edges):
    tri_type = tri.get("triangle_type", classify_triangle_type_4(tri))

    if tri_type != "M-M-Q":
        return False, None

    mast_nodes = [n for n in tri["nodes"] if n["type"] == "mast_top"]
    q_nodes = [n for n in tri["nodes"] if n["type"] == "Q"]

    if len(mast_nodes) != 2 or len(q_nodes) != 1:
        return False, None

    q_label = q_nodes[0]["label"]

    blocked = []

    for m in mast_nodes:
        try:
            mast_idx = int(m["label"].replace("M", ""))
        except Exception:
            continue

        if (mast_idx, q_label) in forbidden_mq_edges:
            blocked.append(f"{m['label']}-{q_label}")

    if blocked:
        return True, ", ".join(blocked)

    return False, None


def filter_triangles_by_forbidden_mq_edges_4(
    triangles,
    forbidden_mq_edges
):
    kept = []
    removed = []

    for tri in triangles:
        tri_type = tri.get("triangle_type", classify_triangle_type_4(tri))

        tri_ext = dict(tri)
        tri_ext["triangle_type"] = tri_type

        remove_it, blocked_edges = triangle_has_forbidden_mq_edge_4(
            tri_ext,
            forbidden_mq_edges
        )

        if remove_it:
            tri_ext["removed_reason"] = (
                "M-Q pertenece a celda cerrada interior eliminada: "
                + str(blocked_edges)
            )
            removed.append(tri_ext)
        else:
            kept.append(tri_ext)

    return kept, removed


def build_active_tri_nodes_after_filter_4(tri_nodes_input, triangles):
    active_labels = set()

    for tri in triangles:
        for n in tri["nodes"]:
            active_labels.add(n["label"])

    return [
        n for n in tri_nodes_input
        if n["type"] == "mast_top" or n["label"] in active_labels
    ]


def filter_closed_inner_q_cells_4(
    input_triangles,
    tri_nodes_input,
    masts,
    results_obj,
    sphere_radius
):
    updated_results = copy_results_robust_4(results_obj)

    detected_cells, rejected_debug = detect_closed_inner_q_cells_4(
        tri_nodes_input=tri_nodes_input,
        masts=masts,
        results_obj=updated_results,
        sphere_radius=sphere_radius
    )

    cuts_by_mast = defaultdict(list)
    forbidden_mq_edges = set()

    closed_q_cycles_log = []
    closed_q_cuts_log = []

    for cell in detected_cells:
        cycle = cell["cycle"]

        closed_q_cycles_log.append({
            "cycle": cycle,
            "n_q": len(cycle),
            "area_xy": cell["area_xy"],
            "centroid_xy": cell["centroid_xy"],
            "edge_masts": cell["edge_masts"],
            "polygon_xy": cell["polygon_xy"]
        })

        for support in cell["edge_supports"]:
            mast_idx = support["mast_idx"]
            q_start = support["q_start"]
            q_end = support["q_end"]

            for cut_piece in support["cut_pieces"]:
                cuts_by_mast[mast_idx].append(cut_piece)

                closed_q_cuts_log.append({
                    "cycle": cycle,
                    "mast_idx": mast_idx,
                    "q_start": q_start,
                    "q_end": q_end,
                    "cut_interval_rad": cut_piece,
                    "cut_interval_deg": (
                        np.degrees(cut_piece[0]),
                        np.degrees(cut_piece[1])
                    ),
                    "width_deg": support["width_deg"]
                })

            forbidden_mq_edges.add((mast_idx, q_start))
            forbidden_mq_edges.add((mast_idx, q_end))

    # Aplicar recortes angulares.
    for mast_idx, cuts in cuts_by_mast.items():
        apply_cut_intervals_to_results_4(
            updated_results=updated_results,
            mast_idx=mast_idx,
            cut_intervals=cuts
        )

    # Eliminar triángulos M-M-Q afectados por los segmentos M-Q prohibidos.
    kept_triangles, removed_triangles = filter_triangles_by_forbidden_mq_edges_4(
        triangles=input_triangles,
        forbidden_mq_edges=forbidden_mq_edges
    )

    # Reconstruir nodos activos para borrar Q huérfanos.
    active_tri_nodes = build_active_tri_nodes_after_filter_4(
        tri_nodes_input=tri_nodes_input,
        triangles=kept_triangles
    )

    return (
        kept_triangles,
        removed_triangles,
        updated_results,
        active_tri_nodes,
        closed_q_cycles_log,
        closed_q_cuts_log,
        forbidden_mq_edges,
        rejected_debug
    )


def plot_after_closed_q_filter_4(
    tri_nodes,
    kept_triangles,
    masts,
    results_obj,
    sphere_radius,
    closed_q_cycles_log,
    show_single_mast_reference=True,
    show_removed_cycles=True
):
    fig = go.Figure()

    # ---------------------------------
    # 1) Triángulos conservados
    # ---------------------------------
    for tri in kept_triangles:
        n1, n2, n3 = tri["nodes"]
        labels = tri["labels"]
        tri_type = tri.get("triangle_type", classify_triangle_type_4(tri))

        if tri_type == "M-M-Q":
            color = "orange"
        elif tri_type == "M-M-M":
            color = "gray"
        else:
            color = "black"

        for a, b in [(n1, n2), (n2, n3), (n3, n1)]:
            fig.add_trace(go.Scatter3d(
                x=[a["x"], b["x"]],
                y=[a["y"], b["y"]],
                z=[a["z"], b["z"]],
                mode="lines",
                line=dict(color=color, width=4),
                showlegend=False,
                hoverinfo="text",
                text=[f"{labels} | {tri_type}", f"{labels} | {tri_type}"]
            ))

    # ---------------------------------
    # 2) Celdas eliminadas
    # ---------------------------------
    if show_removed_cycles and closed_q_cycles_log:
        for k, item in enumerate(closed_q_cycles_log, start=1):
            poly = np.asarray(item["polygon_xy"], dtype=float)

            x = list(poly[:, 0]) + [poly[0, 0]]
            y = list(poly[:, 1]) + [poly[0, 1]]
            z = [0.20 for _ in x]

            fig.add_trace(go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines+markers",
                line=dict(color="red", width=8),
                marker=dict(size=5, color="red"),
                name=f"Celda eliminada {k}",
                hoverinfo="text",
                text=[
                    f"Celda eliminada {k}<br>"
                    f"Q={item['cycle']}<br>"
                    f"Área XY={item['area_xy']:.4f}"
                    for _ in x
                ]
            ))

    # ---------------------------------
    # 3) Puntos Q activos
    # ---------------------------------
    q_nodes = [n for n in tri_nodes if n["type"] == "Q"]

    if q_nodes:
        fig.add_trace(go.Scatter3d(
            x=[n["x"] for n in q_nodes],
            y=[n["y"] for n in q_nodes],
            z=[0.0 for _ in q_nodes],
            mode="markers+text",
            marker=dict(size=6, color="orange"),
            text=[n["label"] for n in q_nodes],
            textposition="top center",
            name="Q activos"
        ))

    # ---------------------------------
    # 4) Mástiles
    # ---------------------------------
    mast_nodes = [n for n in tri_nodes if n["type"] == "mast_top"]

    for n in mast_nodes:
        fig.add_trace(go.Scatter3d(
            x=[n["x"], n["x"]],
            y=[n["y"], n["y"]],
            z=[0.0, n["z"]],
            mode="lines",
            line=dict(color="blue", width=8),
            showlegend=False,
            hoverinfo="skip"
        ))

        fig.add_trace(go.Scatter3d(
            x=[n["x"]],
            y=[n["y"]],
            z=[n["z"]],
            mode="markers+text",
            marker=dict(size=5, color="black"),
            text=[n["label"]],
            textposition="top center",
            name=n["label"]
        ))

    # ---------------------------------
    # 5) Referencia de mástil solo actualizada
    # ---------------------------------
    if show_single_mast_reference:
        for i, mast in enumerate(masts):
            ai = effective_radius(mast.h, sphere_radius)

            useful_intervals = get_result_by_mast_4(
                results_obj,
                i
            )["useful_intervals"]

            for th1, th2 in useful_intervals:
                theta = np.linspace(th1, th2, 80)
                r = np.linspace(0.0, ai, 20)

                TH, RR = np.meshgrid(theta, r, indexing="xy")

                X = mast.x + RR*np.cos(TH)
                Y = mast.y + RR*np.sin(TH)
                Z = np.zeros_like(X)

                fig.add_trace(go.Surface(
                    x=X,
                    y=Y,
                    z=Z,
                    showscale=False,
                    opacity=0.10,
                    hoverinfo="skip",
                    name=f"Mástil solo M{i}"
                ))

    # ---------------------------------
    # 6) Suelo
    # ---------------------------------
    all_xy = np.array(
        [[n["x"], n["y"]] for n in tri_nodes],
        dtype=float
    )

    xmin, ymin = all_xy.min(axis=0) - 5
    xmax, ymax = all_xy.max(axis=0) + 5

    Xg, Yg = np.meshgrid(
        np.linspace(xmin, xmax, 2),
        np.linspace(ymin, ymax, 2)
    )

    fig.add_trace(go.Surface(
        x=Xg,
        y=Yg,
        z=np.zeros_like(Xg),
        opacity=0.08,
        showscale=False,
        hoverinfo="skip",
        name="Suelo"
    ))

    fig.update_layout(
        title="Cuarto filtro: eliminación de celdas cerradas interiores formadas por Q",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="data"
        ),
        height=850
    )

    fig.show()


import numpy as np


import plotly.graph_objects as go


INTERIOR_SAMPLE_DIVISIONS_5 = 18


BARYCENTRIC_EDGE_MARGIN_5 = 0.05


MIN_INTERIOR_HITS_5 = 2


COUNT_UNIQUE_SAMPLE_POINTS_5 = True


RADIAL_MARGIN_5 = 1e-4


ANGULAR_MARGIN_5 = 1e-4


SHOW_REMOVED_MMM_5 = True


SHOW_INVASION_POINTS_5 = True


def classify_triangle_type_5(tri_data):
    if "classify_triangle_type" in globals():
        return classify_triangle_type(tri_data)

    node_types = [n["type"] for n in tri_data["nodes"]]

    nM = sum(1 for t in node_types if t == "mast_top")
    nQ = sum(1 for t in node_types if t == "Q")

    if nM == 3:
        return "M-M-M"
    elif nM == 2 and nQ == 1:
        return "M-M-Q"
    elif nM == 1 and nQ == 2:
        return "M-Q-Q"
    elif nQ == 3:
        return "Q-Q-Q"
    else:
        return "UNKNOWN"


def get_result_by_mast_5(results_obj, mast_idx):
    return results_obj[mast_idx]


def normalize_0_2pi_5(theta):
    return float(theta % (2*np.pi))


def normalize_interval_no_wrap_5(interval):
    a, b = interval

    a = normalize_0_2pi_5(a)
    b = normalize_0_2pi_5(b)

    if a <= b:
        return [(a, b)]

    return [(a, 2*np.pi), (0.0, b)]


def point_in_useful_interval_strict_5(theta, interval, angular_margin=1e-4):
    theta = normalize_0_2pi_5(theta)

    for a, b in normalize_interval_no_wrap_5(interval):
        if (a + angular_margin) < theta < (b - angular_margin):
            return True

    return False


def point_in_any_useful_interval_strict_5(theta, useful_intervals, angular_margin=1e-4):
    for interval in useful_intervals:
        if point_in_useful_interval_strict_5(
            theta,
            interval,
            angular_margin=angular_margin
        ):
            return True

    return False


def sample_interior_points_in_triangle_xy_5(
    n1,
    n2,
    n3,
    divisions=18,
    barycentric_margin=0.05
):
    """
    Genera puntos estrictamente interiores del triángulo en XY.

    No usa:
    - vértices,
    - aristas,
    - puntos demasiado cercanos al borde.

    Retorna:
    - lista de dicts con x, y, coordenadas baricéntricas.
    """
    x1, y1 = n1["x"], n1["y"]
    x2, y2 = n2["x"], n2["y"]
    x3, y3 = n3["x"], n3["y"]

    pts = []

    for i in range(1, divisions):
        for j in range(1, divisions - i):
            a = i / divisions
            b = j / divisions
            c = 1.0 - a - b

            if c <= 0:
                continue

            # Filtro interior estricto.
            if min(a, b, c) <= barycentric_margin:
                continue

            x = a*x1 + b*x2 + c*x3
            y = a*y1 + b*y2 + c*y3

            pts.append({
                "x": float(x),
                "y": float(y),
                "barycentric": (a, b, c)
            })

    return pts


def point_invades_single_mast_layer_5(
    x,
    y,
    mast,
    mast_idx,
    results_obj,
    sphere_radius,
    radial_margin=1e-4,
    angular_margin=1e-4
):
    """
    Retorna True si el punto XY cae estrictamente dentro
    de la capa útil viva de mástil solo.
    """
    ai = effective_radius(mast.h, sphere_radius)

    dx = x - mast.x
    dy = y - mast.y

    r = np.hypot(dx, dy)

    # Punto claramente interior al radio efectivo.
    if r >= ai - radial_margin:
        return False, None

    theta = normalize_0_2pi_5(np.arctan2(dy, dx))

    useful_intervals = get_result_by_mast_5(
        results_obj,
        mast_idx
    )["useful_intervals"]

    if not point_in_any_useful_interval_strict_5(
        theta,
        useful_intervals,
        angular_margin=angular_margin
    ):
        return False, None

    return True, {
        "mast_idx": mast_idx,
        "r": float(r),
        "ai": float(ai),
        "theta_rad": float(theta),
        "theta_deg": float(np.degrees(theta))
    }


def triangle_mmm_invades_single_mast_layer_5(
    tri_data,
    masts,
    results_obj,
    sphere_radius,
    divisions=18,
    barycentric_margin=0.05,
    min_hits=2,
    radial_margin=1e-4,
    angular_margin=1e-4,
    count_unique_sample_points=True
):
    """
    Evalúa si un M-M-M invade en planta la capa viva de mástil solo.

    Criterio:
    - Se muestrean solo puntos interiores.
    - Se cuenta cuántos puntos caen dentro de cualquier capa útil viva.
    - Si hits >= min_hits, el triángulo se elimina.
    """
    n1, n2, n3 = tri_data["nodes"]

    sample_pts = sample_interior_points_in_triangle_xy_5(
        n1,
        n2,
        n3,
        divisions=divisions,
        barycentric_margin=barycentric_margin
    )

    hit_records = []
    unique_hit_points = set()

    for p_idx, p in enumerate(sample_pts):
        x = p["x"]
        y = p["y"]

        point_has_hit = False
        point_hit_infos = []

        for mast_idx, mast in enumerate(masts):
            invades, info = point_invades_single_mast_layer_5(
                x=x,
                y=y,
                mast=mast,
                mast_idx=mast_idx,
                results_obj=results_obj,
                sphere_radius=sphere_radius,
                radial_margin=radial_margin,
                angular_margin=angular_margin
            )

            if not invades:
                continue

            point_has_hit = True

            info_ext = dict(info)
            info_ext["sample_idx"] = p_idx
            info_ext["x"] = x
            info_ext["y"] = y
            info_ext["barycentric"] = p["barycentric"]

            point_hit_infos.append(info_ext)

        if point_has_hit:
            unique_hit_points.add(p_idx)
            hit_records.extend(point_hit_infos)

        if count_unique_sample_points:
            if len(unique_hit_points) >= min_hits:
                return True, hit_records, sample_pts
        else:
            if len(hit_records) >= min_hits:
                return True, hit_records, sample_pts

    if count_unique_sample_points:
        return len(unique_hit_points) >= min_hits, hit_records, sample_pts

    return len(hit_records) >= min_hits, hit_records, sample_pts


def build_active_tri_nodes_after_mmm_overlap_filter_5(tri_nodes_input, triangles):
    """
    Conserva:
    - todos los mástiles;
    - solo Q que sigan apareciendo en triángulos conservados.

    En este filtro se eliminan M-M-M, por lo que normalmente no se
    eliminan Q, pero se reconstruye por consistencia.
    """
    active_labels = set()

    for tri in triangles:
        for n in tri["nodes"]:
            active_labels.add(n["label"])

    active_tri_nodes = [
        n for n in tri_nodes_input
        if n["type"] == "mast_top" or n["label"] in active_labels
    ]

    return active_tri_nodes


def filter_mmm_by_single_mast_layer_overlap_5(
    input_triangles,
    tri_nodes_input,
    masts,
    results_obj,
    sphere_radius,
    divisions=18,
    barycentric_margin=0.05,
    min_hits=2,
    radial_margin=1e-4,
    angular_margin=1e-4,
    count_unique_sample_points=True
):
    kept = []
    removed = []
    overlap_log = []

    all_invasion_points = []

    for tri_data in input_triangles:
        tri_type = tri_data.get(
            "triangle_type",
            classify_triangle_type_5(tri_data)
        )

        tri_ext = dict(tri_data)
        tri_ext["triangle_type"] = tri_type

        # Solo se evalúan M-M-M.
        if tri_type != "M-M-M":
            kept.append(tri_ext)
            continue

        invades, hit_records, sample_pts = triangle_mmm_invades_single_mast_layer_5(
            tri_data=tri_ext,
            masts=masts,
            results_obj=results_obj,
            sphere_radius=sphere_radius,
            divisions=divisions,
            barycentric_margin=barycentric_margin,
            min_hits=min_hits,
            radial_margin=radial_margin,
            angular_margin=angular_margin,
            count_unique_sample_points=count_unique_sample_points
        )

        if invades:
            tri_ext["removed_reason"] = (
                "M-M-M invade en planta la capa viva de mástil solo "
                f"con {len(set(h['sample_idx'] for h in hit_records))} "
                "puntos interiores coincidentes"
            )
            tri_ext["single_mast_overlap_hits"] = hit_records

            removed.append(tri_ext)

            mast_hits = sorted(set(h["mast_idx"] for h in hit_records))
            unique_sample_hits = sorted(set(h["sample_idx"] for h in hit_records))

            overlap_log.append({
                "triangle": tri_ext["labels"],
                "triangle_type": tri_type,
                "mast_hits": mast_hits,
                "n_unique_sample_hits": len(unique_sample_hits),
                "n_total_hits": len(hit_records),
                "hit_records": hit_records
            })

            all_invasion_points.extend(hit_records)

        else:
            kept.append(tri_ext)

    tri_nodes_after = build_active_tri_nodes_after_mmm_overlap_filter_5(
        tri_nodes_input=tri_nodes_input,
        triangles=kept
    )

    return kept, removed, tri_nodes_after, overlap_log, all_invasion_points


def plot_after_mmm_single_mast_overlap_filter_5(
    tri_nodes,
    kept_triangles,
    removed_triangles,
    masts,
    results_obj,
    sphere_radius,
    invasion_points=None,
    show_removed_mmm=True,
    show_invasion_points=True,
    show_single_mast_reference=True
):
    fig = go.Figure()

    # ---------------------------------
    # 1) Triángulos conservados
    # ---------------------------------
    for tri_data in kept_triangles:
        n1, n2, n3 = tri_data["nodes"]
        labels = tri_data["labels"]
        tri_type = tri_data.get(
            "triangle_type",
            classify_triangle_type_5(tri_data)
        )

        if tri_type == "M-M-Q":
            color = "orange"
        elif tri_type == "M-M-M":
            color = "gray"
        else:
            color = "black"

        for a, b in [(n1, n2), (n2, n3), (n3, n1)]:
            fig.add_trace(go.Scatter3d(
                x=[a["x"], b["x"]],
                y=[a["y"], b["y"]],
                z=[a["z"], b["z"]],
                mode="lines",
                line=dict(color=color, width=4),
                showlegend=False,
                hoverinfo="text",
                text=[f"{labels} | {tri_type}", f"{labels} | {tri_type}"]
            ))

    # ---------------------------------
    # 2) M-M-M eliminados
    # ---------------------------------
    if show_removed_mmm:
        for tri_data in removed_triangles:
            n1, n2, n3 = tri_data["nodes"]
            labels = tri_data["labels"]

            xs = [n1["x"], n2["x"], n3["x"], n1["x"]]
            ys = [n1["y"], n2["y"], n3["y"], n1["y"]]
            zs = [n1["z"], n2["z"], n3["z"], n1["z"]]

            fig.add_trace(go.Scatter3d(
                x=xs,
                y=ys,
                z=zs,
                mode="lines+markers",
                line=dict(color="red", width=7, dash="dash"),
                marker=dict(size=4, color="red"),
                name=f"M-M-M eliminado {labels}",
                hoverinfo="text",
                text=[
                    f"{labels}<br>{tri_data.get('removed_reason', '')}"
                    for _ in xs
                ]
            ))

    # ---------------------------------
    # 3) Puntos interiores que causaron invasión
    # ---------------------------------
    if show_invasion_points and invasion_points:
        fig.add_trace(go.Scatter3d(
            x=[p["x"] for p in invasion_points],
            y=[p["y"] for p in invasion_points],
            z=[0.25 for _ in invasion_points],
            mode="markers",
            marker=dict(size=5, color="red"),
            name="Puntos interiores de invasión",
            hoverinfo="text",
            text=[
                f"M{p['mast_idx']}<br>"
                f"θ={p['theta_deg']:.2f}°<br>"
                f"r={p['r']:.4f} / ai={p['ai']:.4f}"
                for p in invasion_points
            ]
        ))

    # ---------------------------------
    # 4) Puntos Q activos
    # ---------------------------------
    q_nodes = [n for n in tri_nodes if n["type"] == "Q"]

    if q_nodes:
        fig.add_trace(go.Scatter3d(
            x=[n["x"] for n in q_nodes],
            y=[n["y"] for n in q_nodes],
            z=[0.0 for _ in q_nodes],
            mode="markers+text",
            marker=dict(size=6, color="orange"),
            text=[n["label"] for n in q_nodes],
            textposition="top center",
            name="Q activos"
        ))

    # ---------------------------------
    # 5) Mástiles
    # ---------------------------------
    mast_nodes = [n for n in tri_nodes if n["type"] == "mast_top"]

    for n in mast_nodes:
        fig.add_trace(go.Scatter3d(
            x=[n["x"], n["x"]],
            y=[n["y"], n["y"]],
            z=[0.0, n["z"]],
            mode="lines",
            line=dict(color="blue", width=8),
            showlegend=False,
            hoverinfo="skip"
        ))

        fig.add_trace(go.Scatter3d(
            x=[n["x"]],
            y=[n["y"]],
            z=[n["z"]],
            mode="markers+text",
            marker=dict(size=5, color="black"),
            text=[n["label"]],
            textposition="top center",
            name=n["label"]
        ))

    # ---------------------------------
    # 6) Capa de mástil solo viva
    # ---------------------------------
    if show_single_mast_reference:
        for i, mast in enumerate(masts):
            ai = effective_radius(mast.h, sphere_radius)

            useful_intervals = get_result_by_mast_5(
                results_obj,
                i
            )["useful_intervals"]

            for th1, th2 in useful_intervals:
                theta = np.linspace(th1, th2, 80)
                r = np.linspace(0.0, ai, 25)

                TH, RR = np.meshgrid(theta, r, indexing="xy")

                X = mast.x + RR*np.cos(TH)
                Y = mast.y + RR*np.sin(TH)
                Z = np.zeros_like(X)

                fig.add_trace(go.Surface(
                    x=X,
                    y=Y,
                    z=Z,
                    showscale=False,
                    opacity=0.13,
                    hoverinfo="skip",
                    name=f"Capa mástil solo M{i}"
                ))

    # ---------------------------------
    # 7) Suelo
    # ---------------------------------
    all_xy = np.array(
        [[n["x"], n["y"]] for n in tri_nodes],
        dtype=float
    )

    xmin, ymin = all_xy.min(axis=0) - 5
    xmax, ymax = all_xy.max(axis=0) + 5

    Xg, Yg = np.meshgrid(
        np.linspace(xmin, xmax, 2),
        np.linspace(ymin, ymax, 2)
    )

    fig.add_trace(go.Surface(
        x=Xg,
        y=Yg,
        z=np.zeros_like(Xg),
        opacity=0.08,
        showscale=False,
        hoverinfo="skip",
        name="Suelo"
    ))

    fig.update_layout(
        title="Quinto filtro: eliminar M-M-M que invaden en planta la capa de mástil solo",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="data"
        ),
        height=850
    )

    fig.show()


import numpy as np


import plotly.graph_objects as go


def point_in_triangle_xy(px, py, n1, n2, n3, tol=1e-9):
    x1, y1 = n1["x"], n1["y"]
    x2, y2 = n2["x"], n2["y"]
    x3, y3 = n3["x"], n3["y"]

    denom = (y2 - y3)*(x1 - x3) + (x3 - x2)*(y1 - y3)

    if abs(denom) < tol:
        return False

    l1 = ((y2 - y3)*(px - x3) + (x3 - x2)*(py - y3)) / denom
    l2 = ((y3 - y1)*(px - x3) + (x1 - x3)*(py - y3)) / denom
    l3 = 1.0 - l1 - l2

    return (l1 >= -tol) and (l2 >= -tol) and (l3 >= -tol)


def sample_points_triangle_interior_dense(n1, n2, n3, divisions=14):
    x1, y1 = n1["x"], n1["y"]
    x2, y2 = n2["x"], n2["y"]
    x3, y3 = n3["x"], n3["y"]

    pts = []

    for i in range(1, divisions):
        for j in range(1, divisions - i):
            a = i / divisions
            b = j / divisions
            c = 1.0 - a - b

            if c <= 0:
                continue

            px = a*x1 + b*x2 + c*x3
            py = a*y1 + b*y2 + c*y3

            pts.append((px, py))

    return pts


def triangles_overlap_in_xy_by_sampling(tri_a, tri_b, min_common_points=1, divisions=14):
    a1, a2, a3 = tri_a["nodes"]
    b1, b2, b3 = tri_b["nodes"]

    common_count = 0

    pts_a = sample_points_triangle_interior_dense(
        a1, a2, a3,
        divisions=divisions
    )

    for px, py in pts_a:
        if point_in_triangle_xy(px, py, b1, b2, b3):
            common_count += 1

            if common_count >= min_common_points:
                return True, common_count

    pts_b = sample_points_triangle_interior_dense(
        b1, b2, b3,
        divisions=divisions
    )

    for px, py in pts_b:
        if point_in_triangle_xy(px, py, a1, a2, a3):
            common_count += 1

            if common_count >= min_common_points:
                return True, common_count

    return False, common_count


def filter_mmm_overlapping_mmq_in_xy(
    triangles,
    min_common_points=1,
    divisions=14
):
    mmm_triangles = []
    mmq_triangles = []
    other_triangles = []

    for tri in triangles:
        tri_type = tri.get("triangle_type", classify_triangle_type(tri))

        tri_ext = dict(tri)
        tri_ext["triangle_type"] = tri_type

        if tri_type == "M-M-M":
            mmm_triangles.append(tri_ext)
        elif tri_type == "M-M-Q":
            mmq_triangles.append(tri_ext)
        else:
            other_triangles.append(tri_ext)

    kept_mmm = []
    removed_mmm = []

    for mmm in mmm_triangles:
        overlaps_any_mmq = False
        overlapped_mmq_labels = []
        overlap_debug = []

        for mmq in mmq_triangles:
            overlaps_xy, common_count = triangles_overlap_in_xy_by_sampling(
                tri_a=mmm,
                tri_b=mmq,
                min_common_points=min_common_points,
                divisions=divisions
            )

            overlap_debug.append({
                "mmq_labels": mmq["labels"],
                "overlaps_xy": overlaps_xy,
                "common_count": common_count
            })

            if overlaps_xy:
                overlaps_any_mmq = True
                overlapped_mmq_labels.append(mmq["labels"])

        mmm_ext = dict(mmm)
        mmm_ext["overlaps_mmq_in_xy"] = overlaps_any_mmq
        mmm_ext["overlapped_mmq_labels"] = overlapped_mmq_labels
        mmm_ext["overlap_xy_debug"] = overlap_debug

        if overlaps_any_mmq:
            removed_mmm.append(mmm_ext)
        else:
            kept_mmm.append(mmm_ext)

    kept_all = kept_mmm + mmq_triangles + other_triangles

    return kept_all, kept_mmm, removed_mmm, mmq_triangles, other_triangles


def plot_triangles_after_mmm_mmq_overlap_filter_xy(
    tri_nodes,
    kept_triangles,
    masts,
    results,
    sphere_radius,
    show_single_mast_reference=True
):
    fig = go.Figure()

    # ---------------------------------
    # 1) Triángulos conservados
    # ---------------------------------
    for tri_data in kept_triangles:
        n1, n2, n3 = tri_data["nodes"]
        labels = tri_data["labels"]
        tri_type = tri_data.get("triangle_type", classify_triangle_type(tri_data))

        hover_txt = f"{labels} | {tri_type}"

        for a, b in [(n1, n2), (n2, n3), (n3, n1)]:
            fig.add_trace(go.Scatter3d(
                x=[a["x"], b["x"]],
                y=[a["y"], b["y"]],
                z=[a["z"], b["z"]],
                mode="lines",
                line=dict(color="gray", width=4),
                showlegend=False,
                hoverinfo="text",
                text=[hover_txt, hover_txt]
            ))

    # ---------------------------------
    # 2) Puntos Q
    # ---------------------------------
    q_nodes = [n for n in tri_nodes if n["type"] == "Q"]

    if q_nodes:
        fig.add_trace(go.Scatter3d(
            x=[n["x"] for n in q_nodes],
            y=[n["y"] for n in q_nodes],
            z=[0.0 for _ in q_nodes],
            mode="markers+text",
            marker=dict(size=6, color="orange"),
            text=[n["label"] for n in q_nodes],
            textposition="top center",
            name="Q"
        ))

    # ---------------------------------
    # 3) Mástiles
    # ---------------------------------
    mast_nodes = [n for n in tri_nodes if n["type"] == "mast_top"]

    for n in mast_nodes:
        fig.add_trace(go.Scatter3d(
            x=[n["x"], n["x"]],
            y=[n["y"], n["y"]],
            z=[0.0, n["z"]],
            mode="lines",
            line=dict(color="blue", width=8),
            showlegend=False,
            hoverinfo="skip"
        ))

        fig.add_trace(go.Scatter3d(
            x=[n["x"]],
            y=[n["y"]],
            z=[n["z"]],
            mode="markers+text",
            marker=dict(size=5, color="black"),
            text=[n["label"]],
            textposition="top center",
            name=n["label"]
        ))

    # ---------------------------------
    # 4) Referencia de mástil solo actualizada
    # ---------------------------------
    if show_single_mast_reference:
        for i, mast in enumerate(masts):
            ai = effective_radius(mast.h, sphere_radius)
            useful_intervals = results[i]["useful_intervals"]

            for th1, th2 in useful_intervals:
                theta = np.linspace(th1, th2, 80)
                r = np.linspace(0.0, ai, 20)

                TH, RR = np.meshgrid(theta, r, indexing="xy")

                X = mast.x + RR * np.cos(TH)
                Y = mast.y + RR * np.sin(TH)
                Z = np.zeros_like(X)

                fig.add_trace(go.Surface(
                    x=X,
                    y=Y,
                    z=Z,
                    showscale=False,
                    opacity=0.10,
                    hoverinfo="skip"
                ))

    # ---------------------------------
    # 5) Plano base
    # ---------------------------------
    xy = np.array([[n["x"], n["y"]] for n in tri_nodes], dtype=float)

    xmin, ymin = xy.min(axis=0) - 5
    xmax, ymax = xy.max(axis=0) + 5

    Xg, Yg = np.meshgrid(
        np.linspace(xmin, xmax, 2),
        np.linspace(ymin, ymax, 2)
    )

    fig.add_trace(go.Surface(
        x=Xg,
        y=Yg,
        z=np.zeros_like(Xg),
        opacity=0.08,
        showscale=False,
        hoverinfo="skip",
        name="Suelo"
    ))

    fig.update_layout(
        title="Sexto filtro: eliminar M-M-M que se solapan en XY con M-M-Q",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="data"
        ),
        height=850
    )

    fig.show()


import numpy as np


import plotly.graph_objects as go


from itertools import combinations


def node_point(n):
    return np.array([n["x"], n["y"], n["z"]], dtype=float)


def edge_key(a, b):
    return tuple(sorted([a, b]))


def label_to_index(label):
    return int(str(label).replace("M", ""))


def edge_has_guard_wire(label1, label2, guard_wire_inputs):
    if guard_wire_inputs is None:
        return False

    key = edge_key(label1, label2)

    for w in guard_wire_inputs:
        wi = f"M{w['i']}"
        wj = f"M{w['j']}"

        if edge_key(wi, wj) == key:
            return True

    return False


def get_guard_neighbors(label, guard_wire_inputs):
    neigh = []

    if guard_wire_inputs is None:
        return neigh

    for w in guard_wire_inputs:
        wi = f"M{w['i']}"
        wj = f"M{w['j']}"

        if label == wi:
            neigh.append(wj)
        elif label == wj:
            neigh.append(wi)

    return neigh


def make_mast_nodes_from_tri_nodes(tri_nodes):
    mast_nodes = [
        n for n in tri_nodes
        if n.get("type", None) == "mast_top"
    ]

    return sorted(
        mast_nodes,
        key=lambda n: label_to_index(n["label"])
    )


def curve_to_array(curve):
    """
    Convierte una curva a matriz Nx3.
    Acepta:
      - tupla (x, y, z);
      - array Nx3.
    """
    if curve is None:
        return None

    if isinstance(curve, tuple) and len(curve) == 3:
        x, y, z = curve
        C = np.column_stack([x, y, z]).astype(float)
    else:
        C = np.asarray(curve, dtype=float)

    if C.ndim != 2 or C.shape[1] != 3:
        return None

    C[:, 2] = np.maximum(C[:, 2], 0.0)

    return C


def resample_curve_xyz(curve_xyz, npts=180):
    C = np.asarray(curve_xyz, dtype=float)

    if len(C) < 2:
        return np.repeat(C[:1], npts, axis=0)

    d = np.linalg.norm(np.diff(C, axis=0), axis=1)
    s_old = np.concatenate([[0.0], np.cumsum(d)])

    if s_old[-1] < 1e-12:
        return np.repeat(C[:1], npts, axis=0)

    s_old = s_old / s_old[-1]
    s_new = np.linspace(0.0, 1.0, npts)

    x = np.interp(s_new, s_old, C[:, 0])
    y = np.interp(s_new, s_old, C[:, 1])
    z = np.interp(s_new, s_old, C[:, 2])

    out = np.column_stack([x, y, z])
    out[:, 2] = np.maximum(out[:, 2], 0.0)

    return out


def orient_curve_xyz(curve_xyz, start_node, end_node):
    C = np.asarray(curve_xyz, dtype=float)

    p_start = node_point(start_node)
    p_end = node_point(end_node)

    d_normal = (
        np.linalg.norm(C[0] - p_start)
        + np.linalg.norm(C[-1] - p_end)
    )

    d_flip = (
        np.linalg.norm(C[-1] - p_start)
        + np.linalg.norm(C[0] - p_end)
    )

    if d_flip < d_normal:
        C = C[::-1].copy()

    C[:, 2] = np.maximum(C[:, 2], 0.0)

    return C


def real_spherical_crest_between_two_masts(n1, n2, sphere_radius, npts=180):
    """
    Cresta esférica real entre dos mástiles.
    Aplica si L_3D <= 2S.
    """
    x1, y1, h1 = n1["x"], n1["y"], n1["z"]
    x2, y2, h2 = n2["x"], n2["y"], n2["z"]

    dx = x2 - x1
    dy = y2 - y1
    dxy = np.hypot(dx, dy)

    if dxy < 1e-12:
        return None

    dh = h2 - h1
    chord_len = np.hypot(dxy, dh)

    if chord_len > 2.0 * sphere_radius:
        return None

    um = 0.5 * dxy
    zm = 0.5 * (h1 + h2)

    a = np.sqrt(max(sphere_radius**2 - (chord_len / 2.0)**2, 0.0))

    nu = -dh / chord_len
    nz = dxy / chord_len

    u0 = um + a * nu
    z0 = zm + a * nz

    u = np.linspace(0.0, dxy, npts)

    inside = sphere_radius**2 - (u - u0)**2
    inside = np.maximum(inside, 0.0)

    z = z0 - np.sqrt(inside)

    z[0] = h1
    z[-1] = h2
    z = np.maximum(z, 0.0)

    ex = dx / dxy
    ey = dy / dxy

    x = x1 + u * ex
    y = y1 + u * ey

    return x, y, z


def tangent_points_from_point_to_circle_2d(P, C, R):
    P = np.asarray(P, dtype=float)
    C = np.asarray(C, dtype=float)

    v = P - C
    D = np.linalg.norm(v)

    if D <= R:
        return []

    e = v / D
    p = np.array([-e[1], e[0]])

    a = R**2 / D
    b = R * np.sqrt(D**2 - R**2) / D

    T1 = C + a * e + b * p
    T2 = C + a * e - b * p

    return [T1, T2]


def choose_inner_tangent_point_2d(P, C, R, side):
    tangents = tangent_points_from_point_to_circle_2d(P, C, R)

    if not tangents:
        return None

    if side == "left":
        candidates = [T for T in tangents if T[0] >= P[0]]
    elif side == "right":
        candidates = [T for T in tangents if T[0] <= P[0]]
    else:
        candidates = tangents

    if not candidates:
        candidates = tangents

    return min(candidates, key=lambda T: T[1])


def long_crest_with_ground_sphere_and_tangents(
    n1,
    n2,
    sphere_radius,
    npts_arc=220,
    npts_line=80
):
    """
    Caso L_3D > 2S:
      tangente + arco inferior de esfera apoyada en suelo + tangente.
    """
    x1, y1, h1 = n1["x"], n1["y"], n1["z"]
    x2, y2, h2 = n2["x"], n2["y"], n2["z"]

    dx = x2 - x1
    dy = y2 - y1
    dxy = np.hypot(dx, dy)

    if dxy < 1e-12:
        return None

    A = np.array([0.0, h1], dtype=float)
    B = np.array([dxy, h2], dtype=float)
    C = np.array([0.5 * dxy, sphere_radius], dtype=float)

    T_A = choose_inner_tangent_point_2d(
        P=A,
        C=C,
        R=sphere_radius,
        side="left"
    )

    T_B = choose_inner_tangent_point_2d(
        P=B,
        C=C,
        R=sphere_radius,
        side="right"
    )

    if T_A is None or T_B is None:
        return None

    if T_A[0] > T_B[0]:
        T_A, T_B = T_B, T_A

    u_left = np.linspace(A[0], T_A[0], npts_line)
    z_left = np.linspace(A[1], T_A[1], npts_line)

    u_arc = np.linspace(T_A[0], T_B[0], npts_arc)

    inside = sphere_radius**2 - (u_arc - C[0])**2
    inside = np.maximum(inside, 0.0)

    z_arc = C[1] - np.sqrt(inside)
    z_arc = np.maximum(z_arc, 0.0)

    u_right = np.linspace(T_B[0], B[0], npts_line)
    z_right = np.linspace(T_B[1], B[1], npts_line)

    u = np.concatenate([u_left, u_arc[1:], u_right[1:]])
    z = np.concatenate([z_left, z_arc[1:], z_right[1:]])

    z = np.maximum(z, 0.0)

    ex = dx / dxy
    ey = dy / dxy

    x = x1 + u * ex
    y = y1 + u * ey

    z[0] = h1
    z[-1] = h2

    return x, y, z


def base_crest_between_two_masts(n1, n2, sphere_radius, npts=220):
    """
    Modelo base:
      - L_3D <= 2S -> cresta normal.
      - L_3D >  2S -> cresta larga al suelo.
    """
    dxy = np.hypot(n2["x"] - n1["x"], n2["y"] - n1["y"])
    dz = n2["z"] - n1["z"]
    chord_len = np.hypot(dxy, dz)

    if dxy < 1e-12:
        return None, "base_none", chord_len

    if chord_len <= 2.0 * sphere_radius:
        curve = real_spherical_crest_between_two_masts(
            n1=n1,
            n2=n2,
            sphere_radius=sphere_radius,
            npts=npts
        )

        return curve, "base_normal_L_le_2S", chord_len

    curve = long_crest_with_ground_sphere_and_tangents(
        n1=n1,
        n2=n2,
        sphere_radius=sphere_radius,
        npts_arc=npts,
        npts_line=max(40, npts // 3)
    )

    return curve, "base_long_L_gt_2S", chord_len


def straight_guard_wire_between_two_masts(n1, n2, npts=180):
    x = np.linspace(n1["x"], n2["x"], npts)
    y = np.linspace(n1["y"], n2["y"], npts)
    z = np.linspace(n1["z"], n2["z"], npts)

    z = np.maximum(z, 0.0)

    return x, y, z


def unique_mast_edges_from_triangles(triangles):
    edge_nodes = {}

    for tri in triangles:
        nodes = tri["nodes"]

        for a, b in [(0, 1), (1, 2), (2, 0)]:
            n1 = nodes[a]
            n2 = nodes[b]

            if n1["type"] != "mast_top" or n2["type"] != "mast_top":
                continue

            key = edge_key(n1["label"], n2["label"])
            edge_nodes[key] = (n1, n2)

    return edge_nodes


def unique_mast_q_edges_from_triangles(triangles):
    edge_nodes = {}

    for tri in triangles:
        nodes = tri["nodes"]

        for a, b in [(0, 1), (1, 2), (2, 0)]:
            n1 = nodes[a]
            n2 = nodes[b]

            types = {n1["type"], n2["type"]}

            if types != {"mast_top", "Q"}:
                continue

            mast_node = n1 if n1["type"] == "mast_top" else n2
            q_node = n1 if n1["type"] == "Q" else n2

            key = (mast_node["label"], q_node["label"])
            edge_nodes[key] = (mast_node, q_node)

    return edge_nodes


def build_common_tetra_edges_from_triangles(triangles):
    return set(unique_mast_edges_from_triangles(triangles).keys())


def build_base_crest_registry(
    tri_nodes,
    triangles,
    sphere_radius,
    guard_wire_inputs=None,
    npts=220
):
    mast_nodes = make_mast_nodes_from_tri_nodes(tri_nodes)
    mm_edges = unique_mast_edges_from_triangles(triangles)
    mq_edges = unique_mast_q_edges_from_triangles(triangles)
    common_edges = build_common_tetra_edges_from_triangles(triangles)

    registry = {}

    for key, (n1, n2) in mm_edges.items():

        if edge_has_guard_wire(n1["label"], n2["label"], guard_wire_inputs):
            curve = straight_guard_wire_between_two_masts(
                n1=n1,
                n2=n2,
                npts=npts
            )

            C = curve_to_array(curve)
            C = orient_curve_xyz(C, n1, n2)

            registry[key] = {
                "edge": key,
                "nodes": (n1, n2),
                "curve": C,
                "kind": "Cable de guarda directo",
                "source": "direct_guard_wire",
                "priority": 100,
                "replaceable": False,
                "info": {
                    "case_type": "direct_guard_wire"
                }
            }

            continue

        curve, base_kind, chord_len = base_crest_between_two_masts(
            n1=n1,
            n2=n2,
            sphere_radius=sphere_radius,
            npts=npts
        )

        C = curve_to_array(curve)

        if C is None:
            registry[key] = {
                "edge": key,
                "nodes": (n1, n2),
                "curve": None,
                "kind": "No calculada",
                "source": "base_failed",
                "priority": -1,
                "replaceable": True,
                "info": {
                    "case_type": "base_failed",
                    "chord_len": chord_len
                }
            }
            continue

        C = orient_curve_xyz(C, n1, n2)

        if base_kind == "base_normal_L_le_2S":
            kind = "Cresta base normal L≤2S"
        else:
            kind = "Cresta base larga al suelo L>2S"

        registry[key] = {
            "edge": key,
            "nodes": (n1, n2),
            "curve": C,
            "kind": kind,
            "source": base_kind,
            "priority": 0,
            "replaceable": True,
            "info": {
                "case_type": base_kind,
                "chord_len": chord_len
            }
        }

    return {
        "crest_registry": registry,
        "mast_nodes": mast_nodes,
        "mm_edges": mm_edges,
        "mq_edges": mq_edges,
        "common_tetra_edges": common_edges,
        "guard_wire_inputs": guard_wire_inputs,
    }


def get_registry_curve(registry, label1, label2):
    key = edge_key(label1, label2)
    item = registry.get(key, None)

    if item is None:
        return None

    return item.get("curve", None)


def registry_color_and_width(item):
    source = item.get("source", "")
    kind = item.get("kind", "")

    if source == "direct_guard_wire":
        return "green", 9

    if source == "four_guard_closed":
        return "dodgerblue", 12

    if source == "three_guard_chain":
        return "deepskyblue", 11

    if source == "shared_guard_plus_k":
        return "cyan", 10

    if source == "independent_guard_lines":
        return "purple", 9

    if "larga" in kind or "suelo" in kind or "L>2S" in kind:
        return "red", 7

    return "orange", 7


def add_masts_and_q_points_to_fig(fig, tri_nodes):
    for n in tri_nodes:
        if n["type"] == "mast_top":
            fig.add_trace(go.Scatter3d(
                x=[n["x"], n["x"]],
                y=[n["y"], n["y"]],
                z=[0.0, n["z"]],
                mode="lines",
                line=dict(width=7, color="blue"),
                name=f"Mástil {n['label']}"
            ))

            fig.add_trace(go.Scatter3d(
                x=[n["x"]],
                y=[n["y"]],
                z=[n["z"]],
                mode="markers+text",
                marker=dict(size=6, color="black"),
                text=[n["label"]],
                textposition="top center",
                name=n["label"]
            ))

        elif n["type"] == "Q":
            fig.add_trace(go.Scatter3d(
                x=[n["x"]],
                y=[n["y"]],
                z=[n["z"]],
                mode="markers+text",
                marker=dict(size=5, color="orange"),
                text=[n["label"]],
                textposition="top center",
                name=n["label"]
            ))


def add_mq_segments_to_fig(fig, mq_edges):
    for key, (m_node, q_node) in mq_edges.items():
        fig.add_trace(go.Scatter3d(
            x=[m_node["x"], q_node["x"]],
            y=[m_node["y"], q_node["y"]],
            z=[m_node["z"], q_node["z"]],
            mode="lines",
            line=dict(width=5, dash="dash", color="red"),
            name=f"Segmento {key[0]}-{key[1]}"
        ))


def add_mmm_borders_to_fig(fig, triangles):
    for k, tri in enumerate(triangles):
        if classify_triangle_type(tri) != "M-M-M":
            continue

        n1, n2, n3 = tri["nodes"]

        fig.add_trace(go.Scatter3d(
            x=[n1["x"], n2["x"], n3["x"], n1["x"]],
            y=[n1["y"], n2["y"], n3["y"], n1["y"]],
            z=[n1["z"], n2["z"], n3["z"], n1["z"]],
            mode="lines",
            line=dict(width=4, color="rgba(80,80,80,0.50)"),
            name=f"Borde M-M-M {k}"
        ))


def add_ground_plane_to_fig(fig, tri_nodes, sphere_radius):
    xy = np.array([[n["x"], n["y"]] for n in tri_nodes], dtype=float)

    xmin, ymin = xy.min(axis=0) - sphere_radius - 5
    xmax, ymax = xy.max(axis=0) + sphere_radius + 5

    Xg, Yg = np.meshgrid(
        np.linspace(xmin, xmax, 2),
        np.linspace(ymin, ymax, 2)
    )

    fig.add_trace(go.Surface(
        x=Xg,
        y=Yg,
        z=np.zeros_like(Xg),
        opacity=0.08,
        showscale=False,
        hoverinfo="skip",
        name="Suelo"
    ))


def plot_crest_registry(
    tri_nodes,
    triangles,
    registry_result,
    sphere_radius,
    title="Registro de crestas",
    show_mmm_borders=True,
    show_mm_crests=True,
    show_mq_segments=True,
    show_ground=True
):
    fig_mmq_esferico_rendijas = go.Figure()
    fig = fig_mmq_esferico_rendijas

    registry = registry_result["crest_registry"]
    mq_edges = registry_result["mq_edges"]

    if show_mmm_borders:
        add_mmm_borders_to_fig(fig, triangles)

    if show_mm_crests:
        for key, item in registry.items():
            C = item.get("curve", None)

            if C is None:
                continue

            color, width = registry_color_and_width(item)

            fig.add_trace(go.Scatter3d(
                x=C[:, 0],
                y=C[:, 1],
                z=C[:, 2],
                mode="lines",
                line=dict(width=width, color=color),
                name=f"{item['kind']} {key[0]}-{key[1]}"
            ))

    if show_mq_segments:
        add_mq_segments_to_fig(fig, mq_edges)

    add_masts_and_q_points_to_fig(fig, tri_nodes)

    if show_ground:
        add_ground_plane_to_fig(fig, tri_nodes, sphere_radius)

    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="data"
        ),
        height=900,
        showlegend=True
    )

    fig.show()

    return fig


import copy


import numpy as np


import plotly.graph_objects as go


from itertools import combinations


from scipy.optimize import least_squares


SHOW_IMAGINARY_LINES = True


SHOW_SUPPORT_SPHERE = True


SHOW_SPHERE_XY_PROJECTION = True


SHOW_CONTACT_POINTS = True


SHOW_RADII_TO_CONTACTS = True


SHOW_THREE_GUARD_SPHERE = True


SHOW_THREE_GUARD_CONTACTS = True


SHOW_THREE_GUARD_RADII = True


SHOW_THREE_GUARD_XY_PROJECTION = True


SHOW_FOUR_GUARD_SPHERE = True


SHOW_FOUR_GUARD_CONTACTS = True


SHOW_FOUR_GUARD_RADII = True


SHOW_FOUR_GUARD_XY_PROJECTION = True


ENABLE_THREE_GUARD_CHAIN_CASE = True


SHOW_SHARED_FREE_EDGE = False


def registry_priority(source):
    priorities = {
        "direct_guard_wire": 100,
        "four_guard_closed": 90,
        "three_guard_chain": 70,
        "shared_guard_plus_k": 60,
        "shared_guard_free_edge_omitted": 60,
        "independent_guard_lines": 50,
    }

    return priorities.get(source, 0)


def override_registry_edge(
    registry,
    label1,
    label2,
    curve,
    kind,
    source,
    info=None,
    log=None
):
    """
    Reemplaza una arista del registro solo si:
      - existe en el registro;
      - no es cable directo;
      - no está omitida;
      - el nuevo caso tiene prioridad igual o mayor.
    """
    key = edge_key(label1, label2)

    if key not in registry:
        if log is not None:
            log.append({
                "edge": key,
                "source": source,
                "status": "skip_edge_not_in_registry"
            })
        return False

    item = registry[key]

    if item.get("source") == "direct_guard_wire":
        if log is not None:
            log.append({
                "edge": key,
                "source": source,
                "status": "skip_direct_guard_wire"
            })
        return False

    if item.get("omit", False):
        if log is not None:
            log.append({
                "edge": key,
                "source": source,
                "status": "skip_edge_omitted",
                "old_source": item.get("source")
            })
        return False

    new_priority = registry_priority(source)
    old_priority = item.get("priority", 0)

    if new_priority < old_priority:
        if log is not None:
            log.append({
                "edge": key,
                "source": source,
                "status": "skip_lower_priority",
                "old_source": item.get("source")
            })
        return False

    n1, n2 = item["nodes"]

    C = curve_to_array(curve)

    if C is None:
        if log is not None:
            log.append({
                "edge": key,
                "source": source,
                "status": "skip_invalid_curve"
            })
        return False

    C = resample_curve_xyz(C, npts=max(80, len(C)))
    C = orient_curve_xyz(C, n1, n2)

    old_source = item.get("source")

    registry[key] = {
        **item,
        "curve": C,
        "kind": kind,
        "source": source,
        "priority": new_priority,
        "replaceable": True,
        "omit": False,
        "info": info if info is not None else {
            "case_type": source
        },
        "overwritten_from": old_source
    }

    if log is not None:
        log.append({
            "edge": key,
            "source": source,
            "status": "replaced",
            "old_source": old_source
        })

    return True


def omit_registry_edge(
    registry,
    label1,
    label2,
    kind,
    source,
    info=None,
    log=None
):
    """
    Marca una arista como omitida.

    Esto evita que:
      - se dibuje como cresta;
      - se use como frontera MMM/MMQ;
      - sea reemplazada después por otro caso de menor prioridad.
    """
    key = edge_key(label1, label2)

    if key not in registry:
        if log is not None:
            log.append({
                "edge": key,
                "source": source,
                "status": "skip_omit_edge_not_in_registry"
            })
        return False

    item = registry[key]

    if item.get("source") == "direct_guard_wire":
        if log is not None:
            log.append({
                "edge": key,
                "source": source,
                "status": "skip_omit_direct_guard_wire"
            })
        return False

    new_priority = registry_priority(source)
    old_priority = item.get("priority", 0)

    if new_priority < old_priority:
        if log is not None:
            log.append({
                "edge": key,
                "source": source,
                "status": "skip_omit_lower_priority",
                "old_source": item.get("source")
            })
        return False

    old_source = item.get("source")

    registry[key] = {
        **item,
        "curve": None,
        "kind": kind,
        "source": source,
        "priority": new_priority,
        "replaceable": False,
        "omit": True,
        "info": info if info is not None else {
            "case_type": source,
            "omit": True
        },
        "overwritten_from": old_source
    }

    if log is not None:
        log.append({
            "edge": key,
            "source": source,
            "status": "omitted",
            "old_source": old_source
        })

    return True


def is_edge_in_registry(registry, label1, label2):
    return edge_key(label1, label2) in registry


def is_common_tetra_edge(label1, label2, common_tetra_edges=None):
    if common_tetra_edges is None:
        return True

    return edge_key(label1, label2) in {
        edge_key(a, b)
        for a, b in common_tetra_edges
    }


def node_by_label_from_masts(mast_nodes):
    return {n["label"]: n for n in mast_nodes}


def guard_edges_from_inputs(guard_wire_inputs, mast_nodes):
    """
    Devuelve los cables de guarda reales como pares de etiquetas:
        [("M1", "M2"), ("M4", "M5"), ...]

    Solo incluye cables cuyos mástiles existan en mast_nodes.
    """
    node_by_label = node_by_label_from_masts(mast_nodes)

    guard_edges = []

    if guard_wire_inputs is None:
        return guard_edges

    for w in guard_wire_inputs:
        a = f"M{w['i']}"
        b = f"M{w['j']}"

        if a not in node_by_label or b not in node_by_label:
            continue

        guard_edges.append(edge_key(a, b))

    return sorted(set(guard_edges))


def make_guard_pair_key(edge1, edge2):
    """
    Llave canónica para un par de cables de guarda.
    """
    e1 = edge_key(edge1[0], edge1[1])
    e2 = edge_key(edge2[0], edge2[1])

    return tuple(sorted([e1, e2]))


def tangent_points_from_point_to_circle_2d(P, C, R, tol=1e-8):
    """
    Tangentes desde un punto P a una circunferencia 2D.

    Corrección:
    - Si P está exactamente sobre la circunferencia, se acepta P
      como punto de tangencia.
    - Si P está dentro, no hay tangentes.
    """
    P = np.asarray(P, dtype=float)
    C = np.asarray(C, dtype=float)

    v = P - C
    D = np.linalg.norm(v)

    if D < R - tol:
        return []

    if abs(D - R) <= tol:
        return [P.copy()]

    e = v / D
    p = np.array([-e[1], e[0]])

    a = R**2 / D
    b = R * np.sqrt(max(D**2 - R**2, 0.0)) / D

    T1 = C + a * e + b * p
    T2 = C + a * e - b * p

    return [T1, T2]


def choose_inner_tangent_point_2d(P, C, R, side):
    tangents = tangent_points_from_point_to_circle_2d(P, C, R)

    if not tangents:
        return None

    if side == "left":
        candidates = [T for T in tangents if T[0] >= P[0] - 1e-9]
    elif side == "right":
        candidates = [T for T in tangents if T[0] <= P[0] + 1e-9]
    else:
        candidates = tangents

    if not candidates:
        candidates = tangents

    return min(candidates, key=lambda T: T[1])


def closest_point_on_segment_3d(P, A, B):
    P = np.asarray(P, dtype=float)
    A = np.asarray(A, dtype=float)
    B = np.asarray(B, dtype=float)

    AB = B - A
    den = np.dot(AB, AB)

    if den < 1e-12:
        return A.copy(), 0.0

    t = np.dot(P - A, AB) / den
    t = np.clip(t, 0.0, 1.0)

    Q = A + t * AB

    return Q, t


def distance_point_to_segment_3d(P, A, B):
    Q, t = closest_point_on_segment_3d(P, A, B)
    return np.linalg.norm(P - Q), Q, t


def lower_support_crest_from_sphere_between_points(n1, n2, O, R, npts=240):
    """
    Cresta inferior asociada a una esfera 3D.

    Se usa el plano definido por:
      - punto 1;
      - punto 2;
      - centro O.
    """
    P1 = node_point(n1)
    P2 = node_point(n2)
    O = np.asarray(O, dtype=float)

    e1 = P2 - P1
    L = np.linalg.norm(e1)

    if L < 1e-12:
        return None

    e1 = e1 / L

    O_proj = P1 + np.dot(O - P1, e1) * e1
    e2 = O - O_proj

    if np.linalg.norm(e2) < 1e-9:
        aux = np.array([0.0, 0.0, 1.0])
        e2 = aux - np.dot(aux, e1) * e1

    if np.linalg.norm(e2) < 1e-9:
        aux = np.array([0.0, 1.0, 0.0])
        e2 = aux - np.dot(aux, e1) * e1

    e2 = e2 / np.linalg.norm(e2)

    def to_local(P):
        rel = P - P1

        return np.array([
            np.dot(rel, e1),
            np.dot(rel, e2)
        ])

    def to_global(u, w):
        return P1 + u * e1 + w * e2

    A = to_local(P1)
    B = to_local(P2)
    C = to_local(O)

    T_A = choose_inner_tangent_point_2d(A, C, R, side="left")
    T_B = choose_inner_tangent_point_2d(B, C, R, side="right")

    if T_A is None or T_B is None:
        return None

    if T_A[0] > T_B[0]:
        T_A, T_B = T_B, T_A

    n_line = max(50, npts // 4)

    u_left = np.linspace(A[0], T_A[0], n_line)
    w_left = np.linspace(A[1], T_A[1], n_line)

    u_arc = np.linspace(T_A[0], T_B[0], npts)

    inside = R**2 - (u_arc - C[0])**2
    inside = np.maximum(inside, 0.0)

    w_arc = C[1] - np.sqrt(inside)

    u_right = np.linspace(T_B[0], B[0], n_line)
    w_right = np.linspace(T_B[1], B[1], n_line)

    u = np.concatenate([u_left, u_arc[1:], u_right[1:]])
    w = np.concatenate([w_left, w_arc[1:], w_right[1:]])

    pts = np.array([to_global(ui, wi) for ui, wi in zip(u, w)])

    pts[:, 2] = np.maximum(pts[:, 2], 0.0)
    pts[0, :] = P1
    pts[-1, :] = P2

    return pts[:, 0], pts[:, 1], pts[:, 2]


def solve_support_sphere_below_contacts(seg1, seg2, point, R):
    A1, B1 = [np.asarray(p, dtype=float) for p in seg1]
    A2, B2 = [np.asarray(p, dtype=float) for p in seg2]
    P = np.asarray(point, dtype=float)

    mid1 = 0.5 * (A1 + B1)
    mid2 = 0.5 * (A2 + B2)
    centroid = (mid1 + mid2 + P) / 3.0

    seeds = []

    for dz in [0.25 * R, 0.5 * R, R, 1.5 * R, 2.0 * R]:
        seeds.append(centroid + np.array([0.0, 0.0, dz]))

    for sx in [-R, 0.0, R]:
        for sy in [-R, 0.0, R]:
            for dz in [0.5 * R, R, 1.5 * R]:
                seeds.append(centroid + np.array([sx, sy, dz]))

    def residual(O):
        O = np.asarray(O, dtype=float)

        d1, _, _ = distance_point_to_segment_3d(O, A1, B1)
        d2, _, _ = distance_point_to_segment_3d(O, A2, B2)
        d3 = np.linalg.norm(O - P)

        return np.array([
            d1 - R,
            d2 - R,
            d3 - R
        ])

    best = None

    for seed in seeds:
        sol = least_squares(
            residual,
            x0=seed,
            xtol=1e-11,
            ftol=1e-11,
            gtol=1e-11,
            max_nfev=5000
        )

        O = sol.x
        err = np.linalg.norm(residual(O))

        d1, Q1, t1 = distance_point_to_segment_3d(O, A1, B1)
        d2, Q2, t2 = distance_point_to_segment_3d(O, A2, B2)
        d3 = np.linalg.norm(O - P)

        inside_segments = (
            -1e-6 <= t1 <= 1.0 + 1e-6 and
            -1e-6 <= t2 <= 1.0 + 1e-6
        )

        contacts_below_center = (
            Q1[2] < O[2] - 1e-6 and
            Q2[2] < O[2] - 1e-6 and
            P[2]  < O[2] - 1e-6
        )

        plausible = O[2] > max(Q1[2], Q2[2], P[2])

        if not inside_segments:
            continue

        if not contacts_below_center:
            continue

        if not plausible:
            continue

        if err > 1e-5:
            continue

        candidate = {
            "O": O,
            "Q1": Q1,
            "Q2": Q2,
            "Q3": P,
            "t1": t1,
            "t2": t2,
            "d1": d1,
            "d2": d2,
            "d3": d3,
            "err": err,
            "score": O[2]
        }

        if best is None or candidate["score"] < best["score"]:
            best = candidate

    return best


def solve_support_sphere_below_three_segments(seg1, seg2, seg3, R):
    A1, B1 = [np.asarray(p, dtype=float) for p in seg1]
    A2, B2 = [np.asarray(p, dtype=float) for p in seg2]
    A3, B3 = [np.asarray(p, dtype=float) for p in seg3]

    mid1 = 0.5 * (A1 + B1)
    mid2 = 0.5 * (A2 + B2)
    mid3 = 0.5 * (A3 + B3)

    centroid = (mid1 + mid2 + mid3) / 3.0

    seeds = []

    for dz in [0.25 * R, 0.5 * R, R, 1.5 * R, 2.0 * R, 2.5 * R]:
        seeds.append(centroid + np.array([0.0, 0.0, dz]))

    for sx in [-R, 0.0, R]:
        for sy in [-R, 0.0, R]:
            for dz in [0.5 * R, R, 1.5 * R, 2.0 * R]:
                seeds.append(centroid + np.array([sx, sy, dz]))

    def residual(O):
        O = np.asarray(O, dtype=float)

        d1, _, _ = distance_point_to_segment_3d(O, A1, B1)
        d2, _, _ = distance_point_to_segment_3d(O, A2, B2)
        d3, _, _ = distance_point_to_segment_3d(O, A3, B3)

        return np.array([
            d1 - R,
            d2 - R,
            d3 - R
        ])

    best = None

    for seed in seeds:
        sol = least_squares(
            residual,
            x0=seed,
            xtol=1e-11,
            ftol=1e-11,
            gtol=1e-11,
            max_nfev=5000
        )

        O = sol.x
        err = np.linalg.norm(residual(O))

        d1, Q1, t1 = distance_point_to_segment_3d(O, A1, B1)
        d2, Q2, t2 = distance_point_to_segment_3d(O, A2, B2)
        d3, Q3, t3 = distance_point_to_segment_3d(O, A3, B3)

        inside_segments = (
            -1e-6 <= t1 <= 1.0 + 1e-6 and
            -1e-6 <= t2 <= 1.0 + 1e-6 and
            -1e-6 <= t3 <= 1.0 + 1e-6
        )

        contacts_below_center = (
            Q1[2] < O[2] - 1e-6 and
            Q2[2] < O[2] - 1e-6 and
            Q3[2] < O[2] - 1e-6
        )

        plausible = O[2] > max(Q1[2], Q2[2], Q3[2])

        if not inside_segments:
            continue

        if not contacts_below_center:
            continue

        if not plausible:
            continue

        if err > 1e-5:
            continue

        candidate = {
            "O": O,
            "Q1": Q1,
            "Q2": Q2,
            "Q3": Q3,
            "t1": t1,
            "t2": t2,
            "t3": t3,
            "d1": d1,
            "d2": d2,
            "d3": d3,
            "err": err,
            "score": O[2]
        }

        if best is None or candidate["score"] < best["score"]:
            best = candidate

    return best


SHOW_INDEPENDENT_MODULE_DEBUG = False


def orient2d(a, b, c):
    return (
        (b[0] - a[0]) * (c[1] - a[1])
        - (b[1] - a[1]) * (c[0] - a[0])
    )


def segments_cross_xy(a, b, c, d, tol=1e-9):
    a = np.asarray(a, dtype=float)[:2]
    b = np.asarray(b, dtype=float)[:2]
    c = np.asarray(c, dtype=float)[:2]
    d = np.asarray(d, dtype=float)[:2]

    o1 = orient2d(a, b, c)
    o2 = orient2d(a, b, d)
    o3 = orient2d(c, d, a)
    o4 = orient2d(c, d, b)

    return (o1 * o2 < -tol) and (o3 * o4 < -tol)


def closest_point_on_segment_xy(P, A, B):
    P = np.asarray(P, dtype=float)
    A = np.asarray(A, dtype=float)
    B = np.asarray(B, dtype=float)

    AB = B - A
    den = np.dot(AB, AB)

    if den < 1e-12:
        return A, 0.0, np.linalg.norm(P - A)

    t = np.dot(P - A, AB) / den
    t = np.clip(t, 0.0, 1.0)

    Q = A + t * AB
    d = np.linalg.norm(P - Q)

    return Q, t, d


def xy_dist(n1, n2):
    p1 = np.array([n1["x"], n1["y"]], dtype=float)
    p2 = np.array([n2["x"], n2["y"]], dtype=float)
    return float(np.linalg.norm(p1 - p2))


def node_xy(n):
    return np.array([n["x"], n["y"]], dtype=float)


def point_on_segment_xy(P, A, B, tol=1e-7):
    P = np.asarray(P, dtype=float)[:2]
    A = np.asarray(A, dtype=float)[:2]
    B = np.asarray(B, dtype=float)[:2]

    AB = B - A
    den = np.dot(AB, AB)

    if den < 1e-12:
        return np.linalg.norm(P - A) <= tol

    t = np.dot(P - A, AB) / den

    if t < -tol or t > 1.0 + tol:
        return False

    Q = A + np.clip(t, 0.0, 1.0) * AB
    return np.linalg.norm(P - Q) <= tol


def point_in_polygon_xy_local(point_xy, polygon_xy, include_boundary=False, tol=1e-9):
    x, y = point_xy
    poly = np.asarray(polygon_xy, dtype=float)
    n = len(poly)

    for i in range(n):
        if point_on_segment_xy(point_xy, poly[i], poly[(i + 1) % n], tol=1e-7):
            return bool(include_boundary)

    inside = False

    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]

        cond = ((y1 > y) != (y2 > y))

        if cond:
            x_inter = x1 + (y - y1) * (x2 - x1) / (y2 - y1 + 1e-15)

            if x_inter > x + tol:
                inside = not inside

    return inside


def polygon_area_xy(poly):
    poly = np.asarray(poly, dtype=float)
    x = poly[:, 0]
    y = poly[:, 1]
    return 0.5 * float(abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))


def build_imaginary_line_family_for_edge(n1, n2, a, b, sphere_radius, npts=220):
    """
    Para una diagonal n1-n2 generada por dos guardas independientes.

    Si el módulo local tiene laterales:
        n1-b
        a-n2

    esas laterales se usan SOLO como curvas guía. No se reemplazan
    como aristas del registro.
    """
    crest_1, _, _ = base_crest_between_two_masts(
        n1=n1,
        n2=b,
        sphere_radius=sphere_radius,
        npts=npts
    )

    crest_2, _, _ = base_crest_between_two_masts(
        n1=a,
        n2=n2,
        sphere_radius=sphere_radius,
        npts=npts
    )

    if crest_1 is None or crest_2 is None:
        return None

    C1 = curve_to_array(crest_1)
    C2 = curve_to_array(crest_2)

    C1 = orient_curve_xyz(C1, n1, b)
    C2 = orient_curve_xyz(C2, a, n2)

    C1 = resample_curve_xyz(C1, npts=npts)
    C2 = resample_curve_xyz(C2, npts=npts)

    return C1, C2


def build_crest_from_imaginary_lines(n1, n2, C1, C2, npts=220):
    x = np.linspace(n1["x"], n2["x"], npts)
    y = np.linspace(n1["y"], n2["y"], npts)

    z = np.zeros(npts)

    for k in range(npts):
        P = np.array([x[k], y[k]], dtype=float)

        best_d = np.inf
        best_z = None

        for pA, pB in zip(C1, C2):
            Axy = pA[:2]
            Bxy = pB[:2]

            _, t, d = closest_point_on_segment_xy(P, Axy, Bxy)

            if d < best_d:
                best_d = d
                best_z = (1.0 - t) * pA[2] + t * pB[2]

        z[k] = 0.0 if best_z is None else best_z

    z = np.maximum(z, 0.0)
    z[0] = n1["z"]
    z[-1] = n2["z"]

    return x, y, z


def independent_module_orientation(edge1, edge2, node_by_label):
    """
    Decide automáticamente laterales y diagonales para dos guardas independientes.

    edge1 = A-B
    edge2 = C-D

    Opción 1:
      laterales  = A-C, B-D
      diagonales = A-D, B-C
      polígono   = A-B-D-C

    Opción 2:
      laterales  = A-D, B-C
      diagonales = A-C, B-D
      polígono   = A-B-C-D

    Se escoge la opción con menor suma de laterales en XY. Esto hace que
    las guardas mismas definan automáticamente los laterales del módulo.
    """
    A_label, B_label = edge1
    C_label, D_label = edge2

    A = node_by_label[A_label]
    B = node_by_label[B_label]
    C = node_by_label[C_label]
    D = node_by_label[D_label]

    options = []

    options.append({
        "orientation": "AC_BD_laterals",
        "guard_edge_1": edge_key(A_label, B_label),
        "guard_edge_2": edge_key(C_label, D_label),
        "A": A,
        "B": B,
        "C": C,
        "D": D,
        "lateral_1": edge_key(A_label, C_label),
        "lateral_2": edge_key(B_label, D_label),
        "diagonal_1": edge_key(A_label, D_label),
        "diagonal_2": edge_key(B_label, C_label),
        "diag_1_nodes": (A, D, B, C),
        "diag_2_nodes": (B, C, A, D),
        "polygon_labels": [A_label, B_label, D_label, C_label],
        "polygon_xy": np.array([node_xy(A), node_xy(B), node_xy(D), node_xy(C)]),
        "lateral_score": xy_dist(A, C) + xy_dist(B, D),
        "diagonal_score": xy_dist(A, D) + xy_dist(B, C),
        "diagonals_cross": segments_cross_xy(node_point(A), node_point(D), node_point(B), node_point(C)),
        "laterals_cross": segments_cross_xy(node_point(A), node_point(C), node_point(B), node_point(D)),
    })

    options.append({
        "orientation": "AD_BC_laterals",
        "guard_edge_1": edge_key(A_label, B_label),
        "guard_edge_2": edge_key(C_label, D_label),
        "A": A,
        "B": B,
        "C": C,
        "D": D,
        "lateral_1": edge_key(A_label, D_label),
        "lateral_2": edge_key(B_label, C_label),
        "diagonal_1": edge_key(A_label, C_label),
        "diagonal_2": edge_key(B_label, D_label),
        "diag_1_nodes": (A, C, B, D),
        "diag_2_nodes": (B, D, A, C),
        "polygon_labels": [A_label, B_label, C_label, D_label],
        "polygon_xy": np.array([node_xy(A), node_xy(B), node_xy(C), node_xy(D)]),
        "lateral_score": xy_dist(A, D) + xy_dist(B, C),
        "diagonal_score": xy_dist(A, C) + xy_dist(B, D),
        "diagonals_cross": segments_cross_xy(node_point(A), node_point(C), node_point(B), node_point(D)),
        "laterals_cross": segments_cross_xy(node_point(A), node_point(D), node_point(B), node_point(C)),
    })

    valid = []

    for opt in options:
        area = polygon_area_xy(opt["polygon_xy"])
        opt["polygon_area"] = area

        if area <= 1e-9:
            continue

        # Las laterales no deberían cruzarse entre sí.
        if opt["laterals_cross"]:
            continue

        valid.append(opt)

    if not valid:
        return None

    # Preferir laterales cortas y, si hay empate, diagonales que crucen.
    valid.sort(key=lambda o: (
        o["lateral_score"],
        0 if o["diagonals_cross"] else 1,
        -o["polygon_area"]
    ))

    return valid[0]


def guard_segment_midpoint_xy(edge, node_by_label):
    a, b = edge
    A = node_by_label[a]
    B = node_by_label[b]
    return 0.5 * (node_xy(A) + node_xy(B))


def module_contains_other_guard(module, guard_edges, node_by_label):
    """
    Rechaza módulos no locales.

    Si otra guarda queda dentro del cuadrilátero, entonces las dos guardas
    evaluadas no son vecinas; están saltándose un módulo intermedio.
    """
    polygon_xy = module["polygon_xy"]
    current_edges = {
        edge_key(*module["guard_edge_1"]),
        edge_key(*module["guard_edge_2"]),
    }

    for edge in guard_edges:
        ekey = edge_key(*edge)

        if ekey in current_edges:
            continue

        midpoint = guard_segment_midpoint_xy(edge, node_by_label)

        if point_in_polygon_xy_local(midpoint, polygon_xy, include_boundary=False):
            return True

        # También se rechaza si la guarda cruza claramente el interior.
        P = node_xy(node_by_label[edge[0]])
        Q = node_xy(node_by_label[edge[1]])

        poly = polygon_xy
        crosses = 0

        for i in range(len(poly)):
            R = poly[i]
            S2 = poly[(i + 1) % len(poly)]

            if segments_cross_xy(P, Q, R, S2):
                crosses += 1

        if crosses >= 2:
            return True

    return False


def module_has_cross_connection_as_guard(module, guard_edges_set):
    """
    Evita confundir este caso con:
      - tres guardas consecutivas;
      - cuadriláteros cerrados;
      - cualquier patrón donde una conexión cruzada ya sea cable real.
    """
    cross_edges = [
        module["lateral_1"],
        module["lateral_2"],
        module["diagonal_1"],
        module["diagonal_2"],
    ]

    return any(edge_key(*e) in guard_edges_set for e in cross_edges)


def independent_module_score(module):
    """
    Puntaje local para comparar posibles módulos de dos guardas independientes.

    Menor puntaje = módulo más local/probable.
    Se prioriza la suma de laterales porque las guardas reales definen
    los lados opuestos del módulo, y las laterales naturales suelen ser
    las conexiones cortas entre extremos correspondientes.
    """
    return (
        float(module.get("lateral_score", np.inf)),
        float(module.get("diagonal_score", np.inf)),
        -float(module.get("polygon_area", 0.0)),
        str(module.get("guard_pair", "")),
    )


def select_mutual_nearest_independent_modules(
    candidates,
    score_rel_tol=1e-7,
    score_abs_tol=1e-7,
    log=None
):
    """
    Selecciona módulos independientes locales para cadenas de 2, 3, 4, ... módulos.

    Problema que corrige:
      - Con varias guardas en cadena, no basta con aceptar todas las combinaciones
        posibles entre guardas independientes, porque aparecen pares no vecinos.

    Regla:
      - Cada cable de guarda se empareja con su mejor candidato geométrico local.
      - Un módulo se acepta solo si la relación es de vecinos mutuos:
            guarda 1 escoge guarda 2
            guarda 2 escoge guarda 1
      - Luego se aplica una selección greedy para evitar que un mismo cable quede
        asignado a dos módulos independientes distintos.

    Esto permite detectar automáticamente:
        módulo 1, módulo 2, módulo 3, ..., módulo N
    y, por tanto, proteger todas las interfaces compartidas entre ellos.
    """
    if not candidates:
        return []

    by_guard = {}

    for cand in candidates:
        for guard_edge in [cand["guard_edge_1"], cand["guard_edge_2"]]:
            by_guard.setdefault(edge_key(*guard_edge), []).append(cand)

    best_score_by_guard = {}

    for guard_edge, items in by_guard.items():
        best_score_by_guard[guard_edge] = min(
            independent_module_score(item)
            for item in items
        )

    mutual_candidates = []

    for cand in candidates:
        e1 = edge_key(*cand["guard_edge_1"])
        e2 = edge_key(*cand["guard_edge_2"])
        cand_score = independent_module_score(cand)

        best1 = best_score_by_guard[e1]
        best2 = best_score_by_guard[e2]

        # Se compara principalmente la suma de laterales, con tolerancia.
        # Los demás campos del score solo actúan como desempate estable.
        is_best_for_e1 = (
            abs(cand_score[0] - best1[0]) <= score_abs_tol + score_rel_tol * max(1.0, abs(best1[0]))
        )
        is_best_for_e2 = (
            abs(cand_score[0] - best2[0]) <= score_abs_tol + score_rel_tol * max(1.0, abs(best2[0]))
        )

        if is_best_for_e1 and is_best_for_e2:
            mutual_candidates.append(cand)
        else:
            if log is not None:
                log.append({
                    "edge": None,
                    "source": "independent_guard_lines",
                    "status": "skip_auto_module_not_mutual_nearest",
                    "guard_pair": cand.get("guard_pair"),
                    "orientation": cand.get("orientation"),
                    "candidate_score": cand_score,
                    "best_for_guard_1": best1,
                    "best_for_guard_2": best2,
                })

    # Selección final: un cable de guarda no debe quedar asignado a dos módulos
    # independientes distintos. Esto evita mezclas cuando hay 3 o más módulos.
    selected = []
    used_guard_edges = set()

    for cand in sorted(mutual_candidates, key=independent_module_score):
        e1 = edge_key(*cand["guard_edge_1"])
        e2 = edge_key(*cand["guard_edge_2"])

        if e1 in used_guard_edges or e2 in used_guard_edges:
            if log is not None:
                log.append({
                    "edge": None,
                    "source": "independent_guard_lines",
                    "status": "skip_auto_module_guard_already_paired",
                    "guard_pair": cand.get("guard_pair"),
                    "orientation": cand.get("orientation"),
                })
            continue

        used_guard_edges.add(e1)
        used_guard_edges.add(e2)
        selected.append(cand)

    return selected


def detect_independent_guard_modules_auto(
    mast_nodes,
    guard_wire_inputs,
    log=None
):
    """
    Detecta automáticamente módulos locales de dos guardas independientes.

    Generalización para cadenas de 2, 3, 4 o más módulos:
      1) Genera candidatos entre pares de guardas que no comparten mástil.
      2) Descarta casos que pertenecen a 3 guardas, 4 guardas o patrones no locales.
      3) Selecciona solo módulos de guardas vecinas mediante criterio de
         vecino mutuo.

    No usa una lista predefinida. La lista de guardas reales viene de
    guard_wire_inputs.
    """
    node_by_label = node_by_label_from_masts(mast_nodes)

    guard_edges = guard_edges_from_inputs(
        guard_wire_inputs=guard_wire_inputs,
        mast_nodes=mast_nodes
    )

    guard_edges_set = set(edge_key(*e) for e in guard_edges)

    candidate_modules = []
    seen = set()

    for edge1, edge2 in combinations(guard_edges, 2):

        # Dos guardas independientes NO comparten mástil.
        if set(edge1).intersection(set(edge2)):
            continue

        module = independent_module_orientation(
            edge1=edge1,
            edge2=edge2,
            node_by_label=node_by_label
        )

        if module is None:
            continue

        module["guard_pair"] = make_guard_pair_key(edge1, edge2)

        # Si una conexión cruzada es guarda real, no es el caso independiente.
        if module_has_cross_connection_as_guard(module, guard_edges_set):
            if log is not None:
                log.append({
                    "edge": None,
                    "source": "independent_guard_lines",
                    "status": "skip_auto_module_cross_connection_is_guard",
                    "guard_pair": module["guard_pair"],
                    "orientation": module["orientation"]
                })
            continue

        # Si hay otra guarda dentro del cuadrilátero, no son vecinas.
        if module_contains_other_guard(module, guard_edges, node_by_label):
            if log is not None:
                log.append({
                    "edge": None,
                    "source": "independent_guard_lines",
                    "status": "skip_auto_module_contains_other_guard",
                    "guard_pair": module["guard_pair"],
                    "orientation": module["orientation"]
                })
            continue

        module_key = (
            module["guard_pair"],
            module["orientation"]
        )

        if module_key in seen:
            continue

        seen.add(module_key)
        candidate_modules.append(module)

    modules = select_mutual_nearest_independent_modules(
        candidates=candidate_modules,
        log=log
    )

    # Orden estable para que los reportes sean legibles. No se usa para decidir
    # qué módulos existen; esa decisión ya quedó hecha por vecino mutuo.
    modules.sort(key=lambda m: (
        min(node_xy(m["A"])[0], node_xy(m["B"])[0], node_xy(m["C"])[0], node_xy(m["D"])[0]),
        min(node_xy(m["A"])[1], node_xy(m["B"])[1], node_xy(m["C"])[1], node_xy(m["D"])[1]),
        m["guard_pair"]
    ))

    for idx, module in enumerate(modules):
        module["module_index"] = idx

    return modules


def apply_one_auto_independent_diagonal(
    registry,
    n1,
    n2,
    a,
    b,
    module_info,
    diagonal_role,
    sphere_radius,
    log,
    protected_shared_lateral_edges=None
):
    """
    Calcula una diagonal interna de un módulo automático.

    Regla conservadora:
      - NO crea aristas nuevas.
      - NO reemplaza cables directos.
      - NO reemplaza casos especiales de mayor prioridad.
      - NO toca laterales/costillas.
    """
    main_edge = edge_key(n1["label"], n2["label"])

    # -----------------------------------------------------
    # Detalle importante:
    # Si esta arista es una lateral/interfaz compartida entre
    # dos módulos independientes consecutivos, se conserva como
    # venía del registro base o de un caso anterior.
    # No se recalcula como diagonal de otro módulo automático.
    # -----------------------------------------------------
    if (
        protected_shared_lateral_edges is not None
        and main_edge in protected_shared_lateral_edges
    ):
        log.append({
            "edge": main_edge,
            "source": "independent_guard_lines",
            "status": "skip_auto_diagonal_is_shared_lateral_between_modules",
            "module_index": module_info["module_index"],
            "diagonal_role": diagonal_role,
            "guard_pair": module_info["guard_pair"]
        })
        return False

    if main_edge not in registry:
        log.append({
            "edge": main_edge,
            "source": "independent_guard_lines",
            "status": "skip_auto_diagonal_not_in_registry",
            "module_index": module_info["module_index"],
            "diagonal_role": diagonal_role,
            "guard_pair": module_info["guard_pair"]
        })
        return False

    item = registry[main_edge]

    if item.get("source") == "direct_guard_wire":
        log.append({
            "edge": main_edge,
            "source": "independent_guard_lines",
            "status": "skip_auto_diagonal_is_direct_guard_wire",
            "module_index": module_info["module_index"],
            "diagonal_role": diagonal_role
        })
        return False

    if item.get("omit", False):
        log.append({
            "edge": main_edge,
            "source": "independent_guard_lines",
            "status": "skip_auto_diagonal_omitted",
            "module_index": module_info["module_index"],
            "diagonal_role": diagonal_role,
            "old_source": item.get("source")
        })
        return False

    # Conserva cualquier caso especial de mayor prioridad.
    if registry_priority(item.get("source")) > registry_priority("independent_guard_lines"):
        log.append({
            "edge": main_edge,
            "source": "independent_guard_lines",
            "status": "skip_auto_diagonal_higher_priority_source",
            "module_index": module_info["module_index"],
            "diagonal_role": diagonal_role,
            "old_source": item.get("source")
        })
        return False

    # Evita que dos módulos escriban la misma diagonal.
    if item.get("source") == "independent_guard_lines":
        log.append({
            "edge": main_edge,
            "source": "independent_guard_lines",
            "status": "skip_auto_diagonal_already_independent",
            "module_index": module_info["module_index"],
            "diagonal_role": diagonal_role,
            "old_source": item.get("source")
        })
        return False

    family = build_imaginary_line_family_for_edge(
        n1=n1,
        n2=n2,
        a=a,
        b=b,
        sphere_radius=sphere_radius,
        npts=220
    )

    if family is None:
        log.append({
            "edge": main_edge,
            "source": "independent_guard_lines",
            "status": "skip_auto_diagonal_invalid_imaginary_family",
            "module_index": module_info["module_index"],
            "diagonal_role": diagonal_role
        })
        return False

    C1, C2 = family

    crest = build_crest_from_imaginary_lines(
        n1=n1,
        n2=n2,
        C1=C1,
        C2=C2,
        npts=220
    )

    z_mean = float(np.mean(crest[2]))

    return override_registry_edge(
        registry=registry,
        label1=n1["label"],
        label2=n2["label"],
        curve=crest,
        kind="Cresta especial por dos guardas independientes",
        source="independent_guard_lines",
        info={
            "case_type": "independent_guard_lines",
            "mode": "auto_local_guard_module",
            "module_index": module_info["module_index"],
            "diagonal_role": diagonal_role,
            "orientation": module_info["orientation"],
            "C1": C1,
            "C2": C2,
            "a": a,
            "b": b,
            "guard_pair": module_info["guard_pair"],
            "guard_edge_1": module_info["guard_edge_1"],
            "guard_edge_2": module_info["guard_edge_2"],
            "lateral_1_not_recalculated": module_info["lateral_1"],
            "lateral_2_not_recalculated": module_info["lateral_2"],
            "diagonal_1": module_info["diagonal_1"],
            "diagonal_2": module_info["diagonal_2"],
            "z_mean": z_mean,
        },
        log=log
    )


def apply_independent_guard_overrides(
    registry,
    mast_nodes,
    guard_wire_inputs,
    sphere_radius,
    log,
    independent_guard_modules=None,
    protected_shared_lateral_edges=None
):
    """
    Aplica el caso de dos guardas independientes usando módulos
    automáticos locales.
    """
    modules = independent_guard_modules

    if modules is None:
        modules = detect_independent_guard_modules_auto(
            mast_nodes=mast_nodes,
            guard_wire_inputs=guard_wire_inputs,
            log=log
        )

    if protected_shared_lateral_edges is None:
        protected_shared_lateral_edges = find_shared_lateral_edges_between_auto_modules(
            independent_guard_modules=modules,
            log=log
        )

    for module_info in modules:
        n1, n2, a, b = module_info["diag_1_nodes"]

        apply_one_auto_independent_diagonal(
            registry=registry,
            n1=n1,
            n2=n2,
            a=a,
            b=b,
            module_info=module_info,
            diagonal_role="diagonal_1",
            sphere_radius=sphere_radius,
            log=log,
            protected_shared_lateral_edges=protected_shared_lateral_edges
        )

        n1, n2, a, b = module_info["diag_2_nodes"]

        apply_one_auto_independent_diagonal(
            registry=registry,
            n1=n1,
            n2=n2,
            a=a,
            b=b,
            module_info=module_info,
            diagonal_role="diagonal_2",
            sphere_radius=sphere_radius,
            log=log,
            protected_shared_lateral_edges=protected_shared_lateral_edges
        )


def make_shared_guard_context_key(edge1, edge2, k_label):
    """
    Llave contextual para bloquear shared_guard_plus_k solo si coinciden:
      - el par de guardas con mástil común;
      - el mástil K exacto.
    """
    return (
        make_guard_pair_key(edge1, edge2),
        k_label if isinstance(k_label, str) else f"M{int(k_label)}"
    )


def auto_module_lateral_records(module_info):
    """
    Devuelve las dos laterales de un módulo automático.

    Para cada lateral se identifica:
      - los dos extremos de la lateral;
      - la guarda real que llega a cada extremo.

    Esto permite bloquear falsos shared_guard_plus_k cuando dos módulos
    independientes comparten una misma lateral/interfaz.
    """
    A = module_info["A"]["label"]
    B = module_info["B"]["label"]
    C = module_info["C"]["label"]
    D = module_info["D"]["label"]

    if module_info["orientation"] == "AC_BD_laterals":
        return [
            {
                "lateral": edge_key(A, C),
                "endpoint_1": A,
                "endpoint_2": C,
                "guard_at_endpoint_1": edge_key(A, B),
                "guard_at_endpoint_2": edge_key(C, D),
                "module_index": module_info["module_index"],
            },
            {
                "lateral": edge_key(B, D),
                "endpoint_1": B,
                "endpoint_2": D,
                "guard_at_endpoint_1": edge_key(B, A),
                "guard_at_endpoint_2": edge_key(D, C),
                "module_index": module_info["module_index"],
            },
        ]

    return [
        {
            "lateral": edge_key(A, D),
            "endpoint_1": A,
            "endpoint_2": D,
            "guard_at_endpoint_1": edge_key(A, B),
            "guard_at_endpoint_2": edge_key(D, C),
            "module_index": module_info["module_index"],
        },
        {
            "lateral": edge_key(B, C),
            "endpoint_1": B,
            "endpoint_2": C,
            "guard_at_endpoint_1": edge_key(B, A),
            "guard_at_endpoint_2": edge_key(C, D),
            "module_index": module_info["module_index"],
        },
    ]


def build_blocked_shared_guard_context_keys_from_auto_modules(
    independent_guard_modules,
    log=None
):
    """
    Bloquea falsos shared_guard_plus_k generados entre módulos de dos
    guardas independientes que comparten una lateral/interfaz.

    Ejemplo:
      módulo 1: M4-M5 con M1-M2
      módulo 2: M1-M2 con M0-M3

    La lateral/interfaz compartida M1-M2 permite bloquear:
      - en M1, el par de guardas que llegan a M1 con K=M2;
      - en M2, el par de guardas que llegan a M2 con K=M1.
    """
    blocked = set()
    lateral_map = {}

    for module_info in independent_guard_modules:
        for rec in auto_module_lateral_records(module_info):
            lateral_map.setdefault(rec["lateral"], []).append(rec)

    for lateral, records in lateral_map.items():
        if len(records) < 2:
            continue

        for r1, r2 in combinations(records, 2):
            p = r1["endpoint_1"]
            q = r1["endpoint_2"]

            if edge_key(r2["endpoint_1"], r2["endpoint_2"]) != edge_key(p, q):
                continue

            g1_p = r1["guard_at_endpoint_1"]
            g2_p = r2["guard_at_endpoint_1"]
            blocked.add(make_shared_guard_context_key(g1_p, g2_p, q))

            g1_q = r1["guard_at_endpoint_2"]
            g2_q = r2["guard_at_endpoint_2"]
            blocked.add(make_shared_guard_context_key(g1_q, g2_q, p))

            if log is not None:
                log.append({
                    "edge": lateral,
                    "source": "independent_guard_lines",
                    "status": "shared_lateral_blocks_shared_guard_plus_k",
                    "module_1": r1["module_index"],
                    "module_2": r2["module_index"],
                    "blocked_at_p": make_shared_guard_context_key(g1_p, g2_p, q),
                    "blocked_at_q": make_shared_guard_context_key(g1_q, g2_q, p),
                })

    return blocked


def find_shared_lateral_edges_between_auto_modules(
    independent_guard_modules,
    log=None
):
    """
    Identifica laterales/interfases compartidas entre dos o más módulos
    automáticos de dos guardas independientes.

    Estas aristas NO deben recalcularse como crestas independientes,
    porque son la frontera común entre módulos consecutivos. Deben
    mantenerse tal como venían del registro base o del caso especial
    que las haya definido antes.

    Ejemplo:
      módulo 1: guardas M4-M5 y M1-M2 -> lateral M5-M2
      módulo 2: guardas M5-M11 y M2-M10 -> lateral M5-M2

    Entonces M5-M2 queda protegida.
    """
    lateral_map = {}

    for module_info in independent_guard_modules:
        for rec in auto_module_lateral_records(module_info):
            lateral_map.setdefault(rec["lateral"], []).append(rec)

    protected = {
        lateral
        for lateral, records in lateral_map.items()
        if len(records) >= 2
    }

    if log is not None:
        for lateral in sorted(protected):
            records = lateral_map[lateral]
            log.append({
                "edge": lateral,
                "source": "independent_guard_lines",
                "status": "protect_shared_lateral_between_independent_modules",
                "modules": [r["module_index"] for r in records]
            })

    return protected


def find_shared_guard_special_case_for_edge(
    n1,
    n2,
    mast_nodes,
    guard_wire_inputs,
    sphere_radius,
    common_tetra_edges=None,
    blocked_shared_guard_pair_keys=None,
    blocked_shared_guard_context_keys=None
):
    """
    Caso:
        n1 -- shared -- n2
                |
                K

    La esfera se apoya en:
      - guarda shared-n1;
      - guarda shared-n2;
      - mástil K.

    Corrección:
      - Si el par de guardas shared-n1 + shared-n2 ya pertenece
        localmente a un modelo de tres guardas o cuadrilátero,
        NO se evalúa como shared_guard_plus_k.
    """
    if edge_has_guard_wire(n1["label"], n2["label"], guard_wire_inputs):
        return None

    neigh1 = get_guard_neighbors(n1["label"], guard_wire_inputs)
    neigh2 = get_guard_neighbors(n2["label"], guard_wire_inputs)

    shared_candidates = sorted(set(neigh1).intersection(set(neigh2)))

    if not shared_candidates:
        return None

    node_by_label = node_by_label_from_masts(mast_nodes)

    best = None

    for shared_label in shared_candidates:

        if shared_label not in node_by_label:
            continue

        shared = node_by_label[shared_label]

        guard_pair_key = make_guard_pair_key(
            edge_key(shared_label, n1["label"]),
            edge_key(shared_label, n2["label"])
        )

        if (
            blocked_shared_guard_pair_keys is not None
            and guard_pair_key in blocked_shared_guard_pair_keys
        ):
            continue

        for k in mast_nodes:

            if k["label"] in [n1["label"], n2["label"], shared["label"]]:
                continue

            if blocked_shared_guard_context_keys is not None:
                context_key = make_shared_guard_context_key(
                    edge_key(shared_label, n1["label"]),
                    edge_key(shared_label, n2["label"]),
                    k["label"]
                )

                if context_key in blocked_shared_guard_context_keys:
                    continue

            free_key = edge_key(n1["label"], n2["label"])
            shared_k_key = edge_key(shared["label"], k["label"])

            if common_tetra_edges is not None:
                free_allowed = is_common_tetra_edge(
                    n1["label"],
                    n2["label"],
                    common_tetra_edges=common_tetra_edges
                )

                shared_k_allowed = is_common_tetra_edge(
                    shared["label"],
                    k["label"],
                    common_tetra_edges=common_tetra_edges
                )

                if not free_allowed and not shared_k_allowed:
                    continue

            seg1 = (node_point(shared), node_point(n1))
            seg2 = (node_point(shared), node_point(n2))
            point_k = node_point(k)

            sol = solve_support_sphere_below_contacts(
                seg1=seg1,
                seg2=seg2,
                point=point_k,
                R=sphere_radius
            )

            if sol is None:
                continue

            O = sol["O"]

            crest_free = lower_support_crest_from_sphere_between_points(
                n1=n1,
                n2=n2,
                O=O,
                R=sphere_radius,
                npts=240
            )

            crest_shared_k = lower_support_crest_from_sphere_between_points(
                n1=shared,
                n2=k,
                O=O,
                R=sphere_radius,
                npts=240
            )

            if crest_shared_k is None:
                continue

            candidate = {
                "crest_free": crest_free,
                "crest_shared_k": crest_shared_k,
                "shared": shared,
                "other": k,
                "free_edge": free_key,
                "shared_k_edge": shared_k_key,
                "sphere": sol,
                "guard_pair_key": guard_pair_key,
                "score": O[2],
            }

            if best is None or candidate["score"] < best["score"]:
                best = candidate

    return best


def apply_shared_guard_plus_k_overrides(
    registry,
    mast_nodes,
    guard_wire_inputs,
    sphere_radius,
    common_tetra_edges,
    log,
    blocked_shared_guard_pair_keys=None,
    blocked_shared_guard_context_keys=None
):
    """
    Aplica el caso:
      dos guardas con mástil común + K.

    Corrección:
      - No se evalúan pares de guardas que ya pertenecen localmente
        a un caso de tres guardas o cuadrilátero cerrado.
      - Se conserva la cresta shared-K.
      - Se omite la cresta libre entre extremos si SHOW_SHARED_FREE_EDGE=False.
    """
    for n1, n2 in combinations(mast_nodes, 2):

        if edge_has_guard_wire(n1["label"], n2["label"], guard_wire_inputs):
            continue

        case = find_shared_guard_special_case_for_edge(
            n1=n1,
            n2=n2,
            mast_nodes=mast_nodes,
            guard_wire_inputs=guard_wire_inputs,
            sphere_radius=sphere_radius,
            common_tetra_edges=common_tetra_edges,
            blocked_shared_guard_pair_keys=blocked_shared_guard_pair_keys,
            blocked_shared_guard_context_keys=blocked_shared_guard_context_keys
        )

        if case is None:
            continue

        free_a, free_b = case["free_edge"]
        shared_a, shared_b = case["shared_k_edge"]

        # -------------------------------------------------
        # 1) Registrar siempre la cresta shared-K si existe
        #    en el registro de aristas reales.
        # -------------------------------------------------
        if is_edge_in_registry(registry, shared_a, shared_b):
            override_registry_edge(
                registry=registry,
                label1=shared_a,
                label2=shared_b,
                curve=case["crest_shared_k"],
                kind="Cresta especial inferior por dos guardas con mástil común",
                source="shared_guard_plus_k",
                info={
                    "case_type": "shared_guard_plus_k",
                    "case": case,
                    "role": "shared_to_k"
                },
                log=log
            )

        # -------------------------------------------------
        # 2) Manejo de la cresta libre entre extremos.
        # -------------------------------------------------
        if is_edge_in_registry(registry, free_a, free_b):

            if SHOW_SHARED_FREE_EDGE and case["crest_free"] is not None:
                override_registry_edge(
                    registry=registry,
                    label1=free_a,
                    label2=free_b,
                    curve=case["crest_free"],
                    kind="Cresta especial inferior por dos guardas con mástil común",
                    source="shared_guard_plus_k",
                    info={
                        "case_type": "shared_guard_plus_k",
                        "case": case,
                        "role": "free_edge"
                    },
                    log=log
                )

            else:
                omit_registry_edge(
                    registry=registry,
                    label1=free_a,
                    label2=free_b,
                    kind="Cresta omitida entre extremos libres de dos guardas con mástil común",
                    source="shared_guard_free_edge_omitted",
                    info={
                        "case_type": "shared_guard_plus_k",
                        "case": case,
                        "role": "free_edge_omitted",
                        "omit": True,
                        "omit_reason": (
                            "Se omite para evitar una cresta libre errónea. "
                            "La superficie MMM debe apoyarse en la cresta shared-K."
                        )
                    },
                    log=log
                )


def find_three_guard_chains(mast_nodes, guard_wire_inputs):
    node_by_label = node_by_label_from_masts(mast_nodes)
    labels = list(node_by_label.keys())

    chains = []

    for A_label in labels:
        for B_label in get_guard_neighbors(A_label, guard_wire_inputs):
            if B_label == A_label:
                continue

            for C_label in get_guard_neighbors(B_label, guard_wire_inputs):
                if C_label in [A_label, B_label]:
                    continue

                for D_label in get_guard_neighbors(C_label, guard_wire_inputs):
                    if D_label in [A_label, B_label, C_label]:
                        continue

                    chain_labels = [A_label, B_label, C_label, D_label]
                    rev_labels = list(reversed(chain_labels))
                    canonical = min(tuple(chain_labels), tuple(rev_labels))

                    chains.append({
                        "canonical": canonical,
                        "labels": chain_labels,
                        "A": node_by_label[A_label],
                        "B": node_by_label[B_label],
                        "C": node_by_label[C_label],
                        "D": node_by_label[D_label],
                    })

    unique = {}

    for ch in chains:
        unique[ch["canonical"]] = ch

    return list(unique.values())


def apply_three_guard_chain_overrides(
    registry,
    mast_nodes,
    guard_wire_inputs,
    sphere_radius,
    common_tetra_edges,
    closed_cycle_sets,
    log
):
    if not ENABLE_THREE_GUARD_CHAIN_CASE:
        return

    chains = find_three_guard_chains(
        mast_nodes=mast_nodes,
        guard_wire_inputs=guard_wire_inputs
    )

    for ch in chains:
        labels_set = frozenset(ch["labels"])

        # Evita que un cuadrilátero cerrado se interprete como cadena abierta.
        if labels_set in closed_cycle_sets:
            log.append({
                "edge": None,
                "source": "three_guard_chain",
                "status": "skip_chain_inside_four_guard_cycle",
                "labels": ch["labels"]
            })
            continue

        A = ch["A"]
        B = ch["B"]
        C = ch["C"]
        D = ch["D"]

        edge_AC = edge_key(A["label"], C["label"])
        edge_BD = edge_key(B["label"], D["label"])

        AC_allowed = edge_AC in registry and is_common_tetra_edge(
            A["label"],
            C["label"],
            common_tetra_edges=common_tetra_edges
        )

        BD_allowed = edge_BD in registry and is_common_tetra_edge(
            B["label"],
            D["label"],
            common_tetra_edges=common_tetra_edges
        )

        if not AC_allowed and not BD_allowed:
            continue

        seg1 = (node_point(A), node_point(B))
        seg2 = (node_point(B), node_point(C))
        seg3 = (node_point(C), node_point(D))

        sol = solve_support_sphere_below_three_segments(
            seg1=seg1,
            seg2=seg2,
            seg3=seg3,
            R=sphere_radius
        )

        if sol is None:
            continue

        O = sol["O"]

        case = {
            "A": A,
            "B": B,
            "C": C,
            "D": D,
            "chain_labels": ch["labels"],
            "edge_AC": edge_AC,
            "edge_BD": edge_BD,
            "sphere": sol,
            "score": O[2],
        }

        if AC_allowed:
            crest_AC = lower_support_crest_from_sphere_between_points(
                n1=A,
                n2=C,
                O=O,
                R=sphere_radius,
                npts=240
            )

            if crest_AC is not None:
                override_registry_edge(
                    registry=registry,
                    label1=A["label"],
                    label2=C["label"],
                    curve=crest_AC,
                    kind="Cresta especial inferior por tres guardas consecutivas",
                    source="three_guard_chain",
                    info={
                        "case_type": "three_guard_chain",
                        "case": case,
                        "role": "diagonal_AC"
                    },
                    log=log
                )

        if BD_allowed:
            crest_BD = lower_support_crest_from_sphere_between_points(
                n1=B,
                n2=D,
                O=O,
                R=sphere_radius,
                npts=240
            )

            if crest_BD is not None:
                override_registry_edge(
                    registry=registry,
                    label1=B["label"],
                    label2=D["label"],
                    curve=crest_BD,
                    kind="Cresta especial inferior por tres guardas consecutivas",
                    source="three_guard_chain",
                    info={
                        "case_type": "three_guard_chain",
                        "case": case,
                        "role": "diagonal_BD"
                    },
                    log=log
                )


def find_four_guard_closed_cycles(mast_nodes, guard_wire_inputs):
    node_by_label = node_by_label_from_masts(mast_nodes)
    labels = list(node_by_label.keys())

    adj = {label: set() for label in labels}

    if guard_wire_inputs is None:
        return []

    for w in guard_wire_inputs:
        a = f"M{w['i']}"
        b = f"M{w['j']}"

        if a in adj and b in adj:
            adj[a].add(b)
            adj[b].add(a)

    cycles = []

    def canonical_cycle(cyc):
        cyc = list(cyc)
        n = len(cyc)

        rotations = []

        for k in range(n):
            rotations.append(tuple(cyc[k:] + cyc[:k]))

        rev = list(reversed(cyc))

        for k in range(n):
            rotations.append(tuple(rev[k:] + rev[:k]))

        return min(rotations)

    for A in labels:
        for B in adj[A]:
            if B == A:
                continue

            for C in adj[B]:
                if C in [A, B]:
                    continue

                for D in adj[C]:
                    if D in [A, B, C]:
                        continue

                    if A not in adj[D]:
                        continue

                    cycle = [A, B, C, D]
                    can = canonical_cycle(cycle)

                    cycles.append({
                        "canonical": can,
                        "labels": cycle,
                        "A": node_by_label[A],
                        "B": node_by_label[B],
                        "C": node_by_label[C],
                        "D": node_by_label[D],
                    })

    unique = {}

    for ch in cycles:
        unique[ch["canonical"]] = ch

    return list(unique.values())


def polygon_xy_from_cycle_labels(cycle_labels, node_by_label):
    pts = []

    for label in cycle_labels:
        n = node_by_label[label]
        pts.append([n["x"], n["y"]])

    return np.asarray(pts, dtype=float)


def point_in_polygon_xy(point_xy, polygon_xy, tol=1e-9):
    x, y = point_xy
    poly = np.asarray(polygon_xy, dtype=float)

    inside = False
    n = len(poly)

    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]

        dx = x2 - x1
        dy = y2 - y1

        seg_len2 = dx * dx + dy * dy

        if seg_len2 > tol:
            t = ((x - x1) * dx + (y - y1) * dy) / seg_len2
            t = np.clip(t, 0.0, 1.0)

            px = x1 + t * dx
            py = y1 + t * dy

            if np.hypot(x - px, y - py) <= 1e-7:
                return True

        cond = ((y1 > y) != (y2 > y))

        if cond:
            x_inter = x1 + (y - y1) * (x2 - x1) / (y2 - y1 + 1e-15)

            if x_inter >= x:
                inside = not inside

    return inside


def build_four_guard_cycle_edges(cycle_labels):
    A, B, C, D = cycle_labels

    return [
        (A, B),
        (B, C),
        (C, D),
        (D, A),
    ]


def segment_from_edge_labels(edge, node_by_label):
    a_label, b_label = edge

    A = node_point(node_by_label[a_label])
    B = node_point(node_by_label[b_label])

    return A, B


def solve_valid_spheres_for_four_guard_cycle(
    cycle_labels,
    node_by_label,
    sphere_radius,
    require_center_inside_polygon=True
):
    polygon_edges = build_four_guard_cycle_edges(cycle_labels)
    polygon_xy = polygon_xy_from_cycle_labels(cycle_labels, node_by_label)

    valid_spheres = []

    for e1, e2, e3 in combinations(polygon_edges, 3):
        seg1 = segment_from_edge_labels(e1, node_by_label)
        seg2 = segment_from_edge_labels(e2, node_by_label)
        seg3 = segment_from_edge_labels(e3, node_by_label)

        sol = solve_support_sphere_below_three_segments(
            seg1=seg1,
            seg2=seg2,
            seg3=seg3,
            R=sphere_radius
        )

        if sol is None:
            continue

        O = sol["O"]

        center_inside = point_in_polygon_xy(
            point_xy=O[:2],
            polygon_xy=polygon_xy
        )

        if require_center_inside_polygon and not center_inside:
            continue

        valid_spheres.append({
            "sphere": sol,
            "support_edges": (e1, e2, e3),
            "center_inside_polygon": center_inside,
        })

    return valid_spheres


def best_crest_for_edge_from_spheres(n1, n2, valid_spheres, sphere_radius):
    best = None

    for idx, item in enumerate(valid_spheres):
        sol = item["sphere"]
        O = sol["O"]

        crest = lower_support_crest_from_sphere_between_points(
            n1=n1,
            n2=n2,
            O=O,
            R=sphere_radius,
            npts=260
        )

        if crest is None:
            continue

        _, _, z = crest
        score = float(np.nanmin(z))

        candidate = {
            "crest": crest,
            "score": score,
            "sphere_index": idx,
            "sphere_item": item,
        }

        if best is None or candidate["score"] > best["score"]:
            best = candidate

    return best


def apply_four_guard_closed_overrides(
    registry,
    mast_nodes,
    guard_wire_inputs,
    sphere_radius,
    common_tetra_edges,
    log
):
    node_by_label = node_by_label_from_masts(mast_nodes)

    cycles = find_four_guard_closed_cycles(
        mast_nodes=mast_nodes,
        guard_wire_inputs=guard_wire_inputs
    )

    closed_cycle_sets = set()

    for cyc in cycles:
        labels = cyc["labels"]
        closed_cycle_sets.add(frozenset(labels))

        A = cyc["A"]
        B = cyc["B"]
        C = cyc["C"]
        D = cyc["D"]

        edge_AC = edge_key(A["label"], C["label"])
        edge_BD = edge_key(B["label"], D["label"])

        AC_allowed = edge_AC in registry and is_common_tetra_edge(
            A["label"],
            C["label"],
            common_tetra_edges=common_tetra_edges
        )

        BD_allowed = edge_BD in registry and is_common_tetra_edge(
            B["label"],
            D["label"],
            common_tetra_edges=common_tetra_edges
        )

        if not AC_allowed and not BD_allowed:
            continue

        valid_spheres = solve_valid_spheres_for_four_guard_cycle(
            cycle_labels=labels,
            node_by_label=node_by_label,
            sphere_radius=sphere_radius,
            require_center_inside_polygon=True
        )

        if not valid_spheres:
            continue

        case_base = {
            "A": A,
            "B": B,
            "C": C,
            "D": D,
            "cycle_labels": labels,
            "edge_AC": edge_AC,
            "edge_BD": edge_BD,
            "valid_spheres": valid_spheres,
        }

        if AC_allowed:
            best_AC = best_crest_for_edge_from_spheres(
                n1=A,
                n2=C,
                valid_spheres=valid_spheres,
                sphere_radius=sphere_radius
            )

            if best_AC is not None:
                sphere_item = best_AC["sphere_item"]

                override_registry_edge(
                    registry=registry,
                    label1=A["label"],
                    label2=C["label"],
                    curve=best_AC["crest"],
                    kind="Cresta especial inferior por cuadrilátero cerrado de guardas",
                    source="four_guard_closed",
                    info={
                        "case_type": "four_guard_closed",
                        "case": {
                            **case_base,
                            "sphere": sphere_item["sphere"],
                            "support_edges": sphere_item["support_edges"],
                        },
                        "role": "diagonal_AC"
                    },
                    log=log
                )

        if BD_allowed:
            best_BD = best_crest_for_edge_from_spheres(
                n1=B,
                n2=D,
                valid_spheres=valid_spheres,
                sphere_radius=sphere_radius
            )

            if best_BD is not None:
                sphere_item = best_BD["sphere_item"]

                override_registry_edge(
                    registry=registry,
                    label1=B["label"],
                    label2=D["label"],
                    curve=best_BD["crest"],
                    kind="Cresta especial inferior por cuadrilátero cerrado de guardas",
                    source="four_guard_closed",
                    info={
                        "case_type": "four_guard_closed",
                        "case": {
                            **case_base,
                            "sphere": sphere_item["sphere"],
                            "support_edges": sphere_item["support_edges"],
                        },
                        "role": "diagonal_BD"
                    },
                    log=log
                )

    return closed_cycle_sets


def build_blocked_shared_guard_pair_keys(
    mast_nodes,
    guard_wire_inputs
):
    """
    Construye los pares de guardas con mástil común que NO deben
    activar el caso shared_guard_plus_k porque ya pertenecen a un
    modelo de mayor orden.

    Bloquea:
      - pares adyacentes dentro de tres guardas consecutivas;
      - pares adyacentes dentro de cuadriláteros cerrados.
    """
    blocked = set()

    # -----------------------------------------------------
    # A-B-C-D:
    #   bloquear A-B + B-C
    #   bloquear B-C + C-D
    # -----------------------------------------------------
    chains = find_three_guard_chains(
        mast_nodes=mast_nodes,
        guard_wire_inputs=guard_wire_inputs
    )

    for ch in chains:
        A, B, C, D = ch["labels"]

        blocked.add(make_guard_pair_key(
            edge_key(A, B),
            edge_key(B, C)
        ))

        blocked.add(make_guard_pair_key(
            edge_key(B, C),
            edge_key(C, D)
        ))

    # -----------------------------------------------------
    # A-B-C-D-A:
    #   bloquear todos los pares adyacentes del contorno.
    # -----------------------------------------------------
    cycles = find_four_guard_closed_cycles(
        mast_nodes=mast_nodes,
        guard_wire_inputs=guard_wire_inputs
    )

    for cyc in cycles:
        A, B, C, D = cyc["labels"]

        contour_edges = [
            edge_key(A, B),
            edge_key(B, C),
            edge_key(C, D),
            edge_key(D, A),
        ]

        for i in range(len(contour_edges)):
            e1 = contour_edges[i]
            e2 = contour_edges[(i + 1) % len(contour_edges)]

            blocked.add(make_guard_pair_key(e1, e2))

    return blocked


def apply_guard_overrides_to_registry(
    base_registry_result,
    sphere_radius,
    guard_wire_inputs=None
):
    final_result = copy.deepcopy(base_registry_result)
    registry = final_result["crest_registry"]
    mast_nodes = final_result["mast_nodes"]
    common_edges = final_result["common_tetra_edges"]

    log = []

    # -----------------------------------------------------
    # 0) Detectar automáticamente módulos locales de
    #    dos guardas independientes desde guard_wire_inputs.
    # -----------------------------------------------------
    independent_guard_modules_auto = detect_independent_guard_modules_auto(
        mast_nodes=mast_nodes,
        guard_wire_inputs=guard_wire_inputs,
        log=log
    )

    final_result["independent_guard_modules_auto"] = independent_guard_modules_auto

    # -----------------------------------------------------
    # 1) Cuadrilátero cerrado de 4 guardas.
    # -----------------------------------------------------
    closed_cycle_sets = apply_four_guard_closed_overrides(
        registry=registry,
        mast_nodes=mast_nodes,
        guard_wire_inputs=guard_wire_inputs,
        sphere_radius=sphere_radius,
        common_tetra_edges=common_edges,
        log=log
    )

    # -----------------------------------------------------
    # 2) Tres guardas consecutivas.
    # -----------------------------------------------------
    apply_three_guard_chain_overrides(
        registry=registry,
        mast_nodes=mast_nodes,
        guard_wire_inputs=guard_wire_inputs,
        sphere_radius=sphere_radius,
        common_tetra_edges=common_edges,
        closed_cycle_sets=closed_cycle_sets,
        log=log
    )

    # -----------------------------------------------------
    # 2B) Bloqueo local para evitar que shared+K se active
    #     sobre pares que ya pertenecen a tres/cuatro guardas.
    # -----------------------------------------------------
    blocked_shared_guard_pair_keys = build_blocked_shared_guard_pair_keys(
        mast_nodes=mast_nodes,
        guard_wire_inputs=guard_wire_inputs
    )

    final_result["blocked_shared_guard_pair_keys"] = blocked_shared_guard_pair_keys

    # -----------------------------------------------------
    # 2C) Bloqueo contextual SOLO para falsos shared+K
    #     causados por módulos independientes contiguos.
    # -----------------------------------------------------
    blocked_shared_guard_context_keys = build_blocked_shared_guard_context_keys_from_auto_modules(
        independent_guard_modules=independent_guard_modules_auto,
        log=log
    )

    final_result["blocked_shared_guard_context_keys"] = blocked_shared_guard_context_keys

    # -----------------------------------------------------
    # 2D) Laterales compartidas entre módulos independientes.
    #     Estas aristas se conservan y NO se recalculan como
    #     diagonales de otro módulo automático.
    # -----------------------------------------------------
    protected_shared_lateral_edges = find_shared_lateral_edges_between_auto_modules(
        independent_guard_modules=independent_guard_modules_auto,
        log=log
    )

    final_result["protected_shared_lateral_edges"] = protected_shared_lateral_edges

    # -----------------------------------------------------
    # 3) Dos guardas con mástil común + mástil K.
    # -----------------------------------------------------
    apply_shared_guard_plus_k_overrides(
        registry=registry,
        mast_nodes=mast_nodes,
        guard_wire_inputs=guard_wire_inputs,
        sphere_radius=sphere_radius,
        common_tetra_edges=common_edges,
        log=log,
        blocked_shared_guard_pair_keys=blocked_shared_guard_pair_keys,
        blocked_shared_guard_context_keys=blocked_shared_guard_context_keys
    )

    # -----------------------------------------------------
    # 4) Dos guardas independientes.
    #    Ahora se evalúa por pares explícitos de cables,
    #    no por vecinos globales.
    # -----------------------------------------------------
    apply_independent_guard_overrides(
        registry=registry,
        mast_nodes=mast_nodes,
        guard_wire_inputs=guard_wire_inputs,
        sphere_radius=sphere_radius,
        log=log,
        independent_guard_modules=independent_guard_modules_auto,
        protected_shared_lateral_edges=protected_shared_lateral_edges
    )

    final_result["override_log"] = log

    return final_result


def add_reference_sphere(fig, O, R, name="Esfera de apoyo", opacity=0.16):
    u = np.linspace(0.0, 2.0 * np.pi, 60)
    v = np.linspace(0.0, np.pi, 35)

    X = O[0] + R * np.outer(np.cos(u), np.sin(v))
    Y = O[1] + R * np.outer(np.sin(u), np.sin(v))
    Z = O[2] + R * np.outer(np.ones_like(u), np.cos(v))

    Z = np.maximum(Z, 0.0)

    fig.add_trace(go.Surface(
        x=X,
        y=Y,
        z=Z,
        opacity=opacity,
        showscale=False,
        hoverinfo="skip",
        name=name
    ))


def add_sphere_xy_projection(fig, O, R, name="Proyección XY esfera", color="cyan"):
    theta = np.linspace(0.0, 2.0 * np.pi, 360)

    fig.add_trace(go.Scatter3d(
        x=O[0] + R * np.cos(theta),
        y=O[1] + R * np.sin(theta),
        z=np.zeros_like(theta),
        mode="lines",
        line=dict(width=5, color=color, dash="dash"),
        name=name
    ))


def add_special_auxiliary_graphics(fig, final_result, sphere_radius):
    registry = final_result["crest_registry"]
    plotted_spheres = set()

    for key, item in registry.items():
        info = item.get("info", {})

        if not isinstance(info, dict):
            continue

        case_type = info.get("case_type", "")

        # -------------------------------------------------
        # Líneas imaginarias para dos guardas independientes.
        # -------------------------------------------------
        if (
            case_type == "independent_guard_lines"
            and SHOW_IMAGINARY_LINES
            and "C1" in info
            and "C2" in info
        ):
            C1 = info["C1"]
            C2 = info["C2"]
            a = info["a"]
            b = info["b"]
            n1, n2 = item["nodes"]

            step = max(1, len(C1) // 18)

            for idx in range(0, len(C1), step):
                p1 = C1[idx]
                p2 = C2[idx]

                fig.add_trace(go.Scatter3d(
                    x=[p1[0], p2[0]],
                    y=[p1[1], p2[1]],
                    z=[p1[2], p2[2]],
                    mode="lines",
                    line=dict(width=2, color="gray", dash="dash"),
                    opacity=0.55,
                    showlegend=False,
                    hoverinfo="skip"
                ))

            fig.add_trace(go.Scatter3d(
                x=C1[:, 0],
                y=C1[:, 1],
                z=C1[:, 2],
                mode="lines",
                line=dict(width=4, color="gray", dash="dot"),
                name=f"Cresta guía {n1['label']}-{b['label']}"
            ))

            fig.add_trace(go.Scatter3d(
                x=C2[:, 0],
                y=C2[:, 1],
                z=C2[:, 2],
                mode="lines",
                line=dict(width=4, color="gray", dash="dot"),
                name=f"Cresta guía {a['label']}-{n2['label']}"
            ))

        # -------------------------------------------------
        # Esferas/contactos/radios.
        # -------------------------------------------------
        if "case" not in info:
            continue

        case = info["case"]

        if "sphere" not in case:
            continue

        sol = case["sphere"]
        O = sol["O"]

        if case_type == "four_guard_closed":
            sphere_id = (
                "four_guard_closed",
                tuple(case["cycle_labels"]),
                round(O[0], 4),
                round(O[1], 4),
                round(O[2], 4)
            )
            color = "dodgerblue"
            sphere_name = f"Esfera cuadrilátero {'-'.join(case['cycle_labels'])}"
            show_sphere = SHOW_FOUR_GUARD_SPHERE
            show_projection = SHOW_FOUR_GUARD_XY_PROJECTION
            show_contacts = SHOW_FOUR_GUARD_CONTACTS
            show_radii = SHOW_FOUR_GUARD_RADII

        elif case_type == "three_guard_chain":
            sphere_id = (
                "three_guard_chain",
                tuple(case["chain_labels"]),
                round(O[0], 4),
                round(O[1], 4),
                round(O[2], 4)
            )
            color = "deepskyblue"
            sphere_name = f"Esfera 3 guardas {'-'.join(case['chain_labels'])}"
            show_sphere = SHOW_THREE_GUARD_SPHERE
            show_projection = SHOW_THREE_GUARD_XY_PROJECTION
            show_contacts = SHOW_THREE_GUARD_CONTACTS
            show_radii = SHOW_THREE_GUARD_RADII

        elif case_type == "shared_guard_plus_k":
            sphere_id = (
                "shared_guard_plus_k",
                case["shared"]["label"],
                case["other"]["label"],
                round(O[0], 4),
                round(O[1], 4),
                round(O[2], 4)
            )
            color = "cyan"
            sphere_name = f"Esfera apoyo {case['shared']['label']}-{case['other']['label']}"
            show_sphere = SHOW_SUPPORT_SPHERE
            show_projection = SHOW_SPHERE_XY_PROJECTION
            show_contacts = SHOW_CONTACT_POINTS
            show_radii = SHOW_RADII_TO_CONTACTS

        else:
            continue

        if sphere_id in plotted_spheres:
            continue

        plotted_spheres.add(sphere_id)

        if show_sphere:
            add_reference_sphere(
                fig=fig,
                O=O,
                R=sphere_radius,
                name=sphere_name,
                opacity=0.15
            )

        if show_projection:
            add_sphere_xy_projection(
                fig=fig,
                O=O,
                R=sphere_radius,
                name=f"Proyección XY {sphere_name}",
                color=color
            )

        Q1 = sol["Q1"]
        Q2 = sol["Q2"]
        Q3 = sol["Q3"]

        if show_contacts:
            fig.add_trace(go.Scatter3d(
                x=[Q1[0], Q2[0], Q3[0], O[0]],
                y=[Q1[1], Q2[1], Q3[1], O[1]],
                z=[Q1[2], Q2[2], Q3[2], O[2]],
                mode="markers+text",
                marker=dict(
                    size=6,
                    color=[color, color, color, "black"]
                ),
                text=[
                    "Contacto 1",
                    "Contacto 2",
                    "Contacto 3",
                    "Centro esfera"
                ],
                textposition="top center",
                name=f"Contactos {sphere_name}"
            ))

        if show_radii:
            for Q in [Q1, Q2, Q3]:
                fig.add_trace(go.Scatter3d(
                    x=[O[0], Q[0]],
                    y=[O[1], Q[1]],
                    z=[O[2], Q[2]],
                    mode="lines",
                    line=dict(width=3, color="black", dash="dot"),
                    showlegend=False
                ))


def plot_final_crest_registry(
    tri_nodes,
    triangles,
    final_result,
    sphere_radius,
    title="13B - Registro final de crestas con overrides por guardas"
):
    fig = go.Figure()

    add_mmm_borders_to_fig(fig, triangles)

    registry = final_result["crest_registry"]

    for key, item in registry.items():

        if item.get("omit", False):
            continue

        C = item.get("curve", None)

        if C is None:
            continue

        color, width = registry_color_and_width(item)

        fig.add_trace(go.Scatter3d(
            x=C[:, 0],
            y=C[:, 1],
            z=C[:, 2],
            mode="lines",
            line=dict(width=width, color=color),
            name=f"{item['kind']} {key[0]}-{key[1]}"
        ))

    add_special_auxiliary_graphics(fig, final_result, sphere_radius)

    add_mq_segments_to_fig(fig, final_result["mq_edges"])
    add_masts_and_q_points_to_fig(fig, tri_nodes)
    add_ground_plane_to_fig(fig, tri_nodes, sphere_radius)

    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="data"
        ),
        height=950,
        showlegend=True
    )

    fig.show()

    return fig


import copy


import numpy as np


from itertools import combinations


FILTER1_ZMIN_TOL = 1e-9


FILTER1_MAX_POINTS_PER_CURVE = None   # por ejemplo 160 si quieres acelerar


FILTER1_SOURCE_NAME = "filter1_independent_vs_independent"


FILTER1_SHOW_SUMMARY = True


def f1_cross2d(u, v):
    return u[0] * v[1] - u[1] * v[0]


def f1_bbox_segments_overlap_xy(a, b, c, d, tol=1e-9):
    a = np.asarray(a, dtype=float)[:2]
    b = np.asarray(b, dtype=float)[:2]
    c = np.asarray(c, dtype=float)[:2]
    d = np.asarray(d, dtype=float)[:2]

    aminx = min(a[0], b[0]) - tol
    amaxx = max(a[0], b[0]) + tol
    aminy = min(a[1], b[1]) - tol
    amaxy = max(a[1], b[1]) + tol

    cminx = min(c[0], d[0]) - tol
    cmaxx = max(c[0], d[0]) + tol
    cminy = min(c[1], d[1]) - tol
    cmaxy = max(c[1], d[1]) + tol

    if amaxx < cminx or cmaxx < aminx:
        return False

    if amaxy < cminy or cmaxy < aminy:
        return False

    return True


def f1_point_close_xy(p, q, tol=1e-7):
    p = np.asarray(p, dtype=float)[:2]
    q = np.asarray(q, dtype=float)[:2]
    return np.linalg.norm(p - q) <= tol


def f1_point_is_global_endpoint_xy(P, C, tol=1e-7):
    C = np.asarray(C, dtype=float)

    if len(C) == 0:
        return False

    P = np.asarray(P, dtype=float)[:2]

    return (
        f1_point_close_xy(P, C[0, :2], tol=tol)
        or f1_point_close_xy(P, C[-1, :2], tol=tol)
    )


def f1_segment_intersection_xy_inclusive(a, b, c, d, tol=1e-9):
    """
    Intersección inclusiva entre dos segmentos 2D.
    Sirve mejor que un cruce estrictamente propio.
    """
    a = np.asarray(a, dtype=float)[:2]
    b = np.asarray(b, dtype=float)[:2]
    c = np.asarray(c, dtype=float)[:2]
    d = np.asarray(d, dtype=float)[:2]

    if not f1_bbox_segments_overlap_xy(a, b, c, d, tol=tol):
        return False, None, None, None

    r = b - a
    s = d - c
    qmp = c - a

    rxs = f1_cross2d(r, s)
    qmpxr = f1_cross2d(qmp, r)

    # Caso no paralelo
    if abs(rxs) > tol:
        t = f1_cross2d(qmp, s) / rxs
        u = f1_cross2d(qmp, r) / rxs

        if (-tol <= t <= 1.0 + tol) and (-tol <= u <= 1.0 + tol):
            t_clip = np.clip(t, 0.0, 1.0)
            u_clip = np.clip(u, 0.0, 1.0)
            P = a + t_clip * r
            return True, P, t_clip, u_clip

        return False, None, None, None

    # Paralelo no colineal
    if abs(qmpxr) > tol:
        return False, None, None, None

    # Colineal
    rr = np.dot(r, r)

    if rr < tol:
        return False, None, None, None

    t0 = np.dot(c - a, r) / rr
    t1 = np.dot(d - a, r) / rr

    tmin = max(0.0, min(t0, t1))
    tmax = min(1.0, max(t0, t1))

    if tmax < tmin - tol:
        return False, None, None, None

    tmid = 0.5 * (tmin + tmax)
    P = a + tmid * r

    return True, P, tmid, None


def f1_downsample_curve(C, max_points=None):
    C = np.asarray(C, dtype=float)

    if max_points is None:
        return C

    if len(C) <= max_points:
        return C

    idx = np.linspace(0, len(C) - 1, max_points).astype(int)
    return C[idx]


def f1_curve_pair_crosses_xy(C1, C2, tol=1e-9, max_points=None):
    """
    Retorna:
      crosses, intersections

    Ignora el caso donde solo hay contacto en extremos globales.
    """
    if "curve_to_array" in globals():
        C1 = curve_to_array(C1)
        C2 = curve_to_array(C2)
    else:
        C1 = np.asarray(C1, dtype=float)
        C2 = np.asarray(C2, dtype=float)

    if C1 is None or C2 is None:
        return False, []

    if len(C1) < 2 or len(C2) < 2:
        return False, []

    C1 = f1_downsample_curve(C1, max_points=max_points)
    C2 = f1_downsample_curve(C2, max_points=max_points)

    xy1 = C1[:, :2]
    xy2 = C2[:, :2]

    min1 = xy1.min(axis=0)
    max1 = xy1.max(axis=0)
    min2 = xy2.min(axis=0)
    max2 = xy2.max(axis=0)

    if max1[0] < min2[0] - tol or max2[0] < min1[0] - tol:
        return False, []

    if max1[1] < min2[1] - tol or max2[1] < min1[1] - tol:
        return False, []

    intersections = []

    for i in range(len(xy1) - 1):
        a = xy1[i]
        b = xy1[i + 1]

        for j in range(len(xy2) - 1):
            c = xy2[j]
            d = xy2[j + 1]

            ok, P, t, u = f1_segment_intersection_xy_inclusive(
                a=a, b=b, c=c, d=d, tol=tol
            )

            if not ok or P is None:
                continue

            endpoint_1 = f1_point_is_global_endpoint_xy(P, C1, tol=1e-6)
            endpoint_2 = f1_point_is_global_endpoint_xy(P, C2, tol=1e-6)

            # Si solo se tocan en extremos globales, no cuenta.
            if endpoint_1 and endpoint_2:
                continue

            intersections.append({
                "point_xy": np.asarray(P, dtype=float),
                "segment_i": i,
                "segment_j": j,
                "t": t,
                "u": u,
            })

    return len(intersections) > 0, intersections


def f1_normalize_edge(edge):
    a, b = edge
    if "edge_key" in globals():
        return edge_key(a, b)
    return tuple(sorted((a, b)))


def f1_normalize_guard_pair(guard_pair):
    """
    guard_pair -> tuple ordenada de dos edges canónicos.
    """
    if guard_pair is None:
        return None

    out = []

    for e in guard_pair:
        if e is None:
            continue
        out.append(f1_normalize_edge(e))

    out = sorted(set(out))
    return tuple(out)


def f1_force_omit_registry_edge(
    registry,
    label1,
    label2,
    kind,
    source,
    info=None,
    log=None
):
    """
    Omite una cresta del registro con prioridad alta.
    Nunca elimina cables de guarda directos.
    """
    key = f1_normalize_edge((label1, label2))

    if key not in registry:
        if log is not None:
            log.append({
                "edge": key,
                "source": source,
                "status": "skip_edge_not_in_registry"
            })
        return False

    item = registry[key]

    if item.get("source", "") == "direct_guard_wire":
        if log is not None:
            log.append({
                "edge": key,
                "source": source,
                "status": "skip_direct_guard_wire"
            })
        return False

    old_source = item.get("source", "")
    old_kind = item.get("kind", "")

    registry[key] = {
        **item,
        "curve": None,
        "kind": kind,
        "source": source,
        "priority": max(item.get("priority", 0), 150),
        "replaceable": False,
        "omit": True,
        "info": info if info is not None else {
            "case_type": source,
            "omit": True
        },
        "overwritten_from": old_source,
        "old_kind": old_kind
    }

    if log is not None:
        log.append({
            "edge": key,
            "source": source,
            "status": "omitted",
            "old_source": old_source
        })

    return True


def collect_independent_guard_examples_from_registry(registry):
    """
    Agrupa las crestas source == 'independent_guard_lines' por ejemplar.

    Un ejemplar se identifica por:
      - guard_pair
      - family

    Cada ejemplar puede tener 1 o 2 crestas.
    """
    examples = {}

    for key, item in registry.items():

        if item.get("omit", False):
            continue

        if item.get("curve", None) is None:
            continue

        if item.get("source", "") != "independent_guard_lines":
            continue

        info = item.get("info", {})
        if not isinstance(info, dict):
            info = {}

        guard_pair = info.get("guard_pair", None)

        if guard_pair is None:
            g1 = info.get("guard_edge_1", None)
            g2 = info.get("guard_edge_2", None)
            if g1 is not None and g2 is not None:
                guard_pair = (g1, g2)

        guard_pair = f1_normalize_guard_pair(guard_pair)
        family = info.get("family", "unknown")

        example_key = (guard_pair, family)

        if example_key not in examples:
            examples[example_key] = {
                "example_key": example_key,
                "guard_pair": guard_pair,
                "family": family,
                "edges": [],
                "curves": [],
                "items": [],
                "zmins_per_edge": [],
                "zmin": None,
                "edge_labels": []
            }

        C = curve_to_array(item["curve"]) if "curve_to_array" in globals() else np.asarray(item["curve"], dtype=float)
        zmin_edge = float(np.nanmin(C[:, 2]))

        examples[example_key]["edges"].append(key)
        examples[example_key]["curves"].append(C)
        examples[example_key]["items"].append(item)
        examples[example_key]["zmins_per_edge"].append(zmin_edge)
        examples[example_key]["edge_labels"].append(f"{key[0]}-{key[1]}")

    out = []

    for ex in examples.values():
        if len(ex["zmins_per_edge"]) > 0:
            ex["zmin"] = float(np.nanmin(ex["zmins_per_edge"]))
        else:
            ex["zmin"] = np.nan

        out.append(ex)

    out.sort(key=lambda d: (np.nan_to_num(d["zmin"], nan=-1e9), str(d["example_key"])), reverse=True)

    return out


def independent_examples_cross_xy(ex1, ex2):
    """
    Dos ejemplares se consideran en conflicto si cualquiera de sus crestas
    se cruza en planta XY con cualquiera de las crestas del otro ejemplar.
    """
    crossing_events = []

    for edge1, C1 in zip(ex1["edges"], ex1["curves"]):
        for edge2, C2 in zip(ex2["edges"], ex2["curves"]):
            crosses, intersections = f1_curve_pair_crosses_xy(
                C1=C1,
                C2=C2,
                tol=1e-9,
                max_points=FILTER1_MAX_POINTS_PER_CURVE
            )

            if not crosses:
                continue

            crossing_events.append({
                "edge_1": edge1,
                "edge_2": edge2,
                "intersections": intersections
            })

    return len(crossing_events) > 0, crossing_events


def apply_filter1_independent_examples_competition(base_registry_result):
    """
    Aplica:
      - competencia entre ejemplares de dos guardas independientes.
      - si se cruzan en XY, se elimina el de menor zmin.
    """
    out = copy.deepcopy(base_registry_result)
    registry = out["crest_registry"]

    examples = collect_independent_guard_examples_from_registry(registry)

    pairwise_log = []
    tie_log = []
    removal_targets = set()

    # -----------------------------------------------------
    # Comparación entre ejemplares
    # -----------------------------------------------------
    for ex1, ex2 in combinations(examples, 2):

        crosses, crossing_events = independent_examples_cross_xy(ex1, ex2)

        if not crosses:
            continue

        z1 = ex1["zmin"]
        z2 = ex2["zmin"]

        if not np.isfinite(z1) or not np.isfinite(z2):
            pairwise_log.append({
                "status": "skip_non_finite_zmin",
                "example_1": ex1["example_key"],
                "example_2": ex2["example_key"],
                "zmin_1": z1,
                "zmin_2": z2
            })
            continue

        # El menor zmin pierde.
        if z1 < z2 - FILTER1_ZMIN_TOL:
            loser = ex1
            winner = ex2
            status = "example_1_loses"

        elif z2 < z1 - FILTER1_ZMIN_TOL:
            loser = ex2
            winner = ex1
            status = "example_2_loses"

        else:
            # Empate: por ahora no se elimina ninguno.
            tie_log.append({
                "status": "tie_no_removal",
                "example_1": ex1["example_key"],
                "example_2": ex2["example_key"],
                "zmin_1": z1,
                "zmin_2": z2,
                "crossing_events": crossing_events
            })
            continue

        removal_targets.add(loser["example_key"])

        pairwise_log.append({
            "status": status,
            "winner": winner["example_key"],
            "loser": loser["example_key"],
            "winner_zmin": winner["zmin"],
            "loser_zmin": loser["zmin"],
            "crossing_events": crossing_events
        })

    # -----------------------------------------------------
    # Omitir las crestas de los ejemplares perdedores
    # -----------------------------------------------------
    omit_log = []
    removed_examples = []
    kept_examples = []

    for ex in examples:
        if ex["example_key"] in removal_targets:
            removed_examples.append(ex)

            for edge in ex["edges"]:
                f1_force_omit_registry_edge(
                    registry=registry,
                    label1=edge[0],
                    label2=edge[1],
                    kind="Cresta omitida por competencia entre dos guardas independientes",
                    source=FILTER1_SOURCE_NAME,
                    info={
                        "case_type": FILTER1_SOURCE_NAME,
                        "omit": True,
                        "example_key": ex["example_key"],
                        "guard_pair": ex["guard_pair"],
                        "family": ex["family"],
                        "zmin": ex["zmin"],
                        "edge_labels": ex["edge_labels"],
                        "omit_reason": (
                            "Este ejemplar del caso de dos guardas independientes "
                            "se cruza en XY con otro ejemplar del mismo caso y "
                            "tiene menor zmin."
                        )
                    },
                    log=omit_log
                )
        else:
            kept_examples.append(ex)

    out["filter1_independent_examples_all"] = examples
    out["filter1_independent_examples_kept"] = kept_examples
    out["filter1_independent_examples_removed"] = removed_examples
    out["filter1_independent_pairwise_log"] = pairwise_log
    out["filter1_independent_tie_log"] = tie_log
    out["filter1_independent_omit_log"] = omit_log

    return out


import copy


import numpy as np


FILTER2_GROUND_ZMIN_TOL = 0.05


FILTER2_HIGH_ZMIN_MIN = 0.20


FILTER2_OVERLAP_DISTANCE_XY_TOL = 0.35


FILTER2_PARALLEL_ANGLE_DEG_TOL = 10.0


FILTER2_PARALLEL_SIN_TOL = np.sin(np.deg2rad(FILTER2_PARALLEL_ANGLE_DEG_TOL))


FILTER2_MIN_OVERLAP_LENGTH = 0.50


FILTER2_MIN_OVERLAP_FRACTION = 0.03


FILTER2_MAX_POINTS_PER_CURVE = None


FILTER2_SOURCE_NAME = "filter2_ground_overlap_with_guard_or_high_crest"


FILTER2_SHOW_SUMMARY = True


FILTER2_SHOW_ZMIN_DIAGNOSTIC = True


def f2_edge_key(a, b):
    if "edge_key" in globals():
        return edge_key(a, b)
    return tuple(sorted([a, b]))


def f2_curve_to_array(curve):
    if curve is None:
        return None

    if "curve_to_array" in globals():
        C = curve_to_array(curve)
    else:
        if isinstance(curve, tuple) and len(curve) == 3:
            x, y, z = curve
            C = np.column_stack([x, y, z]).astype(float)
        else:
            C = np.asarray(curve, dtype=float)

    if C is None:
        return None

    C = np.asarray(C, dtype=float)

    if C.ndim != 2 or C.shape[1] != 3:
        return None

    C[:, 2] = np.maximum(C[:, 2], 0.0)

    return C


def f2_curve_zmin(C):
    C = f2_curve_to_array(C)

    if C is None or len(C) == 0:
        return np.nan

    return float(np.nanmin(C[:, 2]))


def f2_curve_xy_length(C):
    C = f2_curve_to_array(C)

    if C is None or len(C) < 2:
        return 0.0

    d = np.linalg.norm(np.diff(C[:, :2], axis=0), axis=1)

    return float(np.sum(d))


def f2_downsample_curve(C, max_points=None):
    C = np.asarray(C, dtype=float)

    if max_points is None:
        return C

    if len(C) <= max_points:
        return C

    idx = np.linspace(0, len(C) - 1, max_points).astype(int)

    return C[idx]


def f2_point_to_segment_distance_xy(P, A, B):
    P = np.asarray(P, dtype=float)[:2]
    A = np.asarray(A, dtype=float)[:2]
    B = np.asarray(B, dtype=float)[:2]

    AB = B - A
    den = np.dot(AB, AB)

    if den < 1e-12:
        return float(np.linalg.norm(P - A)), A, 0.0

    t = np.dot(P - A, AB) / den
    t = np.clip(t, 0.0, 1.0)

    Q = A + t * AB
    d = float(np.linalg.norm(P - Q))

    return d, Q, t


def f2_cross2d(u, v):
    return u[0] * v[1] - u[1] * v[0]


def f2_segment_aligned_overlap_xy(
    a,
    b,
    c,
    d,
    distance_tol=FILTER2_OVERLAP_DISTANCE_XY_TOL,
    parallel_sin_tol=FILTER2_PARALLEL_SIN_TOL
):
    """
    Evalúa si dos segmentos XY están aproximadamente alineados
    y superpuestos.

    Retorna:
        overlap_flag, overlap_length, info

    Condiciones:
      - casi paralelos;
      - sus intervalos proyectados se solapan;
      - la distancia lateral en la zona de solape es pequeña.
    """
    a = np.asarray(a, dtype=float)[:2]
    b = np.asarray(b, dtype=float)[:2]
    c = np.asarray(c, dtype=float)[:2]
    d = np.asarray(d, dtype=float)[:2]

    r = b - a
    s = d - c

    Lr = np.linalg.norm(r)
    Ls = np.linalg.norm(s)

    if Lr < 1e-9 or Ls < 1e-9:
        return False, 0.0, None

    ur = r / Lr
    us = s / Ls

    # Paralelismo aproximado. abs permite sentido opuesto.
    sin_angle = abs(f2_cross2d(ur, us))

    if sin_angle > parallel_sin_tol:
        return False, 0.0, None

    # Proyectar segmento obstáculo sobre el eje del segmento candidato.
    tc = np.dot(c - a, ur)
    td = np.dot(d - a, ur)

    obs_min = min(tc, td)
    obs_max = max(tc, td)

    cand_min = 0.0
    cand_max = Lr

    ov_min = max(cand_min, obs_min)
    ov_max = min(cand_max, obs_max)

    overlap_len = ov_max - ov_min

    if overlap_len <= 1e-9:
        return False, 0.0, None

    # Punto medio de la zona superpuesta sobre el candidato.
    t_mid = 0.5 * (ov_min + ov_max)
    P_mid = a + t_mid * ur

    # Distancia lateral desde ese punto al segmento obstáculo.
    d_mid, Q_mid, _ = f2_point_to_segment_distance_xy(P_mid, c, d)

    if d_mid > distance_tol:
        return False, 0.0, None

    info = {
        "overlap_length": float(overlap_len),
        "distance_xy": float(d_mid),
        "sin_angle": float(sin_angle),
        "candidate_mid_xy": P_mid,
        "obstacle_closest_xy": Q_mid,
    }

    return True, float(overlap_len), info


def f2_curve_aligned_overlap_xy(
    C_ground,
    C_obstacle,
    distance_tol=FILTER2_OVERLAP_DISTANCE_XY_TOL,
    parallel_sin_tol=FILTER2_PARALLEL_SIN_TOL,
    min_overlap_length=FILTER2_MIN_OVERLAP_LENGTH,
    min_overlap_fraction=FILTER2_MIN_OVERLAP_FRACTION,
    max_points=None
):
    """
    Detecta si una cresta cercana al suelo está superpuesta/alineada
    con un obstáculo en planta XY.

    NO detecta cruces angulares simples.
    """
    Cg = f2_curve_to_array(C_ground)
    Co = f2_curve_to_array(C_obstacle)

    if Cg is None or Co is None:
        return False, []

    if len(Cg) < 2 or len(Co) < 2:
        return False, []

    Cg = f2_downsample_curve(Cg, max_points=max_points)
    Co = f2_downsample_curve(Co, max_points=max_points)

    xy_g = Cg[:, :2]
    xy_o = Co[:, :2]

    total_len_g = f2_curve_xy_length(Cg)
    required_overlap = max(
        min_overlap_length,
        min_overlap_fraction * max(total_len_g, 1e-9)
    )

    total_overlap = 0.0
    events = []

    # Prefiltro por bounding box global con tolerancia lateral.
    min_g = xy_g.min(axis=0) - distance_tol
    max_g = xy_g.max(axis=0) + distance_tol
    min_o = xy_o.min(axis=0) - distance_tol
    max_o = xy_o.max(axis=0) + distance_tol

    if max_g[0] < min_o[0] or max_o[0] < min_g[0]:
        return False, []

    if max_g[1] < min_o[1] or max_o[1] < min_g[1]:
        return False, []

    for i in range(len(xy_g) - 1):
        a = xy_g[i]
        b = xy_g[i + 1]

        seg_len_g = np.linalg.norm(b - a)

        if seg_len_g < 1e-9:
            continue

        for j in range(len(xy_o) - 1):
            c = xy_o[j]
            d = xy_o[j + 1]

            ok, overlap_len, info = f2_segment_aligned_overlap_xy(
                a=a,
                b=b,
                c=c,
                d=d,
                distance_tol=distance_tol,
                parallel_sin_tol=parallel_sin_tol
            )

            if not ok:
                continue

            # Evita que un solape puntual o de extremo dispare el filtro.
            if overlap_len <= 1e-9:
                continue

            total_overlap += min(overlap_len, seg_len_g)

            events.append({
                "candidate_segment": i,
                "obstacle_segment": j,
                "overlap_length": float(overlap_len),
                "distance_xy": info["distance_xy"],
                "sin_angle": info["sin_angle"],
                "candidate_mid_xy": info["candidate_mid_xy"],
                "obstacle_closest_xy": info["obstacle_closest_xy"],
            })

            if total_overlap >= required_overlap:
                return True, {
                    "total_overlap": float(total_overlap),
                    "required_overlap": float(required_overlap),
                    "events": events,
                }

    return False, {
        "total_overlap": float(total_overlap),
        "required_overlap": float(required_overlap),
        "events": events,
    }


def f2_triangle_type(tri):
    if "classify_triangle_type" in globals():
        return classify_triangle_type(tri)

    types = [n["type"] for n in tri["nodes"]]
    nM = sum(t == "mast_top" for t in types)
    nQ = sum(t == "Q" for t in types)

    if nM == 3:
        return "M-M-M"
    if nM == 2 and nQ == 1:
        return "M-M-Q"
    if nM == 1 and nQ == 2:
        return "M-Q-Q"
    if nQ == 3:
        return "Q-Q-Q"

    return "Otro"


def f2_triangle_label_string(tri):
    return "-".join([n["label"] for n in tri["nodes"]])


def f2_triangle_mast_edge_keys(tri):
    nodes = tri["nodes"]
    edges = []

    for a, b in [(0, 1), (1, 2), (2, 0)]:
        n1 = nodes[a]
        n2 = nodes[b]

        if n1["type"] != "mast_top" or n2["type"] != "mast_top":
            continue

        edges.append(f2_edge_key(n1["label"], n2["label"]))

    return edges


def f2_collect_mmm_triangles_by_edge(triangles):
    edge_to_mmm = {}

    for idx, tri in enumerate(triangles):
        if f2_triangle_type(tri) != "M-M-M":
            continue

        for edge in f2_triangle_mast_edge_keys(tri):
            edge_to_mmm.setdefault(edge, []).append(idx)

    return edge_to_mmm


def f2_filter_tri_nodes_used_by_triangles(tri_nodes, triangles):
    used = set()

    for tri in triangles:
        for n in tri["nodes"]:
            used.add((n["type"], n["label"]))

    return [
        n for n in tri_nodes
        if (n["type"], n["label"]) in used
    ]


def f2_node_by_label_from_masts(mast_nodes):
    if "node_by_label_from_masts" in globals():
        return node_by_label_from_masts(mast_nodes)

    return {n["label"]: n for n in mast_nodes}


def f2_is_direct_guard_item(item):
    return item.get("source", "") == "direct_guard_wire"


def f2_is_ground_crest_by_metadata(item):
    source = str(item.get("source", "")).lower()
    kind = str(item.get("kind", "")).lower()

    text = f"{source} {kind}"

    ground_tokens = [
        "base_long_l_gt_2s",
        "base_long",
        "long_l_gt_2s",
        "larga",
        "suelo",
        "ground",
        "l>2s",
        "l > 2s",
        "zmin=0",
        "z_min=0",
        "z=0",
        "z = 0",
        "al suelo",
        "hasta suelo"
    ]

    return any(tok in text for tok in ground_tokens)


def f2_collect_ground_candidates_and_high_crests(registry):
    """
    Candidatas:
      - crestas no-cable cercanas al suelo.

    Obstáculos altos:
      - crestas no-cable con zmin >= FILTER2_HIGH_ZMIN_MIN.

    Importante:
      - Las crestas altas NO se eliminan.
      - Los cables NO entran aquí, se agregan aparte como obstáculos.
    """
    ground_candidates = []
    high_crests = []

    for edge, item in registry.items():

        if item.get("omit", False):
            continue

        if item.get("curve", None) is None:
            continue

        if f2_is_direct_guard_item(item):
            continue

        C = f2_curve_to_array(item.get("curve", None))

        if C is None:
            continue

        zmin = f2_curve_zmin(C)
        ground_meta = f2_is_ground_crest_by_metadata(item)

        rec = {
            "edge": edge,
            "item": item,
            "curve": C,
            "source": item.get("source", ""),
            "kind": item.get("kind", ""),
            "zmin": zmin,
            "ground_meta": ground_meta,
        }

        if ground_meta or (np.isfinite(zmin) and zmin <= FILTER2_GROUND_ZMIN_TOL):
            ground_candidates.append(rec)

        elif np.isfinite(zmin) and zmin >= FILTER2_HIGH_ZMIN_MIN:
            high_crests.append(rec)

    return ground_candidates, high_crests


def f2_build_guard_obstacles(guard_wire_inputs, mast_nodes, registry):
    node_by_label = f2_node_by_label_from_masts(mast_nodes)
    guard_by_edge = {}

    # 1) Cables desde entrada.
    if guard_wire_inputs is not None:
        for w in guard_wire_inputs:
            a_label = f"M{w['i']}"
            b_label = f"M{w['j']}"

            if a_label not in node_by_label or b_label not in node_by_label:
                continue

            A = node_by_label[a_label]
            B = node_by_label[b_label]

            edge = f2_edge_key(a_label, b_label)

            C = np.array([
                [A["x"], A["y"], A["z"]],
                [B["x"], B["y"], B["z"]],
            ], dtype=float)

            C[:, 2] = np.maximum(C[:, 2], 0.0)

            guard_by_edge[edge] = {
                "edge": edge,
                "curve": C,
                "source": "direct_guard_wire_input",
                "kind": "Cable de guarda directo",
                "zmin": f2_curve_zmin(C),
                "obstacle_type": "guard_wire"
            }

    # 2) Cables desde registro.
    for edge, item in registry.items():
        if item.get("source", "") != "direct_guard_wire":
            continue

        if item.get("curve", None) is None:
            continue

        C = f2_curve_to_array(item.get("curve", None))

        if C is None:
            continue

        guard_by_edge[edge] = {
            "edge": edge,
            "curve": C,
            "source": "direct_guard_wire",
            "kind": item.get("kind", "Cable de guarda directo"),
            "zmin": f2_curve_zmin(C),
            "obstacle_type": "guard_wire"
        }

    return list(guard_by_edge.values())


def f2_build_obstacles(registry, guard_wire_inputs, mast_nodes):
    ground_candidates, high_crests = f2_collect_ground_candidates_and_high_crests(
        registry=registry
    )

    guard_obstacles = f2_build_guard_obstacles(
        guard_wire_inputs=guard_wire_inputs,
        mast_nodes=mast_nodes,
        registry=registry
    )

    high_crest_obstacles = []

    for rec in high_crests:
        high_crest_obstacles.append({
            "edge": rec["edge"],
            "curve": rec["curve"],
            "source": rec["source"],
            "kind": rec["kind"],
            "zmin": rec["zmin"],
            "obstacle_type": "high_crest"
        })

    obstacles = guard_obstacles + high_crest_obstacles

    return ground_candidates, high_crests, guard_obstacles, obstacles


def f2_force_omit_registry_edge(
    registry,
    edge,
    kind,
    source,
    info=None,
    log=None
):
    key = f2_edge_key(edge[0], edge[1])

    if key not in registry:
        if log is not None:
            log.append({
                "edge": key,
                "source": source,
                "status": "skip_edge_not_in_registry"
            })
        return False

    item = registry[key]

    # Nunca eliminar cables de guarda.
    if f2_is_direct_guard_item(item):
        if log is not None:
            log.append({
                "edge": key,
                "source": source,
                "status": "skip_direct_guard_wire"
            })
        return False

    # Nunca eliminar crestas altas por este filtro.
    C = f2_curve_to_array(item.get("curve", None))
    zmin = f2_curve_zmin(C)

    is_ground = (
        f2_is_ground_crest_by_metadata(item)
        or (
            np.isfinite(zmin)
            and zmin <= FILTER2_GROUND_ZMIN_TOL
        )
    )

    if not is_ground:
        if log is not None:
            log.append({
                "edge": key,
                "source": source,
                "status": "skip_not_ground_crest",
                "zmin": zmin,
                "old_source": item.get("source", "")
            })
        return False

    if item.get("omit", False):
        if log is not None:
            log.append({
                "edge": key,
                "source": source,
                "status": "already_omitted",
                "old_source": item.get("source", "")
            })
        return False

    old_source = item.get("source", "")
    old_kind = item.get("kind", "")

    registry[key] = {
        **item,
        "curve": None,
        "kind": kind,
        "source": source,
        "priority": max(item.get("priority", 0), 170),
        "replaceable": False,
        "omit": True,
        "info": info if info is not None else {
            "case_type": source,
            "omit": True
        },
        "overwritten_from": old_source,
        "old_kind": old_kind
    }

    if log is not None:
        log.append({
            "edge": key,
            "source": source,
            "status": "omitted",
            "old_source": old_source
        })

    return True


def f2_print_zmin_diagnostic(registry, max_rows=80):
    rows = []

    for edge, item in registry.items():

        if item.get("omit", False):
            continue

        if item.get("curve", None) is None:
            continue

        if f2_is_direct_guard_item(item):
            continue

        C = f2_curve_to_array(item.get("curve", None))

        if C is None:
            continue

        zmin = f2_curve_zmin(C)
        zmax = float(np.nanmax(C[:, 2]))
        ground_meta = f2_is_ground_crest_by_metadata(item)

        if ground_meta or zmin <= FILTER2_GROUND_ZMIN_TOL:
            group = "CANDIDATA_suelo"
        elif zmin >= FILTER2_HIGH_ZMIN_MIN:
            group = "OBSTACULO_alto"
        else:
            group = "IGNORADA_intermedia"

        rows.append({
            "edge": edge,
            "source": item.get("source", ""),
            "kind": item.get("kind", ""),
            "zmin": zmin,
            "zmax": zmax,
            "ground_meta": ground_meta,
            "group": group
        })

    order = {
        "CANDIDATA_suelo": 0,
        "OBSTACULO_alto": 1,
        "IGNORADA_intermedia": 2,
    }

    rows = sorted(rows, key=lambda r: (order.get(r["group"], 99), r["zmin"]))

    print("=========================================================")
    print("DIAGNÓSTICO FILTRO 2 - CLASIFICACIÓN POR zmin")
    print("=========================================================")
    print(f"Crestas revisadas: {len(rows)}")
    print(f"Mostrando primeras {min(max_rows, len(rows))}:")
    print(f"Suelo si zmin <= {FILTER2_GROUND_ZMIN_TOL} o metadata de cresta al suelo")
    print(f"Obstáculo alto si zmin >= {FILTER2_HIGH_ZMIN_MIN}")
    print("---------------------------------------------------------")

    for r in rows[:max_rows]:
        print(
            f"{r['edge'][0]}-{r['edge'][1]} | "
            f"{r['group']} | "
            f"zmin={r['zmin']:.6f} | "
            f"zmax={r['zmax']:.3f} | "
            f"source={r['source']} | "
            f"ground_meta={r['ground_meta']} | "
            f"kind={r['kind']}"
        )

    print("=========================================================")

    return rows


def f2_detect_ground_overlaps_with_obstacles(
    registry,
    guard_wire_inputs,
    mast_nodes
):
    ground_candidates, high_crests, guard_obstacles, obstacles = f2_build_obstacles(
        registry=registry,
        guard_wire_inputs=guard_wire_inputs,
        mast_nodes=mast_nodes
    )

    invalid_by_edge = {}

    for grec in ground_candidates:
        edge_g = grec["edge"]
        C_g = grec["curve"]

        for obs in obstacles:
            obs_edge = obs["edge"]

            # No comparar consigo misma.
            if edge_g == obs_edge:
                continue

            overlaps, overlap_info = f2_curve_aligned_overlap_xy(
                C_ground=C_g,
                C_obstacle=obs["curve"],
                distance_tol=FILTER2_OVERLAP_DISTANCE_XY_TOL,
                parallel_sin_tol=FILTER2_PARALLEL_SIN_TOL,
                min_overlap_length=FILTER2_MIN_OVERLAP_LENGTH,
                min_overlap_fraction=FILTER2_MIN_OVERLAP_FRACTION,
                max_points=FILTER2_MAX_POINTS_PER_CURVE
            )

            if not overlaps:
                continue

            if obs["obstacle_type"] == "guard_wire":
                reason = "ground_crest_overlaps_guard_wire"
            else:
                reason = "ground_crest_overlaps_high_crest"

            invalid_by_edge.setdefault(edge_g, []).append({
                "reason": reason,
                "ground_edge": edge_g,
                "ground_source": grec["source"],
                "ground_kind": grec["kind"],
                "ground_zmin": grec["zmin"],
                "ground_meta": grec.get("ground_meta", False),
                "obstacle_edge": obs_edge,
                "obstacle_source": obs["source"],
                "obstacle_kind": obs["kind"],
                "obstacle_zmin": obs.get("zmin", None),
                "obstacle_type": obs["obstacle_type"],
                "overlap_info": overlap_info
            })

    return {
        "invalid_by_edge": invalid_by_edge,
        "ground_candidates": ground_candidates,
        "high_crests": high_crests,
        "guard_obstacles": guard_obstacles,
        "obstacles": obstacles
    }


def apply_filter2_ground_overlap(
    base_registry_result,
    triangles,
    tri_nodes,
    guard_wire_inputs=None
):
    out = copy.deepcopy(base_registry_result)
    registry = out["crest_registry"]
    mast_nodes = out.get("mast_nodes", [])

    # -----------------------------------------------------
    # 0) Diagnóstico opcional
    # -----------------------------------------------------
    if FILTER2_SHOW_ZMIN_DIAGNOSTIC:
        diagnostic_rows = f2_print_zmin_diagnostic(
            registry=registry,
            max_rows=100
        )
    else:
        diagnostic_rows = []

    # -----------------------------------------------------
    # 1) Detectar crestas cercanas al suelo superpuestas
    #    con guardas o crestas altas.
    # -----------------------------------------------------
    detection = f2_detect_ground_overlaps_with_obstacles(
        registry=registry,
        guard_wire_inputs=guard_wire_inputs,
        mast_nodes=mast_nodes
    )

    invalid_by_edge = detection["invalid_by_edge"]

    edge_to_mmm = f2_collect_mmm_triangles_by_edge(triangles)

    # Solo se omiten las crestas cercanas al suelo conflictivas.
    omitted_edges = set(invalid_by_edge.keys())
    omitted_edge_reasons = {}

    removed_mmm_indices = set()
    removed_mmm_records = []

    # -----------------------------------------------------
    # 2) Si una cresta cercana al suelo conflictiva pertenece
    #    a una MMM, se elimina esa MMM completa.
    #
    #    IMPORTANTE:
    #    - No se omiten las otras aristas de esa MMM.
    #    - No hay cascada hacia MMM vecinas.
    # -----------------------------------------------------
    for edge, events in invalid_by_edge.items():

        omitted_edge_reasons.setdefault(edge, []).append({
            "reason": "ground_crest_overlap_with_obstacle",
            "events": events
        })

        for tri_idx in edge_to_mmm.get(edge, []):

            if tri_idx in removed_mmm_indices:
                continue

            tri = triangles[tri_idx]
            tri_edges = f2_triangle_mast_edge_keys(tri)

            removed_mmm_indices.add(tri_idx)

            removed_mmm_records.append({
                "triangle_index": tri_idx,
                "triangle": f2_triangle_label_string(tri),
                "trigger_edge": edge,
                "triangle_edges": tri_edges,
                "events": events,
                "tri": tri,
                "removal_reason": (
                    "MMM eliminada porque una de sus crestas cercanas al suelo "
                    "se superpone en planta XY con una guarda o una cresta alta."
                )
            })

    # -----------------------------------------------------
    # 3) Omitir en el registro SOLO las crestas cercanas al
    #    suelo conflictivas.
    #
    #    No se omiten:
    #      - cables de guarda;
    #      - crestas altas;
    #      - otras aristas de la MMM eliminada;
    #      - aristas compartidas por MMM vecinas.
    # -----------------------------------------------------
    omit_log = []
    omitted_crests = []

    for edge in sorted(omitted_edges):
        item = registry.get(edge, None)

        if item is None:
            omit_log.append({
                "edge": edge,
                "source": FILTER2_SOURCE_NAME,
                "status": "skip_edge_not_in_registry"
            })
            continue

        old_source = item.get("source", "")
        old_kind = item.get("kind", "")

        ok = f2_force_omit_registry_edge(
            registry=registry,
            edge=edge,
            kind="Cresta cercana al suelo omitida por superposición en XY",
            source=FILTER2_SOURCE_NAME,
            info={
                "case_type": FILTER2_SOURCE_NAME,
                "omit": True,
                "old_source": old_source,
                "old_kind": old_kind,
                "edge": edge,
                "reasons": omitted_edge_reasons.get(edge, []),
                "omit_reason": (
                    "La cresta cercana al suelo fue omitida porque se superpone "
                    "en planta XY con un cable de guarda o con una cresta de altura "
                    "considerable. Se elimina la MMM que contiene directamente esta "
                    "cresta, pero no se propaga la eliminación a MMM vecinas."
                )
            },
            log=omit_log
        )

        if ok:
            omitted_crests.append({
                "edge": edge,
                "old_source": old_source,
                "new_source": FILTER2_SOURCE_NAME,
                "reasons": omitted_edge_reasons.get(edge, [])
            })

    # -----------------------------------------------------
    # 4) Filtrar triángulos.
    #    Aquí sí desaparece la tetra MMM completa afectada,
    #    pero solo esa tetra directa.
    # -----------------------------------------------------
    kept_triangles = []

    for idx, tri in enumerate(triangles):
        if idx in removed_mmm_indices:
            continue

        kept_triangles.append(tri)

    filtered_tri_nodes = f2_filter_tri_nodes_used_by_triangles(
        tri_nodes=tri_nodes,
        triangles=kept_triangles
    )

    # -----------------------------------------------------
    # 5) Actualizar metadatos con las MMM sobrevivientes.
    # -----------------------------------------------------
    if "unique_mast_edges_from_triangles" in globals():
        out["mm_edges"] = unique_mast_edges_from_triangles(kept_triangles)

    if "unique_mast_q_edges_from_triangles" in globals():
        out["mq_edges"] = unique_mast_q_edges_from_triangles(kept_triangles)

    if "build_common_tetra_edges_from_triangles" in globals():
        out["common_tetra_edges"] = build_common_tetra_edges_from_triangles(kept_triangles)

    out["crest_registry"] = registry

    out["filter2_zmin_diagnostic_rows"] = diagnostic_rows

    out["filter2_invalid_ground_by_edge"] = invalid_by_edge
    out["filter2_ground_candidates"] = detection["ground_candidates"]
    out["filter2_high_crests"] = detection["high_crests"]
    out["filter2_guard_obstacles"] = detection["guard_obstacles"]
    out["filter2_obstacles"] = detection["obstacles"]

    out["filter2_removed_mmm"] = removed_mmm_records
    out["filter2_removed_mmm_indices"] = removed_mmm_indices
    out["filter2_omitted_edges"] = omitted_edges
    out["filter2_omitted_crests"] = omitted_crests
    out["filter2_omitted_edge_reasons"] = omitted_edge_reasons
    out["filter2_omit_log"] = omit_log

    return out, kept_triangles, filtered_tri_nodes


import copy


import numpy as np


FILTER3_SPECIAL_SOURCES = {
    "independent_guard_lines",
    "shared_guard_plus_k",
    "three_guard_chain",
    "four_guard_closed",
}


FILTER3_SOURCE_NAME = "filter3_proper_crossing_with_special_crest"


FILTER3_MAX_POINTS_PER_CURVE = None   # Puedes poner 160 si se pone lento.


FILTER3_SHOW_SUMMARY = True


FILTER3_REQUIRE_PROPER_INTERIOR_CROSSING = True


FILTER3_SKIP_SHARED_MAST_EDGES = True


FILTER3_INTERIOR_TOL = 1e-4


def f3_cross2d(u, v):
    return u[0] * v[1] - u[1] * v[0]


def f3_edge_key(a, b):
    if "edge_key" in globals():
        return edge_key(a, b)

    return tuple(sorted([a, b]))


def f3_edges_share_mast(edge_a, edge_b):
    """
    Retorna True si dos aristas comparten algún mástil.
    """
    return len(set(edge_a).intersection(set(edge_b))) > 0


def f3_curve_to_array(curve):
    if curve is None:
        return None

    if "curve_to_array" in globals():
        C = curve_to_array(curve)
    else:
        if isinstance(curve, tuple) and len(curve) == 3:
            x, y, z = curve
            C = np.column_stack([x, y, z]).astype(float)
        else:
            C = np.asarray(curve, dtype=float)

    if C is None:
        return None

    C = np.asarray(C, dtype=float)

    if C.ndim != 2 or C.shape[1] != 3:
        return None

    C[:, 2] = np.maximum(C[:, 2], 0.0)

    return C


def f3_bbox_segments_overlap_xy(a, b, c, d, tol=1e-9):
    a = np.asarray(a, dtype=float)[:2]
    b = np.asarray(b, dtype=float)[:2]
    c = np.asarray(c, dtype=float)[:2]
    d = np.asarray(d, dtype=float)[:2]

    aminx = min(a[0], b[0]) - tol
    amaxx = max(a[0], b[0]) + tol
    aminy = min(a[1], b[1]) - tol
    amaxy = max(a[1], b[1]) + tol

    cminx = min(c[0], d[0]) - tol
    cmaxx = max(c[0], d[0]) + tol
    cminy = min(c[1], d[1]) - tol
    cmaxy = max(c[1], d[1]) + tol

    if amaxx < cminx or cmaxx < aminx:
        return False

    if amaxy < cminy or cmaxy < aminy:
        return False

    return True


def f3_segment_intersection_xy_proper(
    a,
    b,
    c,
    d,
    tol=1e-9,
    interior_tol=FILTER3_INTERIOR_TOL
):
    """
    Cruce propio entre dos segmentos XY.

    Cuenta únicamente si:
      - los segmentos no son paralelos;
      - la intersección cae en el interior de ambos segmentos;
      - no es contacto en extremos;
      - no es solape colineal.
    """
    a = np.asarray(a, dtype=float)[:2]
    b = np.asarray(b, dtype=float)[:2]
    c = np.asarray(c, dtype=float)[:2]
    d = np.asarray(d, dtype=float)[:2]

    if not f3_bbox_segments_overlap_xy(a, b, c, d, tol=tol):
        return False, None, None, None

    r = b - a
    s = d - c
    qmp = c - a

    rxs = f3_cross2d(r, s)

    # Paralelo o colineal: NO cuenta para este filtro.
    if abs(rxs) <= tol:
        return False, None, None, None

    t = f3_cross2d(qmp, s) / rxs
    u = f3_cross2d(qmp, r) / rxs

    # Cruce interior estricto.
    if (
        interior_tol < t < 1.0 - interior_tol
        and interior_tol < u < 1.0 - interior_tol
    ):
        P = a + t * r
        return True, P, t, u

    return False, None, None, None


def f3_downsample_curve(C, max_points=None):
    C = np.asarray(C, dtype=float)

    if max_points is None:
        return C

    if len(C) <= max_points:
        return C

    idx = np.linspace(0, len(C) - 1, max_points).astype(int)

    return C[idx]


def f3_curve_pair_crosses_xy(
    C1,
    C2,
    tol=1e-9,
    max_points=None
):
    """
    Detecta cruces propios entre curvas proyectadas en XY.

    Esta versión es menos agresiva:
      - no cuenta contactos en extremos;
      - no cuenta solapes colineales;
      - no cuenta toques puntuales;
      - solo cuenta cruces interiores reales.
    """
    C1 = f3_curve_to_array(C1)
    C2 = f3_curve_to_array(C2)

    if C1 is None or C2 is None:
        return False, []

    if len(C1) < 2 or len(C2) < 2:
        return False, []

    C1 = f3_downsample_curve(C1, max_points=max_points)
    C2 = f3_downsample_curve(C2, max_points=max_points)

    xy1 = C1[:, :2]
    xy2 = C2[:, :2]

    min1 = xy1.min(axis=0)
    max1 = xy1.max(axis=0)
    min2 = xy2.min(axis=0)
    max2 = xy2.max(axis=0)

    if max1[0] < min2[0] - tol or max2[0] < min1[0] - tol:
        return False, []

    if max1[1] < min2[1] - tol or max2[1] < min1[1] - tol:
        return False, []

    intersections = []

    for i in range(len(xy1) - 1):
        a = xy1[i]
        b = xy1[i + 1]

        for j in range(len(xy2) - 1):
            c = xy2[j]
            d = xy2[j + 1]

            ok, P, t, u = f3_segment_intersection_xy_proper(
                a=a,
                b=b,
                c=c,
                d=d,
                tol=tol,
                interior_tol=FILTER3_INTERIOR_TOL
            )

            if not ok or P is None:
                continue

            intersections.append({
                "point_xy": np.asarray(P, dtype=float),
                "segment_i": i,
                "segment_j": j,
                "t": t,
                "u": u,
            })

    return len(intersections) > 0, intersections


def f3_triangle_type(tri):
    if "classify_triangle_type" in globals():
        return classify_triangle_type(tri)

    types = [n["type"] for n in tri["nodes"]]
    nM = sum(t == "mast_top" for t in types)
    nQ = sum(t == "Q" for t in types)

    if nM == 3:
        return "M-M-M"
    if nM == 2 and nQ == 1:
        return "M-M-Q"
    if nM == 1 and nQ == 2:
        return "M-Q-Q"
    if nQ == 3:
        return "Q-Q-Q"

    return "Otro"


def f3_triangle_label_string(tri):
    return "-".join([n["label"] for n in tri["nodes"]])


def f3_triangle_mast_edge_keys(tri):
    nodes = tri["nodes"]
    edges = []

    for a, b in [(0, 1), (1, 2), (2, 0)]:
        n1 = nodes[a]
        n2 = nodes[b]

        if n1["type"] != "mast_top" or n2["type"] != "mast_top":
            continue

        edges.append(f3_edge_key(n1["label"], n2["label"]))

    return edges


def f3_filter_tri_nodes_used_by_triangles(tri_nodes, triangles):
    used = set()

    for tri in triangles:
        for n in tri["nodes"]:
            used.add((n["type"], n["label"]))

    return [
        n for n in tri_nodes
        if (n["type"], n["label"]) in used
    ]


def f3_collect_mmm_triangles_by_edge(triangles):
    """
    Mapa:
        edge_key -> lista de índices de MMM que usan esa arista.
    """
    edge_to_mmm = {}

    for idx, tri in enumerate(triangles):
        if f3_triangle_type(tri) != "M-M-M":
            continue

        for edge in f3_triangle_mast_edge_keys(tri):
            edge_to_mmm.setdefault(edge, []).append(idx)

    return edge_to_mmm


def f3_collect_mmm_edges(triangles):
    """
    Conjunto de aristas M-M que pertenecen a MMM.
    """
    mmm_edges = set()

    for tri in triangles:
        if f3_triangle_type(tri) != "M-M-M":
            continue

        for edge in f3_triangle_mast_edge_keys(tri):
            mmm_edges.add(edge)

    return mmm_edges


def f3_is_direct_guard_item(item):
    return item.get("source", "") == "direct_guard_wire"


def f3_is_special_crest_item(item):
    return item.get("source", "") in FILTER3_SPECIAL_SOURCES


def f3_is_protected_item(item):
    """
    Elementos que este filtro nunca debe eliminar.
    """
    return (
        f3_is_direct_guard_item(item)
        or f3_is_special_crest_item(item)
    )


def f3_collect_active_special_crests(registry):
    """
    Recoge las crestas especiales activas después de Filtro 1 y Filtro 2.
    """
    specials = []

    for edge, item in registry.items():

        if item.get("omit", False):
            continue

        if item.get("curve", None) is None:
            continue

        if not f3_is_special_crest_item(item):
            continue

        C = f3_curve_to_array(item.get("curve", None))

        if C is None:
            continue

        specials.append({
            "edge": edge,
            "item": item,
            "curve": C,
            "source": item.get("source", ""),
            "kind": item.get("kind", "")
        })

    return specials


def f3_collect_candidate_mmm_crests(registry, triangles):
    """
    Recoge las crestas NO especiales y NO cables que forman parte de MMM.

    Solo estas crestas son candidatas a eliminar.
    """
    mmm_edges = f3_collect_mmm_edges(triangles)

    candidates = []

    for edge, item in registry.items():

        if edge not in mmm_edges:
            continue

        if item.get("omit", False):
            continue

        if item.get("curve", None) is None:
            continue

        # Nunca eliminar cables ni especiales.
        if f3_is_protected_item(item):
            continue

        C = f3_curve_to_array(item.get("curve", None))

        if C is None:
            continue

        candidates.append({
            "edge": edge,
            "item": item,
            "curve": C,
            "source": item.get("source", ""),
            "kind": item.get("kind", "")
        })

    return candidates


def f3_force_omit_registry_edge(
    registry,
    edge,
    kind,
    source,
    info=None,
    log=None
):
    """
    Omite una cresta del registro.
    Este filtro nunca omite:
      - cables de guarda directos;
      - crestas especiales.
    """
    key = f3_edge_key(edge[0], edge[1])

    if key not in registry:
        if log is not None:
            log.append({
                "edge": key,
                "source": source,
                "status": "skip_edge_not_in_registry"
            })
        return False

    item = registry[key]

    if f3_is_direct_guard_item(item):
        if log is not None:
            log.append({
                "edge": key,
                "source": source,
                "status": "skip_direct_guard_wire"
            })
        return False

    if f3_is_special_crest_item(item):
        if log is not None:
            log.append({
                "edge": key,
                "source": source,
                "status": "skip_special_crest"
            })
        return False

    if item.get("omit", False):
        if log is not None:
            log.append({
                "edge": key,
                "source": source,
                "status": "already_omitted",
                "old_source": item.get("source", "")
            })
        return False

    old_source = item.get("source", "")
    old_kind = item.get("kind", "")

    registry[key] = {
        **item,
        "curve": None,
        "kind": kind,
        "source": source,
        "priority": max(item.get("priority", 0), 180),
        "replaceable": False,
        "omit": True,
        "info": info if info is not None else {
            "case_type": source,
            "omit": True
        },
        "overwritten_from": old_source,
        "old_kind": old_kind
    }

    if log is not None:
        log.append({
            "edge": key,
            "source": source,
            "status": "omitted",
            "old_source": old_source
        })

    return True


def f3_detect_mmm_crests_crossing_specials(registry, triangles):
    """
    Detecta crestas NO especiales de MMM que cruzan en planta XY
    con crestas especiales activas.

    Corrección:
      - No compara aristas que comparten mástil.
      - Solo cuenta cruces interiores reales.
    """
    specials = f3_collect_active_special_crests(registry)

    candidates = f3_collect_candidate_mmm_crests(
        registry=registry,
        triangles=triangles
    )

    invalid_by_edge = {}
    skipped_shared_mast_pairs = []

    for cand in candidates:
        cand_edge = cand["edge"]
        cand_curve = cand["curve"]

        for sp in specials:
            sp_edge = sp["edge"]

            if cand_edge == sp_edge:
                continue

            # Evita borrar MMM por relaciones normales entre aristas
            # que se unen en un mismo mástil.
            if FILTER3_SKIP_SHARED_MAST_EDGES and f3_edges_share_mast(cand_edge, sp_edge):
                skipped_shared_mast_pairs.append({
                    "candidate_edge": cand_edge,
                    "special_edge": sp_edge,
                    "candidate_source": cand["source"],
                    "special_source": sp["source"],
                    "reason": "shared_mast_skipped"
                })
                continue

            crosses, intersections = f3_curve_pair_crosses_xy(
                C1=cand_curve,
                C2=sp["curve"],
                tol=1e-9,
                max_points=FILTER3_MAX_POINTS_PER_CURVE
            )

            if not crosses:
                continue

            invalid_by_edge.setdefault(cand_edge, []).append({
                "reason": "mmm_crest_proper_crosses_special_crest",
                "candidate_edge": cand_edge,
                "candidate_source": cand["source"],
                "candidate_kind": cand["kind"],
                "special_edge": sp_edge,
                "special_source": sp["source"],
                "special_kind": sp["kind"],
                "intersections": intersections
            })

    return {
        "invalid_by_edge": invalid_by_edge,
        "special_crests": specials,
        "candidate_mmm_crests": candidates,
        "skipped_shared_mast_pairs": skipped_shared_mast_pairs
    }


def apply_filter3_special_crests_vs_mmm_crests(
    base_registry_result,
    triangles,
    tri_nodes
):
    out = copy.deepcopy(base_registry_result)
    registry = out["crest_registry"]

    detection = f3_detect_mmm_crests_crossing_specials(
        registry=registry,
        triangles=triangles
    )

    invalid_by_edge = detection["invalid_by_edge"]

    edge_to_mmm = f3_collect_mmm_triangles_by_edge(triangles)

    removed_mmm_indices = set()
    removed_mmm_records = []

    omitted_edges = set(invalid_by_edge.keys())
    omitted_edge_reasons = {}

    # -----------------------------------------------------
    # 1) Eliminar MMM que usan crestas no especiales
    #    cruzadas con especiales.
    # -----------------------------------------------------
    for edge, events in invalid_by_edge.items():

        omitted_edge_reasons.setdefault(edge, []).append({
            "reason": "non_special_mmm_crest_proper_crosses_special",
            "events": events
        })

        for tri_idx in edge_to_mmm.get(edge, []):

            if tri_idx in removed_mmm_indices:
                continue

            tri = triangles[tri_idx]
            tri_edges = f3_triangle_mast_edge_keys(tri)

            removed_mmm_indices.add(tri_idx)

            removed_mmm_records.append({
                "triangle_index": tri_idx,
                "triangle": f3_triangle_label_string(tri),
                "trigger_edge": edge,
                "triangle_edges": tri_edges,
                "events": events,
                "tri": tri
            })

    # -----------------------------------------------------
    # 2) Omitir únicamente las crestas no especiales
    #    que se cruzaron con especiales.
    #
    #    IMPORTANTE:
    #    No se omiten las demás crestas de la MMM eliminada.
    # -----------------------------------------------------
    omit_log = []
    omitted_crests = []

    for edge in sorted(omitted_edges):
        item = registry.get(edge, None)

        if item is None:
            omit_log.append({
                "edge": edge,
                "source": FILTER3_SOURCE_NAME,
                "status": "skip_edge_not_in_registry"
            })
            continue

        old_source = item.get("source", "")
        old_kind = item.get("kind", "")

        ok = f3_force_omit_registry_edge(
            registry=registry,
            edge=edge,
            kind="Cresta omitida por cruce interior real con cresta especial",
            source=FILTER3_SOURCE_NAME,
            info={
                "case_type": FILTER3_SOURCE_NAME,
                "omit": True,
                "old_source": old_source,
                "old_kind": old_kind,
                "edge": edge,
                "reasons": omitted_edge_reasons.get(edge, []),
                "omit_reason": (
                    "Cresta no especial perteneciente a una MMM omitida porque "
                    "su proyección XY cruza de forma interior real con una cresta "
                    "especial resultante de modelos de guardas. "
                    "No se omitió por contacto en extremos, solape colineal "
                    "ni por compartir mástil."
                )
            },
            log=omit_log
        )

        if ok:
            omitted_crests.append({
                "edge": edge,
                "old_source": old_source,
                "new_source": FILTER3_SOURCE_NAME,
                "reasons": omitted_edge_reasons.get(edge, [])
            })

    # -----------------------------------------------------
    # 3) Filtrar triángulos.
    # -----------------------------------------------------
    kept_triangles = []

    for idx, tri in enumerate(triangles):
        if idx in removed_mmm_indices:
            continue

        kept_triangles.append(tri)

    filtered_tri_nodes = f3_filter_tri_nodes_used_by_triangles(
        tri_nodes=tri_nodes,
        triangles=kept_triangles
    )

    # -----------------------------------------------------
    # 4) ACTUALIZAR METADATOS SIN PRUNE AGRESIVO
    #
    #    Esta es la corrección clave:
    #    - NO reconstruimos crest_registry solo con kept_triangles.
    #    - NO borramos crestas no conflictivas que pertenecían a una MMM eliminada.
    #    - Solo quedan omitidas las crestas marcadas explícitamente con omit=True.
    # -----------------------------------------------------
    out["crest_registry"] = registry

    if "unique_mast_edges_from_triangles" in globals():
        out["mm_edges"] = unique_mast_edges_from_triangles(kept_triangles)

    if "unique_mast_q_edges_from_triangles" in globals():
        out["mq_edges"] = unique_mast_q_edges_from_triangles(kept_triangles)

    if "build_common_tetra_edges_from_triangles" in globals():
        out["common_tetra_edges"] = build_common_tetra_edges_from_triangles(kept_triangles)

    out["filter3_invalid_by_edge"] = invalid_by_edge
    out["filter3_special_crests"] = detection["special_crests"]
    out["filter3_candidate_mmm_crests"] = detection["candidate_mmm_crests"]
    out["filter3_skipped_shared_mast_pairs"] = detection["skipped_shared_mast_pairs"]
    out["filter3_removed_mmm"] = removed_mmm_records
    out["filter3_removed_mmm_indices"] = removed_mmm_indices
    out["filter3_omitted_crests"] = omitted_crests
    out["filter3_omit_log"] = omit_log

    return out, kept_triangles, filtered_tri_nodes


import copy


import numpy as np


FILTER13D_SOURCE_NAME = "filter13D_lower_zmin_crossed_crest"


FILTER13D_ZMIN_COMPARE_TOL = 1e-6


FILTER13D_XY_INTERSECTION_TOL = 1e-9


FILTER13D_IGNORE_GLOBAL_ENDPOINT_TOUCH = True


FILTER13D_MIN_COLINEAR_OVERLAP = 1e-3


FILTER13D_MAX_POINTS_PER_CURVE = None


FILTER13D_REMOVE_MMQ_WITH_OMITTED_CREST = True


FILTER13D_SHOW_SUMMARY = True


def f13d_edge_key(a, b):
    if "edge_key" in globals():
        return edge_key(a, b)
    return tuple(sorted([a, b]))


def f13d_curve_to_array(curve):
    if curve is None:
        return None

    if "curve_to_array" in globals():
        C = curve_to_array(curve)
    else:
        if isinstance(curve, tuple) and len(curve) == 3:
            x, y, z = curve
            C = np.column_stack([x, y, z]).astype(float)
        else:
            C = np.asarray(curve, dtype=float)

    if C is None:
        return None

    C = np.asarray(C, dtype=float)

    if C.ndim != 2 or C.shape[1] != 3:
        return None

    C[:, 2] = np.maximum(C[:, 2], 0.0)

    return C


def f13d_curve_zmin(C):
    C = f13d_curve_to_array(C)

    if C is None or len(C) == 0:
        return np.nan

    return float(np.nanmin(C[:, 2]))


def f13d_downsample_curve(C, max_points=None):
    C = np.asarray(C, dtype=float)

    if max_points is None:
        return C

    if len(C) <= max_points:
        return C

    idx = np.linspace(0, len(C) - 1, max_points).astype(int)
    return C[idx]


def f13d_cross2d(u, v):
    return u[0] * v[1] - u[1] * v[0]


def f13d_point_close_xy(p, q, tol=1e-7):
    p = np.asarray(p, dtype=float)[:2]
    q = np.asarray(q, dtype=float)[:2]

    return np.linalg.norm(p - q) <= tol


def f13d_point_is_global_endpoint_xy(P, C, tol=1e-7):
    C = np.asarray(C, dtype=float)

    if len(C) == 0:
        return False

    P = np.asarray(P, dtype=float)[:2]

    return (
        f13d_point_close_xy(P, C[0, :2], tol=tol)
        or f13d_point_close_xy(P, C[-1, :2], tol=tol)
    )


def f13d_bbox_segments_overlap_xy(a, b, c, d, tol=1e-9):
    a = np.asarray(a, dtype=float)[:2]
    b = np.asarray(b, dtype=float)[:2]
    c = np.asarray(c, dtype=float)[:2]
    d = np.asarray(d, dtype=float)[:2]

    aminx = min(a[0], b[0]) - tol
    amaxx = max(a[0], b[0]) + tol
    aminy = min(a[1], b[1]) - tol
    amaxy = max(a[1], b[1]) + tol

    cminx = min(c[0], d[0]) - tol
    cmaxx = max(c[0], d[0]) + tol
    cminy = min(c[1], d[1]) - tol
    cmaxy = max(c[1], d[1]) + tol

    if amaxx < cminx or cmaxx < aminx:
        return False

    if amaxy < cminy or cmaxy < aminy:
        return False

    return True


def f13d_segment_intersection_xy(
    a,
    b,
    c,
    d,
    tol=FILTER13D_XY_INTERSECTION_TOL,
    min_colinear_overlap=FILTER13D_MIN_COLINEAR_OVERLAP
):
    """
    Detecta intersección entre dos segmentos XY.

    Cuenta:
      - cruce propio;
      - cruce sobre punto de muestreo;
      - solape colineal con longitud mínima.

    No decide todavía si el punto es extremo global;
    eso se filtra a nivel de curva.
    """
    a = np.asarray(a, dtype=float)[:2]
    b = np.asarray(b, dtype=float)[:2]
    c = np.asarray(c, dtype=float)[:2]
    d = np.asarray(d, dtype=float)[:2]

    if not f13d_bbox_segments_overlap_xy(a, b, c, d, tol=tol):
        return False, None, None, None, "bbox_no_overlap"

    r = b - a
    s = d - c
    qmp = c - a

    rxs = f13d_cross2d(r, s)
    qmpxr = f13d_cross2d(qmp, r)

    # -----------------------------------------------------
    # Caso no paralelo
    # -----------------------------------------------------
    if abs(rxs) > tol:
        t = f13d_cross2d(qmp, s) / rxs
        u = f13d_cross2d(qmp, r) / rxs

        if (-tol <= t <= 1.0 + tol) and (-tol <= u <= 1.0 + tol):
            t_clip = np.clip(t, 0.0, 1.0)
            u_clip = np.clip(u, 0.0, 1.0)
            P = a + t_clip * r
            return True, P, t_clip, u_clip, "proper_or_endpoint_crossing"

        return False, None, None, None, "no_crossing"

    # -----------------------------------------------------
    # Paralelo no colineal
    # -----------------------------------------------------
    if abs(qmpxr) > tol:
        return False, None, None, None, "parallel_not_colinear"

    # -----------------------------------------------------
    # Colineal
    # -----------------------------------------------------
    rr = np.dot(r, r)

    if rr < tol:
        return False, None, None, None, "degenerate_segment"

    t0 = np.dot(c - a, r) / rr
    t1 = np.dot(d - a, r) / rr

    tmin = max(0.0, min(t0, t1))
    tmax = min(1.0, max(t0, t1))

    if tmax < tmin - tol:
        return False, None, None, None, "colinear_no_overlap"

    overlap_len = (tmax - tmin) * np.linalg.norm(r)

    if overlap_len < min_colinear_overlap:
        return False, None, None, None, "colinear_overlap_too_small"

    tmid = 0.5 * (tmin + tmax)
    P = a + tmid * r

    return True, P, tmid, None, "colinear_overlap"


def f13d_curve_pair_crosses_xy(
    C1,
    C2,
    tol=FILTER13D_XY_INTERSECTION_TOL,
    max_points=FILTER13D_MAX_POINTS_PER_CURVE,
    ignore_global_endpoint_touch=FILTER13D_IGNORE_GLOBAL_ENDPOINT_TOUCH
):
    """
    Detecta si dos curvas se cortan en planta XY.

    No cuenta como cruce el contacto trivial en extremos globales
    si ignore_global_endpoint_touch=True.
    """
    C1 = f13d_curve_to_array(C1)
    C2 = f13d_curve_to_array(C2)

    if C1 is None or C2 is None:
        return False, []

    if len(C1) < 2 or len(C2) < 2:
        return False, []

    C1 = f13d_downsample_curve(C1, max_points=max_points)
    C2 = f13d_downsample_curve(C2, max_points=max_points)

    xy1 = C1[:, :2]
    xy2 = C2[:, :2]

    min1 = xy1.min(axis=0)
    max1 = xy1.max(axis=0)
    min2 = xy2.min(axis=0)
    max2 = xy2.max(axis=0)

    if max1[0] < min2[0] - tol or max2[0] < min1[0] - tol:
        return False, []

    if max1[1] < min2[1] - tol or max2[1] < min1[1] - tol:
        return False, []

    intersections = []

    for i in range(len(xy1) - 1):
        a = xy1[i]
        b = xy1[i + 1]

        for j in range(len(xy2) - 1):
            c = xy2[j]
            d = xy2[j + 1]

            ok, P, t, u, kind = f13d_segment_intersection_xy(
                a=a,
                b=b,
                c=c,
                d=d,
                tol=tol
            )

            if not ok or P is None:
                continue

            if ignore_global_endpoint_touch:
                endpoint_1 = f13d_point_is_global_endpoint_xy(P, C1, tol=1e-6)
                endpoint_2 = f13d_point_is_global_endpoint_xy(P, C2, tol=1e-6)

                # Si el contacto ocurre en extremos globales de ambas curvas,
                # normalmente es solo una unión en un mástil.
                if endpoint_1 and endpoint_2:
                    continue

            intersections.append({
                "point_xy": np.asarray(P, dtype=float),
                "segment_i": i,
                "segment_j": j,
                "t": t,
                "u": u,
                "kind": kind
            })

    return len(intersections) > 0, intersections


def f13d_triangle_type(tri):
    if "classify_triangle_type" in globals():
        return classify_triangle_type(tri)

    types = [n["type"] for n in tri["nodes"]]
    nM = sum(t == "mast_top" for t in types)
    nQ = sum(t == "Q" for t in types)

    if nM == 3:
        return "M-M-M"
    if nM == 2 and nQ == 1:
        return "M-M-Q"
    if nM == 1 and nQ == 2:
        return "M-Q-Q"
    if nQ == 3:
        return "Q-Q-Q"

    return "Otro"


def f13d_triangle_label_string(tri):
    return "-".join([n["label"] for n in tri["nodes"]])


def f13d_triangle_mast_edge_keys(tri):
    nodes = tri["nodes"]
    edges = []

    for a, b in [(0, 1), (1, 2), (2, 0)]:
        n1 = nodes[a]
        n2 = nodes[b]

        if n1["type"] != "mast_top" or n2["type"] != "mast_top":
            continue

        edges.append(f13d_edge_key(n1["label"], n2["label"]))

    return edges


def f13d_filter_tri_nodes_used_by_triangles(tri_nodes, triangles):
    used = set()

    for tri in triangles:
        for n in tri["nodes"]:
            used.add((n["type"], n["label"]))

    return [
        n for n in tri_nodes
        if (n["type"], n["label"]) in used
    ]


def f13d_is_direct_guard_item(item):
    return item.get("source", "") == "direct_guard_wire"


def f13d_node_by_label_from_masts(mast_nodes):
    if "node_by_label_from_masts" in globals():
        return node_by_label_from_masts(mast_nodes)

    return {n["label"]: n for n in mast_nodes}


def f13d_collect_active_registry_curves(registry):
    """
    Recoge curvas activas del crest_registry.

    Incluye:
      - crestas base;
      - crestas especiales;
      - cables de guarda directos.

    Pero los cables se marcan como protegidos.
    """
    records = []

    for edge, item in registry.items():

        if item.get("omit", False):
            continue

        if item.get("curve", None) is None:
            continue

        C = f13d_curve_to_array(item.get("curve", None))

        if C is None:
            continue

        zmin = f13d_curve_zmin(C)

        records.append({
            "edge": edge,
            "item": item,
            "curve": C,
            "source": item.get("source", ""),
            "kind": item.get("kind", ""),
            "zmin": zmin,
            "protected": f13d_is_direct_guard_item(item),
            "protected_reason": (
                "direct_guard_wire"
                if f13d_is_direct_guard_item(item)
                else ""
            ),
            "origin": "registry"
        })

    return records


def f13d_collect_guard_input_curves_not_in_registry(
    guard_wire_inputs,
    mast_nodes,
    registry
):
    """
    Añade cables de guarda desde guard_wire_inputs como obstáculos protegidos
    si por alguna razón no están en el registro.
    """
    records = []

    if guard_wire_inputs is None:
        return records

    node_by_label = f13d_node_by_label_from_masts(mast_nodes)

    existing_edges = set(registry.keys())

    for w in guard_wire_inputs:
        a_label = f"M{w['i']}"
        b_label = f"M{w['j']}"

        edge = f13d_edge_key(a_label, b_label)

        if edge in existing_edges:
            continue

        if a_label not in node_by_label or b_label not in node_by_label:
            continue

        A = node_by_label[a_label]
        B = node_by_label[b_label]

        C = np.array([
            [A["x"], A["y"], A["z"]],
            [B["x"], B["y"], B["z"]]
        ], dtype=float)

        C[:, 2] = np.maximum(C[:, 2], 0.0)

        records.append({
            "edge": edge,
            "item": {
                "source": "direct_guard_wire_input",
                "kind": "Cable de guarda directo desde entrada",
                "curve": C,
                "omit": False
            },
            "curve": C,
            "source": "direct_guard_wire_input",
            "kind": "Cable de guarda directo desde entrada",
            "zmin": f13d_curve_zmin(C),
            "protected": True,
            "protected_reason": "direct_guard_wire_input",
            "origin": "guard_wire_inputs"
        })

    return records


def f13d_collect_all_comparable_curves(
    registry,
    guard_wire_inputs=None,
    mast_nodes=None
):
    records = f13d_collect_active_registry_curves(registry)

    extra_guards = f13d_collect_guard_input_curves_not_in_registry(
        guard_wire_inputs=guard_wire_inputs,
        mast_nodes=mast_nodes if mast_nodes is not None else [],
        registry=registry
    )

    records.extend(extra_guards)

    return records


def f13d_force_omit_registry_edge(
    registry,
    edge,
    source,
    info=None,
    log=None
):
    """
    Omite una cresta en el registro.
    Nunca omite cables de guarda directos.
    """
    key = f13d_edge_key(edge[0], edge[1])

    if key not in registry:
        if log is not None:
            log.append({
                "edge": key,
                "status": "skip_edge_not_in_registry"
            })
        return False

    item = registry[key]

    if f13d_is_direct_guard_item(item):
        if log is not None:
            log.append({
                "edge": key,
                "status": "skip_direct_guard_wire"
            })
        return False

    if item.get("omit", False):
        if log is not None:
            log.append({
                "edge": key,
                "status": "already_omitted",
                "old_source": item.get("source", "")
            })
        return False

    old_source = item.get("source", "")
    old_kind = item.get("kind", "")

    registry[key] = {
        **item,
        "curve": None,
        "kind": "Cresta omitida por Filtro 13D",
        "source": source,
        "priority": max(item.get("priority", 0), 190),
        "replaceable": False,
        "omit": True,
        "info": info if info is not None else {
            "case_type": source,
            "omit": True
        },
        "overwritten_from": old_source,
        "old_kind": old_kind
    }

    if log is not None:
        log.append({
            "edge": key,
            "status": "omitted",
            "old_source": old_source
        })

    return True


def f13d_detect_crossed_crests_and_lower_zmin_losers(
    registry,
    guard_wire_inputs=None,
    mast_nodes=None
):
    """
    Compara todos los pares de curvas activas.

    Si dos curvas se cruzan en XY:
      - se elimina la de menor zmin;
      - si empate de zmin, no se elimina ninguna.
    """
    records = f13d_collect_all_comparable_curves(
        registry=registry,
        guard_wire_inputs=guard_wire_inputs,
        mast_nodes=mast_nodes
    )

    loser_by_edge = {}
    pair_events = []
    tie_events = []
    protected_loser_events = []

    for i in range(len(records)):
        A = records[i]

        for j in range(i + 1, len(records)):
            B = records[j]

            edge_a = A["edge"]
            edge_b = B["edge"]

            # No comparar la misma arista.
            if edge_a == edge_b:
                continue

            crosses, intersections = f13d_curve_pair_crosses_xy(
                C1=A["curve"],
                C2=B["curve"],
                tol=FILTER13D_XY_INTERSECTION_TOL,
                max_points=FILTER13D_MAX_POINTS_PER_CURVE,
                ignore_global_endpoint_touch=FILTER13D_IGNORE_GLOBAL_ENDPOINT_TOUCH
            )

            if not crosses:
                continue

            za = A["zmin"]
            zb = B["zmin"]

            event_base = {
                "edge_a": edge_a,
                "edge_b": edge_b,
                "source_a": A["source"],
                "source_b": B["source"],
                "kind_a": A["kind"],
                "kind_b": B["kind"],
                "zmin_a": za,
                "zmin_b": zb,
                "intersections": intersections
            }

            # Empate: no eliminar.
            if not np.isfinite(za) or not np.isfinite(zb):
                tie_events.append({
                    **event_base,
                    "reason": "zmin_not_finite"
                })
                continue

            if abs(za - zb) <= FILTER13D_ZMIN_COMPARE_TOL:
                tie_events.append({
                    **event_base,
                    "reason": "zmin_tie"
                })
                continue

            if za < zb:
                loser = A
                winner = B
                loser_z = za
                winner_z = zb
            else:
                loser = B
                winner = A
                loser_z = zb
                winner_z = za

            pair_event = {
                **event_base,
                "winner_edge": winner["edge"],
                "winner_source": winner["source"],
                "winner_kind": winner["kind"],
                "winner_zmin": winner_z,
                "loser_edge": loser["edge"],
                "loser_source": loser["source"],
                "loser_kind": loser["kind"],
                "loser_zmin": loser_z,
                "reason": "lower_zmin_loses"
            }

            pair_events.append(pair_event)

            # Si el perdedor es cable de guarda, no se elimina.
            if loser.get("protected", False):
                protected_loser_events.append({
                    **pair_event,
                    "protected_reason": loser.get("protected_reason", "")
                })
                continue

            loser_edge = loser["edge"]

            loser_by_edge.setdefault(loser_edge, []).append(pair_event)

    return {
        "records": records,
        "loser_by_edge": loser_by_edge,
        "pair_events": pair_events,
        "tie_events": tie_events,
        "protected_loser_events": protected_loser_events
    }


def apply_filter13D_crossed_crests_by_zmin(
    base_registry_result,
    triangles,
    tri_nodes,
    guard_wire_inputs=None
):
    out = copy.deepcopy(base_registry_result)
    registry = out["crest_registry"]
    mast_nodes = out.get("mast_nodes", [])

    detection = f13d_detect_crossed_crests_and_lower_zmin_losers(
        registry=registry,
        guard_wire_inputs=guard_wire_inputs,
        mast_nodes=mast_nodes
    )

    loser_by_edge = detection["loser_by_edge"]
    omitted_edges = set(loser_by_edge.keys())

    # -----------------------------------------------------
    # 1) Omitir en el registro solo las crestas perdedoras.
    # -----------------------------------------------------
    omit_log = []
    omitted_crests = []

    for edge in sorted(omitted_edges):
        item = registry.get(edge, None)

        if item is None:
            omit_log.append({
                "edge": edge,
                "status": "skip_edge_not_in_registry"
            })
            continue

        old_source = item.get("source", "")
        old_kind = item.get("kind", "")

        ok = f13d_force_omit_registry_edge(
            registry=registry,
            edge=edge,
            source=FILTER13D_SOURCE_NAME,
            info={
                "case_type": FILTER13D_SOURCE_NAME,
                "omit": True,
                "edge": edge,
                "old_source": old_source,
                "old_kind": old_kind,
                "events": loser_by_edge.get(edge, []),
                "omit_reason": (
                    "La cresta fue omitida por el Filtro 13D porque su proyección "
                    "XY se corta con otra cresta/cable de mayor zmin. "
                    "Se conserva la curva con mayor zmin."
                )
            },
            log=omit_log
        )

        if ok:
            omitted_crests.append({
                "edge": edge,
                "old_source": old_source,
                "new_source": FILTER13D_SOURCE_NAME,
                "events": loser_by_edge.get(edge, [])
            })

    # -----------------------------------------------------
    # 2) Eliminar superficies que usen una cresta omitida.
    #
    #    No se hace cascada.
    #    No se omiten otras aristas de esas superficies.
    # -----------------------------------------------------
    removed_triangle_indices = set()
    removed_triangle_records = []

    for idx, tri in enumerate(triangles):
        tri_type = f13d_triangle_type(tri)
        tri_edges = f13d_triangle_mast_edge_keys(tri)

        affected_edges = [
            e for e in tri_edges
            if e in omitted_edges
        ]

        if len(affected_edges) == 0:
            continue

        remove_this = False

        if tri_type == "M-M-M":
            remove_this = True

        elif tri_type == "M-M-Q" and FILTER13D_REMOVE_MMQ_WITH_OMITTED_CREST:
            remove_this = True

        if not remove_this:
            continue

        removed_triangle_indices.add(idx)

        removed_triangle_records.append({
            "triangle_index": idx,
            "triangle": f13d_triangle_label_string(tri),
            "triangle_type": tri_type,
            "affected_edges": affected_edges,
            "tri": tri
        })

    kept_triangles = []

    for idx, tri in enumerate(triangles):
        if idx in removed_triangle_indices:
            continue

        kept_triangles.append(tri)

    filtered_tri_nodes = f13d_filter_tri_nodes_used_by_triangles(
        tri_nodes=tri_nodes,
        triangles=kept_triangles
    )

    # -----------------------------------------------------
    # 3) Actualizar metadatos.
    # -----------------------------------------------------
    if "unique_mast_edges_from_triangles" in globals():
        out["mm_edges"] = unique_mast_edges_from_triangles(kept_triangles)

    if "unique_mast_q_edges_from_triangles" in globals():
        out["mq_edges"] = unique_mast_q_edges_from_triangles(kept_triangles)

    if "build_common_tetra_edges_from_triangles" in globals():
        out["common_tetra_edges"] = build_common_tetra_edges_from_triangles(kept_triangles)

    out["crest_registry"] = registry

    out["filter13D_records"] = detection["records"]
    out["filter13D_loser_by_edge"] = loser_by_edge
    out["filter13D_pair_events"] = detection["pair_events"]
    out["filter13D_tie_events"] = detection["tie_events"]
    out["filter13D_protected_loser_events"] = detection["protected_loser_events"]

    out["filter13D_omitted_edges"] = omitted_edges
    out["filter13D_omitted_crests"] = omitted_crests
    out["filter13D_removed_triangles"] = removed_triangle_records
    out["filter13D_removed_triangle_indices"] = removed_triangle_indices
    out["filter13D_omit_log"] = omit_log

    return out, kept_triangles, filtered_tri_nodes


def local_registry_color_and_width(item):
    """
    Usa registry_color_and_width si ya existe desde 13A/13B.
    Si no existe, usa esta versión local de respaldo.
    """
    if "registry_color_and_width" in globals():
        return registry_color_and_width(item)

    source = item.get("source", "")
    kind = item.get("kind", "")

    if source == "direct_guard_wire":
        return "green", 9

    if source == "four_guard_closed":
        return "dodgerblue", 12

    if source == "three_guard_chain":
        return "deepskyblue", 11

    if source == "shared_guard_plus_k":
        return "cyan", 10

    if source == "independent_guard_lines":
        return "purple", 9

    if source == "removed_guard_wire_crossing":
        return "black", 5

    if "larga" in kind or "suelo" in kind or "L>2S" in kind:
        return "red", 7

    return "orange", 7


def add_crest_registry_to_existing_fig(
    fig,
    crest_registry,
    show_mm_crests=True
):
    """
    Dibuja las fronteras M-M desde el registro final.

    El registro ya contiene:
      - cables directos;
      - crestas base;
      - crestas reemplazadas por guardas independientes;
      - crestas por mástil común + K;
      - crestas por tres guardas consecutivas;
      - crestas por cuadrilátero cerrado;
      - crestas omitidas por filtros posteriores.
    """
    if not show_mm_crests:
        return fig

    if crest_registry is None:
        print("Advertencia: crest_registry es None. No se dibujaron crestas M-M.")
        return fig

    for key, item in crest_registry.items():

        # Importante después de 13C:
        # si la cresta quedó omitida, no debe dibujarse.
        if item.get("omit", False):
            continue

        C = item.get("curve", None)

        if C is None:
            continue

        color, width = local_registry_color_and_width(item)

        fig.add_trace(go.Scatter3d(
            x=C[:, 0],
            y=C[:, 1],
            z=C[:, 2],
            mode="lines",
            line=dict(width=width, color=color),
            name=f"{item.get('kind', 'Frontera M-M')} {key[0]}-{key[1]}"
        ))

    return fig


def add_special_auxiliaries_if_available(
    fig,
    registry_result,
    sphere_radius
):
    """
    Si existe add_special_auxiliary_graphics desde la celda 13B,
    lo usa para dibujar:
      - líneas imaginarias;
      - esferas especiales;
      - contactos;
      - radios;
      - proyecciones XY.

    Si no existe, simplemente no agrega esos auxiliares.
    """
    if registry_result is None:
        return fig

    if "add_special_auxiliary_graphics" in globals():
        add_special_auxiliary_graphics(
            fig=fig,
            final_result=registry_result,
            sphere_radius=sphere_radius
        )

    return fig


def add_triangles_crests_and_mq_to_existing_fig(
    fig,
    tri_nodes,
    triangles,
    sphere_radius,
    guard_wire_inputs=None,
    registry_result=None,
    show_mmm_borders=True,
    show_mm_crests=True,
    show_mq_segments=True,
    show_q_points=True,
    show_special_auxiliaries=True
):
    # -----------------------------------------------------
    # 1) Bordes de triángulos M-M-M
    # -----------------------------------------------------
    if show_mmm_borders:
        for k, tri in enumerate(triangles):
            if classify_triangle_type(tri) != "M-M-M":
                continue

            n1, n2, n3 = tri["nodes"]

            fig.add_trace(go.Scatter3d(
                x=[n1["x"], n2["x"], n3["x"], n1["x"]],
                y=[n1["y"], n2["y"], n3["y"], n1["y"]],
                z=[n1["z"], n2["z"], n3["z"], n1["z"]],
                mode="lines",
                line=dict(width=4, color="rgba(80,80,80,0.50)"),
                name=f"Borde M-M-M {k}"
            ))

    # -----------------------------------------------------
    # 2) Crestas M-M / cables / crestas especiales
    #    DESDE REGISTRO FINAL 13B/13C
    # -----------------------------------------------------
    if show_mm_crests:
        if registry_result is not None:
            crest_registry = registry_result["crest_registry"]

            fig = add_crest_registry_to_existing_fig(
                fig=fig,
                crest_registry=crest_registry,
                show_mm_crests=True
            )

            if show_special_auxiliaries:
                fig = add_special_auxiliaries_if_available(
                    fig=fig,
                    registry_result=registry_result,
                    sphere_radius=sphere_radius
                )

        else:
            print(
                "Advertencia: no se recibió registry_result. "
                "No se dibujaron crestas M-M para evitar recalcular "
                "crestas antiguas fuera del registro final."
            )

    # -----------------------------------------------------
    # 3) Segmentos M-Q conservados
    # -----------------------------------------------------
    if show_mq_segments:
        if registry_result is not None and "mq_edges" in registry_result:
            mq_edges = registry_result["mq_edges"]
        else:
            mq_edges = unique_mast_q_edges_from_triangles(triangles)

        for key, (m_node, q_node) in mq_edges.items():
            fig.add_trace(go.Scatter3d(
                x=[m_node["x"], q_node["x"]],
                y=[m_node["y"], q_node["y"]],
                z=[m_node["z"], q_node["z"]],
                mode="lines",
                line=dict(width=5, dash="dash", color="red"),
                name=f"Segmento {key[0]}-{key[1]}"
            ))

    # -----------------------------------------------------
    # 4) Puntos Q
    # -----------------------------------------------------
    if show_q_points:
        q_nodes = [n for n in tri_nodes if n["type"] == "Q"]

        if q_nodes:
            fig.add_trace(go.Scatter3d(
                x=[n["x"] for n in q_nodes],
                y=[n["y"] for n in q_nodes],
                z=[n["z"] for n in q_nodes],
                mode="markers+text",
                marker=dict(size=6, color="orange"),
                text=[n["label"] for n in q_nodes],
                textposition="top center",
                name="Puntos Q"
            ))

    return fig


def plot_single_mast_surfaces_with_crests_and_mq(
    masts,
    sphere_radius,
    results,
    tri_nodes,
    triangles,
    guard_wire_inputs=None,
    registry_result=None
):
    fig = go.Figure()

    # -----------------------------------------------------
    # 1) Superficies de mástil solo
    # -----------------------------------------------------
    for i, mast in enumerate(masts):
        add_mast_to_figure(
            fig=fig,
            mast=mast,
            idx=i,
            sphere_radius=sphere_radius,
            results=results,
            show_mast_line=True,
            show_base_circle=True
        )

    # -----------------------------------------------------
    # 2) Segmentos rojos sobre la capa de mástil solo
    # -----------------------------------------------------
    dibujar_aristas_Q(
        fig=fig,
        masts=masts,
        results=results,
        S=sphere_radius,
        n_pts=200
    )

    # -----------------------------------------------------
    # 3) Agregar crestas/cables/crestas especiales desde 13B/13C,
    #    M-Q y bordes M-M-M
    # -----------------------------------------------------
    fig = add_triangles_crests_and_mq_to_existing_fig(
        fig=fig,
        tri_nodes=tri_nodes,
        triangles=triangles,
        sphere_radius=sphere_radius,
        guard_wire_inputs=guard_wire_inputs,
        registry_result=registry_result,
        show_mmm_borders=True,
        show_mm_crests=True,
        show_mq_segments=True,
        show_q_points=True,
        show_special_auxiliaries=True
    )

    # -----------------------------------------------------
    # 4) Plano base z = 0
    # -----------------------------------------------------
    all_x = [m.x for m in masts]
    all_y = [m.y for m in masts]
    max_a = max(effective_radius(m.h, sphere_radius) for m in masts)

    xmin = min(all_x) - max_a - 5
    xmax = max(all_x) + max_a + 5
    ymin = min(all_y) - max_a - 5
    ymax = max(all_y) + max_a + 5

    Xg, Yg = np.meshgrid(
        np.linspace(xmin, xmax, 2),
        np.linspace(ymin, ymax, 2)
    )
    Zg = np.zeros_like(Xg)

    fig.add_trace(go.Surface(
        x=Xg,
        y=Yg,
        z=Zg,
        showscale=False,
        opacity=0.15,
        name="Plano z=0",
        hoverinfo="skip"
    ))

    fig.update_layout(
        title="Superficies de mástil solo + crestas finales 13C + segmentos M-Q",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="data"
        ),
        height=900,
        showlegend=True
    )

    fig.show()

    return fig


import numpy as np


import plotly.graph_objects as go


from plotly.subplots import make_subplots


from matplotlib.path import Path


def local_edge_key(a, b):
    return tuple(sorted([a, b]))


def local_node_point(n):
    return np.array([n["x"], n["y"], n["z"]], dtype=float)


def local_curve_to_array(curve):
    """
    Convierte una curva a matriz Nx3.
    Acepta:
      - tupla (x, y, z);
      - array Nx3.
    """
    if curve is None:
        return None

    if isinstance(curve, tuple) and len(curve) == 3:
        x, y, z = curve
        C = np.column_stack([x, y, z]).astype(float)
    else:
        C = np.asarray(curve, dtype=float)

    if C.ndim != 2 or C.shape[1] != 3:
        return None

    C[:, 2] = np.maximum(C[:, 2], 0.0)
    return C


def local_resample_curve_xyz(curve_xyz, npts=120):
    """
    Remuestrea curva Nx3 por longitud de arco.
    """
    C = np.asarray(curve_xyz, dtype=float)

    if len(C) < 2:
        return np.repeat(C[:1], npts, axis=0)

    d = np.linalg.norm(np.diff(C, axis=0), axis=1)
    s_old = np.concatenate([[0.0], np.cumsum(d)])

    if s_old[-1] < 1e-12:
        return np.repeat(C[:1], npts, axis=0)

    s_old = s_old / s_old[-1]
    s_new = np.linspace(0.0, 1.0, npts)

    x = np.interp(s_new, s_old, C[:, 0])
    y = np.interp(s_new, s_old, C[:, 1])
    z = np.interp(s_new, s_old, C[:, 2])

    out = np.column_stack([x, y, z])
    out[:, 2] = np.maximum(out[:, 2], 0.0)

    return out


def local_orient_curve_xyz(curve_xyz, start_node, end_node):
    """
    Orienta la curva para que vaya de start_node a end_node.
    """
    C = np.asarray(curve_xyz, dtype=float)

    p_start = local_node_point(start_node)
    p_end = local_node_point(end_node)

    d_normal = (
        np.linalg.norm(C[0] - p_start)
        + np.linalg.norm(C[-1] - p_end)
    )

    d_flip = (
        np.linalg.norm(C[-1] - p_start)
        + np.linalg.norm(C[0] - p_end)
    )

    if d_flip < d_normal:
        C = C[::-1].copy()

    C[:, 2] = np.maximum(C[:, 2], 0.0)

    return C


def get_crest_registry_from_result(registry_result):
    """
    Obtiene crest_registry desde el resultado de crestas activo:
    13C, filtro 3, filtro 2, filtro 1 o 13B.
    """
    if registry_result is None:
        return None

    if isinstance(registry_result, dict) and "crest_registry" in registry_result:
        return registry_result["crest_registry"]

    return None


def get_registry_item_for_edge(registry_result, label1, label2):
    """
    Obtiene la frontera M-M desde el registro de crestas activo.
    """
    registry = get_crest_registry_from_result(registry_result)

    if registry is None:
        return None

    key = local_edge_key(label1, label2)
    return registry.get(key, None)


def get_top_boundary_from_registry(
    m1,
    m2,
    registry_result,
    ns=80
):
    """
        Retorna la frontera superior M-M desde el registro final 13C.

    Retorna:
        C, top_name, top_kind, source

    top_name:
        "guard_wire" si source == direct_guard_wire.
        "crest" para cualquier otra frontera:
            - cresta base;
            - cresta por guardas independientes;
            - cresta por mástil común + K;
            - cresta por tres guardas;
            - cresta por cuadrilátero cerrado.
    """
    item = get_registry_item_for_edge(
        registry_result=registry_result,
        label1=m1["label"],
        label2=m2["label"]
    )

    if item is None:
        return None, None, None, None

    # Corrección para 13C:
    # si la frontera fue omitida por cualquiera de los filtros,
    # no debe usarse para construir MMQ.
    if item.get("omit", False):
        return None, None, None, None

    C = local_curve_to_array(item.get("curve", None))

    if C is None:
        return None, None, None, None


    C = local_resample_curve_xyz(C, npts=ns)
    C = local_orient_curve_xyz(C, m1, m2)

    source = item.get("source", "")
    top_kind = item.get("kind", "Frontera M-M")

    if source == "direct_guard_wire":
        top_name = "guard_wire"
    else:
        top_name = "crest"

    return C, top_name, top_kind, source


def curve_mast_to_q_on_single_mast_surface(
    m_node,
    q_node,
    sphere_radius,
    npts=120
):
    xm, ym, hm = m_node["x"], m_node["y"], m_node["z"]
    xq, yq = q_node["x"], q_node["y"]

    dx = xq - xm
    dy = yq - ym
    a = np.hypot(dx, dy)

    if a < 1e-12:
        return None

    theta = np.arctan2(dy, dx)
    r = np.linspace(0.0, a, npts)

    x = xm + r * np.cos(theta)
    y = ym + r * np.sin(theta)

    inside = sphere_radius**2 - (r - a)**2
    inside = np.maximum(inside, 0.0)

    z = sphere_radius - np.sqrt(inside)
    z = np.maximum(z, 0.0)

    if len(z) > 1:
        z[:-1] = np.maximum(z[:-1], 1e-8)
        z[-1] = 0.0

    return x, y, z


def build_mmq_guard_patch(C, L, R, q_point, ns, nt, z_eps=1e-8):
    """
    Caso con cable de guarda directo:
    usa Coons triangular porque el borde superior es recto.
    """
    X = np.zeros((nt, ns))
    Y = np.zeros((nt, ns))
    Z = np.zeros((nt, ns))

    C0 = C[0].copy()
    C1 = C[-1].copy()

    for it in range(nt):
        t = it / (nt - 1)

        Lt = L[it]
        Rt = R[it]

        for is_ in range(ns):
            s = is_ / (ns - 1)

            Cs = C[is_]

            top_to_q = (1.0 - t) * Cs + t * q_point
            side_blend = (1.0 - s) * Lt + s * Rt

            corner_blend = (
                (1.0 - s) * ((1.0 - t) * C0 + t * q_point)
                + s * ((1.0 - t) * C1 + t * q_point)
            )

            P = top_to_q + side_blend - corner_blend

            if it == 0:
                P = Cs.copy()
            elif is_ == 0:
                P = Lt.copy()
            elif is_ == ns - 1:
                P = Rt.copy()
            elif it == nt - 1:
                P = q_point.copy()

            if it < nt - 1:
                P[2] = max(P[2], z_eps)
            else:
                P[2] = 0.0

            P[2] = max(P[2], 0.0)

            X[it, is_] = P[0]
            Y[it, is_] = P[1]
            Z[it, is_] = P[2]

    return X, Y, Z


def build_mmq_crest_patch_from_scratch(C, L, R, q_point, ns, nt, z_eps=1e-8):
    """
    Caso con cresta:
    superficie reconstruida desde cero.

    Usa cualquier cresta que venga del registro final 13C:
      - cresta base;
      - cresta por líneas imaginarias;
      - cresta por mástil común + K;
      - cresta por tres guardas;
      - cresta por cuadrilátero cerrado.

    Mantiene:
      - recorte superior solo en Z contra la cresta;
      - fronteras exactas;
      - Z >= 0.
    """
    X = np.zeros((nt, ns))
    Y = np.zeros((nt, ns))
    Z = np.zeros((nt, ns))

    for is_ in range(ns):
        s = is_ / (ns - 1)

        Cs = C[is_].copy()

        # -------------------------------------------------
        # Curva radial desde la cresta hacia Q
        # -------------------------------------------------
        ctrl = np.zeros(3)
        ctrl[0] = 0.55 * Cs[0] + 0.45 * q_point[0]
        ctrl[1] = 0.55 * Cs[1] + 0.45 * q_point[1]
        ctrl[2] = 0.18 * Cs[2]

        for it in range(nt):
            t = it / (nt - 1)

            P_radial = (
                (1.0 - t)**2 * Cs
                + 2.0 * (1.0 - t) * t * ctrl
                + t**2 * q_point
            )

            P_side = (1.0 - s) * L[it] + s * R[it]

            # Peso lateral:
            # 1 en los lados, 0 en el centro.
            dist_to_side = min(s, 1.0 - s)
            w_side = max(0.0, 1.0 - 2.0 * dist_to_side)
            w_side = w_side**2.2

            P = (1.0 - w_side) * P_radial + w_side * P_side

            # -------------------------------------------------
            # Recorte superior SOLO EN Z contra la cresta.
            # Actúa con más fuerza solo cerca de la cresta.
            # -------------------------------------------------
            crest_clip_power = 1.45
            crest_clip_band = 0.35

            z_limit_linear = (1.0 - t) * Cs[2]
            z_limit_strong = ((1.0 - t) ** crest_clip_power) * Cs[2]

            if t <= crest_clip_band:
                u = t / crest_clip_band
                w = (1.0 - u) ** 2
                z_limit_crest = (1.0 - w) * z_limit_linear + w * z_limit_strong
            else:
                z_limit_crest = z_limit_linear

            P[2] = min(P[2], z_limit_crest)

            # -------------------------------------------------
            # Fronteras exactas.
            # -------------------------------------------------
            if it == 0:
                P = Cs.copy()
            elif is_ == 0:
                P = L[it].copy()
            elif is_ == ns - 1:
                P = R[it].copy()
            elif it == nt - 1:
                P = q_point.copy()

            # -------------------------------------------------
            # Solo Q toca suelo.
            # -------------------------------------------------
            if it < nt - 1:
                P[2] = max(P[2], z_eps)
            else:
                P[2] = 0.0

            P[2] = max(P[2], 0.0)

            X[it, is_] = P[0]
            Y[it, is_] = P[1]
            Z[it, is_] = P[2]

    return X, Y, Z


def mask_mmq_patch_to_boundary_xy(
    X,
    Y,
    Z,
    C,
    L,
    R,
    radius=1e-9,
    keep_boundaries=True,
    verbose=False
):
    """
    Recorta/enmascara el parche MMQ en XY usando el contorno válido:

        C + R + L invertida

    No deforma la superficie.
    No mueve X/Y.
    Solo oculta con NaN los puntos fuera del dominio.

    Contorno:
      - C       : frontera superior M-M
      - R       : curva M2-Q
      - L[::-1] : curva Q-M1
    """
    X = np.asarray(X, dtype=float).copy()
    Y = np.asarray(Y, dtype=float).copy()
    Z = np.asarray(Z, dtype=float).copy()

    C = np.asarray(C, dtype=float)
    L = np.asarray(L, dtype=float)
    R = np.asarray(R, dtype=float)

    poly = np.vstack([
        C[:, :2],
        R[:, :2],
        L[::-1, :2]
    ])

    # Eliminar puntos no finitos del polígono
    mask_poly = np.isfinite(poly[:, 0]) & np.isfinite(poly[:, 1])
    poly = poly[mask_poly]

    if len(poly) < 3:
        return X, Y, Z

    path = Path(poly)

    pts = np.column_stack([
        X.ravel(),
        Y.ravel()
    ])

    finite_pts = (
        np.isfinite(pts[:, 0])
        & np.isfinite(pts[:, 1])
    )

    inside_flat = np.zeros(pts.shape[0], dtype=bool)

    inside_flat[finite_pts] = path.contains_points(
        pts[finite_pts],
        radius=radius
    )

    inside = inside_flat.reshape(X.shape)

    # Mantener fronteras exactas aunque Path las marque como fuera.
    if keep_boundaries:
        inside[0, :] = True       # cresta C
        inside[:, 0] = True       # lado L
        inside[:, -1] = True      # lado R
        inside[-1, :] = True      # Q

    removed = np.count_nonzero(~inside)

    X[~inside] = np.nan
    Y[~inside] = np.nan
    Z[~inside] = np.nan

    if verbose:
        total = inside.size
        print("========== MÁSCARA XY MMQ ==========")
        print(f"Puntos totales        : {total}")
        print(f"Puntos conservados    : {np.count_nonzero(inside)}")
        print(f"Puntos enmascarados   : {removed}")

    return X, Y, Z


def build_mmq_patch_from_boundaries(
    m1,
    m2,
    q,
    sphere_radius,
    guard_wire_inputs=None,
    registry_result=None,
    ns=80,
    nt=80,
    flatten_power=3.5,
    z_eps=1e-8,
    apply_xy_mask=True,
    xy_mask_radius=1e-9,
    xy_mask_verbose=False
):
    """
    Construye parche M-M-Q usando la frontera superior del registro final 13C.

    IMPORTANTE:
    - No recalcula circle_crest_between_two_masts.
    - No decide el cable con edge_has_guard_wire.
    - Toma la frontera superior desde el registro de crestas activo."].

    Recorte:
    - El recorte en Z se aplica dentro de build_mmq_crest_patch_from_scratch.
    - El recorte en XY se aplica como máscara, sin mover puntos.
    """

    C, top_name, top_kind, source = get_top_boundary_from_registry(
        m1=m1,
        m2=m2,
        registry_result=registry_result,
        ns=ns
    )

    if C is None:
        print(
            f"No existe frontera M-M en crest_registry_final para "
            f"{m1['label']}-{m2['label']}"
        )
        return None

    c1 = curve_mast_to_q_on_single_mast_surface(
        m_node=m1,
        q_node=q,
        sphere_radius=sphere_radius,
        npts=nt
    )

    c2 = curve_mast_to_q_on_single_mast_surface(
        m_node=m2,
        q_node=q,
        sphere_radius=sphere_radius,
        npts=nt
    )

    if c1 is None or c2 is None:
        return None

    L = np.vstack(c1).T
    R = np.vstack(c2).T

    C[:, 2] = np.maximum(C[:, 2], 0.0)
    L[:, 2] = np.maximum(L[:, 2], 0.0)
    R[:, 2] = np.maximum(R[:, 2], 0.0)

    L[:-1, 2] = np.maximum(L[:-1, 2], z_eps)
    R[:-1, 2] = np.maximum(R[:-1, 2], z_eps)
    L[-1, 2] = 0.0
    R[-1, 2] = 0.0

    q_point = np.array([q["x"], q["y"], 0.0], dtype=float)

    if top_name == "guard_wire":
        X, Y, Z = build_mmq_guard_patch(
            C=C,
            L=L,
            R=R,
            q_point=q_point,
            ns=ns,
            nt=nt,
            z_eps=z_eps
        )
    else:
        X, Y, Z = build_mmq_crest_patch_from_scratch(
            C=C,
            L=L,
            R=R,
            q_point=q_point,
            ns=ns,
            nt=nt,
            z_eps=z_eps
        )

    # -----------------------------------------------------
    # Recorte / máscara del dominio XY.
    #
    # Se aplica solo si apply_xy_mask=True.
    # No mueve puntos: solo oculta los que caen fuera del
    # contorno válido C + R + L[::-1].
    # -----------------------------------------------------
    if apply_xy_mask:
        X, Y, Z = mask_mmq_patch_to_boundary_xy(
            X=X,
            Y=Y,
            Z=Z,
            C=C,
            L=L,
            R=R,
            radius=xy_mask_radius,
            keep_boundaries=True,
            verbose=xy_mask_verbose
        )

    return X, Y, Z, C, L, R, top_name, top_kind, source


def get_mmq_info(tri):
    mast_nodes = [n for n in tri["nodes"] if n["type"] == "mast_top"]
    q_nodes = [n for n in tri["nodes"] if n["type"] == "Q"]

    if len(mast_nodes) != 2 or len(q_nodes) != 1:
        return None

    return mast_nodes[0], mast_nodes[1], q_nodes[0]


def get_top_type_from_registry(m1, m2, registry_result):
    item = get_registry_item_for_edge(
        registry_result=registry_result,
        label1=m1["label"],
        label2=m2["label"]
    )

    if item is None:
        return None, None, None

    # Corrección para 13C:
    # si la frontera fue omitida, no debe usarse para construir MMQ.
    if item.get("omit", False):
        return None, None, None

    if item.get("curve", None) is None:
        return None, None, None

    source = item.get("source", "")
    kind = item.get("kind", "")

    if source == "direct_guard_wire":
        return "guard_wire", kind, source

    return "crest", kind, source


def find_mmq_triangle_by_top_type(
    triangles,
    registry_result,
    desired_top_type="crest",
    desired_source=None
):
    """
    Busca un triángulo M-M-Q según la frontera superior registrada.

    desired_top_type:
      - "guard_wire": source == direct_guard_wire.
      - "crest": cualquier otra frontera M-M.

    desired_source opcional:
      - "independent_guard_lines";
      - "shared_guard_plus_k";
      - "three_guard_chain";
      - "four_guard_closed";
      - "base_normal_L_le_2S";
      - "base_long_L_gt_2S".
    """
    for idx, tri in enumerate(triangles):
        if classify_triangle_type(tri) != "M-M-Q":
            continue

        info = get_mmq_info(tri)

        if info is None:
            continue

        m1, m2, q = info

        top_type, kind, source = get_top_type_from_registry(
            m1=m1,
            m2=m2,
            registry_result=registry_result
        )

        if top_type is None:
            continue

        if desired_top_type is not None and top_type != desired_top_type:
            continue

        if desired_source is not None and source != desired_source:
            continue

        return idx, tri

    return None, None


def add_mmq_case_to_subplot(
    fig,
    tri,
    row,
    col,
    sphere_radius,
    registry_result=None,
    ns=90,
    nt=90,
    flatten_power=3.5,
    show_internal_mesh=True,
    apply_xy_mask=True,
    xy_mask_radius=1e-9,
    xy_mask_verbose=False
):
    info = get_mmq_info(tri)

    if info is None:
        return False

    m1, m2, q = info

    patch = build_mmq_patch_from_boundaries(
        m1=m1,
        m2=m2,
        q=q,
        sphere_radius=sphere_radius,
        registry_result=registry_result,
        ns=ns,
        nt=nt,
        flatten_power=flatten_power,
        apply_xy_mask=apply_xy_mask,
        xy_mask_radius=xy_mask_radius,
        xy_mask_verbose=xy_mask_verbose
    )

    if patch is None:
        return False

    X, Y, Z, C, L, R, top_name, top_kind, source = patch

    if top_name == "guard_wire":
        label_top = "Cable de guarda"
    else:
        label_top = top_kind

    fig.add_trace(
        go.Surface(
            x=X,
            y=Y,
            z=Z,
            opacity=0.75,
            showscale=False,
            name=f"MMQ con {label_top}: {m1['label']}-{m2['label']}-{q['label']}"
        ),
        row=row,
        col=col
    )

    fig.add_trace(
        go.Scatter3d(
            x=C[:, 0],
            y=C[:, 1],
            z=C[:, 2],
            mode="lines",
            line=dict(width=9),
            name=f"{label_top} {m1['label']}-{m2['label']}"
        ),
        row=row,
        col=col
    )

    fig.add_trace(
        go.Scatter3d(
            x=L[:, 0],
            y=L[:, 1],
            z=L[:, 2],
            mode="lines",
            line=dict(width=6),
            name=f"Curva {m1['label']}-{q['label']}"
        ),
        row=row,
        col=col
    )

    fig.add_trace(
        go.Scatter3d(
            x=R[:, 0],
            y=R[:, 1],
            z=R[:, 2],
            mode="lines",
            line=dict(width=6),
            name=f"Curva {m2['label']}-{q['label']}"
        ),
        row=row,
        col=col
    )

    if show_internal_mesh:
        for r in np.linspace(0, X.shape[0] - 1, 8, dtype=int):
            fig.add_trace(
                go.Scatter3d(
                    x=X[r, :],
                    y=Y[r, :],
                    z=Z[r, :],
                    mode="lines",
                    line=dict(width=2),
                    showlegend=False
                ),
                row=row,
                col=col
            )

        for c in np.linspace(0, X.shape[1] - 1, 8, dtype=int):
            fig.add_trace(
                go.Scatter3d(
                    x=X[:, c],
                    y=Y[:, c],
                    z=Z[:, c],
                    mode="lines",
                    line=dict(width=2),
                    showlegend=False
                ),
                row=row,
                col=col
            )

    for m in [m1, m2]:
        fig.add_trace(
            go.Scatter3d(
                x=[m["x"], m["x"]],
                y=[m["y"], m["y"]],
                z=[0.0, m["z"]],
                mode="lines+markers+text",
                line=dict(width=8),
                marker=dict(size=5),
                text=["", m["label"]],
                textposition="top center",
                name=m["label"]
            ),
            row=row,
            col=col
        )

    fig.add_trace(
        go.Scatter3d(
            x=[q["x"]],
            y=[q["y"]],
            z=[0.0],
            mode="markers+text",
            marker=dict(size=7),
            text=[q["label"]],
            textposition="top center",
            name=q["label"]
        ),
        row=row,
        col=col
    )

    pts_x = [m1["x"], m2["x"], q["x"]]
    pts_y = [m1["y"], m2["y"], q["y"]]

    pad = 8
    xmin, xmax = min(pts_x) - pad, max(pts_x) + pad
    ymin, ymax = min(pts_y) - pad, max(pts_y) + pad

    Xg, Yg = np.meshgrid(
        np.linspace(xmin, xmax, 2),
        np.linspace(ymin, ymax, 2)
    )

    fig.add_trace(
        go.Surface(
            x=Xg,
            y=Yg,
            z=np.zeros_like(Xg),
            opacity=0.12,
            showscale=False,
            hoverinfo="skip",
            name="Plano z=0"
        ),
        row=row,
        col=col
    )

    return True


def plot_mmq_guard_vs_crest_prototype(
    triangles,
    sphere_radius,
    registry_result=None,
    flatten_power=3.5,
    show_internal_mesh=True,
    apply_xy_mask=True,
    xy_mask_radius=1e-9,
    xy_mask_verbose=False
):
    """
    Prototipo comparativo MMQ conectado con el registro final 13C.

    Compara:
      - un MMQ cuyo borde superior sea cable directo;
      - un MMQ cuyo borde superior sea cualquier cresta registrada.
    """
    if registry_result is None:
        raise ValueError(
            "Debes pasar registry_result=resultado_crestas_final_13C "
            "para usar las fronteras M-M filtradas."
        )

    idx_guard, tri_guard = find_mmq_triangle_by_top_type(
        triangles=triangles,
        registry_result=registry_result,
        desired_top_type="guard_wire"
    )

    idx_crest, tri_crest = find_mmq_triangle_by_top_type(
        triangles=triangles,
        registry_result=registry_result,
        desired_top_type="crest"
    )

    cases = []

    if tri_guard is not None:
        cases.append(("MMQ con cable de guarda directo", idx_guard, tri_guard))

    if tri_crest is not None:
        cases.append(("MMQ con frontera tipo cresta registrada", idx_crest, tri_crest))

    if len(cases) == 0:
        raise ValueError(
            "No se encontró ningún M-M-Q con cable de guarda ni con cresta registrada."
        )

    cols = len(cases)

    fig = make_subplots(
        rows=1,
        cols=cols,
        specs=[[{"type": "scene"} for _ in range(cols)]],
        subplot_titles=[
            f"{title} | índice {idx}"
            for title, idx, tri in cases
        ]
    )

    for col, (title, idx, tri) in enumerate(cases, start=1):
        ok = add_mmq_case_to_subplot(
            fig=fig,
            tri=tri,
            row=1,
            col=col,
            sphere_radius=sphere_radius,
            registry_result=registry_result,
            ns=90,
            nt=90,
            flatten_power=flatten_power,
            show_internal_mesh=show_internal_mesh,
            apply_xy_mask=apply_xy_mask,
            xy_mask_radius=xy_mask_radius,
            xy_mask_verbose=xy_mask_verbose
        )

        if not ok:
            print(f"No se pudo construir el caso: {title} | índice {idx}")

    fig.update_layout(
        title="Comparación prototipo M-M-Q usando fronteras finales de 13C",
        height=900,
        showlegend=True
    )

    for i in range(1, cols + 1):
        scene_name = "scene" if i == 1 else f"scene{i}"
        fig.layout[scene_name].update(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="data"
        )

    print("Caso con cable de guarda:", "encontrado" if tri_guard is not None else "NO encontrado")
    print("Índice MMQ con guarda:", idx_guard)

    print("Caso con cresta registrada:", "encontrado" if tri_crest is not None else "NO encontrado")
    print("Índice MMQ con cresta:", idx_crest)
    print("Máscara XY aplicada:", apply_xy_mask)

    fig.show()


RUN_MMQ_PROTOTYPE_DIAGNOSTIC = False


def add_all_mmq_patches_to_fig(
    fig,
    triangles,
    sphere_radius,
    guard_wire_inputs=None,
    registry_result=None,
    ns=70,
    nt=70,
    opacity=0.72,
    flatten_power=3.5
):
    """
    Recorre todos los triángulos conservados y rellena los M-M-Q usando
    la frontera superior M-M tomada desde el registro final activo 13C.

    La frontera superior puede ser:
      - cable de guarda directo;
      - cresta base normal;
      - cresta base larga;
      - cresta especial por dos guardas independientes;
      - cresta especial por dos guardas con mástil común + K;
      - cresta especial por tres guardas consecutivas;
      - cresta especial por cuadrilátero cerrado.
    """

    count_ok = 0
    count_fail = 0

    for k, tri in enumerate(triangles):
        if classify_triangle_type(tri) != "M-M-Q":
            continue

        mast_nodes = [n for n in tri["nodes"] if n["type"] == "mast_top"]
        q_nodes = [n for n in tri["nodes"] if n["type"] == "Q"]

        if len(mast_nodes) != 2 or len(q_nodes) != 1:
            count_fail += 1
            continue

        m1, m2 = mast_nodes
        q = q_nodes[0]

        patch = build_mmq_patch_from_boundaries(
            m1=m1,
            m2=m2,
            q=q,
            sphere_radius=sphere_radius,
            guard_wire_inputs=guard_wire_inputs,
            registry_result=registry_result,
            ns=ns,
            nt=nt,
            flatten_power=flatten_power
        )

        if patch is None:
            count_fail += 1
            continue

        # Celda 16 conectada retorna:
        # X, Y, Z, C, L, R, top_name, top_kind, source
        X, Y, Z, C, L, R, top_name, top_kind, source = patch

        Z = np.maximum(Z, 0.0)

        if top_name == "guard_wire":
            label_top = "Cable"
        else:
            label_top = top_kind

        fig.add_trace(go.Surface(
            x=X,
            y=Y,
            z=Z,
            opacity=opacity,
            showscale=False,
            name=f"Relleno MMQ {label_top} {m1['label']}-{m2['label']}-{q['label']}",
            hovertemplate=(
                f"MMQ {m1['label']}-{m2['label']}-{q['label']}<br>"
                f"Borde superior: {label_top}<br>"
                f"source={source}<br>"
                f"flatten_power={flatten_power}<br>"
                "x=%{x:.2f}<br>"
                "y=%{y:.2f}<br>"
                "z=%{z:.2f}<extra></extra>"
            )
        ))

        count_ok += 1

    print(f"Parches MMQ generados correctamente : {count_ok}")
    print(f"Parches MMQ omitidos/no aplicables  : {count_fail}")
    print(f"flatten_power usado en MMQ          : {flatten_power}")

    return fig


def plot_single_mast_surfaces_with_crests_mq_and_mmq_fill(
    masts,
    sphere_radius,
    results,
    tri_nodes,
    triangles,
    guard_wire_inputs=None,
    registry_result=None,
    show_single_mast_surfaces=True,
    show_red_q_edges=True,
    show_mmm_borders=True,
    show_mm_crests=True,
    show_mq_segments=True,
    show_q_points=True,
    show_mmq_fill=True,
    flatten_power=3.5
):
    fig = go.Figure()

    # -----------------------------------------------------
    # 1) Superficies de mástil solo
    # -----------------------------------------------------
    if show_single_mast_surfaces:
        for i, mast in enumerate(masts):
            add_mast_to_figure(
                fig=fig,
                mast=mast,
                idx=i,
                sphere_radius=sphere_radius,
                results=results,
                show_mast_line=True,
                show_base_circle=True
            )

    # -----------------------------------------------------
    # 2) Segmentos rojos sobre la capa de mástil solo
    # -----------------------------------------------------
    if show_red_q_edges:
        dibujar_aristas_Q(
            fig=fig,
            masts=masts,
            results=results,
            S=sphere_radius,
            n_pts=200
        )

    # -----------------------------------------------------
    # 3) Rellenos MMQ usando frontera M-M desde registro final 13C
    # -----------------------------------------------------
    if show_mmq_fill:
        fig = add_all_mmq_patches_to_fig(
            fig=fig,
            triangles=triangles,
            sphere_radius=sphere_radius,
            guard_wire_inputs=guard_wire_inputs,
            registry_result=registry_result,
            ns=UI_MMM_PATCH_N,
            nt=UI_MMM_PATCH_N,
            opacity=0.72,
            flatten_power=flatten_power
        )

    # -----------------------------------------------------
    # 4) Crestas/cables/segmentos desde registro final 13C
    # -----------------------------------------------------
    fig = add_triangles_crests_and_mq_to_existing_fig(
        fig=fig,
        tri_nodes=tri_nodes,
        triangles=triangles,
        sphere_radius=sphere_radius,
        guard_wire_inputs=guard_wire_inputs,
        registry_result=registry_result,
        show_mmm_borders=show_mmm_borders,
        show_mm_crests=show_mm_crests,
        show_mq_segments=show_mq_segments,
        show_q_points=show_q_points,
        show_special_auxiliaries=True
    )

    # -----------------------------------------------------
    # 5) Plano base z = 0
    # -----------------------------------------------------
    all_x = [m.x for m in masts]
    all_y = [m.y for m in masts]
    max_a = max(effective_radius(m.h, sphere_radius) for m in masts)

    xmin = min(all_x) - max_a - 5
    xmax = max(all_x) + max_a + 5
    ymin = min(all_y) - max_a - 5
    ymax = max(all_y) + max_a + 5

    Xg, Yg = np.meshgrid(
        np.linspace(xmin, xmax, 2),
        np.linspace(ymin, ymax, 2)
    )
    Zg = np.zeros_like(Xg)

    fig.add_trace(go.Surface(
        x=Xg,
        y=Yg,
        z=Zg,
        showscale=False,
        opacity=0.15,
        name="Plano z=0",
        hoverinfo="skip"
    ))

    fig.update_layout(
        title=(
            "Superficies de mástil solo + relleno M-M-Q conectado a registro final 13C "
            f"| flatten_power={flatten_power}"
        ),
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="data"
        ),
        height=900,
        showlegend=True
    )

    fig.show()

    return fig


import numpy as np


import plotly.graph_objects as go


MMM_INTERPOLABLE_SOURCES = {
    "base_normal_L_le_2S",
    "base_long_L_gt_2S",
    "direct_guard_wire",
    "independent_guard_lines",
    "shared_guard_plus_k",
    "three_guard_chain",
    "four_guard_closed"
}


INDEPENDENT_GUARD_REORDER_PATTERN = {
    "direct_guard_wire",
    "base_normal_L_le_2S",
    "independent_guard_lines"
}


def is_interpolable_mmm_source(source):
    return source in MMM_INTERPOLABLE_SOURCES


def classify_mmm_sources(source12, source13, source23):
    sources = [source12, source13, source23]

    if all(is_interpolable_mmm_source(src) for src in sources):
        return "INTERPOLABLE_MMM"

    return "UNSUPPORTED_MMM"


def classify_surface_model(source12, source13, source23):
    source_set = {source12, source13, source23}

    if source_set == INDEPENDENT_GUARD_REORDER_PATTERN:
        return "INDEPENDENT_GUARD_REORDER"

    if all(is_interpolable_mmm_source(src) for src in [source12, source13, source23]):
        return "REGISTRY_BOUNDARY_INTERPOLATION"

    return "UNSUPPORTED"


def get_all_mmm_triangles(triangles):
    mmm_list = []

    for tri in triangles:
        if classify_triangle_type(tri) == "M-M-M":
            mmm_list.append(tri)

    return mmm_list


def find_one_mmm_triangle(triangles, index=0):
    mmm_list = get_all_mmm_triangles(triangles)

    if len(mmm_list) == 0:
        raise ValueError("No se encontró ningún triángulo M-M-M.")

    if index >= len(mmm_list):
        raise ValueError(f"Solo hay {len(mmm_list)} triángulos M-M-M.")

    return mmm_list[index]


def find_mmm_index_by_mast_labels(triangles, labels):
    target = set(labels)
    mmm_list = get_all_mmm_triangles(triangles)

    for idx, tri in enumerate(mmm_list):
        mast_nodes = [
            node for node in tri["nodes"]
            if node["type"] == "mast_top"
        ]

        tri_labels = {m["label"] for m in mast_nodes}

        if tri_labels == target:
            return idx

    raise ValueError(f"No se encontró un MMM con mástiles {labels}.")


def local_edge_key(a, b):
    return tuple(sorted([a, b]))


def local_node_point(n):
    return np.array([n["x"], n["y"], n["z"]], dtype=float)


def local_curve_to_array(curve):
    if curve is None:
        return None

    if isinstance(curve, tuple) and len(curve) == 3:
        x, y, z = curve
        C = np.column_stack([x, y, z]).astype(float)
    else:
        C = np.asarray(curve, dtype=float)

    if C.ndim != 2 or C.shape[1] != 3:
        return None

    C[:, 2] = np.maximum(C[:, 2], 0.0)

    return C


def local_resample_curve_xyz(curve_xyz, npts=120):
    C = np.asarray(curve_xyz, dtype=float)

    if len(C) < 2:
        out = np.repeat(C[:1], npts, axis=0)
        out[:, 2] = np.maximum(out[:, 2], 0.0)
        return out

    d = np.linalg.norm(np.diff(C, axis=0), axis=1)
    s_old = np.concatenate([[0.0], np.cumsum(d)])

    if s_old[-1] < 1e-12:
        out = np.repeat(C[:1], npts, axis=0)
        out[:, 2] = np.maximum(out[:, 2], 0.0)
        return out

    s_old = s_old / s_old[-1]
    s_new = np.linspace(0.0, 1.0, npts)

    x = np.interp(s_new, s_old, C[:, 0])
    y = np.interp(s_new, s_old, C[:, 1])
    z = np.interp(s_new, s_old, C[:, 2])

    out = np.column_stack([x, y, z])
    out[:, 2] = np.maximum(out[:, 2], 0.0)

    return out


def local_orient_curve_xyz(curve_xyz, start_node, end_node):
    C = np.asarray(curve_xyz, dtype=float)

    p_start = local_node_point(start_node)
    p_end = local_node_point(end_node)

    d_normal = (
        np.linalg.norm(C[0] - p_start)
        + np.linalg.norm(C[-1] - p_end)
    )

    d_flip = (
        np.linalg.norm(C[-1] - p_start)
        + np.linalg.norm(C[0] - p_end)
    )

    if d_flip < d_normal:
        C = C[::-1].copy()

    C[:, 2] = np.maximum(C[:, 2], 0.0)

    return C


def get_crest_registry_from_result(registry_result):
    if registry_result is None:
        return None

    if isinstance(registry_result, dict) and "crest_registry" in registry_result:
        return registry_result["crest_registry"]

    return None


def get_registry_item_for_edge(registry_result, label1, label2):
    registry = get_crest_registry_from_result(registry_result)

    if registry is None:
        return None

    key = local_edge_key(label1, label2)

    return registry.get(key, None)


def get_registry_source_for_edge(registry_result, label1, label2):
    item = get_registry_item_for_edge(
        registry_result=registry_result,
        label1=label1,
        label2=label2
    )

    if item is None:
        return None, None

    if item.get("omit", False):
        return item.get("kind", "Frontera omitida"), item.get("source", "omitted")

    if item.get("curve", None) is None:
        return item.get("kind", "Frontera sin curva"), item.get("source", "curve_none")

    kind = item.get("kind", "Frontera M-M")
    source = item.get("source", "")

    return kind, source


def mm_edge_curve_from_registry(
    n1,
    n2,
    registry_result,
    npts=120
):
    item = get_registry_item_for_edge(
        registry_result=registry_result,
        label1=n1["label"],
        label2=n2["label"]
    )

    if item is None:
        print(
            f"No existe frontera M-M en crest_registry_final para "
            f"{n1['label']}-{n2['label']}."
        )
        return None, None, None

    if item.get("omit", False):
        print(
            f"La frontera M-M {n1['label']}-{n2['label']} fue omitida. "
            f"source={item.get('source', '')}"
        )
        return None, item.get("kind", "Frontera omitida"), item.get("source", "omitted")

    C = local_curve_to_array(item.get("curve", None))

    if C is None:
        print(
            f"La frontera M-M {n1['label']}-{n2['label']} existe, "
            f"pero no tiene una curva válida."
        )
        return None, item.get("kind", "Frontera sin curva"), item.get("source", "curve_none")

    C = local_resample_curve_xyz(C, npts=npts)
    C = local_orient_curve_xyz(C, n1, n2)

    kind = item.get("kind", "Frontera M-M")
    source = item.get("source", "")

    return C, kind, source


def name_from_source_or_kind(kind, source):
    source_names = {
        "base_normal_L_le_2S": "Cresta base normal L≤2S",
        "base_long_L_gt_2S": "Cresta larga L>2S",
        "direct_guard_wire": "Cable de guarda",
        "independent_guard_lines": "Cresta por guardas independientes",
        "shared_guard_plus_k": "Cresta 2 guardas + mástil K",
        "three_guard_chain": "Cresta cadena de 3 guardas",
        "four_guard_closed": "Cresta cuadrilátero cerrado"
    }

    return source_names.get(source, kind)


def get_edge_source_map_for_three_nodes(mast_nodes, registry_result):
    if len(mast_nodes) != 3:
        raise ValueError("Se requieren exactamente 3 nodos de mástil.")

    edge_map = {}

    pairs = [
        (mast_nodes[0], mast_nodes[1]),
        (mast_nodes[0], mast_nodes[2]),
        (mast_nodes[1], mast_nodes[2])
    ]

    for a, b in pairs:
        kind, source = get_registry_source_for_edge(
            registry_result=registry_result,
            label1=a["label"],
            label2=b["label"]
        )

        key = local_edge_key(a["label"], b["label"])

        edge_map[key] = {
            "node_a": a,
            "node_b": b,
            "kind": kind,
            "source": source
        }

    return edge_map


def get_source_between_nodes(edge_map, node_a, node_b):
    key = local_edge_key(node_a["label"], node_b["label"])

    if key not in edge_map:
        return None

    return edge_map[key]["source"]


def maybe_reorder_independent_guard_case(mast_nodes, registry_result):
    """
    Reordena SOLO el caso:

        direct_guard_wire + base_normal_L_le_2S + independent_guard_lines

    Objetivo:
        C12 = direct_guard_wire
        C13 = base_normal_L_le_2S
        C23 = independent_guard_lines

    Para cualquier otro caso, conserva el orden original.
    """
    original_labels = [m["label"] for m in mast_nodes]

    edge_map = get_edge_source_map_for_three_nodes(
        mast_nodes=mast_nodes,
        registry_result=registry_result
    )

    sources = [item["source"] for item in edge_map.values()]
    source_set = set(sources)

    info = {
        "applied": False,
        "reason": "No coincide con el patrón especial de dos guardas independientes.",
        "original_labels": original_labels,
        "ordered_labels": original_labels,
        "surface_model": "REGISTRY_BOUNDARY_INTERPOLATION"
    }

    if source_set != INDEPENDENT_GUARD_REORDER_PATTERN:
        return mast_nodes, info

    info["surface_model"] = "INDEPENDENT_GUARD_REORDER"

    direct_edges = [
        item for item in edge_map.values()
        if item["source"] == "direct_guard_wire"
    ]

    if len(direct_edges) != 1:
        info["reason"] = "No se encontró exactamente una arista direct_guard_wire."
        return mast_nodes, info

    direct_edge = direct_edges[0]

    a = direct_edge["node_a"]
    b = direct_edge["node_b"]

    direct_labels = {a["label"], b["label"]}

    opposite_candidates = [
        n for n in mast_nodes
        if n["label"] not in direct_labels
    ]

    if len(opposite_candidates) != 1:
        info["reason"] = "No se pudo identificar un único nodo opuesto al cable directo."
        return mast_nodes, info

    c = opposite_candidates[0]

    source_a_c = get_source_between_nodes(edge_map, a, c)
    source_b_c = get_source_between_nodes(edge_map, b, c)

    if (
        source_a_c == "base_normal_L_le_2S"
        and source_b_c == "independent_guard_lines"
    ):
        ordered_nodes = [a, b, c]

    elif (
        source_b_c == "base_normal_L_le_2S"
        and source_a_c == "independent_guard_lines"
    ):
        ordered_nodes = [b, a, c]

    else:
        info["reason"] = (
            "El patrón existe, pero las conexiones hacia el nodo opuesto "
            "no permiten forzar C13=base_normal y C23=independent_guard_lines."
        )
        return mast_nodes, info

    ordered_labels = [m["label"] for m in ordered_nodes]

    info["applied"] = True
    info["reason"] = (
        "Reordenamiento aplicado: "
        "C12=direct_guard_wire, "
        "C13=base_normal_L_le_2S, "
        "C23=independent_guard_lines."
    )
    info["ordered_labels"] = ordered_labels

    return ordered_nodes, info


def list_mmm_examples_by_source(
    triangles,
    registry_result=None,
    max_items=None
):
    if registry_result is None:
        raise ValueError("Debes pasar registry_result=resultado_crestas_final.")

    mmm_list = get_all_mmm_triangles(triangles)

    if len(mmm_list) == 0:
        print("No hay triángulos M-M-M disponibles.")
        return []

    rows = []

    print("=========================================================")
    print("LISTA DE EJEMPLOS M-M-M DISPONIBLES")
    print("=========================================================")

    for idx, tri in enumerate(mmm_list):
        if max_items is not None and idx >= max_items:
            break

        mast_nodes = [
            node for node in tri["nodes"]
            if node["type"] == "mast_top"
        ]

        if len(mast_nodes) != 3:
            continue

        m1, m2, m3 = mast_nodes

        kind12, source12 = get_registry_source_for_edge(
            registry_result, m1["label"], m2["label"]
        )

        kind13, source13 = get_registry_source_for_edge(
            registry_result, m1["label"], m3["label"]
        )

        kind23, source23 = get_registry_source_for_edge(
            registry_result, m2["label"], m3["label"]
        )

        mmm_class = classify_mmm_sources(source12, source13, source23)
        surface_model = classify_surface_model(source12, source13, source23)

        ordered_nodes, reorder_info = maybe_reorder_independent_guard_case(
            mast_nodes=mast_nodes,
            registry_result=registry_result
        )

        labels_txt = f"{m1['label']}-{m2['label']}-{m3['label']}"

        print(f"[{idx}] {labels_txt}")
        print(f"    {m1['label']}-{m2['label']}: {source12}")
        print(f"    {m1['label']}-{m3['label']}: {source13}")
        print(f"    {m2['label']}-{m3['label']}: {source23}")
        print(f"    clasificación: {mmm_class}")
        print(f"    modelo de superficie: {surface_model}")

        if reorder_info["applied"]:
            ordered_txt = "-".join(reorder_info["ordered_labels"])
            print(f"    orden de interpolación corregido: {ordered_txt}")
            print("    patrón usado: C12=direct_guard_wire, C13=base_normal, C23=independent_guard_lines")

        print("")

        rows.append({
            "mmm_index": idx,
            "labels": labels_txt,
            "source12": source12,
            "source13": source13,
            "source23": source23,
            "classification": mmm_class,
            "surface_model": surface_model,
            "reorder_applied": reorder_info["applied"],
            "ordered_labels": reorder_info["ordered_labels"]
        })

    return rows


def build_mmm_patch_from_boundaries(
    C12,
    C13,
    C23,
    ns=90,
    nt=90,

    # Activación de corrección especial:
    # si ninguna cresta baja de este valor, se usa la interpolación antigua.
    low_crest_activation_z=0.50,

    # Parámetros SOLO para MMM cerca del suelo.
    max_iter=3500,
    tol=1e-5,
    omega=1.55,
    rise_gamma_from_low_crest=1.50,
    low_crest_anchor_strength=1.00,
    other_boundary_band=0.14,
    blend_curve_power=0.80,
    preserve_nonnegative=True
):
    """
    Construye un parche MMM híbrido.

    Regla:
      1) Si ninguna frontera está cerca del suelo:
            usa la interpolación ORIGINAL.
      2) Si alguna frontera está cerca del suelo:
            usa la interpolación especial desde la cresta baja,
            con subida suave y progresiva.

    Esto evita deformar todos los MMM.
    """

    import numpy as np

    # =====================================================
    # 0) UTILIDADES
    # =====================================================

    def _resample_curve(C, n):
        C = np.asarray(C, dtype=float)

        if len(C) == n:
            return C.copy()

        if len(C) == 1:
            return np.repeat(C, n, axis=0)

        seg = np.linalg.norm(np.diff(C, axis=0), axis=1)
        s = np.zeros(len(C))
        s[1:] = np.cumsum(seg)

        if s[-1] <= 1e-12:
            return np.repeat(C[:1], n, axis=0)

        u = s / s[-1]
        u_new = np.linspace(0.0, 1.0, n)

        return np.column_stack([
            np.interp(u_new, u, C[:, 0]),
            np.interp(u_new, u, C[:, 1]),
            np.interp(u_new, u, C[:, 2]),
        ])

    def _smoothstep(x):
        x = np.clip(x, 0.0, 1.0)
        return x * x * (3.0 - 2.0 * x)

    def _closest_dist_and_z_to_curve(XY, C):
        """
        Para cada punto XY, busca el punto más cercano sobre C
        y devuelve distancia XY + Z interpolada.
        """
        XY = np.asarray(XY, dtype=float)
        C = np.asarray(C, dtype=float)

        Cxy = C[:, :2]
        Cz = C[:, 2]

        npts = XY.shape[0]

        best_d2 = np.full(npts, np.inf, dtype=float)
        best_z = np.full(npts, np.nan, dtype=float)

        for k in range(len(C) - 1):
            A = Cxy[k]
            B = Cxy[k + 1]

            zA = Cz[k]
            zB = Cz[k + 1]

            AB = B - A
            den = np.dot(AB, AB)

            if den <= 1e-12:
                Q = np.repeat(A[None, :], npts, axis=0)
                zq = np.full(npts, zA, dtype=float)
            else:
                AP = XY - A[None, :]
                q = np.clip((AP @ AB) / den, 0.0, 1.0)

                Q = A[None, :] + q[:, None] * AB[None, :]
                zq = zA + q * (zB - zA)

            d2 = np.sum((XY - Q) ** 2, axis=1)
            mask = d2 < best_d2

            best_d2[mask] = d2[mask]
            best_z[mask] = zq[mask]

        return np.sqrt(best_d2), best_z

    # =====================================================
    # 1) PREPARAR FRONTERAS
    # =====================================================

    C12 = _resample_curve(np.asarray(C12, dtype=float), ns)
    C13 = _resample_curve(np.asarray(C13, dtype=float), nt)
    C23 = _resample_curve(np.asarray(C23, dtype=float), nt)

    C12[:, 2] = np.maximum(C12[:, 2], 0.0)
    C13[:, 2] = np.maximum(C13[:, 2], 0.0)
    C23[:, 2] = np.maximum(C23[:, 2], 0.0)

    # =====================================================
    # 2) INTERPOLACIÓN ORIGINAL
    #    Esta se usa para TODOS los MMM que no estén cerca
    #    del suelo.
    # =====================================================

    def _build_original_patch():
        X = np.zeros((nt, ns))
        Y = np.zeros((nt, ns))
        Z = np.zeros((nt, ns))

        for it in range(nt):
            t = it / (nt - 1)

            Lt = C13[it]
            Rt = C23[it]

            for is_ in range(ns):
                s = is_ / (ns - 1)

                Cs = C12[is_]

                base_lr = (1.0 - s) * Lt + s * Rt
                top_linear = (1.0 - s) * C12[0] + s * C12[-1]
                top_correction = (1.0 - t) * (Cs - top_linear)

                P = base_lr + top_correction

                X[it, is_] = P[0]
                Y[it, is_] = P[1]
                Z[it, is_] = max(P[2], 0.0)

        # Preservar fronteras exactas
        X[0, :] = C12[:, 0]
        Y[0, :] = C12[:, 1]
        Z[0, :] = C12[:, 2]

        X[:, 0] = C13[:, 0]
        Y[:, 0] = C13[:, 1]
        Z[:, 0] = C13[:, 2]

        X[:, -1] = C23[:, 0]
        Y[:, -1] = C23[:, 1]
        Z[:, -1] = C23[:, 2]

        Z = np.maximum(Z, 0.0)

        return X, Y, Z

    # =====================================================
    # 3) DECIDIR SI SE ACTIVA LA CORRECCIÓN DE CRESTA BAJA
    # =====================================================

    zmin_12 = float(np.nanmin(C12[:, 2]))
    zmin_13 = float(np.nanmin(C13[:, 2]))
    zmin_23 = float(np.nanmin(C23[:, 2]))

    zmin_global = min(zmin_12, zmin_13, zmin_23)

    # Si no hay ninguna cresta cerca del suelo:
    # dejar el MMM como antes.
    if zmin_global > low_crest_activation_z:
        return _build_original_patch()

    # =====================================================
    # 4) SI HAY CRESTA BAJA: CONSTRUIR XY COMO ANTES
    # =====================================================

    X = np.zeros((nt, ns))
    Y = np.zeros((nt, ns))

    for it in range(nt):
        t = it / (nt - 1)

        Lt = C13[it, :2]
        Rt = C23[it, :2]

        for is_ in range(ns):
            s = is_ / (ns - 1)

            Cs = C12[is_, :2]

            top_linear = (1.0 - s) * C12[0, :2] + s * C12[-1, :2]
            base_lr = (1.0 - s) * Lt + s * Rt
            top_correction = (1.0 - t) * (Cs - top_linear)

            Pxy = base_lr + top_correction

            X[it, is_] = Pxy[0]
            Y[it, is_] = Pxy[1]

    # Preservar XY de fronteras
    X[0, :] = C12[:, 0]
    Y[0, :] = C12[:, 1]

    X[:, 0] = C13[:, 0]
    Y[:, 0] = C13[:, 1]

    X[:, -1] = C23[:, 0]
    Y[:, -1] = C23[:, 1]

    # =====================================================
    # 5) BASE SUAVE EN Z
    # =====================================================

    Z = np.full((nt, ns), np.nan, dtype=float)
    boundary_mask = np.zeros((nt, ns), dtype=bool)

    Z[0, :] = C12[:, 2]
    boundary_mask[0, :] = True

    Z[:, 0] = C13[:, 2]
    boundary_mask[:, 0] = True

    Z[:, -1] = C23[:, 2]
    boundary_mask[:, -1] = True

    z_m3 = float(max(0.0, 0.5 * (C13[-1, 2] + C23[-1, 2])))

    Z[-1, :] = z_m3
    boundary_mask[-1, :] = True

    Z[0, 0] = C13[0, 2]
    Z[0, -1] = C23[0, 2]
    Z[-1, :] = z_m3

    for it in range(1, nt - 1):
        t = it / (nt - 1)

        for is_ in range(1, ns - 1):
            s = is_ / (ns - 1)

            z_c12 = C12[is_, 2]
            z_side = (1.0 - s) * C13[it, 2] + s * C23[it, 2]
            z_to_m3 = (1.0 - t) * z_c12 + t * z_m3

            Z[it, is_] = 0.55 * z_to_m3 + 0.45 * z_side

    # Relajación armónica base
    for _ in range(max_iter):
        max_delta = 0.0

        for it in range(1, nt - 1):
            for is_ in range(1, ns - 1):
                if boundary_mask[it, is_]:
                    continue

                z_old = Z[it, is_]

                z_avg = 0.25 * (
                    Z[it - 1, is_] +
                    Z[it + 1, is_] +
                    Z[it, is_ - 1] +
                    Z[it, is_ + 1]
                )

                z_new = (1.0 - omega) * z_old + omega * z_avg

                if preserve_nonnegative:
                    z_new = max(z_new, 0.0)

                Z[it, is_] = z_new
                max_delta = max(max_delta, abs(z_new - z_old))

        Z[0, :] = C12[:, 2]
        Z[:, 0] = C13[:, 2]
        Z[:, -1] = C23[:, 2]
        Z[-1, :] = z_m3

        if max_delta < tol:
            break

    Z_base = Z.copy()

    # =====================================================
    # 6) DETECTAR CRESTA MÁS CERCANA AL SUELO
    # =====================================================

    boundary_defs = [
        {
            "name": "C12",
            "curve": C12,
            "zmin": float(np.nanmin(C12[:, 2])),
            "zmean": float(np.nanmean(C12[:, 2])),
        },
        {
            "name": "C13",
            "curve": C13,
            "zmin": float(np.nanmin(C13[:, 2])),
            "zmean": float(np.nanmean(C13[:, 2])),
        },
        {
            "name": "C23",
            "curve": C23,
            "zmin": float(np.nanmin(C23[:, 2])),
            "zmean": float(np.nanmean(C23[:, 2])),
        },
    ]

    boundary_defs = sorted(
        boundary_defs,
        key=lambda r: (r["zmin"], r["zmean"])
    )

    low_boundary = boundary_defs[0]
    other_boundaries = boundary_defs[1:]

    C_low = low_boundary["curve"]

    # =====================================================
    # 7) SUBIDA DESDE LA CRESTA BAJA
    # =====================================================

    XY = np.column_stack([X.ravel(), Y.ravel()])

    d_low, z_low = _closest_dist_and_z_to_curve(XY, C_low)
    d_low = d_low.reshape(X.shape)
    z_low = z_low.reshape(X.shape)

    d_other_all = []

    for bd in other_boundaries:
        d_tmp, _ = _closest_dist_and_z_to_curve(XY, bd["curve"])
        d_other_all.append(d_tmp.reshape(X.shape))

    d_other = np.minimum(d_other_all[0], d_other_all[1])

    xmin, xmax = np.nanmin(X), np.nanmax(X)
    ymin, ymax = np.nanmin(Y), np.nanmax(Y)
    diag_xy = max(np.hypot(xmax - xmin, ymax - ymin), 1e-9)

    d_scale = np.nanpercentile(d_low, 98)

    if not np.isfinite(d_scale) or d_scale <= 1e-9:
        d_scale = np.nanmax(d_low)

    if not np.isfinite(d_scale) or d_scale <= 1e-9:
        d_scale = diag_xy

    rho = np.clip(d_low / d_scale, 0.0, 1.0)

    # gamma alto = subida más lenta desde la cresta baja.
    rise = _smoothstep(rho ** rise_gamma_from_low_crest)

    other_band = max(other_boundary_band * diag_xy, 1e-9)
    q_other = np.clip(d_other / other_band, 0.0, 1.0)

    force_base_near_others = 1.0 - _smoothstep(q_other)

    # Unión suave entre subida desde cresta baja y acople a otras crestas.
    blend = rise + force_base_near_others - rise * force_base_near_others
    blend = np.clip(blend, 0.0, 1.0)

    blend_curve = blend ** blend_curve_power

    Z_from_low_crest = (
        (1.0 - blend_curve) * z_low
        + blend_curve * Z_base
    )

    Z = (
        (1.0 - low_crest_anchor_strength) * Z_base
        + low_crest_anchor_strength * Z_from_low_crest
    )

    if preserve_nonnegative:
        Z = np.maximum(Z, 0.0)

    # =====================================================
    # 8) REIMPONER FRONTERAS EXACTAS
    # =====================================================

    Z[0, :] = C12[:, 2]
    Z[:, 0] = C13[:, 2]
    Z[:, -1] = C23[:, 2]
    Z[-1, :] = z_m3

    if preserve_nonnegative:
        Z = np.maximum(Z, 0.0)

    Z[0, :] = C12[:, 2]
    Z[:, 0] = C13[:, 2]
    Z[:, -1] = C23[:, 2]
    Z[-1, :] = z_m3

    return X, Y, Z


def build_mmm_patch_from_three_crests(
    m1,
    m2,
    m3,
    sphere_radius,
    guard_wire_inputs=None,
    registry_result=None,
    ns=90,
    nt=90
):
    if registry_result is None:
        raise ValueError(
            "Debes pasar registry_result=resultado_crestas_final "
            "para construir MMM con las fronteras definitivas del registro activo."
        )

    C12_raw, kind12, source12 = mm_edge_curve_from_registry(
        n1=m1,
        n2=m2,
        registry_result=registry_result,
        npts=ns
    )

    C13_raw, kind13, source13 = mm_edge_curve_from_registry(
        n1=m1,
        n2=m3,
        registry_result=registry_result,
        npts=nt
    )

    C23_raw, kind23, source23 = mm_edge_curve_from_registry(
        n1=m2,
        n2=m3,
        registry_result=registry_result,
        npts=nt
    )

    if C12_raw is None or C13_raw is None or C23_raw is None:
        return None

    C12 = local_orient_curve_xyz(C12_raw, m1, m2)
    C13 = local_orient_curve_xyz(C13_raw, m1, m3)
    C23 = local_orient_curve_xyz(C23_raw, m2, m3)

    C12 = local_resample_curve_xyz(C12, ns)
    C13 = local_resample_curve_xyz(C13, nt)
    C23 = local_resample_curve_xyz(C23, nt)

    mmm_class = classify_mmm_sources(source12, source13, source23)
    surface_model = classify_surface_model(source12, source13, source23)

    if mmm_class == "INTERPOLABLE_MMM":
        X, Y, Z = build_mmm_patch_from_boundaries(
            C12=C12,
            C13=C13,
            C23=C23,
            ns=ns,
            nt=nt
        )

        return {
            "status": "built",
            "classification": mmm_class,
            "surface_model": surface_model,
            "X": X,
            "Y": Y,
            "Z": Z,
            "C12": C12,
            "C13": C13,
            "C23": C23,
            "kind12": kind12,
            "kind13": kind13,
            "kind23": kind23,
            "source12": source12,
            "source13": source13,
            "source23": source23
        }

    return {
        "status": "unsupported",
        "classification": mmm_class,
        "surface_model": surface_model,
        "X": None,
        "Y": None,
        "Z": None,
        "C12": C12,
        "C13": C13,
        "C23": C23,
        "kind12": kind12,
        "kind13": kind13,
        "kind23": kind23,
        "source12": source12,
        "source13": source13,
        "source23": source23
    }


def plot_one_mmm_patch(
    triangles,
    sphere_radius,
    guard_wire_inputs=None,
    registry_result=None,
    mmm_index=0,
    ns=90,
    nt=90,
    show_internal_mesh=True,
    show_boundary_only_when_unsupported=True
):
    tri = find_one_mmm_triangle(triangles, index=mmm_index)

    mast_nodes_original = [
        node for node in tri["nodes"]
        if node["type"] == "mast_top"
    ]

    if len(mast_nodes_original) != 3:
        raise ValueError("El triángulo seleccionado no es M-M-M válido.")

    mast_nodes_ordered, reorder_info = maybe_reorder_independent_guard_case(
        mast_nodes=mast_nodes_original,
        registry_result=registry_result
    )

    m1, m2, m3 = mast_nodes_ordered

    built = build_mmm_patch_from_three_crests(
        m1=m1,
        m2=m2,
        m3=m3,
        sphere_radius=sphere_radius,
        guard_wire_inputs=guard_wire_inputs,
        registry_result=registry_result,
        ns=ns,
        nt=nt
    )

    if built is None:
        raise ValueError("No se pudo construir ni diagnosticar el parche M-M-M.")

    X = built["X"]
    Y = built["Y"]
    Z = built["Z"]

    C12 = built["C12"]
    C13 = built["C13"]
    C23 = built["C23"]

    kind12 = built["kind12"]
    kind13 = built["kind13"]
    kind23 = built["kind23"]

    source12 = built["source12"]
    source13 = built["source13"]
    source23 = built["source23"]

    status = built["status"]
    classification = built["classification"]
    surface_model = built["surface_model"]

    fig = go.Figure()

    # -----------------------------------------------------
    # 1) Relleno M-M-M
    # -----------------------------------------------------
    if status == "built":
        Z = np.maximum(Z, 0.0)

        fig.add_trace(go.Surface(
            x=X,
            y=Y,
            z=Z,
            opacity=0.75,
            showscale=False,
            name=f"Parche M-M-M | {surface_model}"
        ))

        if show_internal_mesh:
            step_t = max(1, nt // 10)
            step_s = max(1, ns // 10)

            for row in range(0, nt, step_t):
                fig.add_trace(go.Scatter3d(
                    x=X[row, :],
                    y=Y[row, :],
                    z=Z[row, :],
                    mode="lines",
                    line=dict(width=2),
                    showlegend=False
                ))

            for col in range(0, ns, step_s):
                fig.add_trace(go.Scatter3d(
                    x=X[:, col],
                    y=Y[:, col],
                    z=Z[:, col],
                    mode="lines",
                    line=dict(width=2),
                    showlegend=False
                ))

    else:
        if not show_boundary_only_when_unsupported:
            raise ValueError(
                "El MMM seleccionado contiene una frontera no soportada. "
                "No se rellena con la interpolación actual."
            )

    # -----------------------------------------------------
    # 2) Fronteras definitivas
    # -----------------------------------------------------
    name12 = name_from_source_or_kind(kind12, source12)
    name13 = name_from_source_or_kind(kind13, source13)
    name23 = name_from_source_or_kind(kind23, source23)

    fig.add_trace(go.Scatter3d(
        x=C12[:, 0],
        y=C12[:, 1],
        z=C12[:, 2],
        mode="lines",
        line=dict(width=8),
        name=f"C12 | {name12} {m1['label']}-{m2['label']}"
    ))

    fig.add_trace(go.Scatter3d(
        x=C13[:, 0],
        y=C13[:, 1],
        z=C13[:, 2],
        mode="lines",
        line=dict(width=8),
        name=f"C13 | {name13} {m1['label']}-{m3['label']}"
    ))

    fig.add_trace(go.Scatter3d(
        x=C23[:, 0],
        y=C23[:, 1],
        z=C23[:, 2],
        mode="lines",
        line=dict(width=8),
        name=f"C23 | {name23} {m2['label']}-{m3['label']}"
    ))

    # -----------------------------------------------------
    # 3) Mástiles
    # -----------------------------------------------------
    for m in [m1, m2, m3]:
        fig.add_trace(go.Scatter3d(
            x=[m["x"], m["x"]],
            y=[m["y"], m["y"]],
            z=[0.0, m["z"]],
            mode="lines+markers+text",
            line=dict(width=8),
            marker=dict(size=5),
            text=["", m["label"]],
            textposition="top center",
            name=m["label"]
        ))

    # -----------------------------------------------------
    # 4) Plano base
    # -----------------------------------------------------
    pts_x = [m1["x"], m2["x"], m3["x"]]
    pts_y = [m1["y"], m2["y"], m3["y"]]

    pad = 8
    xmin, xmax = min(pts_x) - pad, max(pts_x) + pad
    ymin, ymax = min(pts_y) - pad, max(pts_y) + pad

    Xg, Yg = np.meshgrid(
        np.linspace(xmin, xmax, 2),
        np.linspace(ymin, ymax, 2)
    )

    fig.add_trace(go.Surface(
        x=Xg,
        y=Yg,
        z=np.zeros_like(Xg),
        opacity=0.12,
        showscale=False,
        hoverinfo="skip",
        name="Plano z=0"
    ))

    # -----------------------------------------------------
    # 5) Título
    # -----------------------------------------------------
    if status == "built":
        title_status = "RELLENADO"
    else:
        title_status = "NO RELLENADO | Fuente no soportada"

    fig.update_layout(
        title=(
            f"{title_status}: "
            f"{m1['label']}-{m2['label']}-{m3['label']} | "
            f"{surface_model}"
        ),
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="data"
        ),
        height=900,
        showlegend=True
    )

    # -----------------------------------------------------
    # 6) Diagnóstico
    # -----------------------------------------------------
    original_txt = "-".join(reorder_info["original_labels"])
    ordered_txt = "-".join(reorder_info["ordered_labels"])

    print("=========================================================")
    print("DIAGNÓSTICO DEL M-M-M SELECCIONADO")
    print("=========================================================")
    print(f"mmm_index = {mmm_index}")
    print(f"Triángulo original: {original_txt}")
    print(f"Orden usado para interpolar: {ordered_txt}")
    print(f"Clasificación: {classification}")
    print(f"Modelo de superficie: {surface_model}")
    print(f"Estado: {status}")

    print("")
    print("Reordenamiento especial para dos guardas independientes:")
    print(f"  aplicado: {reorder_info['applied']}")
    print(f"  motivo: {reorder_info['reason']}")

    print("")
    print("Fronteras M-M usadas en la interpolación:")
    print(f"  C12 = {m1['label']}-{m2['label']}: {kind12} | source={source12}")
    print(f"  C13 = {m1['label']}-{m3['label']}: {kind13} | source={source13}")
    print(f"  C23 = {m2['label']}-{m3['label']}: {kind23} | source={source23}")

    if status == "built":
        print("")
        print("Este MMM sí se rellenó porque todas sus fronteras pertenecen a modelos habilitados.")
    else:
        print("")
        print("Este MMM NO se rellenó porque contiene al menos una frontera no reconocida.")
        print("Revisa los source impresos arriba.")

    fig.show()

    return built


import plotly.graph_objects as go


import numpy as np


import plotly.graph_objects as go


import inspect


from matplotlib.path import Path


def function_accepts_argument(func, arg_name):
    """
    Verifica si una función acepta un argumento determinado.
    Sirve para mantener compatibilidad con funciones anteriores.
    """
    try:
        return arg_name in inspect.signature(func).parameters
    except Exception:
        return False


def add_cube_to_fig(fig, cube, opacity=0.35):
    """
    Agrega un cubo/prisma rectangular al gráfico Plotly 3D.

    cube:
      x, y, z    -> esquina inferior mínima
      dx, dy, dz -> dimensiones del equipo
      color      -> color opcional
      name       -> nombre opcional
    """
    x0, y0, z0 = cube["x"], cube["y"], cube["z"]
    dx, dy, dz = cube["dx"], cube["dy"], cube["dz"]

    x = [x0, x0+dx, x0+dx, x0,    x0, x0+dx, x0+dx, x0]
    y = [y0, y0,    y0+dy, y0+dy, y0, y0,    y0+dy, y0+dy]
    z = [z0, z0,    z0,    z0,    z0+dz, z0+dz, z0+dz, z0+dz]

    i = [0, 0, 0, 1, 2, 3, 4, 4, 5, 6, 7, 7]
    j = [1, 2, 3, 2, 3, 0, 5, 6, 6, 7, 4, 5]
    k = [2, 3, 1, 6, 7, 4, 6, 7, 2, 3, 0, 3]

    fig.add_trace(go.Mesh3d(
        x=x,
        y=y,
        z=z,
        i=i,
        j=j,
        k=k,
        opacity=opacity,
        color=cube.get("color", "gray"),
        name=cube.get("name", "Equipo"),
        hovertemplate=(
            f"{cube.get('name', 'Equipo')}<br>"
            f"x=[{x0:.2f}, {x0+dx:.2f}]<br>"
            f"y=[{y0:.2f}, {y0+dy:.2f}]<br>"
            f"z=[{z0:.2f}, {z0+dz:.2f}]<extra></extra>"
        )
    ))

    return fig


def build_all_mmm_patch_records(
    triangles,
    sphere_radius,
    guard_wire_inputs=None,
    registry_result=None,
    ns=75,
    nt=75
):
    """
    Construye todos los parches M-M-M y los guarda como registros.

    Esta versión usa la lógica actualizada de la celda 18:

      - Cada frontera M-M viene desde registry_result["crest_registry"].
      - Se aplica reordenamiento especial si aparece el patrón:
            direct_guard_wire + base_normal_L_le_2S + independent_guard_lines

    El registro resultante se usa luego para:
      - calcular z_min;
      - filtrar capa superior;
      - graficar solo los MMM seleccionados.
    """
    records = []

    count_fail = 0
    count_unsupported = 0
    count_reordered = 0

    for k, tri in enumerate(triangles):
        if classify_triangle_type(tri) != "M-M-M":
            continue

        mast_nodes_original = [
            n for n in tri["nodes"]
            if n["type"] == "mast_top"
        ]

        if len(mast_nodes_original) != 3:
            count_fail += 1
            continue

        # -------------------------------------------------
        # 1) Reordenamiento especial solo si aplica
        # -------------------------------------------------
        mast_nodes_used = mast_nodes_original

        reorder_info = {
            "applied": False,
            "reason": "No se evaluó reordenamiento especial.",
            "original_labels": [m["label"] for m in mast_nodes_original],
            "ordered_labels": [m["label"] for m in mast_nodes_original],
            "surface_model": "REGISTRY_BOUNDARY_INTERPOLATION"
        }

        if (
            registry_result is not None
            and "maybe_reorder_independent_guard_case" in globals()
        ):
            mast_nodes_used, reorder_info = maybe_reorder_independent_guard_case(
                mast_nodes=mast_nodes_original,
                registry_result=registry_result
            )

        if reorder_info.get("applied", False):
            count_reordered += 1

        m1, m2, m3 = mast_nodes_used

        # -------------------------------------------------
        # 2) Construir parche MMM
        # -------------------------------------------------
        try:
            patch = build_mmm_patch_from_three_crests(
                m1=m1,
                m2=m2,
                m3=m3,
                sphere_radius=sphere_radius,
                guard_wire_inputs=guard_wire_inputs,
                registry_result=registry_result,
                ns=ns,
                nt=nt
            )
        except TypeError:
            # Compatibilidad con versión anterior sin registry_result.
            patch = build_mmm_patch_from_three_crests(
                m1=m1,
                m2=m2,
                m3=m3,
                sphere_radius=sphere_radius,
                guard_wire_inputs=guard_wire_inputs,
                ns=ns,
                nt=nt
            )

        if patch is None:
            count_fail += 1
            continue

        # -------------------------------------------------
        # 3) Extraer datos del parche
        # -------------------------------------------------
        if isinstance(patch, dict):
            status = patch.get("status", "unknown")
            classification = patch.get("classification", "")
            surface_model = patch.get("surface_model", "")

            if status != "built":
                count_unsupported += 1
                continue

            X = patch["X"]
            Y = patch["Y"]
            Z = patch["Z"]

            C12 = patch["C12"]
            C13 = patch["C13"]
            C23 = patch["C23"]

            kind12 = patch.get("kind12", "")
            kind13 = patch.get("kind13", "")
            kind23 = patch.get("kind23", "")

            source12 = patch.get("source12", "")
            source13 = patch.get("source13", "")
            source23 = patch.get("source23", "")

        else:
            # Formato antiguo:
            # X, Y, Z, C12, C13, C23, kind12, kind13, kind23
            (
                X, Y, Z,
                C12, C13, C23,
                kind12, kind13, kind23
            ) = patch

            status = "built"
            classification = "LEGACY_MMM"
            surface_model = "LEGACY_INTERPOLATION"

            source12 = kind12
            source13 = kind13
            source23 = kind23

        # -------------------------------------------------
        # 4) Seguridad Z >= 0
        # -------------------------------------------------
        Z = np.maximum(Z, 0.0)

        C12 = np.asarray(C12, dtype=float)
        C13 = np.asarray(C13, dtype=float)
        C23 = np.asarray(C23, dtype=float)

        C12[:, 2] = np.maximum(C12[:, 2], 0.0)
        C13[:, 2] = np.maximum(C13[:, 2], 0.0)
        C23[:, 2] = np.maximum(C23[:, 2], 0.0)

        original_labels = reorder_info.get(
            "original_labels",
            [m["label"] for m in mast_nodes_original]
        )

        ordered_labels = reorder_info.get(
            "ordered_labels",
            [m1["label"], m2["label"], m3["label"]]
        )

        records.append({
            "idx": k,
            "tri": tri,
            "masts": (m1, m2, m3),
            "masts_original": tuple(mast_nodes_original),

            "original_labels": original_labels,
            "ordered_labels": ordered_labels,

            "reorder_applied": reorder_info.get("applied", False),
            "reorder_reason": reorder_info.get("reason", ""),

            "status": status,
            "classification": classification,
            "surface_model": surface_model,

            "X": X,
            "Y": Y,
            "Z": Z,

            "C12": C12,
            "C13": C13,
            "C23": C23,

            "kind12": kind12,
            "kind13": kind13,
            "kind23": kind23,

            "source12": source12,
            "source13": source13,
            "source23": source23,

            "z_min": float(np.nanmin(Z)),
            "z_max": float(np.nanmax(Z)),
        })

    print("=========================================================")
    print("CONSTRUCCIÓN DE REGISTROS MMM")
    print("=========================================================")
    print(f"MMM construidos correctamente : {len(records)}")
    print(f"MMM no construidos por error  : {count_fail}")
    print(f"MMM no soportados             : {count_unsupported}")
    print(f"MMM reordenados               : {count_reordered}")

    return records


def polygon_from_mmm_record(rec):
    """
    Construye el polígono XY de un MMM a partir de sus tres fronteras.

    Orden:
      C12
      C23
      C13 invertida
    """
    C12 = rec["C12"]
    C13 = rec["C13"]
    C23 = rec["C23"]

    poly = np.vstack([
        C12[:, :2],
        C23[:, :2],
        C13[::-1, :2]
    ])

    return poly


def filter_mmm_by_zmin_preserve_xy_coverage(
    mmm_records,
    grid_n=260,
    min_new_cells=1
):
    """
    Filtra los MMM conservando cobertura XY.

    Criterio:
      1) Ordena los MMM por z_min descendente.
      2) Conserva un MMM si aporta nuevas celdas XY no cubiertas.
      3) Descarta MMM redundantes que no aportan cobertura nueva.
    """
    if len(mmm_records) == 0:
        return [], []

    all_xy = []

    for rec in mmm_records:
        all_xy.append(np.column_stack([
            rec["X"].ravel(),
            rec["Y"].ravel()
        ]))

    all_xy = np.vstack(all_xy)

    xmin, ymin = np.nanmin(all_xy, axis=0)
    xmax, ymax = np.nanmax(all_xy, axis=0)

    pad_x = 0.02 * max(xmax - xmin, 1.0)
    pad_y = 0.02 * max(ymax - ymin, 1.0)

    xmin -= pad_x
    xmax += pad_x
    ymin -= pad_y
    ymax += pad_y

    gx = np.linspace(xmin, xmax, grid_n)
    gy = np.linspace(ymin, ymax, grid_n)

    GX, GY = np.meshgrid(gx, gy)
    pts = np.column_stack([GX.ravel(), GY.ravel()])

    covered = np.zeros(pts.shape[0], dtype=bool)

    selected = []
    rejected = []

    ordered = sorted(
        mmm_records,
        key=lambda r: r["z_min"],
        reverse=True
    )

    for rec in ordered:
        poly = polygon_from_mmm_record(rec)
        path = Path(poly)

        mask = path.contains_points(pts)
        new_cells = np.count_nonzero(mask & (~covered))

        rec["coverage_cells"] = int(np.count_nonzero(mask))
        rec["new_cells"] = int(new_cells)

        if new_cells >= min_new_cells:
            selected.append(rec)
            covered |= mask
        else:
            rejected.append(rec)

    print("=========================================================")
    print("FILTRO MMM POR z_min")
    print("=========================================================")
    print(f"MMM construidos                : {len(mmm_records)}")
    print(f"MMM conservados capa superior  : {len(selected)}")
    print(f"MMM eliminados por redundancia : {len(rejected)}")

    print("\nConservados:")
    for rec in selected:
        m1, m2, m3 = rec["masts"]
        print(
            f"  {m1['label']}-{m2['label']}-{m3['label']} | "
            f"z_min={rec['z_min']:.4f} | "
            f"new_cells={rec['new_cells']} | "
            f"modelo={rec.get('surface_model', '')} | "
            f"reordenado={rec.get('reorder_applied', False)}"
        )

    print("\nEliminados:")
    for rec in rejected:
        m1, m2, m3 = rec["masts"]
        print(
            f"  {m1['label']}-{m2['label']}-{m3['label']} | "
            f"z_min={rec['z_min']:.4f} | "
            f"new_cells={rec['new_cells']} | "
            f"modelo={rec.get('surface_model', '')} | "
            f"reordenado={rec.get('reorder_applied', False)}"
        )

    return selected, rejected


def add_selected_mmm_patches_to_fig(
    fig,
    selected_mmm_records,
    opacity=0.72
):
    """
    Agrega al gráfico solamente los MMM seleccionados por el filtro.
    """
    for rec in selected_mmm_records:
        m1, m2, m3 = rec["masts"]

        original_txt = "-".join(rec.get(
            "original_labels",
            [m1["label"], m2["label"], m3["label"]]
        ))

        ordered_txt = "-".join(rec.get(
            "ordered_labels",
            [m1["label"], m2["label"], m3["label"]]
        ))

        fig.add_trace(go.Surface(
            x=rec["X"],
            y=rec["Y"],
            z=np.maximum(rec["Z"], 0.0),
            opacity=opacity,
            showscale=False,
            name=f"MMM superior {m1['label']}-{m2['label']}-{m3['label']}",
            hovertemplate=(
                f"MMM superior<br>"
                f"Original: {original_txt}<br>"
                f"Orden usado: {ordered_txt}<br>"
                f"Modelo: {rec.get('surface_model', '')}<br>"
                f"z_min={rec['z_min']:.3f}<br>"
                f"C12 {m1['label']}-{m2['label']}: {rec.get('source12', '')}<br>"
                f"C13 {m1['label']}-{m3['label']}: {rec.get('source13', '')}<br>"
                f"C23 {m2['label']}-{m3['label']}: {rec.get('source23', '')}<br>"
                f"Reordenado: {rec.get('reorder_applied', False)}<br>"
                "x=%{x:.2f}<br>"
                "y=%{y:.2f}<br>"
                "z=%{z:.2f}<extra></extra>"
            )
        ))

    return fig


def extract_visible_triangles_for_edges(
    original_triangles,
    selected_mmm_records,
    keep_mmq=True
):
    """
    Devuelve una lista de triángulos que sí deben aportar crestas/cables/segmentos:
      - todos los M-M-Q conservados, si keep_mmq=True;
      - solo los M-M-M seleccionados por el filtro.
    """
    visible = []

    selected_ids = set(rec["idx"] for rec in selected_mmm_records)

    for k, tri in enumerate(original_triangles):
        tri_type = classify_triangle_type(tri)

        if keep_mmq and tri_type == "M-M-Q":
            visible.append(tri)

        elif tri_type == "M-M-M" and k in selected_ids:
            visible.append(tri)

    return visible


def plot_full_surface_with_filtered_mmm_layer_clean_edges(
    masts,
    sphere_radius,
    results,
    tri_nodes,
    triangles,
    guard_wire_inputs=None,
    registry_result=None,
    grid_n=260,
    show_single_mast_surfaces=True,
    show_red_q_edges=True,
    show_mmq_fill=True,
    show_filtered_mmm_fill=True,
    show_mmm_borders=True,
    show_mm_crests=True,
    show_mq_segments=True,
    show_q_points=True,
    cube_inputs=None,
):
    fig = go.Figure()

    # -----------------------------------------------------
    # 1) Superficies de mástil solo
    # -----------------------------------------------------
    if show_single_mast_surfaces:
        for i, mast in enumerate(masts):
            add_mast_to_figure(
                fig=fig,
                mast=mast,
                idx=i,
                sphere_radius=sphere_radius,
                results=results,
                show_mast_line=True,
                show_base_circle=True
            )

    # -----------------------------------------------------
    # 2) Segmentos rojos sobre capa de mástil solo
    # -----------------------------------------------------
    if show_red_q_edges:
        dibujar_aristas_Q(
            fig=fig,
            masts=masts,
            results=results,
            S=sphere_radius,
            n_pts=200
        )

    # -----------------------------------------------------
    # 3) Relleno MMQ completo
    # -----------------------------------------------------
    if show_mmq_fill:
        mmq_kwargs = dict(
            fig=fig,
            triangles=triangles,
            sphere_radius=sphere_radius,
            guard_wire_inputs=guard_wire_inputs,
            ns=UI_MMQ_PATCH_N,
            nt=UI_MMQ_PATCH_N,
            opacity=0.70
        )

        if function_accepts_argument(add_all_mmq_patches_to_fig, "registry_result"):
            mmq_kwargs["registry_result"] = registry_result

        fig = add_all_mmq_patches_to_fig(**mmq_kwargs)

    # -----------------------------------------------------
    # 4) Construir y filtrar MMM
    # -----------------------------------------------------
    selected_mmm_records = []
    rejected_mmm_records = []

    if show_filtered_mmm_fill:
        mmm_records = build_all_mmm_patch_records(
            triangles=triangles,
            sphere_radius=sphere_radius,
            guard_wire_inputs=guard_wire_inputs,
            registry_result=registry_result,
            ns=UI_MMM_PATCH_N,
            nt=UI_MMM_PATCH_N
        )

        selected_mmm_records, rejected_mmm_records = filter_mmm_by_zmin_preserve_xy_coverage(
            mmm_records=mmm_records,
            grid_n=grid_n,
            min_new_cells=1
        )

        fig = add_selected_mmm_patches_to_fig(
            fig=fig,
            selected_mmm_records=selected_mmm_records,
            opacity=0.72
        )

    # -----------------------------------------------------
    # 5) Dibujar SOLO crestas/cables/segmentos visibles
    # -----------------------------------------------------
    visible_triangles_for_edges = extract_visible_triangles_for_edges(
        original_triangles=triangles,
        selected_mmm_records=selected_mmm_records,
        keep_mmq=True
    )

    tri_nodes_to_plot = tri_nodes

    crests_kwargs = dict(
        fig=fig,
        tri_nodes=tri_nodes_to_plot,
        triangles=visible_triangles_for_edges,
        sphere_radius=sphere_radius,
        guard_wire_inputs=guard_wire_inputs,
        show_mmm_borders=show_mmm_borders,
        show_mm_crests=show_mm_crests,
        show_mq_segments=show_mq_segments,
        show_q_points=show_q_points
    )

    if function_accepts_argument(add_triangles_crests_and_mq_to_existing_fig, "registry_result"):
        crests_kwargs["registry_result"] = registry_result

    fig = add_triangles_crests_and_mq_to_existing_fig(**crests_kwargs)

    # -----------------------------------------------------
    # 6) Equipos / cubos
    # -----------------------------------------------------
    if cube_inputs is not None:
        for cube in cube_inputs:
            fig = add_cube_to_fig(
                fig=fig,
                cube=cube,
                opacity=cube.get("opacity", 0.35)
            )

    # -----------------------------------------------------
    # 7) Plano base z = 0
    # -----------------------------------------------------
    all_x = [m.x for m in masts]
    all_y = [m.y for m in masts]

    if cube_inputs is not None:
        for cube in cube_inputs:
            all_x.extend([cube["x"], cube["x"] + cube["dx"]])
            all_y.extend([cube["y"], cube["y"] + cube["dy"]])

    max_a = max(effective_radius(m.h, sphere_radius) for m in masts)

    xmin = min(all_x) - max_a - 5
    xmax = max(all_x) + max_a + 5
    ymin = min(all_y) - max_a - 5
    ymax = max(all_y) + max_a + 5

    Xg, Yg = np.meshgrid(
        np.linspace(xmin, xmax, 2),
        np.linspace(ymin, ymax, 2)
    )

    fig.add_trace(go.Surface(
        x=Xg,
        y=Yg,
        z=np.zeros_like(Xg),
        showscale=False,
        opacity=0.15,
        name="Plano z=0",
        hoverinfo="skip"
    ))

    fig.update_layout(
        title="Modelo completo con capa superior MMM, cables de guarda y equipos",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="data"
        ),
        height=950,
        showlegend=True
    )

    fig.show()

    return fig, selected_mmm_records, rejected_mmm_records


from scipy.interpolate import griddata


import numpy as np


import plotly.graph_objects as go


def find_final_plotly_figure(preferred_names=None):
    """
    Busca automáticamente la figura final del modelo.

    Prioridad:
      1) nombres explícitos de figuras finales;
      2) cualquier objeto go.Figure disponible en globals().
    """

    if preferred_names is None:
        preferred_names = [
            "fig_superficies_mmq_mmm_13C",
            "fig_superficies_mmq_mmm",
            "fig_vertical_final",
            "fig_side_final",
            "fig_final",
            "final_fig",
            "fig"
        ]

    # -----------------------------------------------------
    # 1) Buscar por nombres conocidos
    # -----------------------------------------------------
    for name in preferred_names:
        obj = globals().get(name, None)

        if isinstance(obj, go.Figure):
            print(f"Figura final encontrada: {name}")
            return obj, name

    # -----------------------------------------------------
    # 2) Buscar cualquier go.Figure en globals()
    # -----------------------------------------------------
    figure_candidates = []

    for name, obj in globals().items():
        if isinstance(obj, go.Figure):
            figure_candidates.append((name, obj))

    if len(figure_candidates) > 0:
        # Se toma la última encontrada
        name, obj = figure_candidates[-1]
        print(f"Figura Plotly encontrada automáticamente: {name}")
        return obj, name

    print("No se encontró ninguna figura Plotly final.")
    return None, None


def trace_is_visible(trace):
    """
    Verifica si una traza de Plotly está visible.
    """
    visible = getattr(trace, "visible", True)

    if visible is False:
        return False

    if visible == "legendonly":
        return False

    return True


def is_ground_or_reference_surface(name, Z, tol=1e-9):
    """
    Evita usar superficies que no son cubierta:
      - plano de suelo;
      - plano z=0;
      - superficies de referencia.
    """

    name_low = str(name).lower()

    excluded_words = [
        "suelo",
        "ground",
        "plano",
        "plane",
        "referencia",
        "reference",
        "z=0",
        "base"
    ]

    if any(word in name_low for word in excluded_words):
        return True

    Z = np.asarray(Z, dtype=float)

    finite = np.isfinite(Z)

    if not np.any(finite):
        return True

    zmax = np.nanmax(Z[finite])
    zmin = np.nanmin(Z[finite])

    # Si toda la superficie está en z=0, no es cubierta.
    if abs(zmax) <= tol and abs(zmin) <= tol:
        return True

    return False


def prepare_surface_xyz_from_trace(trace):
    """
    Extrae X, Y, Z desde una traza go.Surface.
    """

    try:
        Z = np.asarray(trace.z, dtype=float)
    except Exception:
        return None

    if Z.ndim != 2:
        return None

    try:
        X = np.asarray(trace.x, dtype=float)
        Y = np.asarray(trace.y, dtype=float)
    except Exception:
        return None

    nr, nc = Z.shape

    # Caso 1: X,Y son matrices
    if X.ndim == 2 and Y.ndim == 2:
        if X.shape == Z.shape and Y.shape == Z.shape:
            return X, Y, Z

    # Caso 2: X,Y son vectores
    if X.ndim == 1 and Y.ndim == 1:
        if len(X) == nc and len(Y) == nr:
            Xg, Yg = np.meshgrid(X, Y)
            return Xg, Yg, Z

    return None


def aggregate_xy_keep_max_z(sx, sy, sz, decimals=9):
    """
    Agrupa puntos repetidos en XY y conserva la mayor Z.

    Esto representa la capa superior total.
    """

    sx = np.asarray(sx, dtype=float)
    sy = np.asarray(sy, dtype=float)
    sz = np.asarray(sz, dtype=float)

    finite = (
        np.isfinite(sx)
        & np.isfinite(sy)
        & np.isfinite(sz)
    )

    sx = sx[finite]
    sy = sy[finite]
    sz = sz[finite]

    if len(sx) == 0:
        return sx, sy, sz

    keys = np.round(np.column_stack([sx, sy]), decimals=decimals)

    best = {}

    for key_xy, x, y, z in zip(keys, sx, sy, sz):
        key = tuple(key_xy)

        if key not in best:
            best[key] = [x, y, z]
        else:
            if z > best[key][2]:
                best[key] = [x, y, z]

    arr = np.array(list(best.values()), dtype=float)

    return arr[:, 0], arr[:, 1], arr[:, 2]


def collect_shield_surface_points_from_final_fig(final_fig=None):
    """
    Toma la capa total directamente desde el gráfico final.

    Usa todas las trazas go.Surface visibles, excepto plano de suelo/referencia.
    """

    if final_fig is None:
        final_fig, fig_name = find_final_plotly_figure()
    else:
        fig_name = "figura entregada manualmente"

    xs, ys, zs = [], [], []
    used_traces = []

    if final_fig is None:
        return np.array([]), np.array([]), np.array([]), used_traces

    for idx, trace in enumerate(final_fig.data):

        trace_type = getattr(trace, "type", "")

        if trace_type != "surface":
            continue

        if not trace_is_visible(trace):
            continue

        name = getattr(trace, "name", f"surface_{idx}")

        prepared = prepare_surface_xyz_from_trace(trace)

        if prepared is None:
            continue

        X, Y, Z = prepared

        Z = np.maximum(Z, 0.0)

        if is_ground_or_reference_surface(name, Z):
            continue

        finite = (
            np.isfinite(X)
            & np.isfinite(Y)
            & np.isfinite(Z)
        )

        if not np.any(finite):
            continue

        xs.extend(X[finite].ravel())
        ys.extend(Y[finite].ravel())
        zs.extend(Z[finite].ravel())

        used_traces.append(str(name))

    sx = np.array(xs, dtype=float)
    sy = np.array(ys, dtype=float)
    sz = np.array(zs, dtype=float)

    sx, sy, sz = aggregate_xy_keep_max_z(sx, sy, sz)

    print("=========================================================")
    print("CAPA USADA PARA VERIFICACIÓN DESDE GRÁFICO FINAL")
    print("=========================================================")
    print(f"Figura usada          : {fig_name}")
    print(f"Trazas Surface usadas : {len(used_traces)}")
    print(f"Puntos de cubierta    : {len(sx)}")

    if len(used_traces) > 0:
        print("Trazas usadas:")
        for name in used_traces:
            print(f"  - {name}")

    return sx, sy, sz, used_traces


def sample_cube_surface_points(cube, n=15, include_bottom=False):
    """
    Muestrea puntos sobre:
      - cara superior;
      - cuatro caras laterales.

    No evalúa la cara inferior por defecto.
    """

    x0, y0, z0 = cube["x"], cube["y"], cube["z"]
    dx, dy, dz = cube["dx"], cube["dy"], cube["dz"]

    xs = np.linspace(x0, x0 + dx, n)
    ys = np.linspace(y0, y0 + dy, n)
    zs = np.linspace(z0, z0 + dz, n)

    pts = []

    # Cara superior
    for x in xs:
        for y in ys:
            pts.append([x, y, z0 + dz])

    # Laterales y = y0 / y0 + dy
    for x in xs:
        for z in zs:
            pts.append([x, y0, z])
            pts.append([x, y0 + dy, z])

    # Laterales x = x0 / x0 + dx
    for y in ys:
        for z in zs:
            pts.append([x0, y, z])
            pts.append([x0 + dx, y, z])

    # Cara inferior opcional
    if include_bottom:
        for x in xs:
            for y in ys:
                pts.append([x, y, z0])

    return np.array(pts, dtype=float)


def estimate_z_shield_global(sx, sy, sz, xy_points):
    """
    Interpola la altura de la capa total sobre los puntos XY del cubo.

    Método:
      1) linear;
      2) nearest para los NaN.
    """

    sx = np.asarray(sx, dtype=float)
    sy = np.asarray(sy, dtype=float)
    sz = np.asarray(sz, dtype=float)

    xy_points = np.asarray(xy_points, dtype=float)

    finite = (
        np.isfinite(sx)
        & np.isfinite(sy)
        & np.isfinite(sz)
    )

    sx = sx[finite]
    sy = sy[finite]
    sz = sz[finite]

    if len(sx) == 0:
        return np.full(xy_points.shape[0], np.nan, dtype=float)

    points = np.column_stack([sx, sy])

    # Interpolación lineal
    try:
        z_shield = griddata(
            points=points,
            values=sz,
            xi=xy_points,
            method="linear"
        )
    except Exception:
        z_shield = np.full(xy_points.shape[0], np.nan, dtype=float)

    # Fallback nearest
    nan_mask = np.isnan(z_shield)

    if np.any(nan_mask):
        try:
            z_shield[nan_mask] = griddata(
                points=points,
                values=sz,
                xi=xy_points[nan_mask],
                method="nearest"
            )
        except Exception:
            pass

    return z_shield


def check_cube_shielded_against_final_layer(
    cube,
    final_fig=None,
    margin=0.0,
    sample_n=15,
    include_bottom=False,
    verification_title="VERIFICACIÓN"
):
    """
    Verifica si el cubo está por debajo de la capa total resultante.
    """

    sx, sy, sz, used_traces = collect_shield_surface_points_from_final_fig(
        final_fig=final_fig
    )

    cube_pts = sample_cube_surface_points(
        cube=cube,
        n=sample_n,
        include_bottom=include_bottom
    )

    if len(sx) == 0:
        protected = np.zeros(len(cube_pts), dtype=bool)
        z_shield = np.full(len(cube_pts), np.nan, dtype=float)

        print("=========================================================")
        print(verification_title)
        print("=========================================================")
        print(f"Equipo: {cube.get('name', 'Equipo')}")
        print("No se encontraron puntos de cubierta para verificar.")
        print("RESULTADO: ❌ No se pudo verificar como apantallado.")

        return {
            "fully_shielded": False,
            "cube": cube,
            "cube_pts": cube_pts,
            "z_shield": z_shield,
            "protected": protected,
            "valid_surface": np.zeros(len(cube_pts), dtype=bool),
            "surface_points": {
                "x": sx,
                "y": sy,
                "z": sz
            },
            "used_traces": used_traces
        }

    z_shield = estimate_z_shield_global(
        sx=sx,
        sy=sy,
        sz=sz,
        xy_points=cube_pts[:, :2]
    )

    valid_surface = np.isfinite(z_shield)

    protected = (
        valid_surface
        & (cube_pts[:, 2] <= (z_shield - margin))
    )

    total = len(protected)
    ok = np.count_nonzero(protected)
    fail = total - ok
    invalid = np.count_nonzero(~valid_surface)

    fully_shielded = fail == 0

    excess = cube_pts[:, 2] - (z_shield - margin)
    excess[~valid_surface] = np.nan

    max_excess = np.nanmax(excess) if np.any(np.isfinite(excess)) else np.nan

    print("=========================================================")
    print(verification_title)
    print("=========================================================")
    print(f"Equipo: {cube.get('name', 'Equipo')}")
    print(f"Puntos de cubierta usados    : {len(sx)}")
    print(f"Puntos evaluados             : {total}")
    print(f"Puntos protegidos            : {ok}")
    print(f"Puntos no protegidos         : {fail}")
    print(f"Puntos sin altura interpolada: {invalid}")
    print(f"Margen aplicado              : {margin:.3f} m")

    if np.isfinite(max_excess):
        print(f"Máximo exceso sobre cubierta : {max_excess:.4f} m")
    else:
        print("Máximo exceso sobre cubierta : No calculable")

    if fully_shielded:
        print("RESULTADO: ✅ El equipo queda completamente apantallado.")
    else:
        print("RESULTADO: ❌ El equipo NO queda completamente apantallado.")

    return {
        "fully_shielded": fully_shielded,
        "cube": cube,
        "cube_pts": cube_pts,
        "z_shield": z_shield,
        "protected": protected,
        "valid_surface": valid_surface,
        "surface_points": {
            "x": sx,
            "y": sy,
            "z": sz
        },
        "used_traces": used_traces,
        "margin": margin,
        "sample_n": sample_n,
        "max_excess": max_excess
    }



# Resolución interna para UI. Puede ser ajustada desde run_shielding_model_ui.
UI_MMQ_PATCH_N = 45
UI_MMM_PATCH_N = 45

# =========================================================
# FUNCIÓN PRINCIPAL LIMPIA PARA UI
# =========================================================

import contextlib as _contextlib
import io as _io
import math as _math


def compute_sphere_radius(BIL=350, Zs=300, k=1.2):
    Is = (2.2 * float(BIL)) / float(Zs)
    return float(k) * 8.0 * Is**0.65


def make_cube(name, x, y, z, dx, dy, dz, color="gray"):
    return {
        "name": str(name),
        "x": float(x), "y": float(y), "z": float(z),
        "dx": float(dx), "dy": float(dy), "dz": float(dz),
        "color": color,
    }


def _build_all_points_from_useful_q(masts, results):
    all_points = []
    for m in masts:
        all_points.append(Mast(x=m.x, y=m.y, h=m.h))

    seen_q_points = set()
    for i, data in results.items():
        mi = masts[i]
        useful_ranges = data["useful_intervals"]
        for pr in data["pair_results"]:
            for q in [pr.q_plus, pr.q_minus]:
                angle_q = normalize_0_2pi(atan2(q[1] - mi.y, q[0] - mi.x))
                is_useful = any(low - 1e-9 <= angle_q <= high + 1e-9 for low, high in useful_ranges)
                if is_useful:
                    q_rounded = (round(q[0], 6), round(q[1], 6))
                    if q_rounded not in seen_q_points:
                        seen_q_points.add(q_rounded)
                        all_points.append(Mast(x=q[0], y=q[1], h=0.0))
    return all_points


def _summarize_check_result(result):
    protected = result.get("protected", [])
    valid_surface = result.get("valid_surface", [])
    total = int(len(protected)) if protected is not None else 0
    ok = int(np.count_nonzero(protected)) if total else 0
    invalid = int(np.count_nonzero(~np.asarray(valid_surface, dtype=bool))) if total else 0
    fail = max(total - ok, 0)
    max_excess = result.get("max_excess", None)
    try:
        max_excess = None if max_excess is None or not np.isfinite(max_excess) else float(max_excess)
    except Exception:
        max_excess = None
    cube = result.get("cube", {}) or {}
    fully = bool(result.get("fully_shielded", False))

    # Extract unprotected critical points for the recommendation engine
    critical_points = []
    worst_point = None
    cube_pts_raw = result.get("cube_pts")
    z_shield_raw = result.get("z_shield")
    margin_raw = float(result.get("margin", 0.0) or 0.0)
    if cube_pts_raw is not None and z_shield_raw is not None and total > 0:
        try:
            vs = np.asarray(valid_surface, dtype=bool)
            pr = np.asarray(protected, dtype=bool)
            for i in range(len(cube_pts_raw)):
                if vs[i] and not pr[i]:
                    excess_m = float(cube_pts_raw[i, 2] - (z_shield_raw[i] - margin_raw))
                    critical_points.append({
                        "x": round(float(cube_pts_raw[i, 0]), 3),
                        "y": round(float(cube_pts_raw[i, 1]), 3),
                        "z": round(float(cube_pts_raw[i, 2]), 3),
                        "excess_m": round(excess_m, 3),
                    })
        except Exception:
            pass
    if critical_points:
        worst_point = max(critical_points, key=lambda p: p["excess_m"])

    return {
        "equipment_name": cube.get("name", "Equipo"),
        "fully_shielded": fully,
        "status_text": "El equipo queda completamente apantallado." if fully else "El equipo NO queda completamente apantallado.",
        "points_evaluated": total,
        "points_protected": ok,
        "points_not_protected": fail,
        "points_without_interpolation": invalid,
        "margin": float(result.get("margin", 0.0)) if result.get("margin", None) is not None else 0.0,
        "sample_n": int(result.get("sample_n", 0)) if result.get("sample_n", None) is not None else None,
        "max_excess_m": max_excess,
        "used_surface_traces": list(result.get("used_traces", []) or []),
        "cube": dict(cube),
        "critical_points": critical_points,
        "worst_point": worst_point,
    }


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
    show_final=True,
    final_grid_n=120,
    mmq_patch_n=45,
    mmm_patch_n=45,
    return_raw=True,
):
    """
    Ejecuta el modelo completo y devuelve solo el gráfico final y la verificación.

    Parámetros:
      mast_inputs: [(x, y, h), ...]
      cube_inputs: [{name, x, y, z, dx, dy, dz, color?}, ...]
      guard_wire_pairs: [(i, j), ...]
      S: radio de esfera opcional. Si no se pasa, se calcula con BIL, Zs, k.
    """
    global guard_wire_inputs, results_input_5
    global mast_inputs_global, cube_inputs_global

    if cube_inputs is None:
        cube_inputs = []
    if guard_wire_pairs is None:
        guard_wire_pairs = []

    # Validación básica de entradas.
    mast_inputs_clean = []
    for idx, item in enumerate(mast_inputs):
        if len(item) != 3:
            raise ValueError(f"El mástil {idx} debe tener formato (x, y, h).")
        x, y, h = map(float, item)
        if h <= 0:
            raise ValueError(f"La altura del mástil {idx} debe ser mayor que cero.")
        mast_inputs_clean.append((x, y, h))

    cube_inputs_clean = []
    for idx, cube in enumerate(cube_inputs):
        item = dict(cube)
        item["name"] = str(item.get("name", f"Equipo {idx+1}"))
        for key in ["x", "y", "z", "dx", "dy", "dz"]:
            if key not in item:
                raise ValueError(f"Falta '{key}' en el equipo {idx}.")
            item[key] = float(item[key])
        if item["dx"] <= 0 or item["dy"] <= 0 or item["dz"] <= 0:
            raise ValueError(f"dx, dy y dz deben ser mayores que cero en el equipo {idx}.")
        cube_inputs_clean.append(item)

    guard_wire_pairs_clean = [tuple(sorted((int(a), int(b)))) for a, b in guard_wire_pairs]

    # Variables globales que algunas funciones heredadas consultan.
    globals()["mast_inputs"] = mast_inputs_clean
    globals()["cube_inputs"] = cube_inputs_clean
    globals()["BIL"] = float(BIL)
    globals()["Zs"] = float(Zs)
    globals()["k"] = float(k)
    globals()["S"] = float(S) if S is not None else compute_sphere_radius(BIL, Zs, k)
    globals()["guard_wire_pairs"] = guard_wire_pairs_clean
    globals()["UI_MMQ_PATCH_N"] = int(mmq_patch_n)
    globals()["UI_MMM_PATCH_N"] = int(mmm_patch_n)

    # Validar guardas con la lógica existente del notebook.
    guard_wire_pairs_valid, guard_wire_inputs_valid, guard_component_info = validate_guard_wire_selection(guard_wire_pairs_clean)
    globals()["guard_wire_pairs"] = guard_wire_pairs_valid
    globals()["guard_wire_inputs"] = guard_wire_inputs_valid
    guard_wire_inputs = guard_wire_inputs_valid

    # 1) Modelo base y puntos Q útiles.
    masts = [Mast(x, y, h) for x, y, h in mast_inputs_clean]
    results = useful_angle_ranges_for_each_mast(masts, globals()["S"])
    all_points = _build_all_points_from_useful_q(masts, results)

    # 2) Triángulos candidatos y filtros geométricos iniciales.
    tri_nodes = build_candidate_nodes(all_points)
    candidate_triangles, degenerate_count, ground_count = generate_all_candidate_triangles(tri_nodes)

    kept_triangles_1, removed_MQQ_triangles = filter_out_mqq_triangles(candidate_triangles)

    kept_triangles_2, removed_triangles_2 = filter_mmq_by_surviving_original_useful_edges(
        triangles=kept_triangles_1,
        original_results=results,
        updated_results=results,
        angle_tol=1e-4,
    )
    tri_nodes_after_mmq_filter = build_active_tri_nodes_from_triangles(tri_nodes, kept_triangles_2)

    (
        kept_triangles_3,
        removed_triangles_4,
        results_after_closed_q_filter,
        tri_nodes_after_closed_q_filter,
        closed_q_cycles_log,
        closed_q_cuts_log,
        forbidden_mq_edges_4,
        rejected_closed_q_debug_4,
    ) = filter_closed_inner_q_cells_4(
        input_triangles=kept_triangles_2,
        tri_nodes_input=tri_nodes_after_mmq_filter,
        masts=masts,
        results_obj=results,
        sphere_radius=globals()["S"],
    )

    results_input_5 = results_after_closed_q_filter
    globals()["results_input_5"] = results_input_5

    (
        kept_triangles_4,
        removed_mmm_by_single_mast_overlap_5,
        tri_nodes_after_mmm_overlap_filter,
        overlap_log_5,
        invasion_points_5,
    ) = filter_mmm_by_single_mast_layer_overlap_5(
        input_triangles=kept_triangles_3,
        tri_nodes_input=tri_nodes_after_closed_q_filter,
        masts=masts,
        results_obj=results_input_5,
        sphere_radius=globals()["S"],
        divisions=INTERIOR_SAMPLE_DIVISIONS_5,
        barycentric_margin=BARYCENTRIC_EDGE_MARGIN_5,
        min_hits=MIN_INTERIOR_HITS_5,
        radial_margin=RADIAL_MARGIN_5,
        angular_margin=ANGULAR_MARGIN_5,
        count_unique_sample_points=COUNT_UNIQUE_SAMPLE_POINTS_5,
    )

    kept_triangles_5, kept_mmm_6, removed_mmm_6, mmq_triangles_6, other_triangles_6 = filter_mmm_overlapping_mmq_in_xy(
        triangles=kept_triangles_4,
        min_common_points=1,
        divisions=14,
    )

    # 3) Registro de crestas, guardas y filtros 13C/13D.
    resultado_crestas_base = build_base_crest_registry(
        tri_nodes=tri_nodes_after_mmm_overlap_filter,
        triangles=kept_triangles_5,
        sphere_radius=globals()["S"],
        guard_wire_inputs=guard_wire_inputs,
        npts=220,
    )

    resultado_crestas_final = apply_guard_overrides_to_registry(
        base_registry_result=resultado_crestas_base,
        sphere_radius=globals()["S"],
        guard_wire_inputs=guard_wire_inputs,
    )

    resultado_crestas_filtro1 = apply_filter1_independent_examples_competition(
        base_registry_result=resultado_crestas_final,
    )

    resultado_crestas_filtro2, kept_triangles_filtro2, tri_nodes_filtro2 = apply_filter2_ground_overlap(
        base_registry_result=resultado_crestas_filtro1,
        triangles=kept_triangles_5,
        tri_nodes=tri_nodes_after_mmm_overlap_filter,
        guard_wire_inputs=guard_wire_inputs,
    )

    resultado_crestas_filtro3, kept_triangles_filtro3, tri_nodes_filtro3 = apply_filter3_special_crests_vs_mmm_crests(
        base_registry_result=resultado_crestas_filtro2,
        triangles=kept_triangles_filtro2,
        tri_nodes=tri_nodes_filtro2,
    )

    resultado_crestas_final_13D, kept_triangles_13D, tri_nodes_13D = apply_filter13D_crossed_crests_by_zmin(
        base_registry_result=resultado_crestas_filtro3,
        triangles=kept_triangles_filtro3,
        tri_nodes=tri_nodes_filtro3,
        guard_wire_inputs=guard_wire_inputs,
    )

    resultado_crestas_final_13C = resultado_crestas_final_13D
    kept_triangles_13C = kept_triangles_13D
    tri_nodes_13C = tri_nodes_13D

    # 4) Gráfico final únicamente.
    original_show = go.Figure.show
    if not show_final:
        go.Figure.show = lambda self, *args, **kwargs: None
    try:
        fig_superficies_mmq_mmm_13C, selected_mmm_records, rejected_mmm_records = plot_full_surface_with_filtered_mmm_layer_clean_edges(
            masts=masts,
            sphere_radius=globals()["S"],
            results=results_input_5,
            tri_nodes=tri_nodes_13C,
            triangles=kept_triangles_13C,
            guard_wire_inputs=guard_wire_inputs,
            registry_result=resultado_crestas_final_13C,
            grid_n=int(final_grid_n),
            show_single_mast_surfaces=True,
            show_red_q_edges=True,
            show_mmq_fill=True,
            show_filtered_mmm_fill=True,
            show_mmm_borders=True,
            show_mm_crests=True,
            show_mq_segments=True,
            show_q_points=True,
            cube_inputs=cube_inputs_clean,
        )
    finally:
        go.Figure.show = original_show

    # 5) Verificación contra la figura final.
    shield_check_results = []
    for cube in cube_inputs_clean:
        with _contextlib.redirect_stdout(_io.StringIO()):
            result = check_cube_shielded_against_final_layer(
                cube=cube,
                final_fig=fig_superficies_mmq_mmm_13C,
                margin=float(verification_margin),
                sample_n=int(verification_sample_n),
                include_bottom=bool(include_bottom),
                verification_title="VERIFICACIÓN DE APANTALLAMIENTO",
            )
        shield_check_results.append(result)

    verification = [_summarize_check_result(r) for r in shield_check_results]

    out = {
        "fig": fig_superficies_mmq_mmm_13C,
        "fig_json": fig_superficies_mmq_mmm_13C.to_json() if fig_superficies_mmq_mmm_13C is not None else None,
        "verification": verification,
        "verification_raw": shield_check_results,
        "S": globals()["S"],
        "guard_component_info": guard_component_info,
    }

    if return_raw:
        out["raw"] = {
            "masts": masts,
            "results": results,
            "all_points": all_points,
            "tri_nodes": tri_nodes_13C,
            "triangles": kept_triangles_13C,
            "registry_result": resultado_crestas_final_13C,
            "selected_mmm_records": selected_mmm_records,
            "rejected_mmm_records": rejected_mmm_records,
            "removed": {
                "MQQ": removed_MQQ_triangles,
                "MMQ_edge_filter": removed_triangles_2,
                "closed_q": removed_triangles_4,
                "mmm_single_mast_overlap": removed_mmm_by_single_mast_overlap_5,
                "mmm_mmq_overlap": removed_mmm_6,
            },
        }

    return out

# =========================================================
# WRAPPER SILENCIOSO PARA UI
# =========================================================

_run_shielding_model_ui_core = run_shielding_model_ui

def run_shielding_model_ui(*args, suppress_output=True, **kwargs):
    """Versión pública: por defecto oculta textos intermedios y devuelve solo datos."""
    if suppress_output:
        with _contextlib.redirect_stdout(_io.StringIO()):
            return _run_shielding_model_ui_core(*args, **kwargs)
    return _run_shielding_model_ui_core(*args, **kwargs)
