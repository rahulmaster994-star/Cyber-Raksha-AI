# Cyber Raksha AI — System Architecture Specification

## 1. High-Level Architecture

Cyber Raksha AI is built around a decoupled 3-tier architecture:

```
[ Frontend: React 19 + TypeScript + Vite + Tailwind CSS + Three.js ]
                               │
                       HTTP / REST API
                               │
            [ Backend: FastAPI + Pydantic v2 + Uvicorn ]
                     │                      │
           SQLAlchemy ORM             Internal API
                     │                      │
       [ Database: SQLite ]        [ AI Engine Subsystem ]
     (PostgreSQL-ready schema)    (Standby in Stage 1)
```

## 2. Component Design

### 2.1 Frontend Tier
- **Framework**: React 19 (TypeScript) powered by Vite.
- **Styling**: Tailwind CSS tailored with a dark cybersecurity aesthetic (Deep Navy `#050811`, Midnight Blue `#0B132B`, Electric Cyan `#00F0FF`, Accent Blue `#38BDF8`).
- **Icons**: Lucide React.
- **3D Visualization**: Modular Three.js canvas architecture for interactive cyber-grid / telemetry visualization.
- **State & Communication**: Centralized HTTP client with automatic polling, health monitoring, and connection failure resilience.

### 2.2 Backend Tier
- **Framework**: FastAPI (Python 3.13) running on ASGI (Uvicorn).
- **Validation**: Pydantic v2 schemas for strict contract verification and type safety.
- **Diagnostics**:
  - Live query database health checks measuring round-trip latency (`SELECT 1`).
  - System component introspection distinguishing implemented vs planned components.
- **Routing**: Dual routing layout (`/api/...` for direct spec compliance and `/api/v1/...` for versioned routing).
- **Security**: CORS policies, parameterized database queries, and credential salt hashing.

### 2.3 Database Tier
- **Engine**: SQLite (zero-configuration development engine).
- **ORM**: SQLAlchemy 2.0 with declarative base models.
- **Migration Ready**: Clean relational schemas allowing instantaneous transition to PostgreSQL or CockroachDB via connection string replacement.
- **Entities**:
  - `User`: Analysts and system administrators.
  - `SystemConfig`: Dynamic platform parameters.
  - `SecurityEvent`: System security logs and threat detections.
  - `AnalysisHistory`: Historical runs of detection modules.
  - `Notification`: System status messages and security alerts.

### 2.4 AI Engine Subsystem
- Modular directory structure separating `datasets`, `preprocessing`, `models`, `training`, `evaluation`, and `inference`.
- Pre-configured base interfaces ready for model training in subsequent development stages.
