"""empty message

Revision ID: 0f534f276238
Revises: 3dc8453d444e
Create Date: 2020-03-02 10:46:21.940195

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0f534f276238"
down_revision = "3dc8453d444e"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("purchases") as batch_op:
        batch_op.add_column(sa.Column("admin_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            constraint_name="fk_admin_id",
            referent_table="users",
            local_cols=["admin_id"],
            remote_cols=["id"],
        )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "purchases", type_="foreignkey")
    op.drop_column("purchases", "admin_id")
    # ### end Alembic commands ###
