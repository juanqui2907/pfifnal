# -*- coding: utf-8 -*-
import os
import sys
import types
import streamlit as st

_THIS_DIR   = os.path.dirname(os.path.abspath(__file__))
_MODEL_FILE = os.path.join(_THIS_DIR, "modelo_apantallamiento_ui_extraido (1).py")

def _mock_ipython():
    if "IPython" in sys.modules:
        return
    ipython_pkg = types.ModuleType("IPython")
    display_mod = types.ModuleType("IPython.display")
    display_mod.display      = lambda *a, **kw: None
    display_mod.clear_output = lambda *a, **kw: None
    ipython_pkg.display = display_mod
    sys.modules["IPython"]         = ipython_pkg
    sys.modules["IPython.display"] = display_mod

@st.cache_resource(show_spinner="Cargando modelo...")
def _load_model():
    import importlib.util
    _mock_ipython()
    spec = importlib.util.spec_from_file_location("shielding_model", _MODEL_FILE)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

st.set_page_config(page_title="Apantallamiento", page_icon=":zap:", layout="wide")
st.title("Modelo de Apantallamiento por Esfera Rodante")

# ── Helpers ──────────────────────────────────────────────────────────────────
def _init_mast(i, x=0.0, y=0.0, h=10.0):
    if ("mast_%d_x" % i) not in st.session_state:
        st.session_state["mast_%d_x" % i] = float(x)
    if ("mast_%d_y" % i) not in st.session_state:
        st.session_state["mast_%d_y" % i] = float(y)
    if ("mast_%d_h" % i) not in st.session_state:
        st.session_state["mast_%d_h" % i] = float(h)

def _init_cube(i, name="", x=0.0, y=0.0, z=0.0, dx=3.0, dy=3.0, dz=3.0, color="blue"):
    defaults = [
        ("cube_%d_name" % i, name),
        ("cube_%d_x" % i,    float(x)),
        ("cube_%d_y" % i,    float(y)),
        ("cube_%d_z" % i,    float(z)),
        ("cube_%d_dx" % i,   float(dx)),
        ("cube_%d_dy" % i,   float(dy)),
        ("cube_%d_dz" % i,   float(dz)),
        ("cube_%d_color" % i, color),
    ]
    for key, val in defaults:
        if key not in st.session_state:
            st.session_state[key] = val

# ── Inicializacion unica ──────────────────────────────────────────────────────
if "n_masts" not in st.session_state:
    st.session_state.n_masts = 4
    _init_mast(0,  0.0,  0.0, 20.0)
    _init_mast(1, 30.0,  0.0, 20.0)
    _init_mast(2, 30.0, 30.0, 20.0)
    _init_mast(3,  0.0, 30.0, 20.0)

if "n_cubes" not in st.session_state:
    st.session_state.n_cubes = 1
    _init_cube(0, name="Transformador 1", x=5.0, y=5.0, z=0.0,
               dx=5.0, dy=5.0, dz=4.0, color="blue")

if "guard_pairs" not in st.session_state:
    st.session_state.guard_pairs = []

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Parametros electricos")
    BIL = st.number_input("BIL (kV)",            min_value=1.0,  value=350.0, step=10.0)
    Zs  = st.number_input("Zs (ohm)",            min_value=1.0,  value=300.0, step=10.0)
    k   = st.number_input("k (factor de forma)", min_value=0.01, value=1.2,   step=0.05)
    S_manual = st.checkbox("Ingresar radio de esfera manualmente")
    S_val = None
    if S_manual:
        S_val = st.number_input("Radio de esfera S (m)", min_value=0.1, value=30.0, step=0.5)
    st.divider()
    st.header("Verificacion")
    margin         = st.number_input("Margen de verificacion (m)", value=0.0, step=0.1)
    sample_n       = st.slider("Puntos de muestreo", 5, 30, 15)
    include_bottom = st.checkbox("Incluir cara inferior del equipo", value=False)
    st.divider()
    st.header("Resolucion del grafico")
    grid_n = st.slider("Resolucion de grilla", 40, 200, 120, step=10)
    mmq_n  = st.slider("Parches MMQ", 20, 80, 45, step=5)
    mmm_n  = st.slider("Parches MMM", 20, 80, 45, step=5)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_masts, tab_equipos, tab_guardas, tab_resultados = st.tabs([
    "Mastiles", "Equipos", "Cables de guarda", "Resultados"
])

# ── TAB 1: Mastiles ───────────────────────────────────────────────────────────
with tab_masts:
    st.subheader("Mastiles pararrayos")
    st.caption("El indice empieza en 0. Edita directamente cada celda.")

    c1, c2, _ = st.columns([1, 1, 4])
    if c1.button("+ Agregar mastil"):
        i = st.session_state.n_masts
        _init_mast(i)
        st.session_state.n_masts += 1
        st.rerun()
    if c2.button("- Eliminar ultimo") and st.session_state.n_masts > 1:
        st.session_state.n_masts -= 1
        st.rerun()

    hdr = st.columns([0.6, 2.5, 2.5, 2.5])
    hdr[0].markdown("**#**")
    hdr[1].markdown("**X (m)**")
    hdr[2].markdown("**Y (m)**")
    hdr[3].markdown("**Altura h (m)**")

    for i in range(st.session_state.n_masts):
        _init_mast(i)
        cols = st.columns([0.6, 2.5, 2.5, 2.5])
        cols[0].markdown("**M%d**" % i)
        cols[1].number_input("x", key=("mast_%d_x" % i), label_visibility="collapsed", step=0.5)
        cols[2].number_input("y", key=("mast_%d_y" % i), label_visibility="collapsed", step=0.5)
        cols[3].number_input("h", key=("mast_%d_h" % i), label_visibility="collapsed",
                             step=0.5, min_value=0.01)

    st.info("Total de mastiles: **%d**" % st.session_state.n_masts)

# ── TAB 2: Equipos ────────────────────────────────────────────────────────────
with tab_equipos:
    st.subheader("Equipos a proteger")
    st.caption("(x, y, z) = esquina inferior  |  (dx, dy, dz) = dimensiones")

    c1, c2, _ = st.columns([1.2, 1.5, 4])
    if c1.button("+ Agregar equipo"):
        i = st.session_state.n_cubes
        _init_cube(i, name=("Equipo %d" % (i + 1)))
        st.session_state.n_cubes += 1
        st.rerun()
    if c2.button("- Eliminar ultimo equipo") and st.session_state.n_cubes > 0:
        st.session_state.n_cubes -= 1
        st.rerun()

    if st.session_state.n_cubes == 0:
        st.info("No hay equipos. Agrega al menos uno para verificar el apantallamiento.")
    else:
        for i in range(st.session_state.n_cubes):
            _init_cube(i, name=("Equipo %d" % (i + 1)))
            label = st.session_state.get("cube_%d_name" % i, "Equipo %d" % i)
            with st.expander("Equipo %d - %s" % (i, label), expanded=True):
                st.text_input("Nombre", key=("cube_%d_name" % i))
                r1 = st.columns(3)
                r1[0].number_input("X (m)",  key=("cube_%d_x"  % i), step=0.5)
                r1[1].number_input("Y (m)",  key=("cube_%d_y"  % i), step=0.5)
                r1[2].number_input("Z (m)",  key=("cube_%d_z"  % i), step=0.5)
                r2 = st.columns(3)
                r2[0].number_input("dx (m)", key=("cube_%d_dx" % i), step=0.5, min_value=0.01)
                r2[1].number_input("dy (m)", key=("cube_%d_dy" % i), step=0.5, min_value=0.01)
                r2[2].number_input("dz (m)", key=("cube_%d_dz" % i), step=0.5, min_value=0.01)
                st.text_input("Color Plotly (ej: blue, red, green)", key=("cube_%d_color" % i))

# ── TAB 3: Cables de guarda ───────────────────────────────────────────────────
with tab_guardas:
    st.subheader("Cables de guarda")
    st.caption("Conecta pares de mastiles. Los indices corresponden a los mastiles definidos arriba.")

    n = st.session_state.n_masts
    opts = [
        "M%d (x=%.1f, y=%.1f, h=%.1f)" % (
            i,
            st.session_state.get("mast_%d_x" % i, 0),
            st.session_state.get("mast_%d_y" % i, 0),
            st.session_state.get("mast_%d_h" % i, 0),
        )
        for i in range(n)
    ]

    cg1, cg2, cg3 = st.columns([2, 2, 1])
    g_from = cg1.selectbox("Desde mastil", range(n), format_func=lambda i: opts[i], key="g_from")
    g_to   = cg2.selectbox("Hasta mastil", range(n), format_func=lambda i: opts[i], key="g_to")
    cg3.write("")
    cg3.write("")
    if cg3.button("+ Agregar"):
        if g_from != g_to:
            pair = tuple(sorted((g_from, g_to)))
            if pair not in [tuple(p) for p in st.session_state.guard_pairs]:
                st.session_state.guard_pairs.append(list(pair))
                st.rerun()
            else:
                st.warning("Ese par ya existe.")
        else:
            st.warning("Los dos mastiles deben ser distintos.")

    if st.session_state.guard_pairs:
        st.markdown("**Pares activos:**")
        for idx, pair in enumerate(st.session_state.guard_pairs):
            i, j = pair
            lc, rc = st.columns([5, 1])
            lc.markdown(
                "**M%d** (x=%.1f, y=%.1f)  <-->  **M%d** (x=%.1f, y=%.1f)" % (
                    i, st.session_state.get("mast_%d_x" % i, 0),
                       st.session_state.get("mast_%d_y" % i, 0),
                    j, st.session_state.get("mast_%d_x" % j, 0),
                       st.session_state.get("mast_%d_y" % j, 0),
                )
            )
            if rc.button("X", key=("rm_%d" % idx)):
                st.session_state.guard_pairs.pop(idx)
                st.rerun()
    else:
        st.info("Sin cables de guarda (opcional).")

# ── TAB 4: Resultados ─────────────────────────────────────────────────────────
with tab_resultados:
    st.subheader("Resultados del modelo")

    rc, _ = st.columns([2, 6])
    run_btn = rc.button("Ejecutar modelo", type="primary", use_container_width=True)

    if run_btn:
        mast_inputs, ok = [], True
        for i in range(st.session_state.n_masts):
            x = st.session_state.get("mast_%d_x" % i, 0.0)
            y = st.session_state.get("mast_%d_y" % i, 0.0)
            h = st.session_state.get("mast_%d_h" % i, 10.0)
            if float(h) <= 0:
                st.error("Mastil %d: la altura debe ser > 0." % i)
                ok = False
            else:
                mast_inputs.append((float(x), float(y), float(h)))

        cube_inputs = []
        for i in range(st.session_state.n_cubes):
            try:
                cube_inputs.append({
                    "name":  st.session_state.get("cube_%d_name"  % i, "Equipo %d" % (i+1)),
                    "x":     float(st.session_state.get("cube_%d_x"  % i, 0.0)),
                    "y":     float(st.session_state.get("cube_%d_y"  % i, 0.0)),
                    "z":     float(st.session_state.get("cube_%d_z"  % i, 0.0)),
                    "dx":    float(st.session_state.get("cube_%d_dx" % i, 3.0)),
                    "dy":    float(st.session_state.get("cube_%d_dy" % i, 3.0)),
                    "dz":    float(st.session_state.get("cube_%d_dz" % i, 3.0)),
                    "color": st.session_state.get("cube_%d_color" % i, "blue"),
                })
            except Exception as e:
                st.error("Equipo %d: dato invalido - %s" % (i, e))
                ok = False

        guard_pairs = [tuple(p) for p in st.session_state.guard_pairs]

        if ok and not mast_inputs:
            st.error("Debes ingresar al menos un mastil.")
            ok = False

        if ok:
            with st.spinner("Ejecutando modelo... esto puede tardar unos segundos."):
                try:
                    model  = _load_model()
                    result = model.run_shielding_model_ui(
                        mast_inputs=mast_inputs,
                        cube_inputs=cube_inputs or None,
                        BIL=BIL, Zs=Zs, k=k, S=S_val,
                        guard_wire_pairs=guard_pairs or None,
                        verification_margin=margin,
                        verification_sample_n=sample_n,
                        include_bottom=include_bottom,
                        show_final=False,
                        final_grid_n=grid_n,
                        mmq_patch_n=mmq_n,
                        mmm_patch_n=mmm_n,
                        return_raw=False,
                        suppress_output=True,
                    )
                    st.session_state["last_result"] = result
                except Exception as e:
                    st.error("Error al ejecutar el modelo: %s" % e)
                    import traceback
                    with st.expander("Detalle del error"):
                        st.code(traceback.format_exc())

    if "last_result" in st.session_state:
        result = st.session_state["last_result"]
        S_used = result.get("S")
        if S_used is not None:
            st.success("Modelo ejecutado - Radio de esfera rodante S = %.2f m" % S_used)

        st.markdown("### Visualizacion 3D")
        fig = result.get("fig")
        if fig is not None:
            fig.update_layout(height=650)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No se genero grafico.")

        verification = result.get("verification", [])
        if verification:
            st.markdown("### Verificacion de apantallamiento")
            for v in verification:
                nombre   = v.get("equipment_name", "Equipo")
                shielded = v.get("fully_shielded", False)
                status   = v.get("status_text", "")
                pts_eval = v.get("points_evaluated", 0)
                pts_ok   = v.get("points_protected", 0)
                pts_fail = v.get("points_not_protected", 0)
                pts_inv  = v.get("points_without_interpolation", 0)
                max_exc  = v.get("max_excess_m")
                exc_str  = "N/A" if max_exc is None else "%.3f m" % max_exc
                bg   = "#d4edda" if shielded else "#f8d7da"
                bord = "#28a745" if shielded else "#dc3545"
                icon = "APANTALLADO" if shielded else "NO APANTALLADO"
                html = (
                    "<div style='background:%s;border-left:5px solid %s;"
                    "padding:14px 18px;border-radius:6px;margin-bottom:12px;'>"
                    "<h4 style='margin:0 0 6px 0;'>[%s] %s</h4>"
                    "<p style='margin:0 0 8px 0;'>%s</p>"
                    "<table style='width:100%%;border-collapse:collapse;font-size:0.9em;'>"
                    "<tr>"
                    "<td style='padding:2px 10px;'><b>Puntos evaluados:</b> %d</td>"
                    "<td style='padding:2px 10px;'><b>Protegidos:</b> %d</td>"
                    "<td style='padding:2px 10px;'><b>No protegidos:</b> %d</td>"
                    "</tr><tr>"
                    "<td style='padding:2px 10px;'><b>Sin interpolacion:</b> %d</td>"
                    "<td style='padding:2px 10px;'><b>Exceso max.:</b> %s</td>"
                    "<td></td>"
                    "</tr></table></div>"
                ) % (bg, bord, icon, nombre, status,
                     pts_eval, pts_ok, pts_fail, pts_inv, exc_str)
                st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("Configura los mastiles y equipos, luego presiona Ejecutar modelo.")
