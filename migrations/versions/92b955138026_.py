"""empty message

Revision ID: 92b955138026
Revises: 5e439efc0e2e
Create Date: 2020-02-05 14:51:54.314055

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "92b955138026"
down_revision = "5e439efc0e2e"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "tags",
        sa.Column("is_for_sale", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("tags", "is_for_sale")
    # ### end Alembic commands ###
