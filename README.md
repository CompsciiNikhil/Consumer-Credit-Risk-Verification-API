# Consumer Credit Risk Verification API

[![CI](https://github.com/CompsciiNikhil/Consumer-Credit-Risk-Verification-API/actions/workflows/ci.yml/badge.svg)](https://github.com/CompsciiNikhil/Consumer-Credit-Risk-Verification-API/actions/workflows/ci.yml)

> 🚀 **Live:** [consumer-credit-risk-verification-api.onrender.com](https://consumer-credit-risk-verification-api.onrender.com) · **Docs:** [/docs](https://consumer-credit-risk-verification-api.onrender.com/docs) · **Repo:** [GitHub](https://github.com/CompsciiNikhil/Consumer-Credit-Risk-Verification-API)

> A production-grade backend REST API that ingests consumer credit applications, applies a **transparent, rule-based risk scoring engine**, and exposes an auditable, testable service — mirroring the type of consumer-data-to-risk-signal pipeline that credit information companies (like TransUnion) operate.

---

## Project Description

This API models a consumer credit risk verification workflow. When a credit application is submitted, the system validates the applicant's data, runs it through a deterministic scoring engine, and returns a numeric **risk score (0–100)** and a categorical **risk band (LOW / MEDIUM / HIGH)**. High-risk applications are automatically flagged for analyst review. All records use soft-delete so financial history is never physically removed — mirroring real-world data retention requirements.

The scoring logic is intentionally **rule-based and transparent** — not a black-box ML model. Every factor, weight, and threshold is documented in code and can be audited, debugged, or explained to a regulator without retraining anything. This is a deliberate architectural choice, not a limitation.

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI (Python 3.11+) |
| Database | PostgreSQL (production) / SQLite (CI & tests) |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Testing | PyTest + httpx TestClient |
| API Testing | Postman / Newman |
| CI/CD | GitHub Actions |
| Deployment | Render (free tier) |

---

## Risk Scoring Architecture

The scoring engine (`app/risk_engine.py`) is a **pure function** — no database or HTTP dependencies — making it independently unit-testable.

### Formula (weighted, 0–100 scale, higher = riskier)

```
risk_score = (credit_score_component × 0.40)
           + (dti_component           × 0.35)
           + (employment_component    × 0.25)
```

| Component | Weight | Thresholds |
|---|---|---|
| **Credit Score** | 40% | 740+ → 5pts · 670–739 → 20pts · 580–669 → 50pts · <580 → 85pts |
| **Debt-to-Income (DTI)** | 35% | DTI <0.30 → 5pts · 0.30–0.50 → 45pts · >0.50 → 90pts |
| **Employment Status** | 25% | employed → 5pts · self_employed → 45pts · unemployed → 90pts |

### Risk Band Mapping

| Score Range | Band | Auto Status |
|---|---|---|
| 0 – 33 | `LOW` | `pending` |
| 34 – 66 | `MEDIUM` | `pending` |
| 67 – 100 | `HIGH` | `flagged` (auto) |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/applications` | Submit a credit application |
| `GET` | `/applications` | List all (supports `?status=` and `?risk_band=` filters) |
| `GET` | `/applications/{id}` | Get a single application |
| `PUT` | `/applications/{id}/review` | Analyst review — set status to `approved` or `rejected` |
| `DELETE` | `/applications/{id}` | Soft-delete (record retained, never hard-deleted) |
| `GET` | `/applications/risk-report` | Filter by `?min_score=` / `?max_score=`, sorted by risk desc |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Interactive Swagger UI |

All error responses follow a consistent structured format:
```json
{ "error": "Not Found", "detail": "Application 99 not found" }
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- PostgreSQL (for production use) — SQLite works out of the box for local dev

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/CompsciiNikhil/Consumer-Credit-Risk-Verification-API.git
cd Consumer-Credit-Risk-Verification-API

# 2. Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and set your DATABASE_URL
# For SQLite (no Postgres needed locally):
#   DATABASE_URL=sqlite:///./credit_risk.db

# 5. Run database migrations
alembic upgrade head

# 6. Start the development server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

---

## Running Tests

### PyTest (unit + integration — uses in-memory SQLite, no Postgres required)

```bash
pytest tests/ -v
```

Expected output: **33 tests passing** across two files:
- `tests/test_risk_engine.py` — 13 pure unit tests (no DB, no HTTP)
- `tests/test_applications.py` — 20 integration tests via FastAPI TestClient

### Postman / Newman (API-level tests against a running server)

```bash
# Install Newman globally
npm install -g newman

# Start the server first (in a separate terminal)
uvicorn app.main:app --reload

# Run the collection
newman run postman/credit_risk_api.postman_collection.json \
  --environment postman/environment.json
```

To test against the deployed Render URL, update `base_url` in `postman/environment.json`.

---

## Deployment (Render)

The `render.yaml` in the repo root defines:
- A **Web Service** running `uvicorn app.main:app`
- A **managed PostgreSQL** instance

**Deploy steps:**
1. Push repo to GitHub
2. Connect the repo to [Render](https://render.com)
3. Set `DATABASE_URL` environment variable in Render dashboard (use the managed DB connection string)
4. Render runs `alembic upgrade head` then starts the server automatically

**Live URL:** https://consumer-credit-risk-verification-api.onrender.com  
**Swagger UI:** https://consumer-credit-risk-verification-api.onrender.com/docs

---

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`) triggers on every push and pull request to `main`:

1. Checkout code
2. Set up Python 3.11
3. Cache pip dependencies
4. Install from `requirements.txt`
5. Run Alembic migrations (against SQLite for CI — no Postgres service needed)
6. Run `pytest` — build fails on any test failure

> **Note on CI database choice:** SQLite is used in CI for simplicity and speed. The application automatically detects `sqlite://` URLs and applies the correct driver settings (`check_same_thread=False`, `StaticPool`). Production deployments use PostgreSQL via Render's managed database.

---

## Project Structure

```
credit-risk-api/
├── app/
│   ├── main.py           # FastAPI app, global error handler
│   ├── models.py         # SQLAlchemy ORM model
│   ├── schemas.py        # Pydantic request/response schemas
│   ├── database.py       # Engine, session, Base
│   ├── crud.py           # DB operations (all soft-delete)
│   ├── risk_engine.py    # Pure scoring function (no DB/HTTP deps)
│   └── routers/
│       └── applications.py  # All 6 endpoints
├── tests/
│   ├── conftest.py          # In-memory SQLite fixtures
│   ├── test_risk_engine.py  # Unit tests
│   └── test_applications.py # Integration tests
├── alembic/              # Migration scripts
├── postman/              # Postman collection + environment
├── .github/workflows/    # CI pipeline
├── render.yaml           # Render deployment config
└── PROGRESS.md           # Phase-by-phase build log
```
