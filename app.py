"""Simulador TIA Portal — KOP (Ladder) para S7-1200/1500."""
import streamlit as st
import json
import time
from plc_engine import PLCEngine

st.set_page_config(
    page_title="TIA Portal Simulator — KOP",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estado global
if "plc" not in st.session_state:
    st.session_state["plc"] = PLCEngine("S7-1200")
if "running" not in st.session_state:
    st.session_state["running"] = False

plc = st.session_state["plc"]

# ── Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚡ TIA Portal Simulator")
    cpu = st.selectbox("CPU", ["S7-1200", "S7-1500"], index=0 if plc.cpu == "S7-1200" else 1)
    if cpu != plc.cpu:
        plc.cpu = cpu
    st.markdown("---")
    mode = st.radio("Modo", ["STOP", "RUN", "DEBUG"], index=0)
    if mode == "RUN":
        st.session_state["running"] = True
    elif mode == "STOP":
        st.session_state["running"] = False
        plc.running = False
    elif mode == "DEBUG":
        st.session_state["running"] = False
        plc.debug_mode = True
    st.markdown("---")
    st.markdown("### HMI — Entradas")
    # HMI inputs
    for name in ["I0.0", "I0.1", "I0.2", "I0.3", "Start", "Stop", "Sensor1"]:
        val = st.checkbox(name, value=plc.hmi_inputs.get(name, False), key=f"hmi_{name}")
        plc.hmi_inputs[name] = val
        plc.set_var(name if not name.startswith("I") else name, val)
    st.markdown("---")
    if st.button("Reset PLC"):
        plc.reset()
        st.rerun()
    if st.button("Guardar proyecto"):
        data = plc.save_project("project")
        st.download_button("Descargar JSON", json.dumps(data, indent=2), "proyecto.json", "application/json")
    up = st.file_uploader("Cargar proyecto", type=["json"])
    if up:
        try:
            data = json.load(up)
            plc.load_project(data)
            st.success("Proyecto cargado.")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# ── Ladder SVG generator ─────────────────────────────────
def generate_ladder_svg(nets):
    width = 800
    height = 60 + 80 * len(nets) if nets else 100
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" style="background:#1e293b;border-radius:8px;">']
    parts.append(f'<text x="10" y="20" fill="#94a3b8" font-size="12">OB1 - Programa principal</text>')
    y = 50
    for i, net in enumerate(nets):
        parts.append(f'<line x1="30" y1="{y}" x2="{width-30}" y2="{y}" stroke="#475569" stroke-width="2"/>')
        parts.append(f'<text x="40" y="{y-5}" fill="#64748b" font-size="10">N{i+1}</text>')
        x = 80
        for el in net.get("elements", []):
            t = el.get("type", "")
            label = t.upper()
            if t in ("contact_no", "contact_nc", "contact_p", "contact_n"):
                label = el.get("addr", "I?")
                color = "#22c55e" if t == "contact_no" else "#ef4444"
                # contact symbol
                parts.append(f'<rect x="{x}" y="{y-12}" width="40" height="24" rx="4" fill="{color}22" stroke="{color}"/>')
                parts.append(f'<text x="{x+20}" y="{y+4}" text-anchor="middle" fill="{color}" font-size="9">{label}</text>')
                x += 50
            elif t == "coil":
                label = el.get("addr", "Q?")
                parts.append(f'<rect x="{x}" y="{y-12}" width="40" height="24" rx="4" fill="#3b82f622" stroke="#3b82f6"/>')
                parts.append(f'<text x="{x+20}" y="{y+4}" text-anchor="middle" fill="#3b82f6" font-size="9">{label}</text>')
                x += 50
            elif t in ("ton", "tof", "tp"):
                label = el.get("id", "T?")
                parts.append(f'<rect x="{x}" y="{y-12}" width="50" height="24" rx="4" fill="#f59e0b22" stroke="#f59e0b"/>')
                parts.append(f'<text x="{x+25}" y="{y+4}" text-anchor="middle" fill="#f59e0b" font-size="9">{label}</text>')
                x += 60
            elif t in ("ctu", "ctd"):
                label = el.get("id", "C?")
                parts.append(f'<rect x="{x}" y="{y-12}" width="50" height="24" rx="4" fill="#a78bfa22" stroke="#a78bfa"/>')
                parts.append(f'<text x="{x+25}" y="{y+4}" text-anchor="middle" fill="#a78bfa" font-size="9">{label}</text>')
                x += 60
            else:
                parts.append(f'<rect x="{x}" y="{y-12}" width="45" height="24" rx="4" fill="#64748b22" stroke="#64748b"/>')
                parts.append(f'<text x="{x+22}" y="{y+4}" text-anchor="middle" fill="#64748b" font-size="8">{t}</text>')
                x += 55
        # Output coil at end
        out = net.get("output")
        if out:
            parts.append(f'<line x1="{x}" y1="{y}" x2="{x+20}" y2="{y}" stroke="#3b82f6" stroke-width="2"/>')
            parts.append(f'<circle cx="{x+30}" cy="{y}" r="10" fill="#3b82f622" stroke="#3b82f6"/>')
            parts.append(f'<text x="{x+30}" y="{y+4}" text-anchor="middle" fill="#3b82f6" font-size="8">{out}</text>')
        y += 80
    parts.append("</svg>")
    return "".join(parts)
# ── Main ─────────────────────────────────────────────────
st.markdown("## 🖥️ Simulador TIA Portal — KOP (Ladder)")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📝 Editor Ladder", "📊 Memoria", "🎛️ HMI", "🔍 Debug"])

with tab1:
    st.markdown("### Redes (Networks)")
    nets = plc.get_networks("OB1")
    if not nets:
        plc.add_network("OB1")
        nets = plc.get_networks("OB1")

    # Add network button
    if st.button("➕ Añadir red"):
        plc.add_network("OB1")
        st.rerun()

    # Network selector
    net_idx = st.selectbox("Red activa", range(len(nets)), format_func=lambda i: f"Network {i+1}")

    # Element palette
    st.markdown("### Paleta de bloques")
    col_pal = st.columns(6)
    block_types = [
        ("Contacto NO", "contact_no"),
        ("Contacto NC", "contact_nc"),
        ("Bobina", "coil"),
        ("Bobina Set", "coil_set"),
        ("Bobina Reset", "coil_reset"),
        ("TON", "ton"),
        ("TOF", "tof"),
        ("TP", "tp"),
        ("CTU", "ctu"),
        ("CTD", "ctd"),
        ("Comparador", "cmp"),
        ("Matemática", "math"),
        ("MOVE", "move"),
        ("NOT", "not"),
    ]
    selected_block = st.selectbox("Bloque a añadir", [b[0] for b in block_types])
    block_type = dict(block_types)[selected_block]

    # Address input
    addr = st.text_input("Dirección (ej: I0.0, Q0.0, M0.0, T1, C1)", value="I0.0")

    if st.button("Añadir bloque a la red"):
        net = nets[net_idx]
        el = {"type": block_type}
        if block_type in ("contact_no", "contact_nc", "contact_p", "contact_n", "coil", "coil_set", "coil_reset", "coil_neg", "not"):
            el["addr"] = addr
        elif block_type in ("ton", "tof", "tp"):
            el["id"] = addr if addr.startswith("T") else f"T{len(plc.T)+1}"
            el["preset"] = 1000
            el["input"] = st.session_state.get("last_input", "I0.0")
        elif block_type in ("ctu", "ctd"):
            el["id"] = addr if addr.startswith("C") else f"C{len(plc.C)+1}"
            el["preset"] = 10
            el["input"] = st.session_state.get("last_input", "I0.0")
        elif block_type == "cmp":
            el["op"] = "=="
            el["in1"] = "I0.0"
            el["in2"] = "I0.1"
        elif block_type == "math":
            el["op"] = "ADD"
            el["in1"] = "0"
            el["in2"] = "0"
            el["out"] = "MW0"
        elif block_type == "move":
            el["in"] = "I0.0"
            el["out"] = "Q0.0"
        net["elements"].append(el)
        st.rerun()

    # Output assignment
    out_addr = st.text_input("Salida de la red (bobina) (ej: Q0.0, M0.0)", value="Q0.0")
    if st.button("Asignar salida"):
        nets[net_idx]["output"] = out_addr
        st.rerun()

    # Display networks
    st.markdown("### Redes del programa")
    for i, net in enumerate(nets):
        with st.expander(f"Network {i+1}", expanded=(i == net_idx)):
            elems = net.get("elements", [])
            if elems:
                for j, el in enumerate(elems):
                    st.code(f"{j+1}. {el.get('type','?')} {el}", language="json")
            else:
                st.caption("Red vacía")
            if net.get("output"):
                st.markdown(f"**Salida:** `{net['output']}`")
            if st.button(f"Eliminar red {i+1}", key=f"del_net_{i}"):
                plc.program["OB1"].pop(i)
                st.rerun()

    # Visualization
    st.markdown("### Visualización Ladder")
    svg = generate_ladder_svg(nets)
    st.components.v1.html(svg, height=200 + 60 * len(nets), scrolling=True)

    # Run one cycle
    if st.button("▶ Ejecutar un ciclo"):
        plc.execute_cycle()
        st.rerun()

with tab2:
    st.markdown("### Estado de memoria")
    state = plc.get_state()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Entradas (I)**")
        st.json(state["I"])
        st.markdown("**Salidas (Q)**")
        st.json(state["Q"])
        st.markdown("**Marcas (M)**")
        st.json(state["M"])
    with col2:
        st.markdown("**Temporizadores (T)**")
        st.json(state["T"])
        st.markdown("**Contadores (C)**")
        st.json(state["C"])
        st.markdown("**Bloques de datos (DB)**")
        st.json(state["DB"])
    st.metric("Ciclos ejecutados", state["cycle_count"])
    st.metric("Tiempo de ciclo (ms)", state["cycle_time_ms"])

with tab3:
    st.markdown("### HMI — Salidas")
    for name, addr in plc.hmi_outputs.items():
        val = plc.get_var(addr)
        color = "🟢" if val else "🔴"
        st.markdown(f"{color} **{name}** ({addr}): {val}")
    st.markdown("### Añadir salida HMI")
    hmi_name = st.text_input("Nombre", value="Lamp1")
    hmi_addr = st.text_input("Dirección", value="Q0.0")
    if st.button("Añadir salida HMI"):
        plc.hmi_outputs[hmi_name] = hmi_addr
        st.rerun()

with tab4:
    st.markdown("### Modo Debug (paso a paso)")
    st.info("Avanza ciclo por ciclo para ver el estado.")
    if st.button("⏭ Siguiente ciclo"):
        plc.execute_cycle()
        st.rerun()
    st.json(plc.get_state())

# ── Auto-run ─────────────────────────────────────────────
if st.session_state["running"]:
    plc.execute_cycle()
    time.sleep(0.1)
    st.rerun()

