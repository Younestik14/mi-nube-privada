"""Motor de cálculo eléctrico (REBT + IEC)."""
import math
from typing import Optional

SECTIONS = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300]
BREAKERS = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400]
IZ_CU = {1.5: 14, 2.5: 21, 4: 27, 6: 36, 10: 50, 16: 66, 25: 84, 35: 104, 50: 125,
         70: 160, 95: 194, 120: 225, 150: 260, 185: 300, 240: 350, 300: 405}

USES = {
    "Tomas": (2.0, 5.0, 2.5, 16),
    "Alumbrado": (1.0, 3.0, 1.5, 10),
    "Cocina": (3.5, 5.0, 6.0, 25),
    "Climatizacion": (4.0, 5.0, 6.0, 25),
    "Motor": (5.5, 5.0, 6.0, 25),
    "IRVE": (7.4, 5.0, 10.0, 32),
    "Otros": (2.0, 5.0, 2.5, 16),
}


def current_from_power(power_kw: float, voltage: float = 230, phases: int = 1, cosphi: float = 1.0) -> float:
    if voltage <= 0 or cosphi <= 0:
        return 0.0
    return power_kw * 1000 / (voltage * cosphi * (math.sqrt(3) if phases == 3 else 1))


def voltage_drop_pct(power_kw: float, length_m: float, section: float, voltage: float = 230,
                    phases: int = 1, cosphi: float = 1.0, rho: float = 0.0175) -> float:
    if min(section, voltage) <= 0:
        return 999.0
    ib = current_from_power(power_kw, voltage, phases, cosphi)
    factor = math.sqrt(3) if phases == 3 else 2
    return factor * length_m * ib * rho / section / voltage * 100


def suggest_section(power_kw: float, length_m: float, voltage: float = 230, phases: int = 1,
                   cosphi: float = 1.0, limit: float = 5.0, material: str = "Cobre") -> dict:
    rho = 0.0282 if material == "Aluminio" else 0.0175
    ib = current_from_power(power_kw, voltage, phases, cosphi)
    factor = 0.82 if material == "Aluminio" else 1.0
    for s in SECTIONS:
        iz = IZ_CU[s] * factor
        dv = voltage_drop_pct(power_kw, length_m, s, voltage, phases, cosphi, rho)
        if iz >= ib and dv <= limit:
            possible = [b for b in BREAKERS if b >= math.ceil(ib) and b <= iz]
            return {"section": s, "breaker": possible[0] if possible else None,
                    "ib": ib, "dv": dv, "iz": iz}
    s = SECTIONS[-1]
    dv = voltage_drop_pct(power_kw, length_m, s, voltage, phases, cosphi, rho)
    return {"section": s, "breaker": None, "ib": ib, "dv": dv, "iz": IZ_CU[s] * factor}


def short_circuit_check(icc_ka: float, time_s: float, section: float, material: str = "Cobre",
                        insulation: str = "PVC") -> dict:
    """Verificación térmica de cortocircuito: S >= Icc^2 * t / k^2"""
    k_values = {
        ("Cobre", "PVC"): 115, ("Cobre", "XLPE"): 143,
        ("Aluminio", "PVC"): 76, ("Aluminio", "XLPE"): 94,
    }
    k = k_values.get((material, insulation), 115)
    s_min = icc_ka * 1000 * math.sqrt(time_s) / k
    return {
        "k": k,
        "s_min": round(s_min, 2),
        "cumple": section >= s_min,
        "section": section,
    }


def phase_balance(circuits: list[dict]) -> tuple[dict, float]:
    phases = {1: 0.0, 2: 0.0, 3: 0.0}
    for c in circuits:
        if not c.get("enabled", True):
            continue
        p = c.get("power_kw", 0) / (3 if c.get("phases", 1) == 3 else 1)
        if c.get("phases", 1) == 3:
            for ph in (1, 2, 3):
                phases[ph] += p
        else:
            ph = c.get("phase", 1)
            phases[ph] += c.get("power_kw", 0)
    vals = [phases[1], phases[2], phases[3]]
    mx = max(vals) if vals else 0
    mn = min(vals) if vals else 0
    avg = sum(vals) / 3 if vals else 0
    imbalance = ((mx - mn) / avg * 100) if avg > 0 else 0
    return phases, round(imbalance, 1)


def fv_dimension(power_peak_kw: float, system: str = "230V", losses: float = 0.15,
                 irradiance: float = 5.0) -> dict:
    """Dimensionado fotovoltaico simplificado."""
    p_ac = power_peak_kw * (1 - losses)
    production = power_peak_kw * irradiance * 365 * (1 - losses)
    return {
        "p_pico_kwp": power_peak_kw,
        "p_ac_kw": round(p_ac, 2),
        "produccion_anual_kwh": round(production, 0),
        "ratio_performance": round(1 - losses, 2),
    }
