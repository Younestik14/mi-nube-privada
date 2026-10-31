export default function Home() {
  return (
    <main className="min-h-screen p-8">
      <div className="hero mb-8">
        <p className="text-sm uppercase tracking-widest opacity-80">REBT Suite · v1.0</p>
        <h1 className="text-4xl font-bold mt-2">Diseña instalaciones con criterio y claridad</h1>
        <p className="mt-2 opacity-90">
          Calcula secciones de cable, dimensiona fotovoltaica, verifica protecciones y genera
          documentación técnica conforme a REBT e IEC 60364.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass">
          <h2 className="text-xl font-bold">⚡ Calculadora de secciones</h2>
          <p className="text-sm mt-2 opacity-80">
            Sección de cable, protecciones, caída de tensión. REBT + IEC.
          </p>
        </div>
        <div className="glass">
          <h2 className="text-xl font-bold">☀️ Fotovoltaica</h2>
          <p className="text-sm mt-2 opacity-80">
            Autoconsumo, baterías, excedentes, producción anual.
          </p>
        </div>
        <div className="glass">
          <h2 className="text-xl font-bold">🔌 Cortocircuito</h2>
          <p className="text-sm mt-2 opacity-80">
            Icc, selectividad, poder de corte, verificación térmica.
          </p>
        </div>
        <div className="glass">
          <h2 className="text-xl font-bold">🛡️ Protecciones</h2>
          <p className="text-sm mt-2 opacity-80">
            Curvas, coordinación, selectividad entre protecciones.
          </p>
        </div>
        <div className="glass">
          <h2 className="text-xl font-bold">💰 Presupuesto</h2>
          <p className="text-sm mt-2 opacity-80">
            Mediciones, precios, exportación Excel/PDF/Word.
          </p>
        </div>
        <div className="glass">
          <h2 className="text-xl font-bold">📄 Documentación</h2>
          <p className="text-sm mt-2 opacity-80">
            MTD, anexo de cálculos, pliego de condiciones.
          </p>
        </div>
      </div>

      <footer className="mt-12 text-center text-sm opacity-60">
        REBT Suite · Younesse Tikent Tifaoui · Herramienta de apoyo, no sustituye verificación profesional.
      </footer>
    </main>
  );
}
