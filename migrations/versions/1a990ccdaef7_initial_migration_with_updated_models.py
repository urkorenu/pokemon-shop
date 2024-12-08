"""Initial migration with updated models

Revision ID: 1a990ccdaef7
Revises: 
Create Date: 2024-11-27 16:37:52.586509

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1a990ccdaef7"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=True),
        sa.Column("location", sa.String(length=120), nullable=True),
        sa.Column("contact_preference", sa.String(length=20), nullable=False),
        sa.Column("contact_details", sa.String(length=250), nullable=False),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("feedback_count", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_table(
        "card",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("condition", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("set_name", sa.String(length=120), nullable=False),
        sa.Column("number", sa.String(length=50), nullable=False),
        sa.Column("image_url", sa.String(length=250), nullable=True),
        sa.Column("is_graded", sa.Boolean(), nullable=True),
        sa.Column("grade", sa.Float(), nullable=True),
        sa.Column("grading_company", sa.String(length=50), nullable=True),
        sa.Column("tcg_price", sa.Float(), nullable=True),
        sa.Column("card_type", sa.String(length=50), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), nullable=True),
        sa.Column("uploader_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["uploader_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "order",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("buyer_id", sa.Integer(), nullable=False),
        sa.Column("seller_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["buyer_id"],
            ["user.id"],
        ),
        sa.ForeignKeyConstraint(
            ["seller_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "cart",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("card_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["card_id"],
            ["card.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "order_cards",
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("card_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["card_id"],
            ["card.id"],
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["order.id"],
        ),
        sa.PrimaryKeyConstraint("order_id", "card_id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("order_cards")
    op.drop_table("cart")
    op.drop_table("order")
    op.drop_table("card")
    op.drop_table("user")
    # ### end Alembic commands ###
