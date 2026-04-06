"""Initial schema — create all tables

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Enum types ---
    op.execute("CREATE TYPE user_role AS ENUM ('borrower', 'lender')")
    op.execute("CREATE TYPE loan_status AS ENUM ('created', 'submitted', 'offers_received', 'accepted', 'disbursed', 'active', 'closed')")
    op.execute("CREATE TYPE consent_type_enum AS ENUM ('bank_statement', 'gst_data', 'energy_usage', 'carbon_audit')")
    op.execute("CREATE TYPE consent_status AS ENUM ('pending', 'granted', 'revoked')")
    op.execute("CREATE TYPE offer_status AS ENUM ('pending', 'accepted', 'rejected', 'expired')")
    op.execute("CREATE TYPE transaction_type AS ENUM ('disbursement', 'emi_payment', 'penalty', 'adjustment')")
    op.execute("CREATE TYPE transaction_status AS ENUM ('initiated', 'success', 'failed')")
    op.execute("CREATE TYPE repayment_status AS ENUM ('pending', 'paid', 'overdue', 'waived')")

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.VARCHAR(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.VARCHAR(255), nullable=False),
        sa.Column("name", sa.VARCHAR(255), nullable=False),
        sa.Column("role", sa.Enum("borrower", "lender", name="user_role", create_type=False), nullable=False),
        sa.Column("kyc_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # --- business_profiles ---
    op.create_table(
        "business_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("business_name", sa.VARCHAR(255), nullable=False),
        sa.Column("sector", sa.VARCHAR(50), nullable=False),
        sa.Column("registration_number", sa.VARCHAR(100), nullable=True),
        sa.Column("gst_number", sa.VARCHAR(50), nullable=True, unique=True),
        sa.Column("avg_gst_revenue_3m", sa.Numeric(18, 2), nullable=True),
        sa.Column("renewable_mix_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("carbon_emissions_tons", sa.Numeric(10, 4), nullable=True),
        sa.Column("compliance_status", sa.VARCHAR(30), nullable=False, server_default="'pending'"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # --- loans ---
    op.create_table(
        "loans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("borrower_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount_requested", sa.Numeric(18, 2), nullable=False),
        sa.Column("purpose", sa.VARCHAR(500), nullable=False),
        sa.Column("tenure_months", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("created", "submitted", "offers_received", "accepted", "disbursed", "active", "closed", name="loan_status", create_type=False), nullable=False, server_default="'created'"),
        sa.Column("approved_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("approved_rate", sa.Numeric(6, 4), nullable=True),
        sa.Column("emi_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("risk_score", sa.Integer(), nullable=True),
        sa.Column("ml_decision", sa.VARCHAR(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("disbursed_at", sa.DateTime(), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
    )

    # --- consents ---
    op.create_table(
        "consents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("consent_type", sa.Enum("bank_statement", "gst_data", "energy_usage", "carbon_audit", name="consent_type_enum", create_type=False), nullable=False),
        sa.Column("status", sa.Enum("pending", "granted", "revoked", name="consent_status", create_type=False), nullable=False, server_default="'pending'"),
        sa.Column("granted_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # --- offers ---
    op.create_table(
        "offers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("loan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("loans.id"), nullable=False),
        sa.Column("lender_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("interest_rate", sa.Numeric(6, 4), nullable=False),
        sa.Column("offered_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("tenure_months", sa.Integer(), nullable=False),
        sa.Column("emi_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("status", sa.Enum("pending", "accepted", "rejected", "expired", name="offer_status", create_type=False), nullable=False, server_default="'pending'"),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # --- transactions ---
    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("loan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("loans.id"), nullable=False),
        sa.Column("type", sa.Enum("disbursement", "emi_payment", "penalty", "adjustment", name="transaction_type", create_type=False), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("status", sa.Enum("initiated", "success", "failed", name="transaction_status", create_type=False), nullable=False, server_default="'initiated'"),
        sa.Column("reference_id", sa.VARCHAR(255), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # --- repayment_schedules ---
    op.create_table(
        "repayment_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("loan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("loans.id"), nullable=False),
        sa.Column("installment_number", sa.Integer(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("principal_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("interest_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("emi_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("status", sa.Enum("pending", "paid", "overdue", "waived", name="repayment_status", create_type=False), nullable=False, server_default="'pending'"),
        sa.Column("paid_on", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # --- ml_audit_log ---
    op.create_table(
        "ml_audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("loan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("loans.id"), nullable=False),
        sa.Column("model_version", sa.VARCHAR(50), nullable=False),
        sa.Column("input_features", postgresql.JSONB(), nullable=False),
        sa.Column("prediction_score", sa.Numeric(6, 4), nullable=False),
        sa.Column("shap_values", postgresql.JSONB(), nullable=True),
        sa.Column("decision", sa.VARCHAR(50), nullable=False),
        sa.Column("confidence", sa.Numeric(6, 4), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("ml_audit_log")
    op.drop_table("repayment_schedules")
    op.drop_table("transactions")
    op.drop_table("offers")
    op.drop_table("consents")
    op.drop_table("loans")
    op.drop_table("business_profiles")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS repayment_status")
    op.execute("DROP TYPE IF EXISTS transaction_status")
    op.execute("DROP TYPE IF EXISTS transaction_type")
    op.execute("DROP TYPE IF EXISTS offer_status")
    op.execute("DROP TYPE IF EXISTS consent_status")
    op.execute("DROP TYPE IF EXISTS consent_type_enum")
    op.execute("DROP TYPE IF EXISTS loan_status")
    op.execute("DROP TYPE IF EXISTS user_role")
