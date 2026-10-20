from alembic import op
revision = "journey_0003"
down_revision = "journey_0002"


def upgrade():
    op.execute("""ALTER TABLE journey.journeys ADD CONSTRAINT journey_position_cardinality
        CHECK (cardinality(origin_position_pc)=3 AND cardinality(destination_position_pc)=3)""")
    op.execute("""ALTER TABLE journey.journeys ADD CONSTRAINT journey_finite_timestamps
        CHECK (isfinite(created_at) AND isfinite(expires_at))""")
    op.execute("""ALTER TABLE journey.journeys ADD CONSTRAINT journey_assumptions_array
        CHECK (jsonb_typeof(assumptions)='array')""")


def downgrade():
    raise RuntimeError("Destructive downgrades are disabled")
