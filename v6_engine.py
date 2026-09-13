"""
REBT Suite · Motor de proyecto v6
Capa independiente para el diseñador eléctrico.
Los valores térmicos de referencia son orientativos; el cálculo profesional debe
seleccionar método de instalación, agrupamiento, temperatura, material y tablas
REBT/UNE aplicables.
"""
from __future__ import annotations
import math, json
from datetime import datetime

SECTIONS = [1.5,2.5,4,6,10,16,25,35,50,70,95,120,150,185,240,300]
BREAKERS = [6,10,16,20,25,32,40,50,63,80,100,125,160,200,250,315,400]
# Valores orientativos de Iz para cobre en condiciones genéricas.
IZ_CU = {1.5:14,2.5:21,4:27,6:36,10:50,16:66,25:84,35:104,50:125,70:160,95:194,120:225,150:260,185:300,240:350,300:405}

def new_circuit(name="Nuevo circuito", kind="Tomas", power_kw=2.0, length_m=15.0,
                voltage=230.0, section=2.5, breaker=16, differential="30 mA"):
    return {"id": f"C-{int(datetime.now().timestamp()*1000)}", "name":name,
            "kind":kind,"power_kw":float(power_kw),"length_m":float(length_m),
            "voltage":float(voltage),"section":float(section),"breaker":int(breaker),
            "differential":differential,"box":"CD-01","notes":"","phases":1,
            "cosphi":1.0,"method":"B1","conductors":3,"material":"Cobre"}

def current_from_power(power_kw, voltage=230, phases=1, cosphi=1.0):
    if voltage <= 0 or cosphi <= 0: return 0.0
    return power_kw*1000/(voltage*cosphi*(math.sqrt(3) if phases == 3 else 1))

def voltage_drop_pct(power_kw,length_m,section,voltage=230,phases=1,cosphi=1.0,rho=0.0175):
    if section <= 0 or voltage <= 0: return 999.0
    ib=current_from_power(power_kw,voltage,phases,cosphi)
    factor=math.sqrt(3) if phases == 3 else 2
    return factor*length_m*ib*rho/(section*1000)/voltage*100

def suggest_section(power_kw,length_m,voltage=230,phases=1,cosphi=1.0,limit=3.0,material="Cobre"):
    rho = 0.0175 if material=="Cobre" else 0.0282
    ib=current_from_power(power_kw,voltage,phases,cosphi)
    for s in SECTIONS:
        iz=IZ_CU.get(s,0) * (0.82 if material=="Aluminio" else 1)
        if iz >= ib and voltage_drop_pct(power_kw,length_m,s,voltage,phases,cosphi,rho) <= limit:
            breaker = next((b for b in BREAKERS if b >= math.ceil(ib) and b <= iz), BREAKERS[-1])
            return s, breaker, ib, voltage_drop_pct(power_kw,length_m,s,voltage,phases,cosphi,rho)
    return SECTIONS[-1], BREAKERS[-1], ib, voltage_drop_pct(power_kw,length_m,SECTIONS[-1],voltage,phases,cosphi,rho)

def auto_dimension(c):
    s,b,ib,dv=suggest_section(c["power_kw"],c["length_m"],c["voltage"],c.get("phases",1),c.get("cosphi",1),3 if c["kind"]=="Alumbrado" else 5,c.get("material","Cobre"))
    out=dict(c); out["section"]=s; out["breaker"]=b; out["estimated_ib"]=ib; out["estimated_dv"]=dv
    return out

def inspect(circuits, main_breaker=40):
    findings=[]
    for c in circuits:
        ib=current_from_power(c["power_kw"],c["voltage"],c.get("phases",1),c.get("cosphi",1))
        s=float(c["section"]); iz=IZ_CU.get(s,0)
        dv=voltage_drop_pct(c["power_kw"],c["length_m"],s,c["voltage"],c.get("phases",1),c.get("cosphi",1),0.0175 if c.get("material","Cobre")=="Cobre" else 0.0282)
        lim=3.0 if c["kind"]=="Alumbrado" else 5.0
        if iz and c["breaker"]>iz: findings.append(("error",c["name"],f"PIA {c['breaker']} A > Iz orientativa {iz:g} A."))
        elif iz and ib>iz: findings.append(("error",c["name"],f"Ib {ib:.1f} A > Iz orientativa {iz:g} A."))
        else: findings.append(("ok",c["name"],f"Ib {ib:.1f} A · PIA {c['breaker']} A · Iz≈{iz:g} A."))
        if dv>lim: findings.append(("error",c["name"],f"Caída {dv:.2f}% > {lim:.1f}%."))
        elif dv>lim*.8: findings.append(("warning",c["name"],f"Caída {dv:.2f}% próxima al límite {lim:.1f}%."))
        else: findings.append(("ok",c["name"],f"Caída {dv:.2f}% ≤ {lim:.1f}%."))
        if c.get("differential")=="Sin diferencial": findings.append(("warning",c["name"],"Revisar protección diferencial aplicable."))
        if not c.get("box"): findings.append(("warning",c["name"],"No se ha definido caja de derivación."))
    total=sum(max(0,c["power_kw"]) for c in circuits)
    if total > main_breaker*230/1000: findings.append(("warning","Cuadro",f"{total:.1f} kW instalados frente a {main_breaker} A de IGA teórico."))
    findings.append(("ok","Cuadro",f"{len(circuits)} circuitos analizados · {total:.1f} kW instalados."))
    return findings

def summary(circuits, main_breaker):
    f=inspect(circuits,main_breaker)
    return {"circuits":len(circuits),"power_kw":sum(c["power_kw"] for c in circuits),
            "errors":sum(x[0]=="error" for x in f),"warnings":sum(x[0]=="warning" for x in f),
            "ok":sum(x[0]=="ok" for x in f)}

def load_balance(circuits):
    phases={1:0.0,2:0.0,3:0.0}
    for i,c in enumerate(circuits):
        phases[(i%3)+1]+=c["power_kw"]
    total=sum(phases.values())
    spread=max(phases.values())-min(phases.values()) if phases else 0
    return phases,total,spread

def budget_items(circuits):
    rows=[]
    for c in circuits:
        conductors=c.get("conductors",3)
        qty=max(1,round(c["length_m"]*conductors))
        rows.append({"Código":"CB-"+c["id"].split("-")[-1][-5:],"Partida":f"Cable {c['section']:g} mm² · {c['kind']}",
                     "Cantidad":qty,"Unidad":"m","Precio":0.85*c["section"],"Importe":qty*0.85*c["section"]})
        rows.append({"Código":"PIA-"+c["id"].split("-")[-1][-5:],"Partida":f"PIA {c['breaker']} A","Cantidad":1,"Unidad":"ud","Precio":8+c["breaker"]*.18,"Importe":8+c["breaker"]*.18})
    return rows

def project_payload(project, circuits):
    return {"schema":"rebt-suite-v6","exported_at":datetime.now().isoformat(),
            "project":project,"circuits":circuits}

def unifilar_svg(project_name,circuits,main_breaker=40):
    width=1120; row=88; h=max(360,190+row*len(circuits))
    esc=lambda x:str(x).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    p=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}" viewBox="0 0 {width} {h}">',
       '<rect width="100%" height="100%" fill="#fbfcfe"/>',
       f'<text x="45" y="38" font-family="Arial" font-size="24" font-weight="700" fill="#162033">{esc(project_name)}</text>',
       '<text x="45" y="62" font-family="Arial" font-size="12" fill="#687586">Unifilar preliminar · generado por REBT Suite</text>',
       '<line x1="70" y1="125" x2="1050" y2="125" stroke="#1d2939" stroke-width="4"/>',
       '<text x="70" y="108" font-family="Arial" font-size="13">RED</text>',
       f'<rect x="180" y="99" width="130" height="52" rx="8" fill="#fff" stroke="#1d2939"/><text x="245" y="130" text-anchor="middle" font-family="Arial" font-size="14">IGA {main_breaker} A</text>',
       '<rect x="360" y="99" width="150" height="52" rx="8" fill="#fff" stroke="#1d2939"/><text x="435" y="130" text-anchor="middle" font-family="Arial" font-size="14">ID 30 mA</text>',
       '<line x1="580" y1="125" x2="580" y2="'+str(150+row*len(circuits))+'" stroke="#1d2939" stroke-width="3"/>']
    for i,c in enumerate(circuits):
        y=185+i*row
        p += [f'<line x1="580" y1="{y}" x2="1030" y2="{y}" stroke="#1d2939" stroke-width="2"/>',
              f'<rect x="620" y="{y-25}" width="155" height="50" rx="7" fill="#fff" stroke="#1d2939"/>',
              f'<text x="697" y="{y-3}" text-anchor="middle" font-family="Arial" font-size="13" font-weight="700">{esc(c["name"][:20])}</text>',
              f'<text x="697" y="{y+14}" text-anchor="middle" font-family="Arial" font-size="11">{c["breaker"]} A · {c["section"]:g} mm²</text>',
              f'<text x="795" y="{y+4}" font-family="Arial" font-size="12">{esc(c["kind"])} · {c["power_kw"]:.1f} kW · {c["length_m"]:.0f} m</text>']
    return "".join(p+['</svg>'])
