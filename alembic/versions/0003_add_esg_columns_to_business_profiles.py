"""Add waste_recycled_percent and social_impact_score to business_profiles

Revision ID: 0003
Revises: 0002
Create Date: 2024-01-03 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "business_profiles",
        sa.Column("waste_recycled_percent", sa.Numeric(5, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "business_profiles",
        sa.Column("social_impact_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("business_profiles", "social_impact_score")
    op.drop_column("business_profiles", "waste_recycled_percent")
