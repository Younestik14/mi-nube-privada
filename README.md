# TIA Portal Simulator — KOP (Ladder)

Simulador de TIA Portal para PLCs Siemens S7-1200/S7-1500 con lenguaje KOP (Kontaktplan / Ladder).

## Características
- Editor visual de ladder (contactos, bobinas, temporizadores, contadores, comparadores, matemáticas, MOVE)
- Simulación en tiempo real con HMI (entradas/salidas)
- Modos STOP / RUN / DEBUG (paso a ciclo)
- Memoria de proceso (I, Q, M, T, C, DB)
- Guardar/cargar proyectos JSON
- CPU S7-1200 y S7-1500

## Stack
- Electron + React + TypeScript + Vite
- React Flow (editor de nodos)
- Zustand (estado)

## Desarrollo
```bash
npm install
npm run dev
```

## Build
```bash
npm run build
npm run package
```

## Licencia
MIT — Proyecto educativo. No afiliado con Siemens.