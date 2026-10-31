import React, { useState } from "react";

// ── Types ──────────────────────────────────────────────
interface LadderElement {
  type: string;
  addr?: string;
  id?: string;
  preset?: number;
  op?: string;
  in1?: string;
  in2?: string;
  out?: string;
  in?: string;
}

interface Network {
  id: string;
  elements: LadderElement[];
  output?: string;
  comment?: string;
}

interface ProjectBlock {
  name: string;
  type: "OB" | "FB" | "FC" | "DB" | "UDT";
  networks: Network[];
}

// ── Block palette ──────────────────────────────────────
const BLOCKS = [
  { name: "Contacto NO", type: "contact_no", color: "#22c55e" },
  { name: "Contacto NC", type: "contact_nc", color: "#ef4444" },
  { name: "Contacto P", type: "contact_p", color: "#f59e0b" },
  { name: "Contacto N", type: "contact_n", color: "#a78bfa" },
  { name: "Bobina", type: "coil", color: "#3b82f6" },
  { name: "Bobina Set", type: "coil_set", color: "#22c55e" },
  { name: "Bobina Reset", type: "coil_reset", color: "#ef4444" },
  { name: "Bobina Neg", type: "coil_neg", color: "#f97316" },
  { name: "TON", type: "ton", color: "#f59e0b" },
  { name: "TOF", type: "tof", color: "#f59e0b" },
  { name: "TP", type: "tp", color: "#f59e0b" },
  { name: "CTU", type: "ctu", color: "#a78bfa" },
  { name: "CTD", type: "ctd", color: "#a78bfa" },
  { name: "CTUD", type: "ctud", color: "#a78bfa" },
  { name: "Comparador", type: "cmp", color: "#06b6d4" },
  { name: "Matemática", type: "math", color: "#ec4899" },
  { name: "MOVE", type: "move", color: "#14b8a6" },
  { name: "NOT", type: "not", color: "#64748b" },
  { name: "AND", type: "and", color: "#64748b" },
  { name: "OR", type: "or", color: "#64748b" },
  { name: "XOR", type: "xor", color: "#64748b" },
];

const DEFAULT_PROJECT: ProjectBlock[] = [
  { name: "OB1", type: "OB", networks: [{ id: "N1", elements: [], output: "Q0.0", comment: "Main program cycle" }] },
];

export default function App() {
  const [cpu, setCpu] = useState("S7-1200");
  const [mode, setMode] = useState<"STOP" | "RUN" | "DEBUG">("STOP");
  const [project, setProject] = useState<ProjectBlock[]>(DEFAULT_PROJECT);
  const [activeBlock, setActiveBlock] = useState(0);
  const [activeNet, setActiveNet] = useState(0);
  const [selectedBlock, setSelectedBlock] = useState("contact_no");
  const [addr, setAddr] = useState("I0.0");
  const [memory, setMemory] = useState({ I: {}, Q: {}, M: {}, T: {}, C: {}, DB: {} });
  const [cycleCount, setCycleCount] = useState(0);
  const [hmiInputs, setHmiInputs] = useState<Record<string, boolean>>({ "I0.0": false, "I0.1": false, "I0.2": false, "Start": false, "Stop": false });
  const [hmiOutputs, setHmiOutputs] = useState<Record<string, boolean>>({ "Q0.0": false, "Q0.1": false, "Q0.2": false, "Q0.3": false });

  const activeBlockData = project[activeBlock];
  const activeNetwork = activeBlockData?.networks[activeNet];

  const addBlock = () => {
    const newProject = [...project];
    newProject[activeBlock].networks[activeNet].elements.push({ type: selectedBlock, addr });
    setProject(newProject);
  };

  const addNetwork = () => {
    const newProject = [...project];
    newProject[activeBlock].networks.push({ id: `N${newProject[activeBlock].networks.length + 1}`, elements: [], output: "Q0.0" });
    setProject(newProject);
  };

  const removeNetwork = (idx: number) => {
    const newProject = [...project];
    newProject[activeBlock].networks = newProject[activeBlock].networks.filter((_, i) => i !== idx);
    setProject(newProject);
    if (activeNet >= newProject[activeBlock].networks.length) setActiveNet(Math.max(0, newProject[activeBlock].networks.length - 1));
  };

  const addNewBlock = (type: "OB" | "FB" | "FC" | "DB") => {
    const name = `${type}${project.filter((b) => b.type === type).length + 1}`;
    setProject([...project, { name, type, networks: [{ id: "N1", elements: [], output: "Q0.0" }] }]);
  };

  const renderElement = (el: LadderElement, i: number) => {
    const colors: Record<string, string> = {
      contact_no: "#22c55e", contact_nc: "#ef4444", contact_p: "#f59e0b", contact_n: "#a78bfa",
      coil: "#3b82f6", coil_set: "#22c55e", coil_reset: "#ef4444", coil_neg: "#f97316",
      ton: "#f59e0b", tof: "#f59e0b", tp: "#f59e0b",
      ctu: "#a78bfa", ctd: "#a78bfa", ctud: "#a78bfa",
      cmp: "#06b6d4", math: "#ec4899", move: "#14b8a6",
      not: "#64748b", and: "#64748b", or: "#64748b", xor: "#64748b",
    };
    const color = colors[el.type] || "#64748b";
    const labels: Record<string, string> = {
      contact_no: el.addr || "I?", contact_nc: el.addr || "I?", contact_p: el.addr || "I?", contact_n: el.addr || "I?",
      coil: el.addr || "Q?", coil_set: `S ${el.addr}`, coil_reset: `R ${el.addr}`, coil_neg: `/${el.addr}`,
      ton: el.id || "TON", tof: el.id || "TOF", tp: el.id || "TP",
      ctu: el.id || "CTU", ctd: el.id || "CTD", ctud: el.id || "CTUD",
      cmp: el.op || "==", math: el.op || "ADD", move: "MOVE",
      not: "NOT", and: "AND", or: "OR", xor: "XOR",
    };
    const label = labels[el.type] || el.type;
    const isTimer = ["ton", "tof", "tp"].includes(el.type);
    const isCounter = ["ctu", "ctd", "ctud"].includes(el.type);
    const isCoil = ["coil", "coil_set", "coil_reset", "coil_neg"].includes(el.type);
    const isContact = ["contact_no", "contact_nc", "contact_p", "contact_n"].includes(el.type);

    let className = "block-item";
    if (isContact) className = el.type === "contact_nc" ? "contact nc" : "contact";
    else if (isCoil) className = "coil";
    else if (isTimer) className = "timer";
    else if (isCounter) className = "counter";
    else if (el.type === "cmp") className = "cmp-block";
    else if (el.type === "math") className = "math-block";
    else if (el.type === "move") className = "move-block";

    return (
      <React.Fragment key={i}>
        <div className={className} style={{ borderColor: color, color }}>{label}</div>
        <div className="wire" />
      </React.Fragment>
    );
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
        <span style={{ marginLeft: "auto", fontSize: 12, opacity: 0.6 }}>CPU: {cpu} | Modo: {mode} | Ciclos: {cycleCount}</span>
      </div>

      <div className="main-content">
        {/* Project Tree */}
        <div className="project-tree">
          <h3 style={{ fontSize: 13, marginBottom: 8, color: "#94a3b8", textTransform: "uppercase", letterSpacing: 1 }}>Árbol de proyecto</h3>
          {project.map((block, bi) => (
            <div key={bi}>
              <div className={`tree-item ${activeBlock === bi ? "selected" : ""}`} onClick={() => { setActiveBlock(bi); setActiveNet(0); }}>
                {block.type === "OB" ? "📋" : block.type === "FB" ? "🔧" : block.type === "FC" ? "⚙️" : "📦"} {block.name}
              </div>
              {activeBlock === bi && block.networks.map((net, ni) => (
                <div key={ni} className={`tree-item ${activeNet === ni ? "selected" : ""}`} style={{ paddingLeft: 24 }} onClick={() => setActiveNet(ni)}>
                  📄 Network {ni + 1}
                </div>
              ))}
            </div>
          ))}
          <div style={{ marginTop: 12, display: "flex", gap: 4, flexWrap: "wrap" }}>
            <button onClick={() => addNewBlock("OB")} style={{ padding: "4px 8px", background: "#334155", color: "#e2e8f0", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 11 }}>+ OB</button>
            <button onClick={() => addNewBlock("FB")} style={{ padding: "4px 8px", background: "#334155", color: "#e2e8f0", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 11 }}>+ FB</button>
            <button onClick={() => addNewBlock("FC")} style={{ padding: "4px 8px", background: "#334155", color: "#e2e8f0", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 11 }}>+ FC</button>
            <button onClick={() => addNewBlock("DB")} style={{ padding: "4px 8px", background: "#334155", color: "#e2e8f0", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 11 }}>+ DB</button>
          </div>

          <h3 style={{ fontSize: 13, marginTop: 16, marginBottom: 8, color: "#94a3b8", textTransform: "uppercase", letterSpacing: 1 }}>Paleta de bloques</h3>
          <div className="block-palette">
            {BLOCKS.map((b) => (
              <div key={b.type} className="block-item" onClick={() => setSelectedBlock(b.type)} style={{ borderColor: selectedBlock === b.type ? b.color : "#475569", color: selectedBlock === b.type ? b.color : "#e2e8f0" }}>
                {b.name}
              </div>
            ))}
          </div>

          <div style={{ marginTop: 8 }}>
            <input value={addr} onChange={(e) => setAddr(e.target.value)} placeholder="Dirección (I0.0, Q0.0, M0.0, T1, C1...)" style={{ width: "100%", padding: "6px", borderRadius: 4, background: "#334155", color: "#e2e8f0", border: "1px solid #475569", fontSize: 12, marginBottom: 4 }} />
            <button onClick={addBlock} style={{ width: "100%", padding: "8px", background: "#3b82f6", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 12 }}>
              + Añadir bloque
            </button>
          </div>

          <div style={{ marginTop: 8 }}>
            <input value={activeNetwork?.output || ""} onChange={(e) => {
              const newProject = [...project];
              newProject[activeBlock].networks[activeNet].output = e.target.value;
              setProject(newProject);
            }} placeholder="Salida (Q0.0, M0.0...)" style={{ width: "100%", padding: "6px", borderRadius: 4, background: "#334155", color: "#e2e8f0", border: "1px solid #475569", fontSize: 12, marginBottom: 4 }} />
          </div>

          <div style={{ marginTop: 12, display: "flex", gap: 4 }}>
            <button onClick={addNetwork} style={{ flex: 1, padding: "6px", background: "#22c55e", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 11 }}>+ Red</button>
            {activeBlockData.networks.length > 1 && (
              <button onClick={() => removeNetwork(activeNet)} style={{ flex: 1, padding: "6px", background: "#ef4444", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 11 }}>✕ Red</button>
            )}
          </div>
        </div>

        {/* Canvas */}
        <div className="canvas-area">
          <div style={{ marginBottom: 8, display: "flex", gap: 8, alignItems: "center" }}>
            <span style={{ fontWeight: "bold" }}>{activeBlockData.name} — Network {activeNet + 1}</span>
            <span style={{ fontSize: 12, color: "#94a3b8" }}>{activeNetwork?.comment || ""}</span>
          </div>

          <div style={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8, padding: 16, minHeight: 120 }}>
            {activeNetwork?.elements.length === 0 ? (
              <p style={{ color: "#64748b", textAlign: "center", marginTop: 40 }}>Red vacía. Selecciona un bloque y pulsa "+ Añadir bloque".</p>
            ) : (
              <div className="ladder-rung">
                <div className="rail" />
                {activeNetwork.elements.map((el, i) => (
                  <React.Fragment key={i}>
                    {el.type === "contact_no" && <div className="contact">{el.addr}</div>}
                    {el.type === "contact_nc" && <div className="contact nc">{el.addr}</div>}
                    {el.type === "contact_p" && <div className="contact p">{el.addr}</div>}
                    {el.type === "contact_n" && <div className="contact n">{el.addr}</div>}
                    {el.type === "coil" && <div className="coil">{el.addr}</div>}
                    {el.type === "coil_set" && <div className="coil set">S {el.addr}</div>}
                    {el.type === "coil_reset" && <div className="coil reset">R {el.addr}</div>}
                    {el.type === "coil_neg" && <div className="coil neg">/{el.addr}</div>}
                    {el.type === "ton" && <div className="timer">TON<br/>{el.id}<br/>{el.preset}ms</div>}
                    {el.type === "tof" && <div className="timer">TOF<br/>{el.id}<br/>{el.preset}ms</div>}
                    {el.type === "tp" && <div className="timer">TP<br/>{el.id}<br/>{el.preset}ms</div>}
                    {el.type === "ctu" && <div className="counter">CTU<br/>{el.id}<br/>PV:{el.preset}</div>}
                    {el.type === "ctd" && <div className="counter">CTD<br/>{el.id}<br/>PV:{el.preset}</div>}
                    {el.type === "ctud" && <div className="counter">CTUD<br/>{el.id}<br/>PV:{el.preset}</div>}
                    {el.type === "cmp" && <div className="cmp-block">CMP<br/>{el.op}</div>}
                    {el.type === "math" && <div className="math-block">MATH<br/>{el.op}</div>}
                    {el.type === "move" && <div className="move-block">MOVE</div>}
                    {el.type === "not" && <div className="block" style={{ borderColor: "#64748b", color: "#64748b" }}>NOT</div>}
                    {el.type === "and" && <div className="block" style={{ borderColor: "#64748b", color: "#64748b" }}>AND</div>}
                    {el.type === "or" && <div className="block" style={{ borderColor: "#64748b", color: "#64748b" }}>OR</div>}
                    {el.type === "xor" && <div className="block" style={{ borderColor: "#64748b", color: "#64748b" }}>XOR</div>}
                    <div className="wire" />
                  </React.Fragment>
                ))}
                {activeNetwork?.output && (
                  <>
                    <div className="wire" />
                    <div className="coil">{activeNetwork.output}</div>
                  </>
                )}
              </div>
            )}
          </div>

          <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
            <button onClick={() => {
              const newProject = [...project];
              newProject[activeBlock].networks[activeNet].elements = [];
              setProject(newProject);
            }} style={{ padding: "8px 16px", background: "#ef4444", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }}>
              Limpiar red
            </button>
            <button onClick={() => {
              const data = JSON.stringify({ cpu, project }, null, 2);
              const blob = new Blob([data], { type: "application/json" });
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url; a.download = "proyecto-tia.json"; a.click();
            }} style={{ padding: "8px 16px", background: "#22c55e", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }}>
              Guardar proyecto
            </button>
            <button onClick={() => {
              const input = document.createElement("input");
              input.type = "file"; input.accept = ".json";
              input.onchange = (e: any) => {
                const file = e.target.files[0];
                const reader = new FileReader();
                reader.onload = (ev) => {
                  try {
                    const data = JSON.parse(ev.target?.result as string);
                    if (data.project) setProject(data.project);
                    if (data.cpu) setCpu(data.cpu);
                  } catch (err) { alert("Error al cargar proyecto"); }
                };
                reader.readAsText(file);
              };
              input.click();
            }} style={{ padding: "8px 16px", background: "#3b82f6", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }}>
              Cargar proyecto
            </button>
          </div>
        </div>

        {/* HMI Panel */}
        <div className="hmi-panel">
          <h3 style={{ fontSize: 14, marginBottom: 12 }}>HMI — Entradas</h3>
          {Object.keys(hmiInputs).map((inp) => (
            <div key={inp} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
              <input type="checkbox" checked={hmiInputs[inp]} onChange={(e) => setHmiInputs({ ...hmiInputs, [inp]: e.target.checked })} />
              <label style={{ fontSize: 13 }}>{inp}</label>
            </div>
          ))}
          <button onClick={() => setHmiInputs({ ...hmiInputs, [`I0.${Object.keys(hmiInputs).length}`]: false })} style={{ width: "100%", padding: "6px", background: "#334155", color: "#e2e8f0", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 11, marginTop: 4 }}>
            + Entrada
          </button>

          <h3 style={{ fontSize: 14, marginTop: 16, marginBottom: 12 }}>HMI — Salidas</h3>
          {Object.keys(hmiOutputs).map((out) => (
            <div key={out} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
              <div style={{ width: 20, height: 20, borderRadius: "50%", background: hmiOutputs[out] ? "#22c55e" : "#334155", border: "2px solid #475569", boxShadow: hmiOutputs[out] ? "0 0 10px #22c55e" : "none" }} />
              <span style={{ fontSize: 13 }}>{out}</span>
            </div>
          ))}
          <button onClick={() => setHmiOutputs({ ...hmiOutputs, [`Q0.${Object.keys(hmiOutputs).length}`]: false })} style={{ width: "100%", padding: "6px", background: "#334155", color: "#e2e8f0", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 11, marginTop: 4 }}>
            + Salida
          </button>

          <h3 style={{ fontSize: 14, marginTop: 16, marginBottom: 8 }}>Memoria</h3>
          <div style={{ fontSize: 12, color: "#94a3b8" }}>
            <div>Ciclos: {cycleCount}</div>
            <div>Tiempo ciclo: 0 ms</div>
          </div>
        </div>
      </div>
    </div>
  );
}