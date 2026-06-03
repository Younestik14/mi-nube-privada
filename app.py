# app.py  -- PARTE 1
import math
import io
import json
import pandas as pd
import streamlit as st
from typing import Optional, Dict, Any, List, Tuple

# ==========================
# CONSTANTES Y TABLAS POR DEFECTO
# ==========================

GAMMA = {"Cu": 56.0, "Al": 35.0}  # m/(Ω·mm²) conductividad aproximada
SECCIONES_NORM = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]

# TABLA Iz por defecto (ejemplo). Estructura: DataFrame con columnas:
# material, aislamiento, metodo, n_cond, seccion_mm2, Iz_A
DF_IZ_DEFAULT = pd.DataFrame([
    ["Cu","PVC","A1",1,1.5,14],
    ["Cu","PVC","A1",1,2.5,18],
    ["Cu","PVC","A1",1,4.0,24],
    ["Cu","PVC","B1",2,1.5,16],
    ["Cu","PVC","B1",2,2.5,21],
    ["Cu","PVC","B1",2,4.0,28],
    ["Cu","PVC","C",2,1.5,18],
    ["Cu","PVC","C",2,2.5,24],
    ["Cu","PVC","C",2,4.0,32],
    # Añade más filas reales según REBT
], columns=["material","aislamiento","metodo","n_cond","seccion_mm2","Iz_A"])

# Factores temperatura por defecto: DataFrame con columnas: aislamiento, t_min, t_max, factor
DF_FACT_TEMP_DEFAULT = pd.DataFrame([
    ["PVC",10,25,1.03],
    ["PVC",25,30,1.00],
    ["PVC",30,35,0.94],
    ["PVC",35,40,0.87],
    ["PVC",40,45,0.79],
    ["PVC",45,50,0.71],
    ["XLPE",10,25,1.04],
    ["XLPE",25,30,1.00],
    ["XLPE",30,35,0.96],
], columns=["aislamiento","t_min","t_max","factor"])

# Factores agrupamiento por defecto: DataFrame con columnas: metodo, n_circuitos, factor
DF_FACT_AGRUP_DEFAULT = pd.DataFrame([
    ["A1",1,1.00],
    ["A1",2,0.85],
    ["A2",1,1.00],
    ["B1",1,1.00],
    ["B1",2,0.85],
    ["C",1,1.00],
    ["C",2,0.80],
    ["C",3,0.70],
], columns=["metodo","n_circuitos","factor"])

# Magnetos por defecto: DataFrame con columnas: In_A, curva, poder_corte_kA
DF_MAGNETOS_DEFAULT = pd.DataFrame([
    [6,"B",6],
    [6,"C",6],
    [10,"B",6],
    [10,"C",6],
    [16,"C",6],
    [20,"C",6],
    [25,"C",6],
    [32,"C",6],
    [40,"C",6],
    [50,"C",6],
    [63,"C",10],
], columns=["In_A","curva","poder_corte_kA"])

# Tubos por defecto: DataFrame con columnas: diam_mm, area_util_mm2, max_conductores
DF_TUBOS_DEFAULT = pd.DataFrame([
    [16,120,6],
    [20,200,9],
    [25,320,12],
    [32,530,16],
    [40,800,20],
], columns=["diam_mm","area_util_mm2","max_conductores"])

# ==========================
# FUNCIONES DE CARGA Y EDICIÓN DE TABLAS
# ==========================

@st.cache_data
def cargar_tablas_default() -> Dict[str, pd.DataFrame]:
    return {
        "iz": DF_IZ_DEFAULT.copy(),
        "fact_temp": DF_FACT_TEMP_DEFAULT.copy(),
        "fact_agrup": DF_FACT_AGRUP_DEFAULT.copy(),
        "magnetos": DF_MAGNETOS_DEFAULT.copy(),
        "tubos": DF_TUBOS_DEFAULT.copy(),
    }

def cargar_csv_usuario(uploaded_file) -> Optional[pd.DataFrame]:
    try:
        return pd.read_csv(uploaded_file)
    except Exception:
        try:
            uploaded_file.seek(0)
            return pd.read_excel(uploaded_file)
        except Exception:
            return None

def merge_tabla(base: pd.DataFrame, nueva: pd.DataFrame, key_cols: List[str]) -> pd.DataFrame:
    """
    Reemplaza filas de base por filas de nueva según key_cols, añade nuevas filas.
    """
    if nueva is None or nueva.empty:
        return base
    base = base.copy()
    nueva = nueva.copy()
    # crear índice compuesto
    base["_key"] = base[key_cols].astype(str).agg("|".join, axis=1)
    nueva["_key"] = nueva[key_cols].astype(str).agg("|".join, axis=1)
    # eliminar claves en base que aparecen en nueva
    base = base[~base["_key"].isin(nueva["_key"])]
    resultado = pd.concat([base.drop(columns=["_key"]), nueva.drop(columns=["_key"])], ignore_index=True)
    return resultado

def df_to_options(df: pd.DataFrame, cols: List[str]) -> List[Tuple]:
    return [tuple(row) for row in df[cols].drop_duplicates().itertuples(index=False, name=None)]

# ==========================
# UTILIDADES
# ==========================

def formato_num(x, n=2):
    try:
        return f"{float(x):.{n}f}"
    except Exception:
        return str(x)
# app.py  -- PARTE 2
# ==========================
# NÚCLEO DE CÁLCULOS
# ==========================

def intensidad_desde_potencia(P_w: float, U_v: float, cos_phi: float, trifasico: bool=False) -> float:
    if trifasico:
        return P_w / (math.sqrt(3) * U_v * cos_phi)
    return P_w / (U_v * cos_phi)

def buscar_iz_base(df_iz: pd.DataFrame, material: str, aislamiento: str, metodo: str, n_cond: int, seccion: float) -> Optional[float]:
    q = df_iz[
        (df_iz["material"] == material) &
        (df_iz["aislamiento"] == aislamiento) &
        (df_iz["metodo"] == metodo) &
        (df_iz["n_cond"] == n_cond) &
        (df_iz["seccion_mm2"] == seccion)
    ]
    if q.empty:
        return None
    return float(q.iloc[0]["Iz_A"])

def factor_temp(df_fact_temp: pd.DataFrame, aislamiento: str, T_amb: float) -> float:
    filas = df_fact_temp[df_fact_temp["aislamiento"] == aislamiento]
    for _, r in filas.iterrows():
        if r["t_min"] <= T_amb <= r["t_max"]:
            return float(r["factor"])
    return 1.0

def factor_agrup(df_fact_agrup: pd.DataFrame, metodo: str, n_circ: int) -> float:
    q = df_fact_agrup[(df_fact_agrup["metodo"] == metodo) & (df_fact_agrup["n_circuitos"] == n_circ)]
    if q.empty:
        # buscar aproximación por menor n_circuitos mayor o igual
        q2 = df_fact_agrup[(df_fact_agrup["metodo"] == metodo) & (df_fact_agrup["n_circuitos"] <= n_circ)]
        if not q2.empty:
            return float(q2.sort_values("n_circuitos", ascending=False).iloc[0]["factor"])
        return 1.0
    return float(q.iloc[0]["factor"])

def iz_corregida(df_iz: pd.DataFrame, df_fact_temp: pd.DataFrame, df_fact_agrup: pd.DataFrame,
                 material: str, aislamiento: str, metodo: str, n_cond: int, T_amb: float, n_circ: int, seccion: float) -> Optional[float]:
    Iz = buscar_iz_base(df_iz, material, aislamiento, metodo, n_cond, seccion)
    if Iz is None:
        return None
    ft = factor_temp(df_fact_temp, aislamiento, T_amb)
    fa = factor_agrup(df_fact_agrup, metodo, n_circ)
    return Iz * ft * fa

def seccion_por_caida(I: float, L: float, U_v: float, delta_u_pct: float, cos_phi: float, material: str, trifasico: bool=False) -> float:
    gamma = GAMMA[material]
    delta_u = (delta_u_pct / 100.0) * U_v
    if delta_u <= 0:
        raise ValueError("Delta U debe ser > 0")
    if trifasico:
        S = math.sqrt(3) * L * I * cos_phi / (gamma * delta_u)
    else:
        S = 2 * L * I * cos_phi / (gamma * delta_u)
    return S

def normalizar_seccion(S_calc: float) -> float:
    for s in SECCIONES_NORM:
        if s >= S_calc:
            return s
    return SECCIONES_NORM[-1]

def calcular_seccion_completa(df_iz: pd.DataFrame, df_fact_temp: pd.DataFrame, df_fact_agrup: pd.DataFrame,
                              Ib: float, L: float, U_v: float, delta_u_pct: float, cos_phi: float,
                              material: str, aislamiento: str, metodo: str, n_cond: int, T_amb: float, n_circ: int, trifasico: bool=False) -> Dict[str, Any]:
    # Sección por caída
    S_ct = seccion_por_caida(Ib, L, U_v, delta_u_pct, cos_phi, material, trifasico)

    # Sección por Iz corregida: buscar la menor sección normalizada que cumpla Iz_corr >= Ib
    S_Iz = None
    Iz_corr_elegida = None
    for s in SECCIONES_NORM:
        Iz_corr = iz_corregida(df_iz, df_fact_temp, df_fact_agrup, material, aislamiento, metodo, n_cond, T_amb, n_circ, s)
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
        "Iz_corr": Iz_corr_elegida,
        "S_final_calc": S_final_calc,
        "S_norm": S_norm
    }

def seccion_pe_recomendada(S_fase: float) -> float:
    # Regla práctica: PE = fase si <=16, si fase>16 y <=35 PE=16, si >35 PE = S/2 (redondear)
    if S_fase <= 16:
        return S_fase
    if S_fase <= 35:
        return 16.0
    return max(16.0, round(S_fase / 2.0, 1))

def cc_por_longitud(U_v: float, L: float, S_mm2: float, material: str, factor_resistividad_temp: float=1.0) -> Tuple[Optional[float], Optional[float]]:
    # Resistividad aproximada a 20°C: rho = 1 / gamma (Ω·mm²/m)
    rho20 = 1.0 / GAMMA[material]
    rho = rho20 * factor_resistividad_temp
    # Impedancia resistiva aproximada (2*L conductor ida y vuelta) Z ≈ rho * (2L) / S
    if S_mm2 <= 0:
        return None, None
    Z = rho * (2.0 * L) / S_mm2
    if Z <= 0:
        return None, None
    Icc = U_v / Z
    return Icc, Z

def seleccionar_magnetotermico(df_magnetos: pd.DataFrame, Ib: float, Iz_corr: float, Icc: Optional[float], curva_preferida: Optional[str]=None) -> Optional[Dict[str,Any]]:
    # Filtrar por curva si se indica
    df = df_magnetos.copy()
    if curva_preferida:
        df = df[df["curva"] == curva_preferida]
    # Buscar In tal que Ib <= In <= Iz_corr
    candidatos = df[(df["In_A"] >= Ib) & (df["In_A"] <= Iz_corr)]
    if candidatos.empty:
        # permitir In >= Ib (si no hay <= Iz_corr) y avisar
        candidatos = df[df["In_A"] >= Ib]
        if candidatos.empty:
            return None
    # elegir el menor In que cumpla
    elegido = candidatos.sort_values("In_A").iloc[0]
    poder_corte = float(elegido["poder_corte_kA"])
    cumple_poder = None
    if Icc is not None:
        Icc_kA = float(Icc) / 1000.0
        cumple_poder = poder_corte >= Icc_kA
    else:
        Icc_kA = None
    return {
        "In_A": int(elegido["In_A"]),
        "curva": elegido["curva"],
        "poder_corte_kA": poder_corte,
        "cumple_poder_corte": cumple_poder,
        "Icc_kA": Icc_kA
    }
# app.py  -- PARTE 3
# ==========================
# INTERFAZ STREAMLIT
# ==========================

def sidebar_tablas(tables: Dict[str,pd.DataFrame]) -> Dict[str,pd.DataFrame]:
    st.sidebar.header("Tablas y datos")
    # Mostrar y permitir subir CSV para cada tabla
    for key, df in [("iz","Iz conductores"), ("fact_temp","Factores temperatura"), ("fact_agrup","Factores agrupamiento"), ("magnetos","Magnetos"), ("tubos","Tubos")]:
        st.sidebar.subheader(df)
        uploaded = st.sidebar.file_uploader(f"Subir CSV {key}", type=["csv","xlsx"], key=f"up_{key}")
        if uploaded is not None:
            df_nueva = cargar_csv_usuario(uploaded)
            if df_nueva is not None:
                # intentar normalizar nombres de columnas mínimos
                st.sidebar.success(f"{key} cargada ({len(df_nueva)} filas).")
                # merge con la base
                if key == "iz":
                    tables["iz"] = merge_tabla(tables["iz"], df_nueva, ["material","aislamiento","metodo","n_cond","seccion_mm2"])
                elif key == "fact_temp":
                    tables["fact_temp"] = merge_tabla(tables["fact_temp"], df_nueva, ["aislamiento","t_min","t_max"])
                elif key == "fact_agrup":
                    tables["fact_agrup"] = merge_tabla(tables["fact_agrup"], df_nueva, ["metodo","n_circuitos"])
                elif key == "magnetos":
                    tables["magnetos"] = merge_tabla(tables["magnetos"], df_nueva, ["In_A","curva"])
                elif key == "tubos":
                    tables["tubos"] = merge_tabla(tables["tubos"], df_nueva, ["diam_mm"])
            else:
                st.sidebar.error("Formato no válido")
        if st.sidebar.checkbox(f"Ver tabla {key}", key=f"view_{key}"):
            st.sidebar.dataframe(tables[key].reset_index(drop=True))
    return tables

def pantalla_principal(tables: Dict[str,pd.DataFrame]):
    st.title("SEA Definitiva REBT Lite")
    st.markdown("Calculadora completa de secciones, protecciones, tubos y cortocircuito. Tablas editables o cargables por CSV.")

    menu = st.sidebar.selectbox("Módulo", [
        "Sección y protecciones",
        "Canalizaciones y tubos",
        "Cortocircuito por longitud",
        "Tablas y presets",
        "Resumen y notas"
    ])

    if menu == "Sección y protecciones":
        pantalla_seccion_protecciones_ui(tables)
    elif menu == "Canalizaciones y tubos":
        pantalla_tubos_ui(tables)
    elif menu == "Cortocircuito por longitud":
        pantalla_cc_longitud_ui(tables)
    elif menu == "Tablas y presets":
        pantalla_tablas_presets_ui(tables)
    else:
        pantalla_resumen_ui()

def pantalla_seccion_protecciones_ui(tables: Dict[str,pd.DataFrame]):
    st.header("Sección y protecciones")
    col1, col2 = st.columns(2)
    with col1:
        modo = st.radio("Dato de partida", ["Potencia","Intensidad"])
        trifasico = st.checkbox("Trifásico", value=False)
        U_v = st.number_input("Tensión (V)", value=400 if trifasico else 230)
        cos_phi = st.number_input("Cos φ", value=0.95, min_value=0.1, max_value=1.0, step=0.01)
        L = st.number_input("Longitud (m)", value=20.0, min_value=0.1, step=0.1)
        tipo_circuito = st.selectbox("Tipo de circuito", ["Iluminación","Tomas / Fuerza","Motor"])
        if tipo_circuito == "Iluminación":
            delta_u_pct = st.number_input("Caída máxima (%)", value=3.0, min_value=0.5, max_value=10.0, step=0.5)
        elif tipo_circuito == "Motor":
            delta_u_pct = st.number_input("Caída máxima (%)", value=7.0, min_value=0.5, max_value=10.0, step=0.5)
        else:
            delta_u_pct = st.number_input("Caída máxima (%)", value=5.0, min_value=0.5, max_value=10.0, step=0.5)

    with col2:
        material = st.selectbox("Material", sorted(tables["iz"]["material"].unique()))
        aislamiento = st.selectbox("Aislamiento", sorted(tables["iz"]["aislamiento"].unique()))
        metodo = st.selectbox("Método instalación", sorted(tables["iz"]["metodo"].unique()))
        n_cond = int(st.number_input("Conductores cargados", value=2, min_value=1, max_value=3))
        T_amb = st.number_input("Temperatura ambiente (°C)", value=30.0, min_value=0.0, max_value=80.0)
        n_circ = int(st.number_input("Circuitos agrupados", value=1, min_value=1, max_value=20))
        curva_pref = st.selectbox("Curva preferida magnetotérmico", sorted(tables["magnetos"]["curva"].unique()))

    if modo == "Potencia":
        P = st.number_input("Potencia (W)", value=3500.0, min_value=0.1, step=10.0)
        Ib = intensidad_desde_potencia(P, U_v, cos_phi, trifasico)
        st.metric("Ib calculada", formato_num(Ib,2) + " A")
    else:
        Ib = st.number_input("Ib (A)", value=16.0, min_value=0.01, step=0.1)

    if st.button("Calcular"):
        res = calcular_seccion_completa(
            tables["iz"], tables["fact_temp"], tables["fact_agrup"],
            Ib, L, U_v, delta_u_pct, cos_phi,
            material, aislamiento, metodo, n_cond, T_amb, n_circ, trifasico
        )
        st.subheader("Resultados sección")
        st.write(f"**Sección por caída:** {formato_num(res['S_ct'],2)} mm²")
        st.write(f"**Sección por Iz corregida:** {res['S_Iz']} mm²")
        st.write(f"**Iz corregida aprox:** {formato_num(res['Iz_corr'],2) if res['Iz_corr'] else 'N/D'} A")
        st.write(f"**Sección calculada final:** {formato_num(res['S_final_calc'],2)} mm²")
        st.write(f"**Sección normalizada recomendada:** {res['S_norm']} mm²")

        st.subheader("Sección PE recomendada")
        S_pe = seccion_pe_recomendada(res["S_norm"])
        st.write(f"**PE recomendado:** {formato_num(S_pe,1)} mm²")

        st.subheader("Cortocircuito estimado por longitud")
        Icc, Z = cc_por_longitud(U_v, L, res["S_norm"], material)
        if Icc:
            st.write(f"**Impedancia estimada:** {formato_num(Z,4)} Ω")
            st.write(f"**Icc estimada:** {formato_num(Icc,0)} A ({formato_num(Icc/1000,2)} kA)")
        else:
            st.write("No se pudo estimar Icc con los datos proporcionados.")

        st.subheader("Protección recomendada")
        prot = seleccionar_magnetotermico(tables["magnetos"], Ib, res["Iz_corr"] if res["Iz_corr"] else 0, Icc, curva_pref)
        if prot:
            st.write(f"**Magnetotérmico sugerido:** {prot['In_A']} A curva {prot['curva']} ({prot['poder_corte_kA']} kA)")
            if prot["cumple_poder_corte"] is None:
                st.write("Poder de corte: no calculado (Icc no disponible).")
            elif prot["cumple_poder_corte"]:
                st.success("Poder de corte suficiente frente a Icc estimada.")
            else:
                st.error("Poder de corte insuficiente frente a Icc estimada.")
        else:
            st.warning("No se encontró magnetotérmico adecuado con las tablas actuales.")

def pantalla_tubos_ui(tables: Dict[str,pd.DataFrame]):
    st.header("Canalizaciones y tubos")
    diam = st.selectbox("Diámetro tubo (mm)", sorted(tables["tubos"]["diam_mm"].unique()))
    n_tipos = int(st.number_input("Tipos de conductor distintos en tubo", value=1, min_value=1, max_value=6))
    secciones = []
    n_por_seccion = []
    for i in range(n_tipos):
        col1, col2 = st.columns(2)
        with col1:
            s = st.number_input(f"Sección tipo {i+1} (mm²)", value=2.5, min_value=0.5, step=0.5, key=f"sec_{i}")
        with col2:
            n = int(st.number_input(f"Nº conductores tipo {i+1}", value=2, min_value=1, step=1, key=f"num_{i}"))
        secciones.append(s)
        n_por_seccion.append(n)
    if st.button("Verificar ocupación"):
        tubo = tables["tubos"][tables["tubos"]["diam_mm"]==diam].iloc[0]
        area_util = float(tubo["area_util_mm2"])
        max_cond = int(tubo["max_conductores"])
        S_ocupada = sum([s*n for s,n in zip(secciones,n_por_seccion)])
        n_total = sum(n_por_seccion)
        porcentaje = 100.0 * S_ocupada / area_util
        st.write(f"**Sección ocupada:** {formato_num(S_ocupada,1)} mm²")
        st.write(f"**Área útil tubo:** {formato_num(area_util,1)} mm²")
        st.write(f"**Porcentaje ocupación:** {formato_num(porcentaje,1)} %")
        st.write(f"**Nº conductores total:** {n_total} (máx recomendado: {max_cond})")
        if porcentaje > 40 or n_total > max_cond:
            st.warning("Ocupación alta: aumentar diámetro o reducir conductores.")
        else:
            st.success("Ocupación dentro de límites orientativos.")

def pantalla_cc_longitud_ui(tables: Dict[str,pd.DataFrame]):
    st.header("Cortocircuito por longitud y verificación poder de corte")
    U_v = st.number_input("Tensión (V)", value=230.0)
    L = st.number_input("Longitud (m)", value=20.0, min_value=0.1, step=0.1)
    S_mm2 = st.selectbox("Sección conductor (mm²)", SECCIONES_NORM, index=SECCIONES_NORM.index(2.5) if 2.5 in SECCIONES_NORM else 0)
    material = st.selectbox("Material conductor", sorted(list(GAMMA.keys())))
    factor_temp = st.number_input("Factor resistividad por temperatura", value=1.0, min_value=0.5, max_value=2.0, step=0.01)
    if st.button("Calcular Icc y comparar magnetos"):
        Icc, Z = cc_por_longitud(U_v, L, S_mm2, material, factor_temp)
        if Icc:
            st.write(f"**Z estimada:** {formato_num(Z,4)} Ω")
            st.write(f"**Icc estimada:** {formato_num(Icc,0)} A ({formato_num(Icc/1000,2)} kA)")
            # mostrar magnetos que soportan
            df_ok = tables["magnetos"][tables["magnetos"]["poder_corte_kA"] >= (Icc/1000.0)]
            if not df_ok.empty:
                st.write("Magnetos con poder de corte suficiente")
                st.dataframe(df_ok.reset_index(drop=True))
            else:
                st.error("Ningún magnetotérmico en la tabla tiene poder de corte suficiente.")
        else:
            st.error("No se pudo calcular Icc con los datos proporcionados.")

def pantalla_tablas_presets_ui(tables: Dict[str,pd.DataFrame]):
    st.header("Tablas y presets")
    st.markdown("Edita tablas en la UI y guarda/recupera presets locales (en memoria de sesión).")
    st.subheader("Editar tabla Iz")
    iz_edit = st.experimental_data_editor(tables["iz"], num_rows="dynamic")
    if st.button("Actualizar Iz desde editor"):
        tables["iz"] = iz_edit.copy()
        st.success("Tabla Iz actualizada.")
    st.subheader("Editar factores temperatura")
    ft_edit = st.experimental_data_editor(tables["fact_temp"], num_rows="dynamic")
    if st.button("Actualizar factores temperatura"):
        tables["fact_temp"] = ft_edit.copy()
        st.success("Tabla factores temperatura actualizada.")
    st.subheader("Editar factores agrupamiento")
    fa_edit = st.experimental_data_editor(tables["fact_agrup"], num_rows="dynamic")
    if st.button("Actualizar factores agrupamiento"):
        tables["fact_agrup"] = fa_edit.copy()
        st.success("Tabla factores agrupamiento actualizada.")
    st.subheader("Editar magnetos")
    mg_edit = st.experimental_data_editor(tables["magnetos"], num_rows="dynamic")
    if st.button("Actualizar magnetos"):
        tables["magnetos"] = mg_edit.copy()
        st.success("Tabla magnetos actualizada.")
    st.subheader("Editar tubos")
    tb_edit = st.experimental_data_editor(tables["tubos"], num_rows="dynamic")
    if st.button("Actualizar tubos"):
        tables["tubos"] = tb_edit.copy()
        st.success("Tabla tubos actualizada.")

    st.markdown("---")
    st.subheader("Presets")
    if "presets" not in st.session_state:
        st.session_state["presets"] = {}
    preset_name = st.text_input("Nombre preset")
    if st.button("Guardar preset"):
        st.session_state["presets"][preset_name] = {
            "iz": tables["iz"].to_json(),
            "fact_temp": tables["fact_temp"].to_json(),
            "fact_agrup": tables["fact_agrup"].to_json(),
            "magnetos": tables["magnetos"].to_json(),
            "tubos": tables["tubos"].to_json(),
        }
        st.success(f"Preset '{preset_name}' guardado.")
    if st.session_state["presets"]:
        sel = st.selectbox("Cargar preset", list(st.session_state["presets"].keys()))
        if st.button("Cargar preset seleccionado"):
            p = st.session_state["presets"][sel]
            tables["iz"] = pd.read_json(p["iz"])
            tables["fact_temp"] = pd.read_json(p["fact_temp"])
            tables["fact_agrup"] = pd.read_json(p["fact_agrup"])
            tables["magnetos"] = pd.read_json(p["magnetos"])
            tables["tubos"] = pd.read_json(p["tubos"])
            st.success(f"Preset '{sel}' cargado.")

def pantalla_resumen_ui():
    st.header("Resumen y notas")
    st.markdown("""
    **Características incluidas**
    - Cálculo de sección por caída de tensión y por Iz corregida.
    - Factores de corrección por temperatura y agrupamiento.
    - Selección de magnetotérmico con verificación de poder de corte frente a Icc estimada.
    - Cálculo simplificado de Icc por longitud y sección.
    - Recomendación de sección PE.
    - Verificación de ocupación de tubos.
    - Tablas editables en UI y carga por CSV.
    - Presets locales para guardar conjuntos de tablas.
    """)
# app.py  -- PARTE 4
# ==========================
# ARRANQUE
# ==========================

def main():
    st.set_page_config(page_title="SEA Definitiva REBT", page_icon="⚡", layout="wide")
    # cargar tablas por defecto
    tablas = cargar_tablas_default()
    # permitir al usuario subir/editar tablas desde sidebar
    tablas = sidebar_tablas(tablas)
    # ejecutar UI principal
    pantalla_principal(tablas)

if __name__ == "__main__":
    main()
