# ⚡ REBT Suite — Plataforma de Instalaciones Eléctricas

Plataforma completa para el diseño, cálculo y documentación de instalaciones eléctricas de baja tensión,
conforme a **REBT (España)** e **IEC 60364**.

## Stack
- **Frontend:** Next.js 14 (App Router) + TypeScript + Tailwind CSS + shadcn/ui
- **Backend:** FastAPI (Python) + SQLAlchemy + PostgreSQL
- **Auth:** JWT + Supabase Auth
- **Hosting:** Vercel (frontend) + Render (backend) + Supabase (BD) — todo gratuito

## Funciones
- Calculadora de secciones de cable (REBT + IEC)
- Fotovoltaica (autoconsumo, baterías, excedentes)
- Cálculo de cortocircuito (Icc, selectividad, poder de corte)
- Verificación de protecciones (curvas, coordinación)
- Presupuesto (mediciones, precios, exportación Excel/PDF/Word)
- Documentación técnica (MTD, anexo, pliego)
- Unifilar SVG automático
- Gestión de proyectos y dashboard
- API REST para integraciones
- Multi-idioma (ES/EN/FR)

## Estructura
```
frontend/   # Next.js app
backend/    # FastAPI app
docker-compose.yml
```

## Desarrollo local
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Despliegue
- Frontend → Vercel
- Backend → Render
- BD → Supabase
