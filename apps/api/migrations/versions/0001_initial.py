"""Foundation schema snapshot; extension retained on downgrade."""

from pathlib import Path

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    sql = Path(__file__).with_suffix(".sql").read_text(encoding="utf-8")
    for statement in sql.split(";"):
        if statement.strip():
            op.execute(statement)


def downgrade():
    op.execute("ALTER TABLE consents DROP CONSTRAINT consent_player_org_fk")
    op.execute("ALTER TABLE consents DROP CONSTRAINT consent_subject_fk")
    for table in [
        "audit_log",
        "jobs",
        "style_assignments",
        "style_models",
        "feature_sets",
        "events",
        "annotations",
        "rounds",
        "match_players",
        "matches",
        "assets",
        "players",
        "consents",
        "memberships",
        "users",
        "organizations",
    ]:
        op.drop_table(table)
