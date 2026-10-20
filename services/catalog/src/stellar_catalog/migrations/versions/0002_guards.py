from alembic import op
revision = "catalog_0002"
down_revision = "catalog_0001"

def upgrade():
    op.execute("CREATE INDEX star_id_prefix ON catalog.stars (snapshot_id, source_id text_pattern_ops)")
    op.execute("CREATE INDEX star_radius ON catalog.stars (snapshot_id, distance_pc, source_id)")
    op.execute("CREATE INDEX alias_prefix ON catalog.aliases (snapshot_id, normalized_alias text_pattern_ops)")
    op.execute("""CREATE FUNCTION catalog.guard_snapshot() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF OLD.status = 'ready' THEN RAISE EXCEPTION 'Ready snapshots are immutable'; END IF;
      RETURN NEW;
    END $$""")
    op.execute("CREATE TRIGGER immutable_snapshot BEFORE UPDATE OR DELETE ON catalog.snapshots FOR EACH ROW EXECUTE FUNCTION catalog.guard_snapshot()")
    op.execute("""CREATE FUNCTION catalog.guard_child() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE sid text;
    BEGIN
      sid := CASE WHEN TG_OP = 'DELETE' THEN OLD.snapshot_id ELSE NEW.snapshot_id END;
      IF EXISTS (SELECT 1 FROM catalog.snapshots WHERE id = sid AND status = 'ready')
         OR (TG_OP = 'UPDATE' AND EXISTS (SELECT 1 FROM catalog.snapshots WHERE id = OLD.snapshot_id AND status = 'ready'))
      THEN RAISE EXCEPTION 'Ready snapshot data is immutable'; END IF;
      IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
      RETURN NEW;
    END $$""")
    for table in ("stars", "aliases", "map_chunks"):
        op.execute(f"CREATE TRIGGER immutable_child BEFORE INSERT OR UPDATE OR DELETE ON catalog.{table} FOR EACH ROW EXECUTE FUNCTION catalog.guard_child()")
    op.execute("""CREATE FUNCTION catalog.guard_active() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM catalog.snapshots WHERE id = NEW.snapshot_id AND status = 'ready')
      THEN RAISE EXCEPTION 'Only ready snapshots can be active'; END IF;
      RETURN NEW;
    END $$""")
    op.execute("CREATE TRIGGER ready_active BEFORE INSERT OR UPDATE ON catalog.active_snapshot FOR EACH ROW EXECUTE FUNCTION catalog.guard_active()")

def downgrade():
    raise RuntimeError("Destructive downgrades are disabled")
