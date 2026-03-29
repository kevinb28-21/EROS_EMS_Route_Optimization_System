# EROS — EMS Route Optimization System

A unified EMS dispatcher system that supports route planning, hospital selection, traffic-aware ETAs, operational simulation, and a single web dashboard.

**Course:** COE892 — Distributed Systems and Cloud Computing (W2026, TMU)

---

## Repository layout

```
EROS_EMS-Route_Optimization_System/
├── backend/                 # FastAPI API (deploy on Railway)
│   ├── app/
│   ├── Dockerfile           # PORT-aware for Railway
│   ├── Procfile             # Nixpacks / process start
│   ├── requirements.txt
│   └── .env.example
├── frontend/                # React + Vite SPA (deploy on Netlify)
│   ├── public/_redirects    # SPA fallback (optional)
│   └── src/
├── netlify.toml             # Netlify: base=frontend, build + SPA redirects
├── docker-compose.yml
└── README.md
```

---

## Features

### Intelligent routing
- **A\*** pathfinding on a simplified Toronto road network (NetworkX graph)
- Route polylines, distance, and ETA between incidents, vehicles, and hospitals
- **Traffic simulation** — time-of-day speed multipliers (rush hour, night, etc.); ETAs reflect current traffic level

### Hospital recommendation
- Weighted scoring: distance (35%), capacity (30%), specialty match (25%), trauma center bonus (10%)
- Respects hospital status (open, diversion, closed) and incident severity

### Dispatcher dashboard
- React Leaflet map (CARTO Dark / OSM-based tiles)
- Incident, vehicle, and hospital panels; event log; full incident lifecycle actions
- **Auto-refresh** every 3 seconds for live simulation state
- **Simulation toolbar** — **Tick** (advance one step), **Incident** (random downtown incident)
- **Traffic badge** in the header (congestion level)

### Architecture
- **Frontend:** React + Vite, TanStack Query  
- **Backend:** FastAPI, modular routers + services  
- **Database:** SQLite (default local) / PostgreSQL (Railway, Docker)  
- **Background simulation engine** (optional via `SIMULATION_ENABLED`)

---

## Tech stack

| Layer    | Technology |
|----------|------------|
| Frontend | React 18, TypeScript, Vite, TailwindCSS, TanStack Query, React Leaflet |
| Backend  | Python 3.11+, FastAPI, Uvicorn, SQLAlchemy, Pydantic |
| Database | SQLite (dev default) / PostgreSQL (production) |
| Routing  | NetworkX + custom A* |

---

## Local development

### Prerequisites
- Python 3.11+
- Node.js 18+

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Default DATABASE_URL is SQLite — no Postgres required for quick runs
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: `http://localhost:8000`
- Docs: `http://localhost:8000/api/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

- App: `http://localhost:5173`
- Leave **`VITE_API_URL` unset** so the Vite dev proxy forwards `/api` to `http://localhost:8000`.

### Docker Compose

From the repository root:

```bash
docker compose up
```

---

## Deployment: Railway (backend) + Netlify (frontend)

- **Railway** — FastAPI + **PostgreSQL** (managed `DATABASE_URL`).
- **Netlify** — static build (`frontend/dist`). Root **`netlify.toml`** sets `base = "frontend"`.

### Railway — API

The repo includes **`railway.toml`** (builder **`DOCKERFILE`**) and a **root `Dockerfile`** that copies `backend/` only. This avoids **“Error creating build plan with Railpack”**, which happens when Railway tries to auto-detect a single app at the monorepo root (frontend + backend).

1. New project → connect GitHub → add **PostgreSQL**.
2. Create/deploy the service from this repo — **leave Root Directory empty** (repo root) so Railway uses `railway.toml` + root `Dockerfile`, **or** set Root Directory to **`backend`** and use `backend/Dockerfile` (disable conflicting root config if you duplicate services).
3. Set variables, for example:

| Variable | Notes |
|----------|--------|
| `DATABASE_URL` | Usually from Postgres plugin |
| `CORS_ORIGINS` | Must include your Netlify URL, e.g. `https://your-app.netlify.app,http://localhost:5173` |
| `DEBUG` | `false` in production |
| `SIMULATION_ENABLED` | `true` or `false` |

4. Copy the public **HTTPS API URL** (e.g. `https://….up.railway.app`). Health: `GET /health`.

### Netlify — frontend

1. New site from GitHub (same repo).
2. Netlify reads **`netlify.toml`** at repo root (`base = frontend`).
3. Add build env **`VITE_API_URL`** = Railway API origin only (no path, no trailing slash). Redeploy after changes.

### CORS

`CORS_ORIGINS` on Railway must include your exact Netlify origin (`https://…netlify.app`).

### Render (alternative to Railway)

Use this if Railway credits are exhausted. The repo includes **`render.yaml`** so Render builds from **`backend/`** (avoids “could not find `requirements.txt`” / wrong build root).

1. **New → Blueprint** (or Web Service) → connect this GitHub repo.
2. If not using Blueprint: create a **Web Service**, set **Root Directory** to **`backend`**, **Runtime** Python.
3. **Build command:** `pip install -r requirements.txt`  
   **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add **PostgreSQL** (or use **Neon** / **Supabase** and paste `DATABASE_URL`).
5. Set **`DATABASE_URL`**, **`CORS_ORIGINS`** (your frontend URL), **`DEBUG=false`** (optional).

**If the build failed with exit code 1:** almost always the service was built from the **repo root** instead of **`backend/`**. Fix in **Settings → Root Directory → `backend`**, or redeploy using **`render.yaml`**.

Free web services **sleep after idle**; first request after sleep can be slow (~30–60+ s).

---

## Configuration

### Backend (`backend/.env` or Railway)

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | SQLAlchemy URL |
| `API_HOST` / `API_PORT` | Bind; cloud often sets `PORT` |
| `DEBUG` | `true` / `false` |
| `CORS_ORIGINS` | Comma-separated browser origins |
| `SIMULATION_ENABLED` | Run background simulation engine |
| `SIMULATION_INTERVAL_SECONDS` | Tick interval |

### Frontend (Netlify build env)

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Production: Railway API **origin** only. Local: leave unset. |

---

## API overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/incidents` | List incidents |
| POST | `/api/v1/incidents` | Create incident |
| GET | `/api/v1/incidents/{id}` | Incident details |
| POST | `/api/v1/incidents/{id}/assign-vehicle` | Dispatch vehicle |
| POST | `/api/v1/incidents/{id}/assign-hospital` | Set destination hospital |
| GET | `/api/v1/vehicles` | List vehicles |
| GET | `/api/v1/hospitals` | List hospitals |
| POST | `/api/v1/hospitals/recommend` | Hospital recommendations |
| POST | `/api/v1/routes/calculate` | Route between points |
| GET | `/api/v1/status-updates/recent` | Recent event log |
| GET | `/api/v1/simulation/status` | Simulation & traffic state |
| POST | `/api/v1/simulation/tick` | Advance simulation one step |
| POST | `/api/v1/simulation/generate-incident` | Random incident |

Interactive docs: `/api/docs` on the backend.

---

## Testing

```bash
cd backend
pytest
pytest tests/test_routing.py -v
```

---

## Demo workflow (local)

1. Open `http://localhost:5173` — seeded hospitals, vehicles, incidents; simulation runs in the background.
2. Use **Tick** / **Incident** in the header, or **New Incident** for a manual report.
3. Open an incident → **Dispatch Vehicle** → route on map → **Mark On Scene** → hospital recommendations → **Set Destination** → **Begin Transport** → **Complete Incident**.

---

## Design notes

- **Routing:** A* with Haversine heuristic; road-type base speeds; traffic multipliers by time of day.
- **Hospital scoring:** Distance, capacity, specialties, trauma center bonus for critical cases.
- **Frontend:** TanStack Query with ~3s refetch; dark “command center” UI.

---

## Limitations & future work

- Simplified road graph (no OSRM/GraphHopper in-tree).
- Simulated GPS / capacity (no live feeds).
- No auth (demo / course scope).
- Polling instead of WebSockets for real-time updates.

---

## License & authors

Educational use — COE892, Winter 2026, Toronto Metropolitan University.

**Authors:** project team (COE892 W2026).
