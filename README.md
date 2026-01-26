# EROS - EMS Route Optimization System

A unified EMS Dispatcher System that processes real-time data to optimize emergency response routing and hospital selection.

**Course**: COE892 — Distributed Systems and Cloud Computing (W2026, TMU)

---

## Features

### 1. Intelligent Routing Engine
- **A* pathfinding** on a simplified Toronto road network
- Route calculation between incidents, vehicles, and hospitals
- Real-time route visualization on the map
- Distance and ETA estimations

### 2. Hospital & Resource Availability Module
- Track hospital capacity (ER beds, occupancy rates)
- Monitor hospital status (Open, Diversion, Closed)
- **Smart hospital recommendations** based on:
  - Distance from incident
  - Current capacity/availability
  - Required specialties (trauma, cardiac, etc.)
  - Incident severity

### 3. EMS Operations Communication Dashboard
- Interactive map showing all entities (OpenStreetMap-based)
- Real-time incident list with severity indicators
- Vehicle status tracking
- Hospital availability overview
- Event log for system communications

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                              EROS                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                  Frontend (React + Vite)                     │   │
│   │   • React Leaflet Map                                        │   │
│   │   • Incident/Vehicle/Hospital Panels                         │   │
│   │   • TanStack Query for data fetching                         │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│                              ▼ REST API                              │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                  Backend (FastAPI)                           │   │
│   │   ┌─────────────┐  ┌────────────────┐  ┌─────────────────┐  │   │
│   │   │  Routing    │  │   Hospital     │  │   Simulation    │  │   │
│   │   │  Service    │  │  Recommender   │  │    Engine       │  │   │
│   │   │  (A* algo)  │  │                │  │                 │  │   │
│   │   └─────────────┘  └────────────────┘  └─────────────────┘  │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│                              ▼                                       │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                   PostgreSQL Database                        │   │
│   │   Incidents • Vehicles • Hospitals • StatusUpdates           │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer     | Technology                                          |
|-----------|-----------------------------------------------------|
| Frontend  | React 18, Vite, TypeScript, TailwindCSS             |
| Map       | React Leaflet, OpenStreetMap tiles (CARTO Dark)     |
| State     | TanStack Query (React Query)                        |
| Backend   | Python 3.11+, FastAPI, Uvicorn                      |
| Database  | PostgreSQL with SQLAlchemy ORM                      |
| Routing   | NetworkX + custom A* implementation                 |

---

## Project Structure

```
eros/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI application entry point
│   │   ├── config.py         # Configuration management
│   │   ├── database.py       # Database setup
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── schemas.py        # Pydantic schemas
│   │   ├── routers/          # API endpoints
│   │   │   ├── incidents.py
│   │   │   ├── vehicles.py
│   │   │   ├── hospitals.py
│   │   │   ├── routes.py
│   │   │   └── status_updates.py
│   │   └── services/         # Business logic
│   │       ├── routing.py         # A* pathfinding
│   │       ├── hospital_recommender.py
│   │       ├── simulation.py      # Demo simulation
│   │       └── seeder.py          # Demo data
│   ├── tests/                # Unit tests
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx           # Main dashboard
│   │   ├── api/              # API client
│   │   ├── components/       # React components
│   │   │   ├── MapPanel.tsx
│   │   │   ├── IncidentList.tsx
│   │   │   ├── VehicleList.tsx
│   │   │   ├── HospitalList.tsx
│   │   │   ├── EventLog.tsx
│   │   │   └── ...modals
│   │   └── types/            # TypeScript types
│   ├── package.json
│   └── vite.config.ts
│
└── README.md
```

---

## Setup Instructions

### Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm/pnpm
- **PostgreSQL 14+** (or use SQLite for quick testing)

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env
# Edit .env to set your DATABASE_URL

# For quick testing with SQLite (no PostgreSQL needed):
# Set DATABASE_URL=sqlite:///./eros.db in .env

# Start the backend server
uvicorn app.main:app --reload --port 8000
```

The backend will:
- Initialize database tables on first run
- Seed demo data (hospitals, vehicles, sample incidents)
- Be available at `http://localhost:8000`
- API docs at `http://localhost:8000/api/docs`

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

---

## Demo Script

Follow these steps to demonstrate the system:

### 1. Initial State
- Open the dashboard at `http://localhost:5173`
- Observe the map centered on downtown Toronto
- Note the seeded data: 6 hospitals, 8 vehicles, and several pending incidents

### 2. Create a New Incident
- Click **"New Incident"** button
- Fill in:
  - Description: "Chest pain, 65-year-old male"
  - Severity: **CRITICAL**
  - Leave default Toronto coordinates or adjust
- Click **"Report Incident"**

### 3. Dispatch a Vehicle
- Click on the new incident (or any pending incident)
- In the modal, select an available vehicle
- Click **"Dispatch Vehicle"**
- Observe:
  - Route appears on the map (blue dashed line)
  - Vehicle status changes to "Dispatched"
  - Event log shows dispatch message

### 4. Progress the Incident
- Click on the dispatched incident
- Click **"Mark On Scene"** (simulating arrival)
- Note hospital recommendations appear
- Select a recommended hospital
- Click **"Set Destination"**
- Click **"Begin Transport"**
- Finally, click **"Complete Incident"**

### 5. Hospital Capacity Changes
- Observe hospital capacity bars in the Hospital panel
- In a real demo, capacity fluctuates over time
- Hospitals with >95% capacity go to DIVERSION status

---

## API Endpoints

| Method | Endpoint                        | Description                    |
|--------|--------------------------------|--------------------------------|
| GET    | `/api/v1/incidents`            | List all incidents             |
| POST   | `/api/v1/incidents`            | Create new incident            |
| GET    | `/api/v1/incidents/{id}`       | Get incident details           |
| POST   | `/api/v1/incidents/{id}/assign-vehicle` | Dispatch vehicle      |
| POST   | `/api/v1/incidents/{id}/assign-hospital` | Set destination       |
| GET    | `/api/v1/vehicles`             | List all vehicles              |
| GET    | `/api/v1/vehicles/available`   | List available vehicles        |
| GET    | `/api/v1/hospitals`            | List all hospitals             |
| POST   | `/api/v1/hospitals/recommend`  | Get hospital recommendations   |
| POST   | `/api/v1/routes/calculate`     | Calculate route between points |
| GET    | `/api/v1/status-updates/recent`| Get recent event log           |

Full API documentation available at `/api/docs` (Swagger UI)

---

## Testing

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_routing.py -v
```

---

## Configuration

### Backend Environment Variables

| Variable                    | Default                              | Description                 |
|-----------------------------|--------------------------------------|-----------------------------|
| `DATABASE_URL`              | `postgresql://eros:...`              | Database connection string  |
| `API_HOST`                  | `0.0.0.0`                            | API host                    |
| `API_PORT`                  | `8000`                               | API port                    |
| `DEBUG`                     | `true`                               | Enable debug mode           |
| `CORS_ORIGINS`              | `http://localhost:5173`              | Allowed CORS origins        |
| `SIMULATION_ENABLED`        | `true`                               | Enable background sim       |
| `SIMULATION_INTERVAL_SECONDS` | `5`                                | Simulation tick interval    |

---

## Key Design Decisions

### Routing Algorithm
- Uses **A* pathfinding** with a simplified Toronto road network
- Graph built with ~30 nodes (major intersections) and ~50 edges
- Heuristic: Haversine (great-circle) distance
- Edge weights: Road segment distances
- Speed estimates vary by road type (highway: 80 km/h, arterial: 50 km/h)

### Hospital Recommendation
- **Weighted scoring** system:
  - Distance: 35% weight (closer is better)
  - Capacity: 30% weight (more available beds is better)
  - Specialty match: 25% weight (matching required specialties)
  - Trauma center bonus: 10% weight (for critical incidents)

### Frontend Architecture
- **TanStack Query** for server state management with auto-refresh
- **Component-based** architecture with clear separation
- **Dark theme** "Command Center" aesthetic for EMS feel

---

## Limitations & Future Work

### Current Limitations
- Road network is simplified (downtown Toronto only)
- No real GPS integration (positions are simulated)
- No authentication/authorization (appropriate for demo)
- Single-server deployment (no microservices)

### Potential Enhancements
- Integrate with OSRM or GraphHopper for real routing
- Add WebSocket for true real-time updates
- Implement multi-vehicle dispatch for major incidents
- Add historical analytics and reporting
- Mobile-responsive design for tablet deployment

---

## License

This project is created for educational purposes as part of COE892 at TMU.

---

## Authors

Created for COE892 — Distributed Systems and Cloud Computing
Winter 2026, Toronto Metropolitan University
