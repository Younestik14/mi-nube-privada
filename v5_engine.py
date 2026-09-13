"""
REBT Suite v5 - Project engineering layer.
Keeps project topology, automatic checks and single-line diagram separate
from the legacy calculators.
"""
from __future__ import annotations
import math
from datetime import datetime

NORMALIZED = [1.5,2.5,4,6,10,16,25,35,50,70,95,120,150,185,240,300]
BREAKERS = [6,10,16,20,25,32,40,50,63,80,100,125,160,200,250,315,400]

def new_circuit(name="Nuevo circuito", kind="Tomas", power_kw=2.0, length_m=15.0,
                voltage=230.0, section=2.5, breaker=16, differential="30 mA"):
    return {
        "id": f"C-{int(datetime.now().timestamp()*1000)}",
        "name": name, "kind": kind, "power_kw": float(power_kw),
        "length_m": float(length_m), "voltage": float(voltage),
        "section": float(section), "breaker": int(breaker),
        "differential": differential, "box": "CD-01", "notes": ""
    }

def current_from_power(power_kw, voltage=230, phases=1, cosphi=1.0):
    if voltage <= 0 or cosphi <= 0: return 0.0
    return power_kw*1000/(voltage*cosphi*(math.sqrt(3) if phases == 3 else 1))

def voltage_drop_pct(power_kw, length_m, section, voltage=230, copper=True, phases=1, cosphi=1):
    if section <= 0 or voltage <= 0: return 999.0
    ib=current_from_power(power_kw, voltage, phases, cosphi)
    rho=0.0175 if copper else 0.0282
    factor=math.sqrt(3) if phases == 3 else 2
    du=factor*length_m*ib*rho/(section*1000)
    return du/voltage*100

def inspector(circuits, main_breaker=40, installation_limit=5.0):
    findings=[]
    total_kw=sum(max(0,c["power_kw"]) for c in circuits)
    for c in circuits:
        ib=current_from_power(c["power_kw"],c["voltage"],1)
        s=c["section"]; iz_ref={1.5:14,2.5:21,4:27,6:36,10:50,16:66,25:84,35:104,50:125,70:160,95:194,120:225}.get(s,0)
        dv=voltage_drop_pct(c["power_kw"],c["length_m"],s,c["voltage"])
        if iz_ref and c["breaker"] > iz_ref:
            findings.append(("error",c["name"],f"In={c['breaker']} A supera una Iz orientativa de {iz_ref:g} A para {s:g} mm²."))
        elif iz_ref and ib > iz_ref:
            findings.append(("error",c["name"],f"Ib={ib:.1f} A supera la Iz orientativa de {iz_ref:g} A."))
        else:
            findings.append(("ok",c["name"],f"Relación térmica coherente: Ib={ib:.1f} A · PIA={c['breaker']} A · Iz≈{iz_ref:g} A."))
        if dv > installation_limit:
            findings.append(("error",c["name"],f"Caída de tensión {dv:.2f}% > {installation_limit:.1f}%."))
        elif dv > installation_limit*0.8:
            findings.append(("warning",c["name"],f"Caída de tensión {dv:.2f}% próxima al límite de {installation_limit:.1f}%."))
        else:
            findings.append(("ok",c["name"],f"Caída de tensión {dv:.2f}% ≤ {installation_limit:.1f}%."))
        if c["differential"] == "Sin diferencial":
            findings.append(("warning",c["name"],"Circuito sin diferencial asociado: revisar esquema y requisitos aplicables."))
    if total_kw > main_breaker*230/1000:
        findings.append(("warning","Cuadro",f"Potencia instalada {total_kw:.1f} kW supera la potencia teórica asociada al IGA de {main_breaker} A."))
    findings.append(("ok","Cuadro",f"Se han inspeccionado {len(circuits)} circuitos y {total_kw:.1f} kW de potencia instalada."))
    return findings

def summary(circuits, main_breaker):
    checks=inspector(circuits,main_breaker)
    return {
        "circuits":len(circuits),
        "power_kw":sum(c["power_kw"] for c in circuits),
        "errors":sum(x[0]=="error" for x in checks),
        "warnings":sum(x[0]=="warning" for x in checks),
        "ok":sum(x[0]=="ok" for x in checks),
    }

def unifilar_svg(project_name, circuits, main_breaker=40):
    width=980; row_h=92; height=max(300,170+len(circuits)*row_h)
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           '<rect width="100%" height="100%" fill="white"/>',
           f'<text x="40" y="35" font-family="Arial" font-size="22" font-weight="700" fill="#182230">{project_name}</text>',
           '<text x="40" y="60" font-family="Arial" font-size="13" fill="#687586">Unifilar generado automáticamente · revisar antes de uso profesional</text>']
    x0=80; x1=900; y=110
    parts += [f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="#1d2939" stroke-width="4"/>',
              f'<text x="{x0}" y="{y-18}" font-family="Arial" font-size="14">RED</text>',
              f'<rect x="170" y="{y-24}" width="110" height="48" rx="8" fill="#f4f6f8" stroke="#1d2939"/>',
              f'<text x="225" y="{y+5}" text-anchor="middle" font-family="Arial" font-size="14">IGA {main_breaker} A</text>',
              f'<rect x="340" y="{y-24}" width="140" height="48" rx="8" fill="#f4f6f8" stroke="#1d2939"/>',
              f'<text x="410" y="{y+5}" text-anchor="middle" font-family="Arial" font-size="14">ID 30 mA</text>',
              f'<line x1="550" y1="{y}" x2="550" y2="{y+len(circuits)*row_h}" stroke="#1d2939" stroke-width="3"/>']
    for i,c in enumerate(circuits):
        cy=y+60+i*row_h
        parts += [f'<line x1="550" y1="{cy}" x2="900" y2="{cy}" stroke="#1d2939" stroke-width="2"/>',
                  f'<rect x="585" y="{cy-26}" width="130" height="52" rx="7" fill="#fff" stroke="#1d2939"/>',
                  f'<text x="650" y="{cy-3}" text-anchor="middle" font-family="Arial" font-size="14" font-weight="700">{c["name"][:18]}</text>',
                  f'<text x="650" y="{cy+15}" text-anchor="middle" font-family="Arial" font-size="12">{c["breaker"]} A · {c["section"]:g} mm²</text>',
                  f'<text x="730" y="{cy+5}" font-family="Arial" font-size="13">{c["kind"]} · {c["power_kw"]:.1f} kW · {c["length_m"]:.0f} m</text>']
    parts.append('</svg>')
    return ''.join(parts)
