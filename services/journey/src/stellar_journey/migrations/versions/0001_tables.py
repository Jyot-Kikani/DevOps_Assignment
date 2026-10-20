from alembic import op
from stellar_journey.db import metadata
revision = "journey_0001"
down_revision = None

def upgrade():
    metadata.create_all(op.get_bind())

def downgrade():
    raise RuntimeError("Destructive downgrades are disabled")
