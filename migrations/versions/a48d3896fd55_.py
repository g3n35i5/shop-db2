"""empty message

Revision ID: a48d3896fd55
Revises: 92b955138026
Create Date: 2020-02-07 10:00:16.326372

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a48d3896fd55"
down_revision = "92b955138026"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "ranks",
        sa.Column("is_system_user", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    with op.batch_alter_table("ranks") as batch_op:
        batch_op.alter_column("debt_limit", existing_type=sa.INTEGER(), nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("ranks", "debt_limit", existing_type=sa.INTEGER(), nullable=False)
    op.drop_column("ranks", "is_system_user")
    # ### end Alembic commands ###
