"""
test_applications.py — Integration tests for all 6 API endpoints.
Uses an in-memory SQLite DB via the `client` fixture (see conftest.py).
Tests never touch dev/prod data.
"""
import pytest
from tests.conftest import high_risk_payload, low_risk_payload, medium_risk_payload


# ===========================================================================
# POST /applications
# ===========================================================================

def test_create_application_happy_path(client):
    """Test 6: Create application — 201, risk fields populated."""
    resp = client.post("/applications", json=low_risk_payload())
    assert resp.status_code == 201
    data = resp.json()
    assert data["applicant_name"] == "Alice Smith"
    assert data["risk_score"] is not None
    assert data["risk_band"] is not None
    assert data["status"] in ("pending", "flagged", "approved", "rejected")
    assert data["id"] is not None


def test_create_application_invalid_credit_score(client):
    """Test 7: credit_score outside 300–850 → 422 Unprocessable Entity."""
    payload = low_risk_payload()
    payload["credit_score"] = 200  # below minimum
    resp = client.post("/applications", json=payload)
    assert resp.status_code == 422


def test_create_application_missing_required_field(client):
    """Test 8: Missing applicant_name → 422 Unprocessable Entity."""
    payload = low_risk_payload()
    del payload["applicant_name"]
    resp = client.post("/applications", json=payload)
    assert resp.status_code == 422


def test_create_application_high_risk_auto_flagged(client):
    """Test 9: HIGH risk band automatically sets status to 'flagged'."""
    resp = client.post("/applications", json=high_risk_payload())
    assert resp.status_code == 201
    data = resp.json()
    assert data["risk_band"] == "HIGH"
    assert data["status"] == "flagged"


def test_create_application_low_risk_pending(client):
    """LOW risk application should be set to 'pending' (not flagged)."""
    resp = client.post("/applications", json=low_risk_payload())
    assert resp.status_code == 201
    data = resp.json()
    assert data["risk_band"] == "LOW"
    assert data["status"] == "pending"


def test_create_application_zero_income_rejected(client):
    """annual_income must be > 0 — zero should return 422."""
    payload = low_risk_payload()
    payload["annual_income"] = 0
    resp = client.post("/applications", json=payload)
    assert resp.status_code == 422


def test_create_application_negative_debt_rejected(client):
    """existing_debt must be >= 0 — negative should return 422."""
    payload = low_risk_payload()
    payload["existing_debt"] = -500
    resp = client.post("/applications", json=payload)
    assert resp.status_code == 422


# ===========================================================================
# GET /applications/{id}
# ===========================================================================

def test_get_application_happy_path(client):
    """Test 10: Get by ID — 200 and correct data returned."""
    created = client.post("/applications", json=low_risk_payload()).json()
    resp = client.get(f"/applications/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_application_not_found(client):
    """Test 11: Non-existent ID → 404 with structured error."""
    resp = client.get("/applications/99999")
    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data


# ===========================================================================
# GET /applications
# ===========================================================================

def test_list_applications_filter_by_status(client):
    """Test 12: Filter by status=flagged returns only HIGH-risk (flagged) records."""
    client.post("/applications", json=low_risk_payload())   # pending
    client.post("/applications", json=high_risk_payload())  # flagged

    resp = client.get("/applications?status=flagged")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert all(r["status"] == "flagged" for r in results)


def test_list_applications_filter_by_risk_band(client):
    """Test 13: Filter by risk_band=LOW returns only LOW-risk records."""
    client.post("/applications", json=low_risk_payload())
    client.post("/applications", json=high_risk_payload())

    resp = client.get("/applications?risk_band=LOW")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert all(r["risk_band"] == "LOW" for r in results)


def test_list_applications_excludes_deleted(client):
    """Soft-deleted records must not appear in the list."""
    created = client.post("/applications", json=low_risk_payload()).json()
    client.delete(f"/applications/{created['id']}")

    resp = client.get("/applications")
    ids = [r["id"] for r in resp.json()]
    assert created["id"] not in ids


# ===========================================================================
# PUT /applications/{id}/review
# ===========================================================================

def test_review_application_happy_path(client):
    """Test 14: Analyst approves an application — status changes to approved."""
    created = client.post("/applications", json=low_risk_payload()).json()
    resp = client.put(
        f"/applications/{created['id']}/review",
        json={"status": "approved"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"


def test_review_application_not_found(client):
    """Test 15: Review on non-existent ID → 404."""
    resp = client.put("/applications/99999/review", json={"status": "approved"})
    assert resp.status_code == 404


def test_review_application_invalid_status(client):
    """Status 'pending' is not a valid review target — should return 422."""
    created = client.post("/applications", json=low_risk_payload()).json()
    resp = client.put(
        f"/applications/{created['id']}/review",
        json={"status": "pending"},
    )
    assert resp.status_code == 422


# ===========================================================================
# DELETE /applications/{id}
# ===========================================================================

def test_soft_delete_then_excluded_from_list(client):
    """Test 16: Soft delete returns 204; record excluded from subsequent GET list."""
    created = client.post("/applications", json=low_risk_payload()).json()
    app_id = created["id"]

    # Delete returns 204
    del_resp = client.delete(f"/applications/{app_id}")
    assert del_resp.status_code == 204

    # GET list no longer includes it
    list_resp = client.get("/applications")
    ids = [r["id"] for r in list_resp.json()]
    assert app_id not in ids

    # GET by ID also returns 404
    get_resp = client.get(f"/applications/{app_id}")
    assert get_resp.status_code == 404


def test_delete_not_found(client):
    """Delete on non-existent ID → 404."""
    resp = client.delete("/applications/99999")
    assert resp.status_code == 404


# ===========================================================================
# GET /applications/risk-report
# ===========================================================================

def test_risk_report_filter_by_min_max_score(client):
    """Test 17: Risk report filters correctly by min_score and max_score."""
    client.post("/applications", json=low_risk_payload())    # LOW  ~5–15
    client.post("/applications", json=high_risk_payload())   # HIGH ~67–90
    client.post("/applications", json=medium_risk_payload()) # MEDIUM ~34–66

    # Request only HIGH-risk range
    resp = client.get("/applications/risk-report?min_score=67&max_score=100")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert all(r["risk_score"] >= 67 for r in results)


def test_risk_report_sorted_descending(client):
    """Risk report results must be sorted by risk_score descending."""
    client.post("/applications", json=low_risk_payload())
    client.post("/applications", json=high_risk_payload())
    client.post("/applications", json=medium_risk_payload())

    resp = client.get("/applications/risk-report")
    assert resp.status_code == 200
    scores = [r["risk_score"] for r in resp.json()]
    assert scores == sorted(scores, reverse=True)


def test_risk_report_invalid_range(client):
    """min_score > max_score → 400 Bad Request."""
    resp = client.get("/applications/risk-report?min_score=80&max_score=20")
    assert resp.status_code == 400
