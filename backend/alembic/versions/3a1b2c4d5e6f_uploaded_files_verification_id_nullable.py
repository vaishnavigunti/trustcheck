"""Make uploaded_files.verification_id nullable

A file is uploaded before its verification exists and is linked afterwards,
so the foreign key must allow NULL at insert time.

Revision ID: 3a1b2c4d5e6f
Revises: 2171d4e40e95
Create Date: 2026-06-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "3a1b2c4d5e6f"
down_revision: Union[str, None] = "2171d4e40e95"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("uploaded_files") as batch_op:
        batch_op.alter_column(
            "verification_id",
            existing_type=postgresql.UUID(as_uuid=True),
            nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("uploaded_files") as batch_op:
        batch_op.alter_column(
            "verification_id",
            existing_type=postgresql.UUID(as_uuid=True),
            nullable=False,
        )
