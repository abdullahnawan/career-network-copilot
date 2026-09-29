"""Create student profile foundation tables."""

from alembic import op
import sqlalchemy as sa

revision = "20260928_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("school", sa.String(length=160)),
        sa.Column("program", sa.String(length=160)),
        sa.Column("graduation_year", sa.Integer()),
        sa.Column("location", sa.String(length=160)),
        sa.Column("bio", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "career_goals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_profile_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=160), nullable=False),
        sa.Column("industry", sa.String(length=160)),
        sa.Column("location", sa.String(length=160)),
        sa.Column("goal_type", sa.String(length=80), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["student_profile_id"], ["student_profiles.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "skills",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
    )
    op.create_table(
        "student_skills",
        sa.Column("student_profile_id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("proficiency_level", sa.String(length=40), nullable=False),
        sa.ForeignKeyConstraint(["student_profile_id"], ["student_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("student_profile_id", "skill_id"),
    )


def downgrade() -> None:
    op.drop_table("student_skills")
    op.drop_table("skills")
    op.drop_table("career_goals")
    op.drop_table("student_profiles")
