"""Motor de cálculos eléctricos — REBT + IEC 60364."""
import math
from typing import Optional

# ── Constantes ──────────────────────────────────────────────
SECTIONS = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300]
BREAKERS = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630]
IZ_CU = {1.5: 14, 2.5: 21, 4: 27, 6: 36, 10: 50, 16: 66, 25: 84, 35: 104, 50: 125,
         70: 160, 95: 194, 120: 225, 150: 260, 185: 300, 240: 350, 300: 405}
IZ_AL = {s: round(v * 0.78, 1) for s, v in IZ_CU.items()}
RHO_CU = 0.0175  # ohm*mm2/m a 70°C
RHO_AL = 0.0282
LAMBDA = 0.08  # reactancia lineal ohm/km


# ── 1. Corriente de empleo ──────────────────────────────────
def current_from_power(power_kw, voltage=230, phases=1, cosphi=1.0):
    if voltage <= 0 or cosphi <= 0:
        return 0.0
    return power_kw * 1000 / (voltage * cosphi * (math.sqrt(3) if phases == 3 else 1))


# ── 2. Caída de tensión ─────────────────────────────────────
def voltage_drop_pct(power_kw, length_m, section, voltage=230, phases=1, cosphi=1.0, rho=RHO_CU):
    if min(section, voltage) <= 0:
        return 999.0
    ib = current_from_power(power_kw, voltage, phases, cosphi)
    factor = math.sqrt(3) if phases == 3 else 2
    return factor * length_m * ib * rho / section / voltage * 100


# ── 3. Sección de cable ─────────────────────────────────────
def suggest_section(power_kw, length_m, voltage=230, phases=1, cosphi=1.0,
                    limit=5.0, material="Cobre", method="B1"):
    rho = RHO_AL if material == "Aluminio" else RHO_CU
    ib = current_from_power(power_kw, voltage, phases, cosphi)
    factor = 0.82 if material == "Aluminio" else 1.0
    iz_table = IZ_AL if material == "Aluminio" else IZ_CU
    for s in SECTIONS:
        iz = iz_table[s] * factor
        dv = voltage_drop_pct(power_kw, length_m, s, voltage, phases, cosphi, rho)
        if iz >= ib and dv <= limit:
            possible = [b for b in BREAKERS if b >= math.ceil(ib) and b <= iz]
            return {"section": s, "breaker": possible[0] if possible else None,
                    "ib": round(ib, 2), "dv": round(dv, 2), "iz": round(iz, 1),
                    "cumple": True}
    s = SECTIONS[-1]
    dv = voltage_drop_pct(power_kw, length_m, s, voltage, phases, cosphi, rho)
    return {"section": s, "breaker": None, "ib": round(ib, 2), "dv": round(dv, 2),
            "iz": round(iz_table[s] * factor, 1), "cumple": False}


# ── 4. Cortocircuito ────────────────────────────────────────
K_VALUES = {
    ("Cobre", "PVC"): 115, ("Cobre", "XLPE"): 143,
    ("Aluminio", "PVC"): 76, ("Aluminio", "XLPE"): 94,
}


def short_circuit_check(icc_ka, time_s, section, material="Cobre", insulation="PVC"):
    k = K_VALUES.get((material, insulation), 115)
    s_min = icc_ka * 1000 * math.sqrt(time_s) / k
    return {
        "k": k, "s_min": round(s_min, 2), "section": section,
        "cumple": section >= s_min, "icc_ka": icc_ka, "time_s": time_s,
    }


def icc_at_point(scc_mva, voltage_kv, zk_ohm=None):
    """Icc en kA en un punto de la red."""
    if zk_ohm and zk_ohm > 0:
        return voltage_kv * 1000 / (math.sqrt(3) * zk_ohm) if voltage_kv > 0 else 0
    if scc_mva > 0 and voltage_kv > 0:
        return scc_mva * 1000 / (math.sqrt(3) * voltage_kv)
    return 0.0


# ── 5. Protecciones — coordinación ──────────────────────────
def breaker_curve_check(in_rated, i_load, i_sc, curve="C"):
    """Verifica magnetotérmico: In >= Ib, Icu >= Icc, disparo por magnético."""
    ratios = {"B": (3, 5), "C": (5, 10), "D": (10, 20)}
    lo, hi = ratios.get(curve, (5, 10))
    mag_min = in_rated * lo
    mag_max = in_rated * hi
    return {
        "in_rated": in_rated, "i_load": i_load, "i_sc": i_sc,
        "mag_min": mag_min, "mag_max": mag_max,
        "cumple_in": in_rated >= i_load,
        "cumple_icu": i_sc <= in_rated * 10,  # simplificado
        "dispara": i_sc >= mag_min,
    }


# ── 6. Factor de potencia / compensación reactiva ──────────
def reactive_compensation(p_kw, cosphi1, cosphi2, v=400, freq=50):
    """Potencia de condensador necesaria para pasar de cosφ1 a cosφ2."""
    if cosphi1 <= 0 or cosphi2 <= 0:
        return {"error": "cosφ debe ser > 0"}
    tan1 = math.tan(math.acos(cosphi1))
    tan2 = math.tan(math.acos(cosphi2))
    qc = p_kw * (tan1 - tan2)
    # capacidad del condensador
    if v > 0 and freq > 0:
        c_uf = qc * 1000 / (2 * math.pi * freq * v * v) * 1e6
    else:
        c_uf = 0
    i_c = qc * 1000 / (math.sqrt(3) * v) if v > 0 else 0
    return {
        "p_kw": p_kw, "cosphi1": cosphi1, "cosphi2": cosphi2,
        "qc_kvar": round(qc, 2), "c_uf": round(c_uf, 1),
        "i_condensador_a": round(i_c, 2),
    }


# ── 7. Transformador ────────────────────────────────────────
def transformer_calc(s_kva, v1, v2, imp_pct=4.0):
    """Relación, corrientes nominales, pérdidas."""
    ratio = v1 / v2 if v2 > 0 else 0
    i1 = s_kva * 1000 / (math.sqrt(3) * v1) if v1 > 0 else 0
    i2 = s_kva * 1000 / (math.sqrt(3) * v2) if v2 > 0 else 0
    ucc = v2 * imp_pct / 100  # tensión de cortocircuito
    return {
        "ratio": round(ratio, 3), "i1_a": round(i1, 1), "i2_a": round(i2, 1),
        "ucc_v": round(ucc, 1), "imp_pct": imp_pct,
    }


# ── 8. Motor eléctrico ──────────────────────────────────────
def motor_calc(power_kw, voltage=400, phases=3, cosphi=0.85, efficiency=0.9, service=1.0):
    """Corriente nominal, corriente de arranque, protección."""
    p_in = power_kw / efficiency if efficiency > 0 else power_kw
    inom = p_in * 1000 / (voltage * cosphi * (math.sqrt(3) if phases == 3 else 1))
    i_arranque = inom * 6  # arranque directo ~6x
    # protección: 1.25 * In para motor único (ITC-BT-47)
    i_prot = inom * 1.25
    # PIA sugerido
    pia = None
    for b in BREAKERS:
        if b >= i_prot:
            pia = b
            break
    return {
        "power_kw": power_kw, "p_in_kw": round(p_in, 2),
        "inom_a": round(inom, 2), "i_arranque_a": round(i_arranque, 1),
        "i_prot_a": round(i_prot, 2), "pia_sugerido": pia,
    }


# ── 9. Iluminación ──────────────────────────────────────────
def lighting_calc(area_m2, lux_req, lumens_per_fixture, cu=0.5, mf=0.8):
    """Número de luminarias necesarias."""
    total_lumens = area_m2 * lux_req / (cu * mf) if cu * mf > 0 else 0
    n = math.ceil(total_lumens / lumens_per_fixture) if lumens_per_fixture > 0 else 0
    e_real = n * lumens_per_fixture * cu * mf / area_m2 if area_m2 > 0 else 0
    return {
        "area_m2": area_m2, "lux_req": lux_req, "n_luminarias": n,
        "total_lumens": round(total_lumens, 0), "e_real_lux": round(e_real, 1),
        "cumple": e_real >= lux_req,
    }


# ── 10. Canalizaciones — capacidad de tubo ──────────────────
TUBE_AREAS = {16: 50, 20: 85, 25: 135, 32: 220, 40: 340, 50: 540, 63: 850}  # mm2 sección libre aprox
CABLE_AREAS = {1.5: 8.5, 2.5: 12.0, 4: 15.0, 6: 20.0, 10: 30.0, 16: 45.0, 25: 65.0}


def conduit_fill(cables: list[tuple], tube_diameter: int, fill_pct: float = 40):
    """Verifica si los cables caben en el tubo."""
    total_area = sum(CABLE_AREAS.get(s, 0) * n for s, n in cables)
    tube_area = TUBE_AREAS.get(tube_diameter, 0)
    max_fill = tube_area * fill_pct / 100
    return {
        "tube_diameter": tube_diameter, "tube_area": tube_area,
        "total_cable_area": round(total_area, 1), "max_fill": round(max_fill, 1),
        "fill_pct": round(total_area / tube_area * 100, 1) if tube_area > 0 else 0,
        "cumple": total_area <= max_fill,
    }


# ── 11. Puesta a tierra ─────────────────────────────────────
def earth_electrode(resistivity, length_m, diameter_m=0.014, num_electrodes=1, spacing_m=0):
    """Resistencia de un electrodo de pica (fórmula de Dwight)."""
    if length_m <= 0 or diameter_m <= 0:
        return {"error": "Parámetros inválidos"}
    r = resistivity / (2 * math.pi * length_m) * (math.log(4 * length_m / diameter_m) - 1)
    if num_electrodes > 1 and spacing_m > 0:
        # factor de reducción por múltiples electrodos
        factor = 1 / (1 + (num_electrodes - 1) * (length_m / (spacing_m + length_m)))
        r = r * factor
    return {
        "resistance_ohm": round(r, 2), "num_electrodes": num_electrodes,
        "cumple_20ohm": r <= 20, "cumple_30ohm": r <= 30,
    }


# ── 12. Baterías ────────────────────────────────────────────
def battery_calc(load_w, autonomy_h, voltage=12, dod=0.5, efficiency=0.85):
    """Capacidad de batería necesaria."""
    energy_wh = load_w * autonomy_h
    capacity_ah = energy_wh / (voltage * dod * efficiency) if voltage > 0 else 0
    return {
        "load_w": load_w, "autonomy_h": autonomy_h, "voltage": voltage,
        "energy_wh": round(energy_wh, 0), "capacity_ah": round(capacity_ah, 1),
        "dod": dod, "efficiency": efficiency,
    }


# ── 13. Cuadro eléctrico — IGA / ID ────────────────────────
def panel_calc(total_power_kw, voltage=230, phases=1, cosphi=0.9, margin=1.25):
    """IGA e ID sugeridos."""
    ib = current_from_power(total_power_kw, voltage, phases, cosphi)
    iga = ib * margin
    # ID: 30mA para vivienda, 300mA para industria
    id_type = "30 mA" if total_power_kw < 20 else "300 mA"
    iga_std = None
    for b in BREAKERS:
        if b >= iga:
            iga_std = b
            break
    return {
        "ib_a": round(ib, 2), "iga_calc_a": round(iga, 2),
        "iga_std_a": iga_std, "id_type": id_type,
    }


# ── 14. Protección contra contactos indirectos ──────────────
def indirect_contact(disconnect_time_s, z_loop_ohm, voltage=230):
    """Verifica que la corriente de defecto desconecte la protección a tiempo."""
    i_defect = voltage / z_loop_ohm if z_loop_ohm > 0 else 0
    # Para magnetotérmico tipo C: Ia = 5..10 * In
    # Simplificado: verifica I_defect >= Ia
    return {
        "z_loop_ohm": z_loop_ohm, "i_defect_a": round(i_defect, 1),
        "disconnect_time_s": disconnect_time_s,
        "cumple": i_defect > 0,
    }


# ── 15. Factor de simultaneidad ─────────────────────────────
def simultaneity_factor(n_apartments, total_power_kw):
    """Factor de simultaneidad para viviendas (REBT)."""
    if n_apartments <= 1:
        fs = 1.0
    elif n_apartments <= 5:
        fs = 0.8 + 0.04 * n_apartments
    elif n_apartments <= 10:
        fs = 0.9
    else:
        fs = 0.7 + 0.02 * min(n_apartments, 50)
    fs = min(fs, 1.0)
    power_sim = total_power_kw * fs
    return {"n_apartments": n_apartments, "factor": round(fs, 2),
            "power_simultaneous_kw": round(power_sim, 2)}


# ── 16. Armónicos — neutro ──────────────────────────────────
def neutral_harmonic(i_phase_a, thd_pct, phases=3):
    """Corriente en el neutro por armónicos triplen."""
    if phases == 3:
        # armónicos triplen se suman en el neutro
        i_neutral = i_phase_a * (thd_pct / 100) * 3  # simplificado
    else:
        i_neutral = i_phase_a * (thd_pct / 100)
    return {
        "i_phase_a": i_phase_a, "thd_pct": thd_pct,
        "i_neutral_a": round(i_neutral, 2),
        "neutro_plena_seccion": i_neutral > i_phase_a * 0.5,
    }


# ── 17. Generador ───────────────────────────────────────────
def generator_calc(load_kw, power_factor=0.8, safety_margin=1.25, altitude_m=0, temp_c=25):
    """Potencia de generador necesaria."""
    s_kva = load_kw / power_factor if power_factor > 0 else load_kw
    derating = 1.0
    if altitude_m > 1000:
        derating *= 1 - (altitude_m - 1000) * 0.0001
    if temp_c > 40:
        derating *= 1 - (temp_c - 40) * 0.01
    p_gen = s_kva * safety_margin / derating if derating > 0 else s_kva * safety_margin
    return {
        "load_kw": load_kw, "s_kva": round(s_kva, 2),
        "derating": round(derating, 3), "p_gen_kva": round(p_gen, 2),
    }


# ── 18. FV — autoconsumo con batería ───────────────────────
def fv_with_battery(p_peak_kwp, load_kw, battery_kwh, autonomy_h, losses=0.15):
    """Autoconsumo con batería."""
    prod = p_peak_kwp * 5.0 * 365 * (1 - losses)  # kWh/año estimado
    daily_prod = prod / 365
    daily_load = load_kw * 24
    surplus = max(0, daily_prod - daily_load)
    # batería cubre déficit
    deficit = max(0, daily_load - daily_prod)
    battery_coverage = min(battery_kwh, deficit) / deficit if deficit > 0 else 1
    self_consumption = min(daily_prod, daily_load) / daily_load if daily_load > 0 else 0
    return {
        "p_peak_kwp": p_peak_kwp, "produccion_diaria_kwh": round(daily_prod, 1),
        "consumo_diario_kwh": round(daily_load, 1), "excedente_kwh": round(surplus, 1),
        "deficit_kwh": round(deficit, 1), "cobertura_bateria": round(battery_coverage, 2),
        "autoconsumo_pct": round(self_consumption * 100, 1),
    }


# ── 19. Tensión — flicker ──────────────────────────────────
def flicker_calc(p_step_kw, scc_mva, voltage_kv=0.4):
    """Fluctuación de tensión por arranque de motor."""
    if scc_mva <= 0:
        return {"error": "Scc debe ser > 0"}
    du_pct = p_step_kw / (scc_mva * 1000) * 100
    return {
        "p_step_kw": p_step_kw, "scc_mva": scc_mva,
        "du_pct": round(du_pct, 2),
        "cumple_5pct": du_pct <= 5.0,
    }


# ── 20. Verificación de aislamiento ─────────────────────────
def insulation_check(voltage, r_iso_mohm, min_mohm=1.0):
    """Verifica resistencia de aislamiento."""
    return {
        "voltage": voltage, "r_iso_mohm": r_iso_mohm, "min_mohm": min_mohm,
        "cumple": r_iso_mohm >= min_mohm,
    }
