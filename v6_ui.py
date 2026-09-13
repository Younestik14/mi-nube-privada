from __future__ import annotations
import json, html
import pandas as pd
import streamlit as st
from v6_engine import (new_circuit, auto_dimension, inspect, summary, load_balance,
                       budget_items, project_payload, unifilar_svg, current_from_power, voltage_drop_pct)

def _init():
    st.session_state.setdefault("v6_project", {"name":"Proyecto sin nombre","type":"Vivienda","location":"","designer":"","iga":40,"description":""})
    st.session_state.setdefault("v6_circuits", [])
    st.session_state.setdefault("v6_selected", None)
    st.session_state.setdefault("v6_filter","Todos")

def _css():
    st.markdown("""<style>
    .v6-hero{padding:26px 30px;border:1px solid rgba(120,130,150,.18);border-radius:20px;
    background:linear-gradient(135deg,rgba(38,92,160,.13),rgba(255,255,255,.02));margin-bottom:18px}
    .v6-kicker{font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;font-weight:800;opacity:.62}
    .v6-title{font-size:2.15rem;font-weight:850;line-height:1.05;margin:5px 0}
    .v6-sub{opacity:.7;font-size:.92rem}.v6-card{border:1px solid rgba(120,130,150,.2);border-radius:16px;padding:18px;height:100%}
    .v6-card h3{margin:0 0 6px;font-size:1rem}.v6-number{font-size:1.65rem;font-weight:800}
    .v6-muted{opacity:.62;font-size:.78rem}.v6-pill{display:inline-block;padding:4px 9px;border-radius:999px;
    background:rgba(38,92,160,.10);font-size:.72rem;font-weight:700;margin:2px}
    .v6-step{font-size:.78rem;font-weight:750;opacity:.72}.v6-danger{border-left:4px solid #d84a4a;padding-left:10px}
    .v6-ok{border-left:4px solid #2d9b67;padding-left:10px}
    div[data-testid="stMetric"]{border:1px solid rgba(120,130,150,.18);padding:12px;border-radius:14px}
    </style>""",unsafe_allow_html=True)

def _hero(project):
    st.markdown(f"""<div class="v6-hero">
      <div class="v6-kicker">REBT SUITE · DISEÑO ELÉCTRICO</div>
      <div class="v6-title">{html.escape(project['name'])}</div>
      <div class="v6-sub">{html.escape(project.get('type',''))} · {html.escape(project.get('location','') or 'Ubicación no definida')} · IGA {project.get('iga',40)} A</div>
    </div>""",unsafe_allow_html=True)

def _project():
    p=st.session_state.v6_project
    a,b=st.columns([2,1])
    with a:
        p["name"]=st.text_input("Nombre del proyecto",p["name"],key="v6_name")
        p["description"]=st.text_area("Descripción",p.get("description",""),height=85,key="v6_desc")
    with b:
        p["type"]=st.selectbox("Tipo de instalación",["Vivienda","Local comercial","Oficina","Industria","Garaje","Otros"],index=["Vivienda","Local comercial","Oficina","Industria","Garaje","Otros"].index(p.get("type","Vivienda")),key="v6_type")
        p["iga"]=st.number_input("IGA / protección general (A)",6,400,int(p.get("iga",40)),step=1,key="v6_iga")
        p["location"]=st.text_input("Ubicación",p.get("location",""),key="v6_loc")
        p["designer"]=st.text_input("Proyectista",p.get("designer",""),key="v6_des")
    st.session_state.v6_project=p
    st.info("Flujo recomendado: **Proyecto → Circuitos → Dimensionado → Inspector → Unifilar → Presupuesto → Documentación**.")

def _circuit_form():
    st.subheader("Añadir circuito")
    with st.form("v6_add"):
        c1,c2,c3=st.columns(3)
        name=c1.text_input("Nombre","C-01 Tomas salón")
        kind=c2.selectbox("Uso",["Tomas","Alumbrado","Cocina","Climatización","Motor","IRVE","Otros"])
        power=c3.number_input("Potencia (kW)",0.05,500.0,2.0,0.05)
        c1,c2,c3,c4=st.columns(4)
        length=c1.number_input("Longitud (m)",0.5,1000.0,15.0,0.5)
        voltage=c2.selectbox("Tensión",[230.0,400.0])
        phases=c3.selectbox("Fases",[1,3])
        cosphi=c4.number_input("cos φ",0.1,1.0,1.0,0.01)
        b1,b2,b3,b4=st.columns(4)
        section=b1.selectbox("Sección (mm²)",[1.5,2.5,4,6,10,16,25,35,50,70,95,120],index=1)
        breaker=b2.selectbox("PIA (A)",[6,10,16,20,25,32,40,50,63,80,100],index=2)
        diff=b3.selectbox("Diferencial",["30 mA","300 mA","Sin diferencial"])
        box=b4.text_input("Caja derivación","CD-01")
        auto=b1.checkbox("Auto-dimensionar al guardar",True)
        submitted=st.form_submit_button("＋ Añadir circuito",type="primary",width="stretch")
        if submitted:
            c=new_circuit(name,kind,power,length,voltage,section,breaker,diff)
            c.update({"phases":phases,"cosphi":cosphi,"box":box})
            if auto: c=auto_dimension(c)
            st.session_state.v6_circuits.append(c)
            st.session_state.v6_selected=c["id"]
            st.toast("Circuito añadido")
            st.rerun()

def _circuits():
    circuits=st.session_state.v6_circuits
    left,right=st.columns([1.25,2.2])
    with left:
        st.subheader("Circuitos")
        if not circuits:
            st.warning("Todavía no hay circuitos.")
        for c in circuits:
            active=c["id"]==st.session_state.v6_selected
            label=("● " if active else "")+c["name"]
            if st.button(label,key="sel_"+c["id"],width="stretch"):
                st.session_state.v6_selected=c["id"]; st.rerun()
        _circuit_form()
    with right:
        if not circuits: return
        selected=next((c for c in circuits if c["id"]==st.session_state.v6_selected),circuits[0])
        st.subheader(f"Editor · {selected['name']}")
        idx=circuits.index(selected)
        with st.form("v6_edit"):
            c1,c2,c3=st.columns(3)
            selected["name"]=c1.text_input("Nombre",selected["name"],key="e_name")
            selected["kind"]=c2.selectbox("Uso",["Tomas","Alumbrado","Cocina","Climatización","Motor","IRVE","Otros"],index=["Tomas","Alumbrado","Cocina","Climatización","Motor","IRVE","Otros"].index(selected["kind"]),key="e_kind")
            selected["power_kw"]=c3.number_input("Potencia kW",0.05,500.0,float(selected["power_kw"]),0.05,key="e_power")
            c1,c2,c3,c4=st.columns(4)
            selected["length_m"]=c1.number_input("Longitud m",0.5,1000.0,float(selected["length_m"]),0.5,key="e_len")
            selected["voltage"]=c2.selectbox("Tensión",[230.0,400.0],index=0 if selected["voltage"]==230 else 1,key="e_v")
            selected["section"]=c3.selectbox("Sección mm²",[1.5,2.5,4,6,10,16,25,35,50,70,95,120],index=[1.5,2.5,4,6,10,16,25,35,50,70,95,120].index(selected["section"]) if selected["section"] in [1.5,2.5,4,6,10,16,25,35,50,70,95,120] else 1,key="e_s")
            selected["breaker"]=c4.selectbox("PIA A",[6,10,16,20,25,32,40,50,63,80,100],index=[6,10,16,20,25,32,40,50,63,80,100].index(selected["breaker"]) if selected["breaker"] in [6,10,16,20,25,32,40,50,63,80,100] else 2,key="e_b")
            c1,c2,c3=st.columns(3)
            selected["differential"]=c1.selectbox("Diferencial",["30 mA","300 mA","Sin diferencial"],index=["30 mA","300 mA","Sin diferencial"].index(selected["differential"]),key="e_d")
            selected["box"]=c2.text_input("Caja",selected.get("box","CD-01"),key="e_box")
            selected["notes"]=c3.text_input("Notas",selected.get("notes",""),key="e_notes")
            x,y,z=st.columns(3)
            save=x.form_submit_button("Guardar cambios",type="primary")
            autodim=y.form_submit_button("⚡ Auto-dimensionar")
            delete=z.form_submit_button("🗑 Eliminar")
            if save:
                st.session_state.v6_circuits[idx]=selected; st.toast("Cambios guardados"); st.rerun()
            if autodim:
                st.session_state.v6_circuits[idx]=auto_dimension(selected); st.toast("Circuito dimensionado"); st.rerun()
            if delete:
                st.session_state.v6_circuits.pop(idx); st.session_state.v6_selected=None; st.rerun()
        ib=current_from_power(selected["power_kw"],selected["voltage"],selected.get("phases",1),selected.get("cosphi",1))
        dv=voltage_drop_pct(selected["power_kw"],selected["length_m"],selected["section"],selected["voltage"],selected.get("phases",1),selected.get("cosphi",1))
        m1,m2,m3=st.columns(3); m1.metric("Ib estimada",f"{ib:.1f} A");m2.metric("Caída estimada",f"{dv:.2f}%");m3.metric("Sección",f"{selected['section']:g} mm²")
        st.caption("Cálculo preliminar. Para dimensionado profesional deben verificarse método de instalación, agrupamiento, temperatura, longitud total, conductores y tablas aplicables.")

def _overview():
    circuits=st.session_state.v6_circuits;p=st.session_state.v6_project;s=summary(circuits,p["iga"])
    st.subheader("Centro de control")
    cols=st.columns(5)
    cols[0].metric("Circuitos",s["circuits"]);cols[1].metric("Potencia",f"{s['power_kw']:.1f} kW")
    cols[2].metric("Errores",s["errors"]);cols[3].metric("Avisos",s["warnings"]);cols[4].metric("OK",s["ok"])
    st.markdown("### Estado del proyecto")
    phases,total,spread=load_balance(circuits)
    a,b=st.columns([1.5,1])
    with a:
        data=pd.DataFrame([{"Circuito":c["name"],"Uso":c["kind"],"kW":c["power_kw"],"m":c["length_m"],"Sección":c["section"],"PIA":c["breaker"],"ΔV %":round(voltage_drop_pct(c["power_kw"],c["length_m"],c["section"],c["voltage"],c.get("phases",1),c.get("cosphi",1)),2)} for c in circuits])
        st.dataframe(data,use_container_width=True,hide_index=True)
    with b:
        st.metric("Fase L1",f"{phases[1]:.1f} kW");st.metric("Fase L2",f"{phases[2]:.1f} kW");st.metric("Fase L3",f"{phases[3]:.1f} kW")
        st.caption(f"Desequilibrio simple por reparto: {spread:.1f} kW.")
    st.markdown("### Acciones rápidas")
    x,y,z=st.columns(3)
    if x.button("⚡ Dimensionar todos",width="stretch"):
        st.session_state.v6_circuits=[auto_dimension(c) for c in circuits];st.rerun()
    if y.button("🔎 Ejecutar inspector",width="stretch"):
        st.session_state.v6_jump="Inspector";st.rerun()
    if z.button("📐 Ver unifilar",width="stretch"):
        st.session_state.v6_jump="Unifilar";st.rerun()

def _inspector():
    p=st.session_state.v6_project; f=inspect(st.session_state.v6_circuits,p["iga"])
    st.subheader("Inspector REBT")
    if not f: st.info("Añade circuitos para inspeccionar.")
    for status,name,msg in f:
        icon={"error":"🔴","warning":"🟠","ok":"🟢"}[status]
        st.markdown(f"**{icon} {name}** — {msg}")
    st.caption("Las comprobaciones de esta capa son de prevalidación y no sustituyen la justificación normativa completa.")

def _unifilar():
    st.subheader("Unifilar automático")
    p=st.session_state.v6_project
    svg=unifilar_svg(p["name"],st.session_state.v6_circuits,p["iga"])
    st.components.v1.html(svg,height=max(360,220+88*len(st.session_state.v6_circuits)),scrolling=True)
    st.download_button("⬇ Descargar SVG",svg.encode("utf-8"),"unifilar.svg","image/svg+xml",width="stretch")

def _budget():
    st.subheader("Presupuesto preliminar")
    rows=budget_items(st.session_state.v6_circuits)
    if not rows: st.info("Añade circuitos para generar mediciones.");return
    df=pd.DataFrame(rows);st.dataframe(df,use_container_width=True,hide_index=True)
    total=df["Importe"].sum()
    a,b,c=st.columns(3);a.metric("Material directo",f"{total:,.2f} €");b.metric("+10% auxiliar",f"{total*1.1:,.2f} €");c.metric("+21% IVA",f"{total*1.1*1.21:,.2f} €")
    st.caption("Precios orientativos calculados automáticamente; sustituye por tarifas reales antes de presupuestar.")

def _data():
    st.subheader("Proyecto · importar / exportar")
    payload=project_payload(st.session_state.v6_project,st.session_state.v6_circuits)
    raw=json.dumps(payload,ensure_ascii=False,indent=2)
    st.download_button("⬇ Exportar proyecto JSON",raw,"proyecto-rebt-v6.json","application/json",width="stretch")
    up=st.file_uploader("Importar proyecto JSON",type=["json"])
    if up:
        try:
            data=json.load(up);st.session_state.v6_project=data["project"];st.session_state.v6_circuits=data["circuits"];st.success("Proyecto importado. Pulsa actualizar o navega por las pestañas.")
        except Exception as e: st.error(f"Archivo no válido: {e}")

def render():
    _init();_css()
    p=st.session_state.v6_project
    jump=st.session_state.pop("v6_jump",None)
    _hero(p)
    if jump: 
        tab_names=["Resumen","Proyecto","Circuitos","Inspector","Unifilar","Presupuesto","Datos"]
        tabs=st.tabs(tab_names)
        tab=tabs[tab_names.index(jump)]
        # Render all content is okay for this lightweight layer.
    else:
        tabs=st.tabs(["Resumen","Proyecto","Circuitos","Inspector","Unifilar","Presupuesto","Datos"])
    with tabs[0]: _overview()
    with tabs[1]: _project()
    with tabs[2]: _circuits()
    with tabs[3]: _inspector()
    with tabs[4]: _unifilar()
    with tabs[5]: _budget()
    with tabs[6]: _data()
