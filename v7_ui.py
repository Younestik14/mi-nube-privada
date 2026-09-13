from __future__ import annotations
import json,html,io
import pandas as pd
import streamlit as st
from v7_engine import *

USES_LIST=list(USES)

def init():
    st.session_state.setdefault('v7_project',{'name':'Proyecto sin nombre','type':'Vivienda','location':'','designer':'','iga':40,'description':'','version':'v7'})
    st.session_state.setdefault('v7_circuits',[]);st.session_state.setdefault('v7_selected',None)

def css():
    st.markdown('''<style>
    .studio-hero{position:relative;overflow:hidden;padding:30px 34px;border-radius:18px;background:linear-gradient(115deg,#10213f,#174b73);color:#fff;margin:0 0 18px;box-shadow:0 16px 34px rgba(15,23,42,.16)}
    .studio-hero:after{content:'';position:absolute;right:-80px;bottom:-120px;width:270px;height:270px;border:38px solid rgba(255,255,255,.08);border-radius:50%}
    .studio-kicker{color:#8be0e9!important;font-size:.68rem;letter-spacing:.15em;font-weight:800}.studio-hero h1{color:#fff!important;font-size:2.2rem;margin:.35rem 0}.studio-hero p{color:#d8e5f3!important;opacity:1;margin:0}
    .section{font-size:.7rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;opacity:.62;margin:22px 0 9px}
    .status{padding:12px 14px;border-radius:10px;margin:7px 0;border:1px solid rgba(120,130,150,.16);background:var(--bg-panel)}
    div[data-testid="stMetric"]{border:1px solid rgba(120,130,150,.16);border-radius:12px;padding:14px;background:var(--bg-panel)}
    .studio-note{padding:13px 15px;border-left:3px solid #0f766e;border-radius:8px;background:rgba(15,118,110,.07);font-size:.84rem;color:var(--text-secondary);margin:0 0 12px}
    .studio-note b{color:var(--text-primary)}
    </style>''',unsafe_allow_html=True)

def hero(p):
    st.markdown(f'<div class="studio-hero"><div class="studio-kicker">REBT SUITE · EXPEDIENTE TÉCNICO</div><h1>{html.escape(p["name"])}</h1><p>{html.escape(p.get("type",""))} · {html.escape(p.get("location") or "Ubicación no definida")} · Protección general {p.get("iga",40)} A</p></div>',unsafe_allow_html=True)

def project_tab():
    p=st.session_state.v7_project
    a,b=st.columns([2,1]);p['name']=a.text_input('Nombre del proyecto',p['name']);p['type']=b.selectbox('Tipo', ['Vivienda','Local comercial','Oficina','Industria','Garaje','Otro'],index=['Vivienda','Local comercial','Oficina','Industria','Garaje','Otro'].index(p.get('type','Vivienda')))
    a,b,c=st.columns(3);p['location']=a.text_input('Ubicación',p.get('location',''));p['designer']=b.text_input('Proyectista',p.get('designer',''));p['iga']=c.number_input('IGA (A)',6,400,int(p.get('iga',40)),1)
    p['description']=st.text_area('Descripción',p.get('description',''),height=90);st.session_state.v7_project=p
    st.info('Flujo recomendado: **Proyecto → Circuitos → Auto-dimensionado → Inspector → Unifilar → Presupuesto → Exportación**.')

def add_form():
    st.markdown('<div class="section">Nuevo circuito</div>',unsafe_allow_html=True)
    with st.form('v7_add'):
        a,b,c=st.columns(3);name=a.text_input('Nombre','C-01 Tomas salón');kind=b.selectbox('Uso',USES_LIST);power=c.number_input('Potencia (kW)',.05,500.,USES[kind][0],.05)
        a,b,c,d=st.columns(4);length=a.number_input('Longitud (m)',.5,2000.,15.,.5);voltage=b.selectbox('Tensión',[230.,400.]);phases=c.selectbox('Fases',[1,3]);cosphi=d.number_input('cos φ',.1,1.,1.,.01)
        a,b,c,d=st.columns(4);section=a.selectbox('Sección (mm²)',SECTIONS,index=SECTIONS.index(USES[kind][2]));breaker=b.selectbox('PIA (A)',BREAKERS,index=BREAKERS.index(USES[kind][3]));diff=c.selectbox('Diferencial',['30 mA','300 mA','Sin diferencial']);box=d.text_input('Caja','CD-01')
        auto=st.checkbox('Dimensionar automáticamente al crear',True)
        if st.form_submit_button('＋ Añadir circuito',type='primary',width='stretch'):
            x=new_circuit(name,kind,power,length,voltage,section,breaker,diff);x.update(phases=phases,cosphi=cosphi,box=box)
            if auto:x=auto_dimension(x)
            st.session_state.v7_circuits.append(x);st.session_state.v7_selected=x['id'];st.rerun()

def circuits_tab():
    circuits=st.session_state.v7_circuits
    if circuits:
        f=st.text_input('Buscar circuito',placeholder='Nombre, uso o caja…');shown=[c for c in circuits if not f or f.lower() in (c['name']+' '+c['kind']+' '+c.get('box','')).lower()]
        st.caption(f'{len(shown)} de {len(circuits)} circuitos')
        for c in shown:
            cols=st.columns([3,1,1,1,1]);
            if cols[0].button(('● ' if c['id']==st.session_state.v7_selected else '')+c['name'],key='pick'+c['id'],width='stretch'):st.session_state.v7_selected=c['id'];st.rerun()
            cols[1].write(f'{c["power_kw"]:.1f} kW');cols[2].write(f'{c["section"]:g} mm²');cols[3].write(f'PIA {c["breaker"]}');cols[4].write(f'L{c.get("phase",1)}')
    add_form()
    if not circuits:return
    sel=next((c for c in circuits if c['id']==st.session_state.v7_selected),circuits[0]);idx=circuits.index(sel)
    st.markdown('<div class="section">Editor</div>',unsafe_allow_html=True)
    with st.form('v7_edit'):
        a,b,c=st.columns(3);name=a.text_input('Nombre',sel['name']);kind=b.selectbox('Uso',USES_LIST,index=USES_LIST.index(sel['kind']));power=c.number_input('Potencia kW',.05,500.,float(sel['power_kw']),.05)
        a,b,c,d=st.columns(4);length=a.number_input('Longitud m',.5,2000.,float(sel['length_m']),.5);voltage=b.selectbox('Tensión',[230.,400.],index=0 if sel['voltage']==230 else 1);phases=c.selectbox('Fases',[1,3],index=0 if sel.get('phases',1)==1 else 1);phase=d.selectbox('Fase',[1,2,3],index=sel.get('phase',1)-1)
        a,b,c,d=st.columns(4);section=a.selectbox('Sección mm²',SECTIONS,index=SECTIONS.index(sel['section']) if sel['section'] in SECTIONS else 1);breaker=b.selectbox('PIA A',BREAKERS,index=BREAKERS.index(sel['breaker']) if sel['breaker'] in BREAKERS else 2);diff=c.selectbox('Diferencial',['30 mA','300 mA','Sin diferencial'],index=['30 mA','300 mA','Sin diferencial'].index(sel.get('differential','30 mA')));box=d.text_input('Caja',sel.get('box','CD-01'))
        a,b,c,d=st.columns(4);cos=a.number_input('cos φ',.1,1.,float(sel.get('cosphi',1)),.01);conductors=b.number_input('Conductores',2,10,int(sel.get('conductors',3)),1);loads=c.number_input('Cargas',1,100,int(sel.get('loads',1)),1);notes=d.text_input('Notas',sel.get('notes',''))
        save,auto,delete=st.columns(3);sv=save.form_submit_button('Guardar cambios',type='primary',width='stretch');ad=auto.form_submit_button('⚡ Auto-dimensionar',width='stretch');dl=delete.form_submit_button('🗑 Eliminar',width='stretch')
        if sv:
            sel.update(name=name,kind=kind,power_kw=power,length_m=length,voltage=voltage,phases=phases,phase=phase,section=section,breaker=breaker,differential=diff,box=box,cosphi=cos,conductors=conductors,loads=loads,notes=notes);circuits[idx]=sel;st.rerun()
        if ad:
            sel.update(name=name,kind=kind,power_kw=power,length_m=length,voltage=voltage,phases=phases,phase=phase,section=section,breaker=breaker,differential=diff,box=box,cosphi=cos,conductors=conductors,loads=loads,notes=notes);circuits[idx]=auto_dimension(sel);st.rerun()
        if dl:circuits.pop(idx);st.session_state.v7_selected=None;st.rerun()
    ib=current_from_power(sel['power_kw'],sel['voltage'],sel.get('phases',1),sel.get('cosphi',1));dv=voltage_drop_pct(sel['power_kw'],sel['length_m'],sel['section'],sel['voltage'],sel.get('phases',1),sel.get('cosphi',1));a,b,c,d=st.columns(4);a.metric('Ib estimada',f'{ib:.1f} A');b.metric('Caída estimada',f'{dv:.2f}%');c.metric('Potencia',f'{sel["power_kw"]:.2f} kW');d.metric('Estado', 'Correcto' if ib<=sel['breaker'] else 'PIA insuficiente')

def overview():
    p=st.session_state.v7_project;cs=st.session_state.v7_circuits;s=summary(cs,p['iga']);a,b,c,d,e=st.columns(5);a.metric('Circuitos',s['circuits']);b.metric('Potencia',f'{s["power_kw"]:.1f} kW');c.metric('🔴 Errores',s['errors']);d.metric('🟠 Avisos',s['warnings']);e.metric('🟢 OK',s['ok'])
    st.markdown('<div class="studio-note"><b>Estado del expediente.</b> Revisa el inspector antes de exportar documentación. Los indicadores son una prevalidación y no sustituyen la verificación reglamentaria final.</div>',unsafe_allow_html=True)
    st.markdown('<div class="section">Distribución de cargas</div>',unsafe_allow_html=True);ph,imb=phase_balance(cs);currents,three_phase_current=phase_currents_for_board(cs);x,y,z,t=st.columns(4);x.metric('L1',f'{ph[1]:.1f} kW',f'{currents[1]:.1f} A monofásicos');y.metric('L2',f'{ph[2]:.1f} kW',f'{currents[2]:.1f} A monofásicos');z.metric('L3',f'{ph[3]:.1f} kW',f'{currents[3]:.1f} A monofásicos');t.metric('3Φ común',f'{three_phase_current:.1f} A');st.caption(f'Desequilibrio relativo estimado: {imb:.1f}% · Las cargas trifásicas se muestran por separado porque afectan a las tres fases.')
    if cs:
        df=pd.DataFrame([{'Circuito':c['name'],'Uso':c['kind'],'kW':c['power_kw'],'m':c['length_m'],'Sección':c['section'],'PIA':c['breaker'],'ΔV %':round(voltage_drop_pct(c['power_kw'],c['length_m'],c['section'],c['voltage'],c.get('phases',1),c.get('cosphi',1)),2)} for c in cs if c.get('enabled',True)]);st.dataframe(df,use_container_width=True,hide_index=True)
    a,b=st.columns(2)
    if a.button('⚡ Dimensionar todos los circuitos',type='primary',width='stretch'):st.session_state.v7_circuits=[auto_dimension(c) for c in cs];st.rerun()
    if b.button('🧹 Limpiar circuito desactivado',width='stretch'):st.session_state.v7_circuits=[c for c in cs if c.get('enabled',True)];st.rerun()

def inspector():
    p=st.session_state.v7_project;f=inspect(st.session_state.v7_circuits,p['iga']);counts={'error':0,'warning':0,'ok':0}
    for status,name,msg in f:counts[status]+=1;icon={'error':'🔴','warning':'🟠','ok':'🟢'}[status];st.markdown(f'<div class="status"><b>{icon} {html.escape(name)}</b> · {html.escape(msg)}</div>',unsafe_allow_html=True)
    st.caption(f'Resultado: {counts["error"]} errores · {counts["warning"]} avisos · {counts["ok"]} comprobaciones OK. Prevalidación orientativa.')

def unifilar():
    p=st.session_state.v7_project;cs=st.session_state.v7_circuits
    # HTML/SVG inline, intentionally dependency-free
    width=1180;row=78;height=max(360,170+row*len(cs));esc=lambda x:html.escape(str(x));parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><rect width="100%" height="100%" fill="white"/><text x="30" y="35" font-family="Arial" font-size="22" font-weight="700">{esc(p["name"])}</text><text x="30" y="58" font-family="Arial" font-size="12" fill="#667085">Unifilar preliminar · REBT Suite v7</text><line x1="80" y1="110" x2="1080" y2="110" stroke="#202938" stroke-width="4"/><rect x="180" y="84" width="140" height="52" rx="8" fill="white" stroke="#202938"/><text x="250" y="115" text-anchor="middle" font-family="Arial">IGA {p["iga"]} A</text><rect x="370" y="84" width="160" height="52" rx="8" fill="white" stroke="#202938"/><text x="450" y="115" text-anchor="middle" font-family="Arial">ID 30 mA</text><line x1="600" y1="110" x2="600" y2="{130+row*len(cs)}" stroke="#202938" stroke-width="3"/>']
    for i,c in enumerate(cs):
        y=160+i*row;parts += [f'<line x1="600" y1="{y}" x2="1100" y2="{y}" stroke="#202938" stroke-width="2"/><rect x="640" y="{y-23}" width="190" height="46" rx="7" fill="white" stroke="#202938"/><text x="735" y="{y-3}" text-anchor="middle" font-family="Arial" font-size="13" font-weight="700">{esc(c["name"][:24])}</text><text x="735" y="{y+14}" text-anchor="middle" font-family="Arial" font-size="11">PIA {c["breaker"]} A · {c["section"]:g} mm²</text><text x="850" y="{y+4}" font-family="Arial" font-size="12">{esc(c["kind"])} · {c["power_kw"]:.1f} kW · L{c.get("phase",1)}</text>']
    svg=''.join(parts)+'</svg>';st.components.v1.html(svg,height=height,scrolling=True);st.download_button('⬇ Descargar unifilar SVG',svg.encode(),'unifilar-v7.svg','image/svg+xml',width='stretch')

def budget():
    rows=budget_items(st.session_state.v7_circuits)
    if not rows:st.info('Añade circuitos para generar mediciones.');return
    df=pd.DataFrame(rows);st.dataframe(df,use_container_width=True,hide_index=True);direct=float(df['Importe'].sum());a,b,c=st.columns(3);a.metric('Material',f'{direct:,.2f} €');b.metric('Con auxiliares',f'{direct*1.1:,.2f} €');c.metric('Total + IVA',f'{direct*1.1*1.21:,.2f} €');st.caption('Precios orientativos. Sustituir por tarifas reales.')
    buf=io.BytesIO();df.to_excel(buf,index=False);st.download_button('⬇ Exportar mediciones Excel',buf.getvalue(),'mediciones-rebt-v7.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',width='stretch')

def data_tab():
    payload=project_payload(st.session_state.v7_project,st.session_state.v7_circuits);raw=json.dumps(payload,ensure_ascii=False,indent=2);st.download_button('⬇ Exportar proyecto JSON',raw,'proyecto-rebt-v7.json','application/json',width='stretch')
    up=st.file_uploader('Importar proyecto',type=['json'])
    if up:
        try:
            d=json.load(up);st.session_state.v7_project=d['project'];st.session_state.v7_circuits=[normalize_circuit(x) for x in d['circuits']];st.session_state.v7_selected=None;st.success('Proyecto importado correctamente.');st.rerun()
        except Exception as e:st.error(f'No se pudo importar: {e}')

def render():
    init();css();hero(st.session_state.v7_project);tabs=st.tabs(['📊 Resumen','🏗️ Proyecto','🔌 Circuitos','🔎 Inspector','📐 Unifilar','💰 Presupuesto','💾 Datos'])
    with tabs[0]:overview()
    with tabs[1]:project_tab()
    with tabs[2]:circuits_tab()
    with tabs[3]:inspector()
    with tabs[4]:unifilar()
    with tabs[5]:budget()
    with tabs[6]:data_tab()
