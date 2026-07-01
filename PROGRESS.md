# Progress Tracker — Credit Risk Verification API

- [x] Phase 0 — Scaffolding
- [x] Phase 1 — Data Model & DB
- [x] Phase 2 — Risk Scoring Engine
- [x] Phase 3 — API Endpoints
- [x] Phase 4 — Automated Tests
- [x] Phase 5 — Postman Collection
- [x] Phase 6 — CI/CD
- [ ] Phase 7 — Deployment (Render) — requires user to push to GitHub + connect Render
- [x] Phase 8 — README & Polish

## Notes for next session

### Phase 0 — Scaffolding [DONE]
Full folder structure created. requirements.txt uses unpinned modern versions to get
pre-built cp313 wheels (Python 3.13 on Windows — MSVC not installed, so no source builds).
venv created at credit-risk-api/venv/.

### Phase 1 — Data Model & DB [DONE]
- app/models.py: CreditApplication ORM model with all fields, enums (EmploymentStatus,
  ApplicationStatus, RiskBand), soft-delete via is_deleted, auto timestamps.
- app/database.py: SQLAlchemy engine reading DATABASE_URL from .env; SQLite fallback
  (check_same_thread=False) for local/CI use.
- Alembic initialized; env.py wired to Base.metadata + models; first migration generated
  and applied against SQLite (credit_risk.db).

### Phase 2 — Risk Scoring Engine [DONE]
- app/risk_engine.py: Pure function calculate_risk() → (float, str).
- Weights: 40% credit score band, 35% DTI ratio, 25% employment status.
- Score clamped to [0, 100]; bands: 0-33=LOW, 34-66=MEDIUM, 67-100=HIGH.
- No DB or HTTP deps — fully unit-testable in isolation.

### Phase 3 — API Endpoints [DONE]
- All 6 endpoints in app/routers/applications.py.
- GET /applications/risk-report defined BEFORE /{id} to avoid FastAPI path conflict.
- Global exception handler in main.py — never leaks raw tracebacks.
- Structured error responses: {"error": "...", "detail": "..."}.
- app/crud.py: All DB operations; soft-delete only.
- High-risk (band=HIGH) applications auto-set to status=flagged on creation.

### Phase 4 — Automated Tests [DONE]
- 33 tests, all passing (pytest tests/ -v).
- tests/conftest.py: In-memory SQLite via StaticPool — completely isolated from dev/prod.
- tests/test_risk_engine.py: 13 unit tests (boundaries, employment ordering, range invariant).
- tests/test_applications.py: 20 integration tests via FastAPI TestClient.

### Phase 5 — Postman Collection [DONE]
- postman/credit_risk_api.postman_collection.json: 14 requests covering all endpoints.
- postman/environment.json: base_url variable (swap localhost ↔ Render URL).
- Each request has JS test assertions for status codes, response shape, and business logic.

### Phase 6 — CI/CD [DONE]
- .github/workflows/ci.yml: Triggers on push + PR to main.
- Uses SQLite for CI (no Postgres service needed — keeps workflow simple and fast).
- Steps: checkout → Python 3.11 → pip cache → install → alembic upgrade head → pytest.

### Phase 7 — Deployment [TODO]
Next steps for the user:
1. Create a GitHub repo and push this directory.
2. Go to render.com → New → Web Service → connect the GitHub repo.
3. Render auto-detects render.yaml and creates the web service + managed Postgres DB.
4. Set DATABASE_URL in Render env vars (copy from the managed DB dashboard).
5. Trigger a deploy — Render runs `alembic upgrade head` then starts uvicorn.
6. Update README.md badge URL and live URL placeholders (YOUR_USERNAME, YOUR_SERVICE).

### Phase 8 — README & Polish [DONE]
Full README with: project description, scoring architecture tables, endpoint table,
setup instructions, pytest + newman commands, deployment guide, CI note, project structure.

## Key Decisions
- SQLite for CI/tests: avoids Postgres service complexity; StaticPool keeps connections clean.
- Unpinned requirements: prevents cp313 build failures on Windows without MSVC.
- risk-report before /{id}: FastAPI routes match in definition order — static segments win.
- Soft-delete only: mirrors financial data retention best practices.
