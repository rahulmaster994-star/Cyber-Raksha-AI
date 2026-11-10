# CYBER RAKSHA AI — TECHNOLOGY STACK
**Technical Justification & Component Inventory**

---

## 1. Primary Technology Stack Inventory

| Component / Layer | Technology Selected | Version | Purpose & Technical Justification |
|:---|:---|:---|:---|
| **Backend Framework** | **FastAPI** | `0.115.11` | Modern asynchronous Python framework with native OpenAPI schema generation, pydantic validation, and low request overhead. |
| **ASGI Web Server** | **Uvicorn** | `0.34.0` | High-performance ASGI server supporting asynchronous worker lifespans and background tasks. |
| **Relational Database** | **SQLite** | `3.45+` | Zero-configuration, zero-budget, serverless relational database engine stored as a single portable file (`cyber_raksha.db`). |
| **ORM / Migration** | **SQLAlchemy** | `2.0.38` | Industry standard Python ORM providing declarative models, connection pooling, and seamless transition path to PostgreSQL. |
| **Data Validation** | **Pydantic** | `2.10.6` | Strict typing and serialization for inbound API request payloads and outbound JSON responses. |
| **Machine Learning Core** | **Scikit-Learn** | `1.6.1` | Efficient, reproducible classical ML implementations (Random Forest, LinearSVC) offering deterministic low-latency offline inference. |
| **Model Serialization** | **Joblib** | `1.4.2` | High-efficiency pipelined serialization for trained scikit-learn models and TF-IDF vectorizers. |
| **Audio Processing** | **Standard Library (`wave`, `struct`) + SciPy** | `Python 3.13` | Zero-dependency extraction of acoustic PCM samples and spectral analysis without requiring proprietary audio SDKs. |
| **Frontend Framework** | **React** | `19.3.1` | Component-based interactive UI with concurrent rendering and hooks. |
| **Build Tool & Bundler** | **Vite** | `8.3.5` | Next-generation frontend tooling offering sub-second Hot Module Replacement (HMR) and optimized tree-shaken production bundles. |
| **Type Safety** | **TypeScript** | `5.9.3` | Static typing across all UI state, API client service calls, and component props to eliminate runtime null pointer exceptions. |
| **Styling & CSS** | **Tailwind CSS** | `4.3.3` | Utility-first styling engine enabling a cohesive dark-mode cybersecurity visual system without CSS bloat. |
| **Icons & Visuals** | **Lucide React** | `1.66.0` | Clean, accessible SVG icon set for cybersecurity indicators, status badges, and action buttons. |
| **Automated Testing** | **Pytest** | `9.2.0` | Standard testing harness for unit, integration, performance, and security hardening suites. |
| **HTTP Test Client** | **HTTPX** | `0.28.1` | Modern HTTP client for synchronous and asynchronous route testing inside the pytest harness. |
| **Browser Extension** | **Chromium Manifest V3** | `MV3` | Native extension architecture compatible with Google Chrome, Microsoft Edge, and Brave. |
| **Mobile Deployment** | **PWA + Web Share Target** | `W3C PWA` | Native Android share sheet integration and offline service worker caching without requiring an app store build. |
| **Containerization** | **Docker & Docker Compose**| `Compose v2` | Multi-stage container builds (`Dockerfile.backend`, `Dockerfile.frontend`) for reproducible cross-platform deployments. |

---

## 2. Separation of Implemented vs Planned/Unused Technologies

### A. Implemented & Operational
- All items in the table above are fully installed, configured, verified in the test suite, and operational in the repository.
- Models are physically present in `ai_engine/models/` and loaded in-process.

### B. Deliberately Excluded Technologies (with Rationale)
1. **Redis / Celery:** Excluded to uphold the zero-budget, lightweight deployment constraint. Job queueing and SSE streaming are handled reliably using Python's built-in `ThreadPoolExecutor` and FastAPI's `BackgroundTasks`.
2. **Proprietary Cloud AI APIs (OpenAI, Anthropic):** Excluded to ensure complete data sovereignty, eliminate per-query API costs, and guarantee offline operational capability.
3. **Heavy Deep Learning Frameworks (TensorFlow, PyTorch):** Excluded for inference to keep server memory footprint under 200MB, allowing Cyber Raksha to run on budget virtual private servers (VPS) and developer laptops.

