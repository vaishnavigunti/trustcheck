"""Add user_id owner column to uploaded_files

Records the uploading user so that linking a file to a verification can enforce
ownership (prevents IDOR via guessed file ids).

Revision ID: 4b2c6d7e8f90
Revises: 3a1b2c4d5e6f
Create Date: 2026-06-21 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "4b2c6d7e8f90"
down_revision: Union[str, None] = "3a1b2c4d5e6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "uploaded_files",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_uploaded_files_user_id", "uploaded_files", ["user_id"]
    )
    op.create_foreign_key(
        "fk_uploaded_files_user_id_users",
        "uploaded_files",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_uploaded_files_user_id_users", "uploaded_files", type_="foreignkey"
    )
    op.drop_index("ix_uploaded_files_user_id", table_name="uploaded_files")
    op.drop_column("uploaded_files", "user_id")
