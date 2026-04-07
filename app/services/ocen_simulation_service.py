"""
OCENSimulationService — simulates the Open Credit Enablement Network (OCEN)
protocol for a mock lending network.

In production this would integrate with a real OCEN gateway. Here it provides
deterministic mock responses so the full platform can be developed/tested
without external dependencies.
"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List


# Mock lender registry — represents lenders registered on the OCEN network
_MOCK_LENDERS: List[Dict[str, Any]] = [
    {
        "lender_id": "LENDER-NBFC-001",
        "name": "GreenCapital NBFC",
        "type": "NBFC",
        "specialisation": ["renewable_energy", "agriculture"],
        "min_loan": 50_000,
        "max_loan": 5_000_000,
        "base_rate_pct": 10.5,
        "active": True,
    },
    {
        "lender_id": "LENDER-BANK-002",
        "name": "EcoFirst Bank",
        "type": "Bank",
        "specialisation": ["renewable_energy", "commerce"],
        "min_loan": 100_000,
        "max_loan": 20_000_000,
        "base_rate_pct": 9.75,
        "active": True,
    },
    {
        "lender_id": "LENDER-P2P-003",
        "name": "SustainLend P2P",
        "type": "P2P",
        "specialisation": ["agriculture", "commerce"],
        "min_loan": 25_000,
        "max_loan": 2_000_000,
        "base_rate_pct": 12.0,
        "active": True,
    },
    {
        "lender_id": "LENDER-MFI-004",
        "name": "RuralGreen MFI",
        "type": "MFI",
        "specialisation": ["agriculture"],
        "min_loan": 10_000,
        "max_loan": 500_000,
        "base_rate_pct": 14.0,
        "active": True,
    },
]


class OCENSimulationService:
    NETWORK_ID = "OCEN-GREENFLOW-MOCK-v1"

    @classmethod
    def network_status(cls) -> Dict[str, Any]:
        """Return the current status of the mock OCEN network."""
        return {
            "network_id": cls.NETWORK_ID,
            "status": "operational",
            "protocol_version": "3.0",
            "registered_lenders": len(_MOCK_LENDERS),
            "active_lenders": sum(1 for l in _MOCK_LENDERS if l["active"]),
            "timestamp": datetime.utcnow().isoformat(),
            "features": [
                "loan_discovery",
                "consent_based_data_sharing",
                "digital_disbursement",
                "automated_repayment",
            ],
        }

    @classmethod
    def discover_lenders(
        cls,
        loan_amount: float,
        sector: str = "commerce",
        tenure_months: int = 12,
    ) -> List[Dict[str, Any]]:
        """
        Discover eligible lenders on the OCEN network for a given loan request.

        Filters lenders by amount range and sector specialisation.
        """
        eligible = []
        for lender in _MOCK_LENDERS:
            if not lender["active"]:
                continue
            if loan_amount < lender["min_loan"] or loan_amount > lender["max_loan"]:
                continue
            # Prefer sector-specialised lenders but don't exclude others
            sector_match = sector in lender["specialisation"]
            eligible.append({
                **lender,
                "sector_match": sector_match,
                "indicative_rate_pct": round(
                    lender["base_rate_pct"] * (0.95 if sector_match else 1.0), 2
                ),
                "estimated_emi": cls._estimate_emi(loan_amount, lender["base_rate_pct"], tenure_months),
            })

        # Sort: sector matches first, then by rate
        eligible.sort(key=lambda l: (not l["sector_match"], l["indicative_rate_pct"]))
        return eligible

    @classmethod
    def broadcast_loan_request(cls, loan_id: str, loan_amount: float, sector: str) -> Dict[str, Any]:
        """
        Broadcast a loan request to all eligible lenders on the OCEN network.

        Returns a broadcast receipt with the list of notified lenders.
        """
        eligible = cls.discover_lenders(loan_amount, sector)
        broadcast_id = str(uuid.uuid4())
        notified = [l["lender_id"] for l in eligible]

        return {
            "broadcast_id": broadcast_id,
            "loan_id": loan_id,
            "notified_lender_count": len(notified),
            "notified_lenders": notified,
            "broadcast_at": datetime.utcnow().isoformat(),
            "response_deadline": (datetime.utcnow() + timedelta(hours=48)).isoformat(),
            "status": "broadcasted",
        }

    @staticmethod
    def _estimate_emi(principal: float, annual_rate_pct: float, tenure_months: int) -> float:
        if tenure_months <= 0 or annual_rate_pct <= 0:
            return round(principal / max(tenure_months, 1), 2)
        r = annual_rate_pct / 12 / 100
        factor = (1 + r) ** tenure_months
        return round(principal * r * factor / (factor - 1), 2)
