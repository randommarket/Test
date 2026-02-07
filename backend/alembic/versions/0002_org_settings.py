"""org settings

Revision ID: 0002_org_settings
Revises: 0001_init
Create Date: 2024-01-02 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_org_settings"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organization_settings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, sa.ForeignKey("organizations.id"), nullable=False, unique=True),
        sa.Column("runway_risk_threshold", sa.Float, nullable=False, server_default="6.0"),
        sa.Column("revenue_drop_threshold", sa.Float, nullable=False, server_default="-0.1"),
        sa.Column("margin_drop_threshold", sa.Float, nullable=False, server_default="-0.1"),
        sa.Column("updated_at", sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("organization_settings")
