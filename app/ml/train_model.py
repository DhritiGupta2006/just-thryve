"""
Train the XGBoost underwriting model and save it as model.pkl.
Run: python -m app.ml.train_model
"""
import os
import logging
import numpy as np
import joblib
import shap
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Label: 0=Rejected, 1=ManualReview, 2=Approved
LABELS = [0, 1, 2]


def generate_synthetic_data(n_samples: int = 5000):
    np.random.seed(42)

    gst_revenue = np.random.exponential(500_000, n_samples)
    gst_growth = np.random.normal(15, 30, n_samples)
    gst_volatility = np.abs(np.random.normal(0, 50_000, n_samples))
    renewable_mix = np.random.randint(0, 101, n_samples).astype(float)
    carbon_intensity = np.random.exponential(0.05, n_samples)
    compliance = np.random.choice([0, 1, 2], n_samples, p=[0.6, 0.3, 0.1])
    loan_amount = np.random.uniform(100_000, 5_000_000, n_samples)
    tenure = np.random.choice([6, 12, 18, 24, 36, 48, 60], n_samples).astype(float)
    monthly_rate = 0.01
    emi_to_revenue = (
        loan_amount * monthly_rate * (1 + monthly_rate) ** tenure /
        ((1 + monthly_rate) ** tenure - 1) / (gst_revenue / 12 + 1e-6)
    )
    sector = np.random.choice([0, 1, 2], n_samples).astype(float)

    X = np.column_stack([
        gst_revenue, gst_growth, gst_volatility, renewable_mix,
        carbon_intensity, compliance.astype(float), loan_amount,
        tenure, emi_to_revenue, sector,
    ]).astype(np.float32)

    # Rule-based labeling for synthetic data
    score = np.zeros(n_samples)
    score += np.clip(gst_revenue / (loan_amount + 1e-6) * 0.3, 0, 0.3)
    score += renewable_mix / 100 * 0.25
    score += np.where(compliance == 0, 0.2, np.where(compliance == 2, -0.2, 0.0))
    score += np.where(gst_growth > 10, 0.15, np.where(gst_growth < -10, -0.15, 0.0))
    score += np.where(emi_to_revenue < 0.3, 0.1, np.where(emi_to_revenue > 0.6, -0.1, 0.0))
    score = np.clip(score + np.random.normal(0, 0.05, n_samples), 0, 1)

    y = np.where(score >= 0.7, 2, np.where(score >= 0.4, 1, 0))
    return X, y


def train():
    logger.info("Generating synthetic training data …")
    X, y = generate_synthetic_data(5000)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = XGBClassifier(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        use_label_encoder=False,
        eval_metric="mlogloss",
        random_state=42,
        n_jobs=-1,
    )
    logger.info("Training XGBoost model …")
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    y_pred = model.predict(X_test)
    logger.info("Classification Report:\n%s", classification_report(y_test, y_pred, target_names=["Rejected", "ManualReview", "Approved"]))

    logger.info("Building SHAP TreeExplainer …")
    explainer = shap.TreeExplainer(model)

    os.makedirs("app/ml", exist_ok=True)
    model_path = "app/ml/model.pkl"
    joblib.dump({"model": model, "explainer": explainer, "feature_names": FEATURE_NAMES}, model_path)
    logger.info("Model saved to %s", model_path)


if __name__ == "__main__":
    train()
