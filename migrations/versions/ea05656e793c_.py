"""empty message

Revision ID: ea05656e793c
Revises: 854251ff744d
Create Date: 2019-03-26 09:23:49.235545

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ea05656e793c"
down_revision = "854251ff744d"
branch_labels = None
depends_on = None


def upgrade():
    """
    The column "refund_id" in the table "payoffrevoke" is named wrong and must
    be renamed to "payoff_id".
    """
    op.alter_column("payoffrevokes", "refund_id", new_column_name="payoff_id")


def downgrade():
    """
    The renaming of the column "payoff_id" is undone.
    """
    op.alter_column("payoffrevokes", "payoff_id", new_column_name="refund_id")
