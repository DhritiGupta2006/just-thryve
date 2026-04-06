"""Unit tests for EMIService — no database required."""
import pytest

from app.services.emi_service import EMIService


class TestCalculateEMI:
    def test_standard_emi(self):
        # ₹1,00,000 at 12% p.a. for 12 months → EMI ≈ ₹8,884.88
        emi = EMIService.calculate_emi(100_000, 12.0, 12)
        assert emi == pytest.approx(8884.88, rel=1e-3)

    def test_zero_interest_rate(self):
        # Interest-free: EMI = principal / tenure
        emi = EMIService.calculate_emi(60_000, 0.0, 12)
        assert emi == pytest.approx(5000.0, rel=1e-6)

    def test_single_month_tenure(self):
        emi = EMIService.calculate_emi(10_000, 10.0, 1)
        # One month: entire principal + one month interest
        expected = 10_000 * (10 / 12 / 100) * (1 + 10 / 12 / 100) / ((1 + 10 / 12 / 100) - 1)
        assert emi == pytest.approx(expected, rel=1e-3)

    def test_invalid_tenure_raises(self):
        with pytest.raises(ValueError, match="Tenure must be positive"):
            EMIService.calculate_emi(100_000, 12.0, 0)

    def test_negative_tenure_raises(self):
        with pytest.raises(ValueError, match="Tenure must be positive"):
            EMIService.calculate_emi(100_000, 12.0, -5)


class TestGenerateAmortizationSchedule:
    def test_schedule_length(self):
        schedule = EMIService.generate_amortization_schedule(100_000, 12.0, 6)
        assert len(schedule) == 6

    def test_schedule_installment_numbers(self):
        schedule = EMIService.generate_amortization_schedule(50_000, 10.0, 4)
        numbers = [item["installment_number"] for item in schedule]
        assert numbers == [1, 2, 3, 4]

    def test_total_principal_equals_loan(self):
        principal = 100_000.0
        schedule = EMIService.generate_amortization_schedule(principal, 12.0, 12)
        total_principal = sum(item["principal_amount"] for item in schedule)
        assert total_principal == pytest.approx(principal, rel=1e-3)

    def test_emi_amount_consistent(self):
        schedule = EMIService.generate_amortization_schedule(200_000, 15.0, 24)
        # All but the last installment should have the same EMI
        emis = [item["emi_amount"] for item in schedule[:-1]]
        assert max(emis) - min(emis) < 0.02  # rounding tolerance

    def test_each_row_has_required_keys(self):
        schedule = EMIService.generate_amortization_schedule(50_000, 8.0, 3)
        for row in schedule:
            assert "installment_number" in row
            assert "principal_amount" in row
            assert "interest_amount" in row
            assert "emi_amount" in row

    def test_interest_decreases_over_time(self):
        schedule = EMIService.generate_amortization_schedule(100_000, 12.0, 12)
        interests = [item["interest_amount"] for item in schedule]
        # Each month's interest should be less than or equal to the previous
        for i in range(1, len(interests)):
            assert interests[i] <= interests[i - 1] + 0.02  # allow tiny rounding drift
