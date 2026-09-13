"""
UI for REBT Suite v5.0.
"""
from __future__ import annotations
import json
import streamlit as st
import pandas as pd
from v5_engine import new_circuit, inspector, summary, unifilar_svg, current_from_power, voltage_drop_pct, NORMALIZED, BREAKERS

def _init():
    st.session_state.setdefault("v5_circuits", [])
    st.session_state.setdefault("v5_main_breaker", 40)
    st.session_state.setdefault("v5_project_type", "Vivienda")
    st.session_state.setdefault("v5_description", "")

def _card(title, value, caption, cls=""):
    st.markdown(f"""<div class="result-card {cls}" style="padding:1rem 1.15rem;margin-bottom:.6rem">
    <div style="font-size:.75rem;color:var(--text-secondary)">{title}</div>
    <div style="font-size:1.55rem;font-weight:800;margin:.15rem 0">{value}</div>
    <div style="font-size:.75rem;color:var(--text-secondary)">{caption}</div></div>""", unsafe_allow_html=True)

def render():
    _init()
    st.markdown("## ⚡ Diseñador de proyecto v5")
    st.caption("Flujo completo: proyecto → circuitos → inspección → unifilar. La capa v5 convive con las calculadoras existentes.")
    t1,t2,t3,t4=st.tabs(["🏠 Proyecto","🔌 Circuitos","🔎 Inspector REBT","📐 Unifilar"])
    with t1:
        c1,c2=st.columns([2,1])
        with c1:
            name=st.text_input("Nombre del proyecto", st.session_state.get("nombre_proyecto_actual","Proyecto eléctrico"), key="v5_name")
            st.session_state["nombre_proyecto_actual"]=name
            st.text_area("Descripción / notas", key="v5_description", height=110)
        with c2:
            st.selectbox("Tipo",["Vivienda","Local comercial","Industrial","Otros"],key="v5_project_type")
            st.selectbox("IGA principal (A)",BREAKERS,index=BREAKERS.index(st.session_state["v5_main_breaker"]) if st.session_state["v5_main_breaker"] in BREAKERS else 4,key="v5_iga")
            st.session_state["v5_main_breaker"]=st.session_state["v5_iga"]
        circuits=st.session_state["v5_circuits"]
        sm=summary(circuits,st.session_state["v5_main_breaker"])
        cols=st.columns(4)
        for col,(a,b,c) in zip(cols,[("Circuitos",sm["circuits"],"definidos"),("Potencia",f'{sm["power_kw"]:.1f} kW',"instalada"),("Errores",sm["errors"],"por revisar"),("Avisos",sm["warnings"],"preventivos")]):
            _card(a,b,c)
        st.info("Consejo: crea primero todos los circuitos; después usa Inspector REBT para detectar incoherencias.")
        data={"version":"5.0","project":{"name":name,"type":st.session_state["v5_project_type"],"description":st.session_state["v5_description"],"main_breaker":st.session_state["v5_main_breaker"]},"circuits":circuits}
        st.download_button("⬇️ Exportar proyecto v5 (.json)",json.dumps(data,ensure_ascii=False,indent=2),f"{name.replace(' ','_')}_v5.json","application/json",use_container_width=True)
    with t2:
        st.markdown("### Añadir circuito")
        with st.form("v5_add_circuit",clear_on_submit=True):
            a,b,c=st.columns(3)
            name=a.text_input("Nombre","C1")
            kind=b.selectbox("Uso",["Alumbrado","Tomas","Cocina","Fuerza","Motor","Otros"])
            power=c.number_input("Potencia (kW)",0.01,500.0,2.0,0.1)
            d,e,f=st.columns(3)
            length=d.number_input("Longitud (m)",0.5,1000.0,15.0,0.5)
            voltage=e.selectbox("Tensión",[230.0,400.0])
            section=f.selectbox("Sección (mm²)",NORMALIZED,index=NORMALIZED.index(2.5))
            g,h=st.columns(2)
            breaker=g.selectbox("PIA (A)",BREAKERS,index=BREAKERS.index(16))
            diff=h.selectbox("Diferencial",["30 mA","300 mA","Sin diferencial"])
            if st.form_submit_button("➕ Añadir circuito",type="primary"):
                st.session_state["v5_circuits"].append(new_circuit(name,kind,power,length,voltage,section,breaker,diff))
                st.rerun()
        circuits=st.session_state["v5_circuits"]
        if not circuits:
            st.info("No hay circuitos. Añade el primero arriba.")
        else:
            for i,c in enumerate(circuits):
                with st.container(border=True):
                    a,b,c1,d=st.columns([2.2,1.1,1.1,.6])
                    a.markdown(f"**{c['name']}** · {c['kind']}  \n{c['power_kw']:.2f} kW · {c['length_m']:.0f} m")
                    b.metric("Sección",f"{c['section']:g} mm²")
                    d.metric("PIA",f"{c['breaker']} A")
                    if d.button("🗑️",key=f"v5_del_{i}"):
                        st.session_state["v5_circuits"].pop(i); st.rerun()
            st.caption("Puedes seguir usando la Calculadora principal para obtener una sección; aquí se registra el diseño final elegido.")
    with t3:
        circuits=st.session_state["v5_circuits"]
        if not circuits: st.info("Añade circuitos para ejecutar el inspector.")
        checks=inspector(circuits,st.session_state["v5_main_breaker"])
        sm=summary(circuits,st.session_state["v5_main_breaker"])
        cols=st.columns(3); cols[0].metric("✅ Correctas",sm["ok"]); cols[1].metric("⚠️ Avisos",sm["warnings"]); cols[2].metric("❌ Errores",sm["errors"])
        for status,cname,msg in checks:
            if status=="error": st.error(f"**{cname}** — {msg}")
            elif status=="warning": st.warning(f"**{cname}** — {msg}")
            else: st.success(f"**{cname}** — {msg}")
        st.caption("Las comprobaciones v5 son orientativas y deben contrastarse con la ITC-BT y tablas aplicables al caso concreto.")
    with t4:
        circuits=st.session_state["v5_circuits"]
        if not circuits: st.info("Añade circuitos para generar el unifilar.")
        else:
            svg=unifilar_svg(st.session_state.get("nombre_proyecto_actual","Proyecto eléctrico"),circuits,st.session_state["v5_main_breaker"])
            st.markdown(svg,unsafe_allow_html=True)
            st.download_button("⬇️ Descargar unifilar SVG",svg,f"{st.session_state.get('nombre_proyecto_actual','proyecto').replace(' ','_')}_unifilar.svg","image/svg+xml",use_container_width=True)
            rows=[]
            for c in circuits:
                rows.append({"Circuito":c["name"],"Uso":c["kind"],"Potencia kW":c["power_kw"],"Longitud m":c["length_m"],"Sección mm²":c["section"],"PIA A":c["breaker"],"ΔU %":round(voltage_drop_pct(c["power_kw"],c["length_m"],c["section"],c["voltage"]),2)})
            st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
