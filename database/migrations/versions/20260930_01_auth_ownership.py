"""Add users, opaque sessions, and ownership to legacy data."""

import sqlalchemy as sa
from alembic import op

revision = "20260930_01"
down_revision = "20260929_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column(
            "display_name", sa.String(120), nullable=False, server_default="Legacy user"
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("password_hash", sa.String(512), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index(
        "ix_user_sessions_token_hash", "user_sessions", ["token_hash"], unique=True
    )
    op.execute(
        "INSERT INTO users (email, password_hash) VALUES "
        "('legacy@local.invalid', '$argon2id$v=19$m=65536,t=3,p=4$legacy-migration$legacy-migration')"
    )
    for table in ("student_profiles", "contacts", "outreach_drafts"):
        op.add_column(
            table,
            sa.Column("owner_id", sa.Integer(), nullable=False, server_default="1"),
        )
        op.create_index(f"ix_{table}_owner_id", table, ["owner_id"])
        op.create_foreign_key(
            f"fk_{table}_owner_id",
            table,
            "users",
            ["owner_id"],
            ["id"],
            ondelete="CASCADE",
        )
        op.execute(
            f"UPDATE {table} SET owner_id = (SELECT id FROM users WHERE email = 'legacy@local.invalid')"
        )
        op.alter_column(table, "owner_id", server_default=None)


def downgrade() -> None:
    for table in ("outreach_drafts", "contacts", "student_profiles"):
        op.drop_constraint(f"fk_{table}_owner_id", table, type_="foreignkey")
        op.drop_index(f"ix_{table}_owner_id", table)
        op.drop_column(table, "owner_id")
    op.drop_table("user_sessions")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
