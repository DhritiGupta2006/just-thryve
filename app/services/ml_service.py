"""
ML Underwriting Engine — XGBoost + SHAP explainability.

Feature vector (in order):
  0: gst_revenue_3m_avg
  1: gst_revenue_growth_rate
  2: gst_revenue_volatility
  3: renewable_energy_mix        (0-100)
  4: carbon_emissions_per_revenue
  5: compliance_status           (0=compliant, 1=pending, 2=non_compliant)
  6: loan_amount_requested
  7: tenure_months
  8: requested_emi_to_avg_revenue_ratio
  9: sector_type                 (0=renewable, 1=agriculture, 2=commerce)

Output classes: 0=Rejected, 1=ManualReview, 2=Approved
"""
import os
import logging
from typing import Optional

import numpy as np
import joblib

logger = logging.getLogger(__name__)

MODEL_VERSION = "1.0.0"
DEFAULT_ANNUAL_RATE_PCT = 12.0  # default rate used to estimate EMI-to-revenue ratio during feature engineering
FEATURE_NAMES = [
    "gst_revenue_3m_avg",
    "gst_revenue_growth_rate",
    "gst_revenue_volatility",
    "renewable_energy_mix",
    "carbon_emissions_per_revenue",
    "compliance_status",
    "loan_amount_requested",
    "tenure_months",
    "emi_to_revenue_ratio",
    "sector_type",
]

SECTOR_MAP = {"renewable_energy": 0, "agriculture": 1, "commerce": 2}
COMPLIANCE_MAP = {"compliant": 0, "pending": 1, "non_compliant": 2}


class MLService:
    _model = None
    _explainer = None

    def __init__(self, model_path: str = "app/ml/model.pkl"):
        self.model_path = model_path
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                data = joblib.load(self.model_path)
                MLService._model = data["model"]
                MLService._explainer = data.get("explainer")
                logger.info("ML model loaded from %s", self.model_path)
            except Exception as exc:
                logger.warning("Failed to load ML model: %s — will use heuristic fallback", exc)
        else:
            logger.warning("Model file not found at %s — using heuristic fallback", self.model_path)

    def _build_feature_vector(self, features: dict) -> np.ndarray:
        sector = SECTOR_MAP.get(features.get("sector", "commerce"), 2)
        compliance = COMPLIANCE_MAP.get(features.get("compliance_status", "pending"), 1)
        avg_rev = float(features.get("gst_revenue_3m_avg", 0))
        loan_amount = float(features.get("loan_amount_requested", 0))
        tenure = int(features.get("tenure_months", 12))

        from app.services.emi_service import EMIService
        emi = EMIService.calculate_emi(loan_amount, DEFAULT_ANNUAL_RATE_PCT, tenure) if loan_amount > 0 else 0
        emi_ratio = emi / avg_rev if avg_rev > 0 else 1.0

        return np.array(
            [
                avg_rev,
                float(features.get("gst_revenue_growth_rate", 0)),
                float(features.get("gst_revenue_volatility", 0)),
                float(features.get("renewable_energy_mix", 0)),
                float(features.get("carbon_emissions_per_revenue", 0)),
                float(compliance),
                loan_amount,
                float(tenure),
                emi_ratio,
                float(sector),
            ],
            dtype=np.float32,
        )

    def predict(self, features: dict) -> dict:
        """
        Run ML underwriting. Returns decision, risk_score, shap_values, confidence.
        Falls back to heuristic scoring if model is not loaded.
        """
        X = self._build_feature_vector(features).reshape(1, -1)

        if MLService._model is not None:
            return self._model_predict(X, features)
        return self._heuristic_predict(features, X)

    def _model_predict(self, X: np.ndarray, raw_features: dict) -> dict:
        import shap

        proba = MLService._model.predict_proba(X)[0]  # shape: (3,)
        class_idx = int(np.argmax(proba))
        confidence = float(proba[class_idx])

        decision_map = {0: "rejected", 1: "manual_review", 2: "approved"}
        decision = decision_map[class_idx]
        # Map probability of approval to 0-1000 risk score
        approve_prob = float(proba[2])
        risk_score = int(approve_prob * 1000)

        shap_vals = None
        try:
            if MLService._explainer is None:
                MLService._explainer = shap.TreeExplainer(MLService._model)
            sv = MLService._explainer.shap_values(X)
            # XGBoost multi-class: sv shape is (n_samples, n_features, n_classes)
            # Older SHAP versions return a list of (n_samples, n_features) arrays
            if isinstance(sv, np.ndarray) and sv.ndim == 3:
                # (n_samples=1, n_features, n_classes) → pick class of interest
                sv_for_class = sv[0, :, class_idx]
            elif isinstance(sv, list):
                sv_for_class = np.array(sv[class_idx])[0]
            else:
                sv_for_class = sv[0]
            shap_vals = {name: round(float(val), 4) for name, val in zip(FEATURE_NAMES, sv_for_class)}
        except Exception as exc:
            logger.warning("SHAP computation failed: %s", exc)

        return {
            "decision": decision,
            "risk_score": risk_score,
            "confidence": round(confidence, 4),
            "shap_values": shap_vals,
            "model_version": MODEL_VERSION,
            "input_features": {k: float(v) if isinstance(v, (int, float)) else v for k, v in raw_features.items()},
        }

    def _heuristic_predict(self, features: dict, X: np.ndarray) -> dict:
        """Rule-based fallback when no trained model is available."""
        score = 0.0
        avg_rev = float(features.get("gst_revenue_3m_avg", 0))
        loan_amount = float(features.get("loan_amount_requested", 1))
        renewable_mix = float(features.get("renewable_energy_mix", 0))
        compliance = features.get("compliance_status", "pending")
        growth = float(features.get("gst_revenue_growth_rate", 0))

        # Revenue coverage
        if avg_rev > 0:
            coverage = avg_rev / loan_amount
            score += min(coverage * 0.3, 0.3)
        # ESG bonus
        score += renewable_mix / 100 * 0.25
        if compliance == "compliant":
            score += 0.2
        elif compliance == "non_compliant":
            score -= 0.2
        # Revenue growth
        if growth > 10:
            score += 0.15
        elif growth < -10:
            score -= 0.15

        score = max(0.0, min(1.0, score))

        if score >= 0.7:
            decision = "approved"
        elif score >= 0.4:
            decision = "manual_review"
        else:
            decision = "rejected"

        risk_score = int(score * 1000)
        shap_vals = {
            "gst_revenue_3m_avg": round(min(avg_rev / loan_amount * 0.3, 0.3) if loan_amount else 0, 4),
            "renewable_energy_mix": round(renewable_mix / 100 * 0.25, 4),
            "compliance_status": 0.2 if compliance == "compliant" else (-0.2 if compliance == "non_compliant" else 0.0),
            "gst_revenue_growth_rate": 0.15 if growth > 10 else (-0.15 if growth < -10 else 0.0),
        }
        return {
            "decision": decision,
            "risk_score": risk_score,
            "confidence": round(score, 4),
            "shap_values": shap_vals,
            "model_version": "heuristic-1.0",
            "input_features": {k: float(v) if isinstance(v, (int, float)) else v for k, v in features.items()},
        }
