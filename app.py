import math
import streamlit as st

# ==========================
# 1. CONSTANTES Y TABLAS
# ==========================

GAMMA = {"Cu": 56, "Al": 35}  # m / (Ω·mm²)
SECCIONES_NORM = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]

# TABLA Iz (EJEMPLO). Estructura preparada para que tú la rellenes con REBT/UNE.
# Clave: (material, aislamiento, metodo, n_cond) -> {seccion_mm2: Iz}
TABLA_IZ = {
    ("Cu", "PVC", "C", 2): {
        1.5: 18, 2.5: 24, 4: 32, 6: 41, 10: 57, 16: 76, 25: 99, 35: 123, 50: 150,
    },
    ("Cu", "PVC", "B1", 2): {
        1.5: 16, 2.5: 21, 4: 28, 6: 36, 10: 50, 16: 68, 25: 89, 35: 110, 50: 135,
    },
    # Ejemplos adicionales para que veas la estructura:
    ("Cu", "PVC", "A1", 2): {
        1.5: 14, 2.5: 18, 4: 24, 6: 31, 10: 42, 16: 57,
    },
    ("Cu", "PVC", "A2", 2): {
        1.5: 15, 2.5: 20, 4: 26, 6: 34, 10: 46, 16: 62,
    },
    ("Cu", "PVC", "D", 2): {
        1.5: 19, 2.5: 26, 4: 34, 6: 44, 10: 61, 16: 82,
    },
    # Añade aquí A1, A2, B2, E, F, XLPE, Al, 3 conductores, etc.
}

# Factores de corrección por temperatura (ejemplo)
FACT_TEMP = {
    "PVC": [
        (10, 25, 1.03),
        (25, 30, 1.00),
        (30, 35, 0.94),
        (35, 40, 0.87),
        (40, 45, 0.79),
        (45, 50, 0.71),
    ],
    "XLPE": [
        (10, 25, 1.04),
        (25, 30, 1.00),
        (30, 35, 0.96),
        (35, 40, 0.91),
        (40, 45, 0.87),
        (45, 50, 0.82),
    ],
}

# Factores de agrupamiento (ejemplo)
FACT_AGRUP = {
    ("C", 1): 1.00,
    ("C", 2): 0.80,
    ("C", 3): 0.70,
    ("C", 4): 0.65,
    ("B1", 1): 1.00,
    ("B1", 2): 0.85,
    ("B1", 3): 0.80,
    ("A1", 1): 1.00,
    ("A1", 2): 0.85,
    ("A2", 1): 1.00,
    ("A2", 2): 0.85,
    # Amplía según tus tablas
}

# Tabla de magnetotérmicos (ejemplo)
MAGNETOS = [
    {"In": 6, "curva": "C", "poder_corte_kA": 6},
    {"In": 10, "curva": "C", "poder_corte_kA": 6},
    {"In": 16, "curva": "C", "poder_corte_kA": 6},
    {"In": 20, "curva": "C", "poder_corte_kA": 6},
    {"In": 25, "curva": "C", "poder_corte_kA": 6},
    {"In": 32, "curva": "C", "poder_corte_kA": 6},
    {"In": 40, "curva": "C", "poder_corte_kA": 6},
    {"In": 50, "curva": "C", "poder_corte_kA": 6},
    {"In": 63, "curva": "C", "poder_corte_kA": 6},
    # Añade B, D, otros poderes de corte, etc.
]

# Tabla de tubos (MUY simplificada)
TUBOS = {
    16: {"S_util_mm2": 120, "max_conductores": 6},
    20: {"S_util_mm2": 200, "max_conductores": 9},
    25: {"S_util_mm2": 320, "max_conductores": 12},
    32: {"S_util_mm2": 530, "max_conductores": 16},
}

# ==========================
# 2. FUNCIONES DE CÁLCULO
# ==========================

def intensidad_desde_potencia(P_w, U_v, cos_phi, trifasico=False):
    if trifasico:
        return P_w / (math.sqrt(3) * U_v * cos_phi)
    return P_w / (U_v * cos_phi)

def iz_base(material, aislamiento, metodo, n_cond, seccion):
    clave = (material, aislamiento, metodo, n_cond)
    tabla = TABLA_IZ.get(clave, {})
    return tabla.get(seccion, None)

def factor_temp(aislamiento, T_amb):
    rangos = FACT_TEMP.get(aislamiento, [])
    for t_min, t_max, f in rangos:
        if t_min <= T_amb <= t_max:
            return f
    return 1.0

def factor_agrup(metodo, n_circ):
    return FACT_AGRUP.get((metodo, n_circ), 1.0)

def iz_corregida(material, aislamiento, metodo, n_cond, T_amb, n_circ, seccion):
    Iz = iz_base(material, aislamiento, metodo, n_cond, seccion)
    if Iz is None:
        return None
    ft = factor_temp(aislamiento, T_amb)
    fa = factor_agrup(metodo, n_circ)
    return Iz * ft * fa

def seccion_por_caida(I, L, U_v, delta_u_pct, cos_phi, material, trifasico=False):
    gamma = GAMMA[material]
    delta_u = (delta_u_pct / 100) * U_v
    if trifasico:
        S = math.sqrt(3) * L * I * cos_phi / (gamma * delta_u)
    else:
        S = 2 * L * I * cos_phi / (gamma * delta_u)
    return S

def normalizar_seccion(S_calc):
    for s in SECCIONES_NORM:
        if s >= S_calc:
            return s
    return SECCIONES_NORM[-1]

def calcular_seccion(Ib, L, U_v, delta_u_pct, cos_phi,
                     material, aislamiento, metodo, n_cond, T_amb, n_circ,
                     trifasico=False):
    S_ct = seccion_por_caida(Ib, L, U_v, delta_u_pct, cos_phi, material, trifasico)

    S_Iz = None
    Iz_corr_elegida = None
    for s in SECCIONES_NORM:
        Iz_corr = iz_corregida(material, aislamiento, metodo, n_cond, T_amb, n_circ, s)
        if Iz_corr is None:
            continue
        if Iz_corr >= Ib:
            S_Iz = s
            Iz_corr_elegida = Iz_corr
            break

    S_final_calc = max(S_ct, S_Iz if S_Iz is not None else S_ct)
    S_norm = normalizar_seccion(S_final_calc)

    return {
        "S_ct": S_ct,
        "S_Iz": S_Iz,
        "S_final_calc": S_final_calc,
        "S_norm": S_norm,
        "Iz_corr": Iz_corr_elegida,
    }

def seccion_pe(S_fase):
    if S_fase <= 16:
        return S_fase
    elif S_fase <= 35:
        return 16
    else:
        return S_fase / 2

def seleccionar_magnetotermico(Ib, Iz_corr, Icc, curva="C"):
    candidatos = [
        m for m in MAGNETOS
        if m["curva"] == curva and Ib <= m["In"] <= Iz_corr
    ]
    if not candidatos:
        return None

    m = min(candidatos, key=lambda x: x["In"])
    Icc_kA = Icc / 1000 if Icc is not None else None
    cumple_poder_corte = None
    if Icc_kA is not None:
        cumple_poder_corte = m["poder_corte_kA"] >= Icc_kA

    check_carga = Ib <= m["In"] <= Iz_corr

    return {
        "descripcion": f"{m['In']} A curva {m['curva']} ({m['poder_corte_kA']} kA)",
        "In": m["In"],
        "check_carga": check_carga,
        "cumple_poder_corte": cumple_poder_corte,
        "Icc_kA": Icc_kA,
    }

def cc_simplificado_por_longitud(U_v, L, S_mm2, material):
    rho_20 = 1 / GAMMA[material]  # Ω·mm²/m
    Z = rho_20 * (2 * L) / S_mm2
    if Z <= 0:
        return None, None
    Icc = U_v / Z
    return Icc, Z

def verificar_tubo(diam_mm, secciones, n_por_seccion):
    tubo = TUBOS.get(diam_mm)
    if tubo is None:
        return None
    S_util = tubo["S_util_mm2"]
    S_ocupada = sum(s * n for s, n in zip(secciones, n_por_seccion))
    n_total = sum(n_por_seccion)
    return {
        "S_ocupada": S_ocupada,
        "S_util": S_util,
        "porcentaje": 100 * S_ocupada / S_util,
        "n_total": n_total,
        "n_max": tubo["max_conductores"],
    }

# ==========================
# 3. PANTALLAS STREAMLIT
# ==========================

def pantalla_seccion_protecciones():
    st.header("Sección de conductores y protecciones (ITC-BT-19 / 20)")

    col1, col2 = st.columns(2)
    with col1:
        modo = st.radio("Dato de partida", ["Potencia", "Intensidad"])
        trifasico = st.checkbox("Trifásico", value=False)
        U_v = st.number_input("Tensión (V)", value=400 if trifasico else 230)
        cos_phi = st.number_input("Cos φ", value=0.95, min_value=0.1, max_value=1.0, step=0.01)
        L = st.number_input("Longitud (m)", value=20.0, min_value=1.0, step=1.0)
        tipo_circuito = st.selectbox("Tipo de circuito", ["Iluminación", "Tomas / Fuerza"])
        if tipo_circuito == "Iluminación":
            delta_u_pct = st.number_input("Caída máxima (%)", value=3.0, min_value=0.5, max_value=10.0, step=0.5)
        else:
            delta_u_pct = st.number_input("Caída máxima (%)", value=5.0, min_value=0.5, max_value=10.0, step=0.5)

    with col2:
        material = st.selectbox("Material", ["Cu", "Al"])
        aislamiento = st.selectbox("Aislamiento", ["PVC", "XLPE"])
        metodo = st.selectbox("Método instalación", ["A1", "A2", "B1", "C", "D"])
        n_cond = st.number_input("Conductores cargados", value=2, min_value=1, max_value=3)
        T_amb = st.number_input("Temperatura ambiente (°C)", value=30.0, min_value=10.0, max_value=60.0)
        n_circ = st.number_input("Circuitos agrupados", value=1, min_value=1, max_value=9)
        curva = st.selectbox("Curva magnetotérmico", ["B", "C", "D"], index=1)

    if modo == "Potencia":
        P = st.number_input("Potencia (W)", value=3500.0, min_value=1.0, step=100.0)
        Ib = intensidad_desde_potencia(P, U_v, cos_phi, trifasico)
        st.metric("Intensidad de diseño Ib", f"{Ib:.2f} A")
    else:
        Ib = st.number_input("Intensidad de diseño Ib (A)", value=16.0, min_value=0.1, step=0.5)

    if st.button("Calcular sección y protección"):
        res = calcular_seccion(
            Ib, L, U_v, delta_u_pct, cos_phi,
            material, aislamiento, metodo, int(n_cond), T_amb, int(n_circ),
            trifasico,
        )

        st.subheader("Resultados de sección")
        colr1, colr2 = st.columns(2)
        with colr1:
            st.write(f"**Sección por caída de tensión:** {res['S_ct']:.2f} mm²")
            st.write(f"**Sección por intensidad admisible:** {res['S_Iz']} mm²")
        with colr2:
            st.write(f"**Sección calculada final:** {res['S_final_calc']:.2f} mm²")
            st.write(f"**Sección normalizada recomendada:** {res['S_norm']} mm²")
            st.write(f"**Iz corregida aprox.:** {res['Iz_corr']:.1f} A" if res["Iz_corr"] else "Iz corregida: N/D")

        if res["S_norm"]:
            S_pe = seccion_pe(res["S_norm"])
            st.write(f"**Sección mínima PE (regla simplificada):** {S_pe:.1f} mm²")

        st.subheader("Cortocircuito simplificado en extremo de línea")
        Icc, Z = cc_simplificado_por_longitud(U_v, L, res["S_norm"], material)
        if Icc is not None:
            st.write(f"**Impedancia de línea aprox.:** {Z:.3f} Ω")
            st.write(f"**Icc presumible:** {Icc:.0f} A")
        else:
            st.write("No se ha podido calcular Icc (revisa datos).")

        st.subheader("Protección recomendada")
        if res["Iz_corr"] is not None and Icc is not None:
            prot = seleccionar_magnetotermico(Ib, res["Iz_corr"], Icc, curva="C" if curva != "B" and curva != "D" else curva)
            if prot:
                st.write(f"**Magnetotérmico sugerido:** {prot['descripcion']}")
                st.write(f"**Ib ≤ In ≤ Iz_corr:** {prot['check_carga']}")
                if prot["cumple_poder_corte"] is not None:
                    if prot["cumple_poder_corte"]:
                        st.success(
                            f"Poder de corte suficiente: {prot['descripcion']} con Icc ≈ {prot['Icc_kA']:.2f} kA."
                        )
                    else:
                        st.error(
                            f"Poder de corte insuficiente: {prot['descripcion']} con Icc ≈ {prot['Icc_kA']:.2f} kA."
                        )
            else:
                st.warning("No se ha encontrado magnetotérmico que cumpla Ib ≤ In ≤ Iz_corr con la tabla actual.")
        else:
            st.warning("No se ha podido verificar protección (falta Iz_corr o Icc).")

def pantalla_tubos():
    st.header("Canalizaciones y tubos (ITC-BT-21 simplificada)")

    diam = st.selectbox("Diámetro de tubo (mm)", list(TUBOS.keys()))
    n_tipos = st.number_input("Número de tipos de conductor en el tubo", value=1, min_value=1, max_value=5)

    secciones = []
    n_por_seccion = []
    for i in range(int(n_tipos)):
        col1, col2 = st.columns(2)
        with col1:
            s = st.number_input(f"Sección tipo {i+1} (mm²)", value=2.5, min_value=0.5, step=0.5, key=f"s_{i}")
        with col2:
            n = st.number_input(f"Nº conductores tipo {i+1}", value=2, min_value=1, step=1, key=f"n_{i}")
        secciones.append(s)
        n_por_seccion.append(n)

    if st.button("Verificar tubo"):
        res = verificar_tubo(diam, secciones, n_por_seccion)
        if res is None:
            st.error("No hay datos para ese diámetro de tubo.")
        else:
            st.write(f"**Sección ocupada aprox.:** {res['S_ocupada']:.1f} mm²")
            st.write(f"**Sección útil aprox.:** {res['S_util']:.1f} mm²")
            st.write(f"**Porcentaje ocupación:** {res['porcentaje']:.1f} %")
            st.write(f"**Nº conductores total:** {res['n_total']} (máx. recomendado: {res['n_max']})")

            if res["porcentaje"] > 40 or res["n_total"] > res["n_max"]:
                st.warning("Ocupación elevada: revisa diámetro de tubo o número de conductores.")
            else:
                st.success("Ocupación de tubo razonable con los datos simplificados.")

def pantalla_cc():
    st.header("Cortocircuito y poder de corte (entrada manual)")

    U_v = st.number_input("Tensión (V)", value=230)
    Icc = st.number_input("Icc presumible (A)", value=6000.0, min_value=100.0, step=100.0)
    poder_corte = st.number_input("Poder de corte del magnetotérmico (kA)", value=6.0, min_value=3.0, step=1.0)

    if st.button("Verificar poder de corte"):
        Icc_kA = Icc / 1000
        st.metric("Icc (kA)", f"{Icc_kA:.2f} kA")
        if poder_corte >= Icc_kA:
            st.success(f"Poder de corte suficiente ({poder_corte} kA ≥ {Icc_kA:.2f} kA).")
        else:
            st.error(f"Poder de corte insuficiente ({poder_corte} kA < {Icc_kA:.2f} kA).")

def pantalla_resumen():
    st.header("Resumen / Notas")
    st.markdown(
        """
        **Notas importantes:**

        - Las tablas de Iz, factores de corrección, tubos y magnetotérmicos están **simplificadas**.
        - Para uso profesional, debes sustituirlas por datos completos del REBT/UNE y catálogos de fabricante.
        - La lógica de cálculo está preparada para que solo tengas que ampliar las tablas.
        - Ya incluye:
          - Cálculo de sección por Iz y caída de tensión.
          - Verificación Ib ≤ In ≤ Iz_corr.
          - Cálculo simplificado de Icc y comprobación de poder de corte.
          - Cálculo simplificado de sección de PE.
          - Verificación básica de ocupación de tubos.
        """
    )

# ==========================
# 4. APLICACIÓN PRINCIPAL
# ==========================

st.set_page_config(page_title="SEA – REBT Suite", page_icon="⚡", layout="centered")

def main():
    st.title("SEA – Calculadora REBT (app.py único)")

    modulo = st.sidebar.selectbox(
        "Módulo",
        [
            "Sección y protecciones",
            "Canalizaciones y tubos",
            "Cortocircuito y poder de corte",
            "Resumen / Notas",
        ],
    )

    if modulo == "Sección y protecciones":
        pantalla_seccion_protecciones()
    elif modulo == "Canalizaciones y tubos":
        pantalla_tubos()
    elif modulo == "Cortocircuito y poder de corte":
        pantalla_cc()
    else:
        pantalla_resumen()

if __name__ == "__main__":
    main()
