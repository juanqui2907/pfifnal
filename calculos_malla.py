"""
calculos_malla.py — Cálculos IEEE Std 80-2013 · Malla de Puesta a Tierra
=========================================================================
Organización fiel a las hojas del Excel MALLA_VERSIONFINALCOMPLETA.xlsx.

Códigos de forma (E4 del Excel):
  1 = Rectangular / Cuadrada
  2 = Triangular Equilátero
  3 = Triangular Isósceles
  4 = Triangular Rectángulo
  5 = Escaleno
  6 = Forma L
  7 = Forma T

Códigos de ubicación de varillas (E50):
  0 = Sin varillas
  1 = Solo en las esquinas
  2 = En todo el perímetro
  3 = En todas las intersecciones
"""

import math

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 0 · TABLAS DE REFERENCIA
# ══════════════════════════════════════════════════════════════════════════════

# Tabla 1 — IEEE Std 80-2013: Constantes de material del conductor
# Columnas: alpha_r [1/°C], K0 [°C], Tm [°C], rho_r [μΩ·cm], TCAP [J/(cm³·°C)]
MATERIALES_CONDUCTOR = {
    1:  {"nombre": "Cobre recocido (soft-drawn)",              "alpha_r": 0.00393, "K0": 234, "Tm": 1083, "rho_r":  1.72, "TCAP": 3.4},
    2:  {"nombre": "Cobre comercial (hard-drawn)",             "alpha_r": 0.00381, "K0": 242, "Tm": 1084, "rho_r":  1.78, "TCAP": 3.4},
    3:  {"nombre": "Alambre cobre-cladded (40% IACS)",         "alpha_r": 0.00378, "K0": 245, "Tm": 1084, "rho_r":  4.40, "TCAP": 3.8},
    4:  {"nombre": "Alambre cobre-cladded (30% IACS)",         "alpha_r": 0.00378, "K0": 245, "Tm": 1084, "rho_r":  5.86, "TCAP": 3.8},
    5:  {"nombre": "Varilla cobre-cladded (17% IACS)",         "alpha_r": 0.00378, "K0": 245, "Tm": 1084, "rho_r": 10.10, "TCAP": 3.8},
    6:  {"nombre": "Alambre acero-alum. cladded (20.3% IACS)", "alpha_r": 0.00360, "K0": 258, "Tm":  657, "rho_r":  8.48, "TCAP": 3.561},
    7:  {"nombre": "Acero 1020",                               "alpha_r": 0.00377, "K0": 245, "Tm": 1510, "rho_r": 15.90, "TCAP": 3.8},
    8:  {"nombre": "Varilla acero inox. cladded (9.8% IACS)",  "alpha_r": 0.00377, "K0": 245, "Tm": 1400, "rho_r": 17.50, "TCAP": 4.4},
    9:  {"nombre": "Varilla acero galvanizado (zinc-coated)",   "alpha_r": 0.00320, "K0": 293, "Tm":  419, "rho_r": 20.10, "TCAP": 3.9},
    10: {"nombre": "Acero inoxidable 304",                     "alpha_r": 0.00130, "K0": 749, "Tm": 1400, "rho_r": 72.00, "TCAP": 4.0},
}

# Calibres comerciales disponibles (de menor a mayor área)
CONDUCTORES_COMERCIALES = [
    {"kcmil": 133.1, "AWG": "2/0", "area_mm2":  67.44, "diametro_m": 0.0093},
    {"kcmil": 167.8, "AWG": "3/0", "area_mm2":  85.03, "diametro_m": 0.0104},
    {"kcmil": 211.6, "AWG": "4/0", "area_mm2": 107.22, "diametro_m": 0.0117},
    {"kcmil": 250.0, "AWG": None,  "area_mm2": 126.68, "diametro_m": 0.0127},
    {"kcmil": 300.0, "AWG": None,  "area_mm2": 152.01, "diametro_m": 0.0139},
    {"kcmil": 350.0, "AWG": None,  "area_mm2": 177.35, "diametro_m": 0.0150},
]

# Tabla 7 — IEEE Std 80-2013: Resistividades típicas de materiales superficiales
# Columnas: rho_seco_min, rho_seco_max, rho_hum_min, rho_hum_max  [Ω·m]
# N/A → None
MATERIALES_SUPERFICIE = {
    1:  {"desc": "Crusher run granite with fines (N.C.)",
         "seco_min": 140e6,   "seco_max": 140e6,   "hum_min": 1300,   "hum_max": 1300},
    2:  {"desc": "1.5 in crusher run granite (Ga.)",
         "seco_min": 4000,    "seco_max": 4000,    "hum_min": 1200,   "hum_max": 1200},
    3:  {"desc": "0.75-1 in granite with fines (Calif.)",
         "seco_min": None,    "seco_max": None,    "hum_min": 6513,   "hum_max": 6513},
    4:  {"desc": "#4 (1-2 in) washed granite (Ga.)",
         "seco_min": 1.5e6,   "seco_max": 4.5e6,   "hum_min": 5000,   "hum_max": 5000},
    5:  {"desc": "#3 (2-4 in) washed granite (Ga.)",
         "seco_min": 2.6e6,   "seco_max": 3.0e6,   "hum_min": 10000,  "hum_max": 10000},
    6:  {"desc": "Washed limestone (Mich.)",
         "seco_min": 7.0e6,   "seco_max": 7.0e6,   "hum_min": 2000,   "hum_max": 3000},
    7:  {"desc": "Washed granite ~0.75 in gravel",
         "seco_min": 2.0e6,   "seco_max": 2.0e6,   "hum_min": 10000,  "hum_max": 10000},
    8:  {"desc": "Washed granite, pea gravel",
         "seco_min": 40e6,    "seco_max": 40e6,    "hum_min": 5000,   "hum_max": 5000},
    9:  {"desc": "#57 (0.75 in) washed granite (N.C.)",
         "seco_min": 190e6,   "seco_max": 190e6,   "hum_min": 8000,   "hum_max": 8000},
    10: {"desc": "Asphalt",
         "seco_min": 2.0e6,   "seco_max": 30e6,    "hum_min": 10000,  "hum_max": 6.0e6},
    11: {"desc": "Concrete",
         "seco_min": 1.0e6,   "seco_max": 1.0e9,   "hum_min": 21,     "hum_max": 100},
    12: {"desc": "Custom (definido por usuario)",
         "seco_min": None,    "seco_max": None,    "hum_min": None,   "hum_max": None},
}

# Modelos de varilla de aterrizaje (Excel Entradas §5)
# Columnas: diametro_mm [mm], Lr [m]  (b = diametro_mm/2/1000 [m])
MODELOS_VARILLA = {
    "Copperweld 1/2\"": {"diametro_mm": 12.7, "Lr": 1.50},
    "Copperweld 5/8\"": {"diametro_mm": 15.9, "Lr": 1.80},
    "Copperweld 3/4\"": {"diametro_mm": 19.1, "Lr": 2.40},
    "Galvanized 3/4\"": {"diametro_mm": 19.1, "Lr": 2.44},
    "Copper 1/2\"":     {"diametro_mm": 12.7, "Lr": 1.20},
    "Copper 5/8\"":     {"diametro_mm": 15.9, "Lr": 1.50},
    "Standard 8ft":     {"diametro_mm": 15.9, "Lr": 2.44},
    "Standard 10ft":    {"diametro_mm": 15.9, "Lr": 3.05},
    "Standard 12ft":    {"diametro_mm": 19.1, "Lr": 3.66},
}


def get_rho_s(mat_id, condicion, val_uso, rho_s_custom=None):
    """
    Extrae la resistividad del material superficial según Tabla 7.

    Parámetros:
      mat_id      : int 1-12
      condicion   : 'Dry' o 'Wet'
      val_uso     : 'Mínimo' o 'Máximo'
      rho_s_custom: float requerido si mat_id=12

    Retorna: (rho_s [Ω·m], rho_min, rho_max)  o  error dict
    """
    if mat_id == 12:
        if rho_s_custom is None:
            return {"error": "mat_id=12 (Custom) requiere rho_s_custom"}
        return {"rho_s": rho_s_custom, "rho_min": rho_s_custom, "rho_max": rho_s_custom}
    m = MATERIALES_SUPERFICIE.get(mat_id)
    if m is None:
        return {"error": f"mat_id={mat_id} no existe (válido: 1-12)"}
    if condicion == "Dry":
        lo, hi = m["seco_min"], m["seco_max"]
    else:
        lo, hi = m["hum_min"], m["hum_max"]
    if lo is None:
        return {"error": f"Material {mat_id} no tiene datos para condición {condicion}"}
    rho_s = lo if val_uso == "Mínimo" else hi
    return {"rho_s": rho_s, "rho_min": lo, "rho_max": hi}


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 (auxiliar) · LISTAS_D — Espaciamientos válidos
# Excel: hoja "Listas_D"
# Regla general: D = L/n para n = 1..50, válido si 3 ≤ D ≤ 15 m
# Condiciones adicionales por forma (cols D y E de Listas_D):
#   Isósceles (E4=3):      Db válido solo si Db·(Li/Lb) ≥ 3
#   Tri.Rect. (E4=4):      D1 válido solo si D1·(Ly/Lx) ≥ 3
#   Escaleno  (E4=5):      D1 válido solo si D1·MIN(Lb_e,Lc_e)/La ≥ 3
# ══════════════════════════════════════════════════════════════════════════════
_D_MIN, _D_MAX = 3.0, 15.0


def _candidatos(L, cond_extra=None):
    """
    Genera los 50 candidatos D = L/n (n=1..50) igual que las columnas A-E
    de Listas_D.  Devuelve lista de dicts con {n, D, valido, razon}.

    cond_extra: función(D) -> (bool, str) para la condición de geometría adicional.
    """
    resultado = []
    for n in range(1, 51):
        D = round(L / n, 4) if L > 0 else 0
        en_rango = (_D_MIN - 1e-9) <= D <= (_D_MAX + 1e-9)
        if not en_rango:
            if D > _D_MAX:
                razon = f"D={D} > {_D_MAX} m"
            elif D < _D_MIN and D > 0:
                razon = f"D={D} < {_D_MIN} m"
            else:
                razon = "L=0 o n muy grande"
            resultado.append({"n": n, "D": D, "valido": False, "razon": razon})
            continue
        if cond_extra:
            ok_extra, razon_extra = cond_extra(D)
            if not ok_extra:
                resultado.append({"n": n, "D": D, "valido": False, "razon": razon_extra})
                continue
        resultado.append({"n": n, "D": D, "valido": True, "razon": "✔"})
    return resultado


def listas_d(forma, Lx=0, Ly=0, L=0, Lb=0, Li=0, La=0, Lb_e=0, Lc_e=0):
    """
    Hoja Listas_D del Excel.
    Retorna dict con las listas de candidatos y la lista limpia de D válidos.

    Forma 1,6,7 → {candidatos_Dx, lista_Dx, candidatos_Dy, lista_Dy}
    Forma 2     → {candidatos_D,  lista_D}
    Forma 3     → {candidatos_Db, lista_Db}  con condición Di=Db·Li/Lb≥3
    Forma 4     → {candidatos_D1, lista_D1}  con condición D2=D1·Ly/Lx≥3
    Forma 5     → {candidatos_D1, lista_D1}  con condición D2=D1·min(Lb_e,Lc_e)/La≥3
    """
    if forma in (1, 6, 7):
        # Col A: Ly → Dx = Ly/n  |  Col B: Lx → Dy = Lx/m
        cands_x = _candidatos(Ly)   # Dx
        cands_y = _candidatos(Lx)   # Dy
        return {
            "candidatos_Dx": cands_x,
            "lista_Dx": [c["D"] for c in cands_x if c["valido"]],
            "candidatos_Dy": cands_y,
            "lista_Dy": [c["D"] for c in cands_y if c["valido"]],
        }
    elif forma == 2:
        # Col C: L → D = L/n
        cands = _candidatos(L)
        return {"candidatos_D": cands, "lista_D": [c["D"] for c in cands if c["valido"]]}
    elif forma == 3:
        # Col D: Lb → Db = Lb/n, con Di = Db·(Li/Lb) ≥ 3
        def cond(Db):
            if Lb <= 0:
                return False, "Lb=0"
            Di = Db * (Li / Lb)
            if Di < _D_MIN - 1e-9:
                return False, f"Di=Db·Li/Lb={Di:.4f} < {_D_MIN} m"
            return True, "✔"
        cands = _candidatos(Lb, cond_extra=cond)
        return {"candidatos_Db": cands, "lista_Db": [c["D"] for c in cands if c["valido"]]}
    elif forma == 4:
        # Col E: Lx → D1 = Lx/n, con D2 = D1·(Ly/Lx) ≥ 3
        def cond(D1):
            if Lx <= 0:
                return False, "Lx=0"
            D2 = D1 * (Ly / Lx)
            if D2 < _D_MIN - 1e-9:
                return False, f"D2=D1·Ly/Lx={D2:.4f} < {_D_MIN} m"
            return True, "✔"
        cands = _candidatos(Lx, cond_extra=cond)
        return {"candidatos_D1": cands, "lista_D1": [c["D"] for c in cands if c["valido"]]}
    elif forma == 5:
        # Col E: La → D1 = La/n, con D2 = D1·min(Lb_e,Lc_e)/La ≥ 3
        def cond(D1):
            if La <= 0:
                return False, "La=0"
            Dmin_der = D1 * min(Lb_e, Lc_e) / La
            if Dmin_der < _D_MIN - 1e-9:
                return False, f"D1·min(Lb,Lc)/La={Dmin_der:.4f} < {_D_MIN} m"
            return True, "✔"
        cands = _candidatos(La, cond_extra=cond)
        return {"candidatos_D1": cands, "lista_D1": [c["D"] for c in cands if c["valido"]]}
    return {"error": f"forma={forma} no reconocida"}


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 · CALIBRE DEL CONDUCTOR
# Excel: hoja "Calibre Conductor"
# ══════════════════════════════════════════════════════════════════════════════

def sec2_calibre(material_id, I_falla, tc, tf, XR, Tamb):
    """
    Sección 2 — Calibre del conductor (IEEE 80-2013).

    §2.1  Área mínima requerida — Ec. (37):
          A_min = I_falla / √[TCAP·10⁻⁴ / (tc·αr·ρr) · ln((K0+Tm)/(K0+Tamb))]

    §2.5  Factores de asimetría — Ec. (74) y (75):
          Ta = (X/R) / (2π·60)
          Df = √[1 + (Ta/tf)·(1 − e^(−2·tf/Ta))]

    §2.3  Selección iterativa del calibre: primer calibre con
          área ≥ A_min  Y  IF_conductor = área × denominador ≥ IF_sistema

    Parámetros:
      material_id : int 1-10 (Tabla 1)
      I_falla     : [kA] corriente de falla simétrica
      tc          : [s]  duración para cálculo térmico del conductor
      tf          : [s]  duración para cálculo de asimetría
      XR          : relación X/R del sistema
      Tamb        : [°C] temperatura ambiente

    Retorna dict con todos los valores intermedios y finales.
    """
    mat = MATERIALES_CONDUCTOR.get(material_id, MATERIALES_CONDUCTOR[1])

    # §2.5 — Factores de asimetría
    Ta = XR / (2.0 * math.pi * 60.0)
    if Ta > 0:
        Df = math.sqrt(1.0 + (Ta / tf) * (1.0 - math.exp(-2.0 * tf / Ta)))
    else:
        Df = 1.0
    I_asim_sistema = I_falla * Df   # [kA]

    # §2.1 — Área mínima  (Ec. 37)
    # ln_factor = ln[(K0+Tm)/(K0+Tamb)]
    ln_factor = math.log((mat["K0"] + mat["Tm"]) / (mat["K0"] + Tamb))
    # denominador = √[TCAP·10⁻⁴ / (tc·αr·ρr) · ln_factor]
    denom = math.sqrt((mat["TCAP"] * 1e-4) / (tc * mat["alpha_r"] * mat["rho_r"]) * ln_factor)
    A_min = I_falla / denom   # [mm²]  (I_falla en kA, denom en kA/mm²)

    # §2.3 — Selección iterativa
    conductor = None
    IF_conductor = None
    iteraciones = []
    for c in CONDUCTORES_COMERCIALES:
        if c["area_mm2"] < A_min - 1e-6:
            iteraciones.append({**c, "IF_cond_kA": None, "estado": "✘  Área insuficiente",
                                 "razon": f"área={c['area_mm2']} mm² < A_min={round(A_min,4)} mm²"})
            continue
        IF_c = c["area_mm2"] * denom   # [kA]
        if IF_c >= I_asim_sistema - 1e-9:
            conductor = c
            IF_conductor = IF_c
            iteraciones.append({**c, "IF_cond_kA": round(IF_c, 4), "estado": "✔  Cumple",
                                 "razon": f"IF={round(IF_c,4)} kA ≥ IF_sis={round(I_asim_sistema,4)} kA"})
            break
        iteraciones.append({**c, "IF_cond_kA": round(IF_c, 4), "estado": "✘  IF insuficiente",
                             "razon": f"IF={round(IF_c,4)} kA < IF_sis={round(I_asim_sistema,4)} kA"})

    if conductor is None:
        return {"error": "Ningún calibre comercial es suficiente.", "iteraciones": iteraciones}

    return {
        # Entradas resumidas
        "material": mat["nombre"],
        "I_falla_kA": I_falla, "tc_s": tc, "tf_s": tf, "XR": XR, "Tamb_C": Tamb,
        # §2.5
        "Ta_s": round(Ta, 6),
        "Df": round(Df, 6),
        "I_asim_sistema_kA": round(I_asim_sistema, 4),
        # §2.1
        "ln_factor": round(ln_factor, 6),
        "denom": round(denom, 6),
        "A_min_mm2": round(A_min, 4),
        # §2.3 selección
        "iteraciones": iteraciones,
        "kcmil": conductor["kcmil"],
        "AWG": conductor["AWG"],
        "area_mm2": conductor["area_mm2"],
        "diametro_m": conductor["diametro_m"],
        "radio_m": conductor["diametro_m"] / 2.0,
        "IF_conductor_kA": round(IF_conductor, 4),
        "verif_calibre": (
            f"✔  CUMPLE — IF_conductor ({round(IF_conductor,4)} kA)"
            f" ≥ IF_sistema ({round(I_asim_sistema,4)} kA)"
        ),
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 · GEOMETRÍA Y LONGITUDES
# Excel: hojas "Entradas" y "Cálculo Lc"
# ══════════════════════════════════════════════════════════════════════════════

def _ceiling(x, sig):
    """CEILING(x, sig) — redondear x hacia arriba al múltiplo de sig."""
    if sig <= 0:
        return x
    return math.ceil(x / sig - 1e-9) * sig


def sec3_geometria(forma, Dx=0, Dy=0, D=0, Db=0, D1=0, D1_esc=0,
                   Lx=0, Ly=0, L=0, Lb=0, Li=0,
                   La=0, Lb_e=0, Lc_e=0,
                   Lx1=0, Ly1=0, Lx2=0, Ly2=0,
                   uv=0, Lr=0):
    """
    Sección 3 — Geometría, Lc y varillas (hojas Entradas + Cálculo Lc).

    Parámetros de entrada según forma:
      Formas 1,6,7 (rect/L/T): Lx, Ly, Dx, Dy, [Lx1, Ly1, Lx2, Ly2]
      Forma 2 (equilátero):    L, D
      Forma 3 (isósceles):     Lb, Li, Db
      Forma 4 (tri.rect.):     Lx, Ly, D1
      Forma 5 (escaleno):      La, Lb_e, Lc_e, D1_esc
      uv : ubicación varillas (0-3)
      Lr : longitud de cada varilla [m]

    Fórmulas Lc:
      Forma 1: Lc = Nx·Lx + Ny·Ly        (Nx=Ly/Dx+1, Ny=Lx/Dy+1)
      Forma 2: Lc = 3·L·(n+1)/2           (n = L/D)
      Forma 3: Lc = (n+1)·(Li + Lb/2)     (n = Lb/Db, Di=Db·Li/Lb)
      Forma 4: Lc = (n+1)/2·(Lx+Ly+hyp)  (n = Lx/D1, D2=D1·Ly/Lx, D3=D1·hyp/Lx)
      Forma 5: Lc = (n+1)/2·(La+Lb_e+Lc_e)(n = La/D1_esc)
      Forma 6: Lc = (Nx·Lx+Ny·Ly)−(Nx1·Lx1_aj+Ny1·Ly1_aj)
      Forma 7: ídem −(Nx2·Lx2_aj+Ny2·Ly2_aj)

    Retorna dict con todos los valores intermedios y finales.
    """
    r = {}   # resultado

    # ── Recortes ajustados para L y T (Cálculo Lc C11-C14) ───────────────────
    # Necesario aquí para que el área use los valores ajustados.
    # Lx1_aj = CEILING(Lx1, Dy)   Ly1_aj = CEILING(Ly1, Dx)
    Lx1_aj = Ly1_aj = Lx2_aj = Ly2_aj = 0
    Nx1 = Ny1 = Nx2 = Ny2 = 0
    if forma in (6, 7):
        Lx1_aj = _ceiling(Lx1, Dy)
        Ly1_aj = _ceiling(Ly1, Dx)
    if forma == 7:
        Lx2_aj = _ceiling(Lx2, Dy)
        Ly2_aj = _ceiling(Ly2, Dx)

    # ── Área cubierta (Entradas B72) ──────────────────────────────────────────
    if forma == 1:
        A = Lx * Ly
    elif forma == 2:
        A = (math.sqrt(3) / 4) * L**2
    elif forma == 3:
        h_iso = math.sqrt(max(Li**2 - (Lb / 2)**2, 0))
        A = 0.5 * Lb * h_iso
    elif forma == 4:
        A = 0.5 * Lx * Ly
    elif forma == 5:
        s = (La + Lb_e + Lc_e) / 2
        A = math.sqrt(max(s * (s - La) * (s - Lb_e) * (s - Lc_e), 0))
    elif forma == 6:
        A = Lx * Ly - Lx1_aj * Ly1_aj
    elif forma == 7:
        A = Lx * Ly - Lx1_aj * Ly1_aj - Lx2_aj * Ly2_aj
    else:
        A = 0
    r["A"] = round(A, 4)

    # ── Dimensiones efectivas (para nc, nd, Dm, k1/k2) ───────────────────────
    # Lx_eff / Ly_eff  (Voltajes Em y Es B5/B6)
    if forma in (1, 4, 6, 7):
        Lx_eff = Lx; Ly_eff = Ly
    elif forma == 2:
        Lx_eff = L;  Ly_eff = L * math.sqrt(3) / 2
    elif forma == 3:
        Lx_eff = Lb; Ly_eff = math.sqrt(max(Li**2 - (Lb / 2)**2, 0))
    elif forma == 5:
        Lx_eff = La
        Ly_eff = (2 * A / La) if La > 0 else 0
    else:
        Lx_eff = Lx; Ly_eff = Ly
    r["Lx_eff"] = round(Lx_eff, 4)
    r["Ly_eff"] = round(Ly_eff, 4)

    # Dm — distancia máxima entre dos puntos de la malla (Ec. 93 / B21)
    if forma == 2:
        Dm = L
    elif forma == 3:
        Dm = max(Lb, Li)
    elif forma == 4:
        Dm = math.sqrt(Lx_eff**2 + Ly_eff**2)
    elif forma == 5:
        Dm = max(La, Lb_e, Lc_e)
    else:   # 1, 6, 7
        Dm = math.sqrt(Lx_eff**2 + Ly_eff**2)
    r["Dm"] = round(Dm, 4)
    r["diag_eff"] = round(math.sqrt(Lx_eff**2 + Ly_eff**2), 4)

    # ── Número de conductores Nx, Ny (Cálculo Lc C17/C18) ────────────────────
    if forma in (1, 6, 7):
        Nx = int(round(Ly / Dx)) + 1 if Dx > 0 else 0   # Nx = Ly/Dx + 1
        Ny = int(round(Lx / Dy)) + 1 if Dy > 0 else 0   # Ny = Lx/Dy + 1
    elif forma == 2:
        n2 = int(round(L / D)) if D > 0 else 0
        Nx = n2; Ny = n2   # equilátero: único n
    elif forma == 3:
        n3 = int(round(Lb / Db)) if Db > 0 else 0
        Nx = n3; Ny = 0    # n_tri almacenado en Nx
    elif forma == 4:
        n4 = int(round(Lx / D1)) if D1 > 0 else 0
        Nx = n4; Ny = 0
    elif forma == 5:
        n5 = int(round(La / D1_esc)) if D1_esc > 0 else 0
        Nx = n5; Ny = 0
    else:
        Nx = Ny = 0
    r["Nx"] = Nx; r["Ny"] = Ny

    # Recortes ajustados — Nx/Ny de cada recorte (Cálculo Lc C11-C14)
    # Lx1_aj / Ly1_aj / Lx2_aj / Ly2_aj ya están calculados al inicio.
    if forma in (6, 7):
        Nx1 = int(round(Ly1_aj / Dx)) if Dx > 0 else 0  # tramos eliminados en Y
        Ny1 = int(round(Lx1_aj / Dy)) if Dy > 0 else 0  # tramos eliminados en X
    if forma == 7:
        Nx2 = int(round(Ly2_aj / Dx)) if Dx > 0 else 0
        Ny2 = int(round(Lx2_aj / Dy)) if Dy > 0 else 0
    r["Lx1_aj"] = round(Lx1_aj, 4); r["Ly1_aj"] = round(Ly1_aj, 4)
    r["Lx2_aj"] = round(Lx2_aj, 4); r["Ly2_aj"] = round(Ly2_aj, 4)
    r["Nx1"] = Nx1; r["Ny1"] = Ny1
    r["Nx2"] = Nx2; r["Ny2"] = Ny2

    # ── Espaciados derivados (para mostrar en test) ────────────────────────────
    Di = D2 = D3 = 0.0
    L_hyp = 0.0
    if forma == 3 and Lb > 0:
        Di = Db * (Li / Lb)   # Di = Db·(Li/Lb)
    if forma == 4 and Lx > 0:
        L_hyp = math.sqrt(Lx**2 + Ly**2)
        D2 = D1 * (Ly / Lx)
        D3 = D1 * (L_hyp / Lx)
    if forma == 5 and La > 0:
        D2 = D1_esc * (Lb_e / La)
        D3 = D1_esc * (Lc_e / La)
    r["Di"] = round(Di, 4); r["D2"] = round(D2, 4); r["D3"] = round(D3, 4)
    r["L_hyp"] = round(L_hyp, 4)

    # ── Longitud total de conductores Lc (Cálculo Lc C27-C36) ────────────────
    if forma == 1:
        Lc = Nx * Lx + Ny * Ly                            # Nx·Lx + Ny·Ly
    elif forma == 2:
        n = Nx                                              # n = L/D
        Lc = 3 * L * (n + 1) / 2                          # 3·L·(n+1)/2
    elif forma == 3:
        n = Nx                                              # n = Lb/Db
        Lc = (n + 1) * (Li + Lb / 2)                      # (n+1)·(Li+Lb/2)
    elif forma == 4:
        n = Nx                                              # n = Lx/D1
        Lc = (n + 1) / 2 * (Lx + Ly + L_hyp)             # (n+1)/2·(L1+L2+L3)
    elif forma == 5:
        n = Nx                                              # n = La/D1_esc
        Lc = (n + 1) / 2 * (La + Lb_e + Lc_e)            # (n+1)/2·(La+Lb+Lc)
    elif forma == 6:
        Lc = (Nx * Lx + Ny * Ly) - (Nx1 * Lx1_aj + Ny1 * Ly1_aj)
    elif forma == 7:
        Lc = ((Nx * Lx + Ny * Ly)
              - (Nx1 * Lx1_aj + Ny1 * Ly1_aj)
              - (Nx2 * Lx2_aj + Ny2 * Ly2_aj))
    else:
        Lc = 0
    r["Lc"] = round(Lc, 4)

    # ── Perímetro Lp (Voltajes Em y Es B20) ───────────────────────────────────
    if forma == 1:
        Lp = 2 * (Lx + Ly)                        # 2·(Lx+Ly); Excel: 4·Lx para cuadrado
    elif forma == 2:
        Lp = 3 * L
    elif forma == 3:
        Lp = Lb + 2 * Li
    elif forma == 4:
        Lp = Lx + Ly + L_hyp
    elif forma == 5:
        Lp = La + Lb_e + Lc_e
    else:                                          # 6 y 7: perímetro externo = 2·(Lx+Ly)
        Lp = 2 * (Lx + Ly)
    r["Lp"] = round(Lp, 4)

    # ── Varillas: nR y LR (Entradas B52-B59) ──────────────────────────────────
    # n_tri: número de secciones en el lado primario (para triangulares)
    if forma == 2:   n_tri = Nx           # L/D
    elif forma == 3: n_tri = Nx           # Lb/Db
    elif forma == 4: n_tri = Nx           # Lx/D1
    elif forma == 5: n_tri = Nx           # La/D1_esc
    else:            n_tri = 0
    r["n_tri"] = n_tri

    if uv == 0:
        nR = 0
    elif uv == 1:   # Esquinas (B53)
        nR = {1: 4, 6: 6, 7: 8}.get(forma, 3)     # triangulares = 3
    elif uv == 2:   # Perímetro (B54)
        if forma in (1, 6, 7):
            nR = 2 * Nx + 2 * Ny - 4
        else:
            nR = 3 * n_tri                          # 3·n_tri para triangulares
    elif uv == 3:   # Todas las intersecciones (B55)
        if forma == 1:
            nR = Nx * Ny
        elif forma == 6:
            nR = Nx * Ny - Nx1 * Ny1
        elif forma == 7:
            nR = Nx * Ny - Nx1 * Ny1 - Nx2 * Ny2
        else:
            nR = (n_tri + 1) * (n_tri + 2) // 2   # triangulares
    else:
        nR = 0

    LR = nR * Lr
    LT = Lc + LR
    r["nR"] = nR; r["LR"] = round(LR, 4); r["LT"] = round(LT, 4)

    # ── Validaciones (Cálculo Lc C39-C49) ─────────────────────────────────────
    vals = {}
    if forma in (1, 6, 7):
        vals["Ly/Dx entero"] = "✔ OK" if (Dx > 0 and abs(Ly / Dx - round(Ly / Dx, 0)) < 0.01) else "✘ Ly/Dx no entero"
        vals["Lx/Dy entero"] = "✔ OK" if (Dy > 0 and abs(Lx / Dy - round(Lx / Dy, 0)) < 0.01) else "✘ Lx/Dy no entero"
        vals["Dx en [3,15]"] = "✔ OK" if (_D_MIN <= Dx <= _D_MAX) else f"✘ Dx={Dx} fuera de [3,15]"
        vals["Dy en [3,15]"] = "✔ OK" if (_D_MIN <= Dy <= _D_MAX) else f"✘ Dy={Dy} fuera de [3,15]"
        if forma in (6, 7):
            vals["Lx1_aj < Lx"] = "✔ OK" if Lx1_aj < Lx else "✘ Lx1_aj ≥ Lx"
            vals["Ly1_aj < Ly"] = "✔ OK" if Ly1_aj < Ly else "✘ Ly1_aj ≥ Ly"
        if forma == 7:
            vals["Lx1_aj+Lx2_aj < Lx"] = "✔ OK" if (Lx1_aj + Lx2_aj < Lx) else "✘ sin tronco central"
    elif forma == 2:
        vals["L/D entero"] = "✔ OK" if (D > 0 and abs(L / D - round(L / D, 0)) < 0.01) else "✘ L/D no entero"
    elif forma == 3:
        vals["Lb/Db entero"] = "✔ OK" if (Db > 0 and abs(Lb / Db - round(Lb / Db, 0)) < 0.01) else "✘ Lb/Db no entero"
    elif forma in (4, 5):
        D_prim = D1 if forma == 4 else D1_esc
        L_prim = Lx if forma == 4 else La
        vals["L1/D1 entero"] = "✔ OK" if (D_prim > 0 and abs(L_prim / D_prim - round(L_prim / D_prim, 0)) < 0.01) else "✘ L1/D1 no entero"
        if forma == 5:
            vals["Desig. triangular"] = "✔ OK" if (La + Lb_e > Lc_e and La + Lc_e > Lb_e and Lb_e + Lc_e > La) else "✘ Lados no forman triángulo"
    r["validaciones"] = vals
    return r


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 · CORRIENTES DE DISEÑO
# Excel: hoja "Verificación GPR", §3
# ══════════════════════════════════════════════════════════════════════════════

def sec4_corrientes(I_falla, Sf, Df):
    """
    Sección 4 — Corrientes Ig e IG (IEEE 80-2013, §15).

    Ig = If · Sf          [kA] — corriente simétrica de malla
    IG = Ig · Df          [kA] — corriente máxima de malla (asimétrica)

    Nota: para GPR y Em/Es se usa IG en Amperios = IG_kA × 1000.
    """
    Ig = I_falla * Sf           # [kA]
    IG = Ig * Df                # [kA]
    IG_A = IG * 1000.0          # [A] — para cálculos internos
    return {
        "Ig_kA": round(Ig, 4),
        "IG_kA": round(IG, 4),
        "IG_A":  round(IG_A, 4),
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5 · RESISTENCIA Rg
# Excel: hoja "Resistencia Rg"
# ══════════════════════════════════════════════════════════════════════════════

def sec5_resistencia(rho, h, A, Lc, LT, nR, Lr, b, a_cond, forma,
                     Lx=0, Ly=0, L=0, Lb=0, Li=0, La=0, Lb_e=0, Lc_e=0,
                     metodo_rg="schwarz"):
    """
    Sección 5 — Resistencia de la malla Rg (IEEE 80-2013).

    Sin varillas (nR=0) → Sverak (§14.3):
      Rg = ρ·[1/LT + 1/√(20·A)·(1 + 1/(1+h·√(20/A)))]

    Con varillas (nR>0) → Schwarz (§14.2), Ec. (53)-(56):
      a' = √(a·2h)  si h>0  (radio equiv. del conductor enterrado)
      R1 = (ρ/π·Lc)·[ln(2Lc/a') + k1·Lc/√A − k2]
      R2 = (ρ/2π·nR·Lr)·[ln(4Lr/b) − 1 + 2k1·Lr/√A·(√nR−1)²]
      Rm = (ρ/π·Lc)·[ln(2Lc/Lr) + k1·Lc/√A − k2 + 1]
      Rg = (R1·R2 − Rm²)/(R1+R2−2·Rm)

    k1, k2: interpolados según h y ratio x=dim_mayor/dim_menor (Fig. 24).
    """
    r = {}

    # ── k1, k2 — coeficientes de Schwarz (interpolación Fig. 24) ─────────────
    # Ratio x = dim_mayor/dim_menor  (Resistencia Rg B21)
    sqA = math.sqrt(A) if A > 0 else 1.0
    if forma in (1, 6, 7):
        dmax, dmin = max(Lx, Ly), min(Lx, Ly)
    elif forma == 2:
        dmax = L; dmin = L * math.sqrt(3) / 2
    elif forma == 3:
        dmax = max(Lb, Li); dmin = min(Lb, Li)
    elif forma == 4:
        dmax = max(Lx, Ly); dmin = min(Lx, Ly)
    elif forma == 5:
        dmax = max(La, Lb_e, Lc_e); dmin = min(La, Lb_e, Lc_e)
    else:
        dmax, dmin = 1, 1
    x = dmax / dmin if dmin > 0 else 1.0
    r["x_ratio"] = round(x, 4)

    # Curvas A, B, C — Figura 24
    k1A = -0.04 * x + 1.41;  k1B = -0.05 * x + 1.20;  k1C = -0.05 * x + 1.13
    k2A =  0.15 * x + 5.50;  k2B =  0.10 * x + 4.68;  k2C = -0.05 * x + 4.40
    hB  = sqA / 10.0;         hC  = sqA / 6.0

    if h <= 0:
        k1, k2 = k1A, k2A
    elif h <= hB:
        t = h / hB; k1 = k1A + t * (k1B - k1A); k2 = k2A + t * (k2B - k2A)
    elif h <= hC:
        t = (h - hB) / (hC - hB); k1 = k1B + t * (k1C - k1B); k2 = k2B + t * (k2C - k2B)
    else:
        k1, k2 = k1C, k2C

    r["hB"] = round(hB, 4); r["hC"] = round(hC, 4)
    r["k1A"] = round(k1A, 6); r["k1B"] = round(k1B, 6); r["k1C"] = round(k1C, 6)
    r["k2A"] = round(k2A, 6); r["k2B"] = round(k2B, 6); r["k2C"] = round(k2C, 6)
    r["k1"] = round(k1, 6); r["k2"] = round(k2, 6)

    # ── Radio equivalente a' (Resistencia Rg B34) ────────────────────────────
    a_prima = math.sqrt(a_cond * 2.0 * h) if h > 0 else a_cond
    r["a_prima_m"]  = round(a_prima, 6)
    r["a_prima_mm"] = round(a_prima * 1000, 4)

    # ── Método y Rg ──────────────────────────────────────────────────────────
    usar_sverak = (nR == 0) or (metodo_rg == "sverak")
    if usar_sverak:
        r["metodo"] = "Sverak (sin varillas)" if nR == 0 else "Sverak (con varillas)"
        r["R1"] = r["R2"] = r["Rm"] = None
        sv1 = 1.0 / LT
        sv2 = (1.0 / math.sqrt(20.0 * A)) * (1.0 + 1.0 / (1.0 + h * math.sqrt(20.0 / A)))
        Rg = rho * (sv1 + sv2)
    else:
        # Schwarz — Ec. (53), (54), (55), (56)
        r["metodo"] = "Schwarz"
        R1 = (rho / (math.pi * Lc))      * (math.log(2 * Lc / a_prima)  + k1 * Lc / sqA - k2)
        R2 = (rho / (2 * math.pi * nR * Lr)) * (math.log(4 * Lr / b) - 1 + 2 * k1 * Lr / sqA * (math.sqrt(nR) - 1)**2)
        Rm = (rho / (math.pi * Lc))      * (math.log(2 * Lc / Lr)  + k1 * Lc / sqA - k2 + 1)
        den = R1 + R2 - 2 * Rm
        if abs(den) < 1e-12:
            return {"error": "Denominador nulo en Rg (R1+R2-2Rm≈0)"}
        Rg = (R1 * R2 - Rm**2) / den
        r["R1"] = round(R1, 6); r["R2"] = round(R2, 6); r["Rm"] = round(Rm, 6)

    r["Rg"] = round(Rg, 6)
    verif = "✔  CUMPLE — Rg ≤ 1 Ω" if Rg <= 1.0 else f"✘  NO CUMPLE — Rg = {round(Rg,4)} Ω > 1 Ω"
    r["verif_Rg"] = verif
    return r


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 6 · TENSIONES ADMISIBLES
# Excel: hoja "Tensiones Tolerables"
# ══════════════════════════════════════════════════════════════════════════════

def sec6_tensiones(rho, rho_s, hs, ts, peso):
    """
    Sección 6 — Tensiones tolerables de paso y contacto (IEEE 80-2013, §8.3).

    Cs = 1 − [0.09·(1−ρ/ρs)] / (2·hs + 0.09)     (Ec. 27)
    E_step  = (1000 + 6·Cs·ρs) · K / √ts
    E_touch = (1000 + 1.5·Cs·ρs) · K / √ts

    K = 0.116 para 50 kg  |  K = 0.157 para 70 kg
    """
    K = 0.116 if peso == 50 else 0.157
    if hs == 0 or rho_s == rho:
        Cs = 1.0
    else:
        Cs = 1.0 - (0.09 * (1 - rho / rho_s)) / (2 * hs + 0.09)
    st = math.sqrt(ts)
    E_step  = (1000 + 6.0   * Cs * rho_s) * K / st
    E_touch = (1000 + 1.5   * Cs * rho_s) * K / st
    return {
        "K": K, "Cs": round(Cs, 6),
        "E_step_V":  round(E_step,  4),
        "E_touch_V": round(E_touch, 4),
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 7 · VERIFICACIÓN GPR
# Excel: hoja "Verificación GPR"
# ══════════════════════════════════════════════════════════════════════════════

def sec7_gpr(IG_A, Rg, E_touch_V):
    """
    Sección 7 — GPR y verificación (IEEE 80-2013, §15.1).

    GPR = IG [A] · Rg [Ω]   [V]
    Verificación: GPR < E_touch
    """
    GPR = IG_A * Rg
    ok  = GPR < E_touch_V
    return {
        "GPR_V": round(GPR, 4),
        "gpr_ok": ok,
        "verif_GPR": (f"✔  GPR CUMPLE — GPR={round(GPR,2)} V < E_touch={round(E_touch_V,2)} V"
                      if ok else
                      f"✘  GPR NO CUMPLE — GPR={round(GPR,2)} V > E_touch={round(E_touch_V,2)} V"),
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 8 · VOLTAJES Em y Es
# Excel: hoja "Voltajes Em y Es"
# ══════════════════════════════════════════════════════════════════════════════

def sec8_voltajes(rho, h, forma, uv,
                  Lc, LR, Lr, nR,
                  Lx_eff, Ly_eff, Lp, Dm, A,
                  Dx, Dy, D, Db, D1, D1_esc,
                  La=0, Lb_e=0, Lc_e=0,
                  IG_A=0, d_con=0,
                  E_touch_V=0, E_step_V=0):
    """
    Sección 8 — Voltajes de malla Em y paso Es (IEEE 80-2013, §16.5).

    n = na·nb·nc·nd  (Ec. 89-93)
    Km, Ks  (Ec. 86-88, 99)
    LM, LS  (Ec. 95-96, 98)
    Em = ρ·Km·Ki·IG / LM
    Es = ρ·Ks·Ki·IG / LS
    """
    r = {}
    sqA = math.sqrt(A) if A > 0 else 1.0
    diag_eff = math.sqrt(Lx_eff**2 + Ly_eff**2)

    # ── n = na·nb·nc·nd ───────────────────────────────────────────────────────
    # na = 2·Lc / Lp  (Ec. 90)
    na = 2 * Lc / Lp if Lp > 0 else 1.0

    # nb  (Ec. 91)  — nb = sqrt(Lp / (4·√A)); es 1 solo si la malla es cuadrada
    nb = math.sqrt(Lp / (4 * sqA)) if A > 0 else 1.0

    # nc  (Ec. 92)  — nc=1 para rect (1) y equilátero (2)
    bbox = Lx_eff * Ly_eff
    if forma in (1, 2) or A <= 0 or abs(bbox - A) < 1e-9 * A:
        nc = 1.0
    else:
        nc = (bbox / A) ** (0.7 * A / bbox) if bbox > 0 else 1.0

    # nd  (Ec. 93)  — nd=1 para rect (1), equilátero (2) y Forma L (6)
    if forma in (1, 2, 6):
        nd = 1.0
    else:
        nd = (Dm / diag_eff) if diag_eff > 0 else 1.0

    n  = na * nb * nc * nd
    Ki = 0.644 + 0.148 * n
    r["na"] = round(na, 6); r["nb"] = round(nb, 6)
    r["nc"] = round(nc, 6); r["nd"] = round(nd, 6)
    r["n"]  = round(n,  6); r["Ki"] = round(Ki, 6)

    # ── D promedio para Km y Ks (Entradas B65) ────────────────────────────────
    # Isósceles: Di = Db·(Li/Lb), D_avg = (Db + Di)/2
    # Tri.rect.: D2=D1·Ly/Lx, D3=D1·hyp/Lx, D_avg=(D1+D2+D3)/3
    # Escaleno:  D2=D1_esc·Lb_e/La, D3=D1_esc·Lc_e/La, D_avg=(D1_esc+D2+D3)/3
    if forma in (1, 6, 7):
        D_avg = (Dx + Dy) / 2
    elif forma == 2:
        D_avg = D
    elif forma == 3:
        Di = Db * (r.get("Li", 0) / Db) if False else Db   # Di calculado en sec3
        # Recalcular con info disponible (Di se pasa como D)
        D_avg = D        # D ya contiene el Di calculado si el caller lo pasa, else usamos D
        # Correcto: D_avg = (Db + Di)/2, pero Di debe venir del caller
        D_avg = D        # fallback; caller debe pasar D=D_avg para isósceles
    elif forma == 4:
        L_hyp = math.sqrt(Lx_eff**2 + Ly_eff**2)  # Lx_eff=Lx, Ly_eff=Ly para forma 4
        D_avg = D1 * (1 + Ly_eff / Lx_eff + L_hyp / Lx_eff) / 3 if Lx_eff > 0 else D1
    elif forma == 5:
        D_avg = D1_esc * (1 + Lb_e / La + Lc_e / La) / 3 if La > 0 else D1_esc
    else:
        D_avg = (Dx + Dy) / 2
    r["D_avg"] = round(D_avg, 4)

    # ── Kii, Kh (Ec. 87, 88) ─────────────────────────────────────────────────
    # Kii: uv=0 (sin varillas) → (1/(2n))^(2/n); uv>0 → 1
    Kii = 1.0 if uv > 0 else ((1 / (2 * n)) ** (2 / n) if n > 0 else 1.0)
    Kh  = math.sqrt(1.0 + h / 1.0)         # h₀ = 1 m
    r["Kii"] = round(Kii, 6); r["Kh"] = round(Kh, 6)

    # ── Km (Ec. 86) ───────────────────────────────────────────────────────────
    if D_avg > 0 and h > 0 and d_con > 0 and n > 1:
        ln1 = math.log(D_avg**2 / (16 * h * d_con)
                       + (D_avg + 2 * h)**2 / (8 * D_avg * d_con)
                       - h / (4 * d_con))
        ln2 = math.log(8 / (math.pi * (2 * n - 1)))
        Km = (1 / (2 * math.pi)) * (ln1 + (Kii / Kh) * ln2)
    else:
        Km = 0.0
    r["Km"] = round(Km, 6)

    # ── Ks (Ec. 99) ───────────────────────────────────────────────────────────
    if D_avg > 0 and h > 0:
        Ks = (1 / math.pi) * (1 / (2 * h) + 1 / (D_avg + h) + (1 / D_avg) * (1 - 0.5 ** (n - 2)))
    else:
        Ks = 0.0
    r["Ks"] = round(Ks, 6)

    # ── LM, LS (Ec. 96, 98) ───────────────────────────────────────────────────
    # LM: sin varillas → Lc + LR (LR=0 → LM=Lc)
    #     con varillas → Lc + (1.55 + 1.22·Lr/√(Lx_eff²+Ly_eff²))·LR
    if uv == 0 or LR <= 0:
        LM = Lc + LR
    else:
        LM = Lc + (1.55 + 1.22 * (Lr / diag_eff)) * LR if diag_eff > 0 else Lc
    LS = 0.75 * Lc + 0.85 * LR
    r["LM"] = round(LM, 4); r["LS"] = round(LS, 4)

    # ── Em, Es (Ec. 85, 97) ───────────────────────────────────────────────────
    Em = rho * Km * Ki * IG_A / LM if LM > 0 else 0.0
    Es = rho * Ks * Ki * IG_A / LS if LS > 0 else 0.0
    r["Em_V"] = round(Em, 4); r["Es_V"] = round(Es, 4)

    # ── Verificación final (§16.5) ─────────────────────────────────────────────
    em_ok = Em < E_touch_V
    es_ok = Es < E_step_V
    aprobado = em_ok and es_ok
    r["em_ok"] = em_ok; r["es_ok"] = es_ok; r["aprobado"] = aprobado
    if aprobado:
        veredicto = "✔  DISEÑO ACEPTABLE — Em < E_touch  y  Es < E_step"
    elif not em_ok:
        veredicto = f"✘  NO ACEPTABLE — Em={round(Em,2)} V ≥ E_touch={round(E_touch_V,2)} V"
    else:
        veredicto = f"✘  NO ACEPTABLE — Es={round(Es,2)} V ≥ E_step={round(E_step_V,2)} V"
    r["veredicto"] = veredicto
    return r


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL — calcula todas las secciones en secuencia
# ══════════════════════════════════════════════════════════════════════════════

def calcular_malla(p):
    """
    Ejecuta todas las secciones en orden y retorna un dict con todos los
    resultados intermedios y finales, organizados por sección.

    Parámetros (dict p):
      forma         : int 1-7  (codificación Excel)
      Lx, Ly        : [m] dimensiones para rect/L/T y tri.rect.
      L             : [m] lado equilátero
      Lb, Li        : [m] base y lado igual isósceles
      La, Lb_e, Lc_e: [m] lados escaleno
      Lx1,Ly1,Lx2,Ly2: [m] recortes para L/T
      Dx, Dy        : [m] espaciamientos para rect/L/T
      D             : [m] espaciamiento equilátero
      Db            : [m] espaciamiento base isósceles
      D1            : [m] espaciamiento primario tri.rect.
      D1_esc        : [m] espaciamiento primario escaleno
      rho           : [Ω·m] resistividad del terreno
      h             : [m]  profundidad de enterramiento
      Lr, b         : [m]  longitud y radio de varilla
      uv            : int 0-3  ubicación de varillas
      material_id   : int 1-10
      I_falla       : [kA]
      tc, tf        : [s]
      XR            : relación X/R
      Sf            : factor de división de corriente
      Tamb          : [°C]
      mat_sup_id    : int 1-12 (Tabla 7)
      condicion     : 'Dry' o 'Wet'
      val_uso       : 'Mínimo' o 'Máximo'
      rho_s_custom  : [Ω·m] solo si mat_sup_id=12
      hs, ts        : [m], [s]
      peso          : 50 o 70 [kg]
    """
    out = {}

    forma   = int(p["forma"])
    Lx      = float(p.get("Lx",  0));  Ly      = float(p.get("Ly",  0))
    L       = float(p.get("L",   0))
    Lb      = float(p.get("Lb",  0));  Li      = float(p.get("Li",  0))
    La      = float(p.get("La",  0))
    Lb_e    = float(p.get("Lb_e",0));  Lc_e    = float(p.get("Lc_e",0))
    Lx1     = float(p.get("Lx1", 0));  Ly1     = float(p.get("Ly1", 0))
    Lx2     = float(p.get("Lx2", 0));  Ly2     = float(p.get("Ly2", 0))
    Dx      = float(p.get("Dx",  0));  Dy      = float(p.get("Dy",  0))
    D       = float(p.get("D",   0))
    Db      = float(p.get("Db",  0))
    D1      = float(p.get("D1",  0))
    D1_esc  = float(p.get("D1_esc", 0))
    rho     = float(p["rho"]);         h       = float(p["h"])
    Lr      = float(p["Lr"]);          b       = float(p["b"])
    uv      = int(p["uv"])
    peso    = int(p.get("peso", 50))
    hs      = float(p["hs"]);          ts      = float(p["ts"])

    # §2 — Calibre
    s2 = sec2_calibre(p["material_id"], float(p["I_falla"]),
                      float(p["tc"]), float(p["tf"]), float(p["XR"]), float(p["Tamb"]))
    if "error" in s2:
        return {"error_sec2": s2["error"]}
    out["sec2"] = s2
    a_cond = s2["radio_m"]
    d_cond = s2["diametro_m"]
    Df     = s2["Df"]

    # §3 — Geometría
    s3 = sec3_geometria(forma, Dx=Dx, Dy=Dy, D=D, Db=Db, D1=D1, D1_esc=D1_esc,
                        Lx=Lx, Ly=Ly, L=L, Lb=Lb, Li=Li,
                        La=La, Lb_e=Lb_e, Lc_e=Lc_e,
                        Lx1=Lx1, Ly1=Ly1, Lx2=Lx2, Ly2=Ly2,
                        uv=uv, Lr=Lr)
    # uv=4: configuración personalizada — nR viene del frontend
    if uv == 4:
        nR_cust    = int(p.get("nR_custom", 0))
        s3["nR"]   = nR_cust
        s3["LR"]   = round(nR_cust * Lr, 4)
        s3["LT"]   = round(s3["Lc"] + s3["LR"], 4)
    out["sec3"] = s3
    A      = s3["A"]
    Lc     = s3["Lc"]
    LR     = s3["LR"]
    LT     = s3["LT"]
    nR     = s3["nR"]
    Lp     = s3["Lp"]
    Dm     = s3["Dm"]
    Lx_eff = s3["Lx_eff"]
    Ly_eff = s3["Ly_eff"]

    # §4 — Corrientes
    s4 = sec4_corrientes(float(p["I_falla"]), float(p["Sf"]), Df)
    out["sec4"] = s4
    IG_A = s4["IG_A"]

    # §6 — Tensiones admisibles (necesita rho_s)
    sup = get_rho_s(int(p.get("mat_sup_id", 4)),
                    p.get("condicion", "Wet"),
                    p.get("val_uso", "Mínimo"),
                    p.get("rho_s_custom"))
    out["superficie"] = sup
    if "error" in sup:
        return {**out, "error_sup": sup["error"]}
    rho_s = sup["rho_s"]
    s6 = sec6_tensiones(rho, rho_s, hs, ts, peso)
    out["sec6"] = s6

    # §5 — Resistencia Rg
    metodo_rg = str(p.get("metodo_rg", "schwarz")).lower() if nR > 0 else "sverak"
    s5 = sec5_resistencia(rho, h, A, Lc, LT, nR, Lr, b, a_cond, forma,
                          Lx=Lx, Ly=Ly, L=L, Lb=Lb, Li=Li,
                          La=La, Lb_e=Lb_e, Lc_e=Lc_e,
                          metodo_rg=metodo_rg)
    if "error" in s5:
        return {**out, "error_sec5": s5["error"]}
    out["sec5"] = s5
    Rg = s5["Rg"]

    # §7 — GPR
    s7 = sec7_gpr(IG_A, Rg, s6["E_touch_V"])
    out["sec7"] = s7

    # §8 — Em y Es
    # D promedio isósceles para sec8: (Db + Di)/2
    Di_iso = Db * (Li / Lb) if (forma == 3 and Lb > 0) else 0
    D_iso_avg = (Db + Di_iso) / 2 if forma == 3 else 0

    s8 = sec8_voltajes(rho=rho, h=h, forma=forma, uv=uv,
                       Lc=Lc, LR=LR, Lr=Lr, nR=nR,
                       Lx_eff=Lx_eff, Ly_eff=Ly_eff, Lp=Lp, Dm=Dm, A=A,
                       Dx=Dx, Dy=Dy,
                       D=D_iso_avg if forma == 3 else D,
                       Db=Db, D1=D1, D1_esc=D1_esc,
                       La=La, Lb_e=Lb_e, Lc_e=Lc_e,
                       IG_A=IG_A, d_con=d_cond,
                       E_touch_V=s6["E_touch_V"], E_step_V=s6["E_step_V"])
    out["sec8"] = s8

    # Listas D
    out["listas_d"] = listas_d(forma, Lx=Lx, Ly=Ly, L=L, Lb=Lb, Li=Li,
                                La=La, Lb_e=Lb_e, Lc_e=Lc_e)

    # Recomendaciones contextuales
    out["recomendaciones"] = _generar_recomendaciones(p, out)

    return out


# ══════════════════════════════════════════════════════════════════════════════
# RECOMENDACIONES CONTEXTUALES
# ══════════════════════════════════════════════════════════════════════════════

def _generar_recomendaciones(p, out):
    """
    Devuelve dict con claves 'rg', 'gpr', 'em', 'es' solo para los
    criterios que fallan. Si todo cumple, devuelve {}.
    """
    s3  = out.get("sec3", {})
    s5  = out.get("sec5", {})
    s6  = out.get("sec6", {})
    s7  = out.get("sec7", {})
    s8  = out.get("sec8", {})
    sup = out.get("superficie", {})
    ld  = out.get("listas_d", {})

    ok_Rg  = float(s5.get("Rg",  999)) <= 1.0
    ok_GPR = bool(s7.get("gpr_ok", False))
    ok_Em  = bool(s8.get("em_ok",  False))
    ok_Es  = bool(s8.get("es_ok",  False))

    rec = {}

    # ── Modelos de varilla disponibles ────────────────────────────────────────
    MODELOS_LR = [1.5, 2.4, 3.0, 4.5, 6.0]
    Lr_actual = float(p.get("Lr", 1.8))

    # ── D actual según forma ──────────────────────────────────────────────────
    forma = int(p.get("forma", 1))
    Dx = float(p.get("Dx") or 0); Dy = float(p.get("Dy") or 0)

    def _closest_smaller(lista, ref, n=5):
        """Devuelve los n valores más cercanos por debajo de ref (paso siguiente lógico)."""
        menores = sorted([d for d in lista if d < ref - 1e-9], reverse=True)
        return menores[:n]

    if forma in (1, 6, 7):
        # Mantener Dx y Dy separados para mostrárselos al usuario con precisión
        D_actual = None   # no se usa para forma 1/6/7
        Dx_menores = _closest_smaller(ld.get("lista_Dx", []), Dx)
        Dy_menores = _closest_smaller(ld.get("lista_Dy", []), Dy)
        D_menores  = []   # no se usa para forma 1/6/7
    else:
        if forma == 2:
            D_actual = float(p.get("D") or 0)
            lista_raw = ld.get("lista_D", [])
        elif forma == 3:
            D_actual = float(p.get("Db") or 0)
            lista_raw = ld.get("lista_Db", [])
        elif forma == 4:
            D_actual = float(p.get("D1") or 0)
            lista_raw = ld.get("lista_D1", [])
        else:
            D_actual = float(p.get("D1_esc") or 0)
            lista_raw = ld.get("lista_D1", [])
        D_menores  = _closest_smaller(lista_raw, D_actual)
        Dx_menores = []
        Dy_menores = []

    # Configuración de varillas
    uv = int(p.get("uv", 0))
    _cfg = {0: "sin varillas", 1: "solo esquinas",
            2: "perímetro", 3: "todas las intersecciones",
            4: "personalizado"}
    config_varillas = _cfg.get(uv, "desconocida")

    # ── Criterio 1: Rg ───────────────────────────────────────────────────────
    if not ok_Rg:
        h_val = float(p.get("h", 0.5))
        rec["rg"] = {
            "Lx":              float(p.get("Lx", p.get("L", 0))),
            "Ly":              float(p.get("Ly", p.get("L", 0))),
            "A":               round(float(s3.get("A", 0)), 2),
            "h":               h_val,
            "h_en_limite":     h_val >= 1.5,
            "Lr_actual":       Lr_actual,
            "Lr_modelos_mayores": [m for m in MODELOS_LR if m > Lr_actual + 1e-9],
        }

    # ── Criterio 2: GPR ──────────────────────────────────────────────────────
    if not ok_GPR:
        rec["gpr"] = {
            "Sf":      float(p.get("Sf", 1.0)),
            "Etouch":  round(float(s6.get("E_touch_V", 0)), 2),
            "tf":      float(p.get("tf", 0.5)),
        }

    # ── Criterio 3: Em ───────────────────────────────────────────────────────
    if not ok_Em:
        _JERARQUIA_UV = ["sin varillas", "solo esquinas", "perímetro", "todas las intersecciones"]
        _idx_uv = _JERARQUIA_UV.index(config_varillas) if config_varillas in _JERARQUIA_UV else -1
        _configuraciones_mayores = _JERARQUIA_UV[_idx_uv + 1:] if _idx_uv >= 0 else []
        em_entry = {
            "Nr":                      int(s3.get("nR", 0)),
            "configuracion_actual":    config_varillas,
            "configuraciones_mayores": _configuraciones_mayores,
            "Lr_actual":               Lr_actual,
            "Lr_modelos_mayores":      [m for m in MODELOS_LR if m > Lr_actual + 1e-9],
        }
        if forma in (1, 6, 7):
            em_entry["Dx"]        = round(Dx, 4)
            em_entry["Dy"]        = round(Dy, 4)
            em_entry["Dx_menores"] = Dx_menores
            em_entry["Dy_menores"] = Dy_menores
        else:
            em_entry["D"]         = round(D_actual, 4)
            em_entry["D_menores"] = D_menores
        rec["em"] = em_entry

    # ── Criterio 4: Es ───────────────────────────────────────────────────────
    if not ok_Es:
        hs_val     = float(p.get("hs", 0.1))
        rho_s_act  = float(sup.get("rho_s", 0))
        condicion  = p.get("condicion", "Wet")
        val_uso    = p.get("val_uso", "Mínimo")
        esHum      = condicion == "Wet"
        esMin      = val_uso == "Mínimo"

        # Recopilar todos los ρs de materiales 1-11 con la misma condición/uso
        _rhos_disp = []
        for _mid, _mat in MATERIALES_SUPERFICIE.items():
            if _mid == 12:
                continue
            lo = _mat["hum_min"] if esHum else _mat["seco_min"]
            hi = _mat["hum_max"] if esHum else _mat["seco_max"]
            v  = lo if esMin else hi
            if v is not None:
                _rhos_disp.append(float(v))

        rho_s_mayores = sorted(set(
            v for v in _rhos_disp if v > rho_s_act + 1e-6
        ))

        rec["es"] = {
            "rho_s":          round(rho_s_act, 2),
            "rho_s_mayores":  [round(v, 2) for v in rho_s_mayores],
            "hs":             round(hs_val, 3),
            "hs_en_limite":   hs_val >= 0.150,
            "Cs":             round(float(s6.get("Cs", 1.0)), 4),
            "Estep":          round(float(s6.get("E_step_V", 0)), 2),
            "tf":             float(p.get("tf", 0.5)),
        }

    return rec


