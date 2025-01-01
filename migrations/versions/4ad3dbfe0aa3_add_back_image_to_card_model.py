"""Add back image to Card model

Revision ID: 4ad3dbfe0aa3
Revises: 2ce3bd4f19cd
Create Date: 2024-12-30 16:36:33.703515

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "4ad3dbfe0aa3"
down_revision = "2ce3bd4f19cd"
branch_labels = None
depends_on = None


def upgrade():
    # Drop the 'message' table if required
    op.drop_table("message")

    # Add the 'back_image_url' column to 'card' table with nullable=True
    with op.batch_alter_table("card", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("back_image_url", sa.String(length=250), nullable=True)
        )

    # Optional: If you want to initialize existing rows with a default value (e.g., NULL or a placeholder), you can do so here
    # op.execute("UPDATE card SET back_image_url = NULL")


def downgrade():
    # Remove the 'back_image_url' column in the downgrade
    with op.batch_alter_table("card", schema=None) as batch_op:
        batch_op.drop_column("back_image_url")

    # Recreate the 'message' table
    op.create_table(
        "message",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("sender_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("receiver_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("message", sa.TEXT(), autoincrement=False, nullable=False),
        sa.Column(
            "timestamp", postgresql.TIMESTAMP(), autoincrement=False, nullable=True
        ),
        sa.Column("is_read", sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(
            ["receiver_id"], ["user.id"], name="message_receiver_id_fkey"
        ),
        sa.ForeignKeyConstraint(
            ["sender_id"], ["user.id"], name="message_sender_id_fkey"
        ),
        sa.PrimaryKeyConstraint("id", name="message_pkey"),
    )
