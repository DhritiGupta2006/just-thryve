"""Add performance indexes on frequently queried columns

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-02 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # loans — most-queried filter columns
    op.create_index("ix_loans_borrower_id", "loans", ["borrower_id"])
    op.create_index("ix_loans_status", "loans", ["status"])

    # offers — joins from loans and lookups by lender
    op.create_index("ix_offers_loan_id", "offers", ["loan_id"])
    op.create_index("ix_offers_lender_id", "offers", ["lender_id"])
    op.create_index("ix_offers_status", "offers", ["status"])

    # consents — looked up by user and type frequently
    op.create_index("ix_consents_user_id", "consents", ["user_id"])
    op.create_index("ix_consents_status", "consents", ["status"])

    # repayment_schedules — ordered queries by loan + installment number
    op.create_index("ix_repayment_loan_id", "repayment_schedules", ["loan_id"])
    op.create_index(
        "ix_repayment_loan_status",
        "repayment_schedules",
        ["loan_id", "status"],
    )

    # transactions — audit queries by loan
    op.create_index("ix_transactions_loan_id", "transactions", ["loan_id"])

    # ml_audit_log — queries by loan
    op.create_index("ix_ml_audit_log_loan_id", "ml_audit_log", ["loan_id"])

    # business_profiles — looked up by user_id on loan submission
    op.create_index("ix_business_profiles_user_id", "business_profiles", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_business_profiles_user_id", table_name="business_profiles")
    op.drop_index("ix_ml_audit_log_loan_id", table_name="ml_audit_log")
    op.drop_index("ix_transactions_loan_id", table_name="transactions")
    op.drop_index("ix_repayment_loan_status", table_name="repayment_schedules")
    op.drop_index("ix_repayment_loan_id", table_name="repayment_schedules")
    op.drop_index("ix_consents_status", table_name="consents")
    op.drop_index("ix_consents_user_id", table_name="consents")
    op.drop_index("ix_offers_status", table_name="offers")
    op.drop_index("ix_offers_lender_id", table_name="offers")
    op.drop_index("ix_offers_loan_id", table_name="offers")
    op.drop_index("ix_loans_status", table_name="loans")
    op.drop_index("ix_loans_borrower_id", table_name="loans")
