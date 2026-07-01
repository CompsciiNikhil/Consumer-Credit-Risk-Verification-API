"""
test_risk_engine.py — Unit tests for the pure risk scoring engine.
No database or HTTP dependency — tests the function directly.
"""
import pytest
from app.risk_engine import calculate_risk


# ---------------------------------------------------------------------------
# 1. High credit score + low debt + employed → LOW risk
# ---------------------------------------------------------------------------
def test_low_risk_profile():
    score, band = calculate_risk(
        annual_income=120000.0,
        existing_debt=10000.0,
        credit_score=780,
        employment_status="employed",
    )
    assert band == "LOW"
    assert 0.0 <= score <= 33.0


# ---------------------------------------------------------------------------
# 2. Low credit score + high debt + unemployed → HIGH risk
# ---------------------------------------------------------------------------
def test_high_risk_profile():
    score, band = calculate_risk(
        annual_income=30000.0,
        existing_debt=25000.0,
        credit_score=520,
        employment_status="unemployed",
    )
    assert band == "HIGH"
    assert score > 66.0


# ---------------------------------------------------------------------------
# 3. Mid-range values → MEDIUM risk
# ---------------------------------------------------------------------------
def test_medium_risk_profile():
    score, band = calculate_risk(
        annual_income=60000.0,
        existing_debt=20000.0,  # DTI = 0.33 → medium
        credit_score=640,        # 580–669 → medium
        employment_status="self_employed",  # medium
    )
    assert band == "MEDIUM"
    assert 34.0 <= score <= 66.0


# ---------------------------------------------------------------------------
# 4. Edge case: exactly at credit score band boundaries
# ---------------------------------------------------------------------------
def test_credit_score_boundary_580():
    """580 is the bottom of the medium band — should be medium component."""
    score_580, _ = calculate_risk(60000, 0, 580, "employed")
    score_579, _ = calculate_risk(60000, 0, 579, "employed")
    # 579 is high-risk credit band, should score higher than 580
    assert score_579 > score_580


def test_credit_score_boundary_670():
    """670 is the bottom of the low-medium band."""
    score_670, _ = calculate_risk(60000, 0, 670, "employed")
    score_669, _ = calculate_risk(60000, 0, 669, "employed")
    assert score_669 > score_670


def test_credit_score_boundary_740():
    """740 is the threshold for the lowest risk band."""
    score_740, band_740 = calculate_risk(120000, 0, 740, "employed")
    score_739, band_739 = calculate_risk(120000, 0, 739, "employed")
    assert score_739 > score_740


# ---------------------------------------------------------------------------
# 5. Edge case: zero existing debt → lowest possible DTI component
# ---------------------------------------------------------------------------
def test_zero_existing_debt():
    score, band = calculate_risk(
        annual_income=80000.0,
        existing_debt=0.0,
        credit_score=750,
        employment_status="employed",
    )
    assert band == "LOW"
    # With zero debt, DTI=0 → lowest DTI risk
    assert score <= 33.0


# ---------------------------------------------------------------------------
# 6. DTI boundary: exactly 0.30 (border of low vs medium)
# ---------------------------------------------------------------------------
def test_dti_boundary_030():
    """DTI of exactly 0.30 should hit the medium band (0.30–0.50 range)."""
    score_medium_dti, _ = calculate_risk(100000, 30000, 750, "employed")  # DTI=0.30
    score_low_dti, _ = calculate_risk(100000, 29999, 750, "employed")     # DTI<0.30
    assert score_medium_dti > score_low_dti


# ---------------------------------------------------------------------------
# 7. DTI boundary: exactly 0.50 (border of medium vs high)
# ---------------------------------------------------------------------------
def test_dti_boundary_050():
    """DTI > 0.50 should push into the high DTI component."""
    score_high_dti, _ = calculate_risk(100000, 50001, 750, "employed")  # DTI>0.50
    score_med_dti, _ = calculate_risk(100000, 50000, 750, "employed")   # DTI=0.50
    assert score_high_dti > score_med_dti


# ---------------------------------------------------------------------------
# 8. Score is always in range [0, 100]
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("credit_score,income,debt,employment", [
    (300, 1.0, 0.0, "unemployed"),
    (850, 1000000.0, 0.0, "employed"),
    (580, 50000.0, 40000.0, "self_employed"),
])
def test_score_always_in_range(credit_score, income, debt, employment):
    score, band = calculate_risk(income, debt, credit_score, employment)
    assert 0.0 <= score <= 100.0
    assert band in ("LOW", "MEDIUM", "HIGH")


# ---------------------------------------------------------------------------
# 9. Employment status drives risk correctly
# ---------------------------------------------------------------------------
def test_employment_status_ordering():
    """Unemployed should always score higher than employed, all else equal."""
    score_employed, _ = calculate_risk(60000, 5000, 700, "employed")
    score_self, _ = calculate_risk(60000, 5000, 700, "self_employed")
    score_unemployed, _ = calculate_risk(60000, 5000, 700, "unemployed")
    assert score_employed < score_self < score_unemployed
