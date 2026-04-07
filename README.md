# JUST THRYVE — OCEN-based Green Business Lending Platform

A production-ready full-stack fintech platform built with **FastAPI**, **PostgreSQL**, **XGBoost ML**, and Account Aggregator (AA) consent simulation. Designed for green businesses in renewable energy, sustainable agriculture, and eco-commerce.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **API** | FastAPI + Uvicorn (ASGI) |
| **ORM** | SQLAlchemy 2.0 + Alembic migrations |
| **Database** | PostgreSQL 14+ |
| **Cache / Rate-limit** | Redis |
| **Auth** | JWT (python-jose) + bcrypt |
| **Validation** | Pydantic v2 |
| **ML Underwriting** | XGBoost 2.0 + SHAP explainability |
| **Preprocessing** | scikit-learn + numpy + pandas |
| **Model storage** | joblib (.pkl) |
| **Config** | python-dotenv / pydantic-settings |

---

## Project Structure

```
.
├── app/
│   ├── main.py              # FastAPI app, middleware, lifespan
│   ├── config.py            # Settings (env vars)
│   ├── database.py          # SQLAlchemy engine + session
│   ├── models/              # ORM models (8 tables)
│   │   ├── user.py
│   │   ├── business_profile.py
│   │   ├── loan.py
│   │   ├── consent.py
│   │   ├── offer.py
│   │   ├── transaction.py
│   │   ├── repayment_schedule.py
│   │   └── ml_audit_log.py
│   ├── schemas/             # Pydantic request/response schemas
│   ├── routers/             # FastAPI route handlers
│   │   ├── auth.py          # POST /auth/signup, /auth/login
│   │   ├── loans.py         # Loan lifecycle APIs
│   │   ├── consent.py       # AA consent simulation
│   │   ├── offers.py        # Lender offer management
│   │   └── repayment.py     # Schedule & payment APIs
│   ├── services/
│   │   ├── auth_service.py  # JWT + password hashing
│   │   ├── ml_service.py    # XGBoost inference + SHAP
│   │   ├── emi_service.py   # Reducing-balance EMI engine
│   │   └── aa_service.py    # Mock AA consent flow
│   └── ml/
│       └── train_model.py   # XGBoost training script
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial_schema.py
├── alembic.ini
├── requirements.txt
├── .env.example
└── README.md
```

---

## Quick Start

### 1. Clone & install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your PostgreSQL and Redis connection strings
```

### 3. Run database migrations

```bash
alembic upgrade head
```

### 4. (Optional) Train the ML model

```bash
python -m app.ml.train_model
```

> If no model file is found, the API uses a rule-based heuristic fallback automatically.

### 5. Start the API server

```bash
uvicorn app.main:app --reload
```

API docs available at: http://localhost:8000/docs

---

## Database Schema

| Table | Description |
|-------|-------------|
| `users` | Borrowers & Lenders with JWT auth |
| `business_profiles` | Green business details + ESG metrics |
| `loans` | Full loan lifecycle (created → closed) |
| `consents` | AA consent artefacts (bank, GST, energy, carbon) |
| `offers` | Lender offers with EMI calculation |
| `transactions` | Disbursements, EMI payments, adjustments |
| `repayment_schedules` | Amortization schedule per loan |
| `ml_audit_log` | XGBoost prediction audit trail with SHAP values |

---

## Core API Endpoints

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/signup` | Register borrower or lender |
| POST | `/auth/login` | Obtain JWT token |

### Loan Lifecycle
| Method | Path | Description |
|--------|------|-------------|
| POST | `/loans/apply` | Create loan application |
| POST | `/loans/{id}/submit` | Submit for ML underwriting |
| GET  | `/loans/{id}` | Get loan details + risk score |
| POST | `/loans/{id}/accept-offer/{offer_id}` | Accept a lender offer |
| POST | `/loans/{id}/disburse` | Disburse accepted loan |

### Consent (AA Simulation)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/consent/grant` | Grant consent (bank, GST, energy, carbon) |
| GET  | `/consent/{id}/status` | Check consent status + artefact |

### Offers
| Method | Path | Description |
|--------|------|-------------|
| GET  | `/offers?loan_id=...` | List offers for a loan |
| POST | `/offers` | Lender creates offer (with EMI auto-calc) |

### Repayment
| Method | Path | Description |
|--------|------|-------------|
| GET  | `/repayment/schedule?loan_id=...` | View amortization schedule |
| POST | `/repayment/pay` | Record EMI payment |

---

## ML Underwriting Engine

The XGBoost model uses **10 features** across GST revenue, ESG metrics, and loan parameters to produce a 3-class decision:

| Class | Score | Decision |
|-------|-------|----------|
| 2 | ≥ 0.7 | **Approved** |
| 1 | 0.4–0.7 | **Manual Review** |
| 0 | < 0.4 | **Rejected** |

SHAP values provide per-feature attribution for every decision, stored in `ml_audit_log`.

---

## EMI Calculation

Uses the standard **reducing-balance** formula:

```
EMI = P × r × (1+r)^n / ((1+r)^n − 1)
```

where `r` = monthly rate and `n` = tenure in months. Full amortization schedules are generated on disbursement.

---

## Security

- Passwords hashed with **bcrypt**
- All protected endpoints use **Bearer JWT** tokens
- Role-based access control (**borrower** vs **lender**)
- CORS restricted to `[]` in non-development environments
- Global exception handler prevents stack-trace leakage

