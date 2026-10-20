from alembic import op
revision = "journey_0002"
down_revision = "journey_0001"

def upgrade():
    op.execute("CREATE INDEX journey_expiry ON journey.journeys (expires_at)")
    op.execute("""CREATE FUNCTION journey.immutable() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN RAISE EXCEPTION 'Shared journeys are immutable'; END $$""")
    op.execute("CREATE TRIGGER immutable_journey BEFORE UPDATE ON journey.journeys FOR EACH ROW EXECUTE FUNCTION journey.immutable()")
    op.execute("""CREATE FUNCTION journey.retained() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF OLD.expires_at + interval '7 days' > now() THEN RAISE EXCEPTION 'Journey retention has not elapsed'; END IF;
      RETURN OLD;
    END $$""")
    op.execute("CREATE TRIGGER retained_journey BEFORE DELETE ON journey.journeys FOR EACH ROW EXECUTE FUNCTION journey.retained()")
    op.execute("REVOKE UPDATE ON journey.journeys FROM journey_app")

def downgrade():
    raise RuntimeError("Destructive downgrades are disabled")
