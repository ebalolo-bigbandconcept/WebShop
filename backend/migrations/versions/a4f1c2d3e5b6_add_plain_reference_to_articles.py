"""Rename articles.reference to designation and add plain reference

Revision ID: a4f1c2d3e5b6
Revises: 003_add_interest_rate_ranges
Create Date: 2026-02-16 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a4f1c2d3e5b6"
down_revision = "003_add_interest_rate_ranges"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("articles", schema=None) as batch_op:
        batch_op.alter_column("reference", new_column_name="designation")
        batch_op.add_column(
            sa.Column("reference", sa.String(length=200), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("articles", schema=None) as batch_op:
        batch_op.drop_column("reference")
        batch_op.alter_column("designation", new_column_name="reference")
