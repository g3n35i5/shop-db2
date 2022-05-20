"""empty message

Revision ID: 5e439efc0e2e
Revises: ea05656e793c
Create Date: 2019-04-25 09:23:49.489179

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5e439efc0e2e"
down_revision = "ea05656e793c"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "turnovers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(length=256), nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "turnoverrevokes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("turnover_id", sa.Integer(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["turnover_id"],
            ["turnovers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("turnoverrevokes")
    op.drop_table("turnovers")
    # ### end Alembic commands ###
