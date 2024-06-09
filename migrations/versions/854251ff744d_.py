"""empty message

Revision ID: 854251ff744d
Revises:
Create Date: 2019-03-26 09:19:09.007838

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "854251ff744d"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Initial database schema."""
    op.create_table(
        "ranks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=32), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("debt_limit", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("creation_date", sa.DateTime(), nullable=False),
        sa.Column("firstname", sa.String(length=32), nullable=True),
        sa.Column("lastname", sa.String(length=32), nullable=False),
        sa.Column("password", sa.String(length=256), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "adminupdates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "deposits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(length=64), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "payoffs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(length=64), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "rankupdates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("rank_id", sa.Integer(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["rank_id"],
            ["ranks.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "refunds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(length=64), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("total_price", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "replenishmentcollections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("comment", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "stocktakingcollections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=24), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "uploads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("filename"),
    )
    op.create_table(
        "userverifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "depositrevokes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("deposit_id", sa.Integer(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["deposit_id"],
            ["deposits.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "payoffrevokes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("refund_id", sa.Integer(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["refund_id"],
            ["payoffs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("creation_date", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("barcode", sa.String(length=32), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("countable", sa.Boolean(), nullable=False),
        sa.Column("revocable", sa.Boolean(), nullable=False),
        sa.Column("image_upload_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["image_upload_id"],
            ["uploads.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("barcode"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "refundrevokes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("refund_id", sa.Integer(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["refund_id"],
            ["refunds.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "replenishmentcollectionrevoke",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("replcoll_id", sa.Integer(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["replcoll_id"],
            ["replenishmentcollections.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "stocktakingcollectionrevokes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("collection_id", sa.Integer(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["collection_id"],
            ["stocktakingcollections.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "product_tag_assignments",
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("tag_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["tags.id"],
        ),
    )
    op.create_table(
        "productprices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "purchases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("productprice", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "replenishments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("replcoll_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("total_price", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
        ),
        sa.ForeignKeyConstraint(
            ["replcoll_id"],
            ["replenishmentcollections.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "stocktakings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("collection_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["collection_id"],
            ["stocktakingcollections.id"],
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "purchaserevokes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("purchase_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["purchase_id"],
            ["purchases.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "replenishmentrevoke",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("repl_id", sa.Integer(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["repl_id"],
            ["replenishments.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("replenishmentrevoke")
    op.drop_table("purchaserevokes")
    op.drop_table("stocktakings")
    op.drop_table("replenishments")
    op.drop_table("purchases")
    op.drop_table("productprices")
    op.drop_table("product_tag_assignments")
    op.drop_table("stocktakingcollectionrevokes")
    op.drop_table("replenishmentcollectionrevoke")
    op.drop_table("refundrevokes")
    op.drop_table("products")
    op.drop_table("payoffrevokes")
    op.drop_table("depositrevokes")
    op.drop_table("userverifications")
    op.drop_table("uploads")
    op.drop_table("tags")
    op.drop_table("stocktakingcollections")
    op.drop_table("replenishmentcollections")
    op.drop_table("refunds")
    op.drop_table("rankupdates")
    op.drop_table("payoffs")
    op.drop_table("deposits")
    op.drop_table("adminupdates")
    op.drop_table("users")
    op.drop_table("ranks")
    # ### end Alembic commands ###
