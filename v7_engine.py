from __future__ import annotations
import math
from datetime import datetime

SECTIONS=[1.5,2.5,4,6,10,16,25,35,50,70,95,120,150,185,240,300]
BREAKERS=[6,10,16,20,25,32,40,50,63,80,100,125,160,200,250,315,400]
IZ_CU={1.5:14,2.5:21,4:27,6:36,10:50,16:66,25:84,35:104,50:125,70:160,95:194,120:225,150:260,185:300,240:350,300:405}
USES={
 'Tomas':(2.0,5.0,2.5,16),'Alumbrado':(1.0,3.0,1.5,10),'Cocina':(3.5,5.0,6.0,25),
 'Climatización':(4.0,5.0,6.0,25),'Motor':(5.5,5.0,6.0,25),'IRVE':(7.4,5.0,10.0,32),'Otros':(2.0,5.0,2.5,16)
}

def uid(prefix='C'):
    return f'{prefix}-{datetime.now().strftime("%H%M%S%f")}'

def new_circuit(name='Nuevo circuito',kind='Tomas',power_kw=2.0,length_m=15.0,voltage=230.0,section=2.5,breaker=16,differential='30 mA'):
    return {'id':uid(),'name':name,'kind':kind,'power_kw':float(power_kw),'length_m':float(length_m),'voltage':float(voltage),
            'section':float(section),'breaker':int(breaker),'differential':differential,'box':'CD-01','notes':'','phases':1,
            'cosphi':1.0,'method':'B1','conductors':3,'material':'Cobre','phase':1,'loads':1,'enabled':True}

def current_from_power(power_kw,voltage=230,phases=1,cosphi=1):
    if voltage<=0 or cosphi<=0:return 0.0
    return power_kw*1000/(voltage*cosphi*(math.sqrt(3) if phases==3 else 1))

def voltage_drop_pct(power_kw,length_m,section,voltage=230,phases=1,cosphi=1,rho=0.0175):
    """Voltage drop as a percentage.

    ``rho`` is expressed in ohm·mm²/m, so length must stay in metres.  The
    previous implementation divided by 1,000 a second time, making every
    voltage-drop result one thousand times too optimistic.
    """
    if min(section,voltage)<=0:return 999.0
    ib=current_from_power(power_kw,voltage,phases,cosphi)
    factor=math.sqrt(3) if phases==3 else 2
    return factor*length_m*ib*rho/section/voltage*100

def suggest_section(power_kw,length_m,voltage=230,phases=1,cosphi=1,limit=5,material='Cobre'):
    rho=.0175 if material=='Cobre' else .0282
    ib=current_from_power(power_kw,voltage,phases,cosphi)
    factor=.82 if material=='Aluminio' else 1
    for s in SECTIONS:
        iz=IZ_CU[s]*factor; dv=voltage_drop_pct(power_kw,length_m,s,voltage,phases,cosphi,rho)
        if iz>=ib and dv<=limit:
            possible=[b for b in BREAKERS if b>=math.ceil(ib) and b<=iz]
            return s,(possible[0] if possible else None),ib,dv
    return None,None,ib,voltage_drop_pct(power_kw,length_m,SECTIONS[-1],voltage,phases,cosphi,rho)

def auto_dimension(c):
    lim=3 if c.get('kind')=='Alumbrado' else 5
    s,b,ib,dv=suggest_section(c['power_kw'],c['length_m'],c.get('voltage',230),c.get('phases',1),c.get('cosphi',1),lim,c.get('material','Cobre'))
    o=dict(c)
    # Do not overwrite a valid existing value with None when the fixed, simple
    # v7 table has no compliant solution. The inspector will explain why.
    if s is not None:o['section']=s
    if b is not None:o['breaker']=b
    o.update(estimated_ib=ib,estimated_dv=dv,auto_dimensioned=s is not None and b is not None)
    return o

def normalize_circuit(c):
    d=new_circuit()
    d.update(c or {})
    for k in ('power_kw','length_m','voltage','section','cosphi'): d[k]=float(d[k])
    for k in ('breaker','phases','conductors','loads','phase'): d[k]=int(d[k])
    d['enabled']=bool(d.get('enabled',True)); return d

def inspect(circuits,main_breaker=40):
    findings=[]
    for c in circuits:
        if not c.get('enabled',True):continue
        ib=current_from_power(c['power_kw'],c['voltage'],c.get('phases',1),c.get('cosphi',1))
        iz=IZ_CU.get(float(c['section']),0)*(0.82 if c.get('material')=='Aluminio' else 1)
        dv=voltage_drop_pct(c['power_kw'],c['length_m'],c['section'],c['voltage'],c.get('phases',1),c.get('cosphi',1),.0175 if c.get('material','Cobre')=='Cobre' else .0282)
        lim=3 if c['kind']=='Alumbrado' else 5
        if c['breaker'] < ib: findings.append(('error',c['name'],f'PIA {c["breaker"]} A es inferior a Ib {ib:.1f} A.'))
        elif iz and c['breaker']>iz: findings.append(('error',c['name'],f'PIA {c["breaker"]} A supera Iz≈{iz:g} A.'))
        elif iz and ib>iz: findings.append(('error',c['name'],f'Ib {ib:.1f} A supera Iz≈{iz:g} A.'))
        else: findings.append(('ok',c['name'],f'Ib {ib:.1f} A · PIA {c["breaker"]} A · Iz≈{iz:g} A.'))
        if dv>lim: findings.append(('error',c['name'],f'Caída {dv:.2f}% > {lim:.1f}%.'))
        elif dv>lim*.8: findings.append(('warning',c['name'],f'Caída {dv:.2f}% próxima al límite {lim:.1f}%.'))
        else: findings.append(('ok',c['name'],f'Caída {dv:.2f}% ≤ {lim:.1f}%.'))
        if c.get('differential')=='Sin diferencial':findings.append(('warning',c['name'],'Revisar protección diferencial aplicable.'))
        if not c.get('box'):findings.append(('warning',c['name'],'No se ha definido caja de derivación.'))
    phase_currents, three_phase_current = phase_currents_for_board(circuits)
    overloaded=[f'L{phase}' for phase,current in phase_currents.items() if current>main_breaker]
    if three_phase_current>main_breaker:
        overloaded.append('carga trifásica')
    if overloaded:
        findings.append(('warning','Cuadro',f'IGA {main_breaker} A superado en {", ".join(overloaded)} (sin simultaneidad).'))
    return findings

def summary(circuits,main_breaker):
    f=inspect(circuits,main_breaker);return {'circuits':sum(c.get('enabled',True) for c in circuits),'power_kw':sum(c['power_kw'] for c in circuits if c.get('enabled',True)),'errors':sum(x[0]=='error' for x in f),'warnings':sum(x[0]=='warning' for x in f),'ok':sum(x[0]=='ok' for x in f)}

def phase_balance(circuits):
    p={1:0.,2:0.,3:0.}
    for i,c in enumerate(circuits):
        if not c.get('enabled',True):continue
        ph=int(c.get('phase', (i%3)+1));p[ph]=p.get(ph,0)+c['power_kw']
    vals=list(p.values()); avg=sum(vals)/3 if vals else 0
    imbalance=(max(vals)-min(vals))/avg*100 if avg else 0
    return p,imbalance

def phase_currents_for_board(circuits):
    """Return single-phase current by phase and the total three-phase current.

    A three-phase load draws the same current through all three phases and
    therefore must not be assigned to just L1/L2/L3 for balancing.
    """
    currents={1:0.,2:0.,3:0.}; three_phase_current=0.
    for i,c in enumerate(circuits):
        if not c.get('enabled',True):continue
        ib=current_from_power(c['power_kw'],c['voltage'],c.get('phases',1),c.get('cosphi',1))
        if c.get('phases',1)==3:
            three_phase_current+=ib
        else:
            phase=int(c.get('phase',(i%3)+1))
            currents[phase]=currents.get(phase,0)+ib
    return currents,three_phase_current

def budget_items(circuits):
    rows=[]
    for c in circuits:
        if not c.get('enabled',True):continue
        qty=max(1,round(c['length_m']*c.get('conductors',3)))
        rows += [{'Código':'CB-'+c['id'][-5:],'Partida':f'Conductor {c["section"]:g} mm² · {c["kind"]}','Cantidad':qty,'Unidad':'m','Precio':round(.85*c['section'],2),'Importe':round(qty*.85*c['section'],2)},
                 {'Código':'PIA-'+c['id'][-5:],'Partida':f'PIA {c["breaker"]} A','Cantidad':1,'Unidad':'ud','Precio':round(8+c['breaker']*.18,2),'Importe':round(8+c['breaker']*.18,2)}]
    return rows

def project_payload(project,circuits):return {'schema':'rebt-suite-v7','exported_at':datetime.now().isoformat(),'project':project,'circuits':circuits}
