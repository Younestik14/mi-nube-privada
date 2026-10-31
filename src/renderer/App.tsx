import React, { useState } from "react";

interface LadderElement {
  type: string;
  addr?: string;
  id?: string;
  preset?: number;
}

interface Network {
  elements: LadderElement[];
  output?: string;
}

const BLOCK_PALETTE = [
  { name: "Contacto NO", type: "contact_no" },
  { name: "Contacto NC", type: "contact_nc" },
  { name: "Bobina", type: "coil" },
  { name: "Bobina Set", type: "coil_set" },
  { name: "Bobina Reset", type: "coil_reset" },
  { name: "TON", type: "ton" },
  { name: "TOF", type: "tof" },
  { name: "TP", type: "tp" },
  { name: "CTU", type: "ctu" },
  { name: "CTD", type: "ctd" },
  { name: "Comparador", type: "cmp" },
  { name: "Matemática", type: "math" },
  { name: "MOVE", type: "move" },
  { name: "NOT", type: "not" },
];

export default function App() {
  const [cpu, setCpu] = useState("S7-1200");
  const [mode, setMode] = useState("STOP");
  const [networks, setNetworks] = useState<Network[]>([{ elements: [], output: "Q0.0" }]);
  const [activeNet, setActiveNet] = useState(0);
  const [selectedBlock, setSelectedBlock] = useState("contact_no");
  const [addr, setAddr] = useState("I0.0");
  const [memory, setMemory] = useState({ I: {}, Q: {}, M: {}, T: {}, C: {} });

  const addBlock = () => {
    const newNets = [...networks];
    newNets[activeNet].elements.push({ type: selectedBlock, addr });
    setNetworks(newNets);
  };

  const addNetwork = () => {
    setNetworks([...networks, { elements: [], output: "Q0.0" }]);
  };

  const removeNetwork = (idx: number) => {
    setNetworks(networks.filter((_, i) => i !== idx));
  };

  const setOutput = (idx: number, out: string) => {
    const newNets = [...networks];
    newNets[idx].output = out;
    setNetworks(newNets);
  };

  return (
    <div className="app">
      <div className="toolbar">
        <span style={{ fontWeight: "bold", fontSize: 16 }}>⚡ TIA Portal Simulator</span>
        <select value={cpu} onChange={(e) => setCpu(e.target.value)} style={{ padding: "4px 8px", borderRadius: 4, background: "#334155", color: "#e2e8f0", border: "none" }}>
          <option>S7-1200</option>
          <option>S7-1500</option>
        </select>
        <button className={mode === "STOP" ? "active" : ""} onClick={() => setMode("STOP")}>STOP</button>
        <button className={mode === "RUN" ? "active" : ""} onClick={() => setMode("RUN")}>RUN</button>
        <button className={mode === "DEBUG" ? "active" : ""} onClick={() => setMode("DEBUG")}>DEBUG</button>
        <span style={{ marginLeft: "auto", fontSize: 12, opacity: 0.6 }}>Modo: {mode}</span>
      </div>

      <div className="main-content">
        <div className="sidebar">
          <h3 style={{ fontSize: 14, marginBottom: 8 }}>Bloques</h3>
          <select value={selectedBlock} onChange={(e) => setSelectedBlock(e.target.value)} style={{ width: "100%", padding: "6px", borderRadius: 4, background: "#334155", color: "#e2e8f0", border: "none", marginBottom: 8 }}>
            {BLOCK_PALETTE.map((b) => (
              <option key={b.type} value={b.type}>{b.name}</option>
            ))}
          </select>
          <input
            value={addr}
            onChange={(e) => setAddr(e.target.value)}
            placeholder="Dirección (I0.0, Q0.0, M0.0...)"
            style={{ width: "100%", padding: "6px", borderRadius: 4, background: "#334155", color: "#e2e8f0", border: "1px solid #475569", marginBottom: 8 }}
          />
          <button onClick={addBlock} style={{ width: "100%", padding: "8px", background: "#3b82f6", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer", marginBottom: 12 }}>
            + Añadir bloque
          </button>

          <h3 style={{ fontSize: 14, marginBottom: 8 }}>Redes</h3>
          {networks.map((_, i) => (
            <div key={i} style={{ display: "flex", gap: 4, marginBottom: 4 }}>
              <button
                onClick={() => setActiveNet(i)}
                style={{ flex: 1, padding: "6px", background: activeNet === i ? "#3b82f6" : "#334155", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }}
              >
                Network {i + 1}
              </button>
              {networks.length > 1 && (
                <button onClick={() => removeNetwork(i)} style={{ padding: "6px 10px", background: "#ef4444", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }}>
                  ✕
                </button>
              )}
            </div>
          ))}
          <button onClick={addNetwork} style={{ width: "100%", padding: "8px", background: "#22c55e", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer", marginTop: 8 }}>
            + Nueva red
          </button>

          <h3 style={{ fontSize: 14, marginTop: 16, marginBottom: 8 }}>Salida de red</h3>
          <input
            value={networks[activeNet]?.output || ""}
            onChange={(e) => setOutput(activeNet, e.target.value)}
            placeholder="Q0.0, M0.0..."
            style={{ width: "100%", padding: "6px", borderRadius: 4, background: "#334155", color: "#e2e8f0", border: "1px solid #475569" }}
          />
        </div>

        <div className="canvas-area">
          <div style={{ padding: 16 }}>
            <h2 style={{ fontSize: 16, marginBottom: 12 }}>Editor Ladder — Network {activeNet + 1}</h2>
            <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, padding: 16, minHeight: 200 }}>
              {networks[activeNet]?.elements.length === 0 ? (
                <p style={{ color: "#64748b", textAlign: "center", marginTop: 60 }}>Red vacía. Añade bloques desde la paleta.</p>
              ) : (
                <div className="ladder-rung">
                  {networks[activeNet].elements.map((el, i) => (
                    <React.Fragment key={i}>
                      {el.type === "contact_no" && <div className="contact-no">{el.addr}</div>}
                      {el.type === "contact_nc" && <div className="contact-nc">{el.addr}</div>}
                      {el.type === "coil" && <div className="coil">{el.addr}</div>}
                      {el.type === "coil_set" && <div className="coil" style={{ borderColor: "#22c55e", color: "#22c55e" }}>S {el.addr}</div>}
                      {el.type === "coil_reset" && <div className="coil" style={{ borderColor: "#ef4444", color: "#ef4444" }}>R {el.addr}</div>}
                      {el.type === "ton" && <div className="timer-block">TON {el.id}</div>}
                      {el.type === "tof" && <div className="timer-block">TOF {el.id}</div>}
                      {el.type === "tp" && <div className="timer-block">TP {el.id}</div>}
                      {el.type === "ctu" && <div className="counter-block">CTU {el.id}</div>}
                      {el.type === "ctd" && <div className="counter-block">CTD {el.id}</div>}
                      {el.type === "cmp" && <div className="block">CMP {el.op}</div>}
                      {el.type === "math" && <div className="block">MATH {el.op}</div>}
                      {el.type === "move" && <div className="block">MOVE</div>}
                      {el.type === "not" && <div className="block">NOT</div>}
                      <span style={{ color: "#475569", margin: "0 4px" }}>—</span>
                    </React.Fragment>
                  ))}
                  {networks[activeNet].output && (
                    <div className="coil">{networks[activeNet].output}</div>
                  )}
                </div>
              )}
            </div>

            <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
              <button onClick={() => {
                const newNets = [...networks];
                newNets[activeNet].elements = [];
                setNetworks(newNets);
              }} style={{ padding: "8px 16px", background: "#ef4444", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }}>
                Limpiar red
              </button>
              <button onClick={() => {
                const data = JSON.stringify({ cpu, networks }, null, 2);
                const blob = new Blob([data], { type: "application/json" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "proyecto.json";
                a.click();
              }} style={{ padding: "8px 16px", background: "#22c55e", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }}>
                Guardar proyecto
              </button>
            </div>
          </div>
        </div>

        <div className="hmi-panel">
          <h3 style={{ fontSize: 14, marginBottom: 12 }}>HMI — Entradas</h3>
          {["I0.0", "I0.1", "I0.2", "I0.3", "Start", "Stop"].map((inp) => (
            <div key={inp} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
              <input type="checkbox" id={inp} />
              <label htmlFor={inp} style={{ fontSize: 13 }}>{inp}</label>
            </div>
          ))}

          <h3 style={{ fontSize: 14, marginTop: 16, marginBottom: 12 }}>HMI — Salidas</h3>
          {["Q0.0", "Q0.1", "Q0.2", "Q0.3"].map((out) => (
            <div key={out} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
              <div style={{ width: 16, height: 16, borderRadius: "50%", background: "#334155", border: "2px solid #475569" }} />
              <span style={{ fontSize: 13 }}>{out}</span>
            </div>
          ))}

          <h3 style={{ fontSize: 14, marginTop: 16, marginBottom: 8 }}>Memoria</h3>
          <div style={{ fontSize: 12, color: "#94a3b8" }}>
            <div>Ciclos: 0</div>
            <div>Tiempo ciclo: 0 ms</div>
          </div>
        </div>
      </div>
    </div>
  );
}