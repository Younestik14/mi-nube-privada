import React, { useState, useEffect, useRef } from "react";
import * as XLSX from "xlsx";
import {
  Zap, Sun, Cog, ClipboardList, Calculator, FileText, Download, Save,
  FolderOpen, Plus, Trash2, AlertTriangle, CheckCircle2, Home, Wrench,
  Receipt, Printer, ChevronRight, Info
} from "lucide-react";

/* =========================================================
   DATOS TÉCNICOS DE REFERENCIA
   (valores orientativos de uso didáctico habitual en FP;
   verificar siempre contra el REBT/ITC-BT vigente antes de
   emitir documentación oficial)
   ========================================================= */

const SECCIONES = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300];

// Intensidades admisibles orientativas (A) - Método B1, Cu, PVC, 2 conductores cargados
const AMPACIDAD_B1 = {
  1.5: 15, 2.5: 21, 4: 28, 6: 36, 10: 50, 16: 68, 25: 89, 35: 111,
  50: 134, 70: 171, 95: 207, 120: 239, 150: 262, 185: 296, 240: 346, 300: 388
};

const PROTECCIONES_STD = [6, 10, 13, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250];

const FACTOR_TEMP = { "30": 1.15, "40": 1.0, "45": 0.91, "50": 0.82 };
const FACTOR_AGRUPACION = { "1": 1, "2": 0.8, "3": 0.7, "4": 0.65, "6": 0.57, "9": 0.5 };

const RHO_INV = 56; // 1/ρ del cobre, mm²·m/Ω aprox, uso didáctico estándar en cálculo de cdt

const PRECIOS_DEFAULT = {
  cable_1_5: 0.55, cable_2_5: 0.78, cable_4: 1.15, cable_6: 1.65, cable_10: 2.6,
  cable_16: 4.1, cable_25: 6.8, cable_35: 9.4, cable_50: 13.2, cable_70: 18.6,
  cable_95: 24.5, cable_120: 31.0, cable_150: 38.5, cable_185: 47.0, cable_240: 62.0, cable_300: 78.0,
  magneto: 9.5, diferencial: 42.0, guardamotor: 55.0, tubo_corrugado: 1.2,
  panel_fv: 145.0, inversor: 650.0, estructura_fv: 60.0, mecanismo: 6.5, caja_derivacion: 3.2,
  cuadro_general: 85.0, mano_obra_h: 24.0
};

const uid = () => Math.random().toString(36).slice(2, 10);

/* =========================================================
   FUNCIONES DE CÁLCULO
   ========================================================= */

function ibMono(P, V, cosphi) { return P / (V * cosphi); }
function ibTri(P, V, cosphi) { return P / (Math.sqrt(3) * V * cosphi); }

function cdtMonoPct(L, I, cosphi, S, V) {
  return ((2 * L * I * cosphi) / (RHO_INV * S)) / V * 100;
}
function cdtTriPct(L, I, cosphi, S, V) {
  return ((Math.sqrt(3) * L * I * cosphi) / (RHO_INV * S)) / V * 100;
}

function elegirSeccionPorIntensidad(Ib, factorCorreccion) {
  for (const s of SECCIONES) {
    if (AMPACIDAD_B1[s] * factorCorreccion >= Ib) return s;
  }
  return SECCIONES[SECCIONES.length - 1];
}

function elegirSeccionPorCdt(L, Ib, cosphi, V, limitePct, fases) {
  for (const s of SECCIONES) {
    const cdt = fases === "tri" ? cdtTriPct(L, Ib, cosphi, s, V) : cdtMonoPct(L, Ib, cosphi, s, V);
    if (cdt <= limitePct) return s;
  }
  return SECCIONES[SECCIONES.length - 1];
}

function elegirProteccion(Ib, IzCorregida) {
  for (const In of PROTECCIONES_STD) {
    if (In >= Ib && In <= IzCorregida) return In;
  }
  return PROTECCIONES_STD.find((x) => x >= Ib) || PROTECCIONES_STD[PROTECCIONES_STD.length - 1];
}

function calcularCircuitoBT(c) {
  const fases = c.fases;
  const Ib = fases === "tri" ? ibTri(c.potencia, c.tension, c.cosphi) : ibMono(c.potencia, c.tension, c.cosphi);
  const factorTemp = FACTOR_TEMP[c.tempAmbiente] || 1;
  const factorAgrup = FACTOR_AGRUPACION[c.agrupacion] || 1;
  const factorCorreccion = factorTemp * factorAgrup;

  const seccionInt = elegirSeccionPorIntensidad(Ib, factorCorreccion);
  const seccionCdt = elegirSeccionPorCdt(c.longitud, Ib, c.cosphi, c.tension, c.limiteCdt, fases);
  const seccion = Math.max(seccionInt, seccionCdt);

  const izFinal = AMPACIDAD_B1[seccion] * factorCorreccion;
  const cdtFinal = fases === "tri"
    ? cdtTriPct(c.longitud, Ib, c.cosphi, seccion, c.tension)
    : cdtMonoPct(c.longitud, Ib, c.cosphi, seccion, c.tension);
  const proteccion = elegirProteccion(Ib, izFinal);
  const cumpleCdt = cdtFinal <= c.limiteCdt;
  const cumpleIz = izFinal >= Ib;

  return { Ib, seccion, izFinal, cdtFinal, proteccion, cumpleCdt, cumpleIz, factorCorreccion };
}

function calcularFV(fv) {
  const impp = parseFloat(fv.impp) || 0;
  const numStrings = parseInt(fv.numStrings) || 1;
  const vmpp = parseFloat(fv.vmpp) || 1;
  const idc = impp * numStrings;
  const factorCorr = 1.25; // sobredimensionado típico ramal DC (IDAE)
  const seccionDC = elegirSeccionPorIntensidad(idc * factorCorr, 1);
  const cdtDC = cdtMonoPct(parseFloat(fv.distStringInversor) || 0, idc, 1, seccionDC, vmpp);
  const requiereFusiblesDC = numStrings > 2;

  const potenciaInversor = parseFloat(fv.potenciaInversor) || 0;
  const tensionAC = parseFloat(fv.tensionAC) || 400;
  const fasesAC = fv.fasesAC || "tri";
  const iac = fasesAC === "tri" ? ibTri(potenciaInversor, tensionAC, 1) : ibMono(potenciaInversor, tensionAC, 1);
  const seccionAC = elegirSeccionPorIntensidad(iac * 1.25, 1);
  const cdtAC = fasesAC === "tri"
    ? cdtTriPct(parseFloat(fv.distInversorCuadro) || 0, iac, 1, seccionAC, tensionAC)
    : cdtMonoPct(parseFloat(fv.distInversorCuadro) || 0, iac, 1, seccionAC, tensionAC);
  const proteccionAC = elegirProteccion(iac, AMPACIDAD_B1[seccionAC]);

  return { idc, seccionDC, cdtDC, requiereFusiblesDC, iac, seccionAC, cdtAC, proteccionAC };
}

function calcularMotor(m) {
  const P = parseFloat(m.potencia) || 0;
  const V = parseFloat(m.tension) || 400;
  const cosphi = parseFloat(m.cosphi) || 0.85;
  const rend = (parseFloat(m.rendimiento) || 90) / 100;
  const In = (P * 1000) / (Math.sqrt(3) * V * cosphi * rend);
  const factorArranque = m.tipoArranque === "estrella-triangulo" ? 2.5 : 7;
  const Ia = In * factorArranque;
  const seccion = elegirSeccionPorIntensidad(In * 1.25, 1);
  const protTermica = { min: (In * 0.9).toFixed(1), max: (In * 1.15).toFixed(1) };
  const guardamotor = elegirProteccion(In, AMPACIDAD_B1[seccion]);
  return { In, Ia, seccion, protTermica, guardamotor };
}

const fmt = (n, d = 2) => (isFinite(n) ? n.toFixed(d) : "—");

/* =========================================================
   ESTADO INICIAL
   ========================================================= */

const ESTADO_INICIAL = {
  proyecto: {
    nombre: "", cliente: "", ubicacion: "", tecnico: "", fecha: new Date().toISOString().slice(0, 10),
    tipos: { bt: true, fv: false, industrial: false }
  },
  circuitosBT: [],
  fv: {
    potenciaPico: "", numPaneles: "", potenciaPanel: "", voc: "", isc: "", vmpp: "", impp: "",
    numStrings: "1", distStringInversor: "15", potenciaInversor: "", tensionAC: "400", fasesAC: "tri",
    distInversorCuadro: "5"
  },
  motores: [],
  medicionesManual: [],
  precios: PRECIOS_DEFAULT,
  gastosGenerales: 13, beneficioIndustrial: 6, iva: 21,
  memoria: {
    objeto: "", titular: "", emplazamiento: "", descripcion: "", normativa: "",
  }
};

/* =========================================================
   COMPONENTES DE UI BASE
   ========================================================= */

function Campo({ label, children, hint }) {
  return (
    <label className="campo">
      <span className="campo-label">{label}</span>
      {children}
      {hint && <span className="campo-hint">{hint}</span>}
    </label>
  );
}

function Input(props) {
  return <input {...props} className={"input-tech " + (props.className || "")} />;
}

function Select({ children, ...props }) {
  return <select {...props} className={"input-tech " + (props.className || "")}>{children}</select>;
}

function Panel({ title, eyebrow, icon, children, right }) {
  return (
    <div className="panel">
      <div className="panel-head">
        <div>
          {eyebrow && <div className="panel-eyebrow">{eyebrow}</div>}
          <h3 className="panel-title">{icon}{title}</h3>
        </div>
        {right}
      </div>
      <div className="panel-body">{children}</div>
    </div>
  );
}

function Badge({ ok, children }) {
  return (
    <span className={"badge " + (ok ? "badge-ok" : "badge-bad")}>
      {ok ? <CheckCircle2 size={13} /> : <AlertTriangle size={13} />}
      {children}
    </span>
  );
}

/* =========================================================
   TAB: PROYECTO
   ========================================================= */

function TabProyecto({ proyecto, setProyecto }) {
  const upd = (k, v) => setProyecto({ ...proyecto, [k]: v });
  const updTipo = (k, v) => setProyecto({ ...proyecto, tipos: { ...proyecto.tipos, [k]: v } });
  return (
    <Panel title="Datos generales del proyecto" eyebrow="00 · Ficha" icon={<ClipboardList size={18} />}>
      <div className="grid-2">
        <Campo label="Nombre del proyecto">
          <Input value={proyecto.nombre} onChange={(e) => upd("nombre", e.target.value)} placeholder="Instalación eléctrica vivienda unifamiliar" />
        </Campo>
        <Campo label="Cliente / Titular">
          <Input value={proyecto.cliente} onChange={(e) => upd("cliente", e.target.value)} placeholder="Nombre y apellidos / razón social" />
        </Campo>
        <Campo label="Emplazamiento">
          <Input value={proyecto.ubicacion} onChange={(e) => upd("ubicacion", e.target.value)} placeholder="Dirección, municipio, provincia" />
        </Campo>
        <Campo label="Técnico redactor">
          <Input value={proyecto.tecnico} onChange={(e) => upd("tecnico", e.target.value)} placeholder="Tu nombre" />
        </Campo>
        <Campo label="Fecha">
          <Input type="date" value={proyecto.fecha} onChange={(e) => upd("fecha", e.target.value)} />
        </Campo>
      </div>

      <div className="campo-label" style={{ marginTop: 18, marginBottom: 8 }}>Módulos de cálculo incluidos en este proyecto</div>
      <div className="tipos-grid">
        <label className="tipo-check">
          <input type="checkbox" checked={proyecto.tipos.bt} onChange={(e) => updTipo("bt", e.target.checked)} />
          <Home size={16} /> Baja tensión (REBT)
        </label>
        <label className="tipo-check">
          <input type="checkbox" checked={proyecto.tipos.fv} onChange={(e) => updTipo("fv", e.target.checked)} />
          <Sun size={16} /> Fotovoltaica autoconsumo
        </label>
        <label className="tipo-check">
          <input type="checkbox" checked={proyecto.tipos.industrial} onChange={(e) => updTipo("industrial", e.target.checked)} />
          <Cog size={16} /> Industrial / motores
        </label>
      </div>

      <div className="nota-normativa" style={{ marginTop: 18 }}>
        <Info size={14} />
        Herramienta de apoyo al predimensionado según REBT (RD 842/2002 e ITC-BT) y RD 244/2019 (autoconsumo).
        Los valores de intensidades admisibles y factores de corrección son orientativos (método de referencia B1).
        Verifica siempre la sección, protecciones y caída de tensión definitivas contra las tablas oficiales vigentes
        y el criterio de tu tutor/a en IDEA TSG antes de emitir documentación formal.
      </div>
    </Panel>
  );
}

/* =========================================================
   TAB: BAJA TENSIÓN
   ========================================================= */

function nuevoCircuitoBT() {
  return {
    id: uid(), nombre: "", tipoReceptor: "alumbrado", fases: "mono", tension: 230,
    potencia: "", cosphi: 0.95, longitud: "", tempAmbiente: "40", agrupacion: "1", limiteCdt: 3
  };
}

function TabBT({ circuitos, setCircuitos }) {
  const add = () => setCircuitos([...circuitos, nuevoCircuitoBT()]);
  const remove = (id) => setCircuitos(circuitos.filter((c) => c.id !== id));
  const upd = (id, k, v) => setCircuitos(circuitos.map((c) => (c.id === id ? { ...c, [k]: v, limiteCdt: k === "tipoReceptor" ? (v === "alumbrado" ? 3 : 5) : c.limiteCdt } : c)));

  return (
    <Panel
      title="Circuitos de baja tensión"
      eyebrow="01 · REBT ITC-BT-19 / ITC-BT-25"
      icon={<Home size={18} />}
      right={<button className="btn-primary" onClick={add}><Plus size={15} /> Añadir circuito</button>}
    >
      {circuitos.length === 0 && <p className="vacio">Todavía no hay circuitos. Añade el primero (por ejemplo, "Alumbrado salón").</p>}
      <div className="lista-circuitos">
        {circuitos.map((c) => {
          const r = calcularCircuitoBT({
            ...c,
            potencia: parseFloat(c.potencia) || 0,
            longitud: parseFloat(c.longitud) || 0,
            cosphi: parseFloat(c.cosphi) || 0.95,
            tension: parseFloat(c.tension) || 230,
            limiteCdt: parseFloat(c.limiteCdt) || 3
          });
          return (
            <div className="tarjeta-circuito" key={c.id}>
              <div className="tarjeta-head">
                <Input className="input-nombre" value={c.nombre} onChange={(e) => upd(c.id, "nombre", e.target.value)} placeholder="Nombre del circuito (C1 Alumbrado, C5 Cocina...)" />
                <button className="btn-icon" onClick={() => remove(c.id)}><Trash2 size={15} /></button>
              </div>
              <div className="grid-4">
                <Campo label="Tipo de receptor">
                  <Select value={c.tipoReceptor} onChange={(e) => upd(c.id, "tipoReceptor", e.target.value)}>
                    <option value="alumbrado">Alumbrado</option>
                    <option value="fuerza">Fuerza / tomas</option>
                    <option value="climatizacion">Climatización</option>
                    <option value="mixto">Mixto</option>
                  </Select>
                </Campo>
                <Campo label="Fases">
                  <Select value={c.fases} onChange={(e) => upd(c.id, "fases", e.target.value)}>
                    <option value="mono">Monofásico</option>
                    <option value="tri">Trifásico</option>
                  </Select>
                </Campo>
                <Campo label="Tensión (V)">
                  <Input type="number" value={c.tension} onChange={(e) => upd(c.id, "tension", e.target.value)} />
                </Campo>
                <Campo label="Potencia (W)">
                  <Input type="number" value={c.potencia} onChange={(e) => upd(c.id, "potencia", e.target.value)} />
                </Campo>
                <Campo label="cos φ">
                  <Input type="number" step="0.01" value={c.cosphi} onChange={(e) => upd(c.id, "cosphi", e.target.value)} />
                </Campo>
                <Campo label="Longitud (m)">
                  <Input type="number" value={c.longitud} onChange={(e) => upd(c.id, "longitud", e.target.value)} />
                </Campo>
                <Campo label="Temp. ambiente (°C)">
                  <Select value={c.tempAmbiente} onChange={(e) => upd(c.id, "tempAmbiente", e.target.value)}>
                    <option value="30">30°C</option><option value="40">40°C</option>
                    <option value="45">45°C</option><option value="50">50°C</option>
                  </Select>
                </Campo>
                <Campo label="Circuitos agrupados">
                  <Select value={c.agrupacion} onChange={(e) => upd(c.id, "agrupacion", e.target.value)}>
                    <option value="1">1</option><option value="2">2</option><option value="3">3</option>
                    <option value="4">4-5</option><option value="6">6-8</option><option value="9">9+</option>
                  </Select>
                </Campo>
              </div>

              <div className="resultado-bar">
                <div className="resultado-item"><span>Ib</span><b>{fmt(r.Ib)} A</b></div>
                <div className="resultado-item"><span>Sección</span><b>{r.seccion} mm²</b></div>
                <div className="resultado-item"><span>Iz corregida</span><b>{fmt(r.izFinal)} A</b></div>
                <div className="resultado-item"><span>c.d.t.</span><b>{fmt(r.cdtFinal)}%</b></div>
                <div className="resultado-item"><span>Protección</span><b>{r.proteccion} A</b></div>
                <Badge ok={r.cumpleCdt && r.cumpleIz}>{r.cumpleCdt && r.cumpleIz ? "Cumple" : "Revisar"}</Badge>
              </div>
            </div>
          );
        })}
      </div>
    </Panel>
  );
}

/* =========================================================
   TAB: FOTOVOLTAICA
   ========================================================= */

function TabFV({ fv, setFv }) {
  const upd = (k, v) => setFv({ ...fv, [k]: v });
  const r = calcularFV(fv);
  return (
    <Panel title="Instalación fotovoltaica de autoconsumo" eyebrow="02 · RD 244/2019" icon={<Sun size={18} />}>
      <div className="grid-4">
        <Campo label="Potencia pico (kWp)"><Input type="number" value={fv.potenciaPico} onChange={(e) => upd("potenciaPico", e.target.value)} /></Campo>
        <Campo label="Nº paneles"><Input type="number" value={fv.numPaneles} onChange={(e) => upd("numPaneles", e.target.value)} /></Campo>
        <Campo label="Potencia por panel (Wp)"><Input type="number" value={fv.potenciaPanel} onChange={(e) => upd("potenciaPanel", e.target.value)} /></Campo>
        <Campo label="Nº strings en paralelo"><Input type="number" value={fv.numStrings} onChange={(e) => upd("numStrings", e.target.value)} /></Campo>
        <Campo label="Voc (V)"><Input type="number" value={fv.voc} onChange={(e) => upd("voc", e.target.value)} /></Campo>
        <Campo label="Isc (A)"><Input type="number" value={fv.isc} onChange={(e) => upd("isc", e.target.value)} /></Campo>
        <Campo label="Vmpp (V)"><Input type="number" value={fv.vmpp} onChange={(e) => upd("vmpp", e.target.value)} /></Campo>
        <Campo label="Impp (A)"><Input type="number" value={fv.impp} onChange={(e) => upd("impp", e.target.value)} /></Campo>
        <Campo label="Distancia strings → inversor (m)"><Input type="number" value={fv.distStringInversor} onChange={(e) => upd("distStringInversor", e.target.value)} /></Campo>
        <Campo label="Potencia inversor (W)"><Input type="number" value={fv.potenciaInversor} onChange={(e) => upd("potenciaInversor", e.target.value)} /></Campo>
        <Campo label="Tensión AC (V)"><Input type="number" value={fv.tensionAC} onChange={(e) => upd("tensionAC", e.target.value)} /></Campo>
        <Campo label="Fases AC">
          <Select value={fv.fasesAC} onChange={(e) => upd("fasesAC", e.target.value)}>
            <option value="mono">Monofásico</option><option value="tri">Trifásico</option>
          </Select>
        </Campo>
        <Campo label="Distancia inversor → cuadro AC (m)"><Input type="number" value={fv.distInversorCuadro} onChange={(e) => upd("distInversorCuadro", e.target.value)} /></Campo>
      </div>

      <div className="subtitulo-tabla">Tramo CC (paneles → inversor)</div>
      <div className="resultado-bar">
        <div className="resultado-item"><span>I string acumulada</span><b>{fmt(r.idc)} A</b></div>
        <div className="resultado-item"><span>Sección CC</span><b>{r.seccionDC} mm²</b></div>
        <div className="resultado-item"><span>c.d.t. CC</span><b>{fmt(r.cdtDC)}%</b></div>
        <Badge ok={r.cdtDC <= 1.5}>{r.cdtDC <= 1.5 ? "≤1.5% recomendado" : "Revisar sección"}</Badge>
        {r.requiereFusiblesDC && <Badge ok={false}>Requiere fusibles por string ({">"}2 en paralelo)</Badge>}
      </div>

      <div className="subtitulo-tabla">Tramo CA (inversor → cuadro AC)</div>
      <div className="resultado-bar">
        <div className="resultado-item"><span>I AC</span><b>{fmt(r.iac)} A</b></div>
        <div className="resultado-item"><span>Sección AC</span><b>{r.seccionAC} mm²</b></div>
        <div className="resultado-item"><span>c.d.t. AC</span><b>{fmt(r.cdtAC)}%</b></div>
        <div className="resultado-item"><span>Protección AC</span><b>{r.proteccionAC} A</b></div>
        <Badge ok={r.cdtAC <= 1.5}>{r.cdtAC <= 1.5 ? "≤1.5% recomendado" : "Revisar sección"}</Badge>
      </div>

      <div className="nota-normativa">
        <Info size={14} />
        Recuerda: interruptor-seccionador DC junto al inversor, protección contra sobretensiones, diferencial
        superinmunizado (tipo B si el inversor lo requiere) y equipo de medida bidireccional. Cálculo orientativo;
        contrasta con la ficha técnica del inversor y el pliego IDAE.
      </div>
    </Panel>
  );
}

/* =========================================================
   TAB: INDUSTRIAL / MOTORES
   ========================================================= */

function nuevoMotor() {
  return { id: uid(), nombre: "", potencia: "", tension: 400, cosphi: 0.85, rendimiento: 90, tipoArranque: "directo" };
}

function TabIndustrial({ motores, setMotores }) {
  const add = () => setMotores([...motores, nuevoMotor()]);
  const remove = (id) => setMotores(motores.filter((m) => m.id !== id));
  const upd = (id, k, v) => setMotores(motores.map((m) => (m.id === id ? { ...m, [k]: v } : m)));

  return (
    <Panel
      title="Motores y circuitos industriales"
      eyebrow="03 · ITC-BT-47"
      icon={<Cog size={18} />}
      right={<button className="btn-primary" onClick={add}><Plus size={15} /> Añadir motor</button>}
    >
      {motores.length === 0 && <p className="vacio">Añade un motor para calcular In, Ia, sección y protecciones.</p>}
      <div className="lista-circuitos">
        {motores.map((m) => {
          const r = calcularMotor(m);
          return (
            <div className="tarjeta-circuito" key={m.id}>
              <div className="tarjeta-head">
                <Input className="input-nombre" value={m.nombre} onChange={(e) => upd(m.id, "nombre", e.target.value)} placeholder="Motor bomba, cinta transportadora..." />
                <button className="btn-icon" onClick={() => remove(m.id)}><Trash2 size={15} /></button>
              </div>
              <div className="grid-4">
                <Campo label="Potencia (kW)"><Input type="number" value={m.potencia} onChange={(e) => upd(m.id, "potencia", e.target.value)} /></Campo>
                <Campo label="Tensión (V)"><Input type="number" value={m.tension} onChange={(e) => upd(m.id, "tension", e.target.value)} /></Campo>
                <Campo label="cos φ"><Input type="number" step="0.01" value={m.cosphi} onChange={(e) => upd(m.id, "cosphi", e.target.value)} /></Campo>
                <Campo label="Rendimiento (%)"><Input type="number" value={m.rendimiento} onChange={(e) => upd(m.id, "rendimiento", e.target.value)} /></Campo>
                <Campo label="Tipo de arranque">
                  <Select value={m.tipoArranque} onChange={(e) => upd(m.id, "tipoArranque", e.target.value)}>
                    <option value="directo">Directo</option>
                    <option value="estrella-triangulo">Estrella-triángulo</option>
                  </Select>
                </Campo>
              </div>
              <div className="resultado-bar">
                <div className="resultado-item"><span>In</span><b>{fmt(r.In)} A</b></div>
                <div className="resultado-item"><span>Ia arranque</span><b>{fmt(r.Ia)} A</b></div>
                <div className="resultado-item"><span>Sección (1.25×In)</span><b>{r.seccion} mm²</b></div>
                <div className="resultado-item"><span>Térmico</span><b>{r.protTermica.min}–{r.protTermica.max} A</b></div>
                <div className="resultado-item"><span>Guardamotor</span><b>{r.guardamotor} A</b></div>
              </div>
            </div>
          );
        })}
      </div>
    </Panel>
  );
}

/* =========================================================
   MEDICIONES (derivadas + manuales)
   ========================================================= */

function generarMedicionesAuto(circuitosBT, fv, motores, proyecto) {
  const items = [];
  if (proyecto.tipos.bt) {
    circuitosBT.forEach((c) => {
      const r = calcularCircuitoBT({ ...c, potencia: parseFloat(c.potencia) || 0, longitud: parseFloat(c.longitud) || 0, cosphi: parseFloat(c.cosphi) || 0.95, tension: parseFloat(c.tension) || 230, limiteCdt: parseFloat(c.limiteCdt) || 3 });
      items.push({ id: uid(), auto: true, capitulo: "Baja tensión", descripcion: `Cable ${r.seccion} mm² · ${c.nombre || "circuito"}`, unidad: "m", cantidad: parseFloat(c.longitud) || 0, precioKey: `cable_${String(r.seccion).replace(".", "_")}` });
      items.push({ id: uid(), auto: true, capitulo: "Baja tensión", descripcion: `Interruptor magnetotérmico ${r.proteccion} A · ${c.nombre || "circuito"}`, unidad: "ud", cantidad: 1, precioKey: "magneto" });
    });
    if (circuitosBT.length > 0) {
      items.push({ id: uid(), auto: true, capitulo: "Baja tensión", descripcion: "Interruptor diferencial 30 mA", unidad: "ud", cantidad: Math.max(1, Math.ceil(circuitosBT.length / 5)), precioKey: "diferencial" });
      items.push({ id: uid(), auto: true, capitulo: "Baja tensión", descripcion: "Cuadro general de mando y protección", unidad: "ud", cantidad: 1, precioKey: "cuadro_general" });
    }
  }
  if (proyecto.tipos.fv && (parseFloat(fv.numPaneles) || 0) > 0) {
    const r = calcularFV(fv);
    items.push({ id: uid(), auto: true, capitulo: "Fotovoltaica", descripcion: "Módulo fotovoltaico", unidad: "ud", cantidad: parseFloat(fv.numPaneles) || 0, precioKey: "panel_fv" });
    items.push({ id: uid(), auto: true, capitulo: "Fotovoltaica", descripcion: "Inversor", unidad: "ud", cantidad: 1, precioKey: "inversor" });
    items.push({ id: uid(), auto: true, capitulo: "Fotovoltaica", descripcion: "Estructura soporte", unidad: "ud", cantidad: parseFloat(fv.numPaneles) || 0, precioKey: "estructura_fv" });
    items.push({ id: uid(), auto: true, capitulo: "Fotovoltaica", descripcion: `Cable CC ${r.seccionDC} mm²`, unidad: "m", cantidad: (parseFloat(fv.distStringInversor) || 0) * 2, precioKey: `cable_${String(r.seccionDC).replace(".", "_")}` });
    items.push({ id: uid(), auto: true, capitulo: "Fotovoltaica", descripcion: `Cable CA ${r.seccionAC} mm²`, unidad: "m", cantidad: (parseFloat(fv.distInversorCuadro) || 0) * 2, precioKey: `cable_${String(r.seccionAC).replace(".", "_")}` });
  }
  if (proyecto.tipos.industrial) {
    motores.forEach((m) => {
      const r = calcularMotor(m);
      items.push({ id: uid(), auto: true, capitulo: "Industrial", descripcion: `Cable ${r.seccion} mm² · motor ${m.nombre || ""}`, unidad: "m", cantidad: 10, precioKey: `cable_${String(r.seccion).replace(".", "_")}` });
      items.push({ id: uid(), auto: true, capitulo: "Industrial", descripcion: `Guardamotor ${r.guardamotor} A · ${m.nombre || ""}`, unidad: "ud", cantidad: 1, precioKey: "guardamotor" });
    });
  }
  return items;
}

function TabMediciones({ circuitosBT, fv, motores, proyecto, medicionesManual, setMedicionesManual, precios }) {
  const auto = generarMedicionesAuto(circuitosBT, fv, motores, proyecto);
  const todas = [...auto, ...medicionesManual];

  const addManual = () => setMedicionesManual([...medicionesManual, { id: uid(), auto: false, capitulo: "Otros", descripcion: "", unidad: "ud", cantidad: 1, precioKey: null, precioManual: 0 }]);
  const removeManual = (id) => setMedicionesManual(medicionesManual.filter((i) => i.id !== id));
  const updManual = (id, k, v) => setMedicionesManual(medicionesManual.map((i) => (i.id === id ? { ...i, [k]: v } : i)));

  const porCapitulo = {};
  todas.forEach((it) => { (porCapitulo[it.capitulo] = porCapitulo[it.capitulo] || []).push(it); });

  return (
    <Panel
      title="Mediciones"
      eyebrow="04 · Generadas desde los cálculos"
      icon={<ClipboardList size={18} />}
      right={<button className="btn-primary" onClick={addManual}><Plus size={15} /> Partida manual</button>}
    >
      {Object.keys(porCapitulo).length === 0 && <p className="vacio">Añade circuitos en las pestañas de cálculo para generar mediciones automáticamente.</p>}
      {Object.entries(porCapitulo).map(([cap, items]) => (
        <div key={cap} className="capitulo-bloque">
          <div className="capitulo-titulo">{cap}</div>
          <table className="tabla-tech">
            <thead><tr><th>Descripción</th><th>Ud.</th><th>Cantidad</th><th></th></tr></thead>
            <tbody>
              {items.map((it) => (
                <tr key={it.id}>
                  <td>
                    {it.auto ? it.descripcion : (
                      <Input value={it.descripcion} onChange={(e) => updManual(it.id, "descripcion", e.target.value)} placeholder="Descripción de la partida" />
                    )}
                  </td>
                  <td>{it.auto ? it.unidad : <Input value={it.unidad} onChange={(e) => updManual(it.id, "unidad", e.target.value)} style={{ width: 60 }} />}</td>
                  <td>{it.auto ? fmt(it.cantidad, 1) : <Input type="number" value={it.cantidad} onChange={(e) => updManual(it.id, "cantidad", e.target.value)} style={{ width: 80 }} />}</td>
                  <td>{!it.auto && <button className="btn-icon" onClick={() => removeManual(it.id)}><Trash2 size={14} /></button>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </Panel>
  );
}

/* =========================================================
   PRESUPUESTO
   ========================================================= */

function calcularPresupuesto(circuitosBT, fv, motores, proyecto, medicionesManual, precios, gastosGenerales, beneficioIndustrial, iva) {
  const auto = generarMedicionesAuto(circuitosBT, fv, motores, proyecto);
  const todas = [...auto, ...medicionesManual];
  const filas = todas.map((it) => {
    const precioUnit = it.auto ? (precios[it.precioKey] ?? 0) : (parseFloat(it.precioManual) || 0);
    const cantidad = parseFloat(it.cantidad) || 0;
    return { ...it, precioUnit, importe: precioUnit * cantidad };
  });
  const porCapitulo = {};
  filas.forEach((f) => { porCapitulo[f.capitulo] = (porCapitulo[f.capitulo] || 0) + f.importe; });
  const pem = filas.reduce((a, f) => a + f.importe, 0);
  const gg = pem * (gastosGenerales / 100);
  const bi = pem * (beneficioIndustrial / 100);
  const pca = pem + gg + bi;
  const ivaImporte = pca * (iva / 100);
  const total = pca + ivaImporte;
  return { filas, porCapitulo, pem, gg, bi, pca, ivaImporte, total };
}

function TabPresupuesto({ circuitosBT, fv, motores, proyecto, medicionesManual, precios, setPrecios, gastosGenerales, setGastosGenerales, beneficioIndustrial, setBeneficioIndustrial, iva, setIva }) {
  const p = calcularPresupuesto(circuitosBT, fv, motores, proyecto, medicionesManual, precios, gastosGenerales, beneficioIndustrial, iva);
  const claves = Object.keys(precios);

  return (
    <Panel title="Presupuesto" eyebrow="05 · PEM + GG + BI + IVA" icon={<Receipt size={18} />}>
      {Object.entries(p.porCapitulo).map(([cap, importe]) => (
        <div key={cap} className="linea-presupuesto">
          <span>{cap}</span><b>{fmt(importe)} €</b>
        </div>
      ))}
      <div className="separador" />
      <div className="linea-presupuesto"><span>Presupuesto de Ejecución Material (PEM)</span><b>{fmt(p.pem)} €</b></div>
      <div className="linea-presupuesto sub">
        <span>Gastos generales</span>
        <span className="pct-input"><Input type="number" value={gastosGenerales} onChange={(e) => setGastosGenerales(parseFloat(e.target.value) || 0)} style={{ width: 56 }} />%</span>
        <b>{fmt(p.gg)} €</b>
      </div>
      <div className="linea-presupuesto sub">
        <span>Beneficio industrial</span>
        <span className="pct-input"><Input type="number" value={beneficioIndustrial} onChange={(e) => setBeneficioIndustrial(parseFloat(e.target.value) || 0)} style={{ width: 56 }} />%</span>
        <b>{fmt(p.bi)} €</b>
      </div>
      <div className="linea-presupuesto"><span>Presupuesto de Contrata (sin IVA)</span><b>{fmt(p.pca)} €</b></div>
      <div className="linea-presupuesto sub">
        <span>IVA</span>
        <span className="pct-input"><Input type="number" value={iva} onChange={(e) => setIva(parseFloat(e.target.value) || 0)} style={{ width: 56 }} />%</span>
        <b>{fmt(p.ivaImporte)} €</b>
      </div>
      <div className="linea-presupuesto total"><span>TOTAL PRESUPUESTO</span><b>{fmt(p.total)} €</b></div>

      <details className="detalle-precios">
        <summary>Editar precios unitarios ({claves.length})</summary>
        <div className="grid-precios">
          {claves.map((k) => (
            <label key={k} className="precio-item">
              <span>{k.replace(/_/g, " ")}</span>
              <Input type="number" step="0.01" value={precios[k]} onChange={(e) => setPrecios({ ...precios, [k]: parseFloat(e.target.value) || 0 })} />
            </label>
          ))}
        </div>
      </details>
      <div className="nota-normativa">
        <Info size={14} />
        Precios orientativos de mercado — ajústalos según tu proveedor habitual o el cuadro de precios de IDEA TSG.
      </div>
    </Panel>
  );
}

/* =========================================================
   MEMORIA
   ========================================================= */

function generarMemoriaTexto(proyecto, circuitosBT, fv, motores, memoria) {
  const partes = [];
  partes.push(`MEMORIA TÉCNICA DESCRIPTIVA\n\n1. OBJETO\n${memoria.objeto || `El objeto de la presente memoria es describir y justificar la instalación eléctrica de "${proyecto.nombre || "[nombre del proyecto]"}", conforme al Reglamento Electrotécnico para Baja Tensión (RD 842/2002) y sus Instrucciones Técnicas Complementarias.`}`);
  partes.push(`2. TITULAR\n${memoria.titular || proyecto.cliente || "[titular]"}`);
  partes.push(`3. EMPLAZAMIENTO\n${memoria.emplazamiento || proyecto.ubicacion || "[emplazamiento]"}`);
  partes.push(`4. DESCRIPCIÓN DE LA INSTALACIÓN\n${memoria.descripcion || "Se describe a continuación cada uno de los subsistemas incluidos en el proyecto."}`);

  if (proyecto.tipos.bt && circuitosBT.length > 0) {
    let seccionBT = "4.1. Instalación de baja tensión\nCuadro de circuitos calculados:\n";
    circuitosBT.forEach((c, i) => {
      const r = calcularCircuitoBT({ ...c, potencia: parseFloat(c.potencia) || 0, longitud: parseFloat(c.longitud) || 0, cosphi: parseFloat(c.cosphi) || 0.95, tension: parseFloat(c.tension) || 230, limiteCdt: parseFloat(c.limiteCdt) || 3 });
      seccionBT += `  C${i + 1} ${c.nombre || "circuito"}: ${c.potencia} W, ${r.seccion} mm², Ib=${fmt(r.Ib)} A, c.d.t.=${fmt(r.cdtFinal)}%, protección ${r.proteccion} A.\n`;
    });
    partes.push(seccionBT);
  }
  if (proyecto.tipos.fv && parseFloat(fv.numPaneles) > 0) {
    const r = calcularFV(fv);
    partes.push(`4.2. Instalación fotovoltaica de autoconsumo\nPotencia pico: ${fv.potenciaPico} kWp (${fv.numPaneles} módulos de ${fv.potenciaPanel} Wp). Tramo CC: sección ${r.seccionDC} mm², c.d.t. ${fmt(r.cdtDC)}%. Tramo CA: sección ${r.seccionAC} mm², protección ${r.proteccionAC} A, c.d.t. ${fmt(r.cdtAC)}%.`);
  }
  if (proyecto.tipos.industrial && motores.length > 0) {
    let seccionInd = "4.3. Instalación industrial / motores\n";
    motores.forEach((m) => {
      const r = calcularMotor(m);
      seccionInd += `  ${m.nombre || "Motor"}: ${m.potencia} kW, In=${fmt(r.In)} A, Ia=${fmt(r.Ia)} A, sección ${r.seccion} mm², guardamotor ${r.guardamotor} A.\n`;
    });
    partes.push(seccionInd);
  }

  partes.push(`5. NORMATIVA APLICABLE\n${memoria.normativa || "Reglamento Electrotécnico para Baja Tensión (RD 842/2002) e ITC-BT correspondientes. RD 244/2019 (autoconsumo), en su caso. Normativa municipal y de la compañía distribuidora."}`);
  return partes.join("\n\n");
}

function TabMemoria({ proyecto, circuitosBT, fv, motores, memoria, setMemoria }) {
  const upd = (k, v) => setMemoria({ ...memoria, [k]: v });
  const texto = generarMemoriaTexto(proyecto, circuitosBT, fv, motores, memoria);
  return (
    <Panel title="Memoria técnica y anexos" eyebrow="06 · Generada a partir de los cálculos" icon={<FileText size={18} />}>
      <div className="grid-2">
        <Campo label="Objeto (déjalo vacío para usar el texto por defecto)">
          <textarea className="textarea-tech" rows={2} value={memoria.objeto} onChange={(e) => upd("objeto", e.target.value)} />
        </Campo>
        <Campo label="Normativa (opcional, sobreescribe el texto por defecto)">
          <textarea className="textarea-tech" rows={2} value={memoria.normativa} onChange={(e) => upd("normativa", e.target.value)} />
        </Campo>
        <Campo label="Descripción general (opcional)">
          <textarea className="textarea-tech" rows={2} value={memoria.descripcion} onChange={(e) => upd("descripcion", e.target.value)} />
        </Campo>
      </div>
      <div className="campo-label" style={{ marginTop: 16, marginBottom: 6 }}>Vista previa (se actualiza sola con tus cálculos)</div>
      <pre className="preview-memoria">{texto}</pre>
    </Panel>
  );
}

/* =========================================================
   EXPORTAR
   ========================================================= */

function TabExportar({ estado, onGuardar, onCargar, guardando, cargando, ultimoGuardado }) {
  const exportarExcel = () => {
    const p = calcularPresupuesto(estado.circuitosBT, estado.fv, estado.motores, estado.proyecto, estado.medicionesManual, estado.precios, estado.gastosGenerales, estado.beneficioIndustrial, estado.iva);
    const wb = XLSX.utils.book_new();

    const medRows = p.filas.map((f) => ({ Capítulo: f.capitulo, Descripción: f.descripcion, Ud: f.unidad, Cantidad: f.cantidad }));
    const wsMed = XLSX.utils.json_to_sheet(medRows);
    XLSX.utils.book_append_sheet(wb, wsMed, "Mediciones");

    const presRows = p.filas.map((f) => ({ Capítulo: f.capitulo, Descripción: f.descripcion, Ud: f.unidad, Cantidad: f.cantidad, "Precio unit. (€)": f.precioUnit, "Importe (€)": Number(f.importe.toFixed(2)) }));
    presRows.push({});
    presRows.push({ Descripción: "PEM", "Importe (€)": Number(p.pem.toFixed(2)) });
    presRows.push({ Descripción: `Gastos generales (${estado.gastosGenerales}%)`, "Importe (€)": Number(p.gg.toFixed(2)) });
    presRows.push({ Descripción: `Beneficio industrial (${estado.beneficioIndustrial}%)`, "Importe (€)": Number(p.bi.toFixed(2)) });
    presRows.push({ Descripción: "Presupuesto de contrata", "Importe (€)": Number(p.pca.toFixed(2)) });
    presRows.push({ Descripción: `IVA (${estado.iva}%)`, "Importe (€)": Number(p.ivaImporte.toFixed(2)) });
    presRows.push({ Descripción: "TOTAL", "Importe (€)": Number(p.total.toFixed(2)) });
    const wsPres = XLSX.utils.json_to_sheet(presRows);
    XLSX.utils.book_append_sheet(wb, wsPres, "Presupuesto");

    if (estado.circuitosBT.length > 0) {
      const btRows = estado.circuitosBT.map((c, i) => {
        const r = calcularCircuitoBT({ ...c, potencia: parseFloat(c.potencia) || 0, longitud: parseFloat(c.longitud) || 0, cosphi: parseFloat(c.cosphi) || 0.95, tension: parseFloat(c.tension) || 230, limiteCdt: parseFloat(c.limiteCdt) || 3 });
        return { Circuito: `C${i + 1}`, Nombre: c.nombre, "P (W)": c.potencia, Fases: c.fases, "Ib (A)": Number(r.Ib.toFixed(2)), "Sección (mm²)": r.seccion, "c.d.t. (%)": Number(r.cdtFinal.toFixed(2)), "Protección (A)": r.proteccion };
      });
      const wsBT = XLSX.utils.json_to_sheet(btRows);
      XLSX.utils.book_append_sheet(wb, wsBT, "Cálculo BT");
    }

    XLSX.writeFile(wb, `${(estado.proyecto.nombre || "proyecto").replace(/\s+/g, "_")}.xlsx`);
  };

  const exportarPDF = () => {
    window.print();
  };

  return (
    <Panel title="Guardar y exportar" eyebrow="07 · Salidas del proyecto" icon={<Download size={18} />}>
      <div className="export-grid">
        <div className="export-card">
          <ClipboardList size={20} />
          <h4>Excel — mediciones y presupuesto</h4>
          <p>Genera un libro con hojas de mediciones, presupuesto desglosado y el cálculo de circuitos BT.</p>
          <button className="btn-primary" onClick={exportarExcel}><Download size={15} /> Descargar .xlsx</button>
        </div>
        <div className="export-card">
          <FileText size={20} />
          <h4>PDF — memoria técnica</h4>
          <p>Abre el diálogo de impresión del navegador con una vista limpia de la memoria. Elige "Guardar como PDF".</p>
          <button className="btn-primary" onClick={exportarPDF}><Printer size={15} /> Imprimir / PDF</button>
        </div>
        <div className="export-card">
          <Save size={20} />
          <h4>Guardar proyecto</h4>
          <p>Guarda todos los datos introducidos en este navegador para poder continuar más tarde.</p>
          <button className="btn-primary" onClick={onGuardar} disabled={guardando}>{guardando ? "Guardando..." : "Guardar"}</button>
          {ultimoGuardado && <span className="guardado-hint">Guardado {ultimoGuardado}</span>}
        </div>
        <div className="export-card">
          <FolderOpen size={20} />
          <h4>Cargar proyecto</h4>
          <p>Recupera el último proyecto guardado en este navegador.</p>
          <button className="btn-secondary" onClick={onCargar} disabled={cargando}>{cargando ? "Cargando..." : "Cargar"}</button>
        </div>
      </div>
      <div className="nota-normativa">
        <Info size={14} />
        El guardado es local a tu cuenta en este artefacto (no se comparte con nadie más). La exportación a Word
        no está disponible directamente aquí — si quieres, pídeme aparte que te genere la memoria como documento
        Word y te la preparo con el mismo contenido.
      </div>
    </Panel>
  );
}

/* =========================================================
   VISTA DE IMPRESIÓN (memoria)
   ========================================================= */

function VistaImpresion({ estado }) {
  const texto = generarMemoriaTexto(estado.proyecto, estado.circuitosBT, estado.fv, estado.motores, estado.memoria);
  return (
    <div className="hoja-impresion">
      <h1>{estado.proyecto.nombre || "Memoria técnica"}</h1>
      <div className="cajetin-impresion">
        <span>Cliente: {estado.proyecto.cliente}</span>
        <span>Emplazamiento: {estado.proyecto.ubicacion}</span>
        <span>Técnico: {estado.proyecto.tecnico}</span>
        <span>Fecha: {estado.proyecto.fecha}</span>
      </div>
      <pre>{texto}</pre>
    </div>
  );
}

/* =========================================================
   APP PRINCIPAL
   ========================================================= */

const TABS = [
  { id: "proyecto", label: "Proyecto", icon: ClipboardList },
  { id: "bt", label: "Baja tensión", icon: Home },
  { id: "fv", label: "Fotovoltaica", icon: Sun },
  { id: "industrial", label: "Industrial", icon: Cog },
  { id: "mediciones", label: "Mediciones", icon: Wrench },
  { id: "presupuesto", label: "Presupuesto", icon: Receipt },
  { id: "memoria", label: "Memoria", icon: FileText },
  { id: "exportar", label: "Exportar", icon: Download },
];

export default function App() {
  const [tab, setTab] = useState("proyecto");
  const [proyecto, setProyecto] = useState(ESTADO_INICIAL.proyecto);
  const [circuitosBT, setCircuitosBT] = useState(ESTADO_INICIAL.circuitosBT);
  const [fv, setFv] = useState(ESTADO_INICIAL.fv);
  const [motores, setMotores] = useState(ESTADO_INICIAL.motores);
  const [medicionesManual, setMedicionesManual] = useState(ESTADO_INICIAL.medicionesManual);
  const [precios, setPrecios] = useState(ESTADO_INICIAL.precios);
  const [gastosGenerales, setGastosGenerales] = useState(ESTADO_INICIAL.gastosGenerales);
  const [beneficioIndustrial, setBeneficioIndustrial] = useState(ESTADO_INICIAL.beneficioIndustrial);
  const [iva, setIva] = useState(ESTADO_INICIAL.iva);
  const [memoria, setMemoria] = useState(ESTADO_INICIAL.memoria);

  const [guardando, setGuardando] = useState(false);
  const [cargando, setCargando] = useState(false);
  const [ultimoGuardado, setUltimoGuardado] = useState(null);
  const cargadoInicial = useRef(false);

  const estadoCompleto = { proyecto, circuitosBT, fv, motores, medicionesManual, precios, gastosGenerales, beneficioIndustrial, iva, memoria };

  const aplicarEstado = (s) => {
    if (!s) return;
    if (s.proyecto) setProyecto(s.proyecto);
    if (s.circuitosBT) setCircuitosBT(s.circuitosBT);
    if (s.fv) setFv(s.fv);
    if (s.motores) setMotores(s.motores);
    if (s.medicionesManual) setMedicionesManual(s.medicionesManual);
    if (s.precios) setPrecios(s.precios);
    if (typeof s.gastosGenerales === "number") setGastosGenerales(s.gastosGenerales);
    if (typeof s.beneficioIndustrial === "number") setBeneficioIndustrial(s.beneficioIndustrial);
    if (typeof s.iva === "number") setIva(s.iva);
    if (s.memoria) setMemoria(s.memoria);
  };

  const handleGuardar = async () => {
    setGuardando(true);
    try {
      await window.storage.set("proyecto-actual", JSON.stringify(estadoCompleto), false);
      setUltimoGuardado(new Date().toLocaleTimeString());
    } catch (e) {
      console.error("Error guardando", e);
    }
    setGuardando(false);
  };

  const handleCargar = async () => {
    setCargando(true);
    try {
      const r = await window.storage.get("proyecto-actual");
      if (r && r.value) aplicarEstado(JSON.parse(r.value));
    } catch (e) {
      console.error("No hay proyecto guardado todavía", e);
    }
    setCargando(false);
  };

  useEffect(() => {
    if (cargadoInicial.current) return;
    cargadoInicial.current = true;
    handleCargar();
  }, []);

  return (
    <div className="app-root">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

        .app-root {
          --ink-900: #10263f;
          --ink-700: #1c3f61;
          --ink-500: #45688a;
          --paper: #f6f4ee;
          --paper-line: rgba(16,38,63,0.09);
          --amber: #c8790f;
          --amber-soft: #f4e2c3;
          --green: #2f6f4f;
          --green-soft: #dcece2;
          --red: #a8402f;
          --red-soft: #f4dcd7;
          --white: #ffffff;
          font-family: 'IBM Plex Sans', sans-serif;
          color: var(--ink-900);
          background:
            linear-gradient(var(--paper-line) 1px, transparent 1px) 0 0/100% 28px,
            linear-gradient(90deg, var(--paper-line) 1px, transparent 1px) 0 0/28px 100%,
            var(--paper);
          min-height: 100%;
          padding: 0;
        }
        .app-root * { box-sizing: border-box; }
        .app-root h1, .app-root h2, .app-root h3, .app-root h4 { font-family: 'Space Grotesk', sans-serif; margin: 0; }

        .cajetin {
          display: flex; flex-wrap: wrap; gap: 0;
          border: 2px solid var(--ink-900);
          background: var(--white);
          margin: 14px;
          font-family: 'IBM Plex Mono', monospace;
          font-size: 11px;
        }
        .cajetin-brand {
          display: flex; align-items: center; gap: 8px;
          padding: 10px 16px; border-right: 2px solid var(--ink-900);
          font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 14px;
          color: var(--white); background: var(--ink-900);
        }
        .cajetin-fields { display: flex; flex: 1; flex-wrap: wrap; }
        .cajetin-field { padding: 8px 14px; border-right: 1px solid var(--paper-line); min-width: 140px; flex: 1; }
        .cajetin-field:last-child { border-right: none; }
        .cajetin-field label { display: block; text-transform: uppercase; letter-spacing: 0.06em; color: var(--ink-500); font-size: 9px; margin-bottom: 3px; }
        .cajetin-field input { border: none; background: transparent; font-family: 'IBM Plex Mono', monospace; font-size: 12px; color: var(--ink-900); width: 100%; outline: none; }

        .layout { display: flex; gap: 0; padding: 0 14px 40px; align-items: flex-start; }
        .nav-tabs { display: flex; flex-direction: column; gap: 2px; width: 200px; flex-shrink: 0; position: sticky; top: 14px; }
        .nav-tab {
          display: flex; align-items: center; gap: 9px; text-align: left;
          padding: 10px 12px; border: 1px solid transparent; background: transparent;
          font-family: 'IBM Plex Sans', sans-serif; font-size: 13px; font-weight: 500;
          color: var(--ink-700); cursor: pointer; border-radius: 2px;
        }
        .nav-tab:hover { background: var(--white); }
        .nav-tab.active { background: var(--ink-900); color: var(--white); }
        .nav-tab .num { font-family: 'IBM Plex Mono', monospace; font-size: 10px; opacity: 0.6; }

        .contenido { flex: 1; padding: 4px 0 0 20px; min-width: 0; }

        .panel { background: var(--white); border: 1px solid var(--paper-line); border-radius: 3px; }
        .panel-head { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 2px solid var(--ink-900); }
        .panel-eyebrow { font-family: 'IBM Plex Mono', monospace; font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--amber); margin-bottom: 2px; }
        .panel-title { display: flex; align-items: center; gap: 8px; font-size: 18px; font-weight: 600; }
        .panel-body { padding: 20px; }

        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px 18px; }
        .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px 14px; margin-top: 14px; }
        @media (max-width: 900px) { .grid-2, .grid-4 { grid-template-columns: 1fr 1fr; } }

        .campo { display: flex; flex-direction: column; gap: 4px; }
        .campo-label { font-size: 11px; font-weight: 600; color: var(--ink-500); text-transform: uppercase; letter-spacing: 0.04em; }
        .campo-hint { font-size: 10px; color: var(--ink-500); }

        .input-tech {
          font-family: 'IBM Plex Mono', monospace; font-size: 13px;
          border: 1px solid var(--paper-line); border-bottom: 2px solid var(--ink-500);
          border-radius: 2px; padding: 7px 9px; background: var(--paper); color: var(--ink-900);
          outline: none; width: 100%;
        }
        .input-tech:focus { border-bottom-color: var(--amber); background: var(--white); }
        .input-nombre { font-family: 'Space Grotesk', sans-serif; font-size: 14px; font-weight: 600; }

        .textarea-tech { font-family: 'IBM Plex Sans', sans-serif; font-size: 13px; border: 1px solid var(--paper-line); border-radius: 2px; padding: 8px 10px; background: var(--paper); resize: vertical; width: 100%; }

        .tipos-grid { display: flex; gap: 10px; flex-wrap: wrap; }
        .tipo-check { display: flex; align-items: center; gap: 7px; border: 1px solid var(--paper-line); border-radius: 2px; padding: 9px 14px; font-size: 13px; font-weight: 500; cursor: pointer; background: var(--paper); }
        .tipo-check input { accent-color: var(--ink-900); }

        .nota-normativa { display: flex; gap: 8px; align-items: flex-start; background: var(--amber-soft); border-left: 3px solid var(--amber); padding: 10px 12px; font-size: 12px; color: var(--ink-700); border-radius: 2px; line-height: 1.5; }
        .nota-normativa svg { flex-shrink: 0; margin-top: 2px; color: var(--amber); }

        .btn-primary, .btn-secondary {
          display: inline-flex; align-items: center; gap: 6px; font-family: 'IBM Plex Sans', sans-serif;
          font-weight: 600; font-size: 12.5px; padding: 8px 14px; border-radius: 2px; cursor: pointer; border: none;
        }
        .btn-primary { background: var(--ink-900); color: var(--white); }
        .btn-primary:hover { background: var(--ink-700); }
        .btn-primary:disabled { opacity: 0.5; cursor: default; }
        .btn-secondary { background: var(--white); color: var(--ink-900); border: 1px solid var(--ink-900); }
        .btn-icon { border: none; background: transparent; color: var(--red); cursor: pointer; padding: 6px; border-radius: 2px; }
        .btn-icon:hover { background: var(--red-soft); }

        .vacio { color: var(--ink-500); font-size: 13px; font-style: italic; }

        .lista-circuitos { display: flex; flex-direction: column; gap: 14px; }
        .tarjeta-circuito { border: 1px solid var(--paper-line); border-radius: 3px; padding: 14px; background: var(--paper); }
        .tarjeta-head { display: flex; gap: 8px; align-items: center; margin-bottom: 4px; }
        .tarjeta-head .input-nombre { flex: 1; }

        .resultado-bar { display: flex; gap: 18px; flex-wrap: wrap; align-items: center; margin-top: 14px; padding-top: 12px; border-top: 1px dashed var(--paper-line); }
        .resultado-item { display: flex; flex-direction: column; font-family: 'IBM Plex Mono', monospace; }
        .resultado-item span { font-size: 9px; text-transform: uppercase; color: var(--ink-500); letter-spacing: 0.05em; }
        .resultado-item b { font-size: 14px; color: var(--ink-900); }

        .badge { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; font-weight: 600; padding: 5px 9px; border-radius: 20px; }
        .badge-ok { background: var(--green-soft); color: var(--green); }
        .badge-bad { background: var(--red-soft); color: var(--red); }

        .subtitulo-tabla { font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 13px; margin: 20px 0 4px; color: var(--ink-700); }

        .capitulo-bloque { margin-bottom: 18px; }
        .capitulo-titulo { font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 13px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--amber); margin-bottom: 6px; }
        .tabla-tech { width: 100%; border-collapse: collapse; font-size: 13px; }
        .tabla-tech th { text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--ink-500); border-bottom: 2px solid var(--ink-900); padding: 6px 8px; }
        .tabla-tech td { padding: 6px 8px; border-bottom: 1px solid var(--paper-line); vertical-align: middle; }

        .linea-presupuesto { display: flex; justify-content: space-between; align-items: center; padding: 8px 4px; font-size: 13.5px; gap: 10px; }
        .linea-presupuesto.sub { color: var(--ink-500); font-size: 12.5px; padding-left: 14px; }
        .linea-presupuesto.total { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 17px; border-top: 2px solid var(--ink-900); margin-top: 6px; padding-top: 12px; color: var(--ink-900); }
        .pct-input { display: flex; align-items: center; gap: 4px; font-family: 'IBM Plex Mono', monospace; }
        .separador { height: 1px; background: var(--paper-line); margin: 8px 0; }

        .detalle-precios { margin-top: 18px; font-size: 12.5px; }
        .detalle-precios summary { cursor: pointer; font-weight: 600; color: var(--ink-700); padding: 6px 0; }
        .grid-precios { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 10px; }
        .precio-item { display: flex; flex-direction: column; gap: 3px; font-size: 11px; text-transform: capitalize; color: var(--ink-500); }

        .preview-memoria { font-family: 'IBM Plex Mono', monospace; font-size: 12px; line-height: 1.6; white-space: pre-wrap; background: var(--paper); border: 1px solid var(--paper-line); border-radius: 3px; padding: 16px; max-height: 480px; overflow-y: auto; }

        .export-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }
        @media (max-width: 900px) { .export-grid { grid-template-columns: 1fr; } }
        .export-card { border: 1px solid var(--paper-line); border-radius: 3px; padding: 16px; display: flex; flex-direction: column; gap: 8px; background: var(--paper); }
        .export-card svg { color: var(--amber); }
        .export-card h4 { font-size: 14px; }
        .export-card p { font-size: 12px; color: var(--ink-500); margin: 0; line-height: 1.5; flex: 1; }
        .guardado-hint { font-size: 11px; color: var(--green); }

        .hoja-impresion { display: none; }
        @media print {
          .app-root > .cajetin, .app-root > .layout { display: none !important; }
          .hoja-impresion { display: block; font-family: 'IBM Plex Sans', sans-serif; padding: 20px; }
          .hoja-impresion h1 { font-family: 'Space Grotesk', sans-serif; margin-bottom: 10px; }
          .cajetin-impresion { display: flex; gap: 16px; flex-wrap: wrap; font-size: 11px; border: 1px solid #000; padding: 8px 10px; margin-bottom: 18px; font-family: 'IBM Plex Mono', monospace; }
          .hoja-impresion pre { white-space: pre-wrap; font-family: 'IBM Plex Mono', monospace; font-size: 11.5px; line-height: 1.6; }
        }
      `}</style>

      <div className="cajetin">
        <div className="cajetin-brand"><Zap size={18} /> PROYECTISTA</div>
        <div className="cajetin-fields">
          <div className="cajetin-field"><label>Proyecto</label><input value={proyecto.nombre} onChange={(e) => setProyecto({ ...proyecto, nombre: e.target.value })} placeholder="—" /></div>
          <div className="cajetin-field"><label>Cliente</label><input value={proyecto.cliente} onChange={(e) => setProyecto({ ...proyecto, cliente: e.target.value })} placeholder="—" /></div>
          <div className="cajetin-field"><label>Técnico</label><input value={proyecto.tecnico} onChange={(e) => setProyecto({ ...proyecto, tecnico: e.target.value })} placeholder="—" /></div>
          <div className="cajetin-field"><label>Fecha</label><input value={proyecto.fecha} onChange={(e) => setProyecto({ ...proyecto, fecha: e.target.value })} placeholder="—" /></div>
        </div>
      </div>

      <div className="layout">
        <nav className="nav-tabs">
          {TABS.map((t, i) => {
            const Icon = t.icon;
            return (
              <button key={t.id} className={"nav-tab " + (tab === t.id ? "active" : "")} onClick={() => setTab(t.id)}>
                <span className="num">{String(i).padStart(2, "0")}</span>
                <Icon size={15} />
                {t.label}
                {tab === t.id && <ChevronRight size={13} style={{ marginLeft: "auto" }} />}
              </button>
            );
          })}
        </nav>

        <div className="contenido">
          {tab === "proyecto" && <TabProyecto proyecto={proyecto} setProyecto={setProyecto} />}
          {tab === "bt" && <TabBT circuitos={circuitosBT} setCircuitos={setCircuitosBT} />}
          {tab === "fv" && <TabFV fv={fv} setFv={setFv} />}
          {tab === "industrial" && <TabIndustrial motores={motores} setMotores={setMotores} />}
          {tab === "mediciones" && (
            <TabMediciones
              circuitosBT={circuitosBT} fv={fv} motores={motores} proyecto={proyecto}
              medicionesManual={medicionesManual} setMedicionesManual={setMedicionesManual} precios={precios}
            />
          )}
          {tab === "presupuesto" && (
            <TabPresupuesto
              circuitosBT={circuitosBT} fv={fv} motores={motores} proyecto={proyecto}
              medicionesManual={medicionesManual} precios={precios} setPrecios={setPrecios}
              gastosGenerales={gastosGenerales} setGastosGenerales={setGastosGenerales}
              beneficioIndustrial={beneficioIndustrial} setBeneficioIndustrial={setBeneficioIndustrial}
              iva={iva} setIva={setIva}
            />
          )}
          {tab === "memoria" && <TabMemoria proyecto={proyecto} circuitosBT={circuitosBT} fv={fv} motores={motores} memoria={memoria} setMemoria={setMemoria} />}
          {tab === "exportar" && (
            <TabExportar estado={estadoCompleto} onGuardar={handleGuardar} onCargar={handleCargar} guardando={guardando} cargando={cargando} ultimoGuardado={ultimoGuardado} />
          )}
        </div>
      </div>

      <VistaImpresion estado={estadoCompleto} />
    </div>
  );
}
