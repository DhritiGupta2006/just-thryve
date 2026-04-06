"""
Mock Account Aggregator (AA) consent flow simulation.
In production this would integrate with a real AA gateway (e.g. Sahamati/ONEMONEY).
"""
import uuid
from datetime import datetime, timedelta
from typing import Any


class AAService:
    AA_REDIRECT_BASE = "https://mock-aa-gateway.greenflowcredit.dev/consent"

    @staticmethod
    def initiate_consent(user_id: str, consent_type: str, loan_id: str) -> dict:
        """Simulate sending a consent request to the AA gateway."""
        consent_handle = str(uuid.uuid4())
        redirect_url = f"{AAService.AA_REDIRECT_BASE}?handle={consent_handle}&type={consent_type}&loan={loan_id}"
        return {
            "consent_handle": consent_handle,
            "redirect_url": redirect_url,
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        }

    @staticmethod
    def simulate_grant(consent_type: str) -> dict:
        """
        Simulate the AA callback after user grants consent.
        Returns a mock consent artefact.
        """
        artefact: dict[str, Any] = {
            "artefact_id": str(uuid.uuid4()),
            "consent_type": consent_type,
            "granted_at": datetime.utcnow().isoformat(),
            "valid_until": (datetime.utcnow() + timedelta(days=180)).isoformat(),
            "data_provider": "mock-bank/gst-portal/discom",
            "signature": "mock-digital-signature-" + str(uuid.uuid4())[:8],
        }

        # Add type-specific mock data
        if consent_type == "bank_statement":
            artefact["bank_data"] = {
                "account_number": "XXXX1234",
                "avg_balance_3m": 250000.0,
                "transactions_count": 45,
            }
        elif consent_type == "gst_data":
            artefact["gst_data"] = {
                "gst_number": "29ABCDE1234F1Z5",
                "filing_status": "regular",
                "avg_turnover_3m": 500000.0,
            }
        elif consent_type == "energy_usage":
            artefact["energy_data"] = {
                "utility_id": "BESCOM-12345",
                "monthly_units_kwh": 1200,
                "solar_generation_kwh": 400,
            }
        elif consent_type == "carbon_audit":
            artefact["carbon_data"] = {
                "audit_id": str(uuid.uuid4()),
                "emissions_tons_year": 12.5,
                "offset_tons_year": 4.0,
                "net_emissions": 8.5,
            }
        return artefact

    @staticmethod
    def check_status(consent_handle: str) -> str:
        """
        In a real system this polls the AA gateway. Here we always return 'granted'
        for demonstration; in tests you can override this.
        """
        return "granted"
