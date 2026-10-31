"""UI de cálculos eléctricos."""
import streamlit as st
from calc_engine import *


def _num(label, default, **kw):
    return st.number_input(label, value=default, **kw)


def ui_section():
    st.subheader("Sección de cable")
    c1, c2 = st.columns(2)
    power = _num("Potencia (kW)", 3.5, min_value=0.05, step=0.1, key="sec_power")
    length = _num("Longitud (m)", 20.0, min_value=0.5, step=1.0, key="sec_length")
    voltage = c1.selectbox("Tensión (V)", [230, 400], key="sec_volt")
    phases = c2.selectbox("Fases", [1, 3], key="sec_phases")
    cosphi = _num("cos φ", 1.0, min_value=0.1, max_value=1.0, step=0.01, key="sec_cosphi")
    limit = _num("Caída máx (%)", 5.0, min_value=1.0, max_value=10.0, step=0.5, key="sec_limit")
    material = st.selectbox("Material", ["Cobre", "Aluminio"], key="sec_mat")
    res = suggest_section(power, length, voltage, phases, cosphi, limit, material)
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Sección", f"{res['section']} mm²")
    col2.metric("PIA", f"{res['breaker']} A" if res['breaker'] else "—")
    col3.metric("Ib", f"{res['ib']} A")
    col4.metric("Caída ΔU", f"{res['dv']} %")
    st.metric("Iz", f"{res['iz']} A")
    if res["cumple"]:
        st.success("✅ Cumple criterios térmico y de caída de tensión.")
    else:
        st.error("❌ No cumple. Aumenta sección o reduce longitud.")


def ui_voltage_drop():
    st.subheader("Caída de tensión")
    power = _num("Potencia (kW)", 3.5, min_value=0.05, step=0.1, key="vd_power")
    length = _num("Longitud (m)", 20.0, min_value=0.5, step=1.0, key="vd_length")
    section = _num("Sección (mm²)", 2.5, min_value=1.5, step=0.5, key="vd_section")
    voltage = st.selectbox("Tensión (V)", [230, 400], key="vd_volt")
    phases = st.selectbox("Fases", [1, 3], key="vd_phases")
    cosphi = _num("cos φ", 1.0, min_value=0.1, max_value=1.0, step=0.01, key="vd_cosphi")
    material = st.selectbox("Material", ["Cobre", "Aluminio"], key="vd_mat")
    rho = RHO_AL if material == "Aluminio" else RHO_CU
    dv = voltage_drop_pct(power, length, section, voltage, phases, cosphi, rho)
    ib = current_from_power(power, voltage, phases, cosphi)
    st.metric("Caída de tensión", f"{dv:.2f} %")
    st.metric("Ib", f"{ib:.2f} A")
    st.metric("Límite habitual", "3% (alumbrado) / 5% (fuerza)")
    if dv <= 3:
        st.success("✅ Cumple para alumbrado (≤3%).")
    elif dv <= 5:
        st.warning("⚠️ Cumple para fuerza (≤5%) pero no para alumbrado.")
    else:
        st.error("❌ No cumple (excede 5%).")


def ui_short_circuit():
    st.subheader("Cortocircuito")
    icc = _num("Icc en origen (kA)", 10.0, min_value=0.1, step=0.5, key="sc_icc")
    time_s = _num("Tiempo de actuación (s)", 0.1, min_value=0.01, step=0.01, key="sc_time")
    section = _num("Sección (mm²)", 2.5, min_value=1.5, step=0.5, key="sc_section")
    material = st.selectbox("Material", ["Cobre", "Aluminio"], key="sc_mat")
    insulation = st.selectbox("Aislamiento", ["PVC", "XLPE"], key="sc_ins")
    res = short_circuit_check(icc, time_s, section, material, insulation)
    st.metric("S mínima (mm²)", f"{res['s_min']}")
    st.metric("k", f"{res['k']}")
    if res["cumple"]:
        st.success(f"✅ Sección {section} mm² cumple (≥ {res['s_min']} mm²).")
    else:
        st.error(f"❌ Sección insuficiente. Mínimo: {res['s_min']} mm².")


def ui_reactive():
    st.subheader("Compensación de reactiva")
    p_kw = _num("Potencia activa (kW)", 50.0, min_value=0.1, step=1.0, key="rc_p")
    cos1 = _num("cos φ actual", 0.8, min_value=0.1, max_value=0.99, step=0.01, key="rc_cos1")
    cos2 = _num("cos φ objetivo", 0.95, min_value=0.1, max_value=0.99, step=0.01, key="rc_cos2")
    v = st.selectbox("Tensión (V)", [230, 400], key="rc_v")
    res = reactive_compensation(p_kw, cos1, cos2, v)
    if "error" in res:
        st.error(res["error"])
        return
    st.metric("Potencia condensador (kVAr)", f"{res['qc_kvar']}")
    st.metric("Capacidad (µF)", f"{res['c_uf']}")
    st.metric("Corriente condensador (A)", f"{res['i_condensador_a']}")


def ui_transformer():
    st.subheader("Transformador")
    s_kva = _num("Potencia (kVA)", 100.0, min_value=1.0, step=10.0, key="tr_s")
    v1 = _num("Tensión primario (V)", 20000.0, min_value=1.0, step=100.0, key="tr_v1")
    v2 = _num("Tensión secundario (V)", 400.0, min_value=1.0, step=10.0, key="tr_v2")
    imp = _num("Impedancia (%)", 4.0, min_value=1.0, max_value=10.0, step=0.5, key="tr_imp")
    res = transformer_calc(s_kva, v1, v2, imp)
    c1, c2, c3 = st.columns(3)
    c1.metric("Relación", f"{res['ratio']}")
    c2.metric("I primario (A)", f"{res['i1_a']}")
    c3.metric("I secundario (A)", f"{res['i2_a']}")
    st.metric("Ucc (V)", f"{res['ucc_v']}")


def ui_motor():
    st.subheader("Motor eléctrico")
    power = _num("Potencia (kW)", 7.5, min_value=0.1, step=0.5, key="mot_power")
    voltage = st.selectbox("Tensión (V)", [230, 400], key="mot_volt")
    phases = st.selectbox("Fases", [1, 3], key="mot_phases")
    cosphi = _num("cos φ", 0.85, min_value=0.1, max_value=1.0, step=0.01, key="mot_cosphi")
    eff = _num("Rendimiento", 0.9, min_value=0.1, max_value=1.0, step=0.01, key="mot_eff")
    res = motor_calc(power, voltage, phases, cosphi, eff)
    c1, c2, c3 = st.columns(3)
    c1.metric("In (A)", f"{res['inom_a']}")
    c2.metric("I arranque (A)", f"{res['i_arranque_a']}")
    c3.metric("PIA sugerido (A)", f"{res['pia_sugerido']}")
    st.metric("Potencia de entrada (kW)", f"{res['p_in_kw']}")


def ui_lighting():
    st.subheader("Iluminación")
    area = _num("Área (m²)", 50.0, min_value=1.0, step=1.0, key="light_area")
    lux = _num("Lux requeridos", 300.0, min_value=1.0, step=10.0, key="light_lux")
    lumens = _num("Lúmenes por luminaria", 3000.0, min_value=100.0, step=100.0, key="light_lumens")
    cu = _num("Coef. utilización", 0.5, min_value=0.1, max_value=1.0, step=0.05, key="light_cu")
    mf = _num("Factor mantenimiento", 0.8, min_value=0.1, max_value=1.0, step=0.05, key="light_mf")
    res = lighting_calc(area, lux, lumens, cu, mf)
    c1, c2, c3 = st.columns(3)
    c1.metric("Nº luminarias", f"{res['n_luminarias']}")
    c2.metric("Lux reales", f"{res['e_real_lux']}")
    c3.metric("Lúmenes totales", f"{res['total_lumens']}")
    if res["cumple"]:
        st.success("✅ Cumple iluminancia requerida.")
    else:
        st.error("❌ No cumple. Aumenta luminarias.")


def ui_conduit():
    st.subheader("Canalización — capacidad de tubo")
    tube = st.selectbox("Diámetro tubo (mm)", [16, 20, 25, 32, 40, 50, 63], key="cond_tube")
    fill = _num("Relleno máx (%)", 40.0, min_value=10.0, max_value=60.0, step=5.0, key="cond_fill")
    st.markdown("**Cables (sección, cantidad):**")
    c1, c2 = st.columns(2)
    s1 = c1.selectbox("Sección 1", SECTIONS, key="cond_s1")
    n1 = c2.number_input("Cantidad 1", min_value=0, value=3, step=1, key="cond_n1")
    s2 = c1.selectbox("Sección 2", [0] + SECTIONS, key="cond_s2")
    n2 = c2.number_input("Cantidad 2", min_value=0, value=0, step=1, key="cond_n2")
    cables = [(s1, n1)]
    if s2 > 0 and n2 > 0:
        cables.append((s2, n2))
    res = conduit_fill(cables, tube, fill)
    c1, c2, c3 = st.columns(3)
    c1.metric("Área cables (mm²)", f"{res['total_cable_area']}")
    c2.metric("Relleno máx (mm²)", f"{res['max_fill']}")
    c3.metric("Relleno (%)", f"{res['fill_pct']}")
    if res["cumple"]:
        st.success("✅ Cables caben en el tubo.")
    else:
        st.error("❌ Demasiados cables. Aumenta diámetro.")


def ui_earth():
    st.subheader("Puesta a tierra")
    rho = _num("Resistividad terreno (Ω·m)", 100.0, min_value=1.0, step=10.0, key="earth_rho")
    length = _num("Longitud electrodo (m)", 2.0, min_value=0.5, step=0.5, key="earth_length")
    diam = _num("Diámetro (m)", 0.014, min_value=0.005, step=0.001, key="earth_diam")
    num = st.number_input("Nº electrodos", min_value=1, value=1, step=1, key="earth_num")
    spacing = _num("Separación (m)", 0.0, min_value=0.0, step=0.5, key="earth_spacing")
    res = earth_electrode(rho, length, diam, num, spacing)
    if "error" in res:
        st.error(res["error"])
        return
    st.metric("Resistencia (Ω)", f"{res['resistance_ohm']}")
    if res["cumple_20ohm"]:
        st.success("✅ ≤ 20 Ω (instalación BT).")
    elif res["cumple_30ohm"]:
        st.warning("⚠️ ≤ 30 Ω (límite alternativo).")
    else:
        st.error("❌ Excede 30 Ω. Aumenta electrodos.")


def ui_battery():
    st.subheader("Baterías")
    load = _num("Carga (W)", 500.0, min_value=1.0, step=10.0, key="bat_load")
    autonomy = _num("Autonomía (h)", 4.0, min_value=0.5, step=0.5, key="bat_aut")
    voltage = st.selectbox("Tensión (V)", [12, 24, 48], key="bat_volt")
    dod = _num("Profundidad de descarga", 0.5, min_value=0.1, max_value=1.0, step=0.05, key="bat_dod")
    eff = _num("Rendimiento", 0.85, min_value=0.1, max_value=1.0, step=0.05, key="bat_eff")
    res = battery_calc(load, autonomy, voltage, dod, eff)
    c1, c2 = st.columns(2)
    c1.metric("Energía (Wh)", f"{res['energy_wh']}")
    c2.metric("Capacidad (Ah)", f"{res['capacity_ah']}")


def ui_panel():
    st.subheader("Cuadro eléctrico — IGA / ID")
    power = _num("Potencia total (kW)", 10.0, min_value=0.1, step=0.5, key="panel_power")
    voltage = st.selectbox("Tensión (V)", [230, 400], key="panel_volt")
    phases = st.selectbox("Fases", [1, 3], key="panel_phases")
    cosphi = _num("cos φ", 0.9, min_value=0.1, max_value=1.0, step=0.01, key="panel_cosphi")
    res = panel_calc(power, voltage, phases, cosphi)
    c1, c2, c3 = st.columns(3)
    c1.metric("Ib (A)", f"{res['ib_a']}")
    c2.metric("IGA calc (A)", f"{res['iga_calc_a']}")
    c3.metric("IGA normalizado (A)", f"{res['iga_std_a']}")
    st.metric("ID sugerido", res["id_type"])


def ui_indirect():
    st.subheader("Protección contra contactos indirectos")
    z_loop = _num("Impedancia de lazo (Ω)", 0.5, min_value=0.01, step=0.01, key="ic_zloop")
    voltage = st.selectbox("Tensión (V)", [230, 400], key="ic_volt")
    time_s = _num("Tiempo desconexión (s)", 0.4, min_value=0.01, step=0.01, key="ic_time")
    res = indirect_contact(time_s, z_loop, voltage)
    st.metric("Corriente de defecto (A)", f"{res['i_defect_a']}")
    st.metric("Tiempo (s)", f"{res['disconnect_time_s']}")
    if res["cumple"]:
        st.success("✅ Corriente de defecto suficiente para desconexión.")
    else:
        st.error("❌ Verificar protección.")


def ui_simultaneity():
    st.subheader("Factor de simultaneidad")
    n = st.number_input("Nº de viviendas", min_value=1, value=10, step=1, key="sim_n")
    total = _num("Potencia total (kW)", 50.0, min_value=0.1, step=1.0, key="sim_total")
    res = simultaneity_factor(n, total)
    c1, c2 = st.columns(2)
    c1.metric("Factor", f"{res['factor']}")
    c2.metric("Potencia simultánea (kW)", f"{res['power_simultaneous_kw']}")


def ui_harmonic():
    st.subheader("Armónicos — neutro")
    i_phase = _num("Corriente de fase (A)", 20.0, min_value=0.1, step=1.0, key="harm_iphase")
    thd = _num("THD (%)", 15.0, min_value=0.0, step=1.0, key="harm_thd")
    phases = st.selectbox("Fases", [1, 3], key="harm_phases")
    res = neutral_harmonic(i_phase, thd, phases)
    st.metric("Corriente neutro (A)", f"{res['i_neutral_a']}")
    if res["neutro_plena_seccion"]:
        st.warning("⚠️ Neutro a sección plena (armónicos triplen).")
    else:
        st.success("✅ Neutro puede ser reducido.")


def ui_generator():
    st.subheader("Generador")
    load = _num("Carga (kW)", 50.0, min_value=0.1, step=1.0, key="gen_load")
    pf = _num("Factor de potencia", 0.8, min_value=0.1, max_value=1.0, step=0.01, key="gen_pf")
    margin = _num("Margen seguridad", 1.25, min_value=1.0, step=0.05, key="gen_margin")
    alt = _num("Altitud (m)", 0.0, min_value=0.0, step=100.0, key="gen_alt")
    temp = _num("Temperatura (°C)", 25.0, min_value=-10.0, step=1.0, key="gen_temp")
    res = generator_calc(load, pf, margin, alt, temp)
    c1, c2, c3 = st.columns(3)
    c1.metric("S (kVA)", f"{res['s_kva']}")
    c2.metric("Derating", f"{res['derating']}")
    c3.metric("Generador (kVA)", f"{res['p_gen_kva']}")


def ui_fv_battery():
    st.subheader("Fotovoltaica con batería")
    p_peak = _num("Potencia pico (kWp)", 5.0, min_value=0.1, step=0.5, key="fvb_peak")
    load = _num("Carga (kW)", 2.0, min_value=0.1, step=0.1, key="fvb_load")
    bat = _num("Batería (kWh)", 10.0, min_value=0.1, step=1.0, key="fvb_bat")
    autonomy = _num("Autonomía (h)", 4.0, min_value=0.5, step=0.5, key="fvb_aut")
    losses = _num("Pérdidas", 0.15, min_value=0.0, max_value=0.5, step=0.01, key="fvb_losses")
    res = fv_with_battery(p_peak, load, bat, autonomy, losses)
    c1, c2 = st.columns(2)
    c1.metric("Producción diaria (kWh)", f"{res['produccion_diaria_kwh']}")
    c2.metric("Consumo diario (kWh)", f"{res['consumo_diario_kwh']}")
    c1.metric("Excedente (kWh)", f"{res['excedente_kwh']}")
    c2.metric("Déficit (kWh)", f"{res['deficit_kwh']}")
    st.metric("Autoconsumo (%)", f"{res['autoconsumo_pct']}")
    st.metric("Cobertura batería", f"{res['cobertura_bateria']}")


def ui_flicker():
    st.subheader("Flicker — fluctuación de tensión")
    p_step = _num("Escalón de potencia (kW)", 10.0, min_value=0.1, step=1.0, key="flick_p")
    scc = _num("Scc (MVA)", 50.0, min_value=0.1, step=1.0, key="flick_scc")
    res = flicker_calc(p_step, scc)
    if "error" in res:
        st.error(res["error"])
        return
    st.metric("ΔU (%)", f"{res['du_pct']}")
    if res["cumple_5pct"]:
        st.success("✅ ≤ 5% (cumple).")
    else:
        st.error("❌ Excede 5%.")


def ui_insulation():
    st.subheader("Verificación de aislamiento")
    voltage = st.selectbox("Tensión (V)", [230, 400, 1000], key="iso_volt")
    r_iso = _num("R aislamiento (MΩ)", 5.0, min_value=0.0, step=0.1, key="iso_r")
    min_r = _num("Mínimo (MΩ)", 1.0, min_value=0.1, step=0.1, key="iso_min")
    res = insulation_check(voltage, r_iso, min_r)
    st.metric("R aislamiento (MΩ)", f"{res['r_iso_mohm']}")
    if res["cumple"]:
        st.success("✅ Aislamiento correcto.")
    else:
        st.error("❌ Aislamiento insuficiente.")


def ui_fv():
    st.subheader("Fotovoltaica — autoconsumo")
    p_peak = _num("Potencia pico (kWp)", 5.0, min_value=0.1, step=0.5, key="fv_peak")
    losses = _num("Pérdidas", 0.15, min_value=0.0, max_value=0.5, step=0.01, key="fv_losses")
    irradiance = _num("Irradiancia (kWh/m²/día)", 5.0, min_value=1.0, step=0.5, key="fv_irr")
    res = fv_dimension(p_peak, "230V", losses, irradiance)
    c1, c2, c3 = st.columns(3)
    c1.metric("P pico (kWp)", f"{res['p_pico_kwp']}")
    c2.metric("P AC (kW)", f"{res['p_ac_kw']}")
    c3.metric("Producción anual (kWh)", f"{res['produccion_anual_kwh']}")
    st.metric("Ratio performance", f"{res['ratio_performance']}")


CALCS = {
    "Sección de cable": ui_section,
    "Caída de tensión": ui_voltage_drop,
    "Cortocircuito": ui_short_circuit,
    "Compensación reactiva": ui_reactive,
    "Transformador": ui_transformer,
    "Motor eléctrico": ui_motor,
    "Iluminación": ui_lighting,
    "Canalización": ui_conduit,
    "Puesta a tierra": ui_earth,
    "Baterías": ui_battery,
    "Cuadro eléctrico (IGA/ID)": ui_panel,
    "Contactos indirectos": ui_indirect,
    "Factor de simultaneidad": ui_simultaneity,
    "Armónicos (neutro)": ui_harmonic,
    "Generador": ui_generator,
    "Fotovoltaica + batería": ui_fv_battery,
    "Flicker": ui_flicker,
    "Aislamiento": ui_insulation,
    "Fotovoltaica": ui_fv,
}